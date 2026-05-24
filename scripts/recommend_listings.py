#!/usr/bin/env python3
"""
智能推荐房源（买房版）
用法: python recommend_listings.py --location "公司地址" --budget 500 --room-type "2室" --school-district "XX小学"
"""

import json
import os
import re
import argparse

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/home-buyer-data")
DATA_FILE = os.path.join(DATA_DIR, "listings.json")

def load_listings():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_match_score(listing, args):
    """计算房源匹配度评分"""
    score = 0
    reasons = []

    # 1. 总价匹配（权重35）
    price = listing.get("price_wan", 0)
    if args.budget_min is not None and args.budget_max is not None:
        if args.budget_min <= price <= args.budget_max:
            score += 35
            reasons.append(f"✅ 总价在预算区间({price}万)")
        elif price < args.budget_min * 0.85:
            score += 15
            reasons.append(f"💚 总价低于预算({price}万)")
        elif price > args.budget_max * 1.1:
            score -= 25
            reasons.append(f"❌ 超出预算({price}万)")
        elif price > args.budget_max:
            score += 10
            reasons.append(f"⚠️ 略超预算({price}万)")
    elif args.budget:
        if price <= args.budget:
            score += 35
            reasons.append(f"✅ 总价在预算内({price}万)")
        elif price <= args.budget * 1.1:
            score += 15
            reasons.append(f"⚠️ 略超预算({price}万)")
        else:
            score -= 25
            reasons.append(f"❌ 超出预算({price}万)")

    # 2. 户型匹配（权重20）
    if args.room_type:
        room = listing.get("room_type", "")
        if args.room_type in room:
            score += 20
            reasons.append(f"🏢 户型匹配({room})")
        else:
            score -= 10
            reasons.append(f"🏢 户型不符({room})")

    # 3. 面积匹配（权重10）
    if args.area_min or args.area_max:
        area = listing.get("area", 0)
        if args.area_min and area < args.area_min:
            score -= 5
            reasons.append(f"📐 面积偏小({area}㎡)")
        if args.area_max and area > args.area_max:
            score -= 5
            reasons.append(f"📐 面积偏大({area}㎡)")
        if area and (args.area_min or 0) <= area <= (args.area_max or 9999):
            score += 10
            reasons.append(f"📐 面积合适({area}㎡)")

    # 4. 学区匹配（权重15）
    if args.school_district:
        school = listing.get("school_district", "")
        if args.school_district in school:
            score += 15
            reasons.append(f"📚 学区匹配({school})")

    # 5. 房龄匹配（权重10）
    if args.max_age is not None:
        age = listing.get("building_age", 0)
        if age and age <= args.max_age:
            score += 10
            reasons.append(f"🏗️ 房龄符合({age}年)")
        elif age:
            score -= 5
            reasons.append(f"🏗️ 房龄偏老({age}年)")

    # 6. 满五唯一（权重5）
    if listing.get("is_full5_unique"):
        score += 5
        reasons.append("✅ 满五唯一税费低")

    # 7. 通勤时间（权重15）
    if args.company:
        transport = listing.get("transport", "")
        commute_match = re.search(r'(\d+)\s*分钟', transport)
        if commute_match:
            commute = int(commute_match.group(1))
            if commute <= args.max_commute:
                score += 15
                reasons.append(f"🚇 通勤{commute}分钟")
            elif commute <= args.max_commute + 15:
                score += 5
                reasons.append(f"⚠️ 通勤{commute}分钟，略超预期")

    return score, reasons

def recommend_listings(args):
    listings = load_listings()
    if not listings:
        print("暂无房源记录，请先添加房源")
        return

    scored = []
    for l in listings:
        score, reasons = calculate_match_score(l, args)
        scored.append({"listing": l, "score": score, "reasons": reasons})
    scored.sort(key=lambda x: x["score"], reverse=True)

    matched = [s for s in scored if s["score"] > 0]
    pool = matched if matched else scored[:5]

    print(f"\n🎯 找到 {len(pool)} 套匹配房源（按综合评分排序）：")
    print("=" * 60)

    for i, item in enumerate(pool[:8], 1):
        l = item["listing"]
        print(f"\n【#{i}】{l.get('name', '')}  ⭐ {item['score']}分")
        print(f"   总价: {l.get('price_wan', 0)}万  单价: {l.get('unit_price', '-')}元/㎡")
        print(f"   户型: {l.get('room_type', '-')}  面积: {l.get('area', 0)}㎡")
        print(f"   房龄: {l.get('building_age', '?')}年  朝向: {l.get('orientation', '-')}")
        print(f"   学区: {l.get('school_district', '-')}")
        print(f"   交通: {l.get('transport', '-')}")
        print(f"   税费: {l.get('tax_estimate', 0)}万  满五唯一: {'是' if l.get('is_full5_unique') else '否'}")
        print(f"   匹配: {'; '.join(item['reasons'][:6])}")
        if l.get("pros"):
            print(f"   优点: {l.get('pros')[:80]}")
        if l.get("cons"):
            print(f"   缺点: {l.get('cons')[:80]}")
        print(f"   链接: {l.get('url', '-')}")

    if len(pool) > 8:
        print(f"\n... 还有 {len(pool)-8} 条匹配结果")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="智能推荐房源（买房版）")
    parser.add_argument("--location", help="目标位置")
    parser.add_argument("--budget", type=float, help="总价上限（万元）")
    parser.add_argument("--budget-min", type=float, help="最低总价（万元）")
    parser.add_argument("--budget-max", type=float, help="最高总价（万元）")
    parser.add_argument("--room-type", help="户型要求（如 2室、3室2厅）")
    parser.add_argument("--area-min", type=float, help="最小面积（㎡）")
    parser.add_argument("--area-max", type=float, help="最大面积（㎡）")
    parser.add_argument("--school-district", help="学区要求")
    parser.add_argument("--max-age", type=int, help="最大房龄（年）")
    parser.add_argument("--company", help="公司地址（估算通勤）")
    parser.add_argument("--max-commute", type=int, default=45, help="最大通勤时间（分钟），默认45")
    args = parser.parse_args()
    recommend_listings(args)
