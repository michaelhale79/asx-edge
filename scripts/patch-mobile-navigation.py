from pathlib import Path
p=Path('index.html')
s=p.read_text()

# CSS
css=r'''
.hero{cursor:pointer}.hero:active{transform:scale(.995)}.hero-text.hero-collapsed{display:none}.hero-label{display:flex;justify-content:space-between;gap:8px}.hero-label:after{content:'tap for why';text-transform:none;letter-spacing:0;color:var(--muted)}
.detail-icon-tabs{position:sticky;top:73px;z-index:15;display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:10px 0;background:rgba(11,17,23,.96);padding:7px 0;backdrop-filter:blur(14px)}.detail-icon-tab{border:1px solid var(--line);border-radius:12px;background:var(--panel);color:var(--muted);min-height:51px;font-size:9px;font-weight:800;padding:5px 2px}.detail-icon-tab .ico{display:block;font-size:20px;line-height:22px;margin-bottom:2px}.detail-icon-tab.active{border-color:#38694a;background:#17261d;color:#a9edbe}.detail-group-hidden{display:none!important}
.score-box{cursor:pointer;position:relative}.score-box:after{content:'ⓘ';position:absolute;right:8px;top:8px;color:var(--muted);font-size:11px}.score-box:active{transform:scale(.985)}
.edge-modal{position:fixed;inset:0;z-index:10000;background:rgba(0,0,0,.64);display:none;align-items:flex-end;justify-content:center}.edge-modal.open{display:flex}.edge-modal-card{width:min(100%,520px);max-height:78vh;overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:20px 20px 0 0;padding:18px 16px calc(20px + env(safe-area-inset-bottom));box-shadow:0 -18px 50px rgba(0,0,0,.45)}.edge-modal-head{display:flex;align-items:center;justify-content:space-between;gap:10px}.edge-modal-title{font-size:19px;font-weight:900}.edge-modal-close{border:1px solid var(--line);border-radius:10px;background:var(--panel2);color:white;width:38px;height:38px}.edge-modal-value{font-size:30px;font-weight:900;margin:10px 0}.edge-modal-body{font-size:13px;line-height:1.55;color:#d6dee6}.edge-modal-note{margin-top:12px;padding:10px;border:1px solid var(--line);border-radius:11px;background:#101720;color:var(--muted);font-size:11px;line-height:1.45}
'''
if '.detail-icon-tabs{' not in s:
    s=s.replace('</style>',css+'</style>',1)

# Insert detail icon tabs after tags.
needle='<div class="tags" id="detailTags"></div>'
tabs='''<div class="tags" id="detailTags"></div><div class="detail-icon-tabs" id="detailIconTabs"><button class="detail-icon-tab active" data-detail-group="overview"><span class="ico">⌂</span>Overview</button><button class="detail-icon-tab" data-detail-group="analysis"><span class="ico">⌁</span>Analysis</button><button class="detail-icon-tab" data-detail-group="evidence"><span class="ico">▤</span>Evidence</button><button class="detail-icon-tab" data-detail-group="scores"><span class="ico">◎</span>Scores</button></div>'''
if 'id="detailIconTabs"' not in s:
    if needle not in s: raise SystemExit('detail tags insertion point not found')
    s=s.replace(needle,tabs,1)

# Popup modal before bottom navigation.
modal='''<div class="edge-modal" id="scoreInfoModal"><div class="edge-modal-card"><div class="edge-modal-head"><div class="edge-modal-title" id="scoreInfoTitle">Score</div><button class="edge-modal-close" id="scoreInfoClose">×</button></div><div class="edge-modal-value" id="scoreInfoValue"></div><div class="edge-modal-body" id="scoreInfoBody"></div><div class="edge-modal-note">Score Anatomy explains one input at a time. No single score creates a BUY by itself; ASX Edge combines opportunity, risk, confidence, fundamentals, disclosures, management, market behaviour and other evidence.</div></div></div>'''
if 'id="scoreInfoModal"' not in s:
    nav='<nav class="bottom-nav">'
    if nav not in s: raise SystemExit('bottom nav point not found')
    s=s.replace(nav,modal+nav,1)

