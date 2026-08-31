import datetime as dt
import hashlib
import json
import re
from pathlib import Path

DATA = Path('data.json')
EVIDENCE = Path('study/company-evidence.json')
DEEP = Path('study/deep-research.json')
HISTORY = Path('study/management-history.json')
AUDIT = Path('study/evidence-quality-audit.json')
THESIS = Path('study/investment-theses.json')

CORE_AUDIT = ['DPM','QML','PYC','DRO','CSL','MIN','WBT']


def n(v, default=0.0):
    try: return float(v)
    except Exception: return default

def clamp(x, lo=0, hi=100): return max(lo, min(hi, x))

def snippets(rec, key): return list((rec.get('evidenceSignals') or {}).get(key) or [])

def boilerplate(s):
    x=s.lower()
    risk_words=['uncertainties','risks inherent','risk factors','may be subject','could adversely','possibility that','forward-looking','cannot assure','no assurance','speculative nature','risks arising','risks related','delays in obtaining','subject to unforeseen delays']
    actual_words=['has been delayed','was delayed','is delayed','suspended operations','production suspended','shutdown occurred','terminated the contract','missed guidance','guidance withdrawn','guidance reduced','cost overrun']
    return any(k in x for k in risk_words) and not any(k in x for k in actual_words)

def real_execution_negative(items):
    out=[]
    for s in items:
        x=s.lower()
        accounting_deferred=any(k in x for k in ['deferred share unit','deferred tax','tax deferred','deferred revenue','deferred consideration'])
        successful_planned_shutdown=('planned shutdown' in x and any(k in x for k in ['completed','ahead of schedule','on schedule']))
        if accounting_deferred or successful_planned_shutdown or boilerplate(s):
            continue
        out.append(s)
    return out

def real_cash_burn(items):
    out=[]
    for s in items:
        x=s.lower()
        positive_runway = ('runway' in x and any(k in x for k in ['extend','into 20','funded through','cash on hand','financial resources','fully funded']))
        actual = any(k in x for k in ['cash burn','negative operating cash flow','net cash outflow','funding shortfall','liquidity shortfall'])
        if actual and not positive_runway: out.append(s)
    return out

def supportive_raise(items):
    good=[]; other=[]
    for s in items:
        x=s.lower()
        if any(k in x for k in ['strengthened its balance sheet','strengthening of the company’s funding base','strengthening of the company\'s funding base','fully funded','funding runway','financial resources','paid off its','reduced debt','oversubscribed placement']): good.append(s)
        else: other.append(s)
    return good,other

def quality_evidence(stock, rec):
    sig=rec.get('evidenceSignals') or {}
    pos=[]; flags=[]; corrections=[]; score=50; risk=30
    def add(v,t):
        nonlocal score; score+=v; pos.append(t)
    def sub(sv,rv,t,severity='MEDIUM'):
        nonlocal score,risk; score-=sv; risk+=rv; flags.append({'severity':severity,'text':t})

    if sig.get('guidance_raise'): add(12,'Management has raised or beaten guidance.')
    elif sig.get('guidance_reaffirm'): add(6,'Management has reaffirmed or maintained guidance.')
    if sig.get('guidance_cut'): sub(16,18,'Guidance has been cut, withdrawn or missed.','HIGH')
    if sig.get('contract_win'): add(8,'Recent disclosures contain contract/customer wins.')
    if sig.get('contract_loss'): sub(13,15,'Recent disclosures contain contract/customer loss or termination.','HIGH')
    if sig.get('execution_positive'): add(8,'Recent disclosures show milestones or execution being delivered.')

    raw_neg=snippets(rec,'execution_negative'); clean_neg=real_execution_negative(raw_neg)
    if raw_neg and len(clean_neg)<len(raw_neg): corrections.append('Removed non-operating deferred/accounting language, successful planned shutdowns, or generic forward-looking risk boilerplate from execution-delay detection.')
    if clean_neg: sub(8,9,'Current disclosures contain actual delay, deferral or operating interruption language.')

    raises=snippets(rec,'capital_raise'); good_raise,bad_raise=supportive_raise(raises)
    if good_raise:
        add(2,'Recent funding strengthened liquidity/balance sheet, although dilution still matters.')
        risk+=3
        corrections.append('Capital raising treated as funding-strengthening rather than automatic funding distress where the document explicitly supports that interpretation.')
    if bad_raise: sub(8,10,'Recent capital raising/share issuance creates dilution or funding-dependence risk.')

    if sig.get('options_issue'): sub(4,5,'Options, performance rights or convertibles may add future dilution.','LOW')
    if sig.get('debt_refi_positive'): add(5,'Refinancing/facility evidence supports liquidity.')
    if sig.get('debt_stress'): sub(18,22,'Debt, covenant, going-concern or liquidity stress is disclosed.','HIGH')

    raw_burn=snippets(rec,'cash_burn'); clean_burn=real_cash_burn(raw_burn)
    if raw_burn and not clean_burn: corrections.append('Removed positive cash-runway wording from cash-burn risk detection.')
    if clean_burn and n(stock.get('freeCashflow'))<0: sub(8,10,'Disclosure evidence reinforces actual negative cash-flow/cash-burn risk.')

    if sig.get('capex_overrun'): sub(12,14,'Project/capital costs are rising beyond plan.','HIGH')
    if sig.get('major_customer'):
        risk+=6; flags.append({'severity':'MEDIUM','text':'Customer concentration requires monitoring.'})

    return {
        'qualityEvidenceScore':round(clamp(score)),
        'qualityEvidenceRisk':round(clamp(risk)),
        'qualityEvidencePositives':pos,
        'qualityEvidenceFlags':flags,
        'evidenceCorrections':corrections,
        'cleanSignals':{
            'execution_negative':clean_neg,
            'cash_burn':clean_burn,
            'supportive_capital_raise':good_raise,
            'dilutive_capital_raise':bad_raise,
        }
    }

