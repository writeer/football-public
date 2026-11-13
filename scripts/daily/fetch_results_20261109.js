// 2026-11-09 官方赛果抓取（体彩 getUniformMatchResultV1），同时确认当日是否有赛程
const fs = require('fs');

const RANGES = [['2026-11-09', '2026-11-09'], ['2026-11-08', '2026-11-09'], ['2026-11-09', '2026-11-10']];

async function fetchRange(begin, end) {
  const URL = 'https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry'
    + `?matchBeginDate=${begin}&matchEndDate=${end}&leagueId=&pageSize=100&pageNo=1&isFix=0&matchPage=1&pcOrWap=1&_=${Date.now()}`;
  const res = await fetch(URL, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
      'Accept': 'application/json, text/plain, */*',
      'Referer': 'https://www.sporttery.cn/',
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache',
    },
  });
  const buf = await res.arrayBuffer();
  const text = Buffer.from(buf).toString('utf8');
  fs.writeFileSync(`reports/data/20261109_results_${begin.replace(/-/g, '')}_${end.replace(/-/g, '')}.json`, text, 'utf8');
  let data = {};
  try { data = JSON.parse(text); } catch (e) { console.log('NON-JSON status', res.status, text.slice(0, 300)); return []; }
  const list = (data.value && (data.value.matchResult || data.value.matchResultList)) || [];
  console.log('RANGE', begin, end, 'status', res.status, 'matches', list.length, 'lastUpdate', data.value && data.value.lastUpdateTime);
  return list;
}

(async () => {
  const seen = new Map();
  for (const [b, e] of RANGES) {
    for (const m of await fetchRange(b, e)) seen.set(String(m.matchId || (m.matchNum + '_' + m.matchDate)), m);
  }
  const rows = [...seen.values()].filter(m => String(m.matchNumStr || '').includes('周日') || String(m.matchDate || '').startsWith('2026-11-09'));
  console.log('--- 11-09候选', rows.length, '---');
  for (const m of rows) {
    console.log(JSON.stringify({
      num: m.matchNum, numStr: m.matchNumStr, date: m.matchDate, time: m.matchTime,
      league: m.leagueName, home: m.homeTeam, away: m.awayTeam,
      no999: m.sectionsNo999, no1: m.sectionsNo1, goalLine: m.goalLine,
      status: m.matchStatus, resultStatus: m.matchResultStatus, single: m.bettingSingle,
    }));
  }
})().catch(e => { console.error(e); process.exit(1); });
