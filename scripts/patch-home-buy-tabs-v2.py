from pathlib import Path
p=Path('index.html')
s=p.read_text()

s=s.replace('.home-tabs{display:grid;grid-template-columns:1fr 1fr;', '.home-tabs{display:grid;grid-template-columns:repeat(3,1fr);')

start=s.find('<div class="home-tabs">')
end=s.find('</section>\n<section class="page" id="discover">',start)
if start<0 or end<0: raise SystemExit('home tab region not found')
new='''<div class="home-tabs"><button class="home-tab active" data-home-tab="buys">Top Buys</button><button class="home-tab" data-home-tab="nearbuy">Near Buy</button><button class="home-tab" data-home-tab="tracking">Tracking</button></div><div class="home-pane active" data-home-pane="buys"><div class="small" style="margin:0 2px 10px">Only stocks that pass every current BUY rule appear here. The list is not padded to ten.</div><div id="homeStocks"></div></div><div class="home-pane" data-home-pane="nearbuy"><div class="small" style="margin:0 2px 10px">Highest-ranked HOLDs that are closest to becoming a BUY, with the blocking rule shown.</div><div id="nearBuyStocks"></div></div><div class="home-pane" data-home-pane="tracking"><div id="scorecard"></div></div>'''
s=s[:start]+new+s[end:]

marker='function openDetail(t){'
if marker not in s: raise SystemExit('openDetail marker not found')
helper=r'''function buyBlockers(s){
 const threshold=Number($("#threshold")?.value||75),sh=shortSignal(s),opp=Number(s.opp||0),risk=Number(s.risk||0),conf=Number(s.confidence??50),ann=Number(s.announcementSignal||0),fund=Number(s.fundamentalScore??50),frisk=Number(s.fundamentalRisk??50),evRisk=Number(s.qualityEvidenceRisk??s.evidenceRisk??50),mgmt=Number(s.managementCredibilityScore??s.managementDeliveryScore??50),adjusted=opp+learnedSignalAdjustment(s)+Number(s.aiEventAdjustment||0),out=[];
 if(adjusted<threshold)out.push(`score ${Math.round(adjusted)} / ${threshold} required`);
 if(risk>=50)out.push(`risk ${Math.round(risk)} / below 50 required`);
 if(ann<0)out.push(`announcement signal ${Math.round(ann)} / non-negative required`);
 if(conf<55)out.push(`confidence ${Math.round(conf)} / 55 required`);
 if(sh.score<=-10)out.push('short interest is a strong bearish counter-signal');
 if(fund<45)out.push(`fundamentals ${Math.round(fund)} / 45 required`);
 if(frisk>=65)out.push(`fundamental risk ${Math.round(frisk)} / below 65 required`);
 if(evRisk>=65)out.push(`disclosure risk ${Math.round(evRisk)} / below 65 required`);
 if(mgmt<35)out.push(`management credibility ${Math.round(mgmt)} / 35 required`);
 return out;
}
function refreshHomeBuyTabs(){
 if(!Array.isArray(stocks)||!stocks.length)return;
 const rank=x=>Number(x.opp||0)+Number(x.aiEventAdjustment||0)+learnedSignalAdjustment(x);
 const ranked=[...stocks].sort((a,b)=>rank(b)-rank(a));
 const buys=ranked.filter(s=>recommendation(s).label==='BUY').slice(0,10);
 const near=ranked.filter(s=>recommendation(s).label==='HOLD').map(s=>({s,b:buyBlockers(s)})).sort((a,b)=>a.b.length-b.b.length||rank(b.s)-rank(a.s)).slice(0,10);
 const h=$("#homeStocks"),n=$("#nearBuyStocks");
 if(h)h.innerHTML=buys.length?buys.map(stockCard).join(''):'<div class="empty">No stocks currently pass every BUY rule. ASX Edge will not fill this list with weaker HOLDs.</div>';
 if(n)n.innerHTML=near.length?near.map(x=>`<div>${stockCard(x.s)}<div class="analysis-item watch" style="margin:-2px 0 10px"><b>What stops BUY:</b> ${x.b.slice(0,3).join(' · ')||'Very close — waiting for the next qualifying signal.'}</div></div>`).join(''):'<div class="empty">No near-BUY HOLDs currently available.</div>';
}
'''
if 'function buyBlockers(s)' not in s:s=s.replace(marker,helper+marker,1)

anchor='initLock();'
addon=r'''const _homeBuyObserver=new MutationObserver(()=>{if(window._homeBuyBusy)return;window._homeBuyBusy=true;try{refreshHomeBuyTabs()}finally{setTimeout(()=>window._homeBuyBusy=false,0)}});const _homeStocksNode=document.getElementById('homeStocks');if(_homeStocksNode)_homeBuyObserver.observe(_homeStocksNode,{childList:true});document.addEventListener('change',e=>{if(e.target&&e.target.id==='threshold')setTimeout(refreshHomeBuyTabs,0)});setTimeout(refreshHomeBuyTabs,250);'''
if addon not in s:
    if anchor not in s: raise SystemExit('initLock marker not found')
    s=s.replace(anchor,anchor+addon,1)

p.write_text(s)
print('Top Buys / Near Buy / Tracking tabs integrated')
