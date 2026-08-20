# SnapStocks — Design Language & Site Structure

Working title: **SnapStocks**. Indian-market research tool for swing traders who
trade off the chart but want a fast fundamentals sanity-check before sizing a
position. This document is the single source of truth for how the site looks,
how it's organized on disk, and how to extend it without re-deriving decisions
already made here.

A working build lives in this folder (`/snapstocks`). Every token, color and
component named below is implemented there, not aspirational.

**Local preview:** links are root-relative (see §9), so opening
`index.html` straight off disk (`file://…`) will 404 its own CSS/JS —
serve the folder instead: `npx serve snapstocks` or
`python -m http.server --directory snapstocks`, then visit
`http://localhost:PORT/`.

---

## 1. Product framing → design consequences

| Who / what | Consequence for design |
|---|---|
| Traders acting fast, often on mobile between orders | Dense but scannable; no unnecessary clicks to a number; mobile-responsive by default, not as an afterthought |
| Fundamentals as a *sanity check*, not the main event | Fundamentals views read like a fast scorecard (screener.in-like), not an annual report |
| "AI-assisted" is a real feature, not a marketing coat of paint | AI touches are functional (an `.ai-note` callout with an actual insight) — never decorative chatbot skins |
| Direction (up/down) is a core primitive — sectors, stocks, macro series all get judged as advancing or declining | One consistent color+glyph system for direction, used identically everywhere |
| Must not look "made by Claude" or generic AI-tool-chrome | No purple-gradient-hero-with-rounded-blob cliché, no default shadcn look. Blue-led, white-based, restrained motion, a distinct wordmark treatment |

---

## 2. Visual direction

**White-based, blue-led, quietly technical.** The chrome is calm and mostly
monochrome (white surfaces, near-navy ink, hairline borders); blue is reserved
for interactive elements, brand marks and primary actions so it still reads as
intentional when it appears. A single violet accent, used sparingly, is the
signal for "this bit is AI-generated" — a gradient badge icon, a tinted callout
border — never spread across the whole page. Green and red are reserved
*exclusively* for market direction (see §4.3) so they never compete with the
brand or AI-accent color for attention.

Reference points used while designing (fintech + data-product conventions,
not literal copies): Stripe Dashboard and Linear for restrained blue-on-white
chrome and calm data density; Bloomberg/TradingView for how much information
density traders actually tolerate when it's well-grouped; screener.in for the
fundamentals-scorecard information architecture the Fundamentals view follows.

### What makes it *not* look Claude-made
- No default warm-orange/cream "AI assistant" palette — this is cool-toned and blue-anchored.
- No chat-bubble or sparkle-everywhere motifs — the AI accent is one violet hue, used in exactly the places listed in §4.2 and nowhere else.
- Headings are tight, high-contrast, and left-aligned; no centered hero copy stacks.
- Cards use a 1px hairline border + a very soft shadow, not the heavy glassmorphism / big-blur-blob look common to generated landing pages.

---

## 3. Typography

- **UI/body font:** `Inter` (self-host or load via `<link>` in production; system
  stack `system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`
  is the fallback and what the current build actually renders with, so it works
  offline with zero external requests).
- **No serif, no second display face.** One family, weight and size do all the
  work — this keeps fundamentals tables and deep-dive prose visually unified.
- **Numerals:** `font-variant-numeric: tabular-nums` on every table, KPI value,
  and chart axis — never on prose paragraphs (`.tnum` utility in `base.css`).
- **Scale:** `h1` 2rem / `h2` 1.5rem / `h3` 1.15rem / `h4` 1rem, `-0.01em`
  letter-spacing throughout headings, `text-wrap: balance` so headlines don't
  orphan a single word.
- **Body:** 15px base, 1.55 line-height. Deep-dive report prose caps at `70ch`
  measure (`p { max-width: 70ch }`) for readability; data pages don't need the
  cap since they're table/card-dominated, not long-form.

---

## 4. Color system

Every color is a CSS custom property defined once in
[`assets/css/tokens.css`](assets/css/tokens.css) — no raw hex anywhere else in
the codebase. Colors were chosen and order-tested with Anthropic's dataviz
color-formula method (categorical hue order, CVD simulation, contrast) rather
than picked by eye; the validator output behind the categorical set is below
so future additions can be checked the same way.

