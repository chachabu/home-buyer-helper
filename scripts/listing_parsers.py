#!/usr/bin/env python3
"""Shared listing fetch, parse, and storage helpers."""

import json
import os
import re
import ssl
import urllib.request
from datetime import datetime
from html import unescape
from urllib.parse import urljoin


SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_DIR, "data")
LISTINGS_FILE = os.path.join(DATA_DIR, "listings.json")

CITY_CODES = {
    "北京": "bj",
    "上海": "sh",
    "广州": "gz",
    "深圳": "sz",
    "杭州": "hz",
    "南京": "nj",
    "成都": "cd",
    "武汉": "wh",
    "西安": "xa",
    "重庆": "cq",
}

BEIKE_AREA_SLUGS = {
    "北京": {
        "东城": "dongchengqu",
        "东城区": "dongchengqu",
        "西城": "xichengqu3",
        "西城区": "xichengqu3",
        "朝阳": "chaoyangqu5",
        "朝阳区": "chaoyangqu5",
        "海淀": "haidianqu",
        "海淀区": "haidianqu",
        "丰台": "fengtaiqu",
        "丰台区": "fengtaiqu",
        "石景山": "shijingshanqu",
        "石景山区": "shijingshanqu",
        "通州": "tongzhouqu",
        "通州区": "tongzhouqu",
        "昌平": "changpingqu",
        "昌平区": "changpingqu",
        "大兴": "daxingqu",
        "大兴区": "daxingqu",
        "顺义": "shunyiqu",
        "顺义区": "shunyiqu",
        "房山": "fangshanqu",
        "房山区": "fangshanqu",
        "门头沟": "mentougouqu",
        "门头沟区": "mentougouqu",
        "亦庄开发区": "yizhuangkaifaqu",
        "亦庄": "yizhuangkaifaqu",
        "怀柔": "huairouqu",
        "怀柔区": "huairouqu",
        "密云": "miyunqu",
        "密云区": "miyunqu",
        "平谷": "pingguqu",
        "平谷区": "pingguqu",
        "延庆": "yanqingqu",
        "延庆区": "yanqingqu",
    },
    "上海": {
        "黄浦": "huangpu",
        "黄浦区": "huangpu",
        "徐汇": "xuhui",
        "徐汇区": "xuhui",
        "长宁": "changning",
        "长宁区": "changning",
        "静安": "jingan",
        "静安区": "jingan",
        "普陀": "putuo",
        "普陀区": "putuo",
        "虹口": "hongkou",
        "虹口区": "hongkou",
        "杨浦": "yangpu",
        "杨浦区": "yangpu",
        "浦东": "pudong",
        "浦东新区": "pudong",
        "闵行": "minhang",
        "闵行区": "minhang",
        "宝山": "baoshan",
        "宝山区": "baoshan",
        "嘉定": "jiading",
        "嘉定区": "jiading",
        "松江": "songjiang",
        "松江区": "songjiang",
        "青浦": "qingpu",
        "青浦区": "qingpu",
        "奉贤": "fengxian",
        "奉贤区": "fengxian",
        "金山": "jinshan",
        "金山区": "jinshan",
        "崇明": "chongming",
        "崇明区": "chongming",
    },
}


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_listings():
    if not os.path.exists(LISTINGS_FILE):
        return []
    with open(LISTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_listings(listings):
    ensure_data_dir()
    with open(LISTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(listings, f, ensure_ascii=False, indent=2)


def fetch_page(url, headers=None, timeout=15):
    base_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.5",
        "Connection": "keep-alive",
    }
    if headers:
        base_headers.update(headers)
    req = urllib.request.Request(url, headers=base_headers)
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
        return resp.read().decode("utf-8", errors="replace"), resp.geturl()


def strip_tags(text):
    return re.sub(r"<[^>]+>", " ", text or "")


def clean_text(text):
    return re.sub(r"\s+", " ", unescape(strip_tags(text))).strip()


def parse_number(text, default=0):
    if text is None:
        return default
    m = re.search(r"\d+(?:[,.]\d+)*", str(text))
    if not m:
        return default
    raw = m.group(0).replace(",", "")
    try:
        value = float(raw)
    except ValueError:
        return default
    return int(value) if value.is_integer() else value


def price_token(value):
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number.is_integer():
        return str(int(number))
    return str(number).rstrip("0").rstrip(".")


def resolve_city_code(city):
    if city in CITY_CODES:
        return CITY_CODES[city]
    if city and re.fullmatch(r"[a-z]+", city):
        return city
    return "bj"


def resolve_beike_area_slug(city, area):
    if not area:
        return ""
    area = area.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]+", area):
        return area
    return BEIKE_AREA_SLUGS.get(city, {}).get(area, "")


