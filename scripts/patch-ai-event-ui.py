from pathlib import Path
p=Path('index.html')
s=p.read_text()

old='<div class="panel"><div class="panel-title">Global trends</div><div id="detailGlobalTrend"></div></div><div class="panel"><div class="panel-title">Why this could outperform</div>'
new='<div class="panel"><div class="panel-title">Global trends</div><div id="detailGlobalTrend"></div></div><div class="panel"><div class="panel-title">AI event opportunities</div><div id="detailAIEvents"></div></div><div class="panel"><div class="panel-title">Why this could outperform</div>'
if 'detailAIEvents' not in s:
    if old not in s: raise SystemExit('detail insertion point not found')
    s=s.replace(old,new,1)

old='learn=learnedSignalAdjustment(s),adjusted=opp+learn;'
new='learn=learnedSignalAdjustment(s),ai=Number(s.aiEventAdjustment||0),adjusted=opp+learn+ai;'
if 'adjusted=opp+learn+ai' not in s:
    if old not in s: raise SystemExit('recommendation adjustment point not found')
    s=s.replace(old,new,1)

old='return {label:"BUY",className:"buy",reason:`Strong opportunity with acceptable risk/confidence. ${sh.text}${learn?` Historical signal learning adjusts this setup ${learn>0?"+":""}${learn} points.`:""}`,horizon:30,learn};'
new='return {label:"BUY",className:"buy",reason:`Strong opportunity with acceptable risk/confidence. ${sh.text}${ai?` AI event reasoning contributes ${ai>0?"+":""}${ai} points.`:""}${learn?` Historical signal learning adjusts this setup ${learn>0?"+":""}${learn} points.`:""}`,horizon:30,learn};'
if 'AI event reasoning contributes ${ai' not in s:
    if old not in s: raise SystemExit('BUY reason point not found')
    s=s.replace(old,new,1)

old='return {label:"HOLD",className:"hold",reason:`Evidence is not strong enough for BUY or weak enough for SELL. ${sh.text}${learn?` Historical signal learning adjusts this setup ${learn>0?"+":""}${learn} points.`:""}`,horizon:20,learn}}'
new='return {label:"HOLD",className:"hold",reason:`Evidence is not strong enough for BUY or weak enough for SELL. ${sh.text}${ai?` AI event reasoning contributes ${ai>0?"+":""}${ai} points.`:""}${learn?` Historical signal learning adjusts this setup ${learn>0?"+":""}${learn} points.`:""}`,horizon:20,learn}}'
if old in s: s=s.replace(old,new,1)

old='${co?`<span class="tag ${co.outcome==="FAIL"?"red":co.outcome==="SUCCESS"?"green":"blue"}">${co.outcome} · ${pctText(co.ret)}</span>`:""}</div><div class="thesis">'
new='${Number(s.aiEventAdjustment||0)?`<span class="tag ${Number(s.aiEventAdjustment)>0?"green":"red"}">AI EVENT ${Number(s.aiEventAdjustment)>0?"+":""}${s.aiEventAdjustment}</span>`:""}${co?`<span class="tag ${co.outcome==="FAIL"?"red":co.outcome==="SUCCESS"?"green":"blue"}">${co.outcome} · ${pctText(co.ret)}</span>`:""}</div><div class="thesis">'
if 'AI EVENT ${Number(s.aiEventAdjustment)' not in s:
    if old not in s: raise SystemExit('stock card tag point not found')
    s=s.replace(old,new,1)

# Best Opportunity already evolves independently. Add the AI overlay only when the
# current formula exposes a stable insertion point; never fail the entire UI patch.
if 'ai*1.6-stretch' not in s:
    patterns=[
      ('+shortAdj*.25-stretch};','+shortAdj*.25+Number(x.aiEventAdjustment||0)*1.6-stretch};'),
      ('+shortAdj*.45-stretch};','+shortAdj*.45+Number(x.aiEventAdjustment||0)*1.6-stretch};'),
    ]
    for a,b in patterns:
        if a in s:
            s=s.replace(a,b,1); break

marker='function openDetail(t){'
if 'function aiEventHtml(s)' not in s:
    if marker not in s: raise SystemExit('openDetail marker not found')
    fn='''function aiEventHtml(s){const rows=Array.isArray(s.aiEventReasons)?s.aiEventReasons:[],adj=Number(s.aiEventAdjustment||0);if(!rows.length)return `<div class="empty">No material AI event-driven exposure is currently mapped to this company.</div>`;return `<div class="detail-kpis">${detailKpi("AI event signal",`${adj>0?"+":""}${adj} points`,adj>0?"up":adj<0?"down":"")}${detailKpi("AI event score",`${Number(s.aiEventScore||0)>0?"+":""}${Math.round(Number(s.aiEventScore||0))}/100`)}</div><div class="analysis-list" style="margin-top:9px">${rows.map(x=>`<div class="analysis-item ${x.direction==="BENEFICIARY"?"good":"bad"}"><b>${x.event}</b><br>${x.mechanism||"Event exposure identified."}${x.counterCase?`<br><span class="small">Devil’s advocate: ${x.counterCase}</span>`:""}</div>`).join("")}</div><div class="trend-source">AI event reasoning is capped at ±5 recommendation points and is tracked separately from deterministic market/fundamental scores.</div>`}\n'''
    s=s.replace(marker,fn+marker,1)

render='$("#detailAIEvents").innerHTML=aiEventHtml(s);'
if render not in s:
    old='$("#detailGlobalTrend").innerHTML=globalTrendHtml(s);'
    if old in s:
        s=s.replace(old,old+render,1)
    else:
        anchor='$("#detailEvidence").innerHTML='
        pos=s.find(anchor)
        if pos<0: raise SystemExit('detail render anchor not found')
        s=s[:pos]+render+s[pos:]

p.write_text(s)
print('AI event reasoning UI integrated')
