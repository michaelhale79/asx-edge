#!/usr/bin/env python3
import json, math
from pathlib import Path
from datetime import datetime, timezone

DATA=Path('data.json')
OUT=Path('recommendations.json')
NOW=datetime.now(timezone.utc)
THRESHOLD=75


def n(v,d=0):
    try:
        x=float(v)
        return x if math.isfinite(x) else d
    except Exception:
        return d


def recommendation(s):
    # s['opp'] already contains deterministic backend market/short/global adjustments.
    # AI event reasoning is kept as a separate, capped overlay so its performance can
    # be measured independently rather than silently buried in the base score.
    opp=n(s.get('opp'))
    ai=n(s.get('aiEventAdjustment'))
    adjusted=opp+ai
    risk=n(s.get('risk'))
    conf=n(s.get('confidence'),50)
    ann=n(s.get('announcementSignal'))
    delta=n(s.get('delta'))
    shorts=n(s.get('shortInterestPct'),-1)
    fund=n(s.get('fundamentalScore'),50)
    frisk=n(s.get('fundamentalRisk'),50)
    erisk=n(s.get('qualityEvidenceRisk'),n(s.get('evidenceRisk'),50))
    mgmt=n(s.get('managementCredibilityScore'),n(s.get('managementDeliveryScore'),50))
    if ann <= -15 or opp < 40 or risk >= 75 or delta <= -12 or frisk >= 80 or erisk >= 80:
        return 'SELL',14
    if adjusted >= THRESHOLD and risk < 50 and ann >= 0 and conf >= 55 and not (shorts >= 8) and fund >= 45 and frisk < 65 and erisk < 65 and mgmt >= 35:
        return 'BUY',30
    return 'HOLD',20


def signals(s):
    return {
        'momentum': n(s.get('momentum')) >= 65,
        'relativeStrength': n(s.get('relative1m')) >= 5 or n(s.get('relative3m')) >= 8,
        'announcements': n(s.get('announcementSignal')) >= 10,
        'globalTrend': n(s.get('globalTrendScore')) >= 12,
        'aiEvent': n(s.get('aiEventAdjustment')) >= 2,
        'lowShorts': (0 <= n(s.get('shortInterestPct'),-1) <= 2),
        'value': n(s.get('valuation'),50) >= 60,
        'volume': n(s.get('volumeRatio')) >= 1.25,
    }


def outcome(call, price):
    start=n(call.get('startPrice'))
    if start <= 0: return None
    days=(NOW-datetime.fromisoformat(call['startDate'].replace('Z','+00:00'))).days
    ret=(price/start-1)*100
    due=days >= int(call.get('horizon',20))
    label=call.get('label')
    result='TRACKING'
    if due:
        if label=='BUY': result='SUCCESS' if ret>0 else 'FAIL'
        elif label=='SELL': result='SUCCESS' if ret<0 else 'FAIL'
        else: result='SUCCESS' if abs(ret)<5 else 'MIXED'
    return {'days':days,'returnPct':round(ret,2),'due':due,'outcome':result}


def main():
    data=json.loads(DATA.read_text())
    old={'calls':{},'completed':[]}
    if OUT.exists():
        try: old=json.loads(OUT.read_text())
        except Exception: pass
    calls=old.get('calls') or {}
    completed=old.get('completed') or []
    completed_ids={x.get('id') for x in completed}

    for s in data.get('stocks',[]):
        t=s.get('ticker')
        if not t: continue
        label,horizon=recommendation(s)
        price=n(s.get('price'))
        cur=calls.get(t)
        if cur and cur.get('label') != label:
            ev=outcome(cur,price)
            cid=cur.get('id')
            if cid and cid not in completed_ids:
                completed.append({**cur,'endDate':NOW.isoformat(),'endPrice':price,**(ev or {})})
                completed_ids.add(cid)
            cur=None
        if not cur:
            cur={
                'id':f"{t}-{NOW.strftime('%Y%m%dT%H%M%SZ')}",
                'ticker':t,'label':label,'startPrice':price,'startDate':NOW.isoformat(),
                'horizon':horizon,'opportunity':round(n(s.get('opp')),1),
                'aiEventAdjustment':round(n(s.get('aiEventAdjustment')),1),
                'risk':round(n(s.get('risk')),1),'confidence':round(n(s.get('confidence'),50),1),
                'signals':signals(s),
                'snapshot':{
                    'relative1m':n(s.get('relative1m')),'relative3m':n(s.get('relative3m')),
                    'momentum':n(s.get('momentum')),'valuation':n(s.get('valuation'),50),
                    'announcementSignal':n(s.get('announcementSignal')),
                    'globalTrendScore':n(s.get('globalTrendScore')),
                    'aiEventAdjustment':n(s.get('aiEventAdjustment')),
                    'aiEventScore':n(s.get('aiEventScore')),
                    'shortInterestPct':s.get('shortInterestPct'),
                    'volumeRatio':n(s.get('volumeRatio')),
                }
            }
        ev=outcome(cur,price)
        cur['currentPrice']=price
        if ev: cur.update(ev)
        calls[t]=cur

    resolved=[x for x in completed if x.get('outcome') in ('SUCCESS','FAIL','MIXED')]
    buy_res=[x for x in resolved if x.get('label')=='BUY' and x.get('outcome') in ('SUCCESS','FAIL')]
    overall=(sum(1 for x in buy_res if x['outcome']=='SUCCESS')/len(buy_res)) if buy_res else 0
    diagnostics={}; adjustments={}
    keys=['momentum','relativeStrength','announcements','globalTrend','aiEvent','lowShorts','value','volume']
    for k in keys:
        rows=[x for x in buy_res if (x.get('signals') or {}).get(k)]
        succ=sum(1 for x in rows if x.get('outcome')=='SUCCESS')
        rate=(succ/len(rows)) if rows else None
        diagnostics[k]={'sample':len(rows),'successRate':round(rate*100,1) if rate is not None else None}
        adj=0
        if len(buy_res)>=12 and len(rows)>=6 and rate is not None:
            adj=round(max(-2,min(2,(rate-overall)*10)))
        adjustments[k]=adj

    summary={}
    for lab in ('BUY','HOLD','SELL'):
        rows=[x for x in resolved if x.get('label')==lab]
        decisive=[x for x in rows if x.get('outcome') in ('SUCCESS','FAIL')]
        summary[lab]={
            'completed':len(rows),
            'successRate':round(100*sum(1 for x in decisive if x.get('outcome')=='SUCCESS')/len(decisive),1) if decisive else None,
            'averageReturnPct':round(sum(n(x.get('returnPct')) for x in rows)/len(rows),2) if rows else None,
        }

    result={
        'version':2,'updated':NOW.isoformat(),'threshold':THRESHOLD,
        'scoringNote':'Deterministic opportunity is the base score. AI world-event reasoning is a separate capped +/-5 overlay and is tracked as its own signal.',
        'calls':calls,'completed':completed[-1000:],
        'summary':summary,
        'engineLearning':{
            'completedBuyCalls':len(buy_res),
            'active':len(buy_res)>=12,
            'overallBuySuccessRate':round(overall*100,1) if buy_res else None,
            'signalDiagnostics':diagnostics,
            'signalAdjustments':adjustments,
            'maxTotalAdjustment':5,
            'method':'Only completed BUY calls are used. Learning activates after 12 completed BUY calls; each signal, including AI event hypotheses, needs at least 6 observations and is capped at +/-2 learned points.'
        }
    }
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(f"Tracked {len(calls)} active calls; {len(resolved)} completed outcomes; learning active={result['engineLearning']['active']}")

if __name__=='__main__': main()
