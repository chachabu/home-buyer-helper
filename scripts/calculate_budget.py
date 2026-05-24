#!/usr/bin/env python3
"""
购房预算与月供计算器
用法: python calculate_budget.py --price 500 --down-payment 150 --loan-rate 3.1 --loan-years 30

支持公积金+商贷组合贷款
"""

import json
import os
import argparse
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DATA_FILE = os.path.join(DATA_DIR, "listings.json")
LISTINGS_FILE = DATA_FILE

def calc_equal_payment(principal_wan, annual_rate, months):
    """等额本息：每月还款额
    principal_wan: 贷款本金（万元）
    """
    principal = principal_wan * 10000  # 转元
    monthly_rate = annual_rate / 100 / 12
    if monthly_rate == 0:
        return round(principal / months, 2)
    payment = principal * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)
    return round(payment, 2)

def calc_equal_principal(principal_wan, annual_rate, months):
    """等额本金：逐月递减
    principal_wan: 贷款本金（万元）
    """
    principal = principal_wan * 10000
    monthly_rate = annual_rate / 100 / 12
    base = principal / months
    payments = []
    for i in range(months):
        interest = (principal - base * i) * monthly_rate
        payments.append(round(base + interest, 2))
    return payments[0], payments[-1], sum(payments), payments

def calc_tax_and_fees(price_wan, area, is_full5, is_first_home, is_90sqm, agent_fee_rate=0.02):
    """估算税费与杂费（单位：万元）"""
    price = price_wan
    result = {}

    # 契税
    if is_first_home:
        if is_90sqm:
            result["契税"] = round(price * 0.01, 2)
        else:
            result["契税"] = round(price * 0.015, 2)
    else:
        if is_90sqm:
            result["契税"] = round(price * 0.01, 2)
        else:
            result["契税"] = round(price * 0.02, 2)

    # 增值税及附加（满二唯一免征）
    if is_full5:
        result["增值税及附加"] = 0
        result["个人所得税"] = 0
    else:
        # 简化估算：按5.3%计算（各地政策有差异）
        result["增值税及附加"] = round(price * 0.053, 2)
        # 个税 1%
        result["个人所得税"] = round(price * 0.01, 2)

    # 中介费
    result["中介费"] = round(price * agent_fee_rate, 2)

    # 登记费
    result["不动产登记费"] = 80
    if price > 0:
        result["不动产登记费"] = 80  # 住宅固定

    # 其他杂费（评估费、贷款服务费等）
    result["其他杂费"] = 0.2  # 估算 2000 元

    total_fees = sum(result.values())
    result["合计"] = round(total_fees, 2)

    return result

