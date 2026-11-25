#!/usr/bin/env python3
"""site/ の静的サイトを検証する。
- data.js の JSON 構造・必須項目・ID重複・ジャンル整合
- 画像パス（相対パス）が実在するか
- 外部リンクURLの形式（https / 許可ドメイン）
- index.html が参照するCSS/JSの実在、app.js が使う要素IDの存在
- app.js / data.js の括弧・クォートのバランス（構文の目視前チェック）
- ジャンル別件数・新着順の確認
"""
import html.parser
import json
import os
import re
import sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []
warnings = []


def fail(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


# ---------- data.js ----------
data_src = read("data.js")
start = data_src.index("{")
end = data_src.rindex("}") + 1
try:
    data = json.loads(data_src[start:end])
except json.JSONDecodeError as e:
    fail(f"data.js が JSON として解釈できません: {e}")
    print("\n".join(errors))
    sys.exit(1)

genres = [g["key"] for g in data["genres"]]
products = data["products"]
required = ["id", "date", "genre", "mall", "title", "price", "feature", "url", "img"]

seen = set()
allowed_hosts = {"a.r10.to", "amzn.to", "link.amazon", "r.8to.jp", "www.rebates.jp"}
for i, p in enumerate(products):
    label = p.get("id", f"#{i}")
    for key in required:
        if not p.get(key):
            fail(f"{label}: 必須項目 {key} が空です")
    if p["id"] in seen:
        fail(f"{label}: id が重複しています")
    seen.add(p["id"])
    if p["genre"] not in genres or p["genre"] == "all":
        fail(f"{label}: 未知のジャンル {p['genre']}")
    if p["mall"] not in {"rakuten", "amazon", "service"}:
        fail(f"{label}: 未知のモール {p['mall']}")
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+09:00$", p["date"]):
        fail(f"{label}: 日時の書式が不正 {p['date']}")
    u = urlparse(p["url"])
    if u.scheme != "https":
        fail(f"{label}: URL が https ではありません {p['url']}")
    if u.netloc not in allowed_hosts:
        fail(f"{label}: 想定外のリンク先 {u.netloc}")
    img = p["img"]
    if not os.path.isfile(os.path.join(ROOT, img)):
        fail(f"{label}: 画像が見つかりません {img}")
    if p.get("post"):
        pu = urlparse(p["post"])
        if pu.scheme != "https" or pu.netloc not in {"x.com", "twitter.com"}:
            fail(f"{label}: X投稿URLが不正 {p['post']}")

# 新着順の妥当性（データ内の並びは問わないが、日付が範囲内か）
start_date = data.get("periodStart", "2026-11-08")
end_date = data.get("updatedAt", "2026-11-25")
for p in products:
    if not (start_date <= p["date"][:10] <= end_date):
        fail(f"{p['id']}: 掲載期間外の日付 {p['date']}（{start_date}〜{end_date}）")

# ---------- index.html ----------
class Collector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.refs = []          # (tag, attr, value)
        self.stack = []
        self.problems = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                self.problems.append(f"HTML: id 重複 {a['id']}")
            self.ids.add(a["id"])
        if tag == "a" and "href" in a:
            self.refs.append(("a", "href", a["href"], a))
        if tag in ("img", "script", "link") and ("src" in a or "href" in a):
            v = a.get("src") or a.get("href")
            self.refs.append((tag, "src/href", v, a))
        if tag not in ("meta", "link", "img", "br", "hr", "input", "source", "path", "circle"):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in ("meta", "link", "img", "br", "hr", "input", "source", "circle", "path", "rect", "line", "polygon"):
            return
        if not self.stack:
            self.problems.append(f"HTML: 対応する開始タグがない終了タグ </{tag}>")
            return
        top = self.stack.pop()
        if top != tag:
            self.problems.append(f"HTML: タグの入れ子が不正 <{top}> … </{tag}>")

html_src = read("index.html")
parser = Collector()
parser.feed(html_src)
if parser.stack:
    parser.problems.append(f"HTML: 閉じられていないタグ {parser.stack}")
for pr in parser.problems:
    fail(pr)

for tag, _attr, value, attrs in parser.refs:
    if tag == "a":
        if not value.startswith("http") and not value.startswith("#"):
            fail(f"HTML: リンク先が相対パス/不正です {value}")
        if value.startswith("http") and 'rel="noopener noreferrer"' not in html_src[html_src.index(value) - 200:html_src.index(value) + 200]:
            warn(f"HTML: target=_blank の rel 未設定の可能性 {value}")
    else:
        if value.startswith("http"):
            continue
        if not os.path.isfile(os.path.join(ROOT, value)):
            fail(f"HTML: 参照ファイルが見つかりません {value}")

for must in ("search", "clear-search", "genre-tabs", "product-list", "result-count", "empty-state"):
    if must not in parser.ids:
        fail(f"HTML: app.js が使う id={must} がありません")

# 必須の表示文言（景表法・ステマ規制対応）
for text in ("アフィリエイト広告（PR）を含みます", "価格・在庫はリンク先の最新情報"):
    if text not in html_src:
        fail(f"HTML: 必須表記「{text}」がありません")

# ---------- JS 構文チェック（括弧・クォートのバランス） ----------
def js_balance(src, name):
    depth = {"(": 0, "[": 0, "{": 0}
    pairs = {")": "(", "]": "[", "}": "{"}
    i, n = 0, len(src)
    state = None  # None / "'" / '"' / '`' / "//" / "/*"
    prev_significant = None
    while i < n:
        ch = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if state in ("'", '"', "`"):
            if ch == "\\":
                i += 2
                continue
            if ch == state:
                state = None
        elif state == "//":
            if ch == "\n":
                state = None
        elif state == "/*":
            if ch == "*" and nxt == "/":
                state = None
                i += 2
                continue
        else:
            # 正規表現リテラル（/.../g）は前の記号からヒューリスティックに判定して読み飛ばす
            if ch == "/" and nxt not in ("/", "*") and prev_significant in set("(,=:[!&|?{};+\n") | {None}:
                i += 1
                while i < n:
                    if src[i] == "\\":
                        i += 2
                        continue
                    if src[i] == "/":
                        i += 1
                        break
                    i += 1
                prev_significant = "/"
                continue
            if ch == "/" and nxt == "/":
                state = "//"
                i += 2
                continue
            if ch == "/" and nxt == "*":
                state = "/*"
                i += 2
                continue
            if ch in "'\"`":
                state = ch
            elif ch in depth:
                depth[ch] += 1
            elif ch in pairs:
                depth[pairs[ch]] -= 1
                if depth[pairs[ch]] < 0:
                    fail(f"{name}: 対応しない閉じ括弧 {ch} (offset {i})")
                    return
        if state is None and not ch.isspace():
            prev_significant = ch
        i += 1
    if state in ("'", '"', "`"):
        fail(f"{name}: 閉じていない文字列リテラル {state}")
    if state in ("/*",):
        fail(f"{name}: 閉じていないブロックコメント")
    for k, v in depth.items():
        if v != 0:
            fail(f"{name}: 括弧の対応が不正 {k} 残り {v}")


js_balance(read("app.js"), "app.js")
js_balance(data_src, "data.js")

# ---------- 集計 ----------
counts = {}
for p in products:
    counts[p["genre"]] = counts.get(p["genre"], 0) + 1

by_date = sorted(products, key=lambda p: p["date"], reverse=True)

print("=== 検証結果 ===")
if errors:
    print(f"NG: {len(errors)} 件")
    for e in errors:
        print("  -", e)
else:
    print("OK: エラー 0 件")
if warnings:
    print(f"（参考）警告 {len(warnings)} 件")
    for w in warnings:
        print("  -", w)

print(f"\n掲載商品数: {len(products)} 件（id重複なし）")
label = {g["key"]: g["label"] for g in data["genres"]}
for g in data["genres"]:
    if g["key"] == "all":
        continue
    print(f"  - {label[g['key']]}: {counts.get(g['key'], 0)} 件")
print(f"\n最新5件（新着順）:")
for p in by_date[:5]:
    print(f"  {p['date'][5:16]}  {p['title']}")
print(f"最古: {by_date[-1]['dates'] if False else by_date[-1]['date'][5:16]} {by_date[-1]['title']}")

img_files = [f for f in os.listdir(os.path.join(ROOT, "assets"))]
print(f"\nassets: {len(img_files)} ファイル（jpg {len([f for f in img_files if f.endswith('.jpg')])} / svg {len([f for f in img_files if f.endswith('.svg')])}）")
used = {os.path.basename(p['img']) for p in products}
unused = sorted(set(img_files) - used)
if unused:
    print(f"未使用アセット: {unused}")

sys.exit(1 if errors else 0)
