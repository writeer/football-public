# Trae Work 手动添加 SportteryAPI MCP 服务教程

> **想省事/要迁移**：本仓库已提供 [`football_mcp/`](../football_mcp/README.md) 模块，集中登记 6 个足球 MCP 服务、
> 全程使用相对路径（不含任何本机绝对路径），并提供 CLI / Python / Node 三套直调接口。
> 新增环境或换电脑时优先用它：`node football_mcp/bin/football-mcp.mjs print-config`。
> 本文保留作为单服务（sporttery-odds）手工配置的参考。

## 一、前置条件

- Node.js >= 20.0.0（需支持 `--experimental-strip-types`）
- SportteryAPI 项目已就位在本仓库的 `SportteryAPI/` 子目录
- 依赖已安装（在 `SportteryAPI/` 内执行 `npm install`）

验证命令：
```powershell
node --version
# 应输出 v20.x.x 或更高
```

## 二、SportteryAPI MCP 服务部署状态

| 项目 | 状态 |
|:---|:---|
| 代码克隆 | ✅ 已完成（本仓库 `SportteryAPI/` 子目录） |
| 依赖安装 | ✅ `node_modules` 已就绪 |
| Smoke 测试 | ✅ 7个工具全部可用 |
| 实时数据测试 | ✅ 25场周六比赛全玩法赔率获取成功 |

## 三、Trae Work 手动添加 MCP 服务（详细步骤）

### 步骤1：打开 Trae Work 设置

1. 在 Trae Work 界面中，点击左下角设置图标（齿轮 ⚙️）
2. 或使用快捷键 `Ctrl + ,` 打开设置
3. 在左侧导航栏中找到 **MCP** 或 **Model Context Protocol** 选项

### 步骤2：手动添加 stdio 类型 MCP 服务

1. 在 MCP 设置页面，点击 **「手动添加」** 或 **「Add Server」** 按钮
2. 选择服务类型为 **stdio**
3. 填写以下配置信息：

| 字段 | 值 |
|:---|:---|
| 服务名称 | `sporttery-odds` |
| 服务类型 | stdio |
| 命令 | `node` |
| 参数 | `--no-warnings --experimental-strip-types SportteryAPI/mcp/server.ts`（相对仓库根） |
| 工作目录 | 仓库根目录（若客户端要求填，填仓库根；参数里已带 `SportteryAPI/` 前缀） |

### 步骤3：JSON 配置方式（替代方案）

如果 Trae Work 支持直接编辑 JSON 配置，添加以下内容到 MCP 配置文件：

```json
{
  "mcpServers": {
    "sporttery-odds": {
      "command": "node",
      "args": ["--no-warnings", "--experimental-strip-types", "SportteryAPI/mcp/server.ts"]
    }
  }
}
```

> **路径写法**：一律用相对仓库根的路径，仓库可随意迁移；不要写 `E:\...` 这类绝对路径。
> 只有当客户端确实不支持相对路径时，才用 `node football_mcp/bin/football-mcp.mjs print-config --resolve` 临时生成本机绝对路径版（生成物不入库）。

### 步骤4：验证 MCP 服务连接

添加完成后，Trae Work 会自动尝试连接 MCP 服务。验证方法：

1. 在 MCP 服务列表中，`sporttery-odds` 应显示为 **已连接** 状态
2. 点击服务名称，应能看到 7 个可用工具：
   - `get_matches` — 获取当日全部竞彩场次及赔率
   - `get_match` — 按matchId获取单场全玩法赔率
   - `derive_odds` — 赔率推导（返还率/去水概率/公平赔率）
   - `compare_value` — 凯利指数/价值对比
   - `calc_parlay` — 单关/过关奖金计算
   - `list_parlay_types` — 过关方式对照表
   - `get_meta` — 玩法/公式参考

### 步骤5：在对话中使用 MCP 工具

连接成功后，在 Trae Work 对话中可以直接调用：

