// 回退调度器：按链依次尝试各方法，全部失败才报错。
//
// 默认回退链：mcp -> rest -> direct
// 覆盖方式：
//   --method <id>            强制只用某个方法
//   --chain a,b,c            指定回退顺序
//   环境变量 SPORTTERY_METHOD=a,b,c  全局默认回退链
//
// 每个方法返回 { success, method, data } 或 { success: false, errors: [...] }。

import { call as mcpCall } from "./mcp-client.mjs";
import { call as restCall, probe as restProbe, BASE as REST_BASE } from "./rest-client.mjs";
import { call as directCall } from "./direct.mjs";

export const METHODS = {
  mcp: { label: "MCP stdio 服务", call: mcpCall },
  rest: { label: "本地/远程 REST", call: restCall },
  direct: { label: "直接 Node 库调用", call: directCall },
};

export function defaultChain() {
  const env = process.env.SPORTTERY_METHOD;
  if (env) {
    const list = env
      .split(",")
      .map((s) => s.trim())
      .filter((s) => METHODS[s]);
    if (list.length) return list;
  }
  return ["mcp", "rest", "direct"];
}

export function resolveChain(opts = {}) {
  if (opts.method) {
    if (!METHODS[opts.method]) throw new Error(`unknown method "${opts.method}" (可用: ${Object.keys(METHODS).join(", ")})`);
    return [opts.method];
  }
  if (opts.chain) {
    const list = opts.chain
      .split(",")
      .map((s) => s.trim())
      .filter((s) => METHODS[s]);
    if (!list.length) throw new Error(`--chain 中没有可用的方法: "${opts.chain}"`);
    return list;
  }
  return defaultChain();
}

export async function dispatch(command, params, opts = {}) {
  const chain = resolveChain(opts);
  const errors = [];
  for (const m of chain) {
    try {
      const data = await METHODS[m].call(command, params);
      return { success: true, method: m, data };
    } catch (e) {
      errors.push({ method: m, error: e.message });
    }
  }
  return { success: false, errors };
}

/** 快速可用性探测（不做完整调用；完整验证用 self-test）。 */
export async function probeMethods() {
  const out = [];
  for (const id of Object.keys(METHODS)) {
    if (id === "rest") {
      out.push({ id, label: METHODS[id].label, available: await restProbe(), note: `BASE=${REST_BASE}` });
    } else if (id === "mcp") {
      out.push({ id, label: METHODS[id].label, available: true, note: "文件/依赖存在即可 spawn（实际连通性见 self-test）" });
    } else {
      out.push({ id, label: METHODS[id].label, available: true, note: "本机直连上游即可用" });
    }
  }
  return out;
}
