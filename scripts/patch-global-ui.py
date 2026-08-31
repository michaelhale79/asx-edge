from pathlib import Path

p=Path('index.html')
s=p.read_text()

css='''.global-chip{display:inline-flex;align-items:center;gap:4px;border-radius:999px;padding:5px 8px;font-size:9px;font-weight:850;border:1px solid var(--line)}.global-chip.bullish{background:#153b24;border-color:#2e6e45;color:#baf3cc}.global-chip.bearish{background:#3a1b1b;border-color:#703636;color:#ffb0b0}.global-chip.neutral{background:#1b2d3e;border-color:#36516a;color:#c5dbef}.global-box{margin-top:8px;padding:11px;border-radius:12px;background:#101720;border:1px solid var(--line)}.global-theme-row{padding:9px 0;border-bottom:1px solid var(--line)}.global-theme-row:last-child{border-bottom:0}.global-theme-name{font-size:12px;font-weight:850}.global-headline{font-size:10px;color:var(--muted);line-height:1.4;margin-top:4px}.source-badge{font-size:8px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}.trend-source{font-size:9px;color:var(--muted);margin-top:8px}'''
if '.global-chip{' not in s:
    s=s.replace('</style>',css+'</style>',1)

s=s.replace('>Isobel & Oliver</button>','>Kids</button>')

panel='<div class="panel"><div class="panel-title">Global trends</div><div id="detailGlobalTrend"></div></div>'
anchor='<div class="panel"><div class="panel-title">Why this could outperform</div><p id="detailThesis"></p></div>'
if 'id="detailGlobalTrend"' not in s:
    if anchor not in s: raise SystemExit('detail panel anchor missing')
    s=s.replace(anchor,panel+anchor,1)

helper='''function globalTrendInfo(s){const score=Number(s?.globalTrendScore||0),adj=Number(s?.globalTrendAdjustment||0),signal=String(s?.globalTrendSignal||"NEUTRAL"),themes=Array.isArray(s?.globalThemes)?s.globalThemes:[],top=themes[0]?.theme||"No material global theme";return {score,adj,signal,themes,top,className:signal==="BULLISH"?"bullish":signal==="BEARISH"?"bearish":"neutral"}}\nfunction globalChip(s){const g=globalTrendInfo(s);if(!g.score&&!s?.trendCandidate)return "";return `<span class="global-chip ${g.className}">GLOBAL ${g.adj>=0?"+":""}${g.adj} · ${g.top}</span>`}\n'''
if 'function globalTrendInfo(' not in s:
    marker='function edgeClass('
    if marker not in s: raise SystemExit('helper anchor missing')
    s=s.replace(marker,helper+marker,1)

# Add global chip to normal stock cards by appending after tags begin, preserving existing signals.
old='''<span class="tag ${edgeClass(s.edge)}">${s.edge}</span><span class="tag">Opp ${s.opp}</span>'''
new='''<span class="tag ${edgeClass(s.edge)}">${s.edge}</span>${globalChip(s)}<span class="tag">Opp ${s.opp}</span>'''
if old in s and '${globalChip(s)}' not in s:
    s=s.replace(old,new,1)

# Render global detail content after the regular call text is populated.
needle='''$("#detailCall").textContent=r.reason+(co?` Tracking: ${co.days}/${co.horizon} days, ${pctText(co.ret)} since the call.`:"");'''
render='''$("#detailCall").textContent=r.reason+(co?` Tracking: ${co.days}/${co.horizon} days, ${pctText(co.ret)} since the call.`:"");const gt=globalTrendInfo(s);$("#detailGlobalTrend").innerHTML=gt.themes.length?`<div class="global-chip ${gt.className}">${gt.signal} · score ${gt.score>=0?"+":""}${gt.score} · opportunity ${gt.adj>=0?"+":""}${gt.adj}</div><div class="global-box">${gt.themes.slice(0,3).map(t=>`<div class="global-theme-row"><div class="global-theme-name">${t.theme} · ${Number(t.score)>=0?"+":""}${t.score}</div><div class="source-badge">${t.direction||"NEUTRAL"}</div>${(t.headlines||[]).slice(0,2).map(h=>`<div class="global-headline">${h.title}${h.source?` · ${h.source}`:""}</div>`).join("")}</div>`).join("")}</div><div class="trend-source">Global themes are supporting evidence only; BUY/HOLD/SELL also uses company, price, risk, ASX announcements and short-interest signals.</div>`:`<div class="company">No material global trend exposure is currently mapped to this company.</div>`;'''
if '$("#detailGlobalTrend").innerHTML=' not in s:
    if needle not in s: raise SystemExit('detail render anchor missing')
    s=s.replace(needle,render,1)

p.write_text(s)
print('Patched global trends UI')
