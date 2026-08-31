import csv
import datetime as dt
import io
import json
import math
import re
import statistics
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

DATA_PATH = Path("data.json")
ASX_LIST_URL = "https://www.asx.com.au/asx/research/ASXListedCompanies.csv"
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{}?range=1y&interval=1d"
WORKERS = 12
MIN_HISTORY = 80
MIN_DOLLAR_TURNOVER_20D = 100_000
MAX_NEW_CANDIDATES = 100
MIN_SURFACE_SCORE = 55

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15"
}

ALWAYS_KEEP = {
    "WBT", "CSL", "RIO", "DMP", "DRO", "ETPMAG", "GOLD",
    "S32", "DTL", "WOR", "MIN", "AIA"
}


def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, x))


def pct(a, b):
    return ((a / b) - 1) * 100 if b else 0.0


def avg(xs, n):
    block = xs[-min(n, len(xs)):]
    return sum(block) / len(block) if block else 0.0


def ret(prices, days):
    i = max(0, len(prices) - 1 - days)
    return pct(prices[-1], prices[i])


def drawdown(prices, n=60):
    block = prices[-min(n, len(prices)):]
    if not block:
        return 100.0
    peak = block[0]
    worst = 0.0
    for p in block:
        peak = max(peak, p)
        worst = min(worst, pct(p, peak))
    return abs(worst)


def fetch_bytes(url, timeout=35):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_json(url, timeout=35):
    return json.loads(fetch_bytes(url, timeout).decode("utf-8", errors="ignore"))


def load_asx_universe():
    raw = fetch_bytes(ASX_LIST_URL).decode("utf-8-sig", errors="ignore")
    rows = list(csv.reader(io.StringIO(raw)))
    universe = []
    seen = set()
    for row in rows:
        if len(row) < 2:
            continue
        code = row[1].strip().upper()
        name = row[0].strip()
        if code in {"ASX CODE", "ASX code"}:
            continue
        if not re.fullmatch(r"[A-Z0-9]{3,5}", code):
            continue
        if code in seen:
            continue
        seen.add(code)
        universe.append({"ticker": code, "name": name or code})
    if len(universe) < 1000:
        raise RuntimeError(f"ASX universe unexpectedly small: {len(universe)}")
    return universe


def fetch_market(ticker):
    symbol = ticker + ".AX"
    url = YAHOO_CHART.format(urllib.parse.quote(symbol))
    last_error = None
    for attempt in range(3):
        try:
            raw = fetch_json(url)
            result = raw["chart"]["result"][0]
            quote = result["indicators"]["quote"][0]
            adj = result["indicators"].get("adjclose", [{}])[0].get("adjclose") or quote.get("close")
            vols = quote.get("volume") or []
            rows = []
            for close, vol in zip(adj, vols):
                if close is not None and close > 0:
                    rows.append((float(close), float(vol or 0)))
            if len(rows) < MIN_HISTORY:
                return None
            return rows
        except Exception as e:
            last_error = e
            time.sleep(0.35 * (attempt + 1))
    print("market failed", ticker, last_error)
    return None


