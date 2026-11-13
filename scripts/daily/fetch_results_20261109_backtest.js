// 2026-11-09 分析报告 4 场英锦标赛赛果核对（体彩 getUniformMatchResultV1 官方接口）
const fs = require('fs');

const RANGES = [
  ['2026-11-10', '2026-11-10'],
  ['2026-11-11', '2026-11-11'],
  ['2026-11-12', '2026-11-12'],
  ['2026-11-10', '2026-11-12'],
];

const TARGETS = [
  { num: '周二001', home: '伯顿', away: '诺茨郡' },
  { num: '周二002', home: '布罗姆利', away: '米尔顿' },
  { num: '周三005', home: '谢周三', away: '阿克宁顿' },
  { num: '周三006', home: '巴恩斯利', away: '奥德汉姆' },
];

async function fetchRange(begin, end) {
  const URL = 'https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry'
    + `?matchBeginDate=${begin}&matchEndDate=${end}&leagueId=&pageSize=200&pageNo=1&isFix=0&matchPage=1&pcOrWap=1&_=${Date.now()}`;
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
  fs.writeFileSync(`reports/data/20261109_bt_results_${begin.replace(/-/g, '')}_${end.replace(/-/g, '')}.json`, text, 'utf8');
  let data = {};
  try { data = JSON.parse(text); } catch (e) { console.log('NON-JSON', begin, end, res.status, text.slice(0, 200)); return []; }
  const list = (data.value && (data.value.matchResult || data.value.matchResultList)) || [];
  console.log('RANGE', begin, end, 'status', res.status, 'matches', list.length, 'lastUpdate', data.value && data.value.lastUpdateTime);
  return list;
}

(async () => {
  const seen = new Map();
  for (const [b, e] of RANGES) {
    for (const m of await fetchRange(b, e)) {
      seen.set(String(m.matchId || (m.matchNumStr + '_' + m.matchDate)), m);
    }
  }
  const all = [...seen.values()];
  console.log('TOTAL unique', all.length);
  console.log('--- 4场目标核对 ---');
  for (const t of TARGETS) {
    const hits = all.filter(m => String(m.matchNumStr || '').replace(/\d{3}$/, '') === t.num.slice(0, -3)
      && String(m.homeTeam || '').includes(t.home) && String(m.awayTeam || '').includes(t.away));
    const exact = all.filter(m => String(m.matchNumStr || '') === t.num);
    const pool = exact.length ? exact : hits;
    if (!pool.length) { console.log(t.num, t.home, 'vs', t.away, '=> 未在赛果接口出现'); continue; }
    for (const m of pool) {
      console.log(JSON.stringify({
        target: t.num, numStr: m.matchNumStr, num: m.matchNum, date: m.matchDate, time: m.matchTime,
        league: m.leagueName, home: m.homeTeam, away: m.awayTeam,
        no999: m.sectionsNo999, no1: m.sectionsNo1, goalLine: m.goalLine,
        status: m.matchStatus, resultStatus: m.matchResultStatus, single: m.bettingSingle,
      }));
    }
  }
  console.log('--- 周二/周三编号全量（含未开赛） ---');
  for (const m of all) {
    const s = String(m.matchNumStr || '');
    if (!s.startsWith('周二') && !s.startsWith('周三')) continue;
    console.log(JSON.stringify({
      numStr: s, date: m.matchDate, time: m.matchTime, league: m.leagueName,
      home: m.homeTeam, away: m.awayTeam, no999: m.sectionsNo999, no1: m.sectionsNo1,
      goalLine: m.goalLine, status: m.matchStatus, resultStatus: m.matchResultStatus, single: m.bettingSingle,
    }));
  }
})().catch(e => { console.error(e); process.exit(1); });
