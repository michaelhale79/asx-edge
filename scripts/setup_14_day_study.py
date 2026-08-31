from pathlib import Path

# Patch whole-ASX scanner to preserve market-wide snapshots during the study.
p=Path('scripts/whole_asx_opportunities.py'); s=p.read_text(encoding='utf-8')
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

# Commit snapshots with the whole-ASX update.
p=Path('.github/workflows/whole-asx-opportunities.yml'); s=p.read_text(encoding='utf-8')
s=s.replace('          git add data.json\n','          git add data.json study/market_snapshots 2>/dev/null || git add data.json\n',1)
p.write_text(s,encoding='utf-8')

# Harden intraday slots, add refresh health audit, and wire new research stages.
p=Path('.github/workflows/intraday-refresh.yml'); s=p.read_text(encoding='utf-8')
s=s.replace('  contents: read\n','  contents: write\n',1)
s=s.replace('    steps:\n      - name: Check Melbourne refresh slot\n', '''    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check Melbourne refresh slot
''',1)
s=s.replace('          import datetime\n          from zoneinfo import ZoneInfo\n          import os\n\n          now = datetime.datetime.now(ZoneInfo("Australia/Melbourne"))\n          valid_hours = {8, 10, 12, 14, 16}\n          should_run = now.weekday() < 5 and now.hour in valid_hours\n\n          if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":\n              should_run = True\n\n          print("Melbourne time:", now.isoformat())\n          print("Refresh slot:", should_run)\n          with open(os.environ["GITHUB_OUTPUT"], "a") as fh:\n              fh.write(f"run={\'true\' if should_run else \'false\'}\\n")\n', '''          import datetime
          import json
          from zoneinfo import ZoneInfo
          import os
          from pathlib import Path

          now = datetime.datetime.now(ZoneInfo("Australia/Melbourne"))
          valid_hours = [8, 10, 12, 14, 16]
          slot = None
          for hour in valid_hours:
              target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
              age_minutes = (now - target).total_seconds() / 60
              if 0 <= age_minutes <= 90:
                  slot = target
          event = os.environ.get("GITHUB_EVENT_NAME")
          health = {}
          hp = Path("refresh-health.json")
          if hp.exists():
              try: health = json.loads(hp.read_text(encoding="utf-8"))
              except Exception: health = {}
          slot_key = slot.strftime("%Y-%m-%dT%H:00%z") if slot else ""
          should_run = bool(slot) and now.weekday() < 5 and health.get("lastSlotKey") != slot_key
          if event == "workflow_dispatch":
              should_run = True
              slot_key = "MANUAL-" + now.strftime("%Y-%m-%dT%H:%M%z")
          print("Melbourne time:", now.isoformat())
          print("Resolved slot:", slot_key or "none")
          print("Last completed slot:", health.get("lastSlotKey"))
          print("Refresh slot:", should_run)
          with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
              fh.write(f"run={'true' if should_run else 'false'}\\n")
              fh.write(f"slot={slot_key}\\n")
''',1)
s=s.replace('          GH_REPO: ${{ github.repository }}\n', '          GH_REPO: ${{ github.repository }}\n          REFRESH_SLOT: ${{ steps.melbourne.outputs.slot }}\n',1)
needle='          dispatch_and_wait "company-profiles.yml" "Company sector and profile enrichment"\n          dispatch_and_wait "recommendation-history.yml" "Persistent recommendation tracking and learning diagnostics"\n'
repl='''          dispatch_and_wait "company-profiles.yml" "Company sector and profile enrichment"
          dispatch_and_wait "deep-research.yml" "Company strategy and short-vs-long-term research"
          dispatch_and_wait "recommendation-history.yml" "Persistent recommendation tracking and learning diagnostics"
          dispatch_and_wait "14-day-study-analysis.yml" "Fourteen-day missed-opportunity analysis"

          python - <<'PY'
          import datetime, json, os
          from zoneinfo import ZoneInfo
          now=datetime.datetime.now(ZoneInfo("Australia/Melbourne"))
          payload={"lastSlotKey":os.environ.get("REFRESH_SLOT",""),"completedAtMelbourne":now.isoformat(),"status":"SUCCESS","pipeline":["asx-scan","whole-asx","global-trends","global-candidates","company-profiles","deep-research","recommendation-history","14-day-study-analysis"]}
          open("refresh-health.json","w",encoding="utf-8").write(json.dumps(payload,indent=2))
          PY
          git config user.name "ASX Edge Bot"
          git config user.email "asx-edge@users.noreply.github.com"
          git pull --rebase origin main
          git add refresh-health.json
          git diff --cached --quiet || git commit -m "Record successful intraday refresh"
          git push
'''
if needle not in s: raise SystemExit('intraday pipeline anchor missing')
s=s.replace(needle,repl,1)
p.write_text(s,encoding='utf-8')

print('14-day study and intraday hardening patched')
