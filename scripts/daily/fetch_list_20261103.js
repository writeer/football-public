// 2026-11-03（周二）在售赛程抓取（体彩 getUniformMatchListV1）
const fs = require('fs');

const BEGIN = process.argv[2] || '2026-11-03';
const END = process.argv[3] || '2026-11-04';
const URL = 'https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchListV1.qry'
  + `?matchBeginDate=${BEGIN}&matchEndDate=${END}&pageSize=100&pageNo=1&isFix=0&matchPage=1&pcOrWap=1&_=${Date.now()}`;

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
  fs.writeFileSync('reports/data/20261103_list_raw.json', text, 'utf8');
  const data = JSON.parse(text);
  const list = (data.value && (data.value.matchInfoList || data.value.matchList)) || [];
  console.log('status', res.status, 'matches', list.length);
  for (const m of list) {
    const markets = m.markets || {};
    const hadO = markets.had && markets.had.outcomes;
    const had = hadO ? hadO.map(o => `${o.key}:${o.odds}`).join(' ') : 'noHAD';
    const gline = markets.hhad ? markets.hhad.goalLine : 'noHHAD';
    console.log(JSON.stringify({
      num: m.matchNumStr,
      numDate: m.matchNumDate,
      league: (m.league && (m.league.abbName || m.league.allName)) || '',
      home: m.home && (m.home.allName || m.home.teamName) || '',
      away: m.away && (m.away.allName || m.away.teamName) || '',
      homeRank: m.home && m.home.rank || '',
      awayRank: m.away && m.away.rank || '',
      time: m.matchTime,
      date: m.matchDate,
      single: m.bettingSingle,
      allup: m.bettingAllUp,
      goalLine: gline,
      had,
    }));
  }
  console.log('saved reports/data/20261103_list_raw.json');
}
main().catch(e => { console.error(e); process.exit(1); });
