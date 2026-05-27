#!/usr/bin/env python3
"""Estimate monthly rent from Beike rental listings by community."""

import argparse
import os
import re
import statistics
import subprocess
import tempfile
import time
from collections import defaultdict
from datetime import datetime

from listing_parsers import (
    build_beike_rent_url,
    clean_text,
    fetch_page,
    load_listings,
    normalize_community_name,
    parse_beike_rent_listings_html,
    save_listings,
)


def as_float(value, default=0.0):
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def is_near_subway(listing):
    if listing.get("near_subway"):
        return True
    text = " ".join(str(listing.get(key, "")) for key in ("transport", "nearest_metro", "tags"))
    return "近地铁" in text


def is_ordinary_residence(listing):
    if listing.get("ordinary_residence"):
        return True
    text = " ".join(str(listing.get(key, "")) for key in ("property_type", "house_type"))
    return "普通住宅" in text


def strip_community_suffix(value):
    text = clean_text(value)
    text = re.sub(r"[（(].*?[）)]", "", text)
    return text.strip()


def round_to(value, step):
    if not step:
        return int(round(value))
    return int(round(value / step) * step)


def filter_target_listings(listings, args):
    result = []
    requested = {normalize_community_name(v) for v in args.community}
    for listing in listings:
        community = listing.get("community") or listing.get("address") or ""
        if not community:
            continue
        if requested and normalize_community_name(community) not in requested:
            continue
        price = as_float(listing.get("price_wan"))
        if args.budget_min is not None and price < args.budget_min:
            continue
        if args.budget_max is not None and price > args.budget_max:
            continue
        if args.only_near_subway and not is_near_subway(listing):
            continue
        if args.only_ordinary_residence and not is_ordinary_residence(listing):
            continue
        if not args.overwrite and as_float(listing.get("monthly_rent")) > 0:
            continue
        if as_float(listing.get("area")) <= 0:
            continue
        result.append(listing)
    return result


def group_by_community(listings):
    grouped = defaultdict(list)
    display_names = {}
    for listing in listings:
        community = listing.get("community") or listing.get("address") or ""
        key = normalize_community_name(community)
        if not key:
            continue
        grouped[key].append(listing)
        display_names.setdefault(key, community)
    return grouped, display_names


def load_rent_html_http(url):
    html, final_url = fetch_page(url, timeout=15)
    if _looks_like_rent_blocked(html, final_url):
        return html, final_url, "blocked"
    return html, final_url, "ok"


def load_rent_html_chrome(url, args):
    subprocess.run(["open", "-a", args.chrome_app, url], check=False)
    time.sleep(max(0.5, args.chrome_wait_seconds))
    return load_current_rent_html_chrome(args)


def load_current_rent_html_chrome(args):
    html = _save_current_chrome_html(args.chrome_app, args.current_wait_seconds)
    active_url = _run_osascript(
        f'tell application "{_applescript_string(args.chrome_app)}" to get URL of active tab of front window'
    )
    title = _run_osascript(
        f'tell application "{_applescript_string(args.chrome_app)}" to get title of active tab of front window'
    )
    if _looks_like_rent_blocked(html, active_url, title):
        return html, active_url, "blocked"
    return html, active_url, "ok"


def _save_current_chrome_html(chrome_app, wait_seconds):
    app_name = _applescript_string(chrome_app)
    tmp_dir = tempfile.mkdtemp(prefix="home-buyer-rent-")
    html_path = os.path.join(tmp_dir, "active-tab.html")
    deadline = time.time() + max(0.5, wait_seconds)
    html = ""
    try:
        while True:
            _run_osascript(
                f'tell application "{app_name}" to save active tab of front window '
                f'in POSIX file "{_applescript_string(html_path)}" as "only html"'
            )
            if os.path.exists(html_path):
                with open(html_path, "r", encoding="utf-8", errors="replace") as f:
                    html = f.read()
            if _rent_page_ready(html) or time.time() >= deadline:
                return html
            time.sleep(0.5)
    finally:
        try:
            if os.path.exists(html_path):
                os.remove(html_path)
            os.rmdir(tmp_dir)
        except OSError:
            pass


def _rent_page_ready(html):
    if not html:
        return False
    return (
        "content__list--item" in html
        or "content__pg" in html
        or "ke-passport" in html
        or "验证码" in html
        or "请完成安全验证" in html
    )