def analyse(ticker, name, rows, bench):
    prices = [x[0] for x in rows]
    volumes = [x[1] for x in rows]
    price = prices[-1]
    r5 = ret(prices, 5)
    r20 = ret(prices, 20)
    r60 = ret(prices, 60)
    r120 = ret(prices, 120)
    r250 = ret(prices, 250)
    rs20 = r20 - bench[20]
    rs60 = r60 - bench[60]
    rs120 = r120 - bench[120]
    ma20 = avg(prices, 20)
    ma60 = avg(prices, 60)
    ma200 = avg(prices, 200)
    avgv20 = avg(volumes, 20)
    avgv60 = avg(volumes, 60)
    dollar_turnover = price * avgv20
    vol_ratio = (volumes[-1] / avgv20) if avgv20 else 0.0
    vol_trend = (avgv20 / avgv60) if avgv60 else 1.0
    daily = [pct(prices[i], prices[i - 1]) for i in range(max(1, len(prices) - 60), len(prices))]
    volatility = statistics.pstdev(daily) if len(daily) > 1 else 0.0
    dd = drawdown(prices)
    trend_stack = int(price > ma20) + int(ma20 > ma60) + int(ma60 > ma200)
    acceleration = rs20 - rs60 / 3 + 0.35 * (r5 - r20 / 4)

    score = 43.0
    score += clamp(rs20, -25, 25) * 0.55
    score += clamp(rs60, -35, 35) * 0.20
    score += clamp(rs120, -45, 45) * 0.08
    score += trend_stack * 5.0
    score += clamp(acceleration, -15, 15) * 0.45
    score += clamp((vol_ratio - 1) * 10, -5, 9)
    score += clamp((vol_trend - 1) * 10, -4, 7)

    if r20 > 30:
        score -= min(14, (r20 - 30) * 0.45)
    if r5 > 15:
        score -= min(10, (r5 - 15) * 0.65)
    if price > ma20 * 1.20:
        score -= 7
    score -= max(0, volatility - 3.0) * 1.3
    score -= max(0, dd - 25) * 0.22

    opportunity = round(clamp(score))
    risk = round(clamp(18 + volatility * 7 + dd * 0.9))
    confidence = round(clamp(48 + trend_stack * 7 + min(12, math.log10(max(dollar_turnover, 1)) * 2)))
    momentum = round(clamp(50 + rs20 * 1.1 + rs60 * 0.35 + trend_stack * 5))

    return {
        "ticker": ticker,
        "name": name,
        "price": round(price, 4),
        "opp": opportunity,
        "wholeAsxTechnicalScore": opportunity,
        "edge": "MARKET-WIDE",
        "quality": round(clamp(52 + trend_stack * 5 - max(0, volatility - 2) * 3)),
        "valuation": 50,
        "growth": round(clamp(50 + r120 * 0.25)),
        "momentum": momentum,
        "catalystScore": round(clamp(50 + acceleration + max(0, (vol_ratio - 1) * 10))),
        "risk": risk,
        "confidence": confidence,
        "announcementScore": 50,
        "announcementSignal": 0,
        "mismatchScore": 50,
        "priceSensitiveNews": False,
        "announcements": [],
        "delta": 0,
        "return5d": round(r5, 1),
        "return1m": round(r20, 1),
        "return3m": round(r60, 1),
        "return6m": round(r120, 1),
        "return12m": round(r250, 1),
        "relative1m": round(rs20, 1),
        "relative3m": round(rs60, 1),
        "relative6m": round(rs120, 1),
        "volumeRatio": round(vol_ratio, 2),
        "drawdown60": round(dd, 1),
        "dollarTurnover20d": round(dollar_turnover),
        "thesis": f"Whole-ASX discovery candidate. Relative strength vs ASX 200 is {rs20:+.1f}% over 1 month and {rs60:+.1f}% over 3 months, with a market-wide technical score of {opportunity}/100.",
        "catalyst": "Surfaced by the whole-ASX price, momentum and volume screen. Company announcements, global themes and short interest remain separate confirmation layers.",
        "riskText": f"60-day volatility {volatility:.1f}% per day; recent max drawdown {dd:.1f}%. Average 20-day dollar turnover is about A${dollar_turnover:,.0f}.",
        "history": [],
        "shortInterestPct": None,
        "shortSignal": "N/A",
        "shortAdjustment": 0,
        "globalTrendScore": 0,
        "globalTrendAdjustment": 0,
        "globalTrendSignal": "NEUTRAL",
        "globalThemes": [],
        "trendCandidate": False,
        "wholeAsxCandidate": True,
        "opportunitySource": "WHOLE_ASX"
    }


