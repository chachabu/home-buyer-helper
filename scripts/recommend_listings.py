#!/usr/bin/env python3
"""
智能推荐房源（买房版）。

默认 rental 模式用于筛选适合上班族租客的投资型房源：
- 预算只做硬过滤，不参与评分
- 租金、租售比、近地铁是核心评分项
- 学区低权重，仅作为参考
"""

import argparse
import json
import os
import re


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DATA_FILE = os.path.join(DATA_DIR, "listings.json")

SCHOOL_TIER_SCORE = {
    "none": 0.0,
    "normal": 0.35,
    "good": 0.75,
    "premium": 1.0,
}


def load_listings():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def as_float(value, default=0.0):
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def rent_yield_percent(listing):
    monthly_rent = as_float(listing.get("monthly_rent"))
    price_wan = as_float(listing.get("price_wan"))
    if monthly_rent <= 0 or price_wan <= 0:
        return 0.0
    return monthly_rent * 12 / (price_wan * 10000) * 100


def parse_room_count(room_type):
    m = re.search(r"(\d+)\s*室", room_type or "")
    return int(m.group(1)) if m else 0


def split_csv(value):
    return [part.strip() for part in (value or "").split(",") if part.strip()]


def passes_hard_filters(listing, args):
    price = as_float(listing.get("price_wan"))
    monthly_rent = as_float(listing.get("monthly_rent"))
    rent_yield = rent_yield_percent(listing)
    metro_distance = as_float(listing.get("metro_distance"), default=-1)

    if args.budget is not None and price > args.budget:
        return False, f"总价{price:g}万超过预算上限{args.budget:g}万"
    if args.budget_min is not None and price < args.budget_min:
        return False, f"总价{price:g}万低于预算下限{args.budget_min:g}万"
    if args.budget_max is not None and price > args.budget_max:
        return False, f"总价{price:g}万超过预算上限{args.budget_max:g}万"
    if args.min_monthly_rent is not None and monthly_rent < args.min_monthly_rent:
        return False, f"月租{monthly_rent:g}元低于下限{args.min_monthly_rent:g}元"
    if args.min_rent_yield is not None and rent_yield < args.min_rent_yield:
        return False, f"租售比{rent_yield:.2f}%低于下限{args.min_rent_yield:g}%"
    if args.max_metro_distance is not None:
        if metro_distance < 0:
            return False, "缺少地铁距离"
        if metro_distance > args.max_metro_distance:
            return False, f"距地铁{metro_distance:g}米超过上限{args.max_metro_distance:g}米"
    return True, ""


def score_rent(listing, args):
    monthly_rent = as_float(listing.get("monthly_rent"))
    rent_yield = rent_yield_percent(listing)
    if monthly_rent <= 0 and rent_yield <= 0:
        return 0.0, ["缺少租金数据"]

    rent_score = clamp(monthly_rent / args.target_monthly_rent) if args.target_monthly_rent else 0
    yield_score = clamp(rent_yield / args.target_rent_yield) if args.target_rent_yield else 0
    if rent_yield >= args.strong_rent_yield:
        yield_score = 1.0
    score = (rent_score * args.rent_monthly_ratio) + (yield_score * (1 - args.rent_monthly_ratio))
    reasons = []
    if monthly_rent:
        reasons.append(f"参考月租{monthly_rent:g}元")
    if rent_yield:
        reasons.append(f"年化租售比{rent_yield:.2f}%")
    return clamp(score), reasons


def score_metro(listing, args):
    distance = as_float(listing.get("metro_distance"), default=-1)
    nearest = listing.get("nearest_metro", "")
    if distance < 0:
        return 0.0, ["缺少地铁距离"]
    if distance <= args.metro_strong_distance:
        score = 1.0
    elif distance <= args.metro_good_distance:
        score = 0.82
    elif distance <= args.metro_ok_distance:
        score = 0.45
    elif distance <= args.metro_penalty_distance:
        score = 0.15
    else:
        score = 0.0
    label = f"距地铁{distance:g}米"
    if nearest:
        label += f"({nearest})"
    return score, [label]


