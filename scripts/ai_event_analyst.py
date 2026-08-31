#!/usr/bin/env python3
import datetime as dt
import hashlib
import json
import math
import os
import re
import urllib.request
from pathlib import Path

DATA=Path('data.json')
OUT=Path('study/ai-event-analysis.json')
HISTORY=Path('study/event-hypotheses.json')
MODEL=os.getenv('ASX_EDGE_AI_MODEL','gpt-5.4-mini')
API_KEY=os.getenv('OPENAI_API_KEY','').strip()
NOW=dt.datetime.now(dt.timezone.utc)


def n(v,d=0.0):
    try:
        x=float(v); return x if math.isfinite(x) else d
    except Exception: return d

def clamp(x,lo,hi): return max(lo,min(hi,x))
def norm(s): return re.sub(r'\s+',' ',str(s or '')).strip()

def universe(stocks):
    # Give the model a broad but compact ASX universe. Objective data remains the
    # source of truth; the model is asked to reason about causal exposure, not invent metrics.
    rows=[]
    for s in sorted(stocks,key=lambda x:n(x.get('opp')),reverse=True)[:180]:
        rows.append({
            'ticker':s.get('ticker'),'name':s.get('name'),'sector':s.get('sector'),'industry':s.get('industry'),
            'description':norm(s.get('description'))[:260],
            'opportunity':round(n(s.get('opp')),1),'risk':round(n(s.get('risk')),1),
            'confidence':round(n(s.get('confidence'),50),1),'fundamentalScore':round(n(s.get('fundamentalScore'),50),1),
            'fundamentalRisk':round(n(s.get('fundamentalRisk'),50),1),'managementCredibility':round(n(s.get('managementCredibilityScore'),50),1),
            'freeCashflowPositive':n(s.get('freeCashflow'))>0,'netDebtPositive':n(s.get('netDebt'))>0,
            'revenueGrowthPct':s.get('revenueGrowthPct'),'shortInterestPct':s.get('shortInterestPct'),
        })
    return rows

EVENT_SCHEMA={
 'type':'object','additionalProperties':False,
 'properties':{
   'asOf':{'type':'string'},
   'events':{'type':'array','maxItems':7,'items':{
     'type':'object','additionalProperties':False,
     'properties':{
       'event':{'type':'string'},'eventType':{'type':'string'},'location':{'type':'string'},
       'confidence':{'type':'integer','minimum':0,'maximum':100},
       'timeHorizon':{'type':'string','enum':['DAYS','WEEKS','MONTHS','YEARS','MIXED']},
       'whyItMatters':{'type':'string'},
       'causalChain':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':8},
       'primaryEffects':{'type':'array','items':{'type':'string'},'maxItems':6},
       'secondOrderEffects':{'type':'array','items':{'type':'string'},'maxItems':8},
       'sources':{'type':'array','maxItems':5,'items':{'type':'object','additionalProperties':False,'properties':{'title':{'type':'string'},'url':{'type':'string'},'publisher':{'type':'string'}},'required':['title','url','publisher']}},
       'candidates':{'type':'array','maxItems':12,'items':{'type':'object','additionalProperties':False,'properties':{
          'ticker':{'type':'string'},'direction':{'type':'string','enum':['BENEFICIARY','LOSER']},
          'impactScore':{'type':'integer','minimum':-100,'maximum':100},'confidence':{'type':'integer','minimum':0,'maximum':100},
          'horizon':{'type':'string','enum':['DAYS','WEEKS','MONTHS','YEARS','MIXED']},
          'mechanism':{'type':'string'},'whyThisCompany':{'type':'string'},'whatMustBeTrue':{'type':'array','items':{'type':'string'},'maxItems':5},
          'invalidation':{'type':'array','items':{'type':'string'},'maxItems':5}
       },'required':['ticker','direction','impactScore','confidence','horizon','mechanism','whyThisCompany','whatMustBeTrue','invalidation']}}
     },'required':['event','eventType','location','confidence','timeHorizon','whyItMatters','causalChain','primaryEffects','secondOrderEffects','sources','candidates']
   }}
 },'required':['asOf','events']
}

