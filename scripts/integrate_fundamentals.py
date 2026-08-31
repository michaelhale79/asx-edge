from pathlib import Path

# Deep research: make long-term classification fundamentally grounded.
p=Path('scripts/deep_research.py'); s=p.read_text(encoding='utf-8')
s=s.replace('''    r6=n(stock.get("return6m")); r12=n(stock.get("return12m"))
    short_term=clamp(opp*.26+momentum*.20+catalyst*.17+conf*.10+(100-risk)*.08+clamp(50+rel1*2)*.07+clamp(50+(volume-1)*25)*.05+clamp(50+ann)*.04+clamp(50+gt)*.03)
    durable_trend=clamp(50+r6*.35+r12*.18+rel3*.45)
    strategic_bonus=min(8,len(intents)*2)
    long_term=clamp(quality*.24+growth*.20+value*.15+conf*.14+(100-risk)*.14+durable_trend*.08+clamp(50+gt)*.05+strategic_bonus)
''','''    r6=n(stock.get("return6m")); r12=n(stock.get("return12m"))
    fundamental=n(stock.get("fundamentalScore"),50); fundamental_risk=n(stock.get("fundamentalRisk"),50)
    balance=n(stock.get("balanceSheetScore"),50); cashflow=n(stock.get("cashflowScore"),50); dilution=n(stock.get("dilutionScore"),50)
    short_term=clamp(opp*.24+momentum*.19+catalyst*.16+conf*.10+(100-risk)*.08+clamp(50+rel1*2)*.07+clamp(50+(volume-1)*25)*.05+clamp(50+ann)*.04+clamp(50+gt)*.03+fundamental*.02+(100-fundamental_risk)*.02)
    durable_trend=clamp(50+r6*.35+r12*.18+rel3*.45)
    strategic_bonus=min(7,len(intents)*1.75)
    long_term=clamp(fundamental*.28+balance*.10+cashflow*.08+dilution*.06+quality*.10+growth*.08+value*.08+conf*.08+(100-fundamental_risk)*.07+(100-risk)*.03+durable_trend*.02+clamp(50+gt)*.02+strategic_bonus)
''')
p.write_text(s,encoding='utf-8')

# UI: expose financial strength, debt/dilution risk and use them in opportunity reasoning.
p=Path('index.html'); h=p.read_text(encoding='utf-8')
old='''const score=x=>{const opp=Number(x.opp||0),val=Number(x.valuation??50),conf=Number(x.confidence??50),risk=Number(x.risk||0),r1=Number(x.return1m||0),r3=Number(x.return3m||0),rel=Number(x.relative3m||0),ann=Number(x.announcementSignal||0),shortAdj=Number(x.shortAdjustment||0),stretch=Math.max(0,r1-25)*.7+Math.max(0,r3-45)*.35;return (opp+learnedSignalAdjustment(x))*.42+val*.18+conf*.18+(100-risk)*.14+Math.max(-15,Math.min(15,rel))*.25+Math.max(-12,Math.min(12,ann))*.2+shortAdj*.45-stretch}'''
new='''const score=x=>{const opp=Number(x.opp||0),val=Number(x.valuation??50),conf=Number(x.confidence??50),risk=Number(x.risk||0),fund=Number(x.fundamentalScore??50),frisk=Number(x.fundamentalRisk??50),r1=Number(x.return1m||0),r3=Number(x.return3m||0),rel=Number(x.relative3m||0),ann=Number(x.announcementSignal||0),shortAdj=Number(x.shortAdjustment||0),stretch=Math.max(0,r1-25)*.7+Math.max(0,r3-45)*.35;return (opp+learnedSignalAdjustment(x))*.32+val*.12+conf*.13+(100-risk)*.10+fund*.18+(100-frisk)*.10+Math.max(-15,Math.min(15,rel))*.20+Math.max(-12,Math.min(12,ann))*.15+shortAdj*.30-stretch}'''
if old not in h: raise SystemExit('best opportunity scoring anchor missing')
h=h.replace(old,new,1)