def build_beike_url(city="北京", area=None, budget_min=None, budget_max=None, page=1):
    code = resolve_city_code(city)
    parts = []
    area_slug = resolve_beike_area_slug(city, area)
    if area and area_slug:
        parts.append(area_slug)
    min_token = price_token(budget_min)
    max_token = price_token(budget_max)
    if min_token and max_token:
        parts.append(f"bp{min_token}ep{max_token}")
    elif min_token:
        parts.append(f"bp{min_token}")
    elif max_token:
        parts.append(f"ep{max_token}")
    if page and page > 1:
        parts.append(f"pg{page}")
    suffix = "/".join(parts)
    return f"https://{code}.ke.com/ershoufang/{suffix + '/' if suffix else ''}"


def looks_like_blocked_page(html, final_url=""):
    sample = clean_text((html or "")[:6000])
    if final_url and "clogin.ke.com" in final_url:
        return True
    if final_url and "hip.ke.com/captcha" in final_url:
        return True
    blocked_terms = (
        "验证码",
        "请完成安全验证",
        "登录",
        "clogin.ke.com",
        "ke-passport",
        "CAPTCHA",
        "Captcha",
        "captcha",
    )
    return any(term in sample for term in blocked_terms) and "sellListContent" not in html


def extract_div_by_class(block, class_name):
    pattern = rf'<div[^>]*class="[^"]*\b{re.escape(class_name)}\b[^"]*"[^>]*>(.*?)</div>'
    m = re.search(pattern, block, re.S)
    return m.group(1) if m else ""


def extract_first(patterns, text, flags=re.S):
    for pattern in patterns:
        m = re.search(pattern, text, flags)
        if m:
            return m.group(1)
    return ""


def parse_house_info(house_info):
    text = clean_text(house_info)
    parts = [p.strip() for p in text.split("|") if p.strip()]
    parsed = {
        "room_type": "",
        "area": 0,
        "floor": "",
        "total_floors": "",
        "orientation": "",
        "year_built": "",
        "building_age": 0,
    }
    for part in parts:
        room = re.search(r"\d+室\d+厅", part)
        if room:
            parsed["room_type"] = room.group(0)
            continue
        if "平米" in part or "㎡" in part:
            parsed["area"] = parse_number(part, 0)
            continue
        if "楼层" in part or "层" in part:
            parsed["floor"] = part
            total_m = re.search(r"共\s*(\d+)\s*层", part)
            if total_m:
                parsed["total_floors"] = total_m.group(1)
            continue
        year = re.search(r"(\d{4})\s*年", part)
        if year:
            parsed["year_built"] = year.group(1)
            parsed["building_age"] = datetime.now().year - int(year.group(1))
            continue
        if re.search(r"(东|南|西|北)", part):
            parsed["orientation"] = part
    return parsed


def parse_beike_listings_html(html, city_code="bj", source="贝壳找房", limit=None):
    blocks = re.findall(r'<li[^>]*class="[^"]*\bclear\b[^"]*"[^>]*>(.*?)</li>', html, re.S)
    listings = []
    for block in blocks:
        if limit and len(listings) >= limit:
            break
        title = extract_first(
            [
                r'<a[^>]+title="([^"]{2,120})"',
                r'<div[^>]*class="[^"]*\btitle\b[^"]*"[^>]*>\s*<a[^>]*>(.*?)</a>',
            ],
            block,
        )
        title = clean_text(title)
        detail_url = extract_first(
            [
                r'href="(https?://[^"]+/ershoufang/\d+\.html)"',
                r'href="(/ershoufang/\d+\.html)"',
            ],
            block,
        )
        if not title and not detail_url:
            continue
        if detail_url:
            detail_url = urljoin(f"https://{city_code}.ke.com", detail_url)

        total_price_text = clean_text(extract_div_by_class(block, "totalPrice"))
        unit_price_text = clean_text(extract_div_by_class(block, "unitPrice"))
        house = parse_house_info(extract_div_by_class(block, "houseInfo"))
        position_info = extract_div_by_class(block, "positionInfo")
        community = clean_text(position_info)
        if " " in community:
            community = community.split()[-1]

        listings.append({
            "community": community,
            "name": title[:80],
            "address": community,
            "price_wan": parse_number(total_price_text, 0),
            "unit_price": parse_number(unit_price_text, 0),
            "room_type": house["room_type"],
            "area": house["area"],
            "floor": house["floor"],
            "total_floors": house["total_floors"],
            "orientation": house["orientation"],
            "year_built": house["year_built"],
            "building_age": house["building_age"],
            "nearest_metro": "",
            "monthly_rent": 0,
            "rent_source": "",
            "school_tier": "",
            "is_full5_unique": "满五唯一" in block or "满五年唯一" in block,
            "source": source,
            "url": detail_url,
            "status": "待看房",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        })
    return listings


