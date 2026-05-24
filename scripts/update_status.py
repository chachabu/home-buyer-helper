#!/usr/bin/env python3
"""
更新房源状态
用法: python update_status.py --id H001 --status 已看房 [--notes "备注"]
"""

import json
import os
import argparse
from datetime import datetime

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/home-buyer-data")
DATA_FILE = os.path.join(DATA_DIR, "listings.json")

VALID_STATUS = ["待看房", "已看房", "有意向", "已放弃", "已签约", "已过户"]

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

def update_status(args):
    listings = load_listings()
    listing = next((l for l in listings if l.get("id") == args.id), None)
    if not listing:
        print(f"未找到房源: {args.id}")
        return

    old_status = listing.get("status", "")
    listing["status"] = args.status
    listing["updated_at"] = datetime.now().isoformat()

    if args.notes:
        listing["status_notes"] = args.notes

    save_listings(listings)
    print(f"✅ 房源 [{listing.get('name')}] 状态已更新: {old_status} → {args.status}")
    if args.notes:
        print(f"   备注: {args.notes}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="更新房源状态")
    parser.add_argument("--id", required=True, help="房源ID")
    parser.add_argument("--status", required=True, choices=VALID_STATUS, help="新房源状态")
    parser.add_argument("--notes", help="状态变更备注")
    args = parser.parse_args()
    update_status(args)
