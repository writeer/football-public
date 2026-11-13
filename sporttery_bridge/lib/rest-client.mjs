// 方式 2/4：REST 客户端
//
// 默认指向本地 wrangler dev（http://127.0.0.1:8787，无需鉴权）；
// 通过环境变量可切换：
//   REST_BASE  线上 Cloudflare Worker 地址（方式 4，需 UPSTREAM_PROXY 才能拿到实时赔率）
//   API_KEY    配置了鉴权时携带（Authorization: Bearer <key>）
//
// 端点（与 SportteryAPI/src/index.ts 对应）：
//   GET  /api/matches?pools=&date=&league=&matchId=
//   GET  /api/match/:matchId
//   GET  /api/meta
//   GET  /api/parlay/types?matches=
//   POST /api/derive   {odds:[...]} | {h,d,a}
//   POST /api/value    {offered, reference, labels?}
//   POST /api/parlay   {legs, passType?, folds?, multiplier?}

const BASE = (process.env.REST_BASE || "http://127.0.0.1:8787").replace(/\/+$/, "");
const KEY = process.env.API_KEY || "";

async function req(method, pathname, body, timeoutMs = 60000) {
  const headers = { Accept: "application/json" };
  if (KEY) headers.Authorization = `Bearer ${KEY}`;
  const init = { method, headers, signal: AbortSignal.timeout(timeoutMs) };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  const res = await fetch(BASE + pathname, init);
  let json = null;
  try {
    json = await res.json();
  } catch {
    /* non-JSON body */
  }
  if (!res.ok || (json && json.success === false)) {
    throw new Error(
      `rest ${method} ${pathname} -> HTTP ${res.status}${json?.error ? ": " + json.error : ""}`,
    );
  }
  return json?.data ?? json;
}

/** 命令 -> 数据。params 为 CLI 规范化后的统一参数对象。 */
export async function call(command, params = {}) {
  switch (command) {
    case "matches": {
      const q = new URLSearchParams();
      if (params.pools) q.set("pools", params.pools);
      if (params.date) q.set("date", params.date);
      if (params.league) q.set("league", params.league);
      if (params.matchId != null) q.set("matchId", String(params.matchId));
      const s = q.toString();
      return req("GET", "/api/matches" + (s ? "?" + s : ""));
    }

    case "match":
      if (params.matchId == null) throw new Error("rest match: need matchId");
      return req("GET", `/api/match/${params.matchId}`);

    case "meta":
      return req("GET", "/api/meta");

    case "parlay-types": {
      const s = params.matches != null ? `?matches=${params.matches}` : "";
      return req("GET", "/api/parlay/types" + s);
    }

    case "derive": {
      const body = Array.isArray(params.odds)
        ? { odds: params.odds }
        : { h: params.h, d: params.d, a: params.a };
      return req("POST", "/api/derive", body);
    }

    case "value":
      return req("POST", "/api/value", {
        offered: params.offered,
        reference: params.reference,
        ...(params.labels ? { labels: params.labels } : {}),
      });

    case "parlay":
      return req("POST", "/api/parlay", params);

    default:
      throw new Error(`rest: unknown command "${command}"`);
  }
}

/** 探活：GET /health（不抛错，返回是否可用）。 */
export async function probe(timeoutMs = 3000) {
  try {
    const res = await fetch(`${BASE}/health`, { signal: AbortSignal.timeout(timeoutMs) });
    return res.ok;
  } catch {
    return false;
  }
}

export { BASE };
