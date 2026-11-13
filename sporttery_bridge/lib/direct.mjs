// 方式 3：直接 Node 库调用（零服务、零端口）
//
// 不启动任何进程/端口，直接 import SportteryAPI 的纯函数模块：
//   - mcp/sporttery.ts  -> fetchSporttery()  拉实时上游赔率（本机网络直连，已实测可用）
//   - src/parse.ts      -> parseUpstream()   上游原始 JSON -> 标准化 Match + 衍生指标
//   - src/derive.ts     -> deriveMarket / compareOdds / round  赔率推导、凯利
//   - src/parlay.ts     -> calcParlay / listParlayTypes       单关/过关计算
//   - src/labels.ts     -> POOL_NAME_ZH / POOL_MAX_ALLUP       玩法标签
//
// 运行要求：Node >= 22.6（TypeScript 由 node 类型擦除直接执行，
// Node >= 23.6 默认开启，其余版本需 --experimental-strip-types）。
// 输出结构与 REST 端点保持一致，方便上游切换。

import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const API_DIR = path.resolve(HERE, "..", "..", "SportteryAPI");

const ALL_POOLS = ["had", "hhad", "crs", "ttg", "hafu"];

async function load(rel) {
  const abs = path.join(API_DIR, rel);
  return import(pathToFileURL(abs).href);
}

function splitPools(csv) {
  if (!csv || !String(csv).trim()) return ["had", "hhad"];
  if (String(csv).trim().toLowerCase() === "all") return ALL_POOLS;
  return String(csv)
    .split(",")
    .map((s) => s.trim())
    .filter((s) => ALL_POOLS.includes(s));
}

/** 命令 -> 数据。params 为 CLI 规范化后的统一参数对象。 */
export async function call(command, params = {}) {
  switch (command) {
    case "matches": {
      const [sporttery, parse] = await Promise.all([
        load("mcp/sporttery.ts"),
        load("src/parse.ts"),
      ]);
      const raw = await sporttery.fetchSporttery(ALL_POOLS.join(","));
      const res = parse.parseUpstream(raw, {
        pools: splitPools(params.pools),
        date: params.date,
        league: params.league,
        matchId: params.matchId,
      });
      res.source = "direct-upstream";
      return res;
    }

    case "match": {
      const [sporttery, parse] = await Promise.all([
        load("mcp/sporttery.ts"),
        load("src/parse.ts"),
      ]);
      const raw = await sporttery.fetchSporttery(ALL_POOLS.join(","));
      const res = parse.parseUpstream(raw, { pools: ALL_POOLS, matchId: params.matchId });
      if (res.matchCount === 0) throw new Error(`match ${params.matchId} not found / not selling`);
      return res.matches[0];
    }

    case "meta": {
      const [labels, parlay] = await Promise.all([
        load("src/labels.ts"),
        load("src/parlay.ts"),
      ]);
      return {
        pools: Object.keys(labels.POOL_NAME_ZH).map((p) => ({
          code: p,
          nameZh: labels.POOL_NAME_ZH[p],
          maxAllUp: labels.POOL_MAX_ALLUP[p],
        })),
        parlay: {
          unitPriceYuan: parlay.UNIT_PRICE,
          ticketCapYuan: parlay.TICKET_CAP,
          note: "单注2元；单关=2×倍数×赔率；M串N每注=2×倍数×Π(赔率)；单张封顶500万；混合过关取最小关数(木桶原则)。",
          table: parlay.PARLAY_TABLE,
        },
        formulas: {
          impliedProb: "1 / odds",
          returnRate: "1 / Σ(1/odds)  返还率",
          noVigProb: "(1/odds) / Σ(1/odds)  去水真实概率",
          fairOdds: "1 / noVigProb  真实赔率",
          kellyIndex: "offeredOdds × referenceProb  凯利指数 (需外部参考赔率)",
          ev: "referenceProb × offeredOdds - 1",
        },
      };
    }

    case "parlay-types": {
      const parlay = await load("src/parlay.ts");
      return parlay.listParlayTypes(params.matches);
    }

    case "derive": {
      const derive = await load("src/derive.ts");
      let list;
      let keys;
      if (Array.isArray(params.odds) && params.odds.length) {
        list = params.odds;
      } else if (params.h != null && params.d != null && params.a != null) {
        list = [params.h, params.d, params.a];
        keys = ["home", "draw", "away"];
      } else {
        throw new Error("derive: provide {odds:[...]} or {h,d,a}");
      }
      if (list.length < 2 || list.some((o) => !Number.isFinite(o) || o <= 1)) {
        throw new Error("derive: need at least 2 decimal odds, each > 1");
      }
      const d = derive.deriveMarket(list);
      return {
        overround: derive.round(d.overround, 6),
        returnRate: derive.round(d.returnRate, 6),
        returnRatePct: derive.round(d.returnRate * 100, 3),
        margin: derive.round(d.margin, 6),
        outcomes: d.perOutcome.map((o, i) => ({
          key: keys?.[i] ?? String(i),
          odds: o.odds,
          impliedProb: derive.round(o.impliedProb, 6),
          noVigProb: derive.round(o.noVigProb, 6),
          fairOdds: derive.round(o.fairOdds, 4),
        })),
      };
    }

    case "value": {
      const derive = await load("src/derive.ts");
      if (
        !Array.isArray(params.offered) ||
        !Array.isArray(params.reference) ||
        params.offered.length !== params.reference.length ||
        params.offered.length < 2
      ) {
        throw new Error("value: offered/reference must be equal-length arrays (>= 2)");
      }
      const analyses = derive.compareOdds(params.offered, params.reference);
      const outcomes = analyses.map((a, i) => ({
        label: params.labels?.[i] ?? String(i),
        odds: a.odds,
        refProb: derive.round(a.refProb, 6),
        kelly: derive.round(a.kelly, 4),
        ev: derive.round(a.ev, 4),
        kellyFraction: derive.round(a.kellyFraction, 4),
        isValue: a.isValue,
      }));
      const best = analyses
        .map((a, i) => ({ i, kelly: a.kelly }))
        .sort((x, y) => y.kelly - x.kelly)[0];
      return { outcomes, bestValue: best ? best.i : null };
    }

    case "parlay": {
      const parlay = await load("src/parlay.ts");
      return parlay.calcParlay(params);
    }

    default:
      throw new Error(`direct: unknown command "${command}"`);
  }
}
