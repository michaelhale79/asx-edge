from pathlib import Path
p=Path('index.html')
s=p.read_text()

# Add structured thesis panel.
old='<div class="panel"><div class="panel-title">Company disclosure evidence</div><div id="detailEvidence"></div></div><div class="panel"><div class="panel-title">Recent ASX announcements</div>'
new='<div class="panel"><div class="panel-title">Company disclosure evidence</div><div id="detailEvidence"></div></div><div class="panel"><div class="panel-title">Investment thesis & management</div><div id="detailInvestmentThesis"></div></div><div class="panel"><div class="panel-title">Recent ASX announcements</div>'
if old not in s: raise SystemExit('detail panel anchor not found')
s=s.replace(old,new,1)

# Use the quality-adjusted evidence/management layer in Best Opportunity.
s=s.replace('ev=Number(x.evidenceScore??50),er=Number(x.evidenceRisk??50),md=Number(x.managementDeliveryScore??50)', 'ev=Number(x.qualityEvidenceScore??x.evidenceScore??50),er=Number(x.qualityEvidenceRisk??x.evidenceRisk??50),md=Number(x.managementCredibilityScore??x.managementDeliveryScore??50)')
s=s.replace('const ev=Number(s.evidenceScore),er=Number(s.evidenceRisk),md=Number(s.managementDeliveryScore);', 'const ev=Number(s.qualityEvidenceScore??s.evidenceScore),er=Number(s.qualityEvidenceRisk??s.evidenceRisk),md=Number(s.managementCredibilityScore??s.managementDeliveryScore);')

# Add sensible fundamental/evidence gates to BUY/SELL without allowing these layers to create a BUY alone.
old='const threshold=Number($("#threshold")?.value||75),sh=shortSignal(s),opp=Number(s.opp||0),risk=Number(s.risk||0),conf=Number(s.confidence??50),ann=Number(s.announcementSignal||0),delta=Number(s.delta||0),learn=learnedSignalAdjustment(s),adjusted=opp+learn;'
new='const threshold=Number($("#threshold")?.value||75),sh=shortSignal(s),opp=Number(s.opp||0),risk=Number(s.risk||0),conf=Number(s.confidence??50),ann=Number(s.announcementSignal||0),delta=Number(s.delta||0),fund=Number(s.fundamentalScore??50),frisk=Number(s.fundamentalRisk??50),evRisk=Number(s.qualityEvidenceRisk??s.evidenceRisk??50),mgmt=Number(s.managementCredibilityScore??s.managementDeliveryScore??50),learn=learnedSignalAdjustment(s),adjusted=opp+learn;'
if old not in s: raise SystemExit('recommendation vars anchor not found')
s=s.replace(old,new,1)
s=s.replace('if(ann<=-15||opp<40||risk>=75||delta<=-12)return', 'if(ann<=-15||opp<40||risk>=75||delta<=-12||frisk>=80||evRisk>=80)return',1)
s=s.replace('if(adjusted>=threshold&&risk<50&&ann>=0&&conf>=55&&sh.score>-10)return', 'if(adjusted>=threshold&&risk<50&&ann>=0&&conf>=55&&sh.score>-10&&fund>=45&&frisk<65&&evRisk<65&&mgmt>=35)return',1)

helper=r'''function structuredThesisHtml(s){const t=s.investmentThesis||{};if(!Object.keys(t).length)return `<div class="empty">Structured thesis is still being built for this company.</div>`;const list=(title,items,cls="")=>Array.isArray(items)&&items.length?`<div class="analysis-item ${cls}"><b>${title}</b><br>${items.map(x=>`• ${x}`).join("<br>")}</div>`:"";return `<div class="detail-kpis">${detailKpi("Play type",t.playType||"WATCH")}${detailKpi("Management",isFinite(Number(s.managementCredibilityScore))?`${Math.round(Number(s.managementCredibilityScore))}/100`:"—")}${detailKpi("Evidence quality",isFinite(Number(s.qualityEvidenceScore))?`${Math.round(Number(s.qualityEvidenceScore))}/100`:"—")}${detailKpi("Open commitments",String(s.managementOpenCommitments??"—"))}</div><div class="analysis-list" style="margin-top:8px"><div class="analysis-item"><b>What the company is trying to achieve</b><br>${t.objective||"—"}</div>${list("What must go right",t.whatMustGoRight,"good")}${list("Key milestones",t.keyMilestones)}${list("Near-term catalysts",t.nearTermCatalysts,"good")}${list("Funding assessment",t.fundingAssessment)}${list("Long-term drivers",t.longTermDrivers,"good")}${list("Key risks",t.keyRisks,"bad")}${list("Thesis breaks if",t.thesisBreaks,"bad")}<div class="analysis-item watch"><b>Review rule</b><br>${t.reviewRule||"Reassess on material new information."}</div></div>`}
'''
anchor='function openDetail(t){const s=stockOf(t);if(!s)return;'
if anchor not in s: raise SystemExit('openDetail anchor not found')
s=s.replace(anchor,helper+anchor+'$("#detailInvestmentThesis").innerHTML=structuredThesisHtml(s);',1)

p.write_text(s)
print('patched decision intelligence into phone UI and recommendation gates')
