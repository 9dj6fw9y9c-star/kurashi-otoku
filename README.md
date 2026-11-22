# インスタ用 商品まとめサイト（site/）

Instagram（@mikohuo2）のプロフィールリンクから開く、X（@Mikohup2）で紹介した商品・お得情報のジャンル別まとめページです。ビルド不要の静的サイトで、このフォルダをそのままWebサーバーのルートに置けば公開できます（GitHub Pages も可）。

## ファイル構成

```
site/
├── index.html          ページ本体（ヘッダー・PR表記・検索・タブ・一覧・フッター）
├── styles.css          デザイン（スマホ375〜430px最適化 / PCは2カラム）
├── data.js             掲載データ（41件・ジャンル6区分）※ここを直せば一覧が変わる
├── app.js              描画・ジャンル絞り込み・キーワード検索・新着順ソート
├── assets/             商品画像（幅600pxに最適化したJPEG 35枚＋プレースホルダーSVG 7枚）
├── image_map.json      画像の元ファイル対応表（downloads/ の実商品画像 → assets/）
└── tools/
    ├── build_assets.py 画像の再生成（Pillow。downloads/ から読み、600px・品質80で書き出す）
    ├── validate_site.py データ構造・画像パス・リンク形式・HTML/JS構文の全件検証
    └── preview_render.py カード描画のDOM検証（JSエンジンなしで行う補助チェック）
```

## 掲載内容

- 対象期間: 2026-11-08 〜 2026-11-22 に X（@Mikohup2）で実際に配信した投稿
- 掲載数: 41件（暖房・冬家電9 / キッチン・ガジェット8 / 収納・掃除・日用品8 / ファッション・美容・健康5 / グルメ・お取り寄せ4 / お得・キャンペーン7）
- 各カード: 商品画像・モールバッジ（楽天市場 / Amazon / 公式・サービス）・配信日・商品名・価格目安・事実ベースの特徴・口コミ件数・購入ボタン・（記録があるものは）X投稿へのリンク
- 新着順（配信日時の降順）で表示し、11/20以降の6件に NEW バッジ

## 表記ルール（編集時に守ること）

- ヘッダー直下に「※本ページはアフィリエイト広告（PR）を含みます」「※価格・在庫はリンク先の最新情報をご確認ください」を常時表示（景表法・ステマ規制・ASP規約対応）。
- 未購入の商品について一人称の体験談は書かない。特徴は商品ページの公開情報（価格・口コミ件数・仕様）のみ。
- 画像がない案件（A8.netのサービス系など）は `assets/ph-*.svg` のプレースホルダーを使う。
- 掲載当時と在庫が変わった商品は `note` フィールドで注記する（例: はえぬき）。

## データの直し方

`data.js` の `products` 配列に1件ずつ追加・修正します。

```json
{
  "id": "kabi-kirei",
  "date": "2026-11-21T20:00:00+09:00",
  "genre": "daily",
  "mall": "rakuten",
  "title": "コジット お風呂のカビきれい",
  "price": "1,320円〜（税込）",
  "review": "★4.26（629件）",
  "feature": "天井に貼る・吊るすだけ。9種類のカビ対策で効果は約6ヶ月、日本製。",
  "url": "https://a.r10.to/hPSp5W",
  "img": "assets/kabi-kirei.jpg",
  "post": "https://x.com/Mikohup2/status/2124095477201195315",
  "note": "（任意）在庫切れなど補足"
}
```

- `genre` は `heating` / `kitchen` / `daily` / `beauty` / `food` / `deals`
- `mall` は `rakuten`（楽天市場）/ `amazon`（Amazon）/ `service`（公式・サービス）
- 画像を差し替えるときは `downloads/` に元画像を置き `image_map.json` に追記 → `python3 tools/build_assets.py`

## 検証

```bash
python3 tools/validate_site.py   # データ・画像パス・リンク形式・HTML/JS構文
python3 tools/preview_render.py  # カード描画のDOM整合
```

## 公開するには

1. この `site/` の中身をそのまま静的ホスティングへ（GitHub Pages なら リポジトリ直下に index.html を置いて Pages を有効化）。
2. 公開URLを Instagram のプロフィール「ウェブサイト」欄に設定（この欄はスマホアプリからのみ編集可）。
3. 価格・在庫は変わるため、1〜2週間ごとに `validate_site.py` とリンク先の確認を行う。
