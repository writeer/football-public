// 2026-11-02 周一 9场 官方赛果抓取（体彩 getUniformMatchResultV1）
const fs = require('fs');

const DATE = process.argv[2] || '2026-11-02';
const URL = 'https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry'
  + `?matchBeginDate=${DATE}&matchEndDate=${DATE}&leagueId=&pageSize=30&pageNo=1&isFix=0&matchPage=1&pcOrWap=1&_=${Date.now()}`;

async function main() {
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
  fs.writeFileSync(`reports/data/${DATE.replace(/-/g, '')}_results_official_raw.json`, text, 'utf8');
  const data = JSON.parse(text);
  const list = (data.value && (data.value.matchResult || data.value.matchResultList)) || [];
  console.log('status', res.status, 'matches', list.length, 'lastUpdate', data.value && data.value.lastUpdateTime);
  for (const m of list) {
    const sec = {};
    for (const s of (m.sectionsNo1 || '').split(',')) sec[1] = m.sectionsNo1;
    console.log(JSON.stringify({
      num: m.matchNum,
      league: m.leagueName,
      home: m.homeTeam,
      away: m.awayTeam,
      sectionsNo999: m.sectionsNo999,
      sectionsNo1: m.sectionsNo1,
      goalLine: m.goalLine,
      matchResult: m.matchResult,
      had: m.had,
      hhad: m.hhad,
      status: m.matchStatus,
      time: m.matchDate + ' ' + m.matchTime,
    }));
  }
  console.log('saved reports/data/20261102_results_official_raw.json');
}
main().catch(e => { console.error(e); process.exit(1); });