def fingerprint(ticker, kind, text):
    return hashlib.sha1((ticker+'|'+kind+'|'+re.sub(r'\s+',' ',text.lower())[:500]).encode()).hexdigest()[:16]

def commitment_snippets(rec):
    pool=[]
    for key in ['execution_positive','execution_negative','guidance_raise','guidance_reaffirm','guidance_cut','capex','contract_win']:
        pool += snippets(rec,key)
    out=[]
    for s in pool:
        x=s.lower()
        if any(k in x for k in ['expects','expected to','anticipates','target','planned','plan to','scheduled','on track','guidance','will ','intends','commence','complete','ramp-up','ramp up']):
            out.append(s)
    return out[:8]

def management_score(rec, quality, prior):
    sig=rec.get('evidenceSignals') or {}
    delivered=(1 if sig.get('guidance_raise') else 0)+(1 if sig.get('guidance_reaffirm') else 0)+(1 if sig.get('execution_positive') else 0)+(1 if sig.get('contract_win') else 0)
    missed=(1 if sig.get('guidance_cut') else 0)+(1 if quality['cleanSignals']['execution_negative'] else 0)+(1 if sig.get('contract_loss') else 0)+(1 if sig.get('capex_overrun') else 0)+(1 if sig.get('debt_stress') else 0)
    score=clamp(50 + delivered*8 - missed*12)
    old_scores=[x.get('score') for x in (prior.get('snapshots') or []) if isinstance(x.get('score'),(int,float))]
    if old_scores: score=round(score*.7 + old_scores[-1]*.3)
    return round(score),delivered,missed