CRITIC_SCHEMA={
 'type':'object','additionalProperties':False,
 'properties':{'events':{'type':'array','maxItems':7,'items':{
   'type':'object','additionalProperties':False,'properties':{
     'event':{'type':'string'},'verdict':{'type':'string','enum':['KEEP','DOWNGRADE','REJECT']},
     'confidence':{'type':'integer','minimum':0,'maximum':100},'devilsAdvocate':{'type':'array','items':{'type':'string'},'maxItems':6},
     'candidates':{'type':'array','maxItems':10,'items':{'type':'object','additionalProperties':False,'properties':{
       'ticker':{'type':'string'},'keep':{'type':'boolean'},'direction':{'type':'string','enum':['BENEFICIARY','LOSER']},
       'impactScore':{'type':'integer','minimum':-100,'maximum':100},'confidence':{'type':'integer','minimum':0,'maximum':100},
       'reason':{'type':'string'},'counterCase':{'type':'string'}
     },'required':['ticker','keep','direction','impactScore','confidence','reason','counterCase']}}
   },'required':['event','verdict','confidence','devilsAdvocate','candidates']
 }}},'required':['events']
}

def api_response(instructions,input_text,schema,name,use_web=False):
    if not API_KEY: raise RuntimeError('OPENAI_API_KEY is not configured')
    body={
      'model':MODEL,'store':False,'instructions':instructions,'input':input_text,
      'text':{'format':{'type':'json_schema','name':name,'strict':True,'schema':schema}},
      'reasoning':{'effort':'medium'},
    }
    if use_web: body['tools']=[{'type':'web_search'}]
    req=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps(body).encode(),headers={
      'Authorization':'Bearer '+API_KEY,'Content-Type':'application/json','User-Agent':'ASXEdge/AIEventAnalyst'
    },method='POST')
    with urllib.request.urlopen(req,timeout=240) as r: payload=json.loads(r.read())
    text=payload.get('output_text')
    if not text:
        chunks=[]
        for item in payload.get('output',[]):
            for c in item.get('content',[]) if isinstance(item,dict) else []:
                if c.get('type')=='output_text': chunks.append(c.get('text',''))
        text=''.join(chunks)
    if not text: raise RuntimeError('OpenAI response contained no structured output')
    return json.loads(text),{'responseId':payload.get('id'),'model':payload.get('model'),'usage':payload.get('usage')}

def event_prompt(rows,trend):
    return json.dumps({'currentDate':NOW.date().isoformat(),'asxUniverse':rows,'existingFlatTrendSensor':trend},separators=(',',':'))

def merge(primary,critic,stocks):
    stockmap={str(s.get('ticker','')).upper():s for s in stocks}
    cmap={e['event']:e for e in critic.get('events',[])}
    final=[]
    for e in primary.get('events',[]):
        c=cmap.get(e.get('event'),{})
        if c.get('verdict')=='REJECT': continue
        candidates=[]
        crows={str(x.get('ticker','')).upper():x for x in c.get('candidates',[])}
        for p in e.get('candidates',[]):
            t=str(p.get('ticker','')).upper(); cr=crows.get(t,{})
            if t not in stockmap or cr.get('keep') is False: continue
            item=dict(p)
            if cr:
                item['impactScore']=cr.get('impactScore',item['impactScore']); item['confidence']=cr.get('confidence',item['confidence'])
                item['criticReason']=cr.get('reason',''); item['counterCase']=cr.get('counterCase','')
            candidates.append(item)
        if not candidates: continue
        item=dict(e); item['confidence']=c.get('confidence',e.get('confidence',50)); item['devilsAdvocate']=c.get('devilsAdvocate',[]); item['candidates']=candidates
        final.append(item)
    return final

def hid(event,ticker,direction):
    x=(norm(event).lower()+'|'+ticker+'|'+direction).encode(); return hashlib.sha1(x).hexdigest()[:18]

def update_history(events,stocks):
    prices={str(s.get('ticker','')).upper():n(s.get('price')) for s in stocks}
    old={'active':[],'archive':[]}
    if HISTORY.exists():
        try: old=json.loads(HISTORY.read_text())
        except Exception: pass
    active={x.get('id'):x for x in old.get('active',[]) if x.get('id')}
    for e in events:
        for c in e.get('candidates',[]):
            t=str(c.get('ticker','')).upper(); i=hid(e.get('event'),t,c.get('direction'))
            if i not in active:
                active[i]={'id':i,'event':e.get('event'),'ticker':t,'direction':c.get('direction'),'startDate':NOW.isoformat(),'startPrice':prices.get(t,0),'horizon':c.get('horizon'),'initialImpactScore':c.get('impactScore'),'initialConfidence':c.get('confidence'),'thesis':c.get('mechanism'),'whatMustBeTrue':c.get('whatMustBeTrue',[]),'invalidation':c.get('invalidation',[]),'status':'ACTIVE'}
    for h in active.values():
        p=prices.get(h.get('ticker'),0); start=n(h.get('startPrice'))
        h['currentPrice']=p; h['currentReturnPct']=round((p/start-1)*100,2) if p and start else None; h['lastChecked']=NOW.isoformat()
        try: days=(NOW-dt.datetime.fromisoformat(str(h['startDate']).replace('Z','+00:00'))).days
        except Exception: days=0
        h['daysElapsed']=days
        target={'DAYS':7,'WEEKS':28,'MONTHS':90,'YEARS':365,'MIXED':90}.get(h.get('horizon'),30)
        h['reviewDue']=days>=target
    payload={'updated':NOW.isoformat(),'active':list(active.values()),'archive':old.get('archive',[])}
    HISTORY.parent.mkdir(parents=True,exist_ok=True); HISTORY.write_text(json.dumps(payload,indent=2))
    return payload

