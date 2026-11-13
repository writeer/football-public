const fs = require('fs');
const path = 'C:/Users/admin/AppData/Local/Temp/trae/toolcall-output/161a6e3e-acce-4b08-b808-0df76f9b17f4.txt';
const raw = fs.readFileSync(path, 'utf8');
const jsonStr = raw.replace(/^The MCP server responded with: /, '');
const data = JSON.parse(jsonStr);
const matches = JSON.parse(data[0].text).matches;
const result = [];
matches.forEach(m => {
  const had = m.markets.had?.outcomes || [];
  const hhad = m.markets.hhad?.outcomes || [];
  const ttg = m.markets.ttg?.outcomes || [];
  const hafu = m.markets.hafu?.outcomes || [];
  const crs = m.markets.crs?.outcomes || [];
  result.push({
    matchNum: m.matchNumStr,
    time: m.matchTime,
    weekday: m.weekday,
    league: m.league.abbName,
    leagueFull: m.league.allName,
    home: m.home.abbName,
    homeRank: m.home.rank,
    away: m.away.abbName,
    awayRank: m.away.rank,
    single: m.bettingSingle,
    allup: m.bettingAllUp,
    had: had.map(o => o.labelZh + ':' + o.odds),
    hhad: hhad.map(o => o.labelZh + ':' + o.odds),
    hhadHandicap: m.markets.hhad?.handicap,
    ttg: ttg.slice(0, 8).map(o => o.labelZh + ':' + o.odds),
    hafu: hafu.slice(0, 6).map(o => o.labelZh + ':' + o.odds),
    crs: crs.slice(0, 8).map(o => o.labelZh + ':' + o.odds)
  });
});
fs.writeFileSync('e:/VibeCoding/football/scripts/matches_summary.json', JSON.stringify(result, null, 2));
console.log('Done: ' + result.length + ' matches saved');
result.forEach(r => {
  console.log('---');
  console.log('场次: ' + r.matchNum + ' | 时间: ' + r.time + ' | ' + r.weekday);
  console.log('联赛: ' + r.league + '(' + r.leagueFull + ')');
  console.log('主队: ' + r.home + r.homeRank + ' vs 客队: ' + r.away + r.awayRank);
  console.log('单关: ' + (r.single ? '是' : '否') + ' | 串关: ' + (r.allup ? '是' : '否'));
  console.log('胜平负: ' + r.had.join(' / '));
  console.log('让球(' + r.hhadHandicap + '): ' + r.hhad.join(' / '));
  console.log('总进球: ' + r.ttg.join(' / '));
  console.log('半全场: ' + r.hafu.join(' / '));
  console.log('比分: ' + r.crs.join(' / '));
});
