import datetime as dt
import json
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

DATA_PATH = Path("data.json")
OUT_PATH = Path("study/deep-research.json")
MAX_RESEARCH = 60
LOOKBACK_DAYS = 120
HEADERS = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15"}

CORE = {"WBT","CSL","RIO","DMP","DRO","ETPMAG","GOLD","S32","DTL","WOR","MIN","AIA"}

INTENT_RULES = {
    "Expansion / capacity": ["expansion", "expand", "capacity", "new facility", "new plant", "commissioning", "production increase", "ramp-up", "ramp up"],
    "Customers / contracts": ["contract", "customer", "award", "awarded", "tender", "offtake", "sales agreement", "supply agreement"],
    "Technology / product": ["product", "technology", "platform", "launch", "prototype", "development milestone", "commercialisation", "commercialization"],
    "Resources / exploration": ["drilling", "exploration", "resource", "reserve", "discovery", "mineral", "ore", "feasibility", "study results"],
    "Acquisition / portfolio": ["acquisition", "acquire", "merger", "divest", "sale of", "strategic review", "joint venture"],
    "Approval / regulation": ["approval", "approved", "regulatory", "permit", "licence", "license", "fda", "tga"],
    "Funding / capital": ["capital raising", "placement", "entitlement", "funding", "debt facility", "refinancing"],
    "Efficiency / restructuring": ["cost reduction", "cost saving", "restructur", "transformation", "productivity", "efficiency"]
}

class AnnouncementParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_tr=False; self.in_td=False; self.row=[]; self.cell=""; self.price_sensitive=False; self.rows=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=="tr": self.in_tr=True; self.row=[]; self.price_sensitive=False
        elif tag=="td" and self.in_tr: self.in_td=True; self.cell=""
        elif tag=="img" and self.in_tr and "price sensitive" in attrs.get("alt","").lower(): self.price_sensitive=True
    def handle_data(self, data):
        if self.in_td: self.cell += data
    def handle_endtag(self, tag):
        if tag=="td" and self.in_td:
            self.row.append(" ".join(self.cell.split())); self.in_td=False; self.cell=""
        elif tag=="tr" and self.in_tr:
            if self.row: self.rows.append({"cells":self.row[:],"priceSensitive":self.price_sensitive})
            self.in_tr=False

def clamp(x, lo=0, hi=100): return max(lo,min(hi,x))
def n(v, default=0):
    try: return float(v)
    except: return default

def fetch_text(url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=25) as r: return r.read().decode("utf-8",errors="ignore")

def parse_date(text):
    m=re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})",text)
    if not m: return None
    try: return dt.date(int(m.group(3)),int(m.group(2)),int(m.group(1)))
    except: return None

def fetch_announcements(ticker):
    params=urllib.parse.urlencode({"asxCode":ticker[:3],"by":"asxCode","period":"M6","timeframe":"D"})
    url="https://www.asx.com.au/asx/v2/statistics/announcements.do?"+params
    try:
        p=AnnouncementParser(); p.feed(fetch_text(url)); cutoff=dt.date.today()-dt.timedelta(days=LOOKBACK_DAYS); out=[]
        for row in p.rows:
            cells=row["cells"]
            if len(cells)<2: continue
            d=parse_date(cells[0])
            if not d or d<cutoff: continue
            headline=cells[-1].strip()
            if headline: out.append({"date":d.isoformat(),"headline":headline,"priceSensitive":row["priceSensitive"]})
        return out[:30]
    except Exception as e:
        print("announcement research failed",ticker,e); return []

def infer_intent(announcements):
    scores={k:0 for k in INTENT_RULES}
    evidence={k:[] for k in INTENT_RULES}
    for a in announcements:
        h=a.get("headline","").lower()
        weight=2 if a.get("priceSensitive") else 1
        for label, phrases in INTENT_RULES.items():
            if any(p in h for p in phrases):
                scores[label]+=weight
                if len(evidence[label])<3: evidence[label].append(a.get("headline",""))
    ranked=[k for k,v in sorted(scores.items(),key=lambda x:x[1],reverse=True) if v>0]
    return ranked[:4], {k:evidence[k] for k in ranked[:4]}

def world_theme_names(stock):
    out=[]
    for item in stock.get("globalThemes",[]) or []:
        if isinstance(item,str): out.append(item)
        elif isinstance(item,dict): out.append(str(item.get("theme") or item.get("name") or item.get("label") or ""))
    return [x for x in out if x][:5]

