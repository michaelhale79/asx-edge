import csv
import io
import re

import xlrd
import whole_asx_opportunities as base

ISIN_URL = "https://www.asx.com.au/content/dam/asx/issuers/ISIN.xls"
EXCLUDE = {
    "AUD", "USD", "NZD", "GBP", "EUR", "JPY", "HKD", "CAD", "CHF",
    "ORD", "CDI", "ETF", "ETP", "ETC", "FPO", "PREF", "NCP", "CAP",
    "ASX", "ISIN"
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

    # Current official ASX ISIN directory is a real legacy Excel workbook.
    raw = base.fetch_bytes(ISIN_URL)
    book = xlrd.open_workbook(file_contents=raw)
    found = []
    seen = set()

    for sheet in book.sheets():
        for r in range(sheet.nrows):
            fields = []
            for c in range(sheet.ncols):
                value = sheet.cell_value(r, c)
                text = str(value).strip()
                if text.endswith(".0") and text[:-2].isdigit():
                    text = text[:-2]
                fields.append(text)

            upper = [x.upper() for x in fields if x]
            if not any(re.fullmatch(r"AU[A-Z0-9]{10}", x) for x in upper):
                continue

            candidates = [
                x for x in upper
                if re.fullmatch(r"[A-Z0-9]{3}", x) and x not in EXCLUDE
            ]
            if not candidates:
                continue

            code = candidates[0]
            if code in seen:
                continue

            seen.add(code)
            name = next(
                (
                    x for x in fields
                    if len(x) > 5
                    and not re.fullmatch(r"AU[A-Z0-9]{10}", x.upper())
                    and x.upper() != code
                ),
                code,
            )
            found.append({"ticker": code, "name": name})

    if len(found) < 1000:
        raise RuntimeError(f"ASX ISIN universe unexpectedly small: {len(found)}")

    print("Universe source: ASX ISIN directory", len(found))
    return found


base.load_asx_universe = load_universe_resilient
base.main()
