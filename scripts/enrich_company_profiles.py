import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

DATA=Path('data.json')
H={'User-Agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15'}

FALLBACK={
'WBT':('Information Technology','Semiconductors','Weebit Nano develops non-volatile ReRAM memory technology for semiconductor manufacturers and embedded-system applications.'),
'CSL':('Health Care','Biotechnology','CSL is a global biotechnology company focused on plasma therapies, vaccines and specialty medicines.'),
'RIO':('Materials','Diversified Metals & Mining','Rio Tinto is a global mining group producing iron ore, aluminium, copper and other minerals and metals.'),
'DMP':('Consumer Discretionary','Restaurants','Domino’s Pizza Enterprises operates and franchises Domino’s pizza stores across Australia, New Zealand, Europe and Asia.'),
'DRO':('Industrials','Aerospace & Defence','DroneShield develops counter-drone detection and electronic-warfare systems for defence, government and security customers.'),
'S32':('Materials','Diversified Metals & Mining','South32 is a diversified mining company producing commodities including aluminium, manganese, copper, zinc and base metals.'),
'DTL':('Information Technology','IT Services','Data#3 provides enterprise information-technology solutions, cloud, software, managed services and consulting.'),
'WOR':('Industrials','Engineering & Construction','Worley provides engineering, project and consulting services to energy, chemicals and resources industries worldwide.'),
'MIN':('Materials','Diversified Metals & Mining','Mineral Resources is an Australian mining-services and resources company with iron ore and lithium operations.'),
'AIA':('Industrials','Transportation Infrastructure','Auckland International Airport owns and operates New Zealand’s largest international airport and related property assets.'),
'GOLD':('Financials','Exchange Traded Product','GOLD is an exchange-traded product designed to provide exposure to the Australian-dollar gold price.'),
'ETPMAG':('Materials','Exchange Traded Product','ETPMAG is an exchange-traded product designed to provide exposure to the price of silver.')
}

def fetch_profile(ticker):
    symbol=urllib.parse.quote(ticker+'.AX')
    url=f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=assetProfile,price'
    req=urllib.request.Request(url,headers=H)
    with urllib.request.urlopen(req,timeout=15) as r:
        raw=json.load(r)
    result=(raw.get('quoteSummary',{}).get('result') or [{}])[0]
    p=result.get('assetProfile') or {}
    price=result.get('price') or {}
    return {
        'name': price.get('longName') or price.get('shortName'),
        'sector': p.get('sector'),
        'industry': p.get('industry'),
        'description': p.get('longBusinessSummary')
    }

def main():
    data=json.loads(DATA.read_text(encoding='utf-8'))
    stocks=data.get('stocks',[])
    done=0
    for s in stocks:
        t=str(s.get('ticker','')).upper()
        if not t: continue
        try:
            prof=fetch_profile(t)
            if prof.get('name') and (not s.get('name') or s.get('name')==t): s['name']=prof['name']
            if prof.get('sector'): s['sector']=prof['sector']
            if prof.get('industry'): s['industry']=prof['industry']
            if prof.get('description'): s['description']=prof['description']
            done+=1
        except Exception as e:
            print('profile failed',t,e)
        if t in FALLBACK:
            sec,ind,desc=FALLBACK[t]
            s.setdefault('sector',sec); s.setdefault('industry',ind); s.setdefault('description',desc)
        time.sleep(.08)
    data['companyProfiles']={'updated':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'enrichedCount':done,'source':'Yahoo Finance company profile data with curated fallback for core holdings'}
    DATA.write_text(json.dumps(data,indent=2),encoding='utf-8')
    print('profiles enriched',done,'of',len(stocks))

if __name__=='__main__': main()