def main():
    if not DATA_PATH.exists():
        raise SystemExit("data.json not found")

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    previous = {str(s.get("ticker", "")).upper(): s for s in data.get("stocks", [])}

    universe = load_asx_universe()
    print("ASX universe", len(universe))

    bench_rows = fetch_market("^AXJO"[:-3]) if False else None
    bench_raw = fetch_json(YAHOO_CHART.format(urllib.parse.quote("^AXJO")))
    bench_result = bench_raw["chart"]["result"][0]
    bench_adj = bench_result["indicators"].get("adjclose", [{}])[0].get("adjclose") or bench_result["indicators"]["quote"][0]["close"]
    bench_prices = [float(x) for x in bench_adj if x is not None]
    bench = {20: ret(bench_prices, 20), 60: ret(bench_prices, 60), 120: ret(bench_prices, 120)}

    valid = []
    failed = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(fetch_market, row["ticker"]): row for row in universe}
        for n, future in enumerate(as_completed(futures), 1):
            row = futures[future]
            try:
                market = future.result()
                if not market:
                    failed += 1
                    continue
                candidate = analyse(row["ticker"], row["name"], market, bench)
                if candidate["dollarTurnover20d"] >= MIN_DOLLAR_TURNOVER_20D or row["ticker"] in ALWAYS_KEEP:
                    valid.append(candidate)
            except Exception as e:
                failed += 1
                print("analyse failed", row["ticker"], e)
            if n % 100 == 0:
                print("screened", n, "valid", len(valid), "failed", failed)

    valid.sort(key=lambda x: (x["opp"], x["confidence"], x["dollarTurnover20d"]), reverse=True)
    surfaced = [x for x in valid if x["opp"] >= MIN_SURFACE_SCORE][:MAX_NEW_CANDIDATES]

    # Keep the existing detailed universe intact, then add/mark whole-ASX discoveries.
    merged = list(data.get("stocks", []))
    # Fill proper company names from the official ASX universe when the older
    # detailed scanner only stored the ticker as its name.
    universe_names = {str(x.get("ticker", "")).upper(): str(x.get("name", "")).strip() for x in universe}
    for stock in merged:
        ticker = str(stock.get("ticker", "")).upper()
        current_name = str(stock.get("name", "") or "").strip()
        better_name = universe_names.get(ticker, "")
        if better_name and (not current_name or current_name.upper() == ticker):
            stock["name"] = better_name
    positions = {str(s.get("ticker", "")).upper(): i for i, s in enumerate(merged)}
    rank_map = {}
    for rank, candidate in enumerate(surfaced, 1):
        ticker = candidate["ticker"]
        rank_map[ticker] = rank
        if ticker in positions:
            existing = merged[positions[ticker]]
            existing["wholeAsxCandidate"] = True
            existing["wholeAsxRank"] = rank
            existing["wholeAsxTechnicalScore"] = candidate["wholeAsxTechnicalScore"]
            existing["wholeAsxDollarTurnover20d"] = candidate["dollarTurnover20d"]
            existing["wholeAsxRelative1m"] = candidate["relative1m"]
            existing["wholeAsxRelative3m"] = candidate["relative3m"]
        else:
            candidate["wholeAsxRank"] = rank
            merged.append(candidate)
            positions[ticker] = len(merged) - 1

    merged.sort(key=lambda s: (float(s.get("opp", 0) or 0), float(s.get("confidence", 0) or 0)), reverse=True)
    data["stocks"] = merged
    data["wholeAsxScan"] = {
        "updated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": "ASX official listed-company universe + Yahoo Finance ASX daily price/volume history",
        "universeCount": len(universe),
        "validLiquidCount": len(valid),
        "failedOrInsufficientCount": failed,
        "surfacedCount": len(surfaced),
        "minimum20dDollarTurnover": MIN_DOLLAR_TURNOVER_20D,
        "minimumSurfaceScore": MIN_SURFACE_SCORE,
        "topCandidates": [
            {"ticker": x["ticker"], "name": x["name"], "score": x["opp"], "rank": i + 1}
            for i, x in enumerate(surfaced[:20])
        ]
    }
    data["source"] = "Whole-ASX discovery screen + ASX Edge detailed company, short-interest and global-trend layers"
    DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("surfaced", len(surfaced), "whole-ASX candidates")


if __name__ == "__main__":
    main()
