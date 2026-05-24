#!/usr/bin/env python3
"""
从各大买房网站抓取房源信息（买房版）
用法: python crawl_listings.py --platform 贝壳 --city 北京 --area 朝阳区 --budget-min 300 --budget-max 800

支持平台：
- 贝壳找房 (ke.com)
- 链家 (lianjia.com)
- 58同城 (58.com)
- 安居客 (anjuke.com)
"""

import json
import os
import re
import ssl
import argparse
import urllib.request
from datetime import datetime
from urllib.parse import quote

ssl._create_default_https_context = ssl._create_unverified_context

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
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
        h = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
             'Accept': 'text/html,application/xhtml+xml,*/*;q=0.1'}
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  获取页面失败: {e}")
        return None

def clean(text):
    return re.sub(r'<[^>]+>', ' ', text).strip()

def parse_budget_filter(args):
    """生成价格筛选参数"""
    if args.budget_min is not None and args.budget_max is not None:
        return f"p{args.budget_min}ep{args.budget_max}"
    elif args.budget_max:
        return f"p{args.budget_max}"
    return ""

def crawl_ke(args):
    """抓取贝壳找房"""
    listings = []
    city_codes = {'北京':'bj','上海':'sh','广州':'gz','深圳':'sz','杭州':'hz',
                  '南京':'nj','成都':'cd','武汉':'wh','西安':'xa','重庆':'cq'}
    code = city_codes.get(args.city, 'bj')
    budget_filter = parse_budget_filter(args)
    base = f"https://{code}.ke.com/ershoufang"
    path = f"/{quote(args.area.encode('utf-8'))}" if args.area else ""
    url = f"{base}{path}/{budget_filter}/" if budget_filter else f"{base}{path}/"

    print(f"  抓取: {url}")
    html = fetch_page(url)
    if not html:
        return listings

    # 匹配每条房源卡
    blocks = re.findall(r'<li[^>]*class="clear"[^>]*>(.*?)</li>', html, re.S)
    if not blocks:
        # 尝试匹配 info clear 或通用模式
        blocks = re.split(r'<div[^>]*class="info clear"[^>]*>', html)

    for block in blocks[:args.limit]:
        try:
            title_m = re.search(r'title="([^"]{4,80})"', block)
            if not title_m:
                continue
            name = title_m.group(1).strip()

            price_total_m = re.search(r'(\d+(?:\.\d+)?)\s*<span[^>]*>万', block)
            price_unit_m = re.search(r'(\d{3,5,6})\s*<span[^>]*>元/㎡', block)
            room_m = re.search(r'(\d+)室(\d+)厅', block)
            area_m = re.search(r'(\d+(?:\.\d+)?)\s*㎡', block)
            orient_m = re.search(r'朝\s*(\S+)', block)
            floor_m = re.search(r'(\d+)\s*层\s*/\s*(\d+)\s*层', block)
            year_m = re.search(r'(\d{4})\s*年', block)

            listing = {
                "id": f"H{len(listings)+1:03d}",
                "name": name[:40],
                "price_wan": float(price_total_m.group(1)) if price_total_m else 0,
                "unit_price": int(price_unit_m.group(1)) if price_unit_m else 0,
                "room_type": f"{room_m.group(1)}室{room_m.group(2)}厅" if room_m else "",
                "area": float(area_m.group(1)) if area_m else 0,
                "orientation": orient_m.group(1) if orient_m else "",
                "floor": f"{floor_m.group(1)}/{floor_m.group(2)}层" if floor_m else "",
                "year_built": year_m.group(1) if year_m else "",
                "building_age": datetime.now().year - int(year_m.group(1)) if year_m else 0,
                "source": "贝壳找房",
                "url": f"https://{code}.ke.com" + (re.search(r'href="(/ershoufang/\d+\.html)"', block).group(1) if re.search(r'href="(/ershoufang/\d+\.html)"', block) else ""),
                "status": "待看房",
                "created_at": datetime.now().isoformat(),
            }
            listings.append(listing)
        except Exception:
            continue
    return listings

def crawl_lianjia(args):
    """链家与贝壳同源，复用"""
    return crawl_ke(args)