def classify(stock, intents):
    opp=n(stock.get("opp")); momentum=n(stock.get("momentum"),50); catalyst=n(stock.get("catalystScore"),50)
    risk=n(stock.get("risk"),50); conf=n(stock.get("confidence"),50); quality=n(stock.get("quality"),50)
    growth=n(stock.get("growth"),50); value=n(stock.get("valuation"),50); rel1=n(stock.get("relative1m")); rel3=n(stock.get("relative3m"))
    volume=n(stock.get("volumeRatio"),1); ann=n(stock.get("announcementSignal")); gt=n(stock.get("globalTrendScore"))
    r6=n(stock.get("return6m")); r12=n(stock.get("return12m"))
    short_term=clamp(opp*.26+momentum*.20+catalyst*.17+conf*.10+(100-risk)*.08+clamp(50+rel1*2)*.07+clamp(50+(volume-1)*25)*.05+clamp(50+ann)*.04+clamp(50+gt)*.03)
    durable_trend=clamp(50+r6*.35+r12*.18+rel3*.45)
    strategic_bonus=min(8,len(intents)*2)
    long_term=clamp(quality*.24+growth*.20+value*.15+conf*.14+(100-risk)*.14+durable_trend*.08+clamp(50+gt)*.05+strategic_bonus)
    if long_term>=70 and short_term>=68: play="BOTH"
    elif long_term>=70: play="LONG_TERM"
    elif short_term>=70: play="SHORT_TERM"
    elif long_term>=62 and short_term>=60: play="WATCH_BOTH"
    else: play="WATCH"
    return round(short_term),round(long_term),play

def main():
    data=json.loads(DATA_PATH.read_text(encoding="utf-8")); stocks=data.get("stocks",[])
    ranked=sorted(stocks,key=lambda s:(n(s.get("opp")),n(s.get("confidence"))),reverse=True)
    picked=[]; seen=set()
    for s in ranked:
        t=str(s.get("ticker","")).upper()
        if not t or t in seen: continue
        if len(picked)<MAX_RESEARCH or t in CORE:
            picked.append(s); seen.add(t)
        if len(picked)>=MAX_RESEARCH and CORE.issubset(seen): break
    output=[]
    for i,s in enumerate(picked,1):
        t=str(s.get("ticker","")).upper(); anns=fetch_announcements(t); intents,evidence=infer_intent(anns); themes=world_theme_names(s)
        st,lt,play=classify(s,intents)
        strategy=("Recent announcements suggest focus on "+", ".join(intents)+"." if intents else "No clear strategic direction was detected from recent announcement headlines alone.")
        world=("Relevant world themes: "+", ".join(themes)+"." if themes else "No strong mapped global theme is currently attached to this company.")
        horizon_reason=f"Short-term score {st}/100 versus long-term score {lt}/100. {strategy} {world}"
        rec={"ticker":t,"name":s.get("name",t),"sector":s.get("sector"),"industry":s.get("industry"),"shortTermScore":st,"longTermScore":lt,"playType":play,"strategicThemes":intents,"strategicEvidence":evidence,"worldThemes":themes,"strategySummary":strategy,"worldContext":world,"horizonReason":horizon_reason,"researchedAt":dt.datetime.now(dt.timezone.utc).isoformat(),"recentAnnouncements":anns[:12]}
        output.append(rec)
        s.update({k:rec[k] for k in ["shortTermScore","longTermScore","playType","strategicThemes","strategySummary","worldContext","horizonReason"]})
        if anns: s["announcements"]=anns[:12]
        print(i,t,play,st,lt); time.sleep(.15)
    data["deepResearchUpdated"]=dt.datetime.now(dt.timezone.utc).isoformat(); DATA_PATH.write_text(json.dumps(data,indent=2),encoding="utf-8")
    OUT_PATH.parent.mkdir(parents=True,exist_ok=True); OUT_PATH.write_text(json.dumps({"updated":dt.datetime.now(dt.timezone.utc).isoformat(),"method":"Second-stage research on leading ASX Edge candidates: recent ASX announcement headlines + market/quality/risk metrics + mapped global themes. Classification is evidence-based but not a substitute for full fundamental due diligence.","companies":output},indent=2),encoding="utf-8")

if __name__=="__main__": main()