def parse_ke_lianjia_detail_html(html, url):
    source = "贝壳找房" if "ke.com" in url else "链家"
    info = {"source": source, "url": url}
    title = extract_first([r"<h1[^>]*>(.*?)</h1>", r"<title[^>]*>(.*?)</title>"], html)
    if title:
        info["name"] = clean_text(title).split("_")[0][:80]

    text = clean_text(html)
    patterns = [
        (r"(?:总价|售价)\s*(\d+(?:\.\d+)?)\s*万", "price_wan"),
        (r"单价\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*元/平", "unit_price"),
        (r"房屋户型\s*(\d+室\d+厅)", "room_type"),
        (r"建筑面积\s*(\d+(?:\.\d+)?)\s*(?:㎡|平米)", "area"),
        (r"房屋朝向\s*([东西南北 ]{1,12})", "orientation"),
        (r"所在楼层\s*([^ ]+楼层[^ ]*)", "floor"),
        (r"建成年代\s*(\d{4})\s*年", "year_built"),
        (r"装修情况\s*(精装|简装|毛坯|其他|豪装)", "decoration"),
    ]
    for pattern, key in patterns:
        m = re.search(pattern, text)
        if not m:
            continue
        value = m.group(1).strip()
        if key in ("price_wan", "unit_price", "area"):
            info[key] = parse_number(value, 0)
        else:
            info[key] = value
    if "year_built" in info:
        info["building_age"] = datetime.now().year - int(info["year_built"])
    if "满五唯一" in text or "满五年唯一" in text:
        info["is_full5_unique"] = True
    return info


def parse_generic_html(html, url):
    info = {"source": "通用网页", "url": url}
    title = extract_first([r"<title[^>]*>(.*?)</title>"], html, re.S | re.I)
    if title:
        info["name"] = clean_text(title)[:80]
    text = clean_text(html)
    patterns = [
        (r"(\d+(?:\.\d+)?)\s*万", "price_wan"),
        (r"(\d+(?:,\d+)?(?:\.\d+)?)\s*元/㎡", "unit_price"),
        (r"(\d+室\d+厅)", "room_type"),
        (r"(\d+(?:\.\d+)?)\s*(?:㎡|平米)", "area"),
    ]
    for pattern, key in patterns:
        m = re.search(pattern, text)
        if not m:
            continue
        value = m.group(1)
        info[key] = parse_number(value, 0) if key != "room_type" else value
    return info


def listing_identity(listing):
    url = listing.get("url", "")
    if re.search(r"/ershoufang/\d+\.html", url):
        return ("url", url)
    return (
        "facts",
        listing.get("source", ""),
        listing.get("community", ""),
        listing.get("name", ""),
        listing.get("price_wan", 0),
        listing.get("area", 0),
    )


def next_listing_number(existing):
    max_num = 0
    for listing in existing:
        m = re.match(r"H(\d+)$", str(listing.get("id", "")))
        if m:
            max_num = max(max_num, int(m.group(1)))
    return max_num + 1


def assign_preview_ids(listings, start=1):
    result = []
    for index, listing in enumerate(listings, start=start):
        item = dict(listing)
        item["id"] = f"H{index:03d}"
        result.append(item)
    return result


def append_unique_listings(existing, incoming):
    seen = {listing_identity(item) for item in existing}
    added = []
    next_num = next_listing_number(existing)
    for listing in incoming:
        key = listing_identity(listing)
        if key in seen:
            continue
        item = dict(listing)
        item["id"] = f"H{next_num:03d}"
        next_num += 1
        existing.append(item)
        added.append(item)
        seen.add(key)
    return added
