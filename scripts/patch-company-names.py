from pathlib import Path

p=Path('scripts/whole_asx_opportunities.py')
s=p.read_text(encoding='utf-8')
old='''    # Keep the existing detailed universe intact, then add/mark whole-ASX discoveries.\n    merged = list(data.get("stocks", []))\n    positions = {str(s.get("ticker", "")).upper(): i for i, s in enumerate(merged)}\n'''
new='''    # Keep the existing detailed universe intact, then add/mark whole-ASX discoveries.\n    merged = list(data.get("stocks", []))\n    # Fill proper company names from the official ASX universe when the older\n    # detailed scanner only stored the ticker as its name.\n    universe_names = {str(x.get("ticker", "")).upper(): str(x.get("name", "")).strip() for x in universe}\n    for stock in merged:\n        ticker = str(stock.get("ticker", "")).upper()\n        current_name = str(stock.get("name", "") or "").strip()\n        better_name = universe_names.get(ticker, "")\n        if better_name and (not current_name or current_name.upper() == ticker):\n            stock["name"] = better_name\n    positions = {str(s.get("ticker", "")).upper(): i for i, s in enumerate(merged)}\n'''
if old not in s:
    if 'universe_names = {' in s:
        print('company name enrichment already installed')
    else:
        raise SystemExit('company name merge anchor not found')
else:
    s=s.replace(old,new,1)
    p.write_text(s,encoding='utf-8')
    print('installed company name enrichment')