def score_rental_fit(listing, args):
    room_count = parse_room_count(listing.get("room_type", ""))
    area = as_float(listing.get("area"))
    preferred_rooms = {int(v) for v in split_csv(args.rental_room_counts) if v.isdigit()}
    score = 0.0
    reasons = []

    if room_count:
        if room_count in preferred_rooms:
            score += 0.5
            reasons.append(f"{room_count}室适合出租")
        elif room_count == 3:
            score += 0.25
            reasons.append("3室可出租但总租客门槛更高")
        else:
            reasons.append(f"{room_count}室适租性一般")
    if area:
        if args.rental_area_min <= area <= args.rental_area_max:
            score += 0.5
            reasons.append(f"面积{area:g}㎡适租")
        elif area < args.rental_area_min:
            score += 0.25
            reasons.append(f"面积{area:g}㎡偏小")
        else:
            reasons.append(f"面积{area:g}㎡偏大")
    return clamp(score), reasons or ["缺少户型/面积数据"]


def score_liquidity(listing, args):
    score = 0.0
    reasons = []
    if listing.get("is_full5_unique"):
        score += 0.35
        reasons.append("满五唯一")
    tax = as_float(listing.get("tax_estimate"))
    price = as_float(listing.get("price_wan"))
    if tax > 0 and price > 0:
        tax_ratio = tax / price
        if tax_ratio <= args.low_tax_ratio:
            score += 0.25
            reasons.append(f"税费占比约{tax_ratio * 100:.1f}%")
    area = as_float(listing.get("area"))
    if area and area <= args.liquidity_area_max:
        score += 0.25
        reasons.append("面积段流动性较好")
    if listing.get("url"):
        score += 0.15
        reasons.append("有线上房源链接")
    return clamp(score), reasons or ["流动性信息不足"]


def score_condition(listing, args):
    score = 0.0
    reasons = []
    age = as_float(listing.get("building_age"))
    if age:
        if age <= args.good_age:
            score += 0.7
            reasons.append(f"房龄{age:g}年")
        elif age <= args.ok_age:
            score += 0.4
            reasons.append(f"房龄{age:g}年可接受")
        else:
            reasons.append(f"房龄{age:g}年偏老")
    decoration = listing.get("decoration", "")
    if any(word in decoration for word in ("精装", "简装", "装修")):
        score += 0.3
        reasons.append(f"装修：{decoration}")
    return clamp(score), reasons or ["房龄/装修信息不足"]


def score_school(listing, args):
    tier = (listing.get("school_tier") or "none").strip().lower()
    base = SCHOOL_TIER_SCORE.get(tier, 0.0)
    school = listing.get("school_district", "")
    notes = listing.get("school_notes", "")
    reasons = []
    if school:
        base = max(base, 0.35)
        reasons.append(f"学区参考：{school}")
    if "占用" in notes and "未占用" not in notes:
        base *= 0.5
        reasons.append("学位可能占用")
    elif notes:
        reasons.append(notes)
    return clamp(base), reasons or ["无学区加分"]


def build_tags(listing, args):
    tags = []
    monthly_rent = as_float(listing.get("monthly_rent"))
    rent_yield = rent_yield_percent(listing)
    metro_distance = as_float(listing.get("metro_distance"), default=-1)
    room_score, _ = score_rental_fit(listing, args)

    if metro_distance >= 0 and metro_distance <= args.metro_strong_distance:
        tags.append("近地铁强推荐")
    elif metro_distance >= 0 and metro_distance <= args.metro_good_distance:
        tags.append("地铁友好")
    if monthly_rent >= args.target_monthly_rent:
        tags.append("高租金")
    if rent_yield >= args.strong_rent_yield:
        tags.append("强租售比")
    elif rent_yield >= args.target_rent_yield:
        tags.append("高租售比")
    if (
        metro_distance >= 0
        and metro_distance <= args.metro_good_distance
        and monthly_rent >= args.target_monthly_rent
        and room_score >= 0.75
    ):
        tags.append("上班族适租")
    if listing.get("school_district") or listing.get("school_tier") in ("good", "premium"):
        tags.append("学区参考")
    return tags


