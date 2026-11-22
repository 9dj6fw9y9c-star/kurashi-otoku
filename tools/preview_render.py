#!/usr/bin/env python3
"""app.js のカード描画を Python で写経し、生成されるDOMが壊れていないかを検証する。
（JSエンジンが使えない環境のための補助チェック）
"""
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, "data.js"), encoding="utf-8").read()
data = json.loads(src[src.index("{"): src.rindex("}") + 1])

MALL = {
    "rakuten": ("楽天市場", "badge--rakuten"),
    "amazon": ("Amazon", "badge--amazon"),
    "service": ("公式・サービス", "badge--service"),
}
GENRE = {g["key"]: (g.get("short") or g["label"]) for g in data["genres"]}
NEW_FROM = "2026-11-20"


def esc(t):
    return html.escape(str(t), quote=True)


def card(p):
    label, cls = MALL[p["mall"]]
    mm, dd = p["date"][5:7].lstrip("0"), p["date"][8:10].lstrip("0")
    new = '<span class="new">NEW</span>' if p["date"][:10] >= NEW_FROM else ""
    review = f'<p class="card-review">{esc(p["review"])}</p>' if p.get("review") else ""
    note = f'<p class="card-note">{esc(p["note"])}</p>' if p.get("note") else ""
    post = (
        f'<a class="post-link" href="{esc(p["post"])}" target="_blank" rel="noopener noreferrer">Xの投稿を見る</a>'
        if p.get("post")
        else ""
    )
    return (
        '<article class="card">'
        '<div class="card-main">'
        f'<a class="thumb" href="{esc(p["url"])}"><img src="{esc(p["img"])}" alt="{esc(p["title"])}" width="600" height="600"></a>'
        '<div class="card-body">'
        f'<div class="card-meta"><span class="badge {cls}">{label}</span><time>{mm}/{dd}</time>{new}'
        f'<span class="genre-chip">{esc(GENRE[p["genre"]])}</span></div>'
        f'<h2 class="card-title">{esc(p["title"])}</h2>'
        f'<p class="card-price">{esc(p["price"])}</p>'
        f'<p class="card-feature">{esc(p["feature"])}</p>{review}{note}'
        "</div></div>"
        f'<div class="card-actions"><a class="cta" href="{esc(p["url"])}" target="_blank" rel="noopener noreferrer">購入・詳細ページを見る</a>{post}</div>'
        "</article>"
    )


class Checker(HTMLParser):
    VOID = {"img", "br", "meta", "link", "input", "hr"}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.problems = []
        self.articles = 0
        self.links = 0

    def handle_starttag(self, tag, attrs):
        if tag == "article":
            self.articles += 1
        if tag == "a":
            self.links += 1
            a = dict(attrs)
            if a.get("href") and not re.match(r"^https://", a["href"]):
                self.problems.append(f"リンク先が不正: {a.get('href')}")
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack or self.stack.pop() != tag:
            self.problems.append(f"タグの入れ子が不正 </{tag}>")


items = sorted(data["products"], key=lambda p: p["date"], reverse=True)
body = "".join(card(p) for p in items)
c = Checker()
c.feed(f"<div>{body}</div>")
print(f"カード {c.articles} 枚 / リンク {c.links} 本 / 閉じ残し {c.stack}")
for prob in c.problems[:10]:
    print(" -", prob)
missing_alt = sum(1 for p in items if not p["title"])
print("alt未設定:", missing_alt)
print("NEWバッジ:", sum(1 for p in items if p["date"][:10] >= NEW_FROM), "件")
print("X投稿リンクあり:", sum(1 for p in items if p.get("post")), "件")
sys.exit(1 if c.problems or c.stack else 0)
