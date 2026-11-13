const fs = require('fs');
let raw = fs.readFileSync('C:\\Users\\admin\\AppData\\Local\\Temp\\trae\\toolcall-output\\3325128a-e32d-43a1-b5e0-173da1aa8642.txt', 'utf8');
raw = raw.trim();
const prefix = 'The MCP server responded with: ';
if (raw.startsWith(prefix)) raw = raw.substring(prefix.length);
raw = raw.trim();
const data = JSON.parse(raw);
const json = JSON.parse(data[0].text);

// Save full odds data
fs.writeFileSync('e:\\VibeCoding\\football\\memory\\predictions\\20260828_friday\\odds_raw.json', JSON.stringify(json, null, 2), 'utf8');
console.log('Saved odds_raw.json with', json.matchCount, 'matches');
