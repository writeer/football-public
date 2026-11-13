const fs = require('fs');
const content = fs.readFileSync('C:\\Users\\admin\\AppData\\Local\\Temp\\trae\\toolcall-output\\d132928c-5fab-4ba1-80ef-fb1dd5dbc92d.txt', 'utf8');
// The file content from MCP has format: "The MCP server responded with: [{"type":"text","text":"{ JSON }"}]"
// Need to extract the inner JSON from the text field
const textMatch = content.match(/"text":"([\s\S]+?)"\s*}\s*\]/);
if (!textMatch) {
  // Try direct JSON parse
  const jsonStart = content.indexOf('{');
  const jsonEnd = content.lastIndexOf('}');
  let jsonStr = content.substring(jsonStart, jsonEnd + 1);
  // Check if it starts with "updatedAt"
  console.log('First 200 chars of extracted JSON:', jsonStr.substring(0, 200));
  // Try to find the actual match data JSON
  const matchIdx = jsonStr.indexOf('"matches"');
  console.log('matches index:', matchIdx);
  try {
    const data = JSON.parse(jsonStr);
    console.log('Parsed keys:', Object.keys(data));
    console.log('Type of matches:', typeof data.matches);
  } catch(e) {
    console.log('Parse error:', e.message);
    // The text might be escaped JSON within the MCP response
    // Try to find the text field content
    const textStart = content.indexOf('"text":"{');
    if (textStart > 0) {
      const innerStart = content.indexOf('{', textStart + 7);
      // Find the matching closing brace
      let braceCount = 0;
      let endIdx = innerStart;
      for (let i = innerStart; i < content.length; i++) {
        if (content[i] === '{') braceCount++;
        if (content[i] === '}') braceCount--;
        if (braceCount === 0) {
          endIdx = i;
          break;
        }
      }
      let innerJson = content.substring(innerStart, endIdx + 1);
      // Unescape
      innerJson = innerJson.replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\\\/g, '\\');
      const data2 = JSON.parse(innerJson);
      const tuesdayMatches = data2.matches.filter(m => m.weekday === '周二');
      tuesdayMatches.forEach(m => {
        const had = m.markets.had.outcomes;
        const hhad = m.markets.hhad ? m.markets.hhad.outcomes : [];
        const hhadGl = m.markets.hhad ? m.markets.hhad.goalLine : 'N/A';
        console.log(`${m.matchNumStr} | ID:${m.matchId} | ${m.league.abbName} | ${m.home.abbName} vs ${m.away.abbName} | ${m.matchTime} | Single:${m.bettingSingle} | HHAD_GL:${hhadGl} | HAD:${had[0].odds}/${had[1].odds}/${had[2].odds}`);
      });
    }
  }
}