def calculate_match_score(listing, args):
    """计算房源匹配度评分。预算是硬过滤，不参与评分。"""
    dimensions = []
    scorers = [
        ("租金收益", args.weight_rent, score_rent),
        ("地铁通勤", args.weight_metro, score_metro),
        ("适租户型", args.weight_rental_fit, score_rental_fit),
        ("流动性", args.weight_liquidity, score_liquidity),
        ("房龄装修", args.weight_condition, score_condition),
        ("学区参考", args.weight_school, score_school),
    ]
    total = 0.0
    reasons = []
    for name, weight, fn in scorers:
        component, component_reasons = fn(listing, args)
        points = component * weight
        total += points
        dimensions.append({
            "name": name,
            "points": points,
            "weight": weight,
            "reasons": component_reasons,
        })
        if component_reasons:
            reasons.append(f"{name}: {component_reasons[0]}")
    return total, reasons, dimensions, build_tags(listing, args)


def recommend_listings(args):
    listings = load_listings()
    if not listings:
        print("暂无房源记录，请先添加房源")
        return

    scored = []
    filtered = []
    for listing in listings:
        ok, reason = passes_hard_filters(listing, args)
        if not ok:
            filtered.append((listing, reason))
            continue
        score, reasons, dimensions, tags = calculate_match_score(listing, args)
        scored.append({
            "listing": listing,
            "score": score,
            "reasons": reasons,
            "dimensions": dimensions,
            "tags": tags,
        })
    scored.sort(key=lambda x: x["score"], reverse=True)

    if not scored:
        print("没有房源通过硬过滤条件")
        if filtered:
            print(f"已过滤 {len(filtered)} 条，例如：{filtered[0][0].get('name', '')} - {filtered[0][1]}")
        return

    max_score = sum([
        args.weight_rent,
        args.weight_metro,
        args.weight_rental_fit,
        args.weight_liquidity,
        args.weight_condition,
        args.weight_school,
    ])
    print(f"\n🎯 找到 {len(scored)} 套候选房源（预算/硬条件过滤后，按出租投资评分排序）：")
    if filtered:
        print(f"   已按硬过滤排除 {len(filtered)} 条")
    print(f"   评分权重: 租金{args.weight_rent:g} 地铁{args.weight_metro:g} 适租{args.weight_rental_fit:g} 流动性{args.weight_liquidity:g} 房龄装修{args.weight_condition:g} 学区{args.weight_school:g}")
    print("=" * 76)

    for i, item in enumerate(scored[:args.limit], 1):
        listing = item["listing"]
        monthly_rent = as_float(listing.get("monthly_rent"))
        rent_yield = rent_yield_percent(listing)
        tags = " / ".join(item["tags"]) if item["tags"] else "无重点标签"
        dimension_text = "; ".join(
            f"{d['name']} {d['points']:.1f}/{d['weight']:g}" for d in item["dimensions"]
        )

        print(f"\n【#{i}】{listing.get('community') or listing.get('name', '')}  {item['score']:.1f}/{max_score:g}分")
        print(f"   标签: {tags}")
        print(f"   总价: {listing.get('price_wan', 0)}万  单价: {listing.get('unit_price', '-') or '-'}元/㎡")
        print(f"   租金: {monthly_rent:g}元/月  租售比: {rent_yield:.2f}%  来源: {listing.get('rent_source', '-') or '-'}")
        print(f"   地铁: {listing.get('nearest_metro', '-') or '-'}  {listing.get('metro_distance', '-') or '-'}米")
        print(f"   户型: {listing.get('room_type', '-') or '-'}  面积: {listing.get('area', 0)}㎡")
        print(f"   房龄: {listing.get('building_age', '?') or '?'}年  装修: {listing.get('decoration', '-') or '-'}")
        print(f"   学区: {listing.get('school_district', '-') or '-'}  等级: {listing.get('school_tier', '-') or '-'}")
        print(f"   维度: {dimension_text}")
        print(f"   理由: {'; '.join(item['reasons'][:6])}")
        if listing.get("pros"):
            print(f"   优点: {listing.get('pros')[:80]}")
        if listing.get("cons"):
            print(f"   缺点: {listing.get('cons')[:80]}")
        print(f"   链接: {listing.get('url', '-') or '-'}")

    if len(scored) > args.limit:
        print(f"\n... 还有 {len(scored) - args.limit} 条候选结果")
    print("=" * 76)


