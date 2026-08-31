from pathlib import Path

p=Path('index.html')
s=p.read_text()

old='<div class="section-title">Top 10 opportunities</div><div id="homeStocks"></div><div class="section-title">Recommendation scorecard</div><div id="scorecard"></div></section>'
new='''<div class="home-tabs"><button class="home-tab active" data-home-tab="top10">Top 10</button><button class="home-tab" data-home-tab="tracking">Tracking</button></div><div class="home-pane active" data-home-pane="top10"><div class="section-title">Top 10 opportunities</div><div class="small" style="margin:-4px 2px 10px;line-height:1.4">Ranked by overall opportunity. A stock is only marked BUY after it also clears the risk, confidence, fundamental, disclosure, management and short-interest gates.</div><div id="homeStocks"></div></div><div class="home-pane" data-home-pane="tracking"><div class="section-title">Recommendation tracking</div><div id="scorecard"></div></div></section>'''
if old not in s:
    raise SystemExit('home opportunity/scorecard block not found')
s=s.replace(old,new,1)

css='.portfolio-pane{display:none}.portfolio-pane.active{display:block}'
css_new=css+'.home-tabs{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:16px 0 10px}.home-tab{min-height:44px;border:1px solid var(--line);border-radius:12px;background:var(--panel);color:var(--muted);font-size:11px;font-weight:800}.home-tab.active{border-color:#38694a;background:#17261d;color:#a9edbe}.home-pane{display:none}.home-pane.active{display:block}'
if css not in s:
    raise SystemExit('tab css anchor not found')
s=s.replace(css,css_new,1)

marker='function setPortfolioTab(key){'
fn='''function setHomeTab(key){$$('[data-home-tab]').forEach(b=>b.classList.toggle('active',b.dataset.homeTab===key));$$('[data-home-pane]').forEach(p=>p.classList.toggle('active',p.dataset.homePane===key));}\n'''
if 'function setHomeTab(key)' not in s:
    if marker not in s: raise SystemExit('setPortfolioTab anchor not found')
    s=s.replace(marker,fn+marker,1)

# Bind buttons once alongside the existing portfolio-tab binding area.
bind="$$('[data-home-tab]').forEach(b=>b.onclick=()=>setHomeTab(b.dataset.homeTab));"
if bind not in s:
    # insert before initLock invocation, which is present near the end of the app script
    anchor='initLock();'
    pos=s.rfind(anchor)
    if pos<0: raise SystemExit('initLock invocation not found')
    s=s[:pos]+bind+s[pos:]

p.write_text(s)
print('Home Top 10 / Tracking tabs added')