def build_thesis(stock, deep, rec, q, mgmt):
    strategy=(deep or {}).get('strategySummary') or stock.get('description') or f"Monitor {stock.get('ticker')} strategy and execution."
    themes=list((deep or {}).get('strategicThemes') or [])
    world=list((deep or {}).get('worldThemes') or stock.get('globalThemes') or [])
    play=(deep or {}).get('playType') or stock.get('playType') or 'WATCH'
    short=n((deep or {}).get('shortTermScore'),n(stock.get('shortTermScore'),50))
    long=n((deep or {}).get('longTermScore'),n(stock.get('longTermScore'),50))
    commitments=commitment_snippets(rec)

    must=[]
    if themes: must.append('Management must execute the current strategic focus: '+', '.join(themes[:3])+'.')
    if commitments: must.append('The current announced timetable/guidance must be delivered without material slippage.')
    if n(stock.get('freeCashflow'))<0: must.append('Cash burn must remain funded without value-destructive repeated dilution.')
    if n(stock.get('netDebt'))>0: must.append('Debt and liquidity must remain manageable as the strategy is funded.')
    if not must: must.append('Operating performance must continue to justify the current opportunity score.')

    catalysts=[]
    for a in ((deep or {}).get('recentAnnouncements') or []):
        h=a.get('headline','')
        if any(k in h.lower() for k in ['production','contract','resource','results','approval','trial','guidance','commercial','upgrade','drilling','acquisition','launch']): catalysts.append(h)
        if len(catalysts)>=4: break
    if not catalysts and commitments: catalysts=['Delivery against the current disclosed milestones and guidance.']

    funding=[]
    good_raise=q['cleanSignals']['supportive_capital_raise']
    bad_raise=q['cleanSignals']['dilutive_capital_raise']
    if good_raise: funding.append('Recent funding appears to have strengthened the balance sheet/liquidity, but dilution should still be monitored.')
    if bad_raise: funding.append('Recent raising activity suggests continuing funding/dilution risk.')
    if n(stock.get('cashRunwayMonths'))>0: funding.append(f"Estimated cash runway: {n(stock.get('cashRunwayMonths')):.0f} months.")
    if n(stock.get('netDebt'))>0: funding.append('Net debt is present; refinancing and covenant headroom remain part of the thesis.')
    if not funding: funding.append('No immediate funding warning is identified from the current evidence set; continue monitoring cash flow and debt.')

    drivers=[]
    if world: drivers.append('Global/sector themes: '+', '.join([str(x) for x in world[:3]])+'.')
    if n(stock.get('revenueGrowth'))>0: drivers.append(f"Revenue growth is currently positive ({n(stock.get('revenueGrowth')):.1f}%).")
    if n(stock.get('freeCashflow'))>0: drivers.append('Positive free cash flow supports longer-term durability.')
    if themes: drivers.append('Successful execution of '+', '.join(themes[:2])+' could extend the opportunity beyond a short-term trade.')

    risks=[f.get('text') for f in q.get('qualityEvidenceFlags',[])[:4]]
    for f in (stock.get('fundamentalRiskFlags') or []):
        txt=f.get('text') if isinstance(f,dict) else str(f)
        if txt and txt not in risks: risks.append(txt)
        if len(risks)>=6: break
    if not risks: risks=['The thesis can still fail if operating performance, valuation or market conditions deteriorate.']

    breaks=[]
    if commitments: breaks.append('A material miss or delay against the current disclosed milestones/guidance.')
    breaks.append('A guidance downgrade, unexpected liquidity stress or materially worse balance sheet.')
    if good_raise or bad_raise or n(stock.get('freeCashflow'))<0: breaks.append('Another value-destructive capital raise without a corresponding improvement in per-share value or funded growth.')
    if long>=65: breaks.append('Long-term score falls below 55 after refreshed financial and disclosure evidence.')
    else: breaks.append('The evidence fails to improve enough to lift the long-term score above the current watch/short-term range.')

    milestones=[]
    for c in commitments[:4]: milestones.append(re.sub(r'\s+',' ',c)[:260])
    if not milestones:
        for e in (rec.get('sectorEvidence') or [])[:4]: milestones.append(str(e.get('metric','')).replace('_',' ').title()+': '+str(e.get('evidence',''))[:220])

    return {
        'objective':strategy,
        'playType':play,
        'shortTermScore':round(short),
        'longTermScore':round(long),
        'managementCredibilityScore':mgmt,
        'evidenceQualityScore':q['qualityEvidenceScore'],
        'whatMustGoRight':must,
        'keyMilestones':milestones,
        'nearTermCatalysts':catalysts,
        'fundingAssessment':funding,
        'longTermDrivers':drivers or ['Long-term durability still needs stronger evidence.'],
        'keyRisks':risks,
        'thesisBreaks':breaks,
        'reviewRule':'Reassess on any material ASX announcement, guidance change, capital raising, major contract/project milestone, or scheduled ASX Edge refresh.',
    }

