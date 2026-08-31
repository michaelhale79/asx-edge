from pathlib import Path
p=Path('scripts/decision_intelligence.py')
s=p.read_text()

s=s.replace("['strengthened its balance sheet','strengthening of the company’s funding base','strengthening of the company\\'s funding base','fully funded','funding runway','financial resources','paid off its','reduced debt','oversubscribed placement']", "['strengthened its balance sheet','strengthening of the company’s funding base','strengthening of the company\\'s funding base','fully funded','funding runway','financial resources','paid off its','reduced debt','oversubscribed placement','successful capital raising','cash on hand','leading global specialist','funding base','runway extending']")

old="""    strategy=(deep or {}).get('strategySummary') or stock.get('description') or f\"Monitor {stock.get('ticker')} strategy and execution.\"
    themes=list((deep or {}).get('strategicThemes') or [])
"""
new="""    strategy=(deep or {}).get('strategySummary') or stock.get('description') or f\"Monitor {stock.get('ticker')} strategy and execution.\"
    themes=list((deep or {}).get('strategicThemes') or [])
    all_evidence=' '.join(str(x) for vals in (rec.get('evidenceSignals') or {}).values() for x in (vals or [])).lower()
    if 'no clear strategic direction' in strategy.lower() or strategy.startswith('Monitor '):
        if any(k in all_evidence for k in ['clinical','registrational','phase 1','phase 2','phase 3','patient','trial']):
            strategy='Advance the clinical pipeline through key trial and registrational milestones while preserving enough funding runway to reach value-creating readouts.'
            if not themes: themes=['Clinical development / approvals']
        elif any(k in all_evidence for k in ['resource','drilling','ore body','mine life','production guidance','first ore']):
            strategy='Grow and de-risk the resource/project base, progress development milestones and convert exploration or project work into sustainable production and cash flow.'
            if not themes: themes=['Resources / development']
        elif any(k in all_evidence for k in ['annual recurring revenue','arr','subscriber','recurring revenue','retention']):
            strategy='Grow recurring revenue and customer adoption while improving the durability and cash economics of the business model.'
            if not themes: themes=['Recurring revenue / scale']
"""
if old not in s: raise SystemExit('strategy anchor missing')
s=s.replace(old,new,1)

old2="""    milestones=[]
    for c in commitments[:4]: milestones.append(re.sub(r'\\s+',' ',c)[:260])
    if not milestones:
        for e in (rec.get('sectorEvidence') or [])[:4]: milestones.append(str(e.get('metric','')).replace('_',' ').title()+': '+str(e.get('evidence',''))[:220])
"""
new2="""    milestones=[]
    for c in commitments[:4]: milestones.append(re.sub(r'\\s+',' ',c)[:260])
    if not milestones:
        milestones=catalysts[:4]
    if not milestones and themes:
        milestones=['Evidence that management is progressing '+', '.join(themes[:2])+' against the next disclosed timetable.']
"""
if old2 not in s: raise SystemExit('milestone anchor missing')
s=s.replace(old2,new2,1)

p.write_text(s)
print('refined structured thesis strategy, funding context and milestones')
