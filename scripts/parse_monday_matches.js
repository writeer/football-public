const fs = require('fs');
const raw = fs.readFileSync('C:\\Users\\admin\\AppData\\Local\\Temp\\trae\\toolcall-output\\49528fdf-c1ca-4eaa-9ccb-724878d4f701.txt', 'utf8');

const textMatch = raw.match(/"text":"([\s\S]*?)"\}\s*\]/);
if (!textMatch) {
  console.log('No text field found');
  process.exit(1);
}
const innerJson = textMatch[1].replace(/\\n/g, '').replace(/\\"/g, '"');
const data = JSON.parse(innerJson);

console.log(`Updated: ${data.updatedAt}, Matches: ${data.matchCount}`);
console.log('========================================\n');

for (const m of data.matches) {
  console.log(`${m.matchNumStr} | ${m.league.abbName} | ${m.home.abbName} vs ${m.away.abbName}`);
  console.log(`  日期: ${m.matchDate} ${m.matchTime} | 单关: ${m.bettingSingle}`);
  
  // HAD
  if (m.markets.had) {
    const h = m.markets.had.outcomes;
    console.log(`  HAD: 主胜${h[0].odds} 平${h[1].odds} 客胜${h[2].odds}`);
  }
  
  // HHAD
  if (m.markets.hhad) {
    const hh = m.markets.hhad.outcomes;
    console.log(`  HHAD: 让球${m.markets.hhad.goalLine} | 让胜${hh[0].odds} 让平${hh[1].odds} 让负${hh[2].odds}`);
  }
  
  // CRS
  if (m.markets.crs) {
    const crs = m.markets.crs.outcomes.slice(0, 8);
    console.log(`  CRS TOP8: ${crs.map(c => c.label + c.odds).join(' / ')}`);
  }
  
  // TTG
  if (m.markets.ttg) {
    const ttg = m.markets.ttg.outcomes;
    console.log(`  TTG: ${ttg.map(t => t.label + t.odds).join(' / ')}`);
  }
  
  // HAFU
  if (m.markets.hafu) {
    const hafu = m.markets.hafu.outcomes.slice(0, 6);
    console.log(`  HAFU TOP6: ${hafu.map(h => h.label + h.odds).join(' / ')}`);
  }
  
  console.log('');
}

// Save parsed data
fs.writeFileSync('e:\\VibeCoding\\football\\reports\\data\\20260908_monday_odds.json', JSON.stringify(data, null, 2));
console.log('Data saved to 20260908_monday_odds.json');
