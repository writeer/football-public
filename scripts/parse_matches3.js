const fs = require('fs');
const content = fs.readFileSync('C:\\Users\\admin\\AppData\\Local\\Temp\\trae\\toolcall-output\\d132928c-5fab-4ba1-80ef-fb1dd5dbc92d.txt', 'utf8');
console.log('Content length:', content.length);
console.log('First 300 chars:', content.substring(0, 300));

// Try to find JSON directly
const jsonStart = content.indexOf('{');
console.log('First { at:', jsonStart);

// Try parsing from the first {
try {
  const sub = content.substring(jsonStart);
  const data = JSON.parse(sub);
  console.log('Parsed! Keys:', Object.keys(data));
  if (data.matches) {
    const tm = data.matches.filter(m => m.weekday && m.weekday.includes('002'));
    console.log('Tuesday matches count:', data.matches.filter(m => m.weekday === '周二').length);
  }
} catch(e) {
  console.log('Direct parse failed:', e.message.substring(0, 100));
  // Maybe it's the MCP response format
  const mcpMatch = content.match(/MCP server responded with:\s*(.+)$/s);
  if (mcpMatch) {
    console.log('Found MCP response, length:', mcpMatch[1].length);
    try {
      const arr = JSON.parse(mcpMatch[1]);
      console.log('Parsed array, length:', arr.length);
      if (arr[0] && arr[0].text) {
        const innerData = JSON.parse(arr[0].text);
        console.log('Inner data keys:', Object.keys(innerData));
        const tm = innerData.matches.filter(m => m.weekday === '周二');
        console.log('Tuesday matches:', tm.length);
        tm.forEach(m => {
          const had = m.markets.had.outcomes;
          const hhadGl = m.markets.hhad ? m.markets.hhad.goalLine : 'N/A';
          console.log(`${m.matchNumStr} | ID:${m.matchId} | ${m.league.abbName} | ${m.home.abbName} vs ${m.away.abbName} | ${m.matchTime} | Single:${m.bettingSingle} | HHAD_GL:${hhadGl} | HAD:${had[0].odds}/${had[1].odds}/${had[2].odds}`);
        });
      }
    } catch(e2) {
      console.log('MCP parse failed:', e2.message.substring(0, 200));
    }
  }
}
