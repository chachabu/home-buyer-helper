#!/usr/bin/env python3
"""
交互式网页抓取（买房版）
当网站需要登录时，打开浏览器并提示用户扫码/验证码登录
用法: python crawl_interactive.py --platform 58 --city 北京 --area 朝阳区
"""

import json
import os
import re
import ssl
import argparse
import time
import urllib.request
from datetime import datetime
from urllib.parse import quote

ssl._create_default_https_context = ssl._create_unverified_context

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/home-buyer-data")
DATA_FILE = os.path.join(DATA_DIR, "listings.json")

def load_listings():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_listings(listings):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(listings, f, ensure_ascii=False, indent=2)

def fetch_page(url, headers=None):
    try:
        h = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  获取失败: {e}")
        return None

def clean(text):
    return re.sub(r'<[^>]+>', ' ', text).strip()

def crawl_interactive(args):
    city_codes = {'北京':'bj','上海':'sh','广州':'gz','深圳':'sz','杭州':'hz','成都':'cd'}
    code = city_codes.get(args.city, 'bj')

    if args.platform in ('贝壳', '链家'):
        area_part = f"/{quote(args.area.encode('utf-8'))}" if args.area else ""
        budget_filter = ""
        if args.budget_min and args.budget_max:
            budget_filter = f"p{args.budget_min}ep{args.budget_max}"
        elif args.budget_max:
            budget_filter = f"p{args.budget_max}"
        url = f"https://{code}.ke.com/ershoufang{area_part}/{budget_filter}/"
        print(f"\n🔍 贝壳找房 - {args.city} {args.area or '全城'}")
        print(f"   URL: {url}")

        print("\n💡 贝壳/链家一般不需要登录即可抓取，直接尝试...")
        html = fetch_page(url)
        if html and '登录' in html[:500] and ('验证码' in html or '验证' in html):
            print("⚠️ 检测到需要验证码，建议在浏览器手动打开后重试")
        if html:
            _parse_and_save(html, args.platform)
        else:
            print("❌ 抓取失败，可尝试手动在浏览器打开后用 parse_url.py 解析")

    elif args.platform in ('58', '58同城'):
        area_enc = quote((args.area or args.city).encode('utf-8'))
        url = f"https://{code}.58.com/ershoufang/?key={area_enc}"
        print(f"\n🔍 58同城 - {args.city} {args.area or '全城'}")
        print(f"   URL: {url}")
        print("\n💡 58同城反爬较强，建议：")
        print("   方法1: 在浏览器打开上述链接 → 搜索 → 手动复制房源信息")
        print("   方法2: 保存搜索结果页面为 HTML → 用本脚本解析")
        print("   方法3: 用 parse_url.py 逐条解析具体房源链接")

        try:
            import webbrowser
            webbrowser.open(url)
            print(f"\n🌐 已为你打开浏览器: {url}")
            print("   在浏览器中登录/搜索完成后，按回车继续抓取...")
            input()
            html = fetch_page(url)
            if html:
                _parse_and_save(html, "58同城")
            else:
                print("❌ 抓取失败")
        except Exception as e:
            print(f"浏览器打开失败: {e}")

def _parse_and_save(html, source):
    listings = []
    blocks = re.findall(r'<li[^>]*class="clear"[^>]*>(.*?)</li>', html, re.S)
    for block in blocks[:20]:
        try:
            title_m = re.search(r'title="([^"]{4,80})"', block)
            price_m = re.search(r'(\d+(?:\.\d+)?)\s*<span[^>]*>万', block)
            unit_m = re.search(r'(\d{3,6})\s*<span[^>]*>元/㎡', block)
            room_m = re.search(r'(\d+)室(\d+)厅', block)
            area_m = re.search(r'(\d+(?:\.\d+)?)\s*㎡', block)
            if title_m:
                listings.append({
                    "id": f"H{len(listings)+1:03d}",
                    "name": title_m.group(1)[:40],
                    "price_wan": float(price_m.group(1)) if price_m else 0,
                    "unit_price": int(unit_m.group(1)) if unit_m else 0,
                    "room_type": f"{room_m.group(1)}室{room_m.group(2)}厅" if room_m else "",
                    "area": float(area_m.group(1)) if area_m else 0,
                    "source": source,
                    "status": "待看房",
                    "created_at": datetime.now().isoformat(),
                })
        except Exception:
            continue

    if listings:
        existing = load_listings()
        existing.extend(listings)
        save_listings(existing)
        print(f"\n✅ 抓取到 {len(listings)} 条房源，已保存")
    else:
        print("\n⚠️ 未能解析出房源数据，可能页面结构已变化")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="交互式网页抓取（买房版）")
    parser.add_argument("--platform", choices=['贝壳','链家','58','58同城','安居客'], required=True)
    parser.add_argument("--city", default="北京")
    parser.add_argument("--area")
    parser.add_argument("--budget-min", type=float)
    parser.add_argument("--budget-max", type=float)
    args = parser.parse_args()
    crawl_interactive(args)