### 4.1 Brand blue — chrome, links, primary actions

| Token | Light | Use |
|---|---|---|
| `--brand-500` | `#3366FF` | Primary buttons, active nav state, link color, focus ring |
| `--brand-600` / `--brand-700` | `#2251E0` / `#1A3FB8` | Hover/active states, headings-on-tint |
| `--brand-50` / `--brand-100` | `#EEF3FF` / `#DCE7FF` | Active-tab background, tinted badges |
| `--brand-900` | `#101F5E` | Reserved for dark-mode deep accents |

Blue is **UI chrome only** — it never encodes data magnitude or direction, so
it can't be confused with the green/red direction system.

### 4.2 AI accent — violet, sparing

| Token | Light | Use |
|---|---|---|
| `--ai-500` | `#7C5CFC` | AI-insight badge icon, `.ai-note` callout gradient/border, "Deep-dive available" pill |
| `--ai-600` | `#6238E0` | Text on `.ai-note` |

Rule: **one violet touch per screen region, max.** If a page has an AI insight
callout, that's its one violet moment — don't also tint the hero or nav with it.

### 4.3 Direction (diverging green ↔ red) — reserved for price/return/momentum

| Token | Light | Dark | Use |
|---|---|---|---|
| `--up` / `--up-strong` | `#1A9850` / `#0B7A3D` | `#3DDC84` / `#63E39D` | Positive return text, up-arrow glyph |
| `--up-tint` / `--up-tint-strong` | `#E3F7EA` / `#C3EED3` | `#113322` / `#164429` | Heatmap-style cell backgrounds, light fills |
| `--down` / `--down-strong` | `#D8342A` / `#B0201A` | `#FF6B5E` / `#FF8A7F` | Negative return text, down-arrow glyph |
| `--down-tint` / `--down-tint-strong` | `#FCE7E5` / `#F7C7C2` | — | Heatmap-style cell backgrounds |
| `--flat` / `--flat-tint` | `#98A2B3` / `#F1F3F7` | — | No-change / neutral state |

**Hard rule, not a suggestion:** direction is never color-alone. Red/green is
the single hardest pair for color-blind readers (~8% of men), so every use of
`--up`/`--down` ships with a glyph (▲/▼ triangle, see `.dir` in
`components.css`) or an explicit sign (`+`/`−`) in the same element. A designer
adding a new up/down indicator must include the glyph — that's the CVD
mitigation, not an optional flourish.

This pair is deliberately **separate from the brand blue and from the AI
violet** — nothing in the direction system can be mistaken for a UI or AI
signal, and vice versa.

### 4.4 Sequential blue — magnitude (volume, AI confidence score, etc.)

Single hue, light→dark: `--seq-100 #DCE7FF` → `--seq-700 #1A3FB8`. Use for any
non-directional magnitude (e.g. a future "AI confidence" meter) where more
saturation/darkness = more of something, with no positive/negative sign.

### 4.5 Categorical — multi-series identity (sector rotation trails, multi-line macro charts)

Fixed order, validated with `dataviz/scripts/validate_palette.js` against a
white surface (light) and `#0B1220` (dark) — all six checks pass in both
modes; amber (`--cat-3`) sits below 3:1 contrast by design and requires a
direct label or legend whenever used, never a bare fill:

| Slot | Hue | Light | Dark |
|---|---|---|---|
| 1 | blue | `#2F6FED` | `#4C86FF` |
| 2 | teal | `#0EA5A8` | `#1D9C99` |
| 3 | amber *(needs label — sub-3:1 contrast)* | `#E08E0B` | `#C97A16` |
| 4 | violet | `#8B3FE8` | `#9457EE` |
| 5 | rose | `#E0578A` | `#D25E85` |
| 6 | indigo | `#5B6EE8` | `#6B7CF2` |

Assign in this fixed order, never cycle or reorder per-page. Note slot 4
(violet) is a *different, more saturated* violet than the AI-accent
`--ai-500` — don't reuse `--ai-500` as a categorical series color, and don't
reuse `--cat-4` as the AI-accent; they read as the same hue family but serve
different jobs (identity vs. "this is AI-generated").

When adding a 7th/8th series or a scatter/small-multiples form where any two
series can sit adjacent, re-run the validator with `--pairs all` — the
existing six were only tested on the adjacent pairlist. Cut to "Other" or
facet rather than extending the hue count past what validates.