def main():
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    data=json.loads(DATA.read_text())
    ev=json.loads(EVIDENCE.read_text())
    deep=json.loads(DEEP.read_text()) if DEEP.exists() else {'companies':[]}
    hist=json.loads(HISTORY.read_text()) if HISTORY.exists() else {'companies':{}}
    hist.setdefault('companies',{})
    stocks={str(s.get('ticker','')).upper():s for s in data.get('stocks',[])}
    deeps={str(s.get('ticker','')).upper():s for s in deep.get('companies',[])}
    audit=[]; theses=[]

    for rec in ev.get('companies',[]):
        t=str(rec.get('ticker','')).upper(); stock=stocks.get(t)
        if not stock or rec.get('status')!='OK': continue
        q=quality_evidence(stock,rec)
        prior=hist['companies'].setdefault(t,{'commitments':[],'snapshots':[]})
        mgmt,delivered,missed=management_score(rec,q,prior)

        existing_ids={x.get('id') for x in prior.get('commitments',[])}
        for text in commitment_snippets(rec):
            cid=fingerprint(t,'commitment',text)
            if cid not in existing_ids:
                prior['commitments'].append({'id':cid,'firstSeen':now,'text':re.sub(r'\s+',' ',text)[:600],'status':'OPEN'})
                existing_ids.add(cid)
        # Match current delivery/miss language against open commitments using meaningful token overlap.
        pos_text=' '.join(snippets(rec,'execution_positive')+snippets(rec,'guidance_raise')+snippets(rec,'guidance_reaffirm')).lower()
        neg_text=' '.join(q['cleanSignals']['execution_negative']+snippets(rec,'guidance_cut')+snippets(rec,'contract_loss')).lower()
        stop={'the','and','for','with','from','that','this','will','into','has','have','was','were','are','our','its','company','project'}
        for c in prior['commitments']:
            if c.get('status')!='OPEN': continue
            toks=[x for x in re.findall(r'[a-z]{4,}',c.get('text','').lower()) if x not in stop]
            toks=toks[:20]
            p=sum(1 for x in toks if x in pos_text); m=sum(1 for x in toks if x in neg_text)
            if p>=3 and p>m: c.update({'status':'DELIVERED','resolvedAt':now})
            elif m>=3 and m>p: c.update({'status':'MISSED','resolvedAt':now})
        snapshot={'at':now,'score':mgmt,'deliveredSignals':delivered,'missedSignals':missed,'openCommitments':sum(1 for x in prior['commitments'] if x.get('status')=='OPEN')}
        if not prior.get('snapshots') or prior['snapshots'][-1].get('score')!=snapshot['score'] or prior['snapshots'][-1].get('openCommitments')!=snapshot['openCommitments']:
            prior['snapshots'].append(snapshot)
            prior['snapshots']=prior['snapshots'][-60:]

        for k,v in q.items(): stock[k]=v
        stock['managementCredibilityScore']=mgmt
        stock['managementDeliveredSignals']=delivered
        stock['managementMissedSignals']=missed
        stock['managementOpenCommitments']=snapshot['openCommitments']
        thesis=build_thesis(stock,deeps.get(t),rec,q,mgmt)
        stock['investmentThesis']=thesis
        theses.append({'ticker':t,'name':stock.get('name'),'thesis':thesis})

        if t in CORE_AUDIT:
            audit.append({
                'ticker':t,'documentsRead':rec.get('documentsRead',0),
                'rawEvidenceScore':rec.get('evidenceScore'),'rawEvidenceRisk':rec.get('evidenceRisk'),
                'qualityEvidenceScore':q['qualityEvidenceScore'],'qualityEvidenceRisk':q['qualityEvidenceRisk'],
                'corrections':q['evidenceCorrections'],
                'managementCredibilityScore':mgmt,
                'assessment':'PASS_WITH_CORRECTIONS' if q['evidenceCorrections'] else 'PASS',
            })

    hist['updated']=now
    HISTORY.write_text(json.dumps(hist,indent=2))
    AUDIT.write_text(json.dumps({'updated':now,'purpose':'Quality audit of actual ASX disclosure interpretation on a mixed company set. Raw scores are retained; quality-adjusted scores filter boilerplate and context errors.','companies':audit},indent=2))
    THESIS.write_text(json.dumps({'updated':now,'method':'Structured thesis generated from market setup, fundamentals, actual ASX disclosure evidence, management delivery history and strategic/global context.','companies':theses},indent=2))
    data['decisionIntelligenceUpdated']=now
    data['evidenceQualityAudit']='ACTIVE'
    data['managementCredibilityTracking']='ACTIVE'
    data['structuredThesisEngine']='ACTIVE'
    DATA.write_text(json.dumps(data,indent=2))
    print('Audited',len(audit),'companies; built',len(theses),'structured theses')

if __name__=='__main__': main()
