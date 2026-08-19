#!/usr/bin/env python3
"""Builds data/fundamentals/<TICKER>.json (one per ticker) and the thin
data/fundamentals_index.json (all tickers), the two files
stock-analysis/fundamentals/template.html fetches at load time to render a
ticker's fundamentals for `?symbol=<TICKER>`.

Source data is `Fin statements/<TICKER>/MarketData/raw/*.json` (a sibling
yfinance-pull pipeline, refreshed EOD) plus this repo's own
data/stocks.json (for the sector/industry mapping used for peer grouping,
and any deep_dive_url overlay). Re-run this after every `Fin statements`
EOD refresh - it's a pure local JSON transform, cheap enough to regenerate
every ticker unconditionally rather than tracking staleness.

Usage:
    python scripts/generate_fundamentals_data.py [--fin-statements-dir PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIN_STATEMENTS_DIR = ROOT.parent.parent / "Fin statements"
STOCKS_JSON = ROOT / "data" / "stocks.json"
OUT_DIR = ROOT / "data" / "fundamentals"
INDEX_PATH = ROOT / "data" / "fundamentals_index.json"

TRADING_DAYS_PER_YEAR = 252


# ---------------------------------------------------------------- helpers

def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def num(value) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return None if f != f else f  # filter NaN


def pick_line(stmt: dict, *aliases: str) -> dict:
    for name in aliases:
        if name in stmt:
            return stmt[name] or {}
    return {}


def fy_from_date(dt: datetime) -> int:
    # Indian fiscal year: Apr(y) - Mar(y+1) belongs to FY(y+1)
    return dt.year + 1 if dt.month >= 4 else dt.year


def fy_label(period_key: str) -> str:
    dt = datetime.fromisoformat(period_key.split("T")[0])
    return f"FY{fy_from_date(dt) % 100:02d}"


def fy_quarter_label(period_key: str) -> str:
    dt = datetime.fromisoformat(period_key.split("T")[0])
    fy = fy_from_date(dt) % 100
    quarter = {4: 1, 5: 1, 6: 1, 7: 2, 8: 2, 9: 2, 10: 3, 11: 3, 12: 3, 1: 4, 2: 4, 3: 4}[dt.month]
    return f"Q{quarter}FY{fy:02d}"


def sorted_periods(*statements: dict) -> list[str]:
    periods: set[str] = set()
    for stmt in statements:
        for line in stmt.values():
            periods.update(line.keys())
    return sorted(periods)


def build_rows(stmt: dict, periods: list[str], specs: list[tuple[str, tuple[str, ...]]]) -> dict[str, list]:
    rows: dict[str, list] = {}
    for label, aliases in specs:
        line = pick_line(stmt, *aliases)
        rows[label] = [num(line.get(p)) for p in periods]
    return rows


def pct(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator * 100


def yoy_growth(values: list[float | None]) -> list[float | None]:
    out: list[float | None] = [None]
    for prev, cur in zip(values, values[1:]):
        out.append(pct(None if cur is None or prev is None else cur - prev, prev))
    return out


# --------------------------------------------------------- per-statement

INCOME_ROW_SPECS = [
    ("Sales", ("Total Revenue",)),
    ("Expenses", ("Total Expenses",)),
    ("OperatingProfit", ("Operating Income",)),
    ("NetProfit", ("Net Income",)),
    ("EPS", ("Diluted EPS", "Basic EPS")),
]

BALANCE_ROW_SPECS = [
    ("EquityCapital", ("Common Stock", "Capital Stock")),
    ("Borrowings", ("Total Debt",)),
    ("TotalAssets", ("Total Assets",)),
    ("NetBlock", ("Net PPE",)),
    ("Investments", ("Investmentin Financial Assets", "Available For Sale Securities", "Long Term Equity Investment")),
    ("StockholdersEquity", ("Stockholders Equity", "Common Stock Equity")),
    ("CurrentAssets", ("Current Assets",)),
    ("CurrentLiabilities", ("Current Liabilities",)),
    ("AccountsReceivable", ("Accounts Receivable",)),
]

CASHFLOW_ROW_SPECS = [
    ("OperatingCashFlow", ("Operating Cash Flow",)),
    ("InvestingCashFlow", ("Investing Cash Flow",)),
    ("FinancingCashFlow", ("Financing Cash Flow",)),
    ("NetCashFlow", ("Changes In Cash",)),
]


def build_statement_block(stmt: dict, label_fn, row_specs) -> dict | None:
    if not stmt:
        return None
    periods = sorted_periods(stmt)
    if not periods:
        return None
    rows = build_rows(stmt, periods, row_specs)
    return {"periods": [label_fn(p) for p in periods], "periodDates": periods, "rows": rows}


def quarterly_ttm(income_quarterly: dict) -> dict:
    """Sum the latest 4 quarters of each flow line item for a TTM column."""
    periods = sorted_periods(income_quarterly)
    last4 = periods[-4:]
    ttm: dict[str, float | None] = {}
    for label, aliases in INCOME_ROW_SPECS:
        if label == "EPS":
            continue
        line = pick_line(income_quarterly, *aliases)
        vals = [num(line.get(p)) for p in last4]
        ttm[label] = sum(vals) if len(last4) == 4 and all(v is not None for v in vals) else None
    return ttm


def compute_ratios(income_annual: dict, balance_annual: dict) -> dict | None:
    if not income_annual or not balance_annual:
        return None
    periods = sorted(set(sorted_periods(income_annual)) & set(sorted_periods(balance_annual)))
    if not periods:
        return None

    ebit_line = pick_line(income_annual, "EBIT")
    net_income_line = pick_line(income_annual, "Net Income")
    revenue_line = pick_line(income_annual, "Total Revenue")
    assets_line = pick_line(balance_annual, "Total Assets")
    cur_liab_line = pick_line(balance_annual, "Current Liabilities")
    cur_assets_line = pick_line(balance_annual, "Current Assets")
    equity_line = pick_line(balance_annual, "Stockholders Equity", "Common Stock Equity")
    receivable_line = pick_line(balance_annual, "Accounts Receivable")

    roce, roe, debtor_days, wc_days = [], [], [], []
    for p in periods:
        assets = num(assets_line.get(p))
        cur_liab = num(cur_liab_line.get(p))
        capital_employed = None if assets is None or cur_liab is None else assets - cur_liab
        roce.append(pct(num(ebit_line.get(p)), capital_employed))
        roe.append(pct(num(net_income_line.get(p)), num(equity_line.get(p))))

        revenue = num(revenue_line.get(p))
        receivable = num(receivable_line.get(p))
        debtor_days.append(None if not revenue or receivable is None else receivable / revenue * 365)

        cur_assets = num(cur_assets_line.get(p))
        wc = None if cur_assets is None or cur_liab is None else cur_assets - cur_liab
        wc_days.append(None if not revenue or wc is None else wc / revenue * 365)

    return {
        "periods": [fy_label(p) for p in periods],
        "rows": {"ROCE": roce, "ROE": roe, "DebtorDays": debtor_days, "WorkingCapitalDays": wc_days},
    }


def compute_return_1y(price_history_path: Path) -> float | None:
    if not price_history_path.exists():
        return None
    try:
        with price_history_path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    except OSError:
        return None
    closes = [num(r.get("Close")) for r in rows if num(r.get("Close")) is not None]
    if len(closes) < TRADING_DAYS_PER_YEAR + 1:
        return None
    latest, past = closes[-1], closes[-1 - TRADING_DAYS_PER_YEAR]
    return pct(latest - past, past)


def recent_dividends(dividends: dict | None, limit: int = 8) -> list[dict]:
    if not dividends:
        return []
    items = sorted(dividends.items(), key=lambda kv: kv[0], reverse=True)[:limit]
    return [{"date": date.split("T")[0], "amount": num(amount)} for date, amount in items]


# -------------------------------------------------------------- per-ticker

def process_ticker(ticker_dir: Path, sector_map: dict[str, dict], deep_dive_urls: dict[str, str]) -> tuple[dict, dict] | None:
    symbol = ticker_dir.name
    raw_dir = ticker_dir / "MarketData" / "raw"
    info = load_json(raw_dir / "info.json")
    if not info:
        return None

    fast_info = load_json(raw_dir / "fast_info.json") or {}
    ticker_info = load_json(ticker_dir / "ticker_info.json") or {}
    income_annual = load_json(raw_dir / "income_statement_annual.json") or {}
    income_quarterly = load_json(raw_dir / "income_statement_quarterly.json") or {}
    balance_annual = load_json(raw_dir / "balance_sheet_annual.json") or {}
    cashflow_annual = load_json(raw_dir / "cashflow_annual.json") or {}
    dividends = load_json(raw_dir / "dividends.json")
    price_targets = load_json(raw_dir / "analyst_price_targets.json") or {}
    major_holders = load_json(raw_dir / "major_holders.json") or {}

    name = ticker_info.get("company_name") or info.get("longName") or info.get("shortName") or symbol
    mapping = sector_map.get(symbol, {})

    quarterly_block = build_statement_block(income_quarterly, fy_quarter_label, INCOME_ROW_SPECS)
    annual_block = build_statement_block(income_annual, fy_label, INCOME_ROW_SPECS)
    if annual_block:
        annual_block["rows"]["SalesGrowth"] = yoy_growth(annual_block["rows"]["Sales"])
        annual_block["ttm"] = quarterly_ttm(income_quarterly) if income_quarterly else None

    balance_block = build_statement_block(balance_annual, fy_label, BALANCE_ROW_SPECS)
    cashflow_block = build_statement_block(cashflow_annual, fy_label, CASHFLOW_ROW_SPECS)
    ratios_block = compute_ratios(income_annual, balance_annual)

    market_cap = num(info.get("marketCap"))
    trailing_pe = num(info.get("trailingPE"))
    return_1y = compute_return_1y(raw_dir / "price_history.csv")
    current_price = num(info.get("currentPrice") or info.get("regularMarketPrice") or fast_info.get("lastPrice"))

    doc = {
        "symbol": symbol,
        "name": name,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "profile": {
            "sector": info.get("sector") or mapping.get("sector"),
            "industry": info.get("industry") or mapping.get("industry"),
            "exchange": "NSE",
            "bseCode": ticker_info.get("bse_scrip_code"),
            "nseSymbol": symbol,
            "website": info.get("website"),
            "deepDiveUrl": deep_dive_urls.get(symbol),
            # Peer grouping must use the same taxonomy as fundamentals_index.json's
            # sector/industry (sourced from stocks.json's mapping CSV) - yfinance's
            # own sector/industry strings above are a different taxonomy and won't
            # match peers there.
            "peerSector": mapping.get("sector"),
            "peerIndustry": mapping.get("industry"),
        },
        "price": {
            "current": current_price,
            "change": num(info.get("regularMarketChange")),
            "changePercent": num(info.get("regularMarketChangePercent")),
            "previousClose": num(info.get("regularMarketPreviousClose") or fast_info.get("previousClose")),
            "dayLow": num(info.get("regularMarketDayLow") or fast_info.get("dayLow")),
            "dayHigh": num(info.get("regularMarketDayHigh") or fast_info.get("dayHigh")),
            "fiftyTwoWeekLow": num(info.get("fiftyTwoWeekLow") or fast_info.get("yearLow")),
            "fiftyTwoWeekHigh": num(info.get("fiftyTwoWeekHigh") or fast_info.get("yearHigh")),
            "asOf": info.get("regularMarketTime"),
        },
        "stats": {
            "marketCap": market_cap,
            "trailingPE": trailing_pe,
            "forwardPE": num(info.get("forwardPE")),
            "priceToBook": num(info.get("priceToBook")),
            "bookValue": num(info.get("bookValue")),
            "dividendYield": num(info.get("dividendYield")),
            "trailingEps": num(info.get("trailingEps")),
            "debtToEquity": None if num(info.get("debtToEquity")) is None else num(info.get("debtToEquity")) / 100,
            "roe": ratios_block["rows"]["ROE"][-1] if ratios_block and ratios_block["rows"]["ROE"] else None,
            "roce": ratios_block["rows"]["ROCE"][-1] if ratios_block and ratios_block["rows"]["ROCE"] else None,
            "return1y": return_1y,
            "sharesOutstanding": num(info.get("sharesOutstanding")),
        },
        "quarterly": quarterly_block,
        "annual": annual_block,
        "balanceSheet": balance_block,
        "cashFlow": cashflow_block,
        "ratios": ratios_block,
        "dividends": recent_dividends(dividends),
        "analyst": {
            "targetMean": num(price_targets.get("mean")),
            "targetHigh": num(price_targets.get("high")),
            "targetLow": num(price_targets.get("low")),
            "recommendationKey": info.get("recommendationKey"),
            "numberOfAnalystOpinions": info.get("numberOfAnalystOpinions"),
        },
        "holders": {
            "insidersPercent": num((major_holders.get("insidersPercentHeld") or {}).get("Value")),
            "institutionsPercent": num((major_holders.get("institutionsPercentHeld") or {}).get("Value")),
        },
    }

    index_row = {
        "symbol": symbol,
        "name": name,
        "sector": mapping.get("sector") or info.get("sector"),
        "industry": mapping.get("industry") or info.get("industry"),
        "price": current_price,
        "marketCap": market_cap,
        "peTTM": trailing_pe,
        "roe": doc["stats"]["roe"],
        "return1y": return_1y,
    }
    return doc, index_row


# ------------------------------------------------------------------ main

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fin-statements-dir", type=Path, default=DEFAULT_FIN_STATEMENTS_DIR)
    args = parser.parse_args()

    fin_dir: Path = args.fin_statements_dir
    if not fin_dir.exists():
        raise SystemExit(f"error: Fin statements dir not found at {fin_dir} - pass --fin-statements-dir")

    stocks = load_json(STOCKS_JSON) or []
    sector_map = {s["symbol"]: s for s in stocks}
    deep_dive_urls = {s["symbol"]: s["deep_dive_url"] for s in stocks if s.get("deep_dive_url")}

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped: list[str] = []
    index_rows: list[dict] = []

    for ticker_dir in sorted(fin_dir.iterdir()):
        if not ticker_dir.is_dir() or ticker_dir.name.startswith((".", "_")) or ticker_dir.name == "src":
            continue
        result = process_ticker(ticker_dir, sector_map, deep_dive_urls)
        if result is None:
            skipped.append(ticker_dir.name)
            continue
        doc, index_row = result
        (OUT_DIR / f"{ticker_dir.name}.json").write_text(
            json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )
        index_rows.append(index_row)
        written += 1

    # sector-median P/E, attached per row so the page needn't recompute it
    by_sector: dict[str, list[float]] = {}
    for row in index_rows:
        if row["sector"] and row["peTTM"] is not None:
            by_sector.setdefault(row["sector"], []).append(row["peTTM"])
    for row in index_rows:
        pes = by_sector.get(row["sector"])
        row["sectorMedianPE"] = statistics.median(pes) if pes else None

    index_rows.sort(key=lambda r: r["name"].lower())
    INDEX_PATH.write_text(json.dumps(index_rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    print(f"wrote {written} ticker files to {OUT_DIR.relative_to(ROOT).as_posix()}")
    print(f"wrote {INDEX_PATH.relative_to(ROOT).as_posix()} ({len(index_rows)} rows)")
    if skipped:
        print(f"skipped {len(skipped)} tickers (no MarketData/info.json): {', '.join(skipped[:20])}" + (" ..." if len(skipped) > 20 else ""))


if __name__ == "__main__":
    main()
