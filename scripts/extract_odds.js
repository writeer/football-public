const fs = require('fs');
const raw = fs.readFileSync('C:\\Users\\admin\\AppData\\Local\\Temp\\trae\\toolcall-output\\9f06a4d0-72b7-4eb6-a317-96d2134fe7e6.txt', 'utf8');
const arrStart = raw.indexOf('[{');
const arrEnd = raw.lastIndexOf('}]') + 2;
const arr = JSON.parse(raw.substring(arrStart, arrEnd));
const data = JSON.parse(arr[0].text);

const output = [];
data.matches.forEach(m => {
  const match = {
    num: m.matchNumStr,
    time: m.matchTime,
    league: m.league.abbName,
    home: m.home.abbName,
    homeRank: m.home.rank,
    away: m.away.abbName,
    awayRank: m.away.rank,
    single: m.bettingSingle,
    had: m.markets.had ? m.markets.had.outcomes.map(o => ({key: o.key, odds: o.odds, noVig: o.noVigProb})) : null,
    hhad: m.markets.hhad ? {goalLine: m.markets.hhad.goalLine, outcomes: m.markets.hhad.outcomes.map(o => ({key: o.key, odds: o.odds, noVig: o.noVigProb}))} : null,
    ttg: m.markets.ttg ? m.markets.ttg.outcomes.map(o => ({key: o.key, odds: o.odds, noVig: o.noVigProb})) : null,
    hafu: m.markets.hafu ? m.markets.hafu.outcomes.map(o => ({key: o.key, odds: o.odds, noVig: o.noVigProb})) : null,
    crs: m.markets.crs ? m.markets.crs.outcomes.map(o => ({key: o.key, odds: o.odds, noVig: o.noVigProb})) : null
  };
  output.push(match);
});

fs.writeFileSync('e:\\VibeCoding\\football\\reports\\data\\20260906_sunday_odds.json', JSON.stringify(output, null, 2));
console.log('Saved odds data for', output.length, 'matches');

// Print TTG and HAFU summary for quick reference
output.forEach(m => {
  console.log(`\n[${m.num}] ${m.league} ${m.home} vs ${m.away}`);
  if (m.ttg) {
    console.log('  TTG:', m.ttg.map(t => `${t.key}=${t.odds}(${(t.noVig*100).toFixed(1)}%)`).join(' '));
  }
  if (m.hafu) {
    console.log('  HAFU:', m.hafu.slice(0,9).map(h => `${h.key}=${h.odds}`).join(' '));
  }
  if (m.crs) {
    console.log('  CRS TOP5:', m.crs.sort((a,b) => (b.noVig||0)-(a.noVig||0)).slice(0,5).map(c => `${c.key}=${c.odds}(${(c.noVig*100).toFixed(1)}%)`).join(' '));
  }
});
