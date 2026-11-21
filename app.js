/* トモ｜暮らしとお得のキロク — まとめページ
   ジャンルタブ＋キーワード検索＋新着順の描画 */

(function () {
  "use strict";

  var data = window.SITE_DATA;
  if (!data || !Array.isArray(data.products)) {
    return;
  }

  var MALL = {
    rakuten: { label: "楽天市場", cls: "badge--rakuten" },
    amazon: { label: "Amazon", cls: "badge--amazon" },
    service: { label: "公式・サービス", cls: "badge--service" }
  };

  var GENRE_LABEL = {};
  data.genres.forEach(function (g) {
    GENRE_LABEL[g.key] = g.short || g.label;
  });

  var NEW_FROM = Date.parse("2026-11-20T00:00:00+09:00");

  var listEl = document.getElementById("product-list");
  var tabsEl = document.getElementById("genre-tabs");
  var searchEl = document.getElementById("search");
  var countEl = document.getElementById("result-count");
  var emptyEl = document.getElementById("empty-state");
  var clearEl = document.getElementById("clear-search");

  var state = { genre: "all", q: "" };

  /* 新着順（配信日時の降順） */
  var items = data.products.slice().sort(function (a, b) {
    return Date.parse(b.date) - Date.parse(a.date);
  });

  function norm(text) {
    return String(text || "")
      .toLowerCase()
      .replace(/[\s\u3000]+/g, "");
  }

  function esc(text) {
    return String(text == null ? "" : text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function dateParts(iso) {
    var d = new Date(iso);
    var mm = d.getMonth() + 1;
    var dd = d.getDate();
    var hh = ("0" + d.getHours()).slice(-2);
    var mi = ("0" + d.getMinutes()).slice(-2);
    return {
      short: mm + "/" + dd,
      full: d.getFullYear() + "年" + mm + "月" + dd + "日 " + hh + ":" + mi
    };
  }

  function countByGenre(key) {
    return items.filter(function (p) {
      return key === "all" || p.genre === key;
    }).length;
  }

  function buildTabs() {
    var html = data.genres.map(function (g) {
      var n = countByGenre(g.key);
      return (
        '<button type="button" class="tab" role="tab" data-genre="' +
        esc(g.key) +
        '" aria-selected="' +
        (state.genre === g.key ? "true" : "false") +
        '"><span>' +
        esc(g.short || g.label) +
        '</span><span class="tab-count">' +
        n +
        "</span></button>"
      );
    }).join("");
    tabsEl.innerHTML = html;
  }

  function cardHTML(p) {
    var mall = MALL[p.mall] || MALL.service;
    var d = dateParts(p.date);
    var isNew = Date.parse(p.date) >= NEW_FROM;
    var img = p.img || "assets/ph-generic.svg";

    return (
      '<article class="card">' +
      '<div class="card-main">' +
      '<a class="thumb" href="' +
      esc(p.url) +
      '" target="_blank" rel="noopener noreferrer" tabindex="-1" aria-hidden="true">' +
      '<img src="' +
      esc(img) +
      '" alt="' +
      esc(p.title) +
      '" width="600" height="600" loading="lazy" decoding="async">' +
      "</a>" +
      '<div class="card-body">' +
      '<div class="card-meta">' +
      '<span class="badge ' +
      mall.cls +
      '">' +
      mall.label +
      "</span>" +
      '<time class="date" datetime="' +
      esc(p.date) +
      '" title="' +
      esc(d.full) +
      'にXで紹介">' +
      d.short +
      "</time>" +
      (isNew ? '<span class="new">NEW</span>' : "") +
      '<span class="genre-chip">' +
      esc(GENRE_LABEL[p.genre] || "") +
      "</span>" +
      "</div>" +
      '<h2 class="card-title">' +
      esc(p.title) +
      "</h2>" +
      '<p class="card-price">' +
      esc(p.price) +
      "</p>" +
      '<p class="card-feature">' +
      esc(p.feature) +
      "</p>" +
      (p.review ? '<p class="card-review">' + esc(p.review) + "</p>" : "") +
      (p.note ? '<p class="card-note">※' + esc(p.note) + "</p>" : "") +
      "</div>" +
      "</div>" +
      '<div class="card-actions">' +
      '<a class="cta" href="' +
      esc(p.url) +
      '" target="_blank" rel="noopener noreferrer">購入・詳細ページを見る <span aria-hidden="true">→</span></a>' +
      (p.post
        ? '<a class="post-link" href="' +
          esc(p.post) +
          '" target="_blank" rel="noopener noreferrer">Xの投稿</a>'
        : "") +
      "</div>" +
      "</article>"
    );
  }

  function matches(p) {
    if (state.genre !== "all" && p.genre !== state.genre) {
      return false;
    }
    if (!state.q) {
      return true;
    }
    var haystack = norm(
      [
        p.title,
        p.feature,
        p.price,
        p.review,
        GENRE_LABEL[p.genre],
        (MALL[p.mall] || {}).label
      ].join(" ")
    );
    return haystack.indexOf(state.q) !== -1;
  }

  function render() {
    var shown = items.filter(matches);
    listEl.innerHTML = shown.map(cardHTML).join("");

    if (state.genre === "all" && !state.q) {
      countEl.textContent = "全 " + items.length + " 件";
    } else {
      countEl.textContent = items.length + " 件中 " + shown.length + " 件を表示";
    }

    emptyEl.hidden = shown.length !== 0;
    clearEl.hidden = !state.q;

    Array.prototype.forEach.call(tabsEl.querySelectorAll(".tab"), function (btn) {
      btn.setAttribute(
        "aria-selected",
        btn.getAttribute("data-genre") === state.genre ? "true" : "false"
      );
    });
  }

  tabsEl.addEventListener("click", function (e) {
    var btn = e.target.closest(".tab");
    if (!btn) {
      return;
    }
    state.genre = btn.getAttribute("data-genre");
    render();
  });

  var timer = null;
  searchEl.addEventListener("input", function () {
    var value = searchEl.value;
    window.clearTimeout(timer);
    timer = window.setTimeout(function () {
      state.q = norm(value);
      render();
    }, 120);
  });

  clearEl.addEventListener("click", function () {
    searchEl.value = "";
    state.q = "";
    render();
    searchEl.focus();
  });

  searchEl.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      searchEl.value = "";
      state.q = "";
      render();
    }
  });

  buildTabs();
  render();
})();
