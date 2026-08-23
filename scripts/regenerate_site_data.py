#!/usr/bin/env python3
"""Runs this site's three data generators in the order they depend on each
other. Use this instead of running them individually unless you specifically
know you only need one step.

  1. generate_deep_dive_shells.py  - stamps shells for any new report in
                                      deep-dive/reports/, writes
                                      data/deep_dive_reports.json
  2. generate_stock_index.py       - rebuilds data/stocks.json, including
                                      each ticker's deep_dive_url — needs
                                      step 1's output to know about new
                                      reports
  3. generate_fundamentals_data.py - rebuilds data/fundamentals/*.json,
                                      stamping profile.deepDiveUrl into each
                                      ticker from data/stocks.json — needs
                                      step 2's output, or a stock's own
                                      fundamentals page won't link to its
                                      deep-dive report even after steps 1
                                      and 2 both ran

Running these out of order (or stopping after step 2) is exactly how a
stock ends up with a working deep-dive page that's reachable from search
or the sector-analysis listing, but whose own fundamentals page still
links to the "coming soon" placeholder — the fundamentals JSON was built
before data/stocks.json knew about the report. This happened for real
(IKS, Aug 2026); run this script rather than the three by hand to avoid
repeating it.

Usage:
    python scripts/regenerate_site_data.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    "generate_deep_dive_shells.py",
    "generate_stock_index.py",
    "generate_fundamentals_data.py",
]


def main() -> None:
    for step in STEPS:
        print(f"\n=== {step} ===")
        result = subprocess.run([sys.executable, str(ROOT / step)])
        if result.returncode != 0:
            print(f"\n{step} failed (exit {result.returncode}) - stopping here, later steps would run on stale data.")
            sys.exit(result.returncode)
    print("\nAll three generators ran, in order. Site data is current.")


if __name__ == "__main__":
    main()
