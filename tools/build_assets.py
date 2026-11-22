#!/usr/bin/env python3
"""downloads/ の実商品画像を site/assets/ へ最大幅600pxの軽量JPEGとして書き出す。"""
import json
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # site/
WORK = os.path.dirname(ROOT)
SRC_DIR = os.path.join(WORK, "downloads")
OUT_DIR = os.path.join(ROOT, "assets")
MAX_W = 600
QUALITY = 80

with open(os.path.join(ROOT, "image_map.json"), encoding="utf-8") as f:
    image_map = json.load(f)  # {slug: source filename in downloads/}

os.makedirs(OUT_DIR, exist_ok=True)
rows = []
for slug, src in image_map.items():
    src_path = os.path.join(SRC_DIR, src)
    im = Image.open(src_path)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    if im.width > MAX_W:
        h = round(im.height * MAX_W / im.width)
        im = im.resize((MAX_W, h), Image.LANCZOS)
    if im.mode == "L":
        im = im.convert("RGB")
    out_name = f"{slug}.jpg"
    out_path = os.path.join(OUT_DIR, out_name)
    im.save(out_path, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    rows.append((out_name, im.size, os.path.getsize(out_path)))

total = sum(r[2] for r in rows)
for n, size, b in rows:
    print(f"{n:42s} {size[0]}x{size[1]:<5d} {b/1024:7.1f} KB")
print(f"\n{len(rows)} images / total {total/1024:.1f} KB / avg {total/len(rows)/1024:.1f} KB")
