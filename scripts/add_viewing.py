#!/usr/bin/env python3
"""
记录看房信息（买房版）
用法: python add_viewing.py --id H001 --lighting 4 --noise 3 --condition 5 --consider
"""

import json
import os
import argparse
from datetime import datetime

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/home-buyer-data")
LISTINGS_FILE = os.path.join(DATA_DIR, "listings.json")
VIEWINGS_FILE = os.path.join(DATA_DIR, "viewings.json")

def load_listings():
    if not os.path.exists(LISTINGS_FILE):
        return []
    with open(LISTINGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_viewings():
    if not os.path.exists(VIEWINGS_FILE):
        return []
    with open(VIEWINGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_viewings(viewings):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    with open(VIEWINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(viewings, f, ensure_ascii=False, indent=2)

def add_viewing(args):
    listings = load_listings()
    viewings = load_viewings()

    listing = next((l for l in listings if l.get("id") == args.id), None)
    if not listing:
        print(f"未找到房源: {args.id}")
        return

    new_id = f"V{len(viewings) + 1:03d}"
    viewing = {
        "id": new_id,
        "listing_id": args.id,
        "listing_name": listing.get("name", ""),
        "viewing_time": args.time or datetime.now().isoformat(),
        "description_match": args.accurate,
        "lighting": args.lighting,
        "ventilation": args.ventilation,
        "noise": args.noise,
        "condition": args.condition,
        "layout": args.layout,
        "parking": args.parking,
        "school": args.school,
        "landlord_attitude": args.landlord,
        "tax_detail": args.tax_detail or "",
        "pros": args.pros or "",
        "cons": args.cons or "",
        "overall_score": args.score,
        "consider_signing": args.consider,
        "notes": args.notes or "",
        "created_at": datetime.now().isoformat(),
    }

    viewings.append(viewing)
    save_viewings(viewings)

    # 更新房源状态
    listing["status"] = "已看房"
    with open(LISTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(listings, f, ensure_ascii=False, indent=2)

    print(f"✅ 看房记录已保存！ID: {new_id}")
    print(f"\n📋 看房总结：")
    print(f"房源: {listing.get('name', '')}")
    print(f"整体评分: {args.score}/10")

    scores = [args.lighting, args.ventilation, args.noise, args.condition, args.layout, args.parking, args.school]
    valid = [s for s in scores if s]
    avg_score = sum(valid) / len(valid) if valid else 0
    print(f"各项平均分: {avg_score:.1f}/5")

    if args.consider:
        print("🟢 考虑签约")
    else:
        print("🔴 暂不考虑")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="记录看房信息（买房版）")
    parser.add_argument("--id", required=True, help="房源ID")
    parser.add_argument("--time", help="看房时间")
    parser.add_argument("--accurate", choices=["true", "false"], help="描述是否属实")
    parser.add_argument("--lighting", type=int, choices=range(1, 6), help="采光评分(1-5)")
    parser.add_argument("--ventilation", type=int, choices=range(1, 6), help="通风评分(1-5)")
    parser.add_argument("--noise", type=int, choices=range(1, 6), help="噪音评分(1-5)")
    parser.add_argument("--condition", type=int, choices=range(1, 6), help="房屋保养状况(1-5)")
    parser.add_argument("--layout", type=int, choices=range(1, 6), help="户型合理性(1-5)")
    parser.add_argument("--parking", type=int, choices=range(1, 6), help="车位便利性(1-5)")
    parser.add_argument("--school", type=int, choices=range(1, 6), help="学区配套(1-5)")
    parser.add_argument("--landlord", help="中介/房东态度")
    parser.add_argument("--tax-detail", help="税费/中介费明细")
    parser.add_argument("--pros", help="优点")
    parser.add_argument("--cons", help="缺点")
    parser.add_argument("--score", type=int, choices=range(1, 11), help="整体评分(1-10)")
    parser.add_argument("--consider", action="store_true", help="是否考虑签约")
    parser.add_argument("--notes", help="其他备注")
    args = parser.parse_args()
    add_viewing(args)
