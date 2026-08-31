from pathlib import Path
p=Path('index.html')
s=p.read_text()
css=r'''
/* Premium finance / Apple-style visual system */
:root{--bg:#071019;--panel:rgba(19,28,39,.76);--panel2:rgba(27,39,53,.72);--line:rgba(162,186,210,.16);--text:#f7fbff;--muted:#8fa5b8;--green:#4ee58a;--blue:#76bfff;--red:#ff7474;--amber:#ffc264}
html{background:#071019}
body{position:relative;min-height:100vh;background:
 radial-gradient(circle at 18% -5%,rgba(64,162,255,.15),transparent 30%),
 radial-gradient(circle at 88% 18%,rgba(50,220,135,.12),transparent 26%),
 linear-gradient(180deg,#08111b 0%,#071019 46%,#050b11 100%);background-attachment:fixed}
body:before{content:'';position:fixed;inset:0;pointer-events:none;z-index:-2;opacity:.34;background-image:
 linear-gradient(rgba(103,152,189,.07) 1px,transparent 1px),
 linear-gradient(90deg,rgba(103,152,189,.07) 1px,transparent 1px);background-size:28px 28px;mask-image:linear-gradient(to bottom,rgba(0,0,0,.9),rgba(0,0,0,.28) 72%,transparent)}
body:after{content:'01 0110 10 1101   ASX  ∙  DATA  ∙  SIGNAL  ∙  RISK  ∙  FLOW';position:fixed;left:-12px;right:-12px;top:128px;z-index:-1;pointer-events:none;white-space:nowrap;overflow:hidden;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10px;letter-spacing:6px;color:rgba(117,192,255,.045);transform:rotate(-7deg)}
.app{position:relative}
header{background:rgba(7,16,25,.72)!important;border-bottom:1px solid rgba(255,255,255,.08)!important;box-shadow:0 8px 28px rgba(0,0,0,.18);backdrop-filter:blur(28px) saturate(145%)!important;-webkit-backdrop-filter:blur(28px) saturate(145%)!important}
.panel,.stock,.metric,.global-box,.detail-kpi,.score-box,.analysis-item,.perf-box,.quick-result,.lock-card{background:linear-gradient(180deg,rgba(28,40,54,.78),rgba(15,24,34,.72))!important;border:1px solid rgba(255,255,255,.10)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.035),0 12px 34px rgba(0,0,0,.18);backdrop-filter:blur(22px) saturate(125%);-webkit-backdrop-filter:blur(22px) saturate(125%)}
.hero{background:radial-gradient(circle at 80% 0%,rgba(83,229,145,.18),transparent 35%),linear-gradient(145deg,rgba(30,57,44,.92),rgba(14,28,24,.80))!important;border:1px solid rgba(89,238,154,.28)!important;box-shadow:0 18px 42px rgba(0,0,0,.24),inset 0 1px 0 rgba(255,255,255,.06)}
.stock.buy{border-color:rgba(78,229,138,.48)!important;box-shadow:0 12px 36px rgba(25,132,76,.12),inset 0 1px 0 rgba(255,255,255,.04)}
.stock.hold{border-color:rgba(118,191,255,.30)!important}.stock.sell{border-color:rgba(255,116,116,.38)!important}
button,.btn,.home-tab,.portfolio-tab,.detail-icon-tab,.segment button,.refresh,.unlock-btn{cursor:pointer;transition:transform .16s ease,box-shadow .16s ease,background .16s ease,border-color .16s ease,filter .16s ease}
button:active,.btn:active,.home-tab:active,.portfolio-tab:active,.detail-icon-tab:active,.segment button:active,.refresh:active,.unlock-btn:active{transform:scale(.965);filter:brightness(1.08)}
.btn,.home-tab,.portfolio-tab,.detail-icon-tab,.segment button,.refresh,.edge-modal-close{background:linear-gradient(180deg,rgba(255,255,255,.105),rgba(255,255,255,.045))!important;border:1px solid rgba(255,255,255,.14)!important;color:#eaf4fc!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.09),0 7px 18px rgba(0,0,0,.16)!important;backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px)}
.btn{border-radius:14px!important;min-height:42px;padding:10px 14px!important;font-weight:800!important}
.btn.primary,.unlock-btn{background:linear-gradient(180deg,#56ed93,#2fcf73)!important;border-color:rgba(136,255,182,.75)!important;color:#04130a!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.42),0 8px 22px rgba(46,210,117,.24)!important}
.btn.danger{background:linear-gradient(180deg,rgba(255,112,112,.95),rgba(207,59,59,.92))!important;color:white!important;border-color:rgba(255,180,180,.42)!important}
.home-tab,.portfolio-tab,.segment button{border-radius:999px!important;min-height:42px!important}
.home-tab.active,.portfolio-tab.active,.segment button.active,.detail-icon-tab.active{background:linear-gradient(180deg,rgba(101,235,158,.98),rgba(45,205,115,.96))!important;border-color:rgba(139,255,188,.72)!important;color:#05130b!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.45),0 8px 22px rgba(48,209,119,.20)!important}
.detail-icon-tabs{background:linear-gradient(180deg,rgba(7,16,25,.96),rgba(7,16,25,.78))!important;border:1px solid rgba(255,255,255,.06);border-radius:17px;padding:8px!important;box-shadow:0 10px 30px rgba(0,0,0,.18)}
.detail-icon-tab{border-radius:13px!important;min-height:54px!important}
.refresh{border-radius:14px!important}
.action{border-radius:999px!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.13),0 6px 16px rgba(0,0,0,.16)}
.action.buy{background:linear-gradient(180deg,#45df83,#22b965)!important;color:#04130a!important}.action.hold{background:linear-gradient(180deg,#5aa8e8,#347ab5)!important;color:white!important}.action.sell{background:linear-gradient(180deg,#ef6969,#b63f3f)!important;color:white!important}
.search,.editor input,.setting select,.pin-input{background:rgba(12,22,32,.72)!important;border:1px solid rgba(255,255,255,.13)!important;border-radius:14px!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.035);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px)}
.search:focus,.editor input:focus,.setting select:focus,.pin-input:focus{outline:none;border-color:rgba(118,191,255,.68)!important;box-shadow:0 0 0 3px rgba(80,166,238,.12)}
.bottom-nav{background:rgba(8,16,24,.72)!important;border-top:1px solid rgba(255,255,255,.09)!important;backdrop-filter:blur(30px) saturate(150%)!important;-webkit-backdrop-filter:blur(30px) saturate(150%)!important;box-shadow:0 -10px 34px rgba(0,0,0,.20)}
.nav{margin:6px 5px;border-radius:14px!important;transition:.16s ease}.nav.active{background:rgba(78,229,138,.10);color:#7cf1aa!important;box-shadow:inset 0 0 0 1px rgba(78,229,138,.12)}
.notice{background:rgba(25,70,46,.40)!important;border-color:rgba(78,229,138,.22)!important;backdrop-filter:blur(18px)}
.edge-modal-card{background:linear-gradient(180deg,rgba(29,40,53,.98),rgba(11,19,28,.98))!important;border-color:rgba(255,255,255,.12)!important;backdrop-filter:blur(30px);-webkit-backdrop-filter:blur(30px)}
.tag,.global-chip,.sector-pill{background:rgba(255,255,255,.035);backdrop-filter:blur(10px)}
.section-title{letter-spacing:-.01em}.ticker,.hero-title,.detail-ticker,.detail-score,.metric-value,.score-value{letter-spacing:-.025em}
@media (prefers-reduced-motion:reduce){button,.btn,.home-tab,.portfolio-tab,.detail-icon-tab,.segment button,.refresh,.unlock-btn{transition:none}}
'''
if 'Premium finance / Apple-style visual system' not in s:
    s=s.replace('</style>',css+'\n</style>',1)
p.write_text(s)
print('premium finance UI applied')
