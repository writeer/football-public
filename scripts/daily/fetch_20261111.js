// 2026-11-11 当日比赛拉取：体彩计算器（在售，全玩法）+ 赛果（核对是否已完赛）
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
  try { return { status: res.status, data: JSON.parse(text), text }; }
  catch (e) { return { status: res.status, data: null, text }; }
}

(async () => {
  const calcUrl = 'https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry'
    + '?poolCode=hhad,had,crs,ttg,hafu&channel=c&_=' + Date.now();
  const calc = await getJson(calcUrl);
  fs.writeFileSync('reports/data/20261111_calc_raw.json', calc.text, 'utf8');
  const list = (((calc.data || {}).value || {}).matchInfoList) || [];
  console.log('CALC status', calc.status, 'matchInfoList', list.length);

  const rows = [];
  for (const day of list) {
    for (const m of (day.subMatchList || [])) {
      rows.push({
        businessDate: day.businessDate,
        matchDate: m.matchDate, matchTime: m.matchTime, matchNum: m.matchNum,
        matchNumStr: m.matchNumStr, league: m.leagueName, leagueAbb: m.leagueAbbName,
        home: m.homeTeamAbbName || m.homeTeam, away: m.awayTeamAbbName || m.awayTeam,
        single: m.bettingSingle, status: m.matchStatus, poolList: (m.poolList || []).map(p => p.poolCode),
      });
    }
  }
  fs.writeFileSync('reports/data/20261111_calc_rows.json', JSON.stringify(rows, null, 1), 'utf8');
  console.log('TOTAL rows', rows.length);
  const byDate = {};
  for (const r of rows) byDate[r.matchDate] = (byDate[r.matchDate] || 0) + 1;
  console.log('BY matchDate', JSON.stringify(byDate));
  console.log('--- 全部在售明细 ---');
  for (const r of rows) console.log(JSON.stringify(r));

  const resUrl = 'https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry'
    + '?matchBeginDate=2026-11-11&matchEndDate=2026-11-11&leagueId=&pageSize=200&pageNo=1&isFix=0&matchPage=1&pcOrWap=1&_=' + Date.now();
  const res = await getJson(resUrl);
  fs.writeFileSync('reports/data/20261111_results_official.json', res.text, 'utf8');
  const rl = (((res.data || {}).value || {}).matchResult) || [];
  console.log('RESULTS status', res.status, 'matches', rl.length);
  for (const m of rl) {
    console.log(JSON.stringify({
      numStr: m.matchNumStr, date: m.matchDate, time: m.matchTime, league: m.leagueName,
      home: m.homeTeam, away: m.awayTeam, no999: m.sectionsNo999, no1: m.sectionsNo1,
      goalLine: m.goalLine, status: m.matchStatus, resultStatus: m.matchResultStatus, single: m.bettingSingle,
    }));
  }
})().catch(e => { console.error(e); process.exit(1); });
