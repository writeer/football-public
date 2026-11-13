// 2026-10-28 赛果抓取：体彩官方 getUniformMatchResultV1（唯一权威源）
const fs = require('fs');

const RANGE = [['2026-10-28', '2026-10-29'], ['2026-10-29', '2026-10-29']];

async function pull(begin, end) {
  const url = `https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry?matchBeginDate=${begin}&matchEndDate=${end}&leagueId=&pageSize=100&pageNo=1&isFix=0&matchPage=1&pcOrWap=1`;
  const res = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0', Referer: 'https://www.sporttery.cn/' } });
  const buf = Buffer.from(await res.arrayBuffer());
  const j = JSON.parse(buf.toString('utf8'));
  return j?.value?.matchResult || [];
}

(async () => {
  const seen = new Map();
  for (const [b, e] of RANGE) {
    const list = await pull(b, e);
    for (const r of list) {
      const num = r.matchNumStr;
      if (!num.startsWith('周三')) continue;          // 只要 10-28 周三这一期
      seen.set(r.matchId, r);
    }
  }
  const out = [...seen.values()].map(r => ({
    num: r.matchNumStr,
    league: r.leagueNameAbbr,
    home: r.homeTeam,
    away: r.awayTeam,
    date: r.matchDate,
    kickoff: r.matchTime,
    ft: r.sectionsNo999 || null,
    ht: r.sectionsNo1 || null,
    line: r.goalLine,
    win_flag: r.winFlag,
    status: r.matchResultStatus,
    match_id: r.matchId,
    source: '体彩官方 getUniformMatchResultV1（/gateway/uniform/football/）'
  })).sort((a, b) => a.num.localeCompare(b.num));

  fs.writeFileSync('reports/data/20261028_results_official.json', JSON.stringify(out, null, 1), 'utf8');
  console.log('count', out.length);
  for (const r of out) console.log([r.num, r.league, r.home, r.away, r.ht, r.ft, r.line, r.win_flag, r.status].join(' | '));
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
