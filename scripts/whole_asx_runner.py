import csv
import io
import re

import whole_asx_opportunities as base

ISIN_URL = "https://www.asx.com.au/content/dam/asx/issuers/ISIN.xls"
EXCLUDE = {
    "AUD", "USD", "NZD", "GBP", "EUR", "JPY", "HKD", "CAD", "CHF",
    "ORD", "CDI", "ETF", "ETP", "ETC", "FPO", "PREF", "NCP", "CAP"
}


def load_universe_resilient():
    # First try the long-standing official ASX listed-company CSV.
    try:
        raw = base.fetch_bytes(base.ASX_LIST_URL).decode("utf-8-sig", errors="ignore")
        rows = list(csv.reader(io.StringIO(raw)))
        out = []
        seen = set()
        for row in rows:
            if len(row) < 2:
                continue
            code = row[1].strip().upper()
            name = row[0].strip()
            if not re.fullmatch(r"[A-Z0-9]{3,5}", code):
                continue
            if code in seen:
                continue
            seen.add(code)
            out.append({"ticker": code, "name": name or code})
        if len(out) >= 1000:
            print("Universe source: ASXListedCompanies.csv", len(out))
            return out
    except Exception as e:
        print("Primary ASX universe source failed", e)

    # Current official ASX ISIN directory. It is delivered with an .xls suffix
    # but remains usable as tab-delimited text for extracting issuer codes.
    raw = base.fetch_bytes(ISIN_URL).decode("latin-1", errors="ignore")
    found = []
    seen = set()
    for line in raw.splitlines():
        if "\t" not in line:
            continue
        fields = [x.strip() for x in line.split("\t")]
        if not any(re.fullmatch(r"AU[A-Z0-9]{10}", x.upper()) for x in fields):
            continue
        candidates = []
        for field in fields:
            token = field.upper().strip()
            if re.fullmatch(r"[A-Z0-9]{3}", token) and token not in EXCLUDE:
                candidates.append(token)
        if not candidates:
            continue
        code = candidates[0]
        if code in seen:
            continue
        seen.add(code)
        name = next((x for x in fields if len(x) > 5 and not re.fullmatch(r"AU[A-Z0-9]{10}", x.upper())), code)
        found.append({"ticker": code, "name": name})

    if len(found) < 1000:
        raise RuntimeError(f"ASX ISIN universe unexpectedly small: {len(found)}")
    print("Universe source: ASX ISIN directory", len(found))
    return found


base.load_asx_universe = load_universe_resilient
base.main()
