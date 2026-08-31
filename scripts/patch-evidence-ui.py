from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Add a dedicated evidence panel before the announcement list.
needle='<div class="panel"><div class="panel-title">Recent ASX announcements</div><div id="detailAnnouncements"></div></div>'
repl='<div class="panel"><div class="panel-title">Company disclosure evidence</div><div id="detailEvidence"></div></div>'+needle
if 'id="detailEvidence"' not in s:
    if needle not in s: raise SystemExit('detail evidence insertion point not found')
    s=s.replace(needle,repl,1)

# Best Opportunity: reward strong source-document evidence and management delivery,
# while penalising disclosure risk.
old='shortAdj=Number(x.shortAdjustment||0),stretch=Math.max(0,r1-25)*.7+Math.max(0,r3-45)*.35;return (opp+learnedSignalAdjustment(x))*.32+val*.12+conf*.13+(100-risk)*.10+fund*.18+(100-frisk)*.10+Math.max(-15,Math.min(15,rel))*.20+Math.max(-12,Math.min(12,ann))*.15+shortAdj*.30-stretch'
new='shortAdj=Number(x.shortAdjustment||0),ev=Number(x.evidenceScore??50),er=Number(x.evidenceRisk??50),md=Number(x.managementDeliveryScore??50),stretch=Math.max(0,r1-25)*.7+Math.max(0,r3-45)*.35;return (opp+learnedSignalAdjustment(x))*.30+val*.11+conf*.12+(100-risk)*.09+fund*.16+(100-frisk)*.09+ev*.08+(100-er)*.05+md*.03+Math.max(-15,Math.min(15,rel))*.18+Math.max(-12,Math.min(12,ann))*.13+shortAdj*.25-stretch'
if old in s: s=s.replace(old,new,1)

# Decision rationale: include source-document positives and negatives.
old='if(isFinite(fcf)&&fcf<0)risk.push(`free cash flow is negative`);if(isFinite(shorts)&&shorts>=8)risk.push(`short interest is high at ${shorts.toFixed(1)}%`);'
new='if(isFinite(fcf)&&fcf<0)risk.push(`free cash flow is negative`);const ev=Number(s.evidenceScore),er=Number(s.evidenceRisk),md=Number(s.managementDeliveryScore);if(isFinite(ev)&&ev>=65)parts.push(`company disclosure evidence is strong at ${Math.round(ev)}/100`);if(isFinite(md)&&md>=65)parts.push(`management delivery evidence scores ${Math.round(md)}/100`);for(const x of (s.evidencePositives||[]).slice(0,2))parts.push(String(x));if(isFinite(er)&&er>=60)risk.push(`company disclosure risk is elevated at ${Math.round(er)}/100`);for(const f of (s.evidenceFlags||[]).slice(0,2))risk.push(String(f&&f.text||f));if(isFinite(shorts)&&shorts>=8)risk.push(`short interest is high at ${shorts.toFixed(1)}%`);'
if old in s: s=s.replace(old,new,1)

# Company analysis cards: make evidence readable as bull/risk/watch items.
old='for(const f of (s.riskFlags||[])){(f.severity==="HIGH"?bad:watch).push(`Fundamental risk: ${f.text}`)}if(isFinite(Number(s.fundamentalScore))&&Number(s.fundamentalScore)>=65)good.push(`Fundamental score is ${Math.round(Number(s.fundamentalScore))}/100, supported by profitability, growth, cash flow, balance sheet, dilution and valuation.`);'
new='for(const f of (s.riskFlags||[])){(f.severity==="HIGH"?bad:watch).push(`Fundamental risk: ${f.text}`)}for(const x of (s.evidencePositives||[]).slice(0,3))good.push(`Disclosure evidence: ${x}`);for(const f of (s.evidenceFlags||[]).slice(0,3)){(f.severity==="HIGH"?bad:watch).push(`Disclosure risk: ${f.text||f}`)}if(isFinite(Number(s.fundamentalScore))&&Number(s.fundamentalScore)>=65)good.push(`Fundamental score is ${Math.round(Number(s.fundamentalScore))}/100, supported by profitability, growth, cash flow, balance sheet, dilution and valuation.`);'
if old in s: s=s.replace(old,new,1)

# Add disclosure KPIs to the snapshot.
old='detailKpi("Forward P/E",isFinite(Number(s.forwardPE))?`${Number(s.forwardPE).toFixed(1)}×`:isFinite(Number(s.trailingPE))?`${Number(s.trailingPE).toFixed(1)}× trailing`:"—"),detailKpi("Long-term score",isFinite(Number(s.longTermScore))?`${Math.round(Number(s.longTermScore))}/100 · ${s.playType||""}`:"Pending")'
new='detailKpi("Forward P/E",isFinite(Number(s.forwardPE))?`${Number(s.forwardPE).toFixed(1)}×`:isFinite(Number(s.trailingPE))?`${Number(s.trailingPE).toFixed(1)}× trailing`:"—"),detailKpi("Disclosure evidence",isFinite(Number(s.evidenceScore))?`${Math.round(Number(s.evidenceScore))}/100`:"Pending"),detailKpi("Disclosure risk",isFinite(Number(s.evidenceRisk))?`${Math.round(Number(s.evidenceRisk))}/100`:"Pending"),detailKpi("Management delivery",isFinite(Number(s.managementDeliveryScore))?`${Math.round(Number(s.managementDeliveryScore))}/100`:"Pending"),detailKpi("Documents read",isFinite(Number(s.documentsRead))?String(Number(s.documentsRead)):"Pending"),detailKpi("Long-term score",isFinite(Number(s.longTermScore))?`${Math.round(Number(s.longTermScore))}/100 · ${s.playType||""}`:"Pending")'
if old in s: s=s.replace(old,new,1)

# Render evidence summary, sector-specific excerpts and source document names.
old='$("#detailRisk").textContent=s.riskText||"No risk summary available.";const anns=Array.isArray(s.announcements)?s.announcements:[];'
new='$("#detailRisk").textContent=s.riskText||"No risk summary available.";const sev=Array.isArray(s.sectorEvidence)?s.sectorEvidence:[],edocs=Array.isArray(s.evidenceDocuments)?s.evidenceDocuments:[];$("#detailEvidence").innerHTML=`<div class="analysis-item ${Number(s.evidenceRisk)>=60?"bad":Number(s.evidenceScore)>=65?"good":"watch"}">${s.evidenceSummary||"Disclosure-document analysis is pending for this company."}</div>${sev.slice(0,5).map(x=>`<div class="announcement"><div class="announcement-date">${String(x.metric||"sector evidence").toUpperCase()}</div><div class="announcement-title">${x.evidence||""}</div></div>`).join("")}${edocs.slice(0,4).map(x=>`<div class="announcement"><div class="announcement-date">SOURCE · ${x.date||""}</div><div class="announcement-title">${x.headline||"ASX disclosure"}${x.error?` · could not read: ${x.error}`:""}</div></div>`).join("")}`;const anns=Array.isArray(s.announcements)?s.announcements:[];'
if old in s: s=s.replace(old,new,1)

# Score anatomy now shows the independent evidence layer.
old='["Global trend",Number(s.globalTrendScore||0)],["Learned adj.",learnedSignalAdjustment(s)]]'
new='["Global trend",Number(s.globalTrendScore||0)],["Disclosure",Number(s.evidenceScore??50)],["Disclosure safety",100-Number(s.evidenceRisk??50)],["Mgmt delivery",Number(s.managementDeliveryScore??50)],["Learned adj.",learnedSignalAdjustment(s)]]'
if old in s: s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
print('Evidence UI patch applied')
