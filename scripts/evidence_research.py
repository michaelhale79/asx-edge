import datetime as dt
import io
import json
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

from pypdf import PdfReader

DATA_PATH = Path("data.json")
OUT_PATH = Path("study/company-evidence.json")
MAX_COMPANIES = 40
LOOKBACK_DAYS = 240
MAX_DOCS_PER_COMPANY = 3
MAX_PDF_PAGES = 10
MAX_TEXT_CHARS = 45000
HEADERS = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15"}
CORE = {"WBT","CSL","RIO","DMP","DRO","ETPMAG","GOLD","S32","DTL","WOR","MIN","AIA"}

DOC_PRIORITY = [
    "annual report", "half year", "half-year", "results", "quarterly", "appendix 4c", "appendix 5b",
    "guidance", "investor presentation", "capital raising", "placement", "entitlement", "debt", "facility",
    "contract", "offtake", "customer", "production", "activities report", "cash flow"
]

RULES = {
    "capital_raise": [r"capital rais", r"placement", r"entitlement offer", r"rights issue", r"issue of .*shares", r"securities issued", r"share purchase plan"],
    "options_issue": [r"issue of .*options", r"options granted", r"performance rights", r"convertible note"],
    "guidance_raise": [r"guidance (?:has been )?(?:raised|upgraded|increased)", r"upgrade[sd]? .*guidance", r"ahead of guidance", r"exceed(?:ed|s)? guidance"],
    "guidance_reaffirm": [r"guidance (?:is |has been )?(?:reaffirmed|maintained|unchanged)", r"reaffirm(?:s|ed)? .*guidance"],
    "guidance_cut": [r"guidance (?:has been )?(?:reduced|lowered|downgraded|withdrawn|suspended)", r"downgrade[sd]? .*guidance", r"below guidance", r"miss(?:ed|es) guidance"],
    "debt_refi_positive": [r"refinanc(?:ed|ing).*facility", r"new debt facility", r"extended .*debt maturity", r"facility .*extended", r"undrawn .*facility"],
    "debt_stress": [r"covenant breach", r"waiver .*covenant", r"going concern", r"material uncertainty", r"debt matur(?:es|ity).*within", r"repayment due", r"liquidity constraint"],
    "cash_burn": [r"cash burn", r"net cash outflow", r"negative operating cash flow", r"funding runway", r"cash runway"],
    "capex": [r"capital expenditure", r"capex", r"development expenditure", r"construction cost", r"project cost"],
    "capex_overrun": [r"cost overrun", r"capital cost .*increase", r"project cost .*increase", r"capex .*increase", r"budget .*increase"],
    "major_customer": [r"largest customer", r"major customer", r"key customer", r"single customer", r"customer concentration", r"top customer"],
    "contract_win": [r"contract award", r"awarded .*contract", r"new contract", r"purchase order", r"offtake agreement", r"supply agreement"],
    "contract_loss": [r"contract termination", r"terminated .*contract", r"customer loss", r"non-renewal", r"cancelled .*contract", r"canceled .*contract"],
    "execution_positive": [r"ahead of schedule", r"on schedule", r"commissioning complete", r"commercial production", r"first production", r"milestone achieved", r"delivered on time"],
    "execution_negative": [r"delay(?:ed|s)?", r"defer(?:red|ral)", r"behind schedule", r"commissioning .*delay", r"production .*suspend", r"shutdown", r"cost overrun"],
}

SECTOR_RULES = {
    "resources": ["production", "a isc", "aisc", "cash cost", "resource", "reserve", "grade", "recovery", "capex", "production guidance"],
    "energy": ["production", "boe", "realised price", "unit cost", "reserve", "capex", "production guidance"],
    "technology": ["arr", "annual recurring revenue", "recurring revenue", "churn", "retention", "subscriber", "contracted revenue", "gross margin"],
    "health": ["clinical", "phase 1", "phase 2", "phase 3", "fda", "tga", "approval", "trial", "cash runway", "r&d"],
    "consumer": ["same store", "same-store", "store sales", "store openings", "network sales", "gross margin", "ebitda margin"],
    "industrials": ["order book", "backlog", "contract", "utilisation", "utilization", "ebitda margin", "capex"],
    "financials": ["net interest margin", "nim", "arrears", "bad debts", "capital ratio", "cet1", "funds under management"],
}

class AnnouncementParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_tr=False; self.in_td=False; self.row=[]; self.cell=""; self.price_sensitive=False; self.rows=[]; self.links=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=="tr": self.in_tr=True; self.row=[]; self.price_sensitive=False; self.links=[]
        elif tag=="td" and self.in_tr: self.in_td=True; self.cell=""
        elif tag=="img" and self.in_tr and "price sensitive" in attrs.get("alt","").lower(): self.price_sensitive=True
        elif tag=="a" and self.in_tr and attrs.get("href"): self.links.append(attrs.get("href"))
    def handle_data(self, data):
        if self.in_td: self.cell += data
    def handle_endtag(self, tag):
        if tag=="td" and self.in_td:
            self.row.append(" ".join(self.cell.split())); self.in_td=False; self.cell=""
        elif tag=="tr" and self.in_tr:
            if self.row: self.rows.append({"cells":self.row[:],"priceSensitive":self.price_sensitive,"links":self.links[:]})
            self.in_tr=False

def n(v, default=0):
    try: return float(v)
    except Exception: return default

def clamp(x, lo=0, hi=100): return max(lo,min(hi,x))

def fetch_bytes(url, timeout=25):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=timeout) as r: return r.read()

def fetch_text(url): return fetch_bytes(url).decode("utf-8",errors="ignore")

def parse_date(text):
    m=re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})",text)
    if not m: return None
    try: return dt.date(int(m.group(3)),int(m.group(2)),int(m.group(1)))
    except Exception: return None

def announcement_rows(ticker):
    params=urllib.parse.urlencode({"asxCode":ticker[:3],"by":"asxCode","period":"M6","timeframe":"D"})
    url="https://www.asx.com.au/asx/v2/statistics/announcements.do?"+params
    p=AnnouncementParser(); p.feed(fetch_text(url)); cutoff=dt.date.today()-dt.timedelta(days=LOOKBACK_DAYS); out=[]
    for row in p.rows:
        cells=row.get("cells") or []
        if len(cells)<2: continue
        d=parse_date(cells[0])
        if not d or d<cutoff: continue
        headline=cells[-1].strip()
        href=next((h for h in row.get("links",[]) if "displayannouncement.do" in h.lower() or "asxpdf" in h.lower() or h.lower().endswith(".pdf")),None)
        out.append({"date":d.isoformat(),"headline":headline,"priceSensitive":bool(row.get("priceSensitive")),"url":urljoin("https://www.asx.com.au",href) if href else None})
    return out

