const fs = require('fs');
const raw = fs.readFileSync('C:\\Users\\admin\\AppData\\Local\\Temp\\trae\\toolcall-output\\fa8d216d-9367-4ea3-90c2-59305648682e.txt', 'utf8');

const textMatch = raw.match(/"text":"([\s\S]*?)"\}\s*\]/);
if (!textMatch) {
  console.log('No text field found');
  process.exit(1);
}
const innerJson = textMatch[1].replace(/\\n/g, '').replace(/\\"/g, '"');
const m = JSON.parse(innerJson);

console.log(`${m.matchNumStr} | ${m.league.abbName} | ${m.home.abbName} vs ${m.away.abbName}`);
console.log(`Available markets: ${Object.keys(m.markets).join(', ')}`);

for (const [key, market] of Object.entries(m.markets)) {
  console.log(`\n=== ${market.poolNameZh} (${key}) ===`);
  if (market.goalLine !== undefined) console.log(`Goal line: ${market.goalLine}`);
  if (market.outcomes) {
    for (const o of market.outcomes) {
      console.log(`  ${o.labelZh}: ${o.odds} (prob: ${o.noVigProb?.toFixed(4) || 'N/A'})`);
    }
  }
}
