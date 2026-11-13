const fs = require('fs');
const data = JSON.parse(fs.readFileSync('e:\\VibeCoding\\football\\reports\\data\\20260908_monday_odds.json', 'utf8'));
for (const m of data.matches) {
  console.log(`${m.matchNumStr} ${m.matchId} ${m.league.abbName} ${m.home.abbName} vs ${m.away.abbName}`);
}
