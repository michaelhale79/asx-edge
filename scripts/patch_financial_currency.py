from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
anchor='function metricPct(v){const n=Number(v);return isFinite(n)?pctText(n):"—"}\n'
helper='function financialMoney(s,v){const x=Number(v);if(!isFinite(x))return "—";const a=Math.abs(x),txt=a>=1e9?(a/1e9).toFixed(2)+"B":a>=1e6?(a/1e6).toFixed(1)+"M":a>=1e3?(a/1e3).toFixed(1)+"K":a.toFixed(0);return `${s.financialCurrency||""} ${txt}`.trim()}\n'
if helper not in s:
    if anchor not in s: raise SystemExit('metric anchor missing')
    s=s.replace(anchor,anchor+helper,1)
s=s.replace('detailKpi("Free cash flow",isFinite(Number(s.freeCashflow))?money(Number(s.freeCashflow)):"—"','detailKpi("Free cash flow",isFinite(Number(s.freeCashflow))?financialMoney(s,Number(s.freeCashflow)):"—"',1)
s=s.replace('`${Number(s.netCash)>=0?"Cash ":"Debt "}${money(Math.abs(Number(s.netCash)))}`','`${Number(s.netCash)>=0?"Cash ":"Debt "}${financialMoney(s,Math.abs(Number(s.netCash)))}`',1)
p.write_text(s,encoding='utf-8')
print('financial currency display patched')
