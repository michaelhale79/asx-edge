from pathlib import Path
p=Path('scripts/decision_intelligence.py')
s=p.read_text()
old="""def commitment_snippets(rec):
    pool=[]
    for key in ['execution_positive','execution_negative','guidance_raise','guidance_reaffirm','guidance_cut','capex','contract_win']:
        pool += snippets(rec,key)
    out=[]
    for s in pool:
        x=s.lower()
        if any(k in x for k in ['expects','expected to','anticipates','target','planned','plan to','scheduled','on track','guidance','will ','intends','commence','complete','ramp-up','ramp up']):
            out.append(s)
    return out[:8]
"""
new="""def commitment_snippets(rec):
    pool=[]
    for key in ['execution_positive','guidance_raise','guidance_reaffirm','capex','contract_win']:
        pool += snippets(rec,key)
    out=[]
    future_patterns=[r'\\bexpects?\\b',r'expected to',r'\\banticipates?\\b',r'\\btarget(?:ed|s)? for\\b',r'\\bplanned for\\b',r'\\bscheduled for\\b',r'\\bon track (?:for|to)\\b',r'\\bguidance\\b',r'\\bwill\\b',r'\\bintends? to\\b',r'\\bforecast\\b',r'\\bby fy\\d{2}\\b',r'\\bin fy\\d{2}\\b',r'ramp[- ]up to']
    for text in pool:
        x=text.lower()
        if boilerplate(text):
            continue
        if any(re.search(pat,x) for pat in future_patterns):
            out.append(text)
    return out[:8]
"""
if old not in s: raise SystemExit('commitment function anchor not found')
s=s.replace(old,new)
old2="""        # Match current delivery/miss language against open commitments using meaningful token overlap.
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
"""
new2="""        # A promise must never be resolved by the same evidence set that first created it.
        # Repair any same-run resolutions from early versions, then only assess a promise
        # when an ASX document dated AFTER the commitment was first observed exists.
        for c in prior['commitments']:
            if c.get('resolvedAt')==c.get('firstSeen'):
                c['status']='OPEN'; c.pop('resolvedAt',None)
            if boilerplate(c.get('text','')):
                c['status']='IGNORED'; c.pop('resolvedAt',None)
        pos_text=' '.join(snippets(rec,'execution_positive')+snippets(rec,'guidance_raise')+snippets(rec,'guidance_reaffirm')).lower()
        neg_text=' '.join(q['cleanSignals']['execution_negative']+snippets(rec,'guidance_cut')+snippets(rec,'contract_loss')).lower()
        latest_doc=max([d.get('date','') for d in (rec.get('evidenceDocuments') or []) if d.get('date')],default='')
        stop={'the','and','for','with','from','that','this','will','into','has','have','was','were','are','our','its','company','project'}
        for c in prior['commitments']:
            if c.get('status')!='OPEN': continue
            first_day=str(c.get('firstSeen',''))[:10]
            if not latest_doc or latest_doc<=first_day:
                continue
            toks=[x for x in re.findall(r'[a-z]{4,}',c.get('text','').lower()) if x not in stop][:20]
            p=sum(1 for x in toks if x in pos_text); m=sum(1 for x in toks if x in neg_text)
            if p>=4 and p>m+1: c.update({'status':'DELIVERED','resolvedAt':now,'resolutionDocumentDate':latest_doc})
            elif m>=4 and m>p+1: c.update({'status':'MISSED','resolvedAt':now,'resolutionDocumentDate':latest_doc})
"""
if old2 not in s: raise SystemExit('management resolution anchor not found')
s=s.replace(old2,new2)
p.write_text(s)
print('refined management commitment timing and resolution')
