from pathlib import Path
import re
p=Path('index.html')
s=p.read_text()

# 3-column home tabs
s=s.replace('.home-tabs{display:grid;grid-template-columns:1fr 1fr;', '.home-tabs{display:grid;grid-template-columns:repeat(3,1fr);')

# Replace the existing home tab block in one shot.
pat=re.compile(r'<div class="home-tabs">.*?<div class="home-pane" data-home-pane="tracking"><div id="scorecard"></div></div>',re.S)
new='''<div class="home-tabs"><button class="home-tab active" data-home-tab="buys">Top Buys</button><button class="home-tab" data-home-tab="nearbuy">Near Buy</button><button class="home-tab" data-home-tab="tracking">Tracking</button></div><div class="home-pane active" data-home-pane="buys"><div class="small" style="margin:0 2px 10px">Only stocks that pass every current BUY rule appear here. The list is not padded to ten.</div><div id="homeStocks"></div></div><div class="home-pane" data-home-pane="nearbuy"><div class="small" style="margin:0 2px 10px">Highest-ranked HOLDs that are closest to becoming a BUY, with the blocking rule shown.</div><div id="nearBuyStocks"></div></div><div class="home-pane" data-home-pane="tracking"><div id="scorecard"></div></div>'''
s,n=pat.subn(new,s,count=1)
if n!=1: raise SystemExit('existing home tabs block not found')

# Update home tab click handling from prior patch if present.
s=s.replace("data-home-tab=\"top10\"", "data-home-tab=\"buys\"")
s=s.replace("data-home-pane=\"top10\"", "data-home-pane=\"buys\"")

# Add helpers before openDetail. They deliberately reuse the same recommendation() gate
# as the visible BUY/HOLD/SELL call, preventing ranking logic from redefining BUY.
marker='function openDetail(t){'
if marker not in s: raise SystemExit('openDetail marker not found')
helper=r'''function buyBlockers(s){
 const threshold=Number($("#threshold")?.value||75),sh=shortSignal(s),opp=Number(s.opp||0),risk=Number(s.risk||0),conf=Number(s.confidence??50),ann=Number(s.announcementSignal||0),fund=Number(s.fundamentalScore??50),frisk=Number(s.fundamentalRisk??50),evRisk=Number(s.qualityEvidenceRisk??s.evidenceRisk??50),mgmt=Number(s.managementCredibilityScore??s.managementDeliveryScore??50),adjusted=opp+learnedSignalAdjustment(s)+Number(s.aiEventAdjustment||0),out=[];
 if(adjusted<threshold)out.push(`score ${Math.round(adjusted)} / ${threshold} required`);
 if(risk>=50)out.push(`risk ${Math.round(risk)} / below 50 required`);
 if(ann<0)out.push(`announcement signal ${Math.round(ann)} / non-negative required`);
 if(conf<55)out.push(`confidence ${Math.round(conf)} / 55 required`);
 if(sh.score<=-10)out.push(`short interest is a strong bearish counter-signal`);
 if(fund<45)out.push(`fundamentals ${Math.round(fund)} / 45 required`);
 if(frisk>=65)out.push(`fundamental risk ${Math.round(frisk)} / below 65 required`);
 if(evRisk>=65)out.push(`disclosure risk ${Math.round(evRisk)} / below 65 required`);
 if(mgmt<35)out.push(`management credibility ${Math.round(mgmt)} / 35 required`);
 return out;
}
function refreshHomeBuyTabs(){
 if(!Array.isArray(stocks)||!stocks.length)return;
 const ranked=[...stocks].sort((a,b)=>Number(b.opp||0)+Number(b.aiEventAdjustment||0)+learnedSignalAdjustment(b)-Number(a.opp||0)-Number(a.aiEventAdjustment||0)-learnedSignalAdjustment(a));
 const buys=ranked.filter(s=>recommendation(s).label==='BUY').slice(0,10);
 const near=ranked.filter(s=>recommendation(s).label==='HOLD').map(s=>({s,b:buyBlockers(s)})).sort((a,b)=>a.b.length-b.b.length||(Number(b.s.opp||0)-Number(a.s.opp||0))).slice(0,10);
 const h=$("#homeStocks"),n=$("#nearBuyStocks");
 if(h)h.innerHTML=buys.length?buys.map(stockCard).join(''):'<div class="empty">No stocks currently pass every BUY rule. ASX Edge will not fill this list with weaker HOLDs.</div>';
 if(n)n.innerHTML=near.length?near.map(x=>{const html=stockCard(x.s);const blocker=`<div class="analysis-item watch" style="margin-top:8px"><b>What stops BUY:</b> ${x.b.slice(0,3).join(' · ')||'Very close — waiting for the next qualifying signal.'}</div>`;return html.replace('</div>',`${blocker}</div>`)}).join(''):'<div class="empty">No near-BUY HOLDs currently available.</div>';
}
'''
if 'function buyBlockers(s)' not in s:s=s.replace(marker,helper+marker,1)

# Run after the existing normal home render. MutationObserver keeps it synced whenever
# the app refreshes data without requiring brittle edits to the main render function.
anchor='initLock();'
addon=r'''const _homeBuyObserver=new MutationObserver(()=>{if(window._homeBuyBusy)return;window._homeBuyBusy=true;try{refreshHomeBuyTabs()}finally{setTimeout(()=>window._homeBuyBusy=false,0)}});const _homeStocksNode=document.getElementById('homeStocks');if(_homeStocksNode)_homeBuyObserver.observe(_homeStocksNode,{childList:true});document.addEventListener('change',e=>{if(e.target&&e.target.id==='threshold')setTimeout(refreshHomeBuyTabs,0)});setTimeout(refreshHomeBuyTabs,250);'''
if addon not in s:
    if anchor not in s: raise SystemExit('initLock marker not found')
    s=s.replace(anchor,anchor+addon,1)

p.write_text(s)
print('Top Buys / Near Buy / Tracking tabs integrated')
