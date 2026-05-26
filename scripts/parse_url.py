#!/usr/bin/env python3
"""
从网页链接或已保存详情页 HTML 解析房源信息。

用法：
  python3 scripts/parse_url.py --url "https://bj.ke.com/ershoufang/xxx.html"
  python3 scripts/parse_url.py --url "https://bj.ke.com/ershoufang/xxx.html" --html detail.local.html
"""

import argparse
from datetime import datetime

from listing_parsers import (
    append_unique_listings,
    fetch_page,
    load_listings,
    looks_like_blocked_page,
    parse_generic_html,
    parse_ke_lianjia_detail_html,
    save_listings,
)


def parse_url(url, html_path=None):
    if html_path:
        with open(html_path, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()
    else:
        try:
            html, final_url = fetch_page(url, timeout=10)
        except Exception as e:
            print(f"获取页面失败: {e}")
            return None
        if looks_like_blocked_page(html, final_url):
            print("检测到登录/验证码页面，建议用 crawl_interactive.py 先让人处理验证")
            return None

    if "ke.com" in url or "lianjia.com" in url:
        return parse_ke_lianjia_detail_html(html, url)
    return parse_generic_html(html, url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从网页链接解析房源（买房版）")
    parser.add_argument("--url", required=True, help="房源链接")
    parser.add_argument("--source", help="手动指定来源")
    parser.add_argument("--html", help="解析已保存的详情页 HTML")
    args = parser.parse_args()

    info = parse_url(args.url, args.html)
    if not info:
        print("❌ 解析失败")
        raise SystemExit(1)

    if args.source:
        info["source"] = args.source
    info["status"] = "待看房"
    info["created_at"] = datetime.now().isoformat()
    info["updated_at"] = datetime.now().isoformat()

    listings = load_listings()
    added = append_unique_listings(listings, [info])
    save_listings(listings)

    if not added:
        print("⚠️ 解析成功，但该房源已存在，未重复保存")
        for k, v in info.items():
            print(f"   {k}: {v}")
        raise SystemExit(0)

    print(f"✅ 解析成功！已保存为房源 ID: {added[0]['id']}")
    for k, v in added[0].items():
        if k != "id":
            print(f"   {k}: {v}")
