from pathlib import Path

p=Path('scripts/whole_asx_opportunities.py')
s=p.read_text(encoding='utf-8')
s=s.replace('import csv\nimport datetime as dt\n', 'import csv\nimport datetime as dt\nimport gzip\n', 1)
s=s.replace('from pathlib import Path\n', 'from pathlib import Path\nfrom zoneinfo import ZoneInfo\n', 1)
s=s.replace('MIN_SURFACE_SCORE = 55\n', '''MIN_SURFACE_SCORE = 55
STUDY_START = dt.date(2026, 8, 31)
STUDY_END = dt.date(2026, 9, 14)
STUDY_DIR = Path("study/market_snapshots")
''', 1)
fn='''\ndef write_study_snapshot(valid, surfaced):
    now_utc = dt.datetime.now(dt.timezone.utc)
    mel = now_utc.astimezone(ZoneInfo("Australia/Melbourne"))
    if not (STUDY_START <= mel.date() <= STUDY_END):
        return
    selected = {x["ticker"] for x in surfaced}
    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    stocks = []
    keys = ["ticker","name","price","opp","risk","confidence","momentum","quality","growth","valuation","catalystScore","return5d","return1m","return3m","return6m","return12m","relative1m","relative3m","relative6m","volumeRatio","drawdown60","dollarTurnover20d"]
    for row in valid:
        compact = {k: row.get(k) for k in keys}
        compact["selected"] = row.get("ticker") in selected
        stocks.append(compact)
    payload = {
        "capturedAt": now_utc.isoformat(),
        "melbourneDate": mel.date().isoformat(),
        "studyStart": STUDY_START.isoformat(),
        "studyEnd": STUDY_END.isoformat(),
        "companyCount": len(stocks),
        "selectedCount": len(selected),
        "stocks": stocks,
    }
    path = STUDY_DIR / (mel.strftime("%Y-%m-%dT%H%M%z") + ".json.gz")
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=9) as fh:
        json.dump(payload, fh, separators=(",", ":"))
    print("study snapshot", path, len(stocks))
\n'''
anchor='\n\ndef main():\n'
if 'def write_study_snapshot' not in s:
    if anchor not in s: raise SystemExit('whole scanner main anchor missing')
    s=s.replace(anchor, fn+anchor, 1)
needle='    surfaced = [x for x in valid if x["opp"] >= MIN_SURFACE_SCORE][:MAX_NEW_CANDIDATES]\n'
if 'write_study_snapshot(valid, surfaced)' not in s:
    if needle not in s: raise SystemExit('surfaced anchor missing')
    s=s.replace(needle, needle+'    write_study_snapshot(valid, surfaced)\n', 1)
p.write_text(s,encoding='utf-8')
print('market-wide study capture patched')