# JS behaviour before initLock.
marker='initLock();'
js=r'''
const SCORE_INFO={
 'Opportunity':'Overall attractiveness of the setup using the engine’s market, catalyst and company inputs. Higher is better, but it still has to pass the risk and quality gates.',
 'Momentum':'How strongly price behaviour is trending in a favourable direction. Higher can support timing; very high momentum can also mean the move is already extended.',
 'Catalyst':'Strength of identifiable events that could change expectations or valuation. Higher means there are clearer potential reasons for the market to re-price the company.',
 'Confidence':'How much supporting evidence agrees with the current thesis. Higher means the signals are more consistent; low confidence prevents a BUY even when opportunity looks attractive.',
 'Risk':'General market/company risk score. Lower is better. High risk can block a BUY regardless of opportunity.',
 'Fundamental':'Underlying financial/business quality based on profitability, growth, balance sheet, cash flow, dilution and valuation inputs. Higher is better.',
 'Fundamental safety':'The inverse of fundamental risk. Higher means fewer balance-sheet, cash-flow, debt or dilution concerns.',
 'Balance sheet':'Financial resilience: cash, debt, liquidity and related measures. Higher is better.',
 'Cash flow':'Quality and strength of cash generation. Higher is generally better and reduces reliance on external funding.',
 'Dilution':'How favourable the share-count history is. Higher means less destructive dilution; low scores can indicate repeated issuance or funding pressure.',
 'Valuation':'How attractive valuation appears relative to the available financial evidence. Higher is more favourable, but cheap alone does not make a BUY.',
 'Disclosure':'Quality-adjusted evidence from actual company disclosures. Higher means recent source documents contain more supportive evidence and fewer material negatives.',
 'Disclosure safety':'The inverse of disclosure risk. Higher means fewer serious warning signs in the company’s own announcements and reports.',
 'Mgmt delivery':'Management credibility based on promises, guidance and subsequent delivery evidence. Higher means a stronger record of doing what management said it would do.',
 'Management delivery':'Management credibility based on promises, guidance and subsequent delivery evidence. Higher means a stronger record of doing what management said it would do.',
 'Short interest':'How bearish short positioning is. High short interest is treated as a counter-signal, not as proof that the market is right.',
 'Global trend':'Exposure to relevant global economic or thematic forces. Higher means current external conditions appear more supportive.',
 'AI event':'Capped contribution from the AI event analyst after reasoning through current events, company exposure and a devil’s-advocate check. It cannot override hard safety gates.'
};
function scoreInfoText(label){const k=Object.keys(SCORE_INFO).find(x=>label.toLowerCase().includes(x.toLowerCase()));return k?SCORE_INFO[k]:'This is one component of ASX Edge’s decision model. Higher is generally more supportive unless the label describes risk. It should be interpreted together with the other scores rather than in isolation.'}
function showScoreInfo(box){const label=box.querySelector('.score-label')?.textContent?.trim()||'Score',value=box.querySelector('.score-value')?.textContent?.trim()||'';document.getElementById('scoreInfoTitle').textContent=label;document.getElementById('scoreInfoValue').textContent=value;document.getElementById('scoreInfoBody').textContent=scoreInfoText(label);document.getElementById('scoreInfoModal').classList.add('open')}
function closeScoreInfo(){document.getElementById('scoreInfoModal')?.classList.remove('open')}
document.getElementById('scoreInfoClose')?.addEventListener('click',closeScoreInfo);document.getElementById('scoreInfoModal')?.addEventListener('click',e=>{if(e.target.id==='scoreInfoModal')closeScoreInfo()});document.getElementById('scoreGrid')?.addEventListener('click',e=>{const b=e.target.closest('.score-box');if(b)showScoreInfo(b)});
function detailGroupFor(title){title=(title||'').toLowerCase();if(['company overview','current call','company snapshot','price & market performance'].some(x=>title.includes(x)))return'overview';if(['analysis','global trends','ai event opportunities','why this could outperform','decision','what could prove it wrong'].some(x=>title.includes(x)))return'analysis';if(['company disclosure evidence','investment thesis & management','recent asx announcements'].some(x=>title.includes(x)))return'evidence';if(['score anatomy','recent score changes'].some(x=>title.includes(x)))return'scores';return'overview'}
function setDetailGroup(group){document.querySelectorAll('#detail .panel').forEach(p=>{const title=p.querySelector('.panel-title')?.textContent||'';p.classList.toggle('detail-group-hidden',detailGroupFor(title)!==group)});document.querySelectorAll('.detail-icon-tab').forEach(b=>b.classList.toggle('active',b.dataset.detailGroup===group));window.scrollTo({top:0,behavior:'smooth'})}
document.getElementById('detailIconTabs')?.addEventListener('click',e=>{const b=e.target.closest('[data-detail-group]');if(b)setDetailGroup(b.dataset.detailGroup)});
function openMineHoldings(){const b=document.querySelector('.nav[data-page="holdings"]');if(b)b.click();if(typeof setPortfolioTab==='function')setPortfolioTab('mine')}
const hc=document.getElementById('holdingCount')?.closest('.metric');if(hc){hc.classList.add('clickable');hc.addEventListener('click',openMineHoldings)}
function refreshBestBuyCompact(){if(!Array.isArray(stocks)||!stocks.length)return;const rank=x=>Number(x.opp||0)+Number(x.aiEventAdjustment||0)+(typeof learnedSignalAdjustment==='function'?learnedSignalAdjustment(x):0);const buys=stocks.filter(x=>typeof recommendation==='function'&&recommendation(x).label==='BUY').sort((a,b)=>rank(b)-rank(a));const best=buys[0],title=document.getElementById('heroTitle'),text=document.getElementById('heroText'),label=document.querySelector('.hero-label');if(label)label.firstChild.textContent='Best Buy';if(!title||!text)return;if(best){title.textContent=`${best.name||best.company||best.ticker} (${best.ticker})`;const r=recommendation(best);text.textContent=[r.reason,best.thesis||best.horizonReason||best.companyDescription||''].filter(Boolean).join(' ')}else{title.textContent='No current BUY';text.textContent='No stock currently passes every BUY rule.'}text.classList.add('hero-collapsed')}
const hero=document.querySelector('.hero');hero?.addEventListener('click',()=>document.getElementById('heroText')?.classList.toggle('hero-collapsed'));
const _bestBuyObs=new MutationObserver(()=>{if(!window._bbusy){window._bbusy=true;setTimeout(()=>{refreshBestBuyCompact();window._bbusy=false},0)}});const _live=document.getElementById('liveStatus');if(_live)_bestBuyObs.observe(_live,{childList:true,subtree:true});setTimeout(refreshBestBuyCompact,300);
const _origOpenDetail=typeof openDetail==='function'?openDetail:null;if(_origOpenDetail){openDetail=function(t){const r=_origOpenDetail(t);setTimeout(()=>setDetailGroup('overview'),0);return r}}
'''
if 'function refreshBestBuyCompact()' not in s:
    if marker not in s: raise SystemExit('initLock point not found')
    s=s.replace(marker,js+'\n'+marker,1)

p.write_text(s)
print('compact mobile navigation integrated')