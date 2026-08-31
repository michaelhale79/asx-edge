import datetime as dt
import http.cookiejar
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

DATA_PATH = Path("data.json")
OUT_PATH = Path("study/fundamentals.json")
MAX_COMPANIES = 140
CORE = {"WBT","CSL","RIO","DMP","DRO","ETPMAG","GOLD","S32","DTL","WOR","MIN","AIA"}
HEADERS = {"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15"}


def n(v, default=None):
    if isinstance(v, dict):
        v = v.get("raw", v.get("fmt"))
    try:
        x=float(v)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def clamp(x, lo=0, hi=100): return max(lo,min(hi,x))

def pct(v):
    x=n(v)
    if x is None: return None
    return x*100 if abs(x)<=2 else x

class Yahoo:
    def __init__(self):
        self.jar=http.cookiejar.CookieJar()
        self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.crumb=None

    def get_json(self,url):
        req=urllib.request.Request(url,headers=HEADERS)
        with self.opener.open(req,timeout=25) as r:
            return json.loads(r.read().decode("utf-8",errors="ignore"))

    def ensure_crumb(self):
        if self.crumb: return self.crumb
        try:
            req=urllib.request.Request("https://fc.yahoo.com",headers=HEADERS)
            try: self.opener.open(req,timeout=12).read()
            except Exception: pass
            req=urllib.request.Request("https://query1.finance.yahoo.com/v1/test/getcrumb",headers=HEADERS)
            with self.opener.open(req,timeout=15) as r:
                c=r.read().decode("utf-8",errors="ignore").strip()
                if c and "Too Many Requests" not in c: self.crumb=c
        except Exception: self.crumb=None
        return self.crumb

    def quote_summary(self,symbol):
        modules="financialData,defaultKeyStatistics,summaryDetail,price,incomeStatementHistory,balanceSheetHistory,cashflowStatementHistory"
        q={"modules":modules,"formatted":"false","lang":"en-US","region":"US"}
        crumb=self.ensure_crumb()
        if crumb: q["crumb"]=crumb
        url="https://query2.finance.yahoo.com/v10/finance/quoteSummary/"+urllib.parse.quote(symbol)+"?"+urllib.parse.urlencode(q)
        try:
            obj=self.get_json(url)
            return (((obj.get("quoteSummary") or {}).get("result") or [{}])[0]) or {}
        except Exception as e:
            print("quoteSummary failed",symbol,e); return {}

    def share_history(self,symbol):
        end=int(dt.datetime.now(dt.timezone.utc).timestamp())
        start=end-5*366*86400
        types="annualDilutedAverageShares,annualBasicAverageShares,annualTotalRevenue,annualNetIncome,annualFreeCashFlow"
        q=urllib.parse.urlencode({"symbol":symbol,"type":types,"period1":start,"period2":end})
        url="https://query2.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/"+urllib.parse.quote(symbol)+"?"+q
        try:
            obj=self.get_json(url)
            out={}
            for series in ((obj.get("timeseries") or {}).get("result") or []):
                meta=series.get("meta") or {}; typ=meta.get("type")
                if not typ:
                    typ=next((k for k in series if k.startswith("annual")),None)
                vals=[]
                for row in series.get(typ,[]) if typ else []:
                    raw=n(row.get("reportedValue"))
                    if raw is not None: vals.append((row.get("asOfDate"),raw))
                if typ and vals: out[typ]=vals
            return out
        except Exception as e:
            print("timeseries failed",symbol,e); return {}


def module_raw(mod,key): return n((mod or {}).get(key))

def latest_statement(mod, key):
    arr=(mod or {}).get(key) or []
    return arr[0] if arr else {}


def calc_dilution(hist):
    rows=hist.get("annualDilutedAverageShares") or hist.get("annualBasicAverageShares") or []
    rows=sorted(rows,key=lambda x:x[0] or "")
    if len(rows)<2 or not rows[-2][1]: return None
    return (rows[-1][1]/rows[-2][1]-1)*100


