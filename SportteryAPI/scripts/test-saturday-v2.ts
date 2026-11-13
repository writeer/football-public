import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { writeFileSync } from "node:fs";

const transport = new StdioClientTransport({
  command: "node",
  args: ["--no-warnings", "--experimental-strip-types", "mcp/server.ts"],
});
const client = new Client({ name: "sat-test-v2", version: "1.0.0" });
await client.connect(transport);

console.log("Fetching Saturday matches with ALL pools...");
const result = await client.callTool({
  name: "get_matches",
  arguments: { pools: "had,hhad,crs,ttg,hafu", date: "260815" },
});

const raw = result.content?.[0]?.text ?? "{}";
const data = JSON.parse(raw);

console.log(`Total matches returned: ${data.matchCount}`);
const satMatches = (data.matches || []).filter((m: any) => m.matchNumStr?.includes("周六"));
console.log(`Saturday matches: ${satMatches.length}`);

const simplified = satMatches.map((m: any) => {
  const mk = m.markets || {};
  return {
    matchNumStr: m.matchNumStr,
    matchId: m.matchId,
    home: m.home?.abbName,
    away: m.away?.abbName,
    league: m.league?.abbName,
    had: mk.had?.outcomes?.map((o: any) => ({ label: o.labelZh, odds: o.odds })) ?? [],
    hhad: {
      goalLine: mk.hhad?.goalLine,
      outcomes: mk.hhad?.outcomes?.map((o: any) => ({ label: o.labelZh, odds: o.odds })) ?? [],
    },
    crs: mk.crs?.outcomes?.map((o: any) => ({ label: o.labelZh, odds: o.odds })) ?? [],
    ttg: mk.ttg?.outcomes?.map((o: any) => ({ label: o.labelZh, odds: o.odds })) ?? [],
    hafu: mk.hafu?.outcomes?.map((o: any) => ({ label: o.labelZh, odds: o.odds })) ?? [],
  };
});

let allComplete = 0;
for (const m of simplified) {
  const hasAll = m.had.length > 0 && m.hhad.outcomes.length > 0 && m.crs.length > 0 && m.ttg.length > 0 && m.hafu.length > 0;
  if (hasAll) allComplete++;
  console.log(`${m.matchNumStr} ${m.home} vs ${m.away} | HAD:${m.had.length} HHAD:${m.hhad.outcomes.length} CRS:${m.crs.length} TTG:${m.ttg.length} HAFU:${m.hafu.length} ${hasAll ? "OK" : "MISSING"}`);
}
console.log(`\nComplete (all 5 pools): ${allComplete}/${satMatches.length}`);

if (simplified.length > 0) {
  const s = simplified[0];
  console.log(`\n--- Sample: ${s.matchNumStr} ${s.home} vs ${s.away} ---`);
  console.log(`HAD: ${s.had.map((o: any) => `${o.label}=${o.odds}`).join(" / ")}`);
  console.log(`HHAD (goalLine=${s.hhad.goalLine}): ${s.hhad.outcomes.map((o: any) => `${o.label}=${o.odds}`).join(" / ")}`);
  console.log(`CRS (top 5): ${s.crs.slice(0, 5).map((o: any) => `${o.label}=${o.odds}`).join(" / ")}`);
  console.log(`TTG: ${s.ttg.map((o: any) => `${o.label}=${o.odds}`).join(" / ")}`);
  console.log(`HAFU: ${s.hafu.map((o: any) => `${o.label}=${o.odds}`).join(" / ")}`);
}

writeFileSync("e:/VibeCoding/football/sat_odds_full.json", JSON.stringify(simplified, null, 2));
console.log(`\nSaved ${simplified.length} matches to sat_odds_full.json`);

await client.close();
console.log("Done.");