def _looks_like_rent_blocked(html, url="", title=""):
    sample = clean_text((html or "")[:6000])
    if url and ("clogin.ke.com" in url or "hip.ke.com/captcha" in url):
        return True
    if "ke-passport" in (html or ""):
        return True
    if any(term in sample for term in ("请完成安全验证", "CAPTCHA", "Captcha", "captcha")):
        return True
    if _looks_like_chrome_blocked(url, title):
        return True
    return False


def _looks_like_chrome_blocked(url, title):
    text = f"{url} {title}"
    return any(term in text for term in ("clogin", "captcha", "验证"))


def _run_osascript(script):
    try:
        return subprocess.check_output(
            ["osascript", "-e", script],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError((e.output or "").strip() or str(e)) from e


def _applescript_string(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def clean_rent_samples(rentals, args):
    samples = []
    for rental in rentals:
        monthly_rent = as_float(rental.get("monthly_rent"))
        area = as_float(rental.get("area"))
        rent_per_sqm = as_float(rental.get("rent_per_sqm"))
        title = rental.get("title", "")
        if monthly_rent <= 0 or area <= 0 or rent_per_sqm <= 0:
            continue
        if not args.include_shared and "合租" in title:
            continue
        if rent_per_sqm < args.min_rent_per_sqm or rent_per_sqm > args.max_rent_per_sqm:
            continue
        samples.append(rental)
    return samples


def estimate_for_community(community, args):
    search_name = strip_community_suffix(community) or community
    url = build_beike_rent_url(args.city, search_name, args.area, rent_type=args.rent_type)
    if args.chrome:
        html, final_url, status = load_rent_html_chrome(url, args)
    else:
        html, final_url, status = load_rent_html_http(url)
    if status == "blocked" and args.chrome and args.pause_on_block:
        print(f"      已打开租房页: {url}")
        try:
            input("      请在 Chrome 完成登录/验证并确认列表稳定后按回车继续...")
        except EOFError:
            pass
        html, final_url, status = load_current_rent_html_chrome(args)
    if status == "blocked":
        return {
            "community": community,
            "search_name": search_name,
            "url": final_url or url,
            "status": "blocked",
            "samples": [],
        }

    rentals = parse_beike_rent_listings_html(
        html,
        community=search_name,
        exact_community=not args.allow_nearby_rentals,
        limit=args.sample_limit,
    )
    samples = clean_rent_samples(rentals, args)
    if not samples:
        return {
            "community": community,
            "search_name": search_name,
            "url": final_url or url,
            "status": "no_samples",
            "samples": [],
        }

    per_sqm_values = [sample["rent_per_sqm"] for sample in samples]
    rent_per_sqm = statistics.median(per_sqm_values)
    return {
        "community": community,
        "search_name": search_name,
        "url": final_url or url,
        "status": "ok",
        "samples": samples,
        "rent_per_sqm": rent_per_sqm,
    }


def apply_estimate(listings, estimate, args):
    if estimate["status"] != "ok" or len(estimate["samples"]) < args.min_samples:
        return 0
    rent_per_sqm = estimate["rent_per_sqm"]
    sample_count = len(estimate["samples"])
    updated = 0
    now = datetime.now().isoformat()
    for listing in listings:
        if not args.overwrite and as_float(listing.get("monthly_rent")) > 0:
            continue
        area = as_float(listing.get("area"))
        if area <= 0:
            continue
        listing["monthly_rent"] = round_to(area * rent_per_sqm, args.round_to)
        listing["rent_source"] = "贝壳租房第一页估算"
        listing["rent_estimate_method"] = "community_first_page_median_per_sqm"
        listing["rent_sample_count"] = sample_count
        listing["rent_per_sqm"] = round(rent_per_sqm, 2)
        listing["rent_reference_url"] = estimate["url"]
        listing["updated_at"] = now
        updated += 1
    return updated


def enrich_rent_estimates(args):
    listings = load_listings()
    if not listings:
        print("暂无房源记录，请先抓取或导入房源")
        return

    targets = filter_target_listings(listings, args)
    grouped, display_names = group_by_community(targets)
    if not grouped:
        print("没有需要补租金的房源")
        return

    communities = sorted(grouped, key=lambda key: (-len(grouped[key]), display_names[key]))
    if args.community_limit:
        communities = communities[:args.community_limit]

    print(f"\n🏷️ 待估算: {len(targets)} 套房源，{len(communities)} 个小区")
    print(f"   样本来源: 贝壳租房第一页 / {'Chrome' if args.chrome else 'HTTP'} / {args.rent_type}")

    total_updated = 0
    blocked = False
    for index, key in enumerate(communities, 1):
        community = display_names[key]
        estimate = estimate_for_community(community, args)
        if estimate["status"] == "blocked":
            print(f"  [{index}/{len(communities)}] {community}: 被登录/验证拦截，停止。")
            if not args.chrome:
                print("      可改用 --chrome 复用系统 Chrome 登录态；触发验证时人工处理后再继续。")
            blocked = True
            break
        if estimate["status"] != "ok" or len(estimate["samples"]) < args.min_samples:
            print(f"  [{index}/{len(communities)}] {community}: 无有效租金样本")
        else:
            updated = apply_estimate(grouped[key], estimate, args)
            total_updated += updated
            print(
                f"  [{index}/{len(communities)}] {community}: "
                f"{estimate['rent_per_sqm']:.1f}元/㎡/月，样本{len(estimate['samples'])}，更新{updated}套"
            )
        if args.delay_seconds and index < len(communities):
            time.sleep(max(0, args.delay_seconds))

    if args.save and total_updated:
        save_listings(listings)
        print(f"\n✅ 已写回 {total_updated} 套房源的估算月租")
    elif total_updated:
        print(f"\nℹ️ 预览模式：可写回 {total_updated} 套；加 --save 保存")
    else:
        print("\nℹ️ 没有写回租金")

    if blocked:
        print("   本次在拦截处停止，没有继续批量打开后续小区。")


def add_arguments(parser):
    parser.add_argument("--city", default="北京")
    parser.add_argument("--area", help="可选：限制租房搜索区域 slug/区域名；不填则全城按小区搜索")
    parser.add_argument("--community", action="append", default=[], help="只补指定小区，可重复传")
    parser.add_argument("--budget-min", type=float, help="最低总价（万元），只筛本地二手房记录")
    parser.add_argument("--budget-max", type=float, help="最高总价（万元），只筛本地二手房记录")
    parser.add_argument("--only-near-subway", action="store_true", help="只补近地铁记录")
    parser.add_argument("--only-ordinary-residence", action="store_true", help="只补普通住宅记录")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有 monthly_rent")
    parser.add_argument("--save", action="store_true", help="写回 data/listings.json；不加则只预览")

    parser.add_argument("--chrome", action="store_true", help="用系统 Chrome 打开租房页并读取 HTML，复用登录态")
    parser.add_argument("--chrome-app", default="Google Chrome", help="浏览器应用名，默认 Google Chrome")
    parser.add_argument("--chrome-wait-seconds", type=float, default=2.5, help="打开每个租房页后的等待秒数")
    parser.add_argument("--current-wait-seconds", type=float, default=8.0, help="等待租房列表 HTML 稳定的秒数")
    parser.add_argument("--delay-seconds", type=float, default=1.0, help="每个小区之间的等待秒数")
    parser.add_argument("--pause-on-block", action="store_true", help="Chrome 模式遇到登录/验证时等待人工处理后重读当前页")

    parser.add_argument("--rent-type", choices=["whole", "all", "shared"], default="whole", help="租房样本类型，默认整租")
    parser.add_argument("--include-shared", action="store_true", help="允许合租样本参与估算")
    parser.add_argument("--allow-nearby-rentals", action="store_true", help="允许搜索结果中非精确同小区样本参与估算")
    parser.add_argument("--sample-limit", type=int, default=30, help="每个小区最多使用第一页前N条样本，默认30")
    parser.add_argument("--community-limit", type=int, default=0, help="最多处理多少个小区，默认0表示不限")
    parser.add_argument("--min-samples", type=int, default=1, help="最少有效样本数，默认1")
    parser.add_argument("--min-rent-per-sqm", type=float, default=10, help="有效租金单价下限，默认10元/㎡/月")
    parser.add_argument("--max-rent-per-sqm", type=float, default=500, help="有效租金单价上限，默认500元/㎡/月")
    parser.add_argument("--round-to", type=int, default=10, help="估算月租取整粒度，默认10元")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="按小区租房第一页估算二手房参考月租")
    add_arguments(arg_parser)
    enrich_rent_estimates(arg_parser.parse_args())