def priority(a):
    h=(a.get("headline") or "").lower(); score=12 if a.get("priceSensitive") else 0
    for i,k in enumerate(DOC_PRIORITY):
        if k in h: score += max(2,10-i//3)
    return score

def pdf_text(url):
    raw=fetch_bytes(url,35); reader=PdfReader(io.BytesIO(raw)); chunks=[]
    for page in reader.pages[:MAX_PDF_PAGES]:
        try: chunks.append(page.extract_text() or "")
        except Exception: pass
        if sum(len(x) for x in chunks)>=MAX_TEXT_CHARS: break
    return "\n".join(chunks)[:MAX_TEXT_CHARS]

def clean_snippet(text, start, end, pad=150):
    s=max(0,start-pad); e=min(len(text),end+pad); x=" ".join(text[s:e].split())
    return x[:420]

def find_evidence(text, patterns, limit=3):
    low=text.lower(); out=[]
    for pat in patterns:
        for m in re.finditer(pat,low,re.I):
            sn=clean_snippet(text,m.start(),m.end())
            if sn and sn not in out: out.append(sn)
            if len(out)>=limit: return out
    return out

def sector_family(stock):
    x=(str(stock.get("sector") or "")+" "+str(stock.get("industry") or "")).lower()
    if any(k in x for k in ["materials","mining","metals","gold","lithium","resources"]): return "resources"
    if any(k in x for k in ["energy","oil","gas"]): return "energy"
    if any(k in x for k in ["technology","software","semiconductor","information technology"]): return "technology"
    if any(k in x for k in ["health","biotech","pharma","medical"]): return "health"
    if any(k in x for k in ["consumer","retail","restaurant"]): return "consumer"
    if any(k in x for k in ["financial","bank","insurance"]): return "financials"
    return "industrials"

def sector_snippets(text, family):
    keys=SECTOR_RULES.get(family,[]); out=[]
    for key in keys:
        m=re.search(re.escape(key),text,re.I)
        if m:
            out.append({"metric":key,"evidence":clean_snippet(text,m.start(),m.end(),120)})
        if len(out)>=5: break
    return out

def analyse_company(stock):
    ticker=str(stock.get("ticker","")).upper()
    if ticker in {"GOLD","ETPMAG"}: return {"ticker":ticker,"status":"NOT_APPLICABLE","reason":"Exchange-traded product; issuer operating evidence is not comparable with a company."}
    try: anns=announcement_rows(ticker)
    except Exception as e: return {"ticker":ticker,"status":"ERROR","reason":str(e)}
    docs=sorted([a for a in anns if a.get("url")],key=priority,reverse=True)[:MAX_DOCS_PER_COMPANY]
    combined=[]; doc_meta=[]
    for a in docs:
        try:
            text=pdf_text(a["url"])
            if text.strip():
                combined.append(f"\nDOCUMENT {a['date']} {a['headline']}\n{text}")
                doc_meta.append({"date":a["date"],"headline":a["headline"],"priceSensitive":a["priceSensitive"],"url":a["url"],"textChars":len(text)})
        except Exception as e:
            doc_meta.append({"date":a["date"],"headline":a["headline"],"priceSensitive":a["priceSensitive"],"url":a["url"],"error":str(e)[:160]})
        time.sleep(.08)
    text="\n".join(combined)
    evidence={k:find_evidence(text,p) for k,p in RULES.items()} if text else {k:[] for k in RULES}
    score=50; risk=30; positives=[]; flags=[]
    def pos(delta,label):
        nonlocal score; score+=delta; positives.append(label)
    def neg(sd,rd,label,severity="MEDIUM"):
        nonlocal score,risk; score-=sd; risk+=rd; flags.append({"severity":severity,"text":label})
    if evidence["guidance_raise"]: pos(12,"Management has raised or beaten guidance in recent disclosures.")
    elif evidence["guidance_reaffirm"]: pos(6,"Management has reaffirmed or maintained guidance.")
    if evidence["guidance_cut"]: neg(16,18,"Guidance has been cut, withdrawn or missed.","HIGH")
    if evidence["contract_win"]: pos(8,"Recent disclosures contain contract/customer win evidence.")
    if evidence["contract_loss"]: neg(13,15,"Recent disclosures contain contract/customer loss or termination evidence.","HIGH")
    if evidence["execution_positive"]: pos(8,"Recent disclosures show delivery/commissioning milestones being achieved.")
    if evidence["execution_negative"]: neg(8,9,"Recent disclosures contain delay, deferral or operating interruption language.")
    if evidence["capital_raise"]: neg(8,10,"Recent capital raising/share issuance creates dilution and funding-dependence risk.")
    if evidence["options_issue"]: neg(4,5,"Options, performance rights or convertibles may add future dilution.","LOW")
    if evidence["debt_refi_positive"]: pos(5,"Recent disclosures show refinancing, facility extension or liquidity support.")
    if evidence["debt_stress"]: neg(18,22,"Recent disclosures contain debt, covenant, going-concern or liquidity stress language.","HIGH")
    if evidence["cash_burn"] and n(stock.get("freeCashflow"))<0: neg(8,10,"Disclosure evidence reinforces negative cash-flow/cash-runway risk.")
    if evidence["capex_overrun"]: neg(12,14,"Recent disclosures indicate rising project/capital costs.","HIGH")
    if evidence["major_customer"]: risk+=6; flags.append({"severity":"MEDIUM","text":"Customer-concentration language appears in recent disclosures; dependency should be checked."})
    family=sector_family(stock); sector_evidence=sector_snippets(text,family) if text else []
    delivery=clamp(50 + (12 if evidence["guidance_raise"] else 6 if evidence["guidance_reaffirm"] else 0) + (8 if evidence["execution_positive"] else 0) - (18 if evidence["guidance_cut"] else 0) - (10 if evidence["execution_negative"] else 0))
    score=round(clamp(score)); risk=round(clamp(risk))
    summary_parts=[]
    if positives: summary_parts.append("Positive evidence: "+" ".join(positives[:3]))
    if flags: summary_parts.append("Risks: "+" ".join(f["text"] for f in flags[:3]))
    if not summary_parts: summary_parts.append("No strong positive or negative disclosure signal was detected in the selected recent documents.")
    return {
        "ticker":ticker,"status":"OK","evidenceScore":score,"evidenceRisk":risk,"managementDeliveryScore":round(delivery),
        "evidencePositives":positives,"evidenceFlags":flags,"evidenceSummary":" ".join(summary_parts),"evidenceSignals":evidence,
        "sectorEvidenceFamily":family,"sectorEvidence":sector_evidence,"evidenceDocuments":doc_meta,
        "announcementsReviewed":len(anns),"documentsRead":sum(1 for d in doc_meta if d.get("textChars")),
        "analysedAt":dt.datetime.now(dt.timezone.utc).isoformat()
    }

def main():
    data=json.loads(DATA_PATH.read_text(encoding="utf-8")); stocks=data.get("stocks",[])
    ranked=sorted(stocks,key=lambda s:(n(s.get("opp")),n(s.get("confidence"))),reverse=True)
    picked=[]; seen=set()
    for s in ranked:
        t=str(s.get("ticker","")).upper()
        if not t or t in seen: continue
        if len(picked)<MAX_COMPANIES or t in CORE: picked.append(s); seen.add(t)
        if len(picked)>=MAX_COMPANIES and CORE.issubset(seen): break
    out=[]
    for i,s in enumerate(picked,1):
        rec=analyse_company(s); out.append(rec)
        if rec.get("status")=="OK":
            for k in ["evidenceScore","evidenceRisk","managementDeliveryScore","evidencePositives","evidenceFlags","evidenceSummary","evidenceSignals","sectorEvidenceFamily","sectorEvidence","evidenceDocuments","documentsRead"]:
                s[k]=rec.get(k)
            s["evidenceUpdated"]=rec.get("analysedAt")
        print(i,rec.get("ticker"),rec.get("status"),rec.get("evidenceScore"),rec.get("evidenceRisk"),rec.get("documentsRead"))
    now=dt.datetime.now(dt.timezone.utc).isoformat(); data["companyEvidenceUpdated"]=now
    DATA_PATH.write_text(json.dumps(data,indent=2),encoding="utf-8")
    OUT_PATH.parent.mkdir(parents=True,exist_ok=True)
    OUT_PATH.write_text(json.dumps({"updated":now,"coverage":len(out),"method":"Reads selected recent ASX announcement PDFs for leading candidates and core holdings. Detects guidance, capital raising/dilution, debt/liquidity, cash burn, capex, customer concentration, contracts and execution evidence, plus sector-specific disclosure snippets. Evidence is heuristic and retained with source document metadata for auditability.","companies":out},indent=2),encoding="utf-8")

if __name__=="__main__": main()
