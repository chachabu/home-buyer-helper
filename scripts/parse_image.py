#!/usr/bin/env python3
"""
从图片识别房源信息（OCR，买房版）
用法: python parse_image.py --image path/to/image.jpg

支持识别图片中的文字信息，提取：
- 小区名称
- 总价（万元）
- 户型
- 面积
- 联系方式
- 其他描述
"""

import json
import os
import re
import argparse
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DATA_FILE = os.path.join(DATA_DIR, "listings.json")

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

def extract_info_from_text(text):
    """从 OCR 文本中提取房源信息"""
    info = {}
    lines = text.split('\n')

    # 总价（万元）
    for pat in [r'(\d+(?:\.\d+)?)\s*万', r'总价[：:]\s*(\d+(?:\.\d+)?)\s*万']:
        m = re.search(pat, text)
        if m:
            v = float(m.group(1))
            if 50 <= v <= 50000:
                info["price_wan"] = v
                break

    # 单价
    unit_m = re.search(r'(\d+(?:\.\d+)?)\s*元/㎡', text)
    if unit_m:
        info["unit_price"] = float(unit_m.group(1))

    # 户型
    room_m = re.search(r'(\d+)室(\d+)厅', text)
    if room_m:
        info["room_type"] = f"{room_m.group(1)}室{room_m.group(2)}厅"

    # 面积
    area_m = re.search(r'(\d+(?:\.\d+)?)\s*㎡', text)
    if area_m:
        info["area"] = float(area_m.group(1))

    # 联系方式
    phone_m = re.search(r'1[3-9]\d{9}', text)
    if phone_m:
        info["contact"] = phone_m.group(0)

    # 小区名称（第一行非空非数字）
    for line in lines:
        line = line.strip()
        if line and 2 < len(line) < 30:
            if not re.match(r'^\d+$', line) and not any(w in line for w in ['万', '元', '室', '厅', '㎡', '/']):
                info["name"] = line
                break

    # 朝向
    orient_m = re.search(r'朝\s*(南|北|东|西|南北)', text)
    if orient_m:
        info["orientation"] = orient_m.group(1)

    # 交通
    trans_m = re.search(r'(距地铁[\u4e00-\u9fa5\d]+站[\d\u4e00-\u9fa5]*\d+米)', text)
    if trans_m:
        info["transport"] = trans_m.group(1).strip()

    # 满五唯一
    if '满五唯一' in text:
        info["is_full5_unique"] = True

    return info

def parse_image(args):
    if not os.path.exists(args.image):
        print(f"图片不存在: {args.image}")
        return

    text = ""
    try:
        from PIL import Image
        import pytesseract
        image = Image.open(args.image)
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        print("✅ Tesseract OCR 识别成功")
    except ImportError:
        print("⚠️ 未安装 pytesseract，尝试 easyocr...")
    except Exception as e:
        print(f"⚠️ Tesseract 失败: {e}")

    if not text:
        try:
            import easyocr
            reader = easyocr.Reader(['ch_sim', 'en'])
            result = reader.readtext(args.image)
            text = '\n'.join([item[1] for item in result])
            print("✅ EasyOCR 识别成功")
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️ EasyOCR 失败: {e}")

    if not text:
        print("\n❌ OCR 识别失败，请先安装：")
        print("   方案1: pip3 install pytesseract pillow && brew install tesseract tesseract-lang")
        print("   方案2: pip3 install easyocr")
        return

    print("\n📝 识别文本：")
    print("-" * 40)
    print(text[:500] if len(text) > 500 else text)
    if len(text) > 500:
        print("... (已截断)")
    print("-" * 40)

    info = extract_info_from_text(text)
    if not info:
        print("\n⚠️ 未能提取到房源信息")
        return

    print("\n📋 提取结果：")
    for k, v in info.items():
        print(f"   {k}: {v}")

    listings = load_listings()
    new_id = f"H{len(listings)+1:03d}"
    info["id"] = new_id
    info["status"] = "待看房"
    info["created_at"] = datetime.now().isoformat()
    listings.append(info)
    save_listings(listings)

    print(f"\n✅ 已保存为房源 ID: {new_id}，请补充完善其他信息")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从图片识别房源信息（买房版）")
    parser.add_argument("--image", required=True, help="图片路径")
    args = parser.parse_args()
    parse_image(args)
