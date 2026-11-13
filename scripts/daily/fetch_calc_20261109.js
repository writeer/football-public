// 直接抓取体彩计算器原始数据，核对在售场次与日期
const fs = require('fs');
(async () => {
  const URL = 'https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry?poolCode=had,hhad,crs,ttg,hafu&channel=c&_=' + Date.now();
  const res = await fetch(URL, { headers: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.sporttery.cn/',
  }});
  const text = Buffer.from(await res.arrayBuffer()).toString('utf8');
  fs.writeFileSync('reports/data/20261109_calc_raw.json', text, 'utf8');
  let d = {};
  try { d = JSON.parse(text); } catch (e) { console.log('NON-JSON', res.status, text.slice(0, 200)); return; }
  const v = d.value || {};
  console.log('status', res.status, 'valueKeys', Object.keys(v));
  const groups = v.matchInfoList || [];
  console.log('groups', groups.length);
  for (const g of groups) {
    console.log('GROUP', g.matchNumDate, g.matchNumStr, 'subs', (g.subMatchList || []).length);
    for (const m of (g.subMatchList || [])) {
      console.log(' ', m.matchNum, m.matchNumStr, m.matchDate, m.matchTime, m.leagueAbbName || m.leagueName,
        m.homeTeamAbbName || m.homeTeam, 'vs', m.awayTeamAbbName || m.awayTeam, 'single', m.bettingSingle,
        'had', !!(m.poolList && m.poolList.some ? true : false));
    }
  }
})().catch(e => { console.error(e); process.exit(1); });
