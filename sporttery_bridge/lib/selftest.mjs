// 全方法自测：对回退链中的每个方法跑一组代表性命令，输出逐项报告。
//
// 覆盖：
//   meta         纯计算（各方法均应通过）
//   parlay-types 纯计算
//   derive       纯计算
//   parlay       纯计算
//   matches      实时数据（依赖本机/上游连通性；失败通常 = 地域封锁或服务未起）

import { METHODS } from "./dispatch.mjs";

const CHECKS = [
  { name: "meta", params: {}, validate: (d) => d && Array.isArray(d.pools) && d.pools.length > 0 },
  { name: "parlay-types", params: { matches: 4 }, validate: (d) => d != null && (Array.isArray(d) || typeof d === "object") },
  { name: "derive", params: { odds: [1.44, 3.9, 5.6] }, validate: (d) => d && Array.isArray(d.outcomes) && d.outcomes.length === 3 && d.returnRate > 0 },
  { name: "parlay", params: { legs: [{ odds: 1.44 }, { odds: 2.1 }], multiplier: 1 }, validate: (d) => d && d.bets >= 1 && d.totalStake > 0 },
  { name: "matches", params: { pools: "had,hhad" }, validate: (d) => d && typeof d.matchCount === "number" && Array.isArray(d.matches) },
];

export async function runSelfTest(chain) {
  const report = { ranAt: new Date().toISOString(), chain, methods: {} };
  let anyOk = false;
  for (const m of chain) {
    const entry = { label: METHODS[m].label, ok: false, checks: [] };
    for (const ch of CHECKS) {
      const t0 = Date.now();
      try {
        const data = await METHODS[m].call(ch.name, ch.params);
        const pass = ch.validate ? ch.validate(data) : data != null;
        entry.checks.push({ name: ch.name, ok: pass, ms: Date.now() - t0 });
      } catch (e) {
        entry.checks.push({ name: ch.name, ok: false, ms: Date.now() - t0, error: e.message });
      }
    }
    entry.ok = entry.checks.every((c) => c.ok);
    if (entry.ok) anyOk = true;
    report.methods[m] = entry;
  }
  report.ok = anyOk;
  return report;
}
