const fs = require('fs');
const content = fs.readFileSync('C:\\Users\\admin\\AppData\\Local\\Temp\\trae\\toolcall-output\\d132928c-5fab-4ba1-80ef-fb1dd5dbc92d.txt', 'utf8');
const jsonStart = content.indexOf('{');
const jsonEnd = content.lastIndexOf('}');
let jsonStr = content.substring(jsonStart, jsonEnd + 1);
const data = JSON.parse(jsonStr);
const tuesdayMatches = data.matches.filter(m => m.weekday === '周二');
tuesdayMatches.forEach(m => {
  const had = m.markets.had.outcomes;
  const hhad = m.markets.hhad ? m.markets.hhad.outcomes : [];
  const hhadGl = m.markets.hhad ? m.markets.hhad.goalLine : 'N/A';
  console.log(`${m.matchNumStr} | ID:${m.matchId} | ${m.league.abbName} | ${m.home.abbName} vs ${m.away.abbName} | ${m.matchTime} | Single:${m.bettingSingle} | HHAD_GL:${hhadGl} | HAD:${had[0].odds}/${had[1].odds}/${had[2].odds}`);
});