### 4.6 Status (fixed, reserved — good/warning/serious/critical)

Used for system/data-quality state (e.g. a red-flag count on a fundamentals
page, a "data may be stale" notice) — **not** for price direction, which
always uses §4.3 instead, even though the colors are adjacent. A status pill
is always icon-dot + label (`.pill-*` classes in `components.css`), never a
bare color chip.

| Role | Light | Dark |
|---|---|---|
| Good | `#1A9850` | `#3DDC84` |
| Warning | `#B9790A` | `#E0A83C` |
| Serious | `#C24E17` | `#E8834D` |
| Critical | `#D8342A` | `#FF6B5E` |

### 4.7 Neutrals & surfaces

| Token | Light | Dark |
|---|---|---|
| `--bg` / `--surface` | `#FFFFFF` | `#0A0E1A` / `#10162A` |
| `--surface-sunken` | `#F5F7FC` | `#0D1220` |
| `--border` / `--border-strong` | `#E4E8F1` / `#CBD3E3` | `#232B42` / `#33405F` |
| `--text` | `#0B1220` | `#F2F5FC` |
| `--text-secondary` | `#4B5567` | `#B7C0D6` |
| `--text-muted` | `#8892A6` | `#7C879E` |

**The site defaults to light** — that's the product requirement (white
background, "not look like a chatbot skin"). Dark mode is implemented as a
secondary theme (`tokens.css` has both the `prefers-color-scheme` block and an
explicit `[data-theme="dark"]` override via `assets/js/theme.js`) but every
page should be designed and reviewed in light mode first.

---

## 5. Spacing, radius, shadow

4px base spacing scale: `--space-1` (4px) through `--space-8` (64px) — see
`tokens.css`. Radius: `--radius-sm` 6px (buttons, inputs), `--radius-md` 10px
(stat tiles, small cards), `--radius-lg` 16px (cards, panels), `--radius-pill`
999px (badges, segmented controls). Shadows are soft and blue-tinted
(`rgba(16,31,94,…)` not pure black) so elevation reads as "lifted paper," not
"drop shadow default."

---

## 6. Layout patterns

- **Top nav** (`layout.css` `.topnav`): sticky, blurred-glass background,
  logo mark + wordmark, primary nav (Home / Macro / Sector / Stock), search
  field, hamburger under 800px → full-screen drawer (`.nav-drawer`,
  `assets/js/nav.js`). The search field is live — see "Ticker search" under §8.
- **Page header** (`.page-header`): breadcrumbs, eyebrow + H1 + dek, an
  "as of" timestamp aligned right, and — critically — a **sub-nav** (`.subnav`)
  listing every sub-page in the current section as pill tabs, with a
  `badge-soon` pill for anything not built yet. This is *the* mechanism for
  "add a sub-page and it shows up in navigation" — see §8.
- **Section body** (`.section-body`): vertical stack of cards/panels, `container`-width.
- **Footer**: three-column sitemap (mirrors the same section → sub-page
  structure as the top nav) + a fixed legal/disclaimer line.
- **Empty state** (`.empty-state`): the "coming soon" pattern — dashed
  border, diagonal-hatch background, icon badge, one sentence, one CTA back to
  something that *does* exist. Used by Macro Analysis (whole section) and
  Sector Rotation (one sub-page) — same component, two scopes.

---

## 7. Component catalog (implemented in `components.css`)

`.card` / `.nav-card` · `.kpi-row` + `.kpi` · `.dir` (direction glyph+color) ·
`.pill-*` (status) · `.badge-soon` · `.seg` (segmented toggle) ·
`.search-field` / `.nav-search` + `.stock-search-results` (ticker search
dropdown, see §8) · `table.data` (+ `.mag-cell` for diverging-tinted numeric
cells) · `.chart-panel` + `.chart-tooltip` · `.ai-note` (AI insight callout) ·
`.callout-flag/-note/-pass` (red-flag / caveat / confirmation callouts) ·
`.stat-row` + `.stat` (fundamentals scorecard tiles) · `.empty-state` ·
`.report-frame-wrap` (embedded deep-dive report, see §9).

