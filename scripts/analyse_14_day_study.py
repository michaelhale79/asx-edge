import datetime as dt
import gzip
import json
from collections import defaultdict
from pathlib import Path

SNAP_DIR=Path('study/market_snapshots')
OUT=Path('study/14-day-analysis.json')
START=dt.date(2026,8,31)
END=dt.date(2026,9,14)

def n(v,default=0.0):
    try:return float(v)
    except:return default

def pct(a,b): return ((a/b)-1)*100 if b else 0

def load():
    snaps=[]
    for p in sorted(SNAP_DIR.glob('*.json.gz')):
        try:
            with gzip.open(p,'rt',encoding='utf-8') as f: snaps.append(json.load(f))
        except Exception as e: print('skip',p,e)
    return snaps

def signal_summary(rows):
    defs={
      'highMomentum':lambda r:n(r.get('momentum'))>=65,
      'strongRelative1m':lambda r:n(r.get('relative1m'))>=5,
      'strongRelative3m':lambda r:n(r.get('relative3m'))>=8,
      'highVolume':lambda r:n(r.get('volumeRatio'),1)>=1.25,
      'lowRisk':lambda r:n(r.get('risk'),100)<50,
      'highConfidence':lambda r:n(r.get('confidence'))>=65,
      'highOpportunity':lambda r:n(r.get('opp'))>=65,
    }
    out={}
    for name,test in defs.items():
        vals=[]
        for r in rows:
            if test(r) and 'forwardReturnPct' in r: vals.append(r['forwardReturnPct'])
        out[name]={'samples':len(vals),'avgForwardReturnPct':round(sum(vals)/len(vals),2) if vals else None,'winRatePct':round(sum(v>0 for v in vals)/len(vals)*100,1) if vals else None}
    return out

def main():
    snaps=load(); by=defaultdict(list)
    for snap in snaps:
        captured=snap.get('capturedAt')
        for s in snap.get('stocks',[]):
            row=dict(s); row['capturedAt']=captured; by[str(s.get('ticker','')).upper()].append(row)
    companies=[]; observation_rows=[]
    for ticker,rows in by.items():
        rows=sorted(rows,key=lambda x:x.get('capturedAt',''))
        if len(rows)<2: continue
        first,last=rows[0],rows[-1]; start=n(first.get('price')); end=n(last.get('price'))
        ret=pct(end,start); prices=[n(x.get('price')) for x in rows if n(x.get('price'))>0]
        max_gain=max((pct(p,start) for p in prices),default=ret); min_ret=min((pct(p,start) for p in prices),default=ret)
        ever_selected=any(bool(x.get('selected')) for x in rows); best_score=max(n(x.get('opp')) for x in rows)
        companies.append({'ticker':ticker,'name':last.get('name') or first.get('name') or ticker,'firstPrice':round(start,4),'lastPrice':round(end,4),'periodReturnPct':round(ret,2),'maxGainPct':round(max_gain,2),'maxDrawdownFromStartPct':round(min_ret,2),'firstOpportunity':round(n(first.get('opp'))),'maxOpportunity':round(best_score),'everSelected':ever_selected,'observations':len(rows)})
        latest_price=end
        for r in rows[:-1]:
            rr=dict(r); rr['forwardReturnPct']=round(pct(latest_price,n(r.get('price'))),2) if n(r.get('price')) else 0; observation_rows.append(rr)
    companies.sort(key=lambda x:x['periodReturnPct'],reverse=True)
    missed=[x for x in companies if not x['everSelected'] and (x['periodReturnPct']>=8 or x['maxGainPct']>=10)]
    false_pos=[x for x in companies if x['everSelected'] and x['periodReturnPct']<=-5]
    weak_misses=[x for x in companies if x['periodReturnPct']>=8 and x['firstOpportunity']<55]
    today=dt.datetime.now(dt.timezone.utc).date(); elapsed=max(0,(min(today,END)-START).days); remaining=max(0,(END-today).days)
    payload={'studyStart':START.isoformat(),'studyEnd':END.isoformat(),'status':'COMPLETE' if today>=END else 'COLLECTING','calendarDaysElapsed':elapsed,'calendarDaysRemaining':remaining,'snapshotCount':len(snaps),'companiesObserved':len(companies),'topMovers':companies[:30],'largestDecliners':sorted(companies,key=lambda x:x['periodReturnPct'])[:20],'missedOpportunities':missed[:30],'selectedButWeak':false_pos[:30],'lowScoreWinners':weak_misses[:30],'signalDiagnostics':signal_summary(observation_rows),'interpretation':{'missedOpportunities':'Stocks that rose strongly during the study despite never being surfaced as a selected whole-ASX candidate.','selectedButWeak':'Surfaced stocks that subsequently fell at least 5% across the available study window.','lowScoreWinners':'Strong movers whose initial opportunity score was below the normal surface threshold; these are especially useful for finding missing signals.'},'updated':dt.datetime.now(dt.timezone.utc).isoformat()}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print('snapshots',len(snaps),'companies',len(companies),'missed',len(missed))

if __name__=='__main__': main()