def calculate_budget(args):
    """计算购房预算"""
    print("=" * 55)
    print(f"  购房预算计算")
    print("=" * 55)

    total_price = args.price
    down_payment = args.down_payment
    loan_rate = args.loan_rate
    loan_years = args.loan_years
    is_first_home = args.first_home
    is_90sqm = args.area <= 90 if args.area else True

    # 贷款金额
    provident_fund = args.provident_fund or 0  # 公积金贷款（万）
    commercial = total_price - down_payment - provident_fund  # 商业贷款（万）

    months = loan_years * 12

    print(f"\n💰 房屋信息")
    print(f"   总价:        {total_price:.1f} 万元")
    print(f"   面积:        {args.area or '-'} ㎡")
    print(f"   单价:        {args.unit_price or '-'} 元/㎡")
    print(f"   是否首套:    {'是' if is_first_home else '否'}")
    print(f"   是否90㎡以内:{'是' if is_90sqm else '否'}")

    print(f"\n💳 首付与贷款")
    print(f"   首付:        {down_payment:.1f} 万元 ({down_payment/total_price*100:.1f}%)")
    if provident_fund:
        print(f"   公积金贷款:  {provident_fund:.1f} 万元（利率3.1%）")
    print(f"   商业贷款:    {commercial:.1f} 万元")
    print(f"   贷款总额:    {commercial + provident_fund:.1f} 万元")
    print(f"   贷款年限:    {loan_years} 年（{months} 期）")

    print(f"\n📊 月供计算（商业贷款利率: {loan_rate}%）")

    # 等额本息
    equal_payment = calc_equal_payment(commercial, loan_rate, months)
    print(f"\n   方式一：等额本息")
    print(f"   每月还款:   {equal_payment:,.2f} 元")
    print(f"   支付利息:   {equal_payment * months - commercial*10000:,.2f} 元")

    # 等额本金
    ep_first, ep_last, ep_total, ep_list = calc_equal_principal(commercial, loan_rate, months)
    print(f"\n   方式二：等额本金")
    print(f"   首月还款:   {ep_first:,.2f} 元")
    print(f"   末月还款:   {ep_last:,.2f} 元")
    print(f"   每月递减约: {commercial*10000/months * (loan_rate/100/12):,.2f} 元")
    print(f"   支付利息:   {ep_total - commercial*10000:,.2f} 元")

    # 税费
    print(f"\n🏛️ 过户税费估算")
    taxes = calc_tax_and_fees(
        total_price,
        args.area or 90,
        args.full5 or False,
        is_first_home,
        is_90sqm,
        args.agent_fee_rate or 0.02
    )
    for k, v in taxes.items():
        if k == "合计":
            print(f"   ─────────────────────────")
        unit = "万元" if k not in ("不动产登记费",) else "元"
        print(f"   {k:<15}{v:.2f} {unit}")

    # 月均税费摊销
    months_total = loan_years * 12
    monthly_fee = taxes["合计"] / months_total

    # 总结
    down = down_payment
    taxes_total = taxes["合计"]
    first_month_payment = equal_payment
    monthly_property_wan = args.monthly_property or 0.3
    total_first_outlay = down + taxes_total
    monthly_expense = first_month_payment + monthly_property_wan * 10000 + monthly_fee * 10000

    print(f"\n📋 首月资金需求")
    print(f"   首付款:      {down:.1f} 万元")
    print(f"   税费杂费:    {taxes_total:.2f} 万元")
    print(f"   ─────────────────────────")
    print(f"   首月总支出:  {total_first_outlay:.2f} 万元  （过户当日需准备，不含月供）")

    print(f"\n📋 每月固定支出")
    print(f"   月供(等额本息): {first_month_payment:,.0f} 元")
    print(f"   物业费:         {monthly_property_wan:.1f} 万元/月 = {monthly_property_wan*10000:,.0f} 元")
    print(f"   月均税费摊销:   {monthly_fee:.4f} 万元 = {monthly_fee*10000:,.0f} 元")
    print(f"   ─────────────────────────")
    print(f"   每月合计:       {monthly_expense:,.0f} 元")

    # 建议
    print(f"\n💡 建议")
    monthly_income_needed = monthly_expense / 0.35
    print(f"   建议月收入 ≥ {monthly_income_needed:,.0f} 元（月供占收入≤35%）")
    print(f"   建议预留 ≥ {total_first_outlay + 5:.1f} 万元（含5万备用金）")

def calculate_single_listing(args):
    """计算单个房源预算"""
    listings = load_listings()
    listing = next((l for l in listings if l.get("id") == args.id), None)
    if not listing:
        print(f"未找到房源: {args.id}")
        return

    print(f"\n🏠 房源: {listing.get('name')}")
    total_price = listing["price_wan"]

    # 如果命令行有覆盖参数，以命令行为准
    price = args.price if args.price else total_price
    area = args.area if args.area else listing.get("area", 0)
    unit_price = args.unit_price if args.unit_price else listing.get("unit_price", 0)

    down_payment = args.down_payment if args.down_payment else price * 0.3
    loan_rate = args.loan_rate or 3.1
    loan_years = args.loan_years or 30

    args_fake = argparse.Namespace(
        price=price, area=area, unit_price=unit_price,
        down_payment=down_payment, loan_rate=loan_rate,
        loan_years=loan_years,
        provident_fund=args.provident_fund or 0,
        first_home=True,
        full5=listing.get("is_full5_unique", False),
        agent_fee_rate=0.02,
        monthly_property=0.3
    )
    calculate_budget(args_fake)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="购房预算计算器")
    parser.add_argument("--price", type=float, help="总价（万元）")
    parser.add_argument("--area", type=float, help="面积（㎡）")
    parser.add_argument("--unit-price", type=float, help="单价（元/㎡）")
    parser.add_argument("--down-payment", type=float, help="首付（万元）")
    parser.add_argument("--loan-rate", type=float, default=3.1, help="商贷年利率（%%），默认3.1")
    parser.add_argument("--loan-years", type=int, default=30, help="贷款年限，默认30")
    parser.add_argument("--provident-fund", type=float, default=0, help="公积金贷款金额（万元）")
    parser.add_argument("--first-home", action="store_true", default=True, help="是否首套")
    parser.add_argument("--full5", action="store_true", help="是否满五唯一（免增值税个税）")
    parser.add_argument("--agent-fee-rate", type=float, default=0.02, help="中介费率")
    parser.add_argument("--monthly-property", type=float, default=0.3, help="月物业费（万元）")
    parser.add_argument("--id", help="对指定房源计算（会读取房源数据）")
    args = parser.parse_args()
    if args.id:
        calculate_single_listing(args)
    elif args.price:
        calculate_budget(args)
    else:
        parser.print_help()