Every component is built from tokens only. When a page needs something new,
add the class to `components.css` (or a page-specific `<style>` block if it's
genuinely one-off, as the report-shell/in-tabs patterns in the two
Stock Analysis templates are) — never inline a raw color.

---

## 8. Folder structure

```
snapstocks/                         # Cloudflare Pages project root — deploy this folder as-is
├── DESIGN.md                       # this file
├── index.html                      # Home — the actual domain root, "/"
├── assets/
│   ├── css/
│   │   ├── tokens.css              # ALL color/type/spacing custom properties — edit palette here only
│   │   ├── base.css                # reset + bare element styles, no component classes
│   │   ├── layout.css              # nav, page-header, subnav, footer, hero, container/grid shell
│   │   └── components.css          # cards, KPIs, pills, tables, charts chrome, callouts, empty-state
│   ├── js/
│   │   ├── nav.js                  # mobile drawer open/close (event-delegated, no deps)
│   │   ├── theme.js                 # light/dark toggle, localStorage-persisted
│   │   ├── sector-momentum-data.js  # fetch()es data/sector_momentum.json for the two momentum pages
│   │   ├── stock-search.js          # powers every [data-stock-search] input from data/stocks.json
│   │   ├── deep-dive-listing.js     # renders stock-analysis/index.html's table from deep_dive_reports.json
│   │   └── report-frame.js          # auto-sizes an embedded deep-dive report iframe to its content height
│   └── img/
│       └── brand/                  # logo/favicon exports go here (currently inline SVG in-page)
├── data/
│   ├── sector_momentum.json         # the live feed (generated by stock-research's `srp report site-export`)
│   ├── sector_momentum.sample.json  # the illustrative data CONTRACT reference (not loaded by any page)
│   ├── deep_dive_reports.json       # GENERATED — every stock with a deep-dive; rewritten by the script below
│   ├── stocks.json                  # GENERATED — the full ticker search index; see "Ticker search" below
│   ├── fundamentals/                # GENERATED — one <TICKER>.json per stock; see "Fundamentals data" below
│   └── fundamentals_index.json      # GENERATED — thin per-ticker index (peers, sector median P/E)
├── partials/
│   ├── header.html                  # canonical nav markup — see "no build step" note below
│   └── footer.html
├── scripts/
│   ├── generate_deep_dive_shells.py # stamps out deep-dive shells + the manifest above — see §9
│   ├── generate_stock_index.py      # builds data/stocks.json — see "Ticker search" below
│   └── generate_fundamentals_data.py # builds data/fundamentals/*.json + fundamentals_index.json
├── macro-analysis/
│   └── index.html                   # section landing, "coming soon" (whole section unbuilt)
├── sector-analysis/
│   ├── index.html                   # section landing — links to the 3 views below
│   ├── momentum-chart.html          # quadrant scatter, live
│   ├── momentum-table.html          # sortable table, live
│   └── rotation.html                # "coming soon" (one sub-page unbuilt, section otherwise live)
└── stock-analysis/
    ├── index.html                   # section landing — deep-dive listing renders from the manifest
    ├── fundamentals/
    │   └── template.html            # screener.in-style snapshot — THE live page for every ticker (?symbol=)
    └── deep-dive/
        ├── coming-soon.html          # HAND-WRITTEN — fallback for any ticker with no report yet, see §8
        ├── zaggle.html               # SnapStocks-chrome SHELL — GENERATED, one per report
        ├── optiemus.html             # generated shell
        ├── nh.html                   # generated shell
        ├── refex.html                # generated shell
        └── reports/                  # ← drop new AI-generated report files here
            ├── zaggle.html           # the raw, self-contained report the shell above iframes in
            ├── OPTIEMUS.html         # raw report (filename casing preserved as authored)
            ├── nh.html               # raw report
            └── REFEX.html            # raw report
```

### Deep-dive reports are framed, not inlined — and the shell is generated, not hand-written

Deep-dive reports (`deep-dive/reports/*.html`) are generated by a separate,
independent AI/tool — each one is a **complete, self-contained HTML
document**: its own `<style>` block, its own design tokens (`--ink`,
`--accent`, `--good`, …, a different namespace from this site's
`tokens.css`), its own global element selectors (`a`, `table`, `h1..h4`,
`.card`, `.pill`), sometimes even its own inline `<script>` that draws
chart SVGs. That's normal for what it is — a standalone report someone can
also open directly — but it means the HTML cannot be pasted into a
SnapStocks page directly: those global selectors would leak out and
repaint this site's own nav, cards and tables with the report's styling.
Asking the report-generating AI to instead emit markup that matches this
site's classes/tokens exactly was considered and rejected — it works until
the one time it doesn't, and a silent styling drift is much harder to catch
than an iframe that just shows the report's own (perfectly fine) styling.

