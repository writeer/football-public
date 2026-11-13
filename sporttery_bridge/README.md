# sporttery_bridge — SportteryAPI 统一调用桥

> 版本: 1.0.0 | 更新: 2026-08-21
> 把 `../SportteryAPI`（体彩竞彩足球赔率服务）的 **4 种调用方式** 统一封装，带回退链：
> **mcp → rest → direct**（一种不可用自动尝试下一种），供主项目（lottery_agent / 各子 Agent）调用。

---

## 一、为什么需要这个桥

SportteryAPI 本身提供多种访问形态，但各有可用条件：

| 方式 | 形态 | 可用条件 | 失败典型原因 |
|:---|:---|:---|:---|
| **1. mcp** | MCP stdio 服务（`mcp/server.ts`，7 工具） | Node ≥ 22.6、依赖已装、本机可访问上游 | SDK 缺失、Node 版本过低 |
| **2. rest** | 本地 REST（`wrangler dev` → `http://127.0.0.1:8787`） | 服务进程在跑 | 服务未启动、端口占用 |
| **3. direct** | 直接 Node 库调用（零服务零端口） | Node ≥ 22.6、本机可访问上游 | 上游地域封锁（返回 567） |
| **4. remote** | 线上 Cloudflare Worker（`REST_BASE` 指向 workers.dev） | 已部署、`UPSTREAM_PROXY` 已配 | 未部署、地域封锁、无代理中继 |

桥只实现 **1/2/3** 三种本地方法 + **4（remote）通过 `REST_BASE` 复用 rest 客户端**。
默认回退链 `mcp,rest,direct`；可用 `--method` / `--chain` / 环境变量 `SPORTTERY_METHOD` 覆盖。

设计原则：**统一入参、统一出参（JSON）、自动回退**。调用方永远只面对一个 CLI / 一个 Python 函数。

---

## 二、目录结构

```
sporttery_bridge/
├── README.md               ← 本文件
├── package.json            ← npm scripts（cli / self-test / methods / matches）
├── bin/
│   └── sporttery.mjs       ← 统一 CLI（命令解析 + 输出 JSON）
├── lib/
│   ├── dispatch.mjs        ← 回退链调度（mcp→rest→direct）+ 可用性探测
│   ├── mcp-client.mjs      ← 方式1：MCP stdio JSON-RPC 客户端（零依赖实现）
│   ├── rest-client.mjs     ← 方式2/4：REST 客户端（REST_BASE 可切本地/线上）
│   ├── direct.mjs          ← 方式3：直接 import SportteryAPI 纯函数模块
│   └── selftest.mjs        ← 全方法自测
├── python/
│   └── sporttery_client.py ← Python 封装（推荐 lottery_agent 使用）
└── .gitignore
```

依赖关系：`bin/sporttery.mjs → dispatch → {mcp-client, rest-client, direct}`。
`direct.mjs` 直接引用 `../SportteryAPI/` 的源码模块（无构建步骤）。

---

## 三、统一 CLI 用法

运行需 Node ≥ 22.6（TypeScript 由 node 类型擦除直接执行）：

```powershell
cd sporttery_bridge      # 相对仓库根；也可直接在仓库根用 sporttery_bridge/bin/sporttery.mjs
npm run cli -- <command> [options] [--method <id> | --chain a,b,c]
# 等价：node --no-warnings --experimental-strip-types bin/sporttery.mjs <command> ...
```

所有命令输出 `{"success": true, "method": "mcp|rest|direct", "data": {...}}` 到 stdout；
全部方法失败输出 `{"success": false, "errors": [...]}`，退出码 2。

### 命令一览

| 命令 | 用途 | 示例 |
|:---|:---|:---|
| `matches` | 最新赔率 + 衍生指标 | `matches --pools had,hhad,crs,ttg,hafu --date 260821 --league 英超` |
| `match <id>` | 按 matchId 取单场（全玩法） | `match 123456` |
| `meta` | 玩法标签 / 过关表 / 公式 | `meta` |
| `parlay-types` | M串N 对照表 | `parlay-types --matches 4` |
| `derive` | 赔率推导（去水概率/返还率） | `derive --odds 1.44,3.9,5.6` 或 `derive --h 1.44 --d 3.9 --a 5.6` |
| `value` | 凯利指数 / 价值对比 | `value --offered 2.1,3.4,3.8 --reference 2.0,3.5,4.0 --labels 主胜,平,主负` |
| `parlay` | 单关/过关奖金计算 | `parlay --body-file body.json`（body 含中文时务必用文件，Windows 命令行会乱码） |
| `self-test` | 全方法自测报告 | `self-test` 或 `self-test --chain mcp,rest,direct` |
| `methods` | 快速可用性探测 | `methods` |

