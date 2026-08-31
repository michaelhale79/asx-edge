from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Add compact search styling.
s=s.replace('.tap-more{font-size:9px;color:#8fd8ff;margin-top:4px}', '.tap-more{font-size:9px;color:#8fd8ff;margin-top:4px}.quick-search{margin:0 0 12px}.quick-results{margin-top:7px}.quick-result{display:flex;align-items:center;gap:10px;padding:10px 11px;margin-bottom:6px;border:1px solid var(--line);border-radius:12px;background:var(--panel);cursor:pointer}.quick-result .qr-main{flex:1;min-width:0}.quick-result .qr-ticker{font-size:15px;font-weight:900}.quick-result .qr-name{font-size:10px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.sector-pill{display:inline-block;margin-bottom:7px;padding:4px 8px;border-radius:999px;border:1px solid #315b7b;background:#17283a;color:#b9ddff;font-size:9px;font-weight:850}.company-overview-text{font-size:13px;line-height:1.5;color:#d6dee6}.industry-line{font-size:10px;color:var(--muted);margin-bottom:8px}')

# Add quick lookup to Home, and broaden Discover wording.
home_anchor='<section class="page active" id="home"><div class="notice" id="liveStatus">Loading ASX Edge data…</div>'
home_new='<section class="page active" id="home"><div class="quick-search"><input class="search" id="quickSearch" placeholder="Search ASX ticker or company"><div class="quick-results" id="quickResults"></div></div><div class="notice" id="liveStatus">Loading ASX Edge data…</div>'
if home_anchor not in s: raise SystemExit('home anchor missing')
s=s.replace(home_anchor,home_new,1)
s=s.replace('<input class="search" id="search" placeholder="Search ticker">','<input class="search" id="search" placeholder="Search ticker, company, sector or industry">',1)

# Put company overview first in detail, before Current call.
detail_anchor='<div class="tags" id="detailTags"></div><div class="panel"><div class="panel-title">Current call</div><p id="detailCall"></p></div>'
detail_new='<div class="tags" id="detailTags"></div><div class="panel"><div class="panel-title">Company overview</div><div id="companyOverview"></div></div><div class="panel"><div class="panel-title">Current call</div><p id="detailCall"></p></div>'
if detail_anchor not in s: raise SystemExit('detail anchor missing')
s=s.replace(detail_anchor,detail_new,1)

# Broaden Discover search across sector/industry.
old='function renderDiscover(){const q=$("#search").value.trim().toLowerCase(),r=stocks.filter(s=>(edgeFilter==="ALL"||s.edge===edgeFilter)&&(!q||s.ticker.toLowerCase().includes(q)||String(s.name||"").toLowerCase().includes(q))).sort((a,b)=>b.opp-a.opp);$("#discoverStocks").innerHTML=r.length?r.map(stockCard).join(""):`<div class="empty">No matching companies.</div>`;bind()}'
new='function renderDiscover(){const q=$("#search").value.trim().toLowerCase(),r=stocks.filter(s=>(edgeFilter==="ALL"||s.edge===edgeFilter)&&(!q||[s.ticker,s.name,s.sector,s.industry].some(v=>String(v||"").toLowerCase().includes(q)))).sort((a,b)=>b.opp-a.opp);$("#discoverStocks").innerHTML=r.length?r.map(stockCard).join(""):`<div class="empty">No matching companies.</div>`;bind()}'
if old not in s: raise SystemExit('renderDiscover anchor missing')
s=s.replace(old,new,1)

# Quick-search helper placed before renderHoldings.
anchor='function renderHoldings(){$("#myHoldings").innerHTML=portfolios.mine.map((p,i)=>holdingCard(p,"mine",i)).join("");'
helper='function renderQuickSearch(){const el=$("#quickSearch"),out=$("#quickResults");if(!el||!out)return;const q=el.value.trim().toLowerCase();if(!q){out.innerHTML="";return}const rows=stocks.filter(s=>[s.ticker,s.name,s.sector,s.industry].some(v=>String(v||"").toLowerCase().includes(q))).sort((a,b)=>{const ae=String(a.ticker||"").toLowerCase()===q?1:0,be=String(b.ticker||"").toLowerCase()===q?1:0;return be-ae||Number(b.opp||0)-Number(a.opp||0)}).slice(0,8);out.innerHTML=rows.length?rows.map(s=>`<div class="quick-result" data-open="${s.ticker}"><div class="qr-main"><div class="qr-ticker">${s.ticker}</div><div class="qr-name">${s.name&&s.name!==s.ticker?s.name:"ASX-listed company"}${s.sector?` · ${s.sector}`:""}</div></div><div class="action ${recommendation(s).className}">${recommendation(s).label}</div></div>`).join(""):`<div class="empty">No matching stock in the current ASX scan.</div>`;bind()}\n'+anchor
if anchor not in s: raise SystemExit('renderHoldings anchor missing')
s=s.replace(anchor,helper,1)

# Add overview rendering at the top of openDetail.
old='$("#detailScore").innerHTML=`${s.opp}<small>OPPORTUNITY</small>`;$("#detailTags").innerHTML=`<span class="tag ${r.className==="buy"?"green":r.className==="sell"?"red":"blue"}">${r.label}</span><span class="tag">${s.edge||s.opportunitySource||"ASX"}</span><span class="tag">Risk ${s.risk}</span><span class="tag">Confidence ${s.confidence??"—"}</span><span class="tag ${sh.className}">${sh.label}</span>`;$("#detailCall").textContent=r.reason'
new='$("#detailScore").innerHTML=`${s.opp}<small>OPPORTUNITY</small>`;$("#detailTags").innerHTML=`<span class="tag ${r.className==="buy"?"green":r.className==="sell"?"red":"blue"}">${r.label}</span><span class="tag">${s.edge||s.opportunitySource||"ASX"}</span><span class="tag">Risk ${s.risk}</span><span class="tag">Confidence ${s.confidence??"—"}</span><span class="tag ${sh.className}">${sh.label}</span>`;const overviewSector=s.sector||"Sector not yet classified",overviewIndustry=s.industry||"Industry classification pending",overviewText=s.description||`${s.name&&s.name!==s.ticker?s.name:s.ticker} is an ASX-listed company. A fuller business description has not yet been returned by the company-profile feed.`;$("#companyOverview").innerHTML=`<div class="sector-pill">${overviewSector}</div><div class="industry-line">${overviewIndustry}</div><div class="company-overview-text">${overviewText}</div>`;$("#detailCall").textContent=r.reason'
if old not in s: raise SystemExit('openDetail anchor missing')
s=s.replace(old,new,1)

# Wire quick search input.
old='$("#search").oninput=renderDiscover;$("#threshold").onchange=render;'
new='$("#search").oninput=renderDiscover;$("#quickSearch").oninput=renderQuickSearch;$("#threshold").onchange=render;'
if old not in s: raise SystemExit('search bind anchor missing')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('patched company overview + stock search')
