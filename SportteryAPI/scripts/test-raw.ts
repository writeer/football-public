import { fetchSporttery } from "../mcp/sporttery.ts";
import { writeFileSync } from "node:fs";

console.log("Fetching raw sporttery data...");
const raw = await fetchSporttery("had,hhad,crs,ttg,hafu", { cache: false });

const groups = raw?.value?.matchInfoList ?? [];
console.log(`Total date groups: ${groups.length}`);

for (const g of groups) {
  const subMatches = g.subMatchList ?? [];
  const matchNumDate = g.matchNumDate;
  console.log(`\nDate: ${matchNumDate} (${subMatches.length} matches)`);

  for (const sm of subMatches.slice(0, 3)) {
    console.log(`  ${sm.matchNumStr} ${sm.homeTeamAbbName} vs ${sm.awayTeamAbbName}`);
    console.log(`    had: ${JSON.stringify(sm.had)?.slice(0, 200)}`);
    console.log(`    hhad: ${JSON.stringify(sm.hhad)?.slice(0, 200)}`);
    console.log(`    crs: ${JSON.stringify(sm.crs)?.slice(0, 200)}`);
    console.log(`    ttg: ${JSON.stringify(sm.ttg)?.slice(0, 200)}`);
    console.log(`    hafu: ${JSON.stringify(sm.hafu)?.slice(0, 200)}`);
  }
  if (subMatches.length > 3) console.log(`  ... and ${subMatches.length - 3} more`);
}

writeFileSync("e:/VibeCoding/football/sat_raw_debug.json", JSON.stringify(raw, null, 2));
console.log("\nSaved raw data to sat_raw_debug.json");
