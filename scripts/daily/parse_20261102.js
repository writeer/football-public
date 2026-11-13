// 解析 2026-11-02 体彩原始数据（sporttery_bridge 归一化格式）→ matches.json
import fs from 'fs';

let rawStr = fs.readFileSync('reports/data/20261102_raw.json', 'utf8');
if (rawStr.charCodeAt(0) === 0xFEFF) rawStr = rawStr.slice(1);
const raw = JSON.parse(rawStr);
const groups = raw.matches || (raw.data && raw.data.matches) || [];

const matches = [];
for (const g of groups) {
  if (g.matchNumDate !== '261102') continue;
  const m = g.markets || {};
  const match = {
    num: g.matchNumStr,
    league: g.league.abbName,
    home: g.home.allName,
    away: g.away.allName,
    home_rank: (g.home.rank || '').replace(/[\[\]]/g, ''),
    away_rank: (g.away.rank || '').replace(/[\[\]]/g, ''),
    time: g.matchTime || '',
    match_date: g.matchDate || '',
    betting_single: !!g.bettingSingle,
    betting_allup: !!g.bettingAllUp,
  };
  const pick = (pool) => (m[pool] && m[pool].outcomes ? m[pool].outcomes.map(o => ({ key: o.key, odds: o.odds, noVig: o.noVigProb })) : null);
  const had = pick('had'); if (had) match.had = had;
  const hhad = pick('hhad'); if (hhad) match.hhad = { goalLine: m.hhad.goalLine, outcomes: hhad };
  const ttg = pick('ttg'); if (ttg) match.ttg = ttg;
  const hafu = pick('hafu'); if (hafu) match.hafu = hafu;
  const crs = pick('crs'); if (crs) match.crs = crs;
  matches.push(match);
}

fs.writeFileSync('reports/data/20261102_matches.json', JSON.stringify(matches, null, 2), 'utf8');
console.log(`Parsed ${matches.length} matches`);
for (const x of matches) {
  const had_s = x.had ? `H${x.had.find(o => o.key === 'home')?.odds} D${x.had.find(o => o.key === 'draw')?.odds} A${x.had.find(o => o.key === 'away')?.odds}` : 'noHAD';
  const hhad_s = x.hhad ? `(gl${x.hhad.goalLine})` : '';
  console.log(`  ${x.num} ${x.league} ${x.home}[${x.home_rank}] vs ${x.away}[${x.away_rank}] ${x.time} ${had_s} ${hhad_s} 单关=${x.betting_single}`);
}