```
# 获取当日全部场次（含全玩法赔率）
Agent 会自动调用 get_matches 工具

# 获取特定日期场次
调用 get_matches，参数 date="260815"，pools="had,hhad,crs,ttg,hafu"

# 获取单场详细赔率
调用 get_match，参数 matchId=2040864

# 计算串关奖金
调用 calc_parlay，参数 legs=[{odds:1.5},{odds:2.3},{odds:1.8}], passType="3串1", multiplier=1
```

## 四、MCP 工具能力详解

### 4.1 get_matches — 获取竞彩场次

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| pools | string (可选) | 逗号分隔：had,hhad,crs,ttg,hafu（默认 had,hhad） |
| date | string (可选) | 日期过滤，格式 YYMMDD，如 260815 |
| league | string (可选) | 联赛名过滤，如 "英超" |
| matchId | number (可选) | 单场过滤 |

返回数据包含：
- 场次编号（周六001等）
- 球队名称（中文缩写）
- 5类赔率完整数据
- 返还率/去水概率/公平赔率（推导值）
- 赔率走势（涨/平/跌）

### 4.2 calc_parlay — 串关奖金计算

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| legs | array | 选中场次列表，每项含 odds(赔率) 和可选 result(win/lose/void) |
| passType | string (可选) | "单关" 或 "M串N" 标签如 "3串1" |
| folds | array (可选) | 显式指定组合数，如 [2,3] |
| multiplier | int (可选) | 倍数（默认1） |

返回数据包含：
- 注数
- 总投注额
- 最大奖金
- 实际奖金（根据result）
- 500万封顶标记

### 4.3 derive_odds — 赔率推导

输入一组赔率，返回：
- 总概率
- 返还率
- 庄家利润
- 每个选项的隐含概率/去水概率/公平赔率

## 五、第二个 MCP 服务：公共托管体育 MCP（可选）

用户提到的第二个服务为境外数据源（外围赔率），有两个选择：

### 5.1 InferSports MCP（远程 HTTP MCP）

| 项目 | 说明 |
|:---|:---|
| 类型 | 远程 HTTP MCP |
| 数据 | 亚盘、欧赔 |
| 适用 | 外围赔率参考 |
| 网络要求 | 国内连通性一般，可能需要代理 |

添加方式：在 Trae Work MCP 设置中选择「远程/HTTP」类型，填入服务URL。

### 5.2 betbetter-mcp（本地模型推算）

| 项目 | 说明 |
|:---|:---|
| 类型 | 本地 MCP |
| 数据 | 模型推算公平赔率（非真实机构数据） |
| 适用 | 仅作参考，不含实时赔率 |

> **建议**：SportteryAPI 已能获取全部5类体彩官方赔率，满足分析需求。外围赔率参考价值有限，可暂不部署第二个MCP，优先确保 SportteryAPI 稳定运行。

## 六、故障排查

### 问题1：MCP 服务无法连接

```powershell
# 手动启动 MCP 服务测试（命令在仓库根目录执行）
cd SportteryAPI
node --no-warnings --experimental-strip-types mcp/server.ts
# 应看到 "[sporttery-odds] MCP server ready (stdio)"
```

### 问题2：获取数据失败（上游不可达）

上游 sporttery.cn API 被限流或网络异常时：
- MCP 服务会返回 Error
- 可设置代理：环境变量 `SPORTTERY_PROXY` 或 `HTTPS_PROXY`

### 问题3：Node 版本不兼容

`--experimental-strip-types` 需要 Node.js >= 20.0.0
```powershell
node --version
# 如版本过低，升级 Node.js
```

## 七、数据验证结果（2026-08-15 测试）

| 指标 | 结果 |
|:---|:---|
| 测试时间 | 2026-08-15 深夜 |
| 获取场次 | 25场周六比赛 |
| HAD（胜平负） | 24/25场有数据 |
| HHAD（让球胜平负） | 25/25场有数据 |
| CRS（比分） | 25/25场有数据（每场31个比分赔率） |
| TTG（总进球） | 25/25场有数据（每场8个选项） |
| HAFU（半全场） | 25/25场有数据（每场9个选项） |

> **结论**：11点后所有赔率全部可获取，不存在"未开售"情况。之前标注"未开售"是数据源问题，现已通过 MCP 服务彻底解决。
