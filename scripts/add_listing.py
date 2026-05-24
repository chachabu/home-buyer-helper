#!/usr/bin/env python3
"""
添加新房源记录（买房版）
用法: python add_listing.py --name "小区名称" --price 500 --room-type "2室2厅" ...
"""

import json
import os
import argparse
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DATA_FILE = os.path.join(DATA_DIR, "listings.json")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_listings():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_listings(listings):
    ensure_data_dir()
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(listings, f, ensure_ascii=False, indent=2)

def add_listing(args):
    listings = load_listings()
    new_id = f"H{len(listings) + 1:03d}"

    listing = {
        "id": new_id,
        "community": args.community or "",      # 小区名
        "name": args.name,
        "address": args.address or "",
        "price_wan": args.price,           # 总价（万元）
        "unit_price": args.unit_price or 0, # 单价（元/㎡）
        "room_type": args.room_type or "",
        "area": args.area or 0,             # 建筑面积（㎡）
        "inner_area": args.inner_area or 0,  # 套内面积（㎡）
        "floor": args.floor or "",
        "total_floors": args.total_floors or "",
        "orientation": args.orientation or "",
        "year_built": args.year_built or "",
        "building_age": args.building_age or 0,  # 房龄
        "decoration": args.decoration or "",
        "property_type": args.property_type or "商品房",  # 产权性质
        "house_type": args.house_type or "普通住宅",         # 房屋类型
        "is_full5_unique": args.is_full5_unique or False,    # 满五唯一
        "has_parking": args.has_parking or "",
        "parking_price": args.parking_price or 0,            # 车位价格（万）
        "has_elevator": args.has_elevator or "",
        "school_district": args.school_district or "",
        "school_notes": args.school_notes or "",             # 学位占用情况
        "transport": args.transport or "",
        "facilities": args.facilities or "",
        "metro_distance": args.metro_distance or "",  # 最近地铁站距离（米）
        "mortgage_balance": args.mortgage_balance or 0,      # 剩余贷款（万）
        "tax_estimate": args.tax_estimate or 0,              # 税费估算（万）
        "agent_fee_rate": args.agent_fee_rate or 0.02,       # 中介费率
        "agent_fee": args.agent_fee or 0,                    # 中介费（万）
        "contact": args.contact or "",
        "pros": args.pros or "",
        "cons": args.cons or "",
        "my_score": args.my_score or 0,          # 个人评分（1-10）
        "url": args.url or "",
        "images": args.images or "",
        "status": "待看房",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    listings.append(listing)
    save_listings(listings)
    try:
        from _git_push import git_push
        git_push(f"feat: 新增房源 {args.name} ({new_id})")
    except Exception:
        pass
    print(f"✅ 房源已记录！ID: {new_id}")
    print(f"   名称: {args.name}")
    print(f"   总价: {args.price}万元")
    if args.room_type:
        print(f"   户型: {args.room_type}")
    if args.area:
        print(f"   面积: {args.area}㎡")
    if args.url:
        print(f"   链接: {args.url}")
    return new_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="添加新房源")
    parser.add_argument("--community", help="小区名称")
    parser.add_argument("--name", required=True, help="房源名称/备注")
    parser.add_argument("--price", type=float, required=True, help="总价（万元）")
    parser.add_argument("--address", help="详细地址")
    parser.add_argument("--unit-price", type=float, help="单价（元/㎡）")
    parser.add_argument("--room-type", help="户型（几室几厅）")
    parser.add_argument("--area", type=float, help="建筑面积（㎡）")
    parser.add_argument("--inner-area", type=float, help="套内面积（㎡）")
    parser.add_argument("--floor", help="楼层（如：中楼层/18/32）")
    parser.add_argument("--total-floors", help="总楼层")
    parser.add_argument("--orientation", help="朝向")
    parser.add_argument("--year-built", help="建筑年代（如：2018）")
    parser.add_argument("--building-age", type=int, help="房龄（年）")
    parser.add_argument("--decoration", help="装修情况")
    parser.add_argument("--property-type", help="产权性质（商品房/经济适用房等）")
    parser.add_argument("--house-type", help="房屋类型（普通住宅/公寓/别墅等）")
    parser.add_argument("--is-full5-unique", action="store_true", help="是否满五唯一")
    parser.add_argument("--has-parking", help="车位情况（有/无/租/买）")
    parser.add_argument("--parking-price", type=float, help="车位价格（万元）")
    parser.add_argument("--has-elevator", help="是否有电梯")
    parser.add_argument("--school-district", help="学区/对口学校")
    parser.add_argument("--school-notes", help="学位情况（如：未占用/锁定至2030）")
    parser.add_argument("--mortgage-balance", type=float, help="剩余贷款（万元）")
    parser.add_argument("--tax-estimate", type=float, help="税费估算（万元）")
    parser.add_argument("--agent-fee-rate", type=float, help="中介费率（如：0.02）")
    parser.add_argument("--agent-fee", type=float, help="中介费（万元）")
    parser.add_argument("--transport", help="交通情况")
    parser.add_argument("--facilities", help="周边配套")
    parser.add_argument("--metro-distance", type=int, help="最近地铁站距离（米）")
    parser.add_argument("--contact", help="中介/房东联系方式")
    parser.add_argument("--pros", help="优点")
    parser.add_argument("--cons", help="缺点")
    parser.add_argument("--my-score", type=float, help="个人评分（1-10）")
    parser.add_argument("--url", help="房源链接")
    parser.add_argument("--images", help="房间图片链接（多个用逗号分隔）")
    args = parser.parse_args()
    add_listing(args)