def analyse(stock, y):
    ticker=str(stock.get("ticker","")).upper(); symbol=ticker+".AX"
    q=y.quote_summary(symbol); hist=y.share_history(symbol)
    fd=q.get("financialData") or {}; ks=q.get("defaultKeyStatistics") or {}; sd=q.get("summaryDetail") or {}; pr=q.get("price") or {}
    inc=latest_statement(q.get("incomeStatementHistory"),"incomeStatementHistory")
    bal=latest_statement(q.get("balanceSheetHistory"),"balanceSheetStatements")
    cf=latest_statement(q.get("cashflowStatementHistory"),"cashflowStatements")

    quote_type=(pr.get("quoteType") or stock.get("quoteType") or "").upper()
    if quote_type in {"ETF","MUTUALFUND"} or ticker in {"GOLD","ETPMAG"}:
        return {"ticker":ticker,"status":"NOT_APPLICABLE","reason":"Exchange-traded product; company balance-sheet analysis is not meaningful."}

    market_cap=module_raw(pr,"marketCap") or module_raw(sd,"marketCap")
    revenue=module_raw(fd,"totalRevenue") or module_raw(inc,"totalRevenue")
    revenue_growth=pct(fd.get("revenueGrowth"))
    earnings_growth=pct(fd.get("earningsGrowth"))
    gross_margin=pct(fd.get("grossMargins")); operating_margin=pct(fd.get("operatingMargins")); profit_margin=pct(fd.get("profitMargins"))
    op_cash=module_raw(fd,"operatingCashflow") or module_raw(cf,"totalCashFromOperatingActivities")
    fcf=module_raw(fd,"freeCashflow")
    cash=module_raw(fd,"totalCash") or module_raw(bal,"cash")
    debt=module_raw(fd,"totalDebt") or module_raw(bal,"totalDebt")
    debt_equity=module_raw(fd,"debtToEquity")
    current_ratio=module_raw(fd,"currentRatio"); quick_ratio=module_raw(fd,"quickRatio")
    roe=pct(fd.get("returnOnEquity")); roa=pct(fd.get("returnOnAssets"))
    pe=module_raw(sd,"trailingPE"); forward_pe=module_raw(ks,"forwardPE") or module_raw(sd,"forwardPE")
    pb=module_raw(ks,"priceToBook"); ev_ebitda=module_raw(ks,"enterpriseToEbitda")
    div_yield=pct(sd.get("dividendYield"))
    dilution=calc_dilution(hist)
    net_cash=(cash-debt) if cash is not None and debt is not None else None
    cash_runway=None
    if cash is not None and fcf is not None and fcf<0: cash_runway=cash/abs(fcf) if fcf else None

    flags=[]
    def flag(severity,text): flags.append({"severity":severity,"text":text})
    if debt_equity is not None and debt_equity>150: flag("HIGH",f"High debt-to-equity ({debt_equity:.0f}%).")
    elif debt_equity is not None and debt_equity>80: flag("MEDIUM",f"Elevated debt-to-equity ({debt_equity:.0f}%).")
    if cash is not None and debt is not None and debt>max(cash*2,1): flag("MEDIUM","Debt is more than twice cash on hand.")
    if current_ratio is not None and current_ratio<1: flag("HIGH",f"Current ratio below 1 ({current_ratio:.2f}).")
    if fcf is not None and fcf<0: flag("MEDIUM","Free cash flow is negative.")
    if cash_runway is not None and cash_runway<1.5: flag("HIGH",f"Estimated cash runway is only about {cash_runway:.1f} years at the current FCF burn rate.")
    if profit_margin is not None and profit_margin<0: flag("MEDIUM","Company is currently loss-making on reported profit margin.")
    if revenue_growth is not None and revenue_growth<-10: flag("MEDIUM",f"Revenue is shrinking ({revenue_growth:.1f}% growth).")
    if dilution is not None and dilution>15: flag("HIGH",f"Heavy annual share dilution ({dilution:.1f}%).")
    elif dilution is not None and dilution>7: flag("MEDIUM",f"Meaningful annual share dilution ({dilution:.1f}%).")
    if pe is not None and pe>60: flag("MEDIUM",f"High trailing P/E ({pe:.1f}x).")

    profitability=50
    if profit_margin is not None: profitability=clamp(50+profit_margin*1.6)
    if roe is not None: profitability=clamp(profitability*.65+clamp(50+roe)*.35)
    growth=50
    if revenue_growth is not None: growth=clamp(50+revenue_growth*1.5)
    if earnings_growth is not None: growth=clamp(growth*.55+clamp(50+earnings_growth)*.45)
    balance=60
    if debt_equity is not None: balance-=max(0,debt_equity-30)*.22
    if current_ratio is not None: balance+=clamp((current_ratio-1)*15,-20,20)
    if net_cash is not None and market_cap: balance+=clamp(net_cash/market_cap*100, -20,20)
    cashflow=60
    if fcf is not None and revenue: cashflow=clamp(50+(fcf/revenue)*220)
    elif op_cash is not None and revenue: cashflow=clamp(50+(op_cash/revenue)*140)
    dilution_score=70 if dilution is None else clamp(80-dilution*3)
    valuation=55
    if forward_pe is not None and forward_pe>0: valuation=clamp(85-forward_pe*1.7)
    elif pe is not None and pe>0: valuation=clamp(82-pe*1.5)
    if pb is not None and pb>0: valuation=clamp(valuation*.8+clamp(80-pb*5)*.2)
    fundamental=clamp(profitability*.20+growth*.18+balance*.22+cashflow*.18+dilution_score*.12+valuation*.10)
    high=sum(1 for f in flags if f["severity"]=="HIGH"); med=sum(1 for f in flags if f["severity"]=="MEDIUM")
    risk=clamp(25+high*18+med*8+(100-balance)*.25+(100-dilution_score)*.15)

    return {
      "ticker":ticker,"status":"OK","marketCap":market_cap,"revenue":revenue,"revenueGrowthPct":revenue_growth,"earningsGrowthPct":earnings_growth,
      "grossMarginPct":gross_margin,"operatingMarginPct":operating_margin,"profitMarginPct":profit_margin,"operatingCashflow":op_cash,"freeCashflow":fcf,
      "cash":cash,"debt":debt,"netCash":net_cash,"debtToEquityPct":debt_equity,"currentRatio":current_ratio,"quickRatio":quick_ratio,"returnOnEquityPct":roe,"returnOnAssetsPct":roa,
      "trailingPE":pe,"forwardPE":forward_pe,"priceToBook":pb,"evToEbitda":ev_ebitda,"dividendYieldPct":div_yield,"annualDilutionPct":dilution,"cashRunwayYears":cash_runway,
      "profitabilityScore":round(profitability),"growthFundamentalScore":round(growth),"balanceSheetScore":round(clamp(balance)),"cashflowScore":round(cashflow),"dilutionScore":round(dilution_score),"valuationFundamentalScore":round(valuation),
      "fundamentalScore":round(fundamental),"fundamentalRisk":round(risk),"riskFlags":flags,"source":"Yahoo Finance financial modules/time-series","analysedAt":dt.datetime.now(dt.timezone.utc).isoformat()
    }


