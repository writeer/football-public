import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { writeFileSync } from "node:fs";

const transport = new StdioClientTransport({
  command: "node",
  args: ["--no-warnings", "--experimental-strip-types", "mcp/server.ts"],
});
const client = new Client({ name: "sat-test", version: "1.0.0" });
await client.connect(transport);

console.log("Fetching Saturday matches with ALL pools (had,hhad,crs,ttg,hafu)...");

const result = await client.callTool({
  name: "get_matches",
  arguments: { pools: "had,hhad,crs,ttg,hafu", date: "260815" },
});

const raw = result.content?.[0]?.text ?? "{}";
const data = JSON.parse(raw);

console.log(`\nTotal matches: ${data.matchCount}`);

let satMatches: any[] = [];
if (data.matches) {
  satMatches = data.matches.filter((m: any) => m.matchNumStr?.includes("周六"));
}

console.log(`Saturday matches: ${satMatches.length}`);

let fullOddsCount = 0;
let missingPools: Record<string, string[]> = {};

for (const m of satMatches) {
  const pools = ["had", "hhad", "crs", "ttg", "hafu"];
  const missing = pools.filter((p) => !m[p] || (Array.isArray(m[p]) && m[p].length === 0));
  if (missing.length > 0) {
    missingPools[m.matchNumStr] = missing;
  } else {
    fullOddsCount++;
  }
}

console.log(`\nMatches with ALL 5 pools: ${fullOddsCount}/${satMatches.length}`);
if (Object.keys(missingPools).length > 0) {
  console.log("Matches with missing pools:");
  for (const [matchNum, pools] of Object.entries(missingPools)) {
    console.log(`  ${matchNum}: missing ${pools.join(", ")}`);
  }
} else {
  console.log("All Saturday matches have complete 5-pool odds data!");
}

if (satMatches.length > 0) {
  console.log("\n--- Sample: First Saturday Match ---");
  const sample = satMatches[0];
  console.log(`${sample.matchNumStr} ${sample.home?.abbName} vs ${sample.away?.abbName}`);
  console.log(`  HAD: ${JSON.stringify(sample.had?.map((o: any) => `${o.label}=${o.odds}`).join(" / "))}`);
  console.log(`  HHAD: ${JSON.stringify(sample.hhad)}`);
  console.log(`  CRS: ${sample.crs?.length ?? 0} entries`);
  console.log(`  TTG: ${sample.ttg?.length ?? 0} entries`);
  console.log(`  HAFU: ${sample.hafu?.length ?? 0} entries`);
}

const simplified = satMatches.map((m: any) => ({
  matchNumStr: m.matchNumStr,
  matchId: m.matchId,
  home: m.home?.abbName,
  away: m.away?.abbName,
  league: m.leagueName,
  had: m.had,
  hhad: m.hhad,
  crs: m.crs,
  ttg: m.ttg,
  hafu: m.hafu,
}));

writeFileSync("e:/VibeCoding/football/sat_odds_full.json", JSON.stringify(simplified, null, 2));
console.log(`\nSaved ${simplified.length} matches to sat_odds_full.json`);

await client.close();
console.log("\nDone.");
