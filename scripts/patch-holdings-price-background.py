from pathlib import Path
import re
p=Path('index.html')
s=p.read_text()

css=r'''
/* Holdings price alignment + fixed financial backdrop */
.holding-title-line{display:flex;align-items:baseline;gap:8px;min-width:0;flex-wrap:wrap}
.holding-card .holding-price{font-size:15.75px;line-height:1;font-weight:750;color:#c3d0dc;opacity:.94;white-space:nowrap;letter-spacing:-.01em}
.holding-card .company{margin-top:4px}
body{background-attachment:fixed!important}
body:before{background-attachment:fixed!important}
body:after{content:'ASX  ·  PRICE  ·  FLOW  ·  RISK  ·  SIGNAL  ·  VOLUME  ·  DATA  ·  TREND'!important;top:132px!important;font-size:9px!important;letter-spacing:5px!important;color:rgba(117,192,255,.052)!important;transform:rotate(-7deg)!important}
body{background-image:
 radial-gradient(circle at 18% -5%,rgba(64,162,255,.15),transparent 30%),
 radial-gradient(circle at 88% 18%,rgba(50,220,135,.12),transparent 26%),
 repeating-linear-gradient(0deg,rgba(95,142,176,.025) 0,rgba(95,142,176,.025) 1px,transparent 1px,transparent 7px),
 linear-gradient(180deg,#08111b 0%,#071019 46%,#050b11 100%)!important;background-attachment:fixed!important}
'''
if '/* Holdings price alignment + fixed financial backdrop */' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

old=r'''<div class=\"stock-name\"><div class=\"ticker\" data-open=\"${p.ticker}\">${p.ticker||\"NEW HOLDING\"}</div><div class=\"company\">${st?`${money(price)} · Opp ${st.opp}<span class=\"tap-more\">View analysis ›</span>`:\"Waiting for scanner\"}</div></div>'''
new=r'''<div class=\"stock-name\"><div class=\"holding-title-line\" data-open=\"${p.ticker}\"><span class=\"ticker\">${p.ticker||\"NEW HOLDING\"}</span><span class=\"holding-price\">${st?money(price):\"\"}</span></div><div class=\"company\">${st?`Opp ${st.opp}<span class=\"tap-more\">View analysis ›</span>`:\"Waiting for scanner\"}</div></div>'''
if old in s:
    s=s.replace(old,new,1)
elif 'holding-title-line' not in s:
    raise SystemExit('holding header markup not found')

p.write_text(s)
print('holdings price alignment and fixed financial backdrop applied')
