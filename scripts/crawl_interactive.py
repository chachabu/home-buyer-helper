#!/usr/bin/env python3
"""
人在回路网页抓取。

有 Playwright 时：打开真实浏览器，用户手动登录/填验证码/调筛选，回车后读取当前页面解析。
无 Playwright 时：打开默认浏览器，用户保存 HTML 文件后脚本解析该 HTML。
"""

import argparse
import os
import subprocess
import tempfile
import time
import webbrowser

from listing_parsers import (
    DATA_DIR,
    append_unique_listings,
    assign_preview_ids,
    build_beike_url,
    load_listings,
    mark_ordinary_residence_listings,
    mark_near_subway_listings,
    parse_beike_listings_html,
    resolve_city_code,
    save_listings,
)


def crawl_interactive(args):
    if args.platform in ("贝壳", "链家"):
        code = resolve_city_code(args.city)
        source = "贝壳找房" if args.platform == "贝壳" else "链家"

        if args.current_chrome:
            print(f"\n🔍 {args.platform} - 读取当前 Chrome 标签页")
            current_page = _load_current_chrome_page(args)
            if not current_page:
                print("❌ 未能读取当前 Chrome 页面")
                return
            html_pages = [current_page["html"]]
            source_urls = [current_page["url"]]
            page_count = 1
            print(f"   URL: {current_page['url']}")
            print(f"   标题: {current_page['title']}")
        else:
            page_count = max(1, args.pages or 1)
            urls = [
                build_beike_url(
                    args.city,
                    args.area,
                    args.budget_min,
                    args.budget_max,
                    page=page,
                    near_subway=args.near_subway,
                    ordinary_residence=args.ordinary_residence,
                )
                for page in range(1, page_count + 1)
            ]
            source_urls = urls
            print(f"\n🔍 {args.platform} - {args.city} {args.area or '全城'}")
            for index, url in enumerate(urls, start=1):
                prefix = f"URL 第 {index}/{page_count} 页" if page_count > 1 else "URL"
                print(f"   {prefix}: {url}")

            if args.html:
                html_pages = _load_html_pages_from_paths(args.html, page_count)
            else:
                html_pages = _load_html_pages_with_human_browser(urls, args)

        if not html_pages:
            print("❌ 未获得页面 HTML")
            return

        listings = []
        for index, html in enumerate(html_pages, start=1):
            if not html:
                continue
            if args.limit and len(listings) >= args.limit:
                break
            source_url = source_urls[index - 1] if index <= len(source_urls) else ""
            remaining = args.limit - len(listings) if args.limit else 0
            page_listings = parse_beike_listings_html(html, city_code=code, source=source)
            is_near_subway = args.near_subway or "su1" in source_url
            is_ordinary_residence = args.ordinary_residence or "sf1" in source_url
            page_listings = _filter_listings_by_args(page_listings, args, is_ordinary_residence)
            if remaining:
                page_listings = page_listings[:remaining]
            if is_near_subway:
                mark_near_subway_listings(page_listings, label=f"近地铁（{source}筛选）")
            if is_ordinary_residence:
                mark_ordinary_residence_listings(page_listings)
            if page_count > 1:
                print(f"   第 {index}/{page_count} 页解析: {len(page_listings)} 条")
            listings.extend(page_listings)
        _preview_and_save(listings, args.save)
        return

    url = _fallback_url(args)
    print(f"\n🔍 {args.platform} - {args.city} {args.area or '全城'}")
    print(f"   URL: {url}")
    print("\n💡 该平台暂未做专用解析。建议在浏览器完成搜索后保存 HTML，再用 crawl_listings.py --html 解析。")
    webbrowser.open(url)


def _fallback_url(args):
    if args.platform in ("58", "58同城"):
        city_map = {"北京": "bj", "上海": "sh", "广州": "gz", "深圳": "sz", "成都": "cd"}
        return f"https://{city_map.get(args.city, 'bj')}.58.com/ershoufang/"
    if args.platform == "安居客":
        city_map = {"北京": "beijing", "上海": "shanghai", "广州": "guangzhou", "深圳": "shenzhen"}
        return f"https://{city_map.get(args.city, 'beijing')}.fang.anjuke.com/"
    return "https://www.ke.com/"


def _load_html_with_human_browser(url, args):
    html_pages = _load_html_pages_with_human_browser([url], args)
    return html_pages[0] if html_pages else ""


def _load_current_chrome_page(args):
    app_name = _applescript_string(args.chrome_app)
    tmp_dir = tempfile.mkdtemp(prefix="home-buyer-chrome-")
    html_path = os.path.join(tmp_dir, "active-tab.html")
    try:
        url = _run_osascript(f'tell application "{app_name}" to get URL of active tab of front window')
        title = _run_osascript(f'tell application "{app_name}" to get title of active tab of front window')
        _run_osascript(
            f'tell application "{app_name}" to save active tab of front window '
            f'in POSIX file "{_applescript_string(html_path)}" as "only html"'
        )
        for _ in range(30):
            if os.path.exists(html_path) and os.path.getsize(html_path) > 0:
                break
            time.sleep(0.1)
        with open(html_path, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()
        return {"url": url, "title": title, "html": html}
    except Exception as e:
        print(f"⚠️ 读取 Chrome 当前页失败: {e}")
        return None
    finally:
        try:
            if os.path.exists(html_path):
                os.remove(html_path)
            os.rmdir(tmp_dir)
        except OSError:
            pass


def _run_osascript(script):
    try:
        return subprocess.check_output(
            ["osascript", "-e", script],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError((e.output or "").strip() or str(e)) from e


def _applescript_string(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _filter_listings_by_args(listings, args, ordinary_residence=False):
    filtered = []
    for listing in listings:
        price = float(listing.get("price_wan") or 0)
        if args.budget_min is not None and price < args.budget_min:
            continue
        if args.budget_max is not None and price > args.budget_max:
            continue
        if ordinary_residence:
            text = f"{listing.get('community', '')}{listing.get('name', '')}{listing.get('property_type', '')}"
            if "商业类" in text or "商业办公" in text:
                continue
        filtered.append(listing)
    return filtered


def _load_html_pages_from_paths(html_path, page_count):
    expanded = os.path.expanduser(html_path)
    if page_count > 1 and "{page}" not in expanded:
        print("  ⚠️ --html 未包含 {page} 占位符，将只解析单个 HTML 文件")
        page_count = 1
    paths = [expanded.format(page=page) for page in range(1, page_count + 1)]
    html_pages = []
    for path in paths:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            html_pages.append(f.read())
    return html_pages


def _load_html_pages_with_human_browser(urls, args):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n💡 当前未安装 Playwright，已退回到手动 HTML 模式。")
        print("   安装后可直接在脚本打开的浏览器里登录/填验证码，然后自动解析：")
        print("   python3 -m pip install playwright && python3 -m playwright install chromium")
        html_pages = []
        for index, url in enumerate(urls, start=1):
            webbrowser.open(url)
            suffix = f"第 {index}/{len(urls)} 页" if len(urls) > 1 else "当前页"
            html_path = input(f"\n请在浏览器完成登录/验证码后保存{suffix} HTML，并输入 HTML 文件路径: ").strip()
            if not html_path:
                continue
            with open(os.path.expanduser(html_path), "r", encoding="utf-8", errors="replace") as f:
                html_pages.append(f.read())
        return html_pages

    profile_dir = os.path.expanduser(args.profile_dir or os.path.join(DATA_DIR, "browser-profile"))
    os.makedirs(profile_dir, exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                profile_dir,
                headless=False,
                viewport={"width": 1440, "height": 1000},
                locale="zh-CN",
            )
            page = browser.pages[0] if browser.pages else browser.new_page()
            html_pages = []
            print("\n🌐 已打开浏览器。请在浏览器里完成登录/验证码/筛选调整。")
            for index, url in enumerate(urls, start=1):
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                suffix = f"第 {index}/{len(urls)} 页" if len(urls) > 1 else "当前页面"
                input(f"{suffix} 准备好后回到终端按回车，脚本会读取当前页面并解析房源...")
                html_pages.append(page.content())
            if args.keep_browser:
                print("浏览器将保持打开，方便继续调整筛选。")
            else:
                browser.close()
            return html_pages
    except Exception as e:
        print(f"\n⚠️ Playwright 浏览器启动失败: {e}")
        print("   可运行：python3 -m playwright install chromium")
        html_pages = []
        for index, url in enumerate(urls, start=1):
            webbrowser.open(url)
            suffix = f"第 {index}/{len(urls)} 页" if len(urls) > 1 else "当前页"
            html_path = input(f"也可以保存{suffix} HTML 后输入路径继续解析: ").strip()
            if not html_path:
                continue
            with open(os.path.expanduser(html_path), "r", encoding="utf-8", errors="replace") as f:
                html_pages.append(f.read())
        return html_pages


def _preview_and_save(listings, should_save):
    if not listings:
        print("\n⚠️ 未能解析出房源数据，可能页面结构已变化，或当前页面不是列表页")
        return

    preview = assign_preview_ids(listings)
    print(f"\n✅ 解析到 {len(preview)} 条房源")
    for item in preview[:10]:
        label = item.get("community") or item.get("name", "")[:8]
        print(f"  [{item['id']}] {label:8} {item.get('price_wan', 0)}万 {item.get('room_type', '')} {item.get('area', 0)}㎡ {item.get('url', '')}")
    if len(preview) > 10:
        print(f"  ... 还有 {len(preview) - 10} 条")

    if should_save:
        existing = load_listings()
        added = append_unique_listings(existing, listings)
        save_listings(existing)
        skipped = len(listings) - len(added)
        print(f"\n✅ 已保存 {len(added)} 条新房源，跳过 {skipped} 条重复房源")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="人在回路网页抓取（买房版）")
    parser.add_argument("--platform", choices=["贝壳", "链家", "58", "58同城", "安居客"], required=True)
    parser.add_argument("--city", default="北京")
    parser.add_argument("--area")
    parser.add_argument("--budget-min", type=float)
    parser.add_argument("--budget-max", type=float)
    parser.add_argument("--near-subway", action="store_true", help="贝壳近地铁筛选（su1）")
    parser.add_argument("--ordinary-residence", action="store_true", help="贝壳普通住宅筛选（sf1）")
    parser.add_argument("--pages", type=int, default=1, help="贝壳/链家列表页数，--limit 为总条数上限")
    parser.add_argument("--limit", type=int, default=0, help="解析条数上限，默认0表示当前页全部")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--html", help="直接解析已保存的列表页 HTML")
    parser.add_argument("--current-chrome", action="store_true", help="读取当前 Google Chrome 标签页；适合手动筛选/翻页/过验证后导入")
    parser.add_argument("--chrome-app", default="Google Chrome", help="--current-chrome 使用的浏览器应用名，默认 Google Chrome")
    parser.add_argument("--profile-dir", help="Playwright 浏览器用户数据目录，默认 data/browser-profile")
    parser.add_argument("--keep-browser", action="store_true", help="解析后不关闭 Playwright 浏览器")
    args = parser.parse_args()
    crawl_interactive(args)
