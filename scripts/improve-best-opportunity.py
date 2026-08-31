from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

s=s.replace('<div class="hero-label">Best current setup</div>','<div class="hero-label">Best Opportunity</div>')
s=s.replace('<div class="panel-title">Why now</div><p id="detailCatalyst"></p>','<div class="panel-title" id="detailDecisionTitle">Decision</div><p id="detailCatalyst"></p>')

css_marker='.company-overview-text{font-size:13px;line-height:1.5;color:#d6dee6}.industry-line{font-size:10px;color:var(--muted);margin-bottom:8px}'
css_add=css_marker+'.hero-company{font-size:12px;color:#b8c6d4;margin-top:5px}.hero-points{display:grid;gap:6px;margin-top:11px}.hero-point{padding:8px 9px;border-radius:10px;background:rgba(0,0,0,.16);font-size:11px;line-height:1.4}.hero-point.good{color:#c4f5d4}.hero-point.watch{color:#ffe0aa}.decision-lead{font-weight:850;color:#fff}'
if css_marker in s and '.hero-company{' not in s:
    s=s.replace(css_marker,css_add)

insert_before='function render(){if(!stocks.length)return;'
helper=r'''function bestOpportunity(){const candidates=stocks.filter(s=>recommendation(s).label==="BUY");const pool=candidates.length?candidates:stocks;return [...pool].sort((a,b)=>{const score=x=>{const opp=Number(x.opp||0),val=Number(x.valuation??50),conf=Number(x.confidence??50),risk=Number(x.risk||0),r1=Number(x.return1m||0),r3=Number(x.return3m||0),rel=Number(x.relative3m||0),ann=Number(x.announcementSignal||0),shortAdj=Number(x.shortAdjustment||0),stretch=Math.max(0,r1-25)*.7+Math.max(0,r3-45)*.35;return opp*.42+val*.18+conf*.18+(100-risk)*.14+Math.max(-15,Math.min(15,rel))*.25+Math.max(-12,Math.min(12,ann))*.2+shortAdj*.45-stretch};return score(b)-score(a)})[0]}
function decisionReason(s,r){const parts=[],risk=[];const r1=Number(s.return1m||0),r3=Number(s.return3m||0),rel1=Number(s.relative1m||0),rel3=Number(s.relative3m||0),vol=Number(s.volumeRatio||0),ann=Number(s.announcementSignal||0),conf=Number(s.confidence??50),riskScore=Number(s.risk||0),shorts=Number(s.shortInterestPct),gt=Number(s.globalTrendScore||0),val=Number(s.valuation??50);if(rel1>=5)parts.push(`beating the ASX 200 by ${rel1.toFixed(1)}% over 1 month`);if(rel3>=8)parts.push(`3-month relative strength is +${rel3.toFixed(1)}%`);if(vol>=1.25)parts.push(`volume is ${vol.toFixed(2)}× normal, showing stronger market participation`);if(ann>=8)parts.push(`recent ASX news is positively scored at +${Math.round(ann)}`);if(gt>=10)parts.push(`global themes are supportive at +${Math.round(gt)}`);if(conf>=70)parts.push(`confidence is strong at ${Math.round(conf)}/100`);if(val>=60)parts.push(`valuation score is attractive at ${Math.round(val)}/100`);if(isFinite(shorts)&&shorts<=2)parts.push(`short interest is low at ${shorts.toFixed(1)}%`);if(r1>25)risk.push(`the share price has already risen ${r1.toFixed(1)}% in a month, so entry timing matters`);if(riskScore>=55)risk.push(`risk is elevated at ${Math.round(riskScore)}/100`);if(isFinite(shorts)&&shorts>=8)risk.push(`short interest is high at ${shorts.toFixed(1)}%`);if(ann<=-8)risk.push(`recent ASX news is negatively scored at ${Math.round(ann)}`);if(gt<=-10)risk.push(`global themes are a headwind at ${Math.round(gt)}`);if(rel1<=-5)risk.push(`it is underperforming the ASX 200 by ${Math.abs(rel1).toFixed(1)}% over 1 month`);let lead;if(r.label==="BUY")lead='Why BUY: the evidence is strong enough to justify considering an entry now.';else if(r.label==="SELL")lead='Why I would avoid / reduce: deterioration currently outweighs the upside case.';else lead='Why HOLD: there is not enough confirmation to add aggressively, but the case is not weak enough to exit automatically.';const pos=parts.length?` Supporting evidence: ${parts.slice(0,4).join('; ')}.`:' There is no single strong confirmation signal yet.';const neg=risk.length?` What stops this being stronger: ${risk.slice(0,3).join('; ')}.`:' No major counter-signal is dominating at the moment.';return lead+pos+neg}
function bestOpportunityHtml(s){const r=recommendation(s),name=(s.name&&s.name!==s.ticker)?s.name:s.ticker,desc=s.description||'Company profile is still being enriched.',sector=[s.sector,s.industry].filter(Boolean).join(' · '),reason=decisionReason(s,r),risk=Number(s.risk||0),val=Number(s.valuation??50),conf=Number(s.confidence??50);return `<div class="hero-company">${name}${sector?` · ${sector}`:''}</div><div class="hero-points"><div class="hero-point good"><b>Why it stands out:</b> ${reason}</div><div class="hero-point good"><b>Value check:</b> Opportunity ${Math.round(Number(s.opp||0))}/100 · Valuation ${Math.round(val)}/100 · Confidence ${Math.round(conf)}/100.</div><div class="hero-point watch"><b>Main risk:</b> Risk ${Math.round(risk)}/100. ${s.riskText||'Watch for deterioration in price action, news, shorts or global themes.'}</div></div><div class="hero-text">${desc}</div>`}
'''
if insert_before in s and 'function bestOpportunity(){' not in s:
    s=s.replace(insert_before,helper+insert_before)

old_render='const sorted=[...stocks].sort((a,b)=>b.opp-a.opp),top=sorted[0];$("#heroTitle").textContent=`${top.ticker} · ${recommendation(top).label}`;$("#heroText").textContent=recommendation(top).reason;'
new_render='const sorted=[...stocks].sort((a,b)=>b.opp-a.opp),top=bestOpportunity()||sorted[0];$("#heroTitle").textContent=`${top.ticker} · ${recommendation(top).label}`;$("#heroText").innerHTML=bestOpportunityHtml(top);'
if old_render in s:
    s=s.replace(old_render,new_render)
else:
    s=re.sub(r'const sorted=\[\.\.\.stocks\]\.sort\(\(a,b\)=>b\.opp-a\.opp\),top=sorted\[0\];\$\("#heroTitle"\)\.textContent=`\$\{top\.ticker\} · \$\{recommendation\(top\)\.label\}`;\$\("#heroText"\)\.textContent=recommendation\(top\)\.reason;',new_render,s)

old='$("#detailCatalyst").textContent=s.catalyst||"No catalyst information available.";'
new='$("#detailDecisionTitle").textContent=r.label==="BUY"?"Why BUY":r.label==="SELL"?"Why I would avoid / reduce":"Why HOLD";$("#detailCatalyst").textContent=decisionReason(s,r);'
if old in s:
    s=s.replace(old,new)
else:
    s=re.sub(r'\$\("#detailCatalyst"\)\.textContent=s\.catalyst\|\|"No catalyst information available\.";',new,s)

p.write_text(s,encoding='utf-8')
print('patched')