So each deep-dive **page** (`deep-dive/<name>.html`) is a thin shell: the
usual topnav/breadcrumbs/subnav chrome, then a `.report-frame-wrap` div
holding an `<iframe data-report-frame src="/stock-analysis/deep-dive/reports/<name>.html">`
that frames the real report. `assets/js/report-frame.js` measures the
same-origin iframe's content height on load (plus a couple of delayed
re-checks and a `ResizeObserver`, since fonts/charts can still shift
height after `load` fires) and sets the iframe's height to match, so it
reads as part of the page rather than a scrolling box-in-a-box —
`components.css`'s `.report-frame-wrap` handles the loading spinner state
until that first resize lands. This is why the URL stays stable
(`/stock-analysis/deep-dive/zaggle.html`) while the content underneath can
be regenerated independently at any time by dropping a new file into
`reports/`.

Nobody hand-writes the shell file, though — `scripts/generate_deep_dive_shells.py`
does. Workflow: drop the new report into `deep-dive/reports/`, run
`python scripts/generate_deep_dive_shells.py` from the `snapstocks/` folder.
For every report that doesn't already have a shell, it stamps one out (name
pulled from the report's own first `<h1>` — that field has been reliable
across every report seen so far; a report's `<title>` hasn't, e.g. one
report's `<title>` says "Zaggle Ledger" while its `<h1>` says the real
company name), and it rewrites `data/deep_dive_reports.json` — the manifest
`assets/js/deep-dive-listing.js` fetches to render the "Deep-dive reports"
table on `stock-analysis/index.html`. Existing shells are never touched
unless you pass `--force`, so hand edits to a specific shell survive
re-runs; `--dry-run` prints what would happen without writing anything.

### Ticker search

Every `<input data-stock-search>` on the site — the header's `.nav-search`
and the bigger `.search-field` on `stock-analysis/index.html` — is powered
by the same `assets/js/stock-search.js` reading the same `data/stocks.json`.
Typing filters client-side (ranked: exact symbol → symbol-prefix →
name-prefix → substring) and renders up to 8 results in a
`.stock-search-results` dropdown; arrow keys move, Enter or a click selects,
and a global `/` shortcut focuses the nearest visible search box.