def crawl_58(args):
    """抓取58同城二手房"""
    listings = []
    city_map = {'北京':'bj','上海':'sh','广州':'gz','深圳':'sz','成都':'cd'}
    code = city_map.get(args.city, 'bj')
    area_enc = quote(args.area.encode('utf-8')) if args.area else ''
    url = f"https://{code}.58.com/ershoufang/?key={area_enc}"

    print(f"  抓取: {url}")
    html = fetch_page(url)
    if not html:
        return listings

    blocks = re.findall(r'<li[^>]*class="property"[^>]*>(.*?)</li>', html, re.S)
    for block in blocks[:args.limit]:
        try:
            title_m = re.search(r'<h2[^>]*>.*?<a[^>]*>([^<]+)</a>', block, re.S)
            if not title_m:
                continue
            price_m = re.search(r'(\d+(?:\.\d+)?)\s*万', block)
            unit_m = re.search(r'(\d+)\s*元/㎡', block)
            listings.append({
                "id": f"H{len(listings)+1:03d}",
                "name": title_m.group(1).strip()[:40],
                "price_wan": float(price_m.group(1)) if price_m else 0,
                "unit_price": int(unit_m.group(1)) if unit_m else 0,
                "source": "58同城",
                "status": "待看房",
                "created_at": datetime.now().isoformat(),
            })
        except Exception:
            continue
    return listings

def crawl_anjuke(args):
    """抓取安居客"""
    listings = []
    city_map = {'北京':'beijing','上海':'shanghai','广州':'guangzhou','深圳':'shenzhen'}
    code = city_map.get(args.city, 'beijing')
    url = f"https://{code}.fang.anjuke.com/"

    if args.area:
        url += f"?kw={quote(args.area.encode('utf-8'))}"

    print(f"  抓取: {url}")
    html = fetch_page(url)
    if not html:
        return listings

    blocks = re.findall(r'<h3[^>]*>.*?<a[^>]*>([^<]+)</a>.*?</h3>', html, re.S)
    for i, title in enumerate(blocks[:args.limit]):
        price_m = re.search(r'(\d+(?:\.\d+)?)\s*万', html)
        listings.append({
            "id": f"H{len(listings)+1:03d}",
            "name": title.strip()[:40],
            "price_wan": float(price_m.group(1)) if price_m else 0,
            "source": "安居客",
            "status": "待看房",
            "created_at": datetime.now().isoformat(),
        })
    return listings

def crawl_listings(args):
    all_listings = []
    crawlers = {
        '贝壳': crawl_ke,
        '链家': crawl_lianjia,
        '58同城': crawl_58,
        '安居客': crawl_anjuke,
    }

    targets = [args.platform] if args.platform else list(crawlers.keys())
    for p in targets:
        fn = crawlers.get(p)
        if not fn:
            continue
        print(f"\n🔍 正在抓取 {p}...")
        result = fn(args)
        print(f"  ✅ {p}: {len(result)} 条")
        all_listings.extend(result)

    if not all_listings:
        print("\n⚠️ 未抓取到房源，可能被反爬限制。建议：")
        print("   1. 用 parse_url.py 手动解析具体房源链接")
        print("   2. 用 crawl_interactive.py 交互式抓取（支持扫码登录）")
        return

    # 去重
    seen = set()
    unique = []
    for l in all_listings:
        if l.get('url') and l['url'] not in seen:
            seen.add(l['url'])
            unique.append(l)
        elif not l.get('url'):
            unique.append(l)

    print(f"\n📊 汇总: {len(unique)} 条去重房源")
    for l in unique[:10]:
        print(f"  [{l['id']}] {l.get('name',''):20} {l.get('price_wan',0)}万  {l.get('room_type','')}  {l.get('area',0)}㎡")
    if len(unique) > 10:
        print(f"  ... 还有 {len(unique)-10} 条")

    if args.save:
        existing = load_listings()
        existing.extend(unique)
        save_listings(existing)
        print(f"\n✅ 已保存 {len(unique)} 条到数据库")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="抓取买房网站房源")
    p.add_argument("--platform", choices=['贝壳','链家','58同城','安居客'])
    p.add_argument("--city", default="北京")
    p.add_argument("--area")
    p.add_argument("--budget-min", type=float)
    p.add_argument("--budget-max", type=float)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--save", action="store_true")
    args = p.parse_args()
    crawl_listings(args)