def add_arguments(parser):
    parser.add_argument("--profile", choices=["rental"], default="rental", help="评分模式，默认 rental：上班族出租友好")

    # 硬过滤：资金/硬指标，不参与评分。
    parser.add_argument("--budget", type=float, help="总价上限（万元），硬过滤")
    parser.add_argument("--budget-min", type=float, help="最低总价（万元），硬过滤")
    parser.add_argument("--budget-max", type=float, help="最高总价（万元），硬过滤")
    parser.add_argument("--min-monthly-rent", type=float, help="最低月租（元），硬过滤；不填则只参与评分/标签")
    parser.add_argument("--min-rent-yield", type=float, help="最低年化租售比（%），硬过滤；不填则只参与评分/标签")
    parser.add_argument("--max-metro-distance", type=float, help="最大距地铁距离（米），硬过滤；不填则只参与评分")

    # 默认权重总和 100，执行 skill 时可按需覆盖。
    parser.add_argument("--weight-rent", type=float, default=35, help="租金收益权重，默认35")
    parser.add_argument("--weight-metro", type=float, default=30, help="地铁/通勤权重，默认30")
    parser.add_argument("--weight-rental-fit", type=float, default=15, help="户型面积适租权重，默认15")
    parser.add_argument("--weight-liquidity", type=float, default=10, help="流动性/交易属性权重，默认10")
    parser.add_argument("--weight-condition", type=float, default=5, help="房龄装修权重，默认5")
    parser.add_argument("--weight-school", type=float, default=5, help="学区参考权重，默认5")

    # 租金/租售比参数。
    parser.add_argument("--target-monthly-rent", type=float, default=5000, help="高租金/评分参考月租，默认5000元")
    parser.add_argument("--target-rent-yield", type=float, default=2.0, help="高租售比阈值，默认2.0%")
    parser.add_argument("--strong-rent-yield", type=float, default=2.5, help="强租售比阈值，默认2.5%")
    parser.add_argument("--rent-monthly-ratio", type=float, default=0.45, help="租金收益中月租占比，默认0.45，剩余为租售比")

    # 地铁参数。
    parser.add_argument("--metro-strong-distance", type=float, default=500, help="近地铁强推荐距离，默认500米")
    parser.add_argument("--metro-good-distance", type=float, default=800, help="地铁友好距离，默认800米")
    parser.add_argument("--metro-ok-distance", type=float, default=1200, help="可接受地铁距离，默认1200米")
    parser.add_argument("--metro-penalty-distance", type=float, default=1500, help="超过该距离地铁得分趋近0，默认1500米")

    # 适租/流动性/房龄参数。
    parser.add_argument("--rental-room-counts", default="1,2", help="偏好的出租卧室数，逗号分隔，默认1,2")
    parser.add_argument("--rental-area-min", type=float, default=35, help="适租面积下限，默认35㎡")
    parser.add_argument("--rental-area-max", type=float, default=90, help="适租面积上限，默认90㎡")
    parser.add_argument("--liquidity-area-max", type=float, default=90, help="流动性较好面积上限，默认90㎡")
    parser.add_argument("--low-tax-ratio", type=float, default=0.03, help="低税费占比阈值，默认0.03")
    parser.add_argument("--good-age", type=float, default=15, help="较好房龄上限，默认15年")
    parser.add_argument("--ok-age", type=float, default=25, help="可接受房龄上限，默认25年")

    parser.add_argument("--limit", type=int, default=8, help="输出结果数量，默认8")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="智能推荐房源（出租投资/近地铁优先）")
    add_arguments(arg_parser)
    recommend_listings(arg_parser.parse_args())