**Selecting a result always goes to that stock's fundamentals page.** Every
entry's `fundamentals_url` is `stock-analysis/fundamentals/template.html
?symbol=<TICKER>` — the one live page, reading its data from that ticker's
generated JSON (see "Fundamentals data" below). A result that also has a
deep-dive report shows a `.pill-ai` "Deep-dive" badge; clicking that badge
specifically (rather than the row) jumps to the deep-dive page instead.

### Fundamentals data

`stock-analysis/fundamentals/template.html` is one static page shared by
every ticker — it reads `?symbol=TICKER` from the URL and
`assets/js/fundamentals-page.js` fetches `data/fundamentals/<TICKER>.json`
(plus the thin `data/fundamentals_index.json` for peer comparison and
sector-median P/E) to render it. No symbol in the URL shows an
`.empty-state` search prompt; a symbol with no generated file shows a
"not available" state instead of a broken page.

Both JSON files are generated by `scripts/generate_fundamentals_data.py`,
which transforms the sibling `Fin statements/<TICKER>/MarketData/raw/*.json`
yfinance pull (refreshed EOD by a separate pipeline) into the shape the
page expects — price/valuation stats, quarterly results, annual P&L,
balance sheet, cash flow, and a handful of computed ratios (ROCE, ROE,
debtor days, working capital days) derived from the raw statement line
items where those fields exist. Run it after every `Fin statements`
refresh:

```
python scripts/generate_fundamentals_data.py
```

It's a pure local JSON transform (no network calls), so it regenerates all
~750 tickers unconditionally rather than tracking staleness. A few sections
from an earlier hand-typed sample version of this page — AI-written
"Strengths/Watch-outs" commentary, an AI quickview paragraph, and a 4-way
Promoter/FII/DII/Public shareholding split — were dropped rather than
faked, since neither yfinance nor this pipeline has a mechanical source for
them yet.

`data/stocks.json` is generated, not hand-maintained — run
`python scripts/generate_stock_index.py` (from `snapstocks/`) after
changing the deep-dive reports or updating the mapping CSV. It merges two
sources: the NSE symbol/sector/industry universe from stock-research's
`sector_industry_mapping.csv` (one sibling-repo path up, at
`../stock-research/reports/sector_momentum/input/`; pass `--mapping-csv` to
point elsewhere), which gives every symbol a name (defaulting to the symbol
itself), sector and industry; and `stock-analysis/deep-dive/reports/*.html`,
which overlays the real company name and a `deep_dive_url` onto whichever
mapping row matches its ticker (same `<h1>` extraction as
`generate_deep_dive_shells.py`, plus a best-effort regex for the ticker
itself off each report's "NSE: XXX" text). `fundamentals_url` for every
entry is `stock-analysis/fundamentals/template.html?symbol=<TICKER>` — the
one live per-ticker page described above.

**Two places the fundamentals page links out, both driven by the same
`doc.profile.deepDiveUrl` field (null when the ticker has no report) —
never hardcode either to a specific stock's report:** the `.pill-ai`
"Deep-dive report available" badge in `renderIdentity()` only renders when
`deepDiveUrl` is truthy, so it just doesn't appear otherwise (no broken
link to fix there). The subnav's "Deep-Dive Reports" tab (`#fund-deepdive-tab`)
always renders, though, so it needs an explicit fallback: when `deepDiveUrl`
is null, `fundamentals-page.js` points it at
`stock-analysis/deep-dive/coming-soon.html?symbol=<TICKER>&name=<NAME>`
instead — a real page (topnav/breadcrumbs/subnav, same shell as every other
deep-dive page) with a personalized "No deep-dive report yet for `<name>`"
empty-state, not a redirect to whichever stock happened to be the sample
data before this page went live. The tab's static HTML default (before JS
runs) points at `coming-soon.html` with no query params too, for the same
reason — it should never be able to show *someone else's* report, even
mid-load.

Every top-level section folder (`macro-analysis/`, `sector-analysis/`,
`stock-analysis/`) sits directly under the project root, as siblings of
`index.html` — there is no `pages/` wrapper. That wrapper existed in an
earlier draft and was removed specifically so Cloudflare Pages picks up
`index.html` for the bare domain root without a redirect (see §9).

### Naming/URL convention
- One folder per top-level section (`macro-analysis/`, `sector-analysis/`,
  `stock-analysis/`), `kebab-case`, matching the nav label.
- One folder per **sub-page family** that will have many instances
  (`fundamentals/`, `deep-dive/`) with a real file per instance
  (`zaggle.html`, `template.html`) — see §10 for how this scales past two
  stocks.
- A sub-page that's a single fixed view (`momentum-chart.html`,
  `momentum-table.html`, `rotation.html`) is a flat file directly under its
  section, no extra folder.
- `index.html` is always the section landing page, never a specific view.
- **Every internal `href`/`src` is root-relative** (`/assets/css/tokens.css`,
  `/sector-analysis/index.html`) — never `../`-relative. See §9 for why.

### No build step, on purpose
This is currently plain static HTML with `<link>`/`<script>` includes — no
templating engine, no bundler. Every page repeats the same nav/footer markup
verbatim; `partials/header.html` and `partials/footer.html` document that
canonical markup so copies don't drift. This is a deliberate, temporary
tradeoff: it keeps the design reviewable file-by-file with zero tooling, at
the cost of manual sync when the nav changes.

**When the real product gets built** (Next.js, Astro, a Python static-site
generator off the `reports/` pipeline, whatever the eng team picks), the
migration is mechanical: `tokens.css`/`base.css`/`layout.css`/`components.css`
port unchanged, `partials/*.html` become real layout components, and every
top-level `.html` file/folder becomes a route. Nothing about the design
system is tied to the no-build-step choice.

---

## 9. Deployment (Cloudflare Pages)

The site deploys to Cloudflare Pages with **the `snapstocks/` folder as the
Pages project root** — point the Pages build at this folder (build command:
none, output directory: `/`). `index.html` sits directly at that root, so
Cloudflare serves it for the bare domain with no redirect and no extra
configuration required.

### Why every link is root-relative

Every `href`/`src` across the site points at an absolute, root-relative path
(`/assets/css/tokens.css`, `/sector-analysis/index.html`) rather than a
`../`-relative one. This isn't stylistic — `../`-relative paths broke in
exactly the way you'd expect on a static host once pages sit at different
folder depths (`index.html` vs.
`stock-analysis/fundamentals/template.html`, two levels deep): every link
needed a different number of `../` depending on where the file lived, and
Cloudflare Pages' clean-URL rewriting (`/foo.html` ↔ `/foo` ↔ `/foo/`)
changes what "relative to this page" even means. Root-relative paths
sidestep both problems — the exact same `href="/sector-analysis/index.html"`
works unmodified from every page, at every depth, regardless of URL
rewriting. `partials/header.html` and `partials/footer.html` are the
canonical source for this markup.

### Adding a page under this scheme

Nothing changes about §10 below — copy a sibling page, its `<link>`/`<script>`
tags and nav markup are already root-relative and portable to any depth.
Just don't reintroduce a `../`-relative href; if you paste a link from an
old draft or another project, rootify it first.

---

## 10. How to add a page or sub-page

**A new sub-page inside an existing section** (e.g. a "Sector Heatmap" view
next to Momentum Chart/Table):
1. Add the file: `sector-analysis/heatmap.html`, copy an existing
   sibling page as the starting point (same head, same nav/footer markup).
2. Add one `<a>` to the `.subnav` block in **every** page inside that
   section's `page-header` (all files currently list the same 3 tabs — add a
   4th everywhere).
3. Add the matching link to `.nav-drawer .drawer-sub` in every page (mobile
   nav) and to the footer's sitemap column.
4. If it's not ready yet, ship it anyway with `class="disabled"` and a
   `<span class="badge-soon">Soon</span>` — that's what Rotation Graphs does
   today. This keeps the nav honest about what's coming without a broken link.

**A brand-new top-level section** (e.g. future "Screener" or "Watchlist"):
1. New folder at the project root, `kebab-case`, as a sibling of
   `sector-analysis/` etc.
2. Add its link to `.nav-primary` and `.nav-drawer` in every existing page
   (yes, every page — see §8's build-step note) plus its own `.subnav` once
   it has sub-pages.
3. Add a footer sitemap column.
4. Follow Macro Analysis's pattern if it's not live yet: an `index.html` that
   is entirely an `.empty-state` card, so the nav item exists and is honest
   about status from day one.

**A new stock's fundamentals page**: nothing to hand-copy — every ticker
shares the one live page, `stock-analysis/fundamentals/template.html`,
which reads `?symbol=TICKER` from the URL and fetches
`data/fundamentals/<TICKER>.json`. After the daily `Fin statements` EOD
pull, run `python scripts/generate_fundamentals_data.py` from `snapstocks/`
to (re)generate that JSON for every ticker plus the thin
`data/fundamentals_index.json` peer/sector index — see "Fundamentals data"
below for the full pipeline.

**A new stock's deep-dive page** (see §9's "framed, not inlined" note for
why this is two files, not one — and why the second step is a script, not a
copy-paste):
1. Drop the generated report file into `stock-analysis/deep-dive/reports/`
   (whatever filename the generator gives it — casing doesn't need to match
   the site's kebab-case convention, since it's never linked to directly).
2. Run `python scripts/generate_deep_dive_shells.py` from `snapstocks/`.
   That's it — it stamps out `stock-analysis/deep-dive/<slug>.html` (slug
   derived from the report's filename) and adds the stock to
   `stock-analysis/index.html`'s listing via the regenerated manifest.
   Nothing to hand-edit; nothing else to link up.
3. Optional: link the new stock's deep-dive page from wherever else makes
   sense — e.g. the fundamentals page's "Deep-dive report available" pill,
   once that stock has a fundamentals page too.

---

## 11. Motion & "AI-jazzy" elements — used sparingly, on purpose

- **Hero mesh glow** (`.hero::before` in `layout.css`): a soft dual radial
  gradient in brand-blue + AI-violet, blurred, `pointer-events: none`, sitting
  behind the H1 on the homepage only. This is the single biggest "AI product"
  visual signal on the site — it appears once, not on every page.
- **AI badge gradient** (`.logo-badge`, `.ai-note .icon`): a 135° blue→violet
  gradient fill on small icon chips only — never a full-width background.
  gradient.
- **Backdrop blur** on the sticky nav (`backdrop-filter: blur(10px)`) — a
  restrained "glass" touch, not full glassmorphism panels.
  `@media (prefers-reduced-motion: reduce)` disables all animation/transition
  durations site-wide (`base.css`) — respected everywhere, no exceptions.
- Everything else (cards, tables, buttons) is intentionally flat and static.
  The AI/tech signal comes from these two or three restrained touches, not
  from motion everywhere.

---

## 12. Responsive rules

- Breakpoints used throughout: `900px` (search field hides), `800px`
  (primary nav collapses to hamburger), `700px` (2/3-column grids collapse to
  1 column, table font-size steps down), `640px` (container padding tightens).
- Tables never break the layout: every `table.data` sits inside
  `.table-scroll { overflow-x: auto }` inside a bordered `.table-shell` — the
  page scrolls vertically, the table scrolls horizontally within its own box.
- KPI rows and stat grids use `grid-template-columns: repeat(auto-fit,
  minmax(…, 1fr))` so they reflow from 5-across to 1-across with no explicit
  breakpoint needed.
- Deep-dive reports drop the sticky TOC sidebar entirely below 880px (it
  becomes dead weight on a phone, not a collapsible drawer) and go single-column.
- Every interactive control (search, segmented toggles, sortable table
  headers) has a large enough hit target on touch (`padding: 8-9px` minimum)
  and a visible `:focus-visible` ring (`base.css`) for keyboard use.

---

## 13. Accessibility notes

- Color is never the only signal: direction uses glyph+color (§4.3), status
  uses icon-dot+label, "coming soon" uses a text badge, not a faded color.
- All interactive elements have visible focus states (`:focus-visible` in
  `base.css`); the mobile drawer traps focus visually within itself.
- Chart (`momentum-chart.html`) ships a hover+focus tooltip on every point
  (mouse *and* keyboard, via `tabindex="0"` on each SVG point group) and has
  a same-data table view one click away (`momentum-table.html`) as the
  required non-visual fallback per the dataviz accessibility pass.
- Sortable table headers expose `aria-sort`; the mobile nav toggle exposes
  `aria-expanded`; breadcrumbs and nav landmarks use `aria-label`/`aria-current`.

---

## 14. Current build status

| Section | Sub-page | Status |
|---|---|---|
| Home | — | ✅ Built |
| Macro Analysis | (bond yields / DXY / crude) | 🚧 Section placeholder only — none of the sub-pages exist yet |
| Sector Analysis | Momentum Chart | ✅ Built, **live data** |
| Sector Analysis | Momentum Table | ✅ Built, **live data** |
| Sector Analysis | Rotation Graphs | 🚧 Placeholder |
| Stock Analysis | Fundamentals | ✅ Built, **live data**, ~750 tickers (`?symbol=`, see "Fundamentals data") |
| Stock Analysis | Deep-Dive Reports | ✅ Built, 4 stocks live (generated shells — see §9) |
| (site-wide) | Ticker search | ✅ Built, ~750-symbol index — see "Ticker search" under §8 |

"Sample data" means the numbers are illustrative for the design, hand-typed.
Fundamentals moved off that (now live per-ticker, see "Fundamentals data"
under §8); Deep-Dive Reports were always real, generated reports, just for
a small fixed set of stocks. The two Sector Analysis
momentum views are wired to a real feed: `assets/js/sector-momentum-data.js`
now `fetch()`es `/data/sector_momentum.json` at load (both group=sector and
group=industry), generated by the `stock-research` repo's
`srp report site-export` command (`execution/sector_momentum/site_export.py`)
from that pipeline's `sector_momentum_daily` table — see that repo's
`reports/sector_momentum/README.md` for how to regenerate it.
`data/sector_momentum.sample.json` stays as the illustrative contract
reference (a single "sector" group, 2 rows) — `sector_momentum.json` is the
real one actually loaded, with both `sector` and `industry` arrays plus
`n_mapped`/`n_with_data` coverage and `breadth` per row.
