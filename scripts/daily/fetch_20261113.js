// 2026-11-13（周五）销售日：体彩计算器在售全部场次（全玩法）
const fs = require('fs');
const HDR = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
  'Accept': 'application/json, text/plain, */*',
  'Referer': 'https://www.sporttery.cn/',
  'Cache-Control': 'no-cache',
};
async function getJson(url) {
  const res = await fetch(url, { headers: HDR });
  const buf = await res.arrayBuffer();
  const text = Buffer.from(buf).toString('utf8');
  try { return { status: res.status, data: JSON.parse(text), text }; } catch (e) { return { status: res.status, data: null, text }; }
}
(async () => {
  const calcUrl = 'https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry?poolCode=hhad,had,crs,ttg,hafu&channel=c&_=' + Date.now();
  const calc = await getJson(calcUrl);
  fs.writeFileSync('reports/data/20261113_calc_raw.json', calc.text, 'utf8');
  console.log('CALC status', calc.status, 'len', calc.text.length);
  const list = (((calc.data || {}).value || {}).matchInfoList) || [];
  console.log('businessDate groups', list.length);
  const rows = [];
  for (const day of list) {
    for (const m of (day.subMatchList || [])) {
      rows.push({
        businessDate: day.businessDate, matchDate: m.matchDate, matchTime: m.matchTime,
        matchNum: m.matchNum, matchNumStr: m.matchNumStr, league: m.leagueName, leagueAbb: m.leagueAbbName,
        home: m.homeTeamAbbName || m.homeTeam, away: m.awayTeamAbbName || m.awayTeam,
        single: m.bettingSingle, status: m.matchStatus, pools: (m.poolList || []).map(p => p.poolCode),
      });
    }
  }
  fs.writeFileSync('reports/data/20261113_calc_rows.json', JSON.stringify(rows, null, 1), 'utf8');
  console.log('TOTAL rows', rows.length);
  for (const r of rows) console.log(JSON.stringify(r));
})().catch(e => { console.error(e); process.exit(1); });
