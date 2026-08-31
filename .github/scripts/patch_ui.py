from pathlib import Path

p = Path('index.html')
s = p.read_text()

css = '''
.lock-screen{position:fixed;inset:0;z-index:9999;background:var(--bg);display:flex;align-items:center;justify-content:center;padding:24px}.lock-card{width:min(100%,380px);background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:24px;text-align:center;box-shadow:0 24px 70px rgba(0,0,0,.45)}.lock-logo{font-size:28px;font-weight:900;margin-bottom:5px}.lock-sub{color:var(--muted);font-size:12px;margin-bottom:20px}.pin-input{width:100%;height:54px;border:1px solid var(--line);border-radius:14px;background:var(--panel2);color:#fff;text-align:center;font-size:26px;letter-spacing:.3em;padding-left:.3em}.unlock-btn{width:100%;height:50px;margin-top:10px;border:1px solid #2e6e45;border-radius:13px;background:#183321;color:#baf3cc;font-weight:850}.pin-error{min-height:18px;color:#ff9c9c;font-size:11px;margin-top:9px}.portfolio-tabs{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:4px 0 14px}.portfolio-tab{min-height:44px;border:1px solid var(--line);border-radius:12px;background:var(--panel);color:var(--muted);font-size:11px;font-weight:800}.portfolio-tab.active{border-color:#38694a;background:#17261d;color:#a9edbe}.portfolio-pane{display:none}.portfolio-pane.active{display:block}
'''
if '.lock-screen{' not in s:
    s = s.replace('</style>', css + '\n</style>')

lock_html = '<div class="lock-screen" id="lockScreen"><div class="lock-card"><div class="lock-logo">ASX Edge</div><div class="lock-sub">Enter PIN to continue</div><input class="pin-input" id="pinInput" type="password" inputmode="numeric" pattern="[0-9]*" maxlength="4" autocomplete="off"><button class="unlock-btn" id="unlockBtn">Unlock</button><div class="pin-error" id="pinError"></div></div></div>'
if 'id="lockScreen"' not in s:
    s = s.replace('<body><div class="app">', '<body>' + lock_html + '<div class="app">')

old_holdings = '<section class="page" id="holdings"><div class="section-title">My Holdings</div><div id="myHoldings"></div><button class="btn primary" data-add="mine">+ Add my holding</button><div class="section-title">Isobel & Oliver Holdings</div><div id="kidsHoldings"></div><button class="btn primary" data-add="kids">+ Add holding</button></section>'
new_holdings = '<section class="page" id="holdings"><div class="portfolio-tabs"><button class="portfolio-tab active" data-portfolio-tab="mine">My Holdings</button><button class="portfolio-tab" data-portfolio-tab="kids">Isobel & Oliver</button></div><div class="portfolio-pane active" data-portfolio-pane="mine"><div id="myHoldings"></div><button class="btn primary" data-add="mine">+ Add my holding</button></div><div class="portfolio-pane" data-portfolio-pane="kids"><div id="kidsHoldings"></div><button class="btn primary" data-add="kids">+ Add holding</button></div></section>'
s = s.replace(old_holdings, new_holdings)

s = s.replace('s?.shortPercent??s?.shortInterestPercent??NaN', 's?.shortInterestPct??s?.shortPercent??s?.shortInterestPercent??NaN')

marker = 'const KEYS={mine:"asxEdgeMineV2",kids:"asxEdgeKidsV2",calls:"asxEdgeCallsV2"};'
security_js = '''
const PIN_SALT="asx-edge-2026-lock-v1";
const PIN_HASH="7d9a312d7047de782175cc3aed77e45aaeb31555faa81f2f7607f677fe327eee";
let activePortfolio="mine";
async function sha256(text){const data=new TextEncoder().encode(text),buf=await crypto.subtle.digest("SHA-256",data);return [...new Uint8Array(buf)].map(b=>b.toString(16).padStart(2,"0")).join("")}
async function tryUnlock(){const input=$("#pinInput"),error=$("#pinError"),hash=await sha256(PIN_SALT+input.value);if(hash===PIN_HASH){sessionStorage.setItem("asxEdgeUnlocked","1");$("#lockScreen").style.display="none";input.value="";error.textContent="";loadData()}else{error.textContent="Incorrect PIN";input.value="";input.focus()}}
function initLock(){const unlocked=sessionStorage.getItem("asxEdgeUnlocked")==="1";if(unlocked){$("#lockScreen").style.display="none";loadData()}else{$("#lockScreen").style.display="flex";setTimeout(()=>$("#pinInput").focus(),50)}}
function setPortfolioTab(key){activePortfolio=key;$$('[data-portfolio-tab]').forEach(b=>b.classList.toggle('active',b.dataset.portfolioTab===key));$$('[data-portfolio-pane]').forEach(p=>p.classList.toggle('active',p.dataset.portfolioPane===key));window.scrollTo(0,0)}
'''
if 'const PIN_HASH=' not in s:
    s = s.replace(marker, marker + security_js)

old_render = 'function renderHoldings(){$("#myHoldings").innerHTML=portfolios.mine.map((p,i)=>holdingCard(p,"mine",i)).join("");$("#kidsHoldings").innerHTML=portfolios.kids.map((p,i)=>holdingCard(p,"kids",i)).join("");bind()}'
new_render = 'function renderHoldings(){$("#myHoldings").innerHTML=portfolios.mine.map((p,i)=>holdingCard(p,"mine",i)).join("");$("#kidsHoldings").innerHTML=portfolios.kids.map((p,i)=>holdingCard(p,"kids",i)).join("");setPortfolioTab(activePortfolio);bind()}'
if old_render not in s:
    raise SystemExit('renderHoldings block not found')
s = s.replace(old_render, new_render)

old_end = ';loadData();\n</script>'
new_end = ';$$(\'[data-portfolio-tab]\').forEach(b=>b.onclick=()=>setPortfolioTab(b.dataset.portfolioTab));$("#unlockBtn").onclick=tryUnlock;$("#pinInput").addEventListener("keydown",e=>{if(e.key==="Enter")tryUnlock()});initLock();\n</script>'
if old_end not in s:
    raise SystemExit('startup block not found')
s = s.replace(old_end, new_end)

p.write_text(s)
