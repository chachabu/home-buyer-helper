#!/usr/bin/env python3
"""
列出房源列表（买房版，支持筛选和看房记录）
用法: python list_listings.py [--status 状态] [--min-price 200] [--max-price 500] [--room-type 2] [--viewings]
"""

import json
import os
import argparse

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
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

def list_listings(args):
    listings = load_listings()
    viewings = load_viewings()

    if not listings:
        print("暂无房源记录")
        return

    # 筛选
    filtered = listings
    if args.status:
        filtered = [l for l in filtered if l.get("status") == args.status]
    if args.min_price is not None:
        filtered = [l for l in filtered if l.get("price_wan", 0) >= args.min_price]
    if args.max_price is not None:
        filtered = [l for l in filtered if l.get("price_wan", 0) <= args.max_price]
    if args.room_type:
        filtered = [l for l in filtered if args.room_type in l.get("room_type", "")]
    if args.decoration:
        filtered = [l for l in filtered if args.decoration in l.get("decoration", "")]
    if args.full5:
        filtered = [l for l in filtered if l.get("is_full5_unique")]

    if not filtered:
        print("没有符合条件的房源")
        return

    # 列表视图
    print(f"\n{'小区':<12}{'名称':<12}{'总价(万)':<10}{'面积':<7}{'地铁':<7}{'我的分':<7}{'状态':<8}")
    print("-" * 65)
    for l in filtered:
        name = l.get("name", "")[:11]
        community = l.get("community", "")[:10]
        price = f"{l.get('price_wan', 0)}万"
        area = f"{l.get('area', 0)}㎡"
        metro = f"{l.get('metro_distance', '')}m" if l.get("metro_distance") else "-"
        score = f"{l.get('my_score', '-')}/10" if l.get("my_score") else "-"
        status = l.get("status", "")[:6]
        print(f"{community:<12}{name:<12}{price:<10}{area:<7}{metro:<7}{score:<7}{status:<8}")

    print(f"\n共 {len(filtered)} 条记录")

    # 详情视图
    if args.id:
        listing = next((l for l in listings if l.get("id") == args.id), None)
        if not listing:
            print(f"未找到 ID={args.id} 的房源")
            return
        print(f"\n{'='*55}")
        print(f"【{listing.get('name')}】详情")
        print(f"{'='*55}")
        print(f"ID:            {listing.get('id')}")
        print(f"地址:          {listing.get('address') or '-'}")
        print(f"总价:          {listing.get('price_wan', 0)} 万元")
        if listing.get("unit_price"):
            print(f"单价:          {listing['unit_price']} 元/㎡")
        print(f"户型:          {listing.get('room_type') or '-'}")
        print(f"建筑面积:      {listing.get('area', 0)} ㎡")
        if listing.get("inner_area"):
            print(f"套内面积:      {listing.get('inner_area')} ㎡")
        print(f"楼层:          {listing.get('floor') or '-'} / {listing.get('total_floors') or '-'}层")
        print(f"朝向:          {listing.get('orientation') or '-'}")
        print(f"建筑年代:      {listing.get('year_built') or '-'}（房龄约{listing.get('building_age', 0)}年）")
        print(f"装修:          {listing.get('decoration') or '-'}")
        print(f"产权性质:      {listing.get('property_type') or '商品房'}")
        print(f"房屋类型:      {listing.get('house_type') or '普通住宅'}")
        print(f"满五唯一:      {'是' if listing.get('is_full5_unique') else '否'}")
        print(f"车位:          {listing.get('has_parking') or '-'}")
        if listing.get("parking_price"):
            print(f"车位价格:      {listing.get('parking_price')} 万元")
        print(f"电梯:          {listing.get('has_elevator') or '-'}")
        print(f"学区:          {listing.get('school_district') or '-'}")
        if listing.get("school_notes"):
            print(f"学位情况:      {listing.get('school_notes')}")
        print(f"交通:          {listing.get('transport') or '-'}")
        if listing.get("metro_distance"):
            print(f"距地铁:        {listing['metro_distance']}米")
        print(f"周边配套:      {listing.get('facilities') or '-'}")
        if listing.get("mortgage_balance"):
            print(f"剩余贷款:      {listing.get('mortgage_balance')} 万元")
        print(f"税费估算:      {listing.get('tax_estimate', 0)} 万元")
        print(f"中介费率:      {listing.get('agent_fee_rate', 0.02)*100:.1f}%")
        print(f"中介费:        {listing.get('agent_fee', 0)} 万元")
        print(f"联系方式:      {listing.get('contact') or '-'}")
        print(f"优点:          {listing.get('pros') or '-'}")
        print(f"缺点:          {listing.get('cons') or '-'}")
        if listing.get("my_score"):
            stars = "⭐" * int(listing["my_score"])
            print(f"🏆 我的评分:    {listing['my_score']}/10  {stars}")
        print(f"房源链接:      {listing.get('url') or '-'}")
        print(f"状态:          {listing.get('status')}")
        print(f"录入时间:      {listing.get('created_at', '')[:10]}")

        # 看房记录
        if args.viewings:
            listing_viewings = [v for v in viewings if v.get("listing_id") == args.id]
            if listing_viewings:
                print(f"\n📋 看房记录:")
                for v in listing_viewings:
                    print(f"  时间: {v.get('viewing_time', '')[:10]}")
                    print(f"  是否与描述一致: {v.get('description_match') or '-'}")
                    print(f"  采光: {v.get('lighting')}/5  通风: {v.get('ventilation')}/5  噪音: {v.get('noise')}/5")
                    print(f"  房屋保养: {v.get('condition')}/5  户型合理性: {v.get('layout')}/5")
                    print(f"  车位便利: {v.get('parking')}/5  学区配套: {v.get('school')}/5")
                    print(f"  综合评分: {v.get('overall_score', 0)}/10")
                    print(f"  是否考虑签约: {'是' if v.get('consider_signing') else '否'}")
                    if v.get("notes"):
                        print(f"  备注: {v.get('notes')}")
                    print()
            else:
                print(f"\n暂无看房记录")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="列出房源")
    parser.add_argument("--status", help="按状态筛选")
    parser.add_argument("--min-price", type=float, help="最低总价（万元）")
    parser.add_argument("--max-price", type=float, help="最高总价（万元）")
    parser.add_argument("--room-type", help="户型筛选（如 2）")
    parser.add_argument("--decoration", help="装修筛选")
    parser.add_argument("--full5", action="store_true", help="只看满五唯一")
    parser.add_argument("--id", help="查看指定ID的详情")
    parser.add_argument("--viewings", action="store_true", help="同时显示看房记录")
    args = parser.parse_args()
    list_listings(args)