def main():
    data=json.loads(DATA_PATH.read_text(encoding="utf-8")); stocks=data.get("stocks",[])
    ranked=sorted(stocks,key=lambda s:(float(s.get("opp") or 0),float(s.get("confidence") or 0)),reverse=True)
    picked=[]; seen=set()
    for s in ranked:
        t=str(s.get("ticker","")).upper()
        if not t or t in seen: continue
        if len(picked)<MAX_COMPANIES or t in CORE:
            picked.append(s); seen.add(t)
        if len(picked)>=MAX_COMPANIES and CORE.issubset(seen): break
    y=Yahoo(); out=[]
    for i,s in enumerate(picked,1):
        rec=analyse(s,y); out.append(rec)
        if rec.get("status")=="OK":
            for k,v in rec.items():
                if k not in {"ticker","status","source","analysedAt"}: s[k]=v
            # Replace old placeholder valuation with a real fundamentals-derived score where available.
            s["valuation"]=rec["valuationFundamentalScore"]
            s["fundamentalUpdated"]=rec["analysedAt"]
        print(i,rec.get("ticker"),rec.get("status"),rec.get("fundamentalScore"),rec.get("fundamentalRisk")); time.sleep(.12)
    now=dt.datetime.now(dt.timezone.utc).isoformat(); data["fundamentalsUpdated"]=now
    DATA_PATH.write_text(json.dumps(data,indent=2),encoding="utf-8")
    OUT_PATH.parent.mkdir(parents=True,exist_ok=True)
    OUT_PATH.write_text(json.dumps({"updated":now,"coverage":len(out),"method":"Financial statement, balance sheet, cash-flow, valuation and dilution enrichment. Missing source fields remain null rather than being guessed.","companies":out},indent=2),encoding="utf-8")

if __name__=="__main__": main()
