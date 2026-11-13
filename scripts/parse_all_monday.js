const fs = require('fs');

const files = {
  '001': 'fa8d216d-9367-4ea3-90c2-59305648682e',
  '002': 'f3ad7ef6-b746-4b2c-ae8e-6cd8df01175a',
  '003': 'a9d9f1ff-883d-40eb-8d71-bb1458a662bb',
  '004': '4988c8f0-7593-4c4e-8228-77e1a7dcfed0',
  '005': '400afc08-efae-4e7b-b838-1469c0534724',
  '006': '5b5886d6-04ec-4828-8c8f-b6a2c1077c1e',
  '007': 'c6963c1b-8392-4cdb-b21a-bda0f7961116',
  '008': '337ce4e3-fe56-4425-9b7f-982ee8d9b32d',
  '009': 'c31e6904-6e2d-44f6-b002-16d30d83166d',
};

const allMatches = {};

for (const [num, fileId] of Object.entries(files)) {
  const raw = fs.readFileSync(`C:\\Users\\admin\\AppData\\Local\\Temp\\trae\\toolcall-output\\${fileId}.txt`, 'utf8');
  const textMatch = raw.match(/"text":"([\s\S]*?)"\}\s*\]/);
  if (!textMatch) {
    console.log(`${num}: No text field found`);
    continue;
  }
  const innerJson = textMatch[1].replace(/\\n/g, '').replace(/\\"/g, '"');
  const m = JSON.parse(innerJson);
  
  const summary = {
    matchNum: m.matchNumStr,
    league: m.league.abbName,
    home: m.home.abbName,
    away: m.away.abbName,
    homeRank: m.home.rank,
    awayRank: m.away.rank,
    date: m.matchDate,
    time: m.matchTime,
    bettingSingle: m.bettingSingle,
  };
  
  // HAD
  if (m.markets.had) {
    const h = m.markets.had.outcomes;
    summary.had = {
      h: h[0].odds, hProb: h[0].noVigProb,
      d: h[1].odds, dProb: h[1].noVigProb,
      a: h[2].odds, aProb: h[2].noVigProb
    };
  }
  
  // HHAD
  if (m.markets.hhad) {
    const hh = m.markets.hhad.outcomes;
    summary.hhad = {
      goalLine: m.markets.hhad.goalLine,
      h: hh[0].odds, hProb: hh[0].noVigProb,
      d: hh[1].odds, dProb: hh[1].noVigProb,
      a: hh[2].odds, aProb: hh[2].noVigProb
    };
  }
  
  // CRS - top 8
  if (m.markets.crs) {
    summary.crs = m.markets.crs.outcomes.map(c => ({
      label: c.labelZh, odds: c.odds, prob: c.noVigProb
    })).sort((a, b) => b.prob - a.prob).slice(0, 10);
  }
  
  // TTG
  if (m.markets.ttg) {
    summary.ttg = m.markets.ttg.outcomes.map(t => ({
      label: t.labelZh, odds: t.odds, prob: t.noVigProb
    }));
  }
  
  // HAFU - top 6
  if (m.markets.hafu) {
    summary.hafu = m.markets.hafu.outcomes.map(h => ({
      label: h.labelZh, odds: h.odds, prob: h.noVigProb
    })).sort((a, b) => b.prob - a.prob);
  }
  
  allMatches[num] = summary;
  
  // Print summary
  console.log(`\n=== ${summary.matchNum} | ${summary.league} | ${summary.home} vs ${summary.away} ===`);
  console.log(`  ${summary.date} ${summary.time} | 单关:${summary.bettingSingle}`);
  console.log(`  HAD: 主${summary.had.h}(${(summary.had.hProb*100).toFixed(1)}%) 平${summary.had.d}(${(summary.had.dProb*100).toFixed(1)}%) 客${summary.had.a}(${(summary.had.aProb*100).toFixed(1)}%)`);
  console.log(`  HHAD: 让${summary.hhad.goalLine} 让胜${summary.hhad.h}(${(summary.hhad.hProb*100).toFixed(1)}%) 让平${summary.hhad.d}(${(summary.hhad.dProb*100).toFixed(1)}%) 让负${summary.hhad.a}(${(summary.hhad.aProb*100).toFixed(1)}%)`);
  console.log(`  CRS TOP5: ${summary.crs.slice(0,5).map(c => `${c.label}@${c.odds}(${(c.prob*100).toFixed(1)}%)`).join(' / ')}`);
  console.log(`  TTG: ${summary.ttg.map(t => `${t.label}@${t.odds}(${(t.prob*100).toFixed(1)}%)`).join(' / ')}`);
  console.log(`  HAFU TOP5: ${summary.hafu.slice(0,5).map(h => `${h.label}@${h.odds}(${(h.prob*100).toFixed(1)}%)`).join(' / ')}`);
}

// Save
fs.writeFileSync('e:\\VibeCoding\\football\\reports\\data\\20260908_monday_all_odds.json', JSON.stringify(allMatches, null, 2));
console.log('\n\nAll data saved to 20260908_monday_all_odds.json');
