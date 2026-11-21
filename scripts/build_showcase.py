#!/usr/bin/env python3
"""Build Each-Touch Asset Lab public GitHub Pages storefront."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CATALOG_PATH = ROOT / "packs-catalog.json"
BASE_URL = "https://each-touch.github.io/asset-lab"


def _esc(s: object) -> str:
    return html.escape(str(s or ""), quote=True)


def main() -> int:
    packs = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / ".nojekyll").touch()

    pack = packs[0]
    manifest_p = DOCS / "packs" / pack["slug"] / "manifest.json"
    manifest = json.loads(manifest_p.read_text(encoding="utf-8")) if manifest_p.is_file() else {"categories": [], "tracklist": []}
    cats = manifest.get("categories", [])

    itch_buy_url = pack.get("itchUrl") or "https://each-touch.itch.io/"

    sample_rows = []
    for idx, c in enumerate(cats, start=1):
        sample_src = f"./packs/{_esc(pack['slug'])}/{_esc(c['sampleFile'])}"
        sample_rows.append(
            f"""
            <div class="sample-row">
              <div class="sample-meta">
                <span class="mono idx">{idx:02d}</span>
                <div>
                  <strong>{_esc(c['category'])}</strong>
                  <span>{_esc(c['count'])} files (WAV + OGG) · Sample: {_esc(c['sampleTitle'])}</span>
                </div>
              </div>
              <audio controls preload="none" src="{sample_src}"></audio>
            </div>
            """
        )

    cards_html = []
    for p in packs:
        buy_url = p.get("itchUrl") or "https://each-touch.itch.io/"
        hl_html = "".join(f"<li>{_esc(h)}</li>" for h in p.get("highlights", []))
        cards_html.append(
            f"""
            <article class="pack-card">
              <div class="pack-top">
                <span class="badge badge-cyan">{_esc(p['category'])}</span>
                <span class="badge badge-amber">${p['priceUsd']:.2f} USD · Free Demo</span>
              </div>
              <h2>{_esc(p['shortTitle'])}</h2>
              <p class="pack-desc">{_esc(p['tagline'])}</p>
              <ul class="pack-list">{hl_html}</ul>
              <div class="pack-cta">
                <a class="btn btn-primary" href="{_esc(buy_url)}" target="_blank" rel="noopener noreferrer">Get Full Pack (${p['priceUsd']:.2f}) / Free Demo on itch.io</a>
              </div>
            </article>
            """
        )

    ld_json = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": pack["shortTitle"],
            "description": pack["tagline"],
            "brand": {"@type": "Brand", "name": "Each-Touch Asset Lab"},
            "offers": {
                "@type": "Offer",
                "priceCurrency": "USD",
                "price": str(pack["priceUsd"]),
                "availability": "https://schema.org/InStock",
                "url": itch_buy_url,
            },
        },
        ensure_ascii=False,
    )

    page_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Each-Touch Asset Lab — CC0 Procedural Game Asset Packs (Zero AI)</title>
  <meta name="description" content="Commercial-safe CC0 game audio, UI kits, VFX &amp; tiles synthesized deterministically with zero generative AI. Audition samples online and grab free demos." />
  <link rel="canonical" href="{BASE_URL}/" />
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%2338bdf8'/%3E%3Ctext x='16' y='21' text-anchor='middle' font-family='monospace' font-weight='800' font-size='14' fill='%230b0f14'%3EAL%3C/text%3E%3C/svg%3E" />
  <script type="application/ld+json">{ld_json}</script>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b0f14; --surface: #131922; --panel: #19212c; --border: rgba(148,163,184,0.18);
      --text: #f1f5f9; --sec: #b6c4d6; --muted: #8b9bb4; --amber: #f59e0b; --cyan: #38bdf8; --green: #10b981;
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--text); font-family: var(--font); font-size: 14px; line-height: 1.5; overflow-x: hidden; }}
    a {{ color: var(--cyan); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .mono {{ font-family: var(--mono); }}
    .topbar {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 18px; background: var(--surface); border-bottom: 1px solid var(--border); flex-wrap: wrap; }}
    .brand {{ display: inline-flex; align-items: center; gap: 10px; color: var(--text); font-weight: 800; font-size: 15px; }}
    .mark {{ width: 28px; height: 28px; border-radius: 7px; background: linear-gradient(135deg, #38bdf8, #0284c7); color: #0b0f14; display: inline-flex; align-items: center; justify-content: center; font-family: var(--mono); font-weight: 800; font-size: 13px; }}
    .badges {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .badge {{ padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 700; border: 1px solid var(--border); background: var(--panel); color: var(--sec); white-space: nowrap; }}
    .badge-amber {{ background: rgba(245,158,11,0.14); border-color: rgba(245,158,11,0.38); color: var(--amber); }}
    .badge-cyan {{ background: rgba(56,189,248,0.14); border-color: rgba(56,189,248,0.38); color: var(--cyan); }}
    .badge-green {{ background: rgba(16,185,129,0.14); border-color: rgba(16,185,129,0.38); color: var(--green); }}
    .wrap {{ max-width: 1180px; margin: 0 auto; padding: 18px 18px 28px; }}
    .hero {{ background: radial-gradient(circle at 86% 18%, rgba(56,189,248,0.15), transparent 45%), var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 22px 24px; display: grid; grid-template-columns: 1.4fr 1fr; gap: 20px; align-items: center; }}
    .hero h1 {{ margin: 8px 0 8px; font-size: clamp(22px, 3vw, 32px); line-height: 1.15; }}
    .hero p {{ margin: 0 0 14px; color: var(--sec); font-size: 14.5px; }}
    .btn {{ display: inline-flex; align-items: center; justify-content: center; padding: 9px 15px; border-radius: 7px; font-weight: 700; font-size: 13px; border: 1px solid rgba(148,163,184,0.3); background: var(--panel); color: var(--text); }}
    .btn:hover {{ text-decoration: none; border-color: var(--cyan); }}
    .btn-primary {{ background: var(--amber); border-color: var(--amber); color: #0b0f14; }}
    .hero-stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    .stat {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 11px 13px; }}
    .stat strong {{ display: block; color: var(--amber); font-size: 15px; }}
    .stat span {{ font-size: 12px; color: var(--sec); }}
    .section-title {{ margin: 22px 0 10px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); font-weight: 700; }}
    .pack-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 18px; display: flex; flex-direction: column; gap: 10px; }}
    .pack-top {{ display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; }}
    .pack-card h2 {{ margin: 2px 0 0; font-size: 19px; }}
    .pack-desc {{ margin: 0; color: var(--sec); }}
    .pack-list {{ margin: 0; padding-left: 18px; color: var(--sec); font-size: 13px; }}
    .audition-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
    .sample-row {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }}
    .sample-meta {{ display: flex; align-items: center; gap: 10px; min-width: 0; }}
    .sample-meta .idx {{ color: var(--amber); font-weight: 800; font-size: 13px; }}
    .sample-meta strong {{ display: block; font-size: 13px; }}
    .sample-meta span {{ display: block; font-size: 11.5px; color: var(--muted); }}
    .sample-row audio {{ height: 32px; max-width: 220px; width: 100%; }}
    .ecosystem {{ margin-top: 22px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; font-size: 12.5px; color: var(--sec); }}
    .eco-links {{ display: flex; gap: 12px; flex-wrap: wrap; }}
    @media (max-width: 820px) {{
      .hero {{ grid-template-columns: 1fr; padding: 16px; }}
      .hero .btn {{ width: 100%; }}
      .audition-grid {{ grid-template-columns: 1fr; }}
      .sample-row audio {{ max-width: 100%; }}
    }}
  </style>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="./"><span class="mark">AL</span><span>Each-Touch Asset Lab</span></a>
    <div class="badges">
      <span class="badge badge-green">100% CC0 Commercial-Safe</span>
      <span class="badge badge-cyan">Zero Generative AI</span>
      <span class="badge badge-amber">Free Demos + Full Packs</span>
    </div>
  </header>

  <main class="wrap">
    <section class="hero">
      <div>
        <span class="badge badge-cyan">Commercial Game Assets · Pure DSP &amp; Procedural Art</span>
        <h1>Royalty-Free CC0 Sound, UI &amp; Sprite Packs for Indie Devs</h1>
        <p>Every pack is crafted deterministically via code—zero AI slop, zero copyright grey zones, instant WAV + OGG / PNG downloads with free trial demos.</p>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <a class="btn btn-primary" href="{_esc(itch_buy_url)}" target="_blank" rel="noopener noreferrer">Buy Flagship 150-SFX Pack ($2.99)</a>
          <a class="btn" href="#audition">Audition 10 Live Samples</a>
        </div>
      </div>
      <div class="hero-stats">
        <div class="stat"><strong>150 SFX</strong><span>10 categories × 15 studio sounds</span></div>
        <div class="stat"><strong>300 Files</strong><span>44.1kHz 16-bit WAV + OGG</span></div>
        <div class="stat"><strong>Zero AI</strong><span>100% Python DSP synthesis</span></div>
        <div class="stat"><strong>Free Demo</strong><span>20 sounds free before buying</span></div>
      </div>
    </section>

    <div class="section-title">Featured Commercial Pack</div>
    <section>{"".join(cards_html)}</section>

    <div class="section-title" id="audition">Live Browser Audition (10 Categories · Zero-AI Audio Previews)</div>
    <section class="audition-grid">{"".join(sample_rows)}</section>

    <footer class="ecosystem">
      <span>Each-Touch Creative Ecosystem · Commercial-Safe Tools &amp; Assets</span>
      <div class="eco-links">
        <a href="https://each-touch.github.io/forge-tools/" target="_blank" rel="noopener noreferrer">Forge Tools (Free Web Synths)</a>
        <a href="https://each-touch.github.io/print-play-lab/" target="_blank" rel="noopener noreferrer">Print-Play Lab</a>
        <a href="https://each-touch.github.io/dev-kits/" target="_blank" rel="noopener noreferrer">Dev Kits</a>
        <a href="https://each-touch.github.io/" target="_blank" rel="noopener noreferrer">Each-Touch Arcade</a>
      </div>
    </footer>
  </main>
</body>
</html>
"""
    (DOCS / "index.html").write_text(page_html, encoding="utf-8")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (DOCS / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url>\n    <loc>{BASE_URL}/</loc>\n    <lastmod>{today}</lastmod>\n    <priority>1.0</priority>\n  </url>\n</urlset>\n',
        encoding="utf-8",
    )
    (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
    print(f"Built Asset Lab showcase -> {DOCS / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
