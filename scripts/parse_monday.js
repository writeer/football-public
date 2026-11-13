const d = require('../reports/data/monday_260928_matches.json');
d.data.matches.forEach(m => {
  const h = m.markets.had.outcomes;
  const hh = m.markets.hhad.outcomes;
  console.log(`${m.matchNumStr} | ${m.league.abbName} | ${m.home.abbName} vs ${m.away.abbName} | ${m.matchTime} | HAD: ${h[0].odds}/${h[1].odds}/${h[2].odds} | HHAD(${m.markets.hhad.goalLine}): ${hh[0].odds}/${hh[1].odds}/${hh[2].odds} | 单关:${m.bettingSingle}`);
});
console.log(`\n总场次: ${d.data.matchCount}`);
console.log(`更新时间: ${d.data.updatedAt}`);
