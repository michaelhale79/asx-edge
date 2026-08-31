from pathlib import Path
import re
p=Path('index.html')
s=p.read_text()

css=r'''
/* Compact holdings cards */
#holdings .portfolio-tabs{margin:0 0 10px;position:sticky;top:74px;z-index:14;background:rgba(7,16,25,.82);padding:7px 0;backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px)}
#holdings .holding-card{padding:13px 14px 11px;margin-bottom:9px;border-radius:18px!important}
.holding-card .stock-top{align-items:center;gap:8px}
.holding-card .ticker{font-size:21px;line-height:1.05}
.holding-card .company{font-size:10px;margin-top:3px}
.holding-card .tap-more{display:inline;margin-left:5px;font-size:9px}
.holding-card .action{font-size:11px!important;padding:7px 11px!important;min-width:58px;text-align:center}
.holding-summary{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:10px}
.holding-stat{min-width:0;padding:8px 9px;border-radius:12px;background:rgba(8,17,26,.48);border:1px solid rgba(255,255,255,.08)}
.holding-stat-label{font-size:8px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.holding-stat-value{font-size:15px;font-weight:850;line-height:1.2;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.holding-stat-sub{font-size:8px;color:var(--muted);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.holding-actions{display:flex;align-items:center;gap:7px;margin-top:8px}
.holding-actions .btn{min-height:34px!important;padding:6px 10px!important;border-radius:11px!important;font-size:10px!important}
.holding-review{margin-left:auto;font-size:9px;color:var(--muted);font-weight:750}
.holding-why-btn{border:0;background:none!important;box-shadow:none!important;color:#8ed7ff!important;padding:5px 3px!important;font-size:10px;font-weight:800}
.holding-reason{display:none;margin-top:7px;padding:8px 9px;border-radius:10px;background:rgba(255,255,255,.035);color:#cbd6df;font-size:10px;line-height:1.4}
.holding-card.why-open .holding-reason{display:block}
.holding-card .trade-banner{display:none!important}
.holding-card>.thesis{display:none!important}
.holding-card .perf{display:none!important}
.holding-card .holding-readonly>.editor-actions{display:none!important}
@media(max-width:360px){.holding-summary{grid-template-columns:1fr 1fr}.holding-stat:last-child{grid-column:1/-1}}
'''
if '/* Compact holdings cards */' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

pat=re.compile(r'function holdingCard\(p,key,i\)\{.*?\}\nfunction bestOpportunity\(\)',re.S)
new=r'''function holdingCard(p,key,i){const st=stockOf(p.ticker),r=recommendation(st);if(st&&!p.dayZeroPrice){p.dayZeroPrice=Number(st.price||0);p.dayZeroDate=new Date().toISOString();savePortfolios()}const price=Number(st?.price||0),pl=p.buyPrice&&p.qty?(price-p.buyPrice)*p.qty:NaN,plPct=p.buyPrice?((price/p.buyPrice)-1)*100:NaN,dz=p.dayZeroPrice?((price/p.dayZeroPrice)-1)*100:NaN,id=`${key}:${i}`,editing=editingHolding===id;return `<div class="stock ${r.className} holding-card ${editing?"editing":""}" ${p.ticker?`data-open="${p.ticker}"`:""}><div class="stock-top"><div class="stock-name"><div class="ticker" data-open="${p.ticker}">${p.ticker||"NEW HOLDING"}</div><div class="company">${st?`${money(price)} · Opp ${st.opp}<span class="tap-more">View analysis ›</span>`:"Waiting for scanner"}</div></div><div class="action ${r.className}">${r.label}</div></div><div class="holding-readonly"><div class="holding-summary"><div class="holding-stat"><div class="holding-stat-label">P/L</div><div class="holding-stat-value ${pl>=0?"up":"down"}">${isFinite(pl)?money(pl):"—"}</div><div class="holding-stat-sub">${pctText(plPct)}</div></div><div class="holding-stat"><div class="holding-stat-label">Day zero</div><div class="holding-stat-value ${dz>=0?"up":"down"}">${pctText(dz)}</div><div class="holding-stat-sub">${p.dayZeroDate?new Date(p.dayZeroDate).toLocaleDateString("en-AU"):"First live price"}</div></div><div class="holding-stat"><div class="holding-stat-label">Position</div><div class="holding-stat-value">${p.qty||0}</div><div class="holding-stat-sub">@ ${p.buyPrice?money(p.buyPrice):"—"}</div></div></div><div class="holding-actions"><button class="btn" data-editholding="${key}" data-i="${i}">Edit</button><button class="holding-why-btn" data-holdingwhy="1">Why ${r.label}?</button><span class="holding-review">${r.horizon}d review</span></div><div class="holding-reason">${r.reason}</div></div><div class="holding-edit"><div class="editor"><div class="field"><label>Ticker</label><input data-edit="ticker" data-key="${key}" data-i="${i}" value="${p.ticker}"></div><div class="field"><label>Qty</label><input inputmode="decimal" data-edit="qty" data-key="${key}" data-i="${i}" value="${p.qty||""}"></div><div class="field"><label>Buy price</label><input inputmode="decimal" data-edit="buyPrice" data-key="${key}" data-i="${i}" value="${p.buyPrice||""}"></div></div><div class="editor-actions"><button class="btn primary" data-saveholding="${key}" data-i="${i}">Save</button><button class="btn" data-cancelholding="${key}" data-i="${i}">Cancel</button><button class="btn danger" data-deleteholding="${key}" data-i="${i}">Delete</button></div></div></div>`}
function bestOpportunity()'''
s,n=pat.subn(new,s,count=1)
if n!=1: raise SystemExit('holdingCard function not found')

# delegated Why toggle; capture prevents the card's data-open handler from navigating.
marker='initLock();'
js=r'''document.addEventListener('click',e=>{const w=e.target.closest('[data-holdingwhy]');if(!w)return;e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();w.closest('.holding-card')?.classList.toggle('why-open')},true);'''
if "data-holdingwhy" in s and js not in s:
    if marker not in s: raise SystemExit('initLock marker not found')
    s=s.replace(marker,js+marker,1)

p.write_text(s)
print('compact holdings UI applied')
