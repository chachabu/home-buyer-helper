#!/usr/bin/env python3
"""
人在回路网页抓取。

有 Playwright 时：打开真实浏览器，用户手动登录/填验证码/调筛选，回车后读取当前页面解析。
无 Playwright 时：打开默认浏览器，用户保存 HTML 文件后脚本解析该 HTML。
"""

import argparse
import os
import webbrowser

from listing_parsers import (
    DATA_DIR,
    append_unique_listings,
    assign_preview_ids,
    build_beike_url,
    load_listings,
    parse_beike_listings_html,
    resolve_city_code,
    save_listings,
)


def crawl_interactive(args):
    if args.platform in ("贝壳", "链家"):
        code = resolve_city_code(args.city)
        url = build_beike_url(args.city, args.area, args.budget_min, args.budget_max)
        print(f"\n🔍 {args.platform} - {args.city} {args.area or '全城'}")
        print(f"   URL: {url}")

        if args.html:
            with open(os.path.expanduser(args.html), "r", encoding="utf-8", errors="replace") as f:
                html = f.read()
        else:
            html = _load_html_with_human_browser(url, args)
        if not html:
            print("❌ 未获得页面 HTML")
            return
        source = "贝壳找房" if args.platform == "贝壳" else "链家"
        listings = parse_beike_listings_html(html, city_code=code, source=source, limit=args.limit)
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
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n💡 当前未安装 Playwright，已退回到手动 HTML 模式。")
        print("   安装后可直接在脚本打开的浏览器里登录/填验证码，然后自动解析：")
        print("   python3 -m pip install playwright && python3 -m playwright install chromium")
        webbrowser.open(url)
        html_path = input("\n请在浏览器完成登录/验证码后保存网页 HTML，并输入 HTML 文件路径: ").strip()
        if not html_path:
            return ""
        with open(os.path.expanduser(html_path), "r", encoding="utf-8", errors="replace") as f:
            return f.read()

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
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print("\n🌐 已打开浏览器。请在浏览器里完成登录/验证码/筛选调整。")
            input("完成后回到终端按回车，脚本会读取当前页面并解析房源...")
            html = page.content()
            if args.keep_browser:
                print("浏览器将保持打开，方便继续调整筛选。")
            else:
                browser.close()
            return html
    except Exception as e:
        print(f"\n⚠️ Playwright 浏览器启动失败: {e}")
        print("   可运行：python3 -m playwright install chromium")
        webbrowser.open(url)
        html_path = input("也可以保存网页 HTML 后输入路径继续解析: ").strip()
        if not html_path:
            return ""
        with open(os.path.expanduser(html_path), "r", encoding="utf-8", errors="replace") as f:
            return f.read()


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
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--html", help="直接解析已保存的列表页 HTML")
    parser.add_argument("--profile-dir", help="Playwright 浏览器用户数据目录，默认 data/browser-profile")
    parser.add_argument("--keep-browser", action="store_true", help="解析后不关闭 Playwright 浏览器")
    args = parser.parse_args()
    crawl_interactive(args)