### 常用环境变量

| 变量 | 默认 | 含义 |
|:---|:---|:---|
| `SPORTTERY_METHOD` | `mcp,rest,direct` | 默认回退链 |
| `REST_BASE` | `http://127.0.0.1:8787` | REST 目标；指向线上 Worker 即启用方式 4 |
| `API_KEY` | 空 | 服务端开启鉴权时携带 |

---

## 四、Python 用法（推荐主项目使用）

```python
import sys
from pathlib import Path

# 不写死绝对路径：脚本在仓库根下用相对路径，子目录里则相对本文件定位
sys.path.insert(0, str(Path("sporttery_bridge/python").resolve()))
# sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sporttery_bridge" / "python"))

from sporttery_client import get_matches, derive, calc_parlay, meta, parlay_types, value, self_test

# 拉全部场次全玩法赔率（规则15：5类赔率必须收集）
res = get_matches(pools="had,hhad,crs,ttg,hafu")
print(res["matchCount"], res["source"], res["matches"][0]["matchNumStr"])

# 赔率推导（去水概率）
d = derive(odds=[1.44, 3.90, 5.60])
print(d["returnRatePct"], d["outcomes"])

# 串关奖金
p = calc_parlay([{"odds": 1.44, "label": "周五001 主胜"}, {"odds": 2.10, "label": "周五002 客胜"}], pass_type="2串1")
print(p["bets"], p["totalStake"], p["maxPayoutCapped"])

# 强制指定方法 / 自定义回退链
get_matches(method="direct")                    # 只走直接库调用
get_matches()                                   # 默认 mcp->rest->direct 回退
self_test(chain="rest,direct")                  # 只看某两个方法的自测
```

命令行直跑：`python python/sporttery_client.py matches --pools had,hhad,crs,ttg,hafu`

---

## 五、自测与验收

```powershell
cd sporttery_bridge
npm run self-test
```

`self-test` 对回退链中**每个方法**逐项执行 5 个代表性命令：
`meta` / `parlay-types` / `derive` / `parlay`（纯计算，各方法都应通过）+ `matches`（实时数据，依赖上游连通）。
输出每项 通过/失败 + 耗时；报告含 `ok` 汇总。退出码：至少一个方法全过 = 0，否则 2。

> REST 方法的 `matches` 依赖 `wrangler dev` 在 8787 端口运行（`cd ../SportteryAPI && npm run dev`）。

---

## 六、故障排查速查

| 现象 | 原因 | 处理 |
|:---|:---|:---|
| `mcp server exited` / SDK import 失败 | node_modules 缺失 | `cd ../SportteryAPI && npm install` |
| `--experimental-strip-types` 报错 | Node < 22.6 | 升级 Node |
| REST `HTTP 502` | 上游地域封锁（Worker 场景） | 本地跑 mcp/direct，或给 Worker 配 `UPSTREAM_PROXY` |
| REST `ECONNREFUSED` | 8787 未启动 | `cd ../SportteryAPI && npm run dev` |
| `sporttery upstream HTTP 567` | 本机到 webapi 被 WAF 拦截 | 换网络/配代理（`SPORTTERY_PROXY`） |
| 中文 body 乱码 | Windows 命令行代码页 | 一律用 `--body-file`（Python 封装已自动处理） |
| 全部方法失败 | 网络/依赖/服务全挂 | `npm run self-test` 看逐项失败原因 |

---

## 七、与主项目集成（AGENTS.md 同步见主文档）

- **信息收集器**：`get_matches(pools="had,hhad,crs,ttg,hafu")` 采集全部场次 5 类赔率（规则15/58/59）
- **信息审核核查器**：`derive()` / `value()` 校验赔率、推导去水概率与返还率
- **串关优化器**：`calc_parlay()` / `parlay_types()` 计算过关奖金与玩法组合（规则47/49/55/56）
- 每次分析前建议跑一次 `self-test` 确认当前可用方法，失败时按回退链自动降级，无需人工干预
