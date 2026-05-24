#!/usr/bin/env python3
"""
从网页链接解析房源信息（买房版）
用法: python parse_url.py --url "https://..." [--source 贝壳|链家|安居客|58]

支持的平台：
- 贝壳找房 (ke.com)
- 链家 (lianjia.com)
- 安居客 (anjuke.com)
- 58同城 (58.com)
"""

import json
import os
import re
import argparse
import urllib.request
from datetime import datetime

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

def fetch_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"获取页面失败: {e}")
        return None

def extract_clean(text):
    return re.sub(r'<[^>]+>', '', text).strip()

def parse_ke_lianjia(html, url):
    info = {"source": "贝壳找房" if "ke.com" in url else "链家", "url": url}

    title_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
    if title_m:
        info["name"] = extract_clean(title_m.group(1)).split()[0]

    # 总价（万元） - 贝壳买房页面
    price_m = re.search(r'(\d+(?:\.\d+)?)\s*万', html)
    if not price_m:
        price_m = re.search(r'price[^>]*>(\d+(?:\.\d+)?)<', html, re.I)
    if price_m:
        info["price_wan"] = float(price_m.group(1))

    # 单价
    unit_m = re.search(r'(\d+(?:\.\d+)?)\s*元/㎡', html)
    if unit_m:
        info["unit_price"] = float(unit_m.group(1))

    # 户型
    room_m = re.search(r'(\d+)室(\d+)厅', html)
    if room_m:
        info["room_type"] = f"{room_m.group(1)}室{room_m.group(2)}厅"

    # 面积
    area_m = re.search(r'(\d+(?:\.\d+)?)\s*㎡', html)
    if area_m:
        info["area"] = float(area_m.group(1))

    # 朝向
    orient_m = re.search(r'朝\s*<[^>]*>?(\S+?)<', html)
    if orient_m:
        info["orientation"] = extract_clean(orient_m.group(1))

    # 楼层
    floor_m = re.search(r'(\d+)\s*层\s*/\s*共?\s*(\d+)\s*层', html)
    if floor_m:
        info["floor"] = f"{floor_m.group(1)}/{floor_m.group(2)}层"

    # 建筑年代
    year_m = re.search(r'(\d{4})\s*年', html)
    if year_m:
        info["year_built"] = year_m.group(1)
        info["building_age"] = datetime.now().year - int(year_m.group(1))

    # 装修
    deco_m = re.search(r'(精装|简装|毛坯|豪装)', html)
    if deco_m:
        info["decoration"] = deco_m.group(1)

    # 交通
    transport_m = re.search(r'(距地铁[\u4e00-\u9fa5\d]+站\d+米[^<]*)', html)
    if transport_m:
        info["transport"] = transport_m.group(1).strip()

    return info

def parse_generic(html, url):
    info = {"source": "通用网页", "url": url}
    title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S | re.I)
    if title_m:
        info["name"] = extract_clean(title_m.group(1))[:50]

    for pat, key, fmt in [
        (r'(\d+(?:\.\d+)?)\s*万', 'price_wan', float),
        (r'(\d+(?:\.\d+)?)\s*元/㎡', 'unit_price', float),
        (r'(\d+)室(\d+)厅', 'room_type', lambda m: f"{m.group(1)}室{m.group(2)}厅"),
        (r'(\d+(?:\.\d+)?)\s*㎡', 'area', float),
    ]:
        m = re.search(pat, html)
        if m:
            info[key] = fmt(m) if callable(fmt) else m.group(1)
    return info

def parse_url(url):
    html = fetch_page(url)
    if not html:
        return None
    if "ke.com" in url or "lianjia.com" in url:
        return parse_ke_lianjia(html, url)
    return parse_generic(html, url)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从网页链接解析房源（买房版）")
    parser.add_argument("--url", required=True, help="房源链接")
    parser.add_argument("--source", help="手动指定来源")
    args = parser.parse_args()

    info = parse_url(args.url)
    if info:
        if args.source:
            info["source"] = args.source

        listings = load_listings()
        new_id = f"H{len(listings)+1:03d}"
        info["id"] = new_id
        info["status"] = "待看房"
        info["created_at"] = datetime.now().isoformat()

        listings.append(info)
        save_listings(listings)

        print(f"✅ 解析成功！已保存为房源 ID: {new_id}")
        for k, v in info.items():
            if k != "id":
                print(f"   {k}: {v}")
    else:
        print("❌ 解析失败")
