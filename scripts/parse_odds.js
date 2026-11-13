const fs = require('fs');
const ids = [2041740, 2041741, 2041742, 2041743, 2041744, 2041745, 2041746, 2041747];
const out = {};
for (const id of ids) {
  const raw = fs.readFileSync(`reports/data/monday_m${id}.json`, 'utf8').replace(/^\uFEFF/, '');
  const d = JSON.parse(raw);
  const m = d.data;
  const rec = { num: m.matchNumStr, home: m.home.abbName, away: m.away.abbName, league: m.league.abbName, single: m.bettingSingle };
  const pools = m.markets;
  rec.had = {};
  if (pools.had) pools.had.outcomes.forEach(o => rec.had[o.labelZh] = o.odds);
  rec.hhad = { goalLine: pools.hhad ? pools.hhad.goalLine : null, odds: {} };
  if (pools.hhad) pools.hhad.outcomes.forEach(o => rec.hhad.odds[o.labelZh] = o.odds);
  rec.ttg = {};
  if (pools.ttg) pools.ttg.outcomes.forEach(o => rec.ttg[o.labelZh] = o.odds);
  rec.hafu = {};
  if (pools.hafu) pools.hafu.outcomes.forEach(o => rec.hafu[o.labelZh] = o.odds);
  rec.crs = {};
  if (pools.crs) pools.crs.outcomes.forEach(o => rec.crs[o.labelZh] = o.odds);
  out[rec.num] = rec;
}
fs.writeFileSync('reports/data/monday_odds_parsed.json', JSON.stringify(out, null, 2), 'utf8');
for (const k in out) {
  const r = out[k];
  console.log(`\n=== ${r.num} ${r.home}vs${r.away} (${r.league})${r.single ? ' [单关]' : ''} ===`);
  console.log(`HHAD(${r.hhad.goalLine}):`, JSON.stringify(r.hhad.odds));
  console.log(`TTG:`, JSON.stringify(r.ttg));
  console.log(`HAFU:`, JSON.stringify(r.hafu));
  console.log(`CRS:`, JSON.stringify(r.crs));
}
