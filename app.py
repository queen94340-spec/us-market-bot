#!/usr/bin/env python3
"""US market real-time alert program for S&P 500, VOO, and NVIDIA."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from typing import Iterable

import requests

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

DEFAULT_TICKERS = {
    "S&P 500": "^GSPC",
    "VOO": "VOO",
    "NVIDIA": "NVDA",
}


@dataclasses.dataclass
class Quote:
    name: str
    symbol: str
    price: float
    prev_close: float
    currency: str

    @property
    def change_percent(self) -> float:
        if self.prev_close == 0:
            return 0.0
        return (self.price - self.prev_close) / self.prev_close * 100


class QuoteError(RuntimeError):
    pass


def fetch_quote(session: requests.Session, name: str, symbol: str) -> Quote:
    response = session.get(
        YAHOO_CHART_URL.format(symbol=symbol),
        params={"interval": "2m", "range": "1d"},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    result = payload.get("chart", {}).get("result")
    if not result:
        raise QuoteError(f"No data returned for {symbol}")
    meta = result[0].get("meta", {})
    price = meta.get("regularMarketPrice")
    prev_close = meta.get("previousClose")
    currency = meta.get("currency") or "USD"
    if price is None or prev_close is None:
        raise QuoteError(f"Missing price data for {symbol}")
    return Quote(name=name, symbol=symbol, price=float(price), prev_close=float(prev_close), currency=currency)


def format_quote(quote: Quote) -> str:
    change = quote.price - quote.prev_close
    return (
        f"{quote.name} ({quote.symbol}) {quote.price:.2f} {quote.currency} "
        f"({change:+.2f}, {quote.change_percent:+.2f}%)"
    )


def should_alert(quote: Quote, threshold: float) -> bool:
    return abs(quote.change_percent) >= threshold


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="US market real-time alert program for S&P 500, VOO, and NVIDIA.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Polling interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1.0,
        help="Alert threshold for percent change (default: 1.0)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Fetch and print once, then exit.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    session = requests.Session()

    while True:
        quotes = []
        errors = []
        for name, symbol in DEFAULT_TICKERS.items():
            try:
                quotes.append(fetch_quote(session, name, symbol))
            except (requests.RequestException, QuoteError, json.JSONDecodeError) as exc:
                errors.append(f"{name} ({symbol}): {exc}")

        if errors:
            print("[WARN] Failed to fetch some quotes:")
            for error in errors:
                print(f"  - {error}")

        for quote in quotes:
            line = format_quote(quote)
            if should_alert(quote, args.threshold):
                print(f"[ALERT] {line}")
            else:
                print(f"[INFO]  {line}")

        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
