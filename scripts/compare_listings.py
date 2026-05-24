#!/usr/bin/env python3
"""
生成房源对比表格（买房版）
用法: python compare_listings.py --ids H001 H002 H003 [--format markdown|feishu] [--company "公司地址"]
"""

import json
import os
import argparse
import re

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/home-buyer-data")
LISTINGS_FILE = os.path.join(DATA_DIR, "listings.json")
VIEWINGS_FILE = os.path.join(DATA_DIR, "viewings.json")

def load_listings():
    """加载买房房源数据"""
    if not os.path.exists(LISTINGS_FILE):
        return []
    with open(LISTINGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_viewings():
    if not os.path.exists(VIEWINGS_FILE):
        return []
    with open(VIEWINGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_value(value, max_len=20):
    if not value or value == "-":
        return "-"
    value = str(value).replace('\n', ' ').replace('|', '｜')
    if len(value) > max_len:
        return value[:max_len-1] + "…"
    return value

def get_cell_width(text, min_width=12):
    width = 0
    for char in str(text):
        if ord(char) > 127:
            width += 2
        else:
            width += 1
    return max(width, min_width)

def print_markdown_table(headers, rows):
    col_widths = []
    for i, header in enumerate(headers):
        width = get_cell_width(header)
        for row in rows:
            if i < len(row):
                width = max(width, get_cell_width(row[i]))
        col_widths.append(width + 2)

    header_line = "|"
    for i, header in enumerate(headers):
        header_line += f" {header:<{col_widths[i]-2}} |"
    print(header_line)

    sep_line = "|"
    for width in col_widths:
        sep_line += "-" * width + "|"
    print(sep_line)

    for row in rows:
        row_line = "|"
        for i, cell in enumerate(row):
            if i < len(col_widths):
                cell_str = str(cell)
                cell_width = get_cell_width(cell_str)
                padding = col_widths[i] - cell_width - 2
                row_line += f" {cell_str}{' ' * padding} |"
        print(row_line)

def analyze_listing(listing, all_listings, company_location=None):
    """智能分析房源优缺点"""
    pros = []
    cons = []

    # 1. 价格分析
    prices = [l.get("price_wan", 0) for l in all_listings if l.get("price_wan", 0) > 0]
    if prices:
        avg_price = sum(prices) / len(prices)
        price = listing.get("price_wan", 0)
        if price < avg_price * 0.9:
            pros.append(f"💰 总价低于平均{((avg_price-price)/avg_price*100):.0f}%")
        elif price > avg_price * 1.1:
            cons.append(f"💰 总价高于平均{((price-avg_price)/avg_price*100):.0f}%")

    # 单价分析
    unit_prices = [l.get("unit_price", 0) for l in all_listings if l.get("unit_price", 0) > 0]
    if unit_prices:
        avg_unit = sum(unit_prices) / len(unit_prices)
        unit = listing.get("unit_price", 0)
        if unit and unit < avg_unit * 0.9:
            pros.append(f"💵 单价低于均价{((avg_unit-unit)/avg_unit*100):.0f}%")
        elif unit and unit > avg_unit * 1.1:
            cons.append(f"💵 单价高于均价{((unit-avg_unit)/avg_unit*100):.0f}%")

    # 2. 面积分析
    areas = [l.get("area", 0) for l in all_listings if l.get("area", 0) > 0]
    if areas:
        avg_area = sum(areas) / len(areas)
        area = listing.get("area", 0)
        if area > avg_area * 1.15:
            pros.append(f"📐 面积超平均{(area-avg_area):.0f}㎡")
        elif area < avg_area * 0.85:
            cons.append(f"📐 面积比平均小{(avg_area-area):.0f}㎡")

    # 3. 房龄分析
    age = listing.get("building_age", 0)
    if age:
        if age <= 5:
            pros.append(f"🏗️ 房龄仅{age}年，次新房")
        elif age >= 20:
            cons.append(f"🏗️ 房龄{age}年，房龄较老")

    # 4. 满五唯一
    if listing.get("is_full5_unique"):
        pros.append("✅ 满五唯一，税费极低")

    # 5. 朝向分析
    orientation = listing.get("orientation", "")
    if "南北" in orientation:
        pros.append("☀️ 南北通透")
    elif "南" in orientation:
        pros.append("☀️ 朝南采光好")
    elif "北" in orientation:
        cons.append("🌑 朝北，采光偏弱")

    # 6. 电梯
    if listing.get("has_elevator") and listing.get("floor", ""):
        floor_match = re.search(r"(\d+)", str(listing.get("floor", "")))
        if floor_match and int(floor_match.group(1)) >= 10:
            pros.append("🛗 高层有电梯")
    elif not listing.get("has_elevator") and listing.get("floor", ""):
        floor_match = re.search(r"(\d+)", str(listing.get("floor", "")))
        if floor_match and int(floor_match.group(1)) >= 5:
            cons.append("🏃 楼层较高无电梯")

    # 7. 装修
    decoration = listing.get("decoration", "")
    if "精装" in decoration:
        pros.append("✨ 精装修，可拎包入住")
    elif "简装" in decoration or "毛坯" in decoration:
        cons.append("🔧 装修一般，需二次投入")

    # 8. 学位
    if listing.get("school_district"):
        school_notes = listing.get("school_notes", "")
        if "未占用" in school_notes or "空置" in school_notes:
            pros.append(f"📚 学位可用（{listing.get('school_district')}）")
        elif "占用" in school_notes:
            cons.append(f"📚 学位被占用（{listing.get('school_district')}）")

    # 9. 车位
    parking = listing.get("has_parking", "")
    if "有" in parking:
        pros.append("🚗 有车位")
    elif "无" in parking:
        cons.append("🚗 无固定车位")

    # 10. 通勤分析（如果提供了公司地址）
    if company_location:
        transport = listing.get("transport", "")
        time_match = re.search(r'(\d+)分钟', transport)
        if time_match:
            commute = int(time_match.group(1))
            if commute <= 20:
                pros.append(f"🚇 通勤{commute}分钟，非常方便")
            elif commute <= 40:
                pros.append(f"🚇 通勤{commute}分钟，可接受")
            elif commute > 60:
                cons.append(f"🚇 通勤{commute}分钟，偏远")

    return pros, cons

def compare_listings(args):
    listings = load_listings()
    viewings = load_viewings()

    if not args.ids:
        print("请指定要对比的房源ID，如：--ids H001 H002 H003")
        return

    selected = []
    for id in args.ids:
        listing = next((l for l in listings if l.get("id") == id), None)
        if not listing:
            print(f"⚠️ 未找到房源: {id}")
            continue

        listing_viewings = [v for v in viewings if v.get("listing_id") == id]
        if listing_viewings:
            latest = max(listing_viewings, key=lambda x: x.get("viewing_time", ""))
            listing["viewing_score"] = latest.get("overall_score", "-")
            listing["viewing_consider"] = latest.get("consider_signing", False)
        else:
            listing["viewing_score"] = "-"
            listing["viewing_consider"] = False

        listing["_pros"], listing["_cons"] = analyze_listing(listing, selected + [listing], args.company)
        selected.append(listing)

    if len(selected) < 2:
        print("至少需要2个房源才能对比")
        return

    fmt = args.format or "markdown"

    if fmt == "markdown":
        print("\n" + "=" * 75)
        print("🏠 房源对比表")
        print("=" * 75)

        headers = ["对比项"] + [format_value(l.get("name", l.get("id", "")), 18) for l in selected]

        def price_breakdown(l):
            down = l.get("price_wan", 0) * 0.3
            loan = l.get("price_wan", 0) * 0.7
            monthly = round(loan * 10000 * (3.1/100/12) * (1+3.1/100/12)**360 / ((1+3.1/100/12)**360-1), 0)
            return f"{l.get('price_wan', 0)}万(首{down:.0f}/月供{monthly:.0f})"

        rows = [
            ["💰 总价(首付/月供)"] + [price_breakdown(l) for l in selected],
            ["💵 单价"] + [f"{l.get('unit_price', 0)}元/㎡" if l.get("unit_price") else "-" for l in selected],
            ["🏢 户型"] + [format_value(l.get("room_type", "-")) for l in selected],
            ["📐 面积"] + [f"{l.get('area', 0)}㎡ / {l.get('inner_area', '') or '?'}㎡" for l in selected],
            ["🏗️ 房龄"] + [f"{l.get('building_age', '?')}年({l.get('year_built', '')})" for l in selected],
            ["🔢 楼层"] + [format_value(f"{l.get('floor','')}/{l.get('total_floors','')}层  {'有电梯' if l.get('has_elevator') else '无电梯'}") for l in selected],
            ["🧭 朝向"] + [format_value(l.get("orientation", "-")) for l in selected],
            ["✨ 装修"] + [format_value(l.get("decoration", "-")) for l in selected],
            ["📋 产权"] + [format_value(f"{l.get('property_type','')} {l.get('house_type','')} {'满五唯一' if l.get('is_full5_unique') else ''}") for l in selected],
            ["🏫 学区"] + [format_value(l.get("school_district", "-"), 18) for l in selected],
            ["🚇 交通"] + [format_value(l.get("transport", "-"), 25) for l in selected],
            ["🏪 配套"] + [format_value(l.get("facilities", "-"), 25) for l in selected],
            ["💳 税费估算"] + [f"{l.get('tax_estimate', 0)}万" for l in selected],
            ["🔗 链接"] + [format_value(l.get("url", "-"), 25) for l in selected],
            ["⭐ 看房评分"] + [f"{l.get('viewing_score')}分{' 🟢' if l.get('viewing_consider') else ''}" for l in selected],
            ["📊 状态"] + [format_value(l.get("status", "-")) for l in selected],
        ]

        print_markdown_table(headers, rows)

        # 智能分析
        print("\n" + "=" * 75)
        print("🎯 智能分析")
        print("=" * 75)
        for listing in selected:
            print(f"\n【{listing.get('name')}】")
            for pro in listing["_pros"][:6]:
                print(f"  ✅ {pro}")
            for con in listing["_cons"][:4]:
                print(f"  ❌ {con}")
            if not listing["_pros"] and not listing["_cons"]:
                print("  ℹ️ 暂无自动分析（可以补充更多房源后再对比）")

        # 推荐排序
        print("\n" + "=" * 75)
        print("🏆 综合推荐")
        print("=" * 75)
        for i, listing in enumerate(selected, 1):
            score = len(listing["_pros"]) - len(listing["_cons"]) * 0.5
            if listing.get("viewing_score") and listing.get("viewing_score") != "-":
                score += int(listing["viewing_score"]) * 0.5
            print(f"  #{i} {listing.get('name')}: 综合分 {score:.1f} ({len(listing['_pros'])}优 {len(listing['_cons'])}缺)")

        print("=" * 75)
    else:
        # Feishu CSV 格式
        print("\n飞书多维表格格式（可复制粘贴）：\n")
        print("名称,总价(万),单价(元/㎡),户型,面积(㎡),房龄,朝向,装修,满五唯一,学区,税费(万),看房评分,推荐分,智能优点,智能缺点")
        for listing in selected:
            score = len(listing["_pros"]) - len(listing["_cons"]) * 0.5
            pros = ";".join(listing["_pros"][:4])
            cons = ";".join(listing["_cons"][:3])
            row = [
                listing.get("name", ""),
                str(listing.get("price_wan", "")),
                str(listing.get("unit_price", "")),
                listing.get("room_type", ""),
                str(listing.get("area", "")),
                str(listing.get("building_age", "")),
                listing.get("orientation", ""),
                listing.get("decoration", ""),
                "是" if listing.get("is_full5_unique") else "否",
                listing.get("school_district", ""),
                str(listing.get("tax_estimate", "")),
                str(listing.get("viewing_score", "")),
                f"{score:.1f}",
                pros,
                cons,
            ]
            print(",".join(row))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成房源对比表（买房版）")
    parser.add_argument("--ids", nargs="+", required=True, help="要对比的房源ID，如 H001 H002 H003")
    parser.add_argument("--format", choices=["markdown", "feishu"], default="markdown")
    parser.add_argument("--company", help="公司地址（用于通勤分析）")
    args = parser.parse_args()
    compare_listings(args)
