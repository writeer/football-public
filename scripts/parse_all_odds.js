const fs = require('fs');
const path = require('path');

const files = {
  '001': '32ed3dcf-fe06-4b36-ad47-af8a5999315d.txt',
  '002': '23506b28-1dd1-422b-8eb1-6e45bb2b1649.txt',
  '003': '904489e6-9ea8-416e-9541-4a0b010f7f16.txt',
  '004': '8959038b-17a2-438a-93ef-f55141591f7d.txt',
  '005': 'b076e883-bbc9-47b7-8586-f57f993a9982.txt',
  '006': 'e2416433-a471-4445-8801-393c912c6c95.txt',
  '007': '0c3abe7b-e611-46ac-9cf3-75739a5c7115.txt',
  '008': '5a687ba9-cf2d-4a0e-9fef-4bb35fac8889.txt',
  '009': '57cfdd6f-720d-4056-b1cb-65fc48be7c25.txt',
  '010': 'bb7e9849-2847-4d7e-8d48-60d8a904c9d0.txt',
  '011': 'dd0c9632-f408-4414-bcfb-6f4583bc2f7b.txt',
  '012': '5669ad03-967b-447d-bcc1-64cae3ba4e6f.txt',
};

const baseDir = 'C:\\Users\\admin\\AppData\\Local\\Temp\\trae\\toolcall-output\\';

function parseMatch(file) {
  const content = fs.readFileSync(path.join(baseDir, file), 'utf8');
  const mcpMatch = content.match(/MCP server responded with:\s*(.+)$/s);
  if (!mcpMatch) return null;
  const arr = JSON.parse(mcpMatch[1]);
  const data = JSON.parse(arr[0].text);

  const result = {
    num: data.matchNumStr,
    league: data.league.abbName,
    home: data.home.abbName,
    away: data.away.abbName,
    time: data.matchTime,
    hhad: data.markets.hhad ? data.markets.hhad.goalLine : 'N/A',
    had: {},
    ttg: {},
    crs: {},
    hafu: {}
  };

  // HAD
  if (data.markets.had) {
    result.had = {
      h: data.markets.had.outcomes[0].odds,
      d: data.markets.had.outcomes[1].odds,
      a: data.markets.had.outcomes[2].odds
    };
  }

  // HHAD
  if (data.markets.hhad) {
    result.hhad_odds = {
      h: data.markets.hhad.outcomes[0].odds,
      d: data.markets.hhad.outcomes[1].odds,
      a: data.markets.hhad.outcomes[2].odds
    };
  }

  // TTG
  if (data.markets.ttg) {
    result.ttg = data.markets.ttg.outcomes.map(o => ({
      key: o.key,
      odds: o.odds
    }));
  }

  // CRS - top 10 by lowest odds
  if (data.markets.crs) {
    const sorted = [...data.markets.crs.outcomes].sort((a, b) => a.odds - b.odds);
    result.crs = sorted.slice(0, 10).map(o => ({
      key: o.key,
      odds: o.odds
    }));
  }

  // HAFU - top 6 by lowest odds
  if (data.markets.hafu) {
    const sorted = [...data.markets.hafu.outcomes].sort((a, b) => a.odds - b.odds);
    result.hafu = sorted.slice(0, 6).map(o => ({
      key: o.key,
      odds: o.odds
    }));
  }

  return result;
}

for (const [num, file] of Object.entries(files)) {
  try {
    const r = parseMatch(file);
    if (r) {
      console.log(`\n=== ${r.num} ${r.league} ${r.home} vs ${r.away} (${r.time}) ===`);
      console.log(`HHAD让球: ${r.hhad}`);
      console.log(`HAD: ${r.had.h}/${r.had.d}/${r.had.a}`);
      if (r.hhad_odds) console.log(`HHAD: ${r.hhad_odds.h}/${r.hhad_odds.d}/${r.hhad_odds.a}`);
      if (r.ttg.length) console.log(`TTG: ${r.ttg.map(t => `${t.key}(${t.odds})`).join(', ')}`);
      if (r.crs.length) console.log(`CRS TOP10: ${r.crs.map(c => `${c.key}(${c.odds})`).join(', ')}`);
      if (r.hafu.length) console.log(`HAFU TOP6: ${r.hafu.map(h => `${h.key}(${h.odds})`).join(', ')}`);
    }
  } catch(e) {
    console.log(`Error parsing ${num}: ${e.message.substring(0, 80)}`);
  }
}
