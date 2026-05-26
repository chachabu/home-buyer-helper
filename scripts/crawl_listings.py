#!/usr/bin/env python3
"""
从买房网站抓取/导入房源列表。

推荐用法：
- 直接尝试低频抓取：
  python3 scripts/crawl_listings.py --platform 贝壳 --city 北京 --area 朝阳区 --budget-min 300 --budget-max 800
- 浏览器登录/验证码后保存 HTML，再解析：
  python3 scripts/crawl_listings.py --platform 贝壳 --city 北京 --html page.local.html --save
"""

import argparse

from listing_parsers import (
    append_unique_listings,
    assign_preview_ids,
    build_beike_url,
    fetch_page,
    load_listings,
    looks_like_blocked_page,
    mark_ordinary_residence_listings,
    mark_near_subway_listings,
    parse_beike_listings_html,
    parse_generic_html,
    resolve_beike_area_slug,
    resolve_city_code,
    save_listings,
)


def crawl_ke(args):
    """抓取贝壳找房列表页。"""
    code = resolve_city_code(args.city)
    if args.area and not resolve_beike_area_slug(args.city, args.area):
        print(f"  ⚠️ 暂未内置区域 slug: {args.city} {args.area}，将抓取全城列表")
    source = "贝壳找房" if args.platform == "贝壳" else "链家"
    listings = []
    page_count = max(1, args.pages or 1)

    for page in range(1, page_count + 1):
        if args.limit and len(listings) >= args.limit:
            break
        remaining = args.limit - len(listings) if args.limit else None
        url = build_beike_url(
            args.city,
            args.area,
            args.budget_min,
            args.budget_max,
            page=page,
            near_subway=args.near_subway,
            ordinary_residence=args.ordinary_residence,
        )
        prefix = f"第 {page}/{page_count} 页" if page_count > 1 else "抓取"
        print(f"  {prefix}: {url}")
        try:
            html, final_url = fetch_page(url)
        except Exception as e:
            print(f"  获取页面失败: {e}")
            break
        if looks_like_blocked_page(html, final_url):
            print("  ⚠️ 检测到登录/验证码页面，建议改用 crawl_interactive.py 让人处理验证")
            break
        page_listings = parse_beike_listings_html(html, city_code=code, source=source, limit=remaining)
        if args.near_subway:
            mark_near_subway_listings(page_listings, label=f"近地铁（{source}筛选）")
        if args.ordinary_residence:
            mark_ordinary_residence_listings(page_listings)
        print(f"    解析: {len(page_listings)} 条")
        if not page_listings:
            break
        listings.extend(page_listings)
    return listings


def crawl_lianjia(args):
    """链家与贝壳页面结构相近，复用贝壳解析器。"""
    return crawl_ke(args)


def crawl_58(args):
    """58 同城仅保留低保真通用解析，复杂场景建议用 HTML 导入。"""
    city_map = {'北京': 'bj', '上海': 'sh', '广州': 'gz', '深圳': 'sz', '成都': 'cd'}
    code = city_map.get(args.city, 'bj')
    url = f"https://{code}.58.com/ershoufang/"
    print(f"  抓取: {url}")
    try:
        html, _ = fetch_page(url)
    except Exception as e:
        print(f"  获取页面失败: {e}")
        return []
    info = parse_generic_html(html, url)
    return [info] if info.get("name") else []


def crawl_anjuke(args):
    """安居客仅保留低保真通用解析，复杂场景建议用 HTML 导入。"""
    city_map = {'北京': 'beijing', '上海': 'shanghai', '广州': 'guangzhou', '深圳': 'shenzhen'}
    code = city_map.get(args.city, 'beijing')
    url = f"https://{code}.fang.anjuke.com/"
    print(f"  抓取: {url}")
    try:
        html, _ = fetch_page(url)
    except Exception as e:
        print(f"  获取页面失败: {e}")
        return []
    info = parse_generic_html(html, url)
    return [info] if info.get("name") else []


def crawl_from_html(args):
    code = resolve_city_code(args.city)
    html_paths = [args.html]
    if args.pages and args.pages > 1:
        if "{page}" in args.html:
            html_paths = [args.html.format(page=page) for page in range(1, args.pages + 1)]
        else:
            print("  ⚠️ --html 未包含 {page} 占位符，将只解析单个 HTML 文件")

    listings = []
    for html_path in html_paths:
        if args.limit and len(listings) >= args.limit:
            break
        remaining = args.limit - len(listings) if args.limit else None
        with open(html_path, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()
        if args.platform in ("贝壳", "链家"):
            source = "贝壳找房" if args.platform == "贝壳" else "链家"
            page_listings = parse_beike_listings_html(html, city_code=code, source=source, limit=remaining)
            if args.near_subway:
                mark_near_subway_listings(page_listings, label=f"近地铁（{source}筛选）")
            if args.ordinary_residence:
                mark_ordinary_residence_listings(page_listings)
            listings.extend(page_listings)
            continue
        info = parse_generic_html(html, html_path)
        if info.get("name"):
            listings.append(info)
    return listings


def crawl_listings(args):
    if args.html:
        all_listings = crawl_from_html(args)
    else:
        crawlers = {
            '贝壳': crawl_ke,
            '链家': crawl_lianjia,
            '58同城': crawl_58,
            '安居客': crawl_anjuke,
        }
        all_listings = []
        targets = [args.platform] if args.platform else list(crawlers.keys())
        for platform in targets:
            fn = crawlers.get(platform)
            if not fn:
                continue
            print(f"\n🔍 正在抓取 {platform}...")
            result = fn(args)
            print(f"  ✅ {platform}: {len(result)} 条")
            all_listings.extend(result)

    if not all_listings:
        print("\n⚠️ 未抓取到房源，可能被登录/验证码/反爬限制。建议：")
        print("   1. 用 crawl_interactive.py 打开浏览器，手动完成登录/验证码后自动解析")
        print("   2. 在浏览器保存列表页 HTML，再用 crawl_listings.py --html 页面.local.html 解析")
        print("   3. 用 parse_url.py 解析具体房源链接")
        return

    preview = assign_preview_ids(all_listings)
    print(f"\n📊 汇总: {len(preview)} 条房源")
    for item in preview[:10]:
        label = item.get('community') or item.get('name', '')[:8]
        print(f"  [{item['id']}] {label:8} {item.get('price_wan', 0)}万  {item.get('room_type', '')}  {item.get('area', 0)}㎡  {item.get('url', '')}")
    if len(preview) > 10:
        print(f"  ... 还有 {len(preview) - 10} 条")

    if args.save:
        existing = load_listings()
        added = append_unique_listings(existing, all_listings)
        save_listings(existing)
        skipped = len(all_listings) - len(added)
        print(f"\n✅ 已保存 {len(added)} 条新房源到数据库，跳过 {skipped} 条重复房源")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抓取/导入买房网站房源")
    parser.add_argument("--platform", choices=['贝壳', '链家', '58同城', '安居客'], default="贝壳")
    parser.add_argument("--city", default="北京")
    parser.add_argument("--area")
    parser.add_argument("--budget-min", type=float)
    parser.add_argument("--budget-max", type=float)
    parser.add_argument("--near-subway", action="store_true", help="贝壳近地铁筛选（su1）")
    parser.add_argument("--ordinary-residence", action="store_true", help="贝壳普通住宅筛选（sf1）")
    parser.add_argument("--pages", type=int, default=1, help="贝壳/链家列表页数，--limit 为总条数上限")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--html", help="解析已保存的列表页 HTML，适合手动登录/验证码后使用")
    args = parser.parse_args()
    crawl_listings(args)
