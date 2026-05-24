#!/usr/bin/env python3
"""
批量导入房源（买房版，支持CSV和Excel）
用法: python import_listings.py --file path/to/file.csv

CSV必需字段：name,price_wan
可选字段：address,room_type,area,inner_area,floor,total_floors,orientation,year_built,building_age,
          decoration,property_type,house_type,is_full5_unique,has_parking,has_elevator,
          school_district,school_notes,transport,facilities,mortgage_balance,
          tax_estimate,agent_fee_rate,agent_fee,contact,pros,cons,source,url
"""

import json
import os
import argparse
import csv
from datetime import datetime

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/home-buyer-data")
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

def import_from_csv(file_path, listings):
    imported = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("name") or not row.get("price_wan"):
                continue
            new_id = f"H{len(listings) + imported + 1:03d}"
            listing = {
                "id": new_id,
                "name": row.get("name", "").strip(),
                "address": row.get("address", "").strip(),
                "price_wan": float(row.get("price_wan", 0)),
                "unit_price": float(row.get("unit_price", 0)) if row.get("unit_price") else 0,
                "room_type": row.get("room_type", "").strip(),
                "area": float(row.get("area", 0)) if row.get("area") else 0,
                "inner_area": float(row.get("inner_area", 0)) if row.get("inner_area") else 0,
                "floor": row.get("floor", "").strip(),
                "total_floors": row.get("total_floors", "").strip(),
                "orientation": row.get("orientation", "").strip(),
                "year_built": row.get("year_built", "").strip(),
                "building_age": int(row.get("building_age", 0)) if row.get("building_age") else 0,
                "decoration": row.get("decoration", "").strip(),
                "property_type": row.get("property_type", "商品房").strip(),
                "house_type": row.get("house_type", "普通住宅").strip(),
                "is_full5_unique": row.get("is_full5_unique", "").strip().lower() in ("true", "1", "yes", "是"),
                "has_parking": row.get("has_parking", "").strip(),
                "parking_price": float(row.get("parking_price", 0)) if row.get("parking_price") else 0,
                "has_elevator": row.get("has_elevator", "").strip(),
                "school_district": row.get("school_district", "").strip(),
                "school_notes": row.get("school_notes", "").strip(),
                "transport": row.get("transport", "").strip(),
                "facilities": row.get("facilities", "").strip(),
                "mortgage_balance": float(row.get("mortgage_balance", 0)) if row.get("mortgage_balance") else 0,
                "tax_estimate": float(row.get("tax_estimate", 0)) if row.get("tax_estimate") else 0,
                "agent_fee_rate": float(row.get("agent_fee_rate", 0.02)) if row.get("agent_fee_rate") else 0.02,
                "agent_fee": float(row.get("agent_fee", 0)) if row.get("agent_fee") else 0,
                "contact": row.get("contact", "").strip(),
                "pros": row.get("pros", "").strip(),
                "cons": row.get("cons", "").strip(),
                "source": row.get("source", "").strip(),
                "url": row.get("url", "").strip(),
                "status": "待看房",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            listings.append(listing)
            imported += 1
    return imported

def import_from_excel(file_path, listings):
    try:
        import pandas as pd
        df = pd.read_excel(file_path)
        imported = 0
        for _, row in df.iterrows():
            name = str(row.get("name", "")).strip()
            if not name or pd.isna(row.get("name")):
                continue
            new_id = f"H{len(listings) + imported + 1:03d}"
            def safe_float(v, default=0):
                try:
                    return float(v) if pd.notna(v) else default
                except Exception:
                    return default
            listing = {
                "id": new_id,
                "name": name,
                "address": str(row.get("address", "") or "").strip(),
                "price_wan": safe_float(row.get("price_wan")),
                "unit_price": safe_float(row.get("unit_price")),
                "room_type": str(row.get("room_type", "") or "").strip(),
                "area": safe_float(row.get("area")),
                "inner_area": safe_float(row.get("inner_area")),
                "floor": str(row.get("floor", "") or "").strip(),
                "total_floors": str(row.get("total_floors", "") or "").strip(),
                "orientation": str(row.get("orientation", "") or "").strip(),
                "year_built": str(row.get("year_built", "") or "").strip(),
                "building_age": int(safe_float(row.get("building_age"))),
                "decoration": str(row.get("decoration", "") or "").strip(),
                "property_type": str(row.get("property_type", "商品房") or "商品房").strip(),
                "house_type": str(row.get("house_type", "普通住宅") or "普通住宅").strip(),
                "is_full5_unique": str(row.get("is_full5_unique", "") or "").strip().lower() in ("true", "1", "yes", "是"),
                "has_parking": str(row.get("has_parking", "") or "").strip(),
                "parking_price": safe_float(row.get("parking_price")),
                "has_elevator": str(row.get("has_elevator", "") or "").strip(),
                "school_district": str(row.get("school_district", "") or "").strip(),
                "school_notes": str(row.get("school_notes", "") or "").strip(),
                "transport": str(row.get("transport", "") or "").strip(),
                "facilities": str(row.get("facilities", "") or "").strip(),
                "mortgage_balance": safe_float(row.get("mortgage_balance")),
                "tax_estimate": safe_float(row.get("tax_estimate")),
                "agent_fee_rate": safe_float(row.get("agent_fee_rate"), 0.02),
                "agent_fee": safe_float(row.get("agent_fee")),
                "contact": str(row.get("contact", "") or "").strip(),
                "pros": str(row.get("pros", "") or "").strip(),
                "cons": str(row.get("cons", "") or "").strip(),
                "source": str(row.get("source", "") or "").strip(),
                "url": str(row.get("url", "") or "").strip(),
                "status": "待看房",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            listings.append(listing)
            imported += 1
        return imported
    except ImportError:
        print("⚠️ 请先安装依赖: pip3 install pandas openpyxl")
        return 0
    except Exception as e:
        print(f"⚠️ Excel导入出错: {e}")
        return 0

def import_listings(args):
    if not os.path.exists(args.file):
        print(f"文件不存在: {args.file}")
        return
    listings = load_listings()
    initial = len(listings)
    fmt = args.format
    if not fmt:
        if args.file.endswith('.csv'):
            fmt = 'csv'
        elif args.file.endswith(('.xlsx', '.xls')):
            fmt = 'excel'
    if fmt == 'csv':
        imported = import_from_csv(args.file, listings)
    elif fmt == 'excel':
        imported = import_from_excel(args.file, listings)
    else:
        print("不支持的文件格式，请使用CSV或Excel")
        return
    save_listings(listings)
    print(f"✅ 导入完成！原有{initial}条 → 新增{imported}条 → 总计{len(listings)}条")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量导入房源（买房版）")
    parser.add_argument("--file", required=True, help="文件路径")
    parser.add_argument("--format", choices=["csv", "excel"], help="文件格式")
    args = parser.parse_args()
    import_listings(args)
