#!/usr/bin/env python3
"""Builds data/stocks.json, the index the site's ticker search reads from
(assets/js/stock-search.js powers both the header search box and the
search field on stock-analysis/index.html from this one file).

Merges two sources:
  1. stock-research's sector_industry_mapping.csv — the NSE symbol/sector/
     industry universe (751 symbols as of Aug 2026). Every row becomes a
     searchable entry; without a deep-dive report its display name is just
     its own symbol, since there's no per-ticker fundamentals data yet.
  2. stock-analysis/deep-dive/reports/*.html — overlays the real company
     name (from each report's <h1>, same extraction as
     generate_deep_dive_shells.py) and a deep_dive_url onto whichever
     mapping-CSV row matches its ticker (parsed from the report's own
     "NSE: XXX" text). A report whose ticker isn't in the mapping CSV still
     gets its own entry rather than being dropped.

Every entry's fundamentals_url points at the shared
stock-analysis/fundamentals/template.html with its own symbol as a
`?symbol=` query param — see generate_fundamentals_data.py, which builds
the per-ticker JSON that page fetches at load time.

Usage:
    python scripts/generate_stock_index.py [--mapping-csv PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "stock-analysis" / "deep-dive" / "reports"
OUT_PATH = ROOT / "data" / "stocks.json"
DEFAULT_MAPPING_CSV = (
    ROOT.parent / "stock-research" / "reports" / "sector_momentum" / "input" / "sector_industry_mapping.csv"
)
FUNDAMENTALS_URL_BASE = "/stock-analysis/fundamentals/template.html"


def fundamentals_url(symbol: str) -> str:
    return f"{FUNDAMENTALS_URL_BASE}?symbol={symbol}"

H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
TICKER_RE = re.compile(r"NSE\s*(?:/\s*BSE)?\s*:?\s*([A-Z][A-Z0-9]{1,14})\b")


def clean_text(raw: str) -> str:
    return WS_RE.sub(" ", TAG_RE.sub("", raw)).strip()


def extract_company_name(html_text: str, fallback: str) -> str:
    match = H1_RE.search(html_text)
    if not match:
        return fallback
    return clean_text(match.group(1)) or fallback


def extract_ticker(html_text: str) -> str | None:
    match = TICKER_RE.search(html_text)
    if not match:
        return None
    token = match.group(1)
    return None if token == "BSE" else token


def slugify(stem: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", stem.strip().lower())
    return slug.strip("-")


def load_mapping(csv_path: Path) -> dict[str, dict[str, str | None]]:
    if not csv_path.exists():
        print(f"warning: mapping CSV not found at {csv_path} - stock index will only include deep-dive reports")
        return {}
    rows: dict[str, dict[str, str | None]] = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            symbol = row["symbol"].strip().upper()
            if not symbol:
                continue
            rows[symbol] = {
                "sector": row.get("sector", "").strip() or None,
                "industry": row.get("industry", "").strip() or None,
            }
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mapping-csv", type=Path, default=DEFAULT_MAPPING_CSV, help="path to sector_industry_mapping.csv")
    args = parser.parse_args()

    mapping = load_mapping(args.mapping_csv)

    stocks: dict[str, dict] = {}
    for symbol, meta in mapping.items():
        stocks[symbol] = {
            "symbol": symbol,
            "name": symbol,
            "sector": meta["sector"],
            "industry": meta["industry"],
            "fundamentals_url": fundamentals_url(symbol),
            "deep_dive_url": None,
        }

    overlaid = 0
    added = 0
    if REPORTS_DIR.exists():
        for report_path in sorted(REPORTS_DIR.glob("*.html")):
            text = report_path.read_text(encoding="utf-8")
            ticker = extract_ticker(text)
            name = extract_company_name(text, fallback=report_path.stem)
            deep_dive_url = f"/stock-analysis/deep-dive/{slugify(report_path.stem)}.html"

            key = ticker or f"__{report_path.stem}"
            if key in stocks:
                stocks[key]["name"] = name
                stocks[key]["deep_dive_url"] = deep_dive_url
                overlaid += 1
            else:
                entry_symbol = ticker or name
                stocks[key] = {
                    "symbol": entry_symbol,
                    "name": name,
                    "sector": None,
                    "industry": None,
                    "fundamentals_url": fundamentals_url(entry_symbol),
                    "deep_dive_url": deep_dive_url,
                }
                added += 1

    index = sorted(stocks.values(), key=lambda s: s["name"].lower())
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    print(
        f"wrote {OUT_PATH.relative_to(ROOT).as_posix()} ({len(index)} stocks total: "
        f"{len(mapping)} from mapping CSV, {overlaid} overlaid with deep-dive data, {added} deep-dive-only)"
    )


if __name__ == "__main__":
    main()
