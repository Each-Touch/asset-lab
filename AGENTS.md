# Each-Touch Asset Lab — Autonomous Operating Manual (`AGENTS.md`)

> Scope: `/Users/zhaozixu/.gemini/antigravity/scratch/asset-lab`
> Schedule: Mon/Wed/Fri 15:00 Asia/Shanghai
> Positioning: Commercial CC0 Procedural Game & Creator Asset Packs (Pure DSP / Python PIL / Procedural Geometry — ZERO Generative AI).

## Strict Red Lines
1. **Zero Collision**: NEVER touch `运营总台/`, `game-studio-ops/`, `each-touch-arcade/`, `forge-tools/`, `print-play-lab/`, `dev-kits/`, or existing personal `ego-browser` spaces (`2, 3, 27, 31, 50, 51, 54, 61, 77`).
2. **Paywall Protection**: Paid full packs MUST match `releases/*/*-full-*` or `releases/*/paid_*` so `.gitignore` blocks them from public GitHub repos! Only showcase pages + lightweight free demos go to GitHub Pages; full packs upload ONLY to `itch.io` behind the Paid paywall (`$2.99–$3.99` + Free Demo).
3. **Zero Generative AI & Zero External CDNs**: All audio/images/UI generated purely by math/DSP/PIL/Canvas; `Generative AI disclosure` on itch.io MUST be `No`.
4. **Browser & Visual Audit Gate**: Fresh temporary `taskSpace(...)`, close with `await task.finish({ keep: [] })` in a separate final script; never `read_file` PNGs in main conversation (`research` `Model: "pro"` only). Never submit personal tax/bank forms.

## 5-Stage Autonomous Production Loop
1. Run `python3 scripts/fetch_metrics.py` & inspect `https://itch.io/dashboard` (read-only); pick next `TODO` from `ops/01_高转化付费素材排期池.md` (`IN_PROGRESS`).
2. Write deterministic generator in `scripts/` producing Paid Full ZIP + Free Demo ZIP + web preview assets + `630x500` cover + `1280x720` preview sheet; run `python3 scripts/build_showcase.py`.
3. Run temporary HTTP QA (`1280x800` & `390x844`, zero console/404/overflow) and `research` (`Model: "pro"`) visual review until `VERDICT: PASS`.
4. Verify `git status` excludes Paid Full ZIPs, push `Each-Touch/asset-lab` `main`, verify `https://each-touch.github.io/asset-lab/` `HTTP 200`; upload Paid Full ZIP + Free Demo ZIP (checked Demo) to `itch.io` (`Classification: Game assets`, `Paid` `$2.99–$3.99`, `Generative AI: No`), publish `Public`, verify live Buy/Demo CTAs.
5. Update `packs-catalog.json` with live `itchUrl`, rebuild showcase, mark `DONE`, log metrics & lessons in `ops/00..02`, commit & push.