old='''if(val>=60)parts.push(`valuation score is attractive at ${Math.round(val)}/100`);if(isFinite(shorts)&&shorts<=2)parts.push(`short interest is low at ${shorts.toFixed(1)}%`);'''
new='''if(val>=60)parts.push(`valuation score is attractive at ${Math.round(val)}/100`);const fund=Number(s.fundamentalScore),frisk=Number(s.fundamentalRisk),dil=Number(s.annualDilutionPct),de=Number(s.debtToEquityPct),fcf=Number(s.freeCashflow);if(isFinite(fund)&&fund>=65)parts.push(`fundamental quality is strong at ${Math.round(fund)}/100`);if(isFinite(frisk)&&frisk<=35)parts.push(`balance-sheet/fundamental risk is low at ${Math.round(frisk)}/100`);if(isFinite(dil)&&dil<=2)parts.push(`share dilution is contained at ${dil.toFixed(1)}%`);if(isFinite(shorts)&&shorts<=2)parts.push(`short interest is low at ${shorts.toFixed(1)}%`);'''
if old not in h: raise SystemExit('decision positive anchor missing')
h=h.replace(old,new,1)
old='''if(riskScore>=55)risk.push(`risk is elevated at ${Math.round(riskScore)}/100`);if(isFinite(shorts)&&shorts>=8)risk.push(`short interest is high at ${shorts.toFixed(1)}%`);'''
new='''if(riskScore>=55)risk.push(`market risk is elevated at ${Math.round(riskScore)}/100`);if(isFinite(frisk)&&frisk>=60)risk.push(`fundamental/balance-sheet risk is elevated at ${Math.round(frisk)}/100`);if(isFinite(dil)&&dil>=7)risk.push(`annual share dilution is ${dil.toFixed(1)}%`);if(isFinite(de)&&de>=100)risk.push(`debt-to-equity is high at ${de.toFixed(0)}%`);if(isFinite(fcf)&&fcf<0)risk.push(`free cash flow is negative`);if(isFinite(shorts)&&shorts>=8)risk.push(`short interest is high at ${shorts.toFixed(1)}%`);'''
if old not in h: raise SystemExit('decision risk anchor missing')
h=h.replace(old,new,1)

old='''detailKpi("Confidence",`${Math.round(Number(s.confidence||0))}/100`),detailKpi("Short interest",isFinite(Number(s.shortInterestPct))?`${Number(s.shortInterestPct).toFixed(1)}%`:"N/A")].join("")'''
new='''detailKpi("Confidence",`${Math.round(Number(s.confidence||0))}/100`),detailKpi("Short interest",isFinite(Number(s.shortInterestPct))?`${Number(s.shortInterestPct).toFixed(1)}%`:"N/A"),detailKpi("Fundamentals",isFinite(Number(s.fundamentalScore))?`${Math.round(Number(s.fundamentalScore))}/100`:"Pending"),detailKpi("Fundamental risk",isFinite(Number(s.fundamentalRisk))?`${Math.round(Number(s.fundamentalRisk))}/100`:"Pending"),detailKpi("Revenue growth",isFinite(Number(s.revenueGrowthPct))?`${Number(s.revenueGrowthPct).toFixed(1)}%`:"—",Number(s.revenueGrowthPct)>=0?"up":"down"),detailKpi("Profit margin",isFinite(Number(s.profitMarginPct))?`${Number(s.profitMarginPct).toFixed(1)}%`:"—",Number(s.profitMarginPct)>=0?"up":"down"),detailKpi("Free cash flow",isFinite(Number(s.freeCashflow))?money(Number(s.freeCashflow)):"—",Number(s.freeCashflow)>=0?"up":"down"),detailKpi("Net cash / debt",isFinite(Number(s.netCash))?`${Number(s.netCash)>=0?"Cash ":"Debt "}${money(Math.abs(Number(s.netCash)))}`:"—",Number(s.netCash)>=0?"up":"down"),detailKpi("Debt / equity",isFinite(Number(s.debtToEquityPct))?`${Number(s.debtToEquityPct).toFixed(0)}%`:"—"),detailKpi("Annual dilution",isFinite(Number(s.annualDilutionPct))?`${Number(s.annualDilutionPct).toFixed(1)}%`:"—",Number(s.annualDilutionPct)<=3?"up":Number(s.annualDilutionPct)>=8?"down":""),detailKpi("Forward P/E",isFinite(Number(s.forwardPE))?`${Number(s.forwardPE).toFixed(1)}×`:isFinite(Number(s.trailingPE))?`${Number(s.trailingPE).toFixed(1)}× trailing`:"—"),detailKpi("Long-term score",isFinite(Number(s.longTermScore))?`${Math.round(Number(s.longTermScore))}/100 · ${s.playType||""}`:"Pending")].join("")'''
if old not in h: raise SystemExit('snapshot anchor missing')
h=h.replace(old,new,1)

old='''if(gt<=-12)bad.push(`Global-news themes are currently a headwind with a score of ${Math.round(gt)}.`);if(!good.length)watch.push'''
new='''if(gt<=-12)bad.push(`Global-news themes are currently a headwind with a score of ${Math.round(gt)}.`);for(const f of (s.riskFlags||[])){(f.severity==="HIGH"?bad:watch).push(`Fundamental risk: ${f.text}`)}if(isFinite(Number(s.fundamentalScore))&&Number(s.fundamentalScore)>=65)good.push(`Fundamental score is ${Math.round(Number(s.fundamentalScore))}/100, supported by profitability, growth, cash flow, balance sheet, dilution and valuation.`);if(!good.length)watch.push'''
if old not in h: raise SystemExit('analysis anchor missing')
h=h.replace(old,new,1)

p.write_text(h,encoding='utf-8')
print('fundamentals integrated into deep research and UI')