def apply(events,stocks):
    by={}
    for e in events:
        for c in e.get('candidates',[]):
            t=str(c.get('ticker','')).upper(); sign=1 if c.get('direction')=='BENEFICIARY' else -1
            raw=abs(n(c.get('impactScore')))*n(c.get('confidence'))/100*n(e.get('confidence'))/100*sign
            by.setdefault(t,[]).append((raw,e,c))
    for s in stocks:
        t=str(s.get('ticker','')).upper(); rows=by.get(t,[])
        # AI is influential but cannot overwhelm objective market/fundamental evidence.
        net=sum(x[0] for x in rows); adj=round(clamp(net/20,-5,5)) if rows else 0
        s['aiEventAdjustment']=adj; s['aiEventScore']=round(clamp(net,-100,100)) if rows else 0
        s['aiEventSignal']='BULLISH' if adj>=2 else 'BEARISH' if adj<=-2 else 'NEUTRAL'
        s['aiEventReasons']=[{'event':e.get('event'),'direction':c.get('direction'),'confidence':c.get('confidence'),'mechanism':c.get('mechanism'),'counterCase':c.get('counterCase','')} for _,e,c in sorted(rows,key=lambda z:abs(z[0]),reverse=True)[:4]]

def main():
    data=json.loads(DATA.read_text()); stocks=data.get('stocks',[]); rows=universe(stocks)
    if not API_KEY:
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps({'updated':NOW.isoformat(),'status':'NEEDS_API_KEY','message':'Add repository secret OPENAI_API_KEY to activate the AI Event Analyst. No AI score has been applied.'},indent=2))
        print('OPENAI_API_KEY not configured; wrote setup status without changing stock scores')
        return
    flat=(data.get('globalTrendThemes') or [])[:10]
    instructions=(
      'You are the ASX Edge Event Analyst. Search the current web for genuinely important world AND Australian events from the last 72 hours that could change listed-company economics. '
      'Reason causally: event -> commodity/rates/demand/supply/regulation/logistics -> first-order effects -> second-order effects -> specific ASX businesses. Do not rely on ticker keywords. '
      'Only nominate tickers present in the supplied ASX universe. Separate short-lived trading effects from structural effects. Prefer economic exposure over narrative association. '
      'Every event needs credible current sources. Do not manufacture facts or company exposure; lower confidence when evidence is weak.'
    )
    primary,meta1=api_response(instructions,event_prompt(rows,flat),EVENT_SCHEMA,'asx_event_analysis',True)
    critic_in={'asxUniverse':rows,'proposedAnalysis':primary}
    critic_inst=(
      'You are the independent devil’s advocate for an ASX event-driven investment engine. Challenge each proposed causal chain and company mapping. '
      'Reject superficial ticker associations, already-priced narratives, companies without meaningful economic exposure, and claims contradicted by the supplied company metrics. '
      'Downgrade confidence when timing, balance-sheet capacity, hedging, funding, valuation, or second-order effects weaken the thesis. Preserve only defensible hypotheses.'
    )
    critic,meta2=api_response(critic_inst,json.dumps(critic_in,separators=(',',':')),CRITIC_SCHEMA,'asx_event_critic',False)
    events=merge(primary,critic,stocks); apply(events,stocks); hist=update_history(events,stocks)
    result={'updated':NOW.isoformat(),'status':'ACTIVE','model':MODEL,'method':'AI Event Analyst web-search pass + independent devil’s-advocate pass + deterministic ASX/fundamental overlay.','events':events,'hypothesesActive':len(hist.get('active',[])),'api':{'analyst':meta1,'critic':meta2}}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,indent=2))
    data['stocks']=stocks; data['aiEventUpdated']=NOW.isoformat(); data['aiEventStatus']='ACTIVE'; data['aiEventModel']=MODEL; data['aiEventCount']=len(events); DATA.write_text(json.dumps(data,indent=2))
    print('AI events',len(events),'active hypotheses',len(hist.get('active',[])))

if __name__=='__main__': main()
