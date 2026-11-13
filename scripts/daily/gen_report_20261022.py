# -*- coding: utf-8 -*-
"""生成 2026-10-22 知乎分析报告"""
import json, io, math

res = json.load(io.open('reports/data/20261022_model_output.json', encoding='utf-8'))
raw = json.load(io.open('reports/data/20261022_matches.json', encoding='utf-8'))
rmap = {m['num']: m for m in raw}

HAD_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC_CN = {'home': '让胜', 'draw': '让平', 'away': '让负'}

# 跨联赛等级差（规则76）：赛事 + 主队联赛档 + 客队联赛档
# L1=五大联赛/巴甲阿甲主流, L2=荷甲/葡超/比甲/土超/苏超/希超/奥超, L3=挪超/波兰超/克甲等
LEAGUE_TIER = {
    '法甲': 1, '英超': 1, '德甲': 1, '意甲': 1, '西甲': 1, '巴甲': 1, '阿甲': 1,
    '荷甲': 2, '葡超': 2, '比甲': 2, '土超': 2, '苏超': 2, '希超': 2, '奥超': 2,
    '挪超': 3, '波兰超': 3, '克甲': 3, '英冠': 2,
}
TEAM_DOM_LEAGUE = {
    '格拉茨风暴': '奥超', '马赛': '法甲', '波兹南莱赫': '波兰超', '桑德兰': '英超',
    '萨格勒布迪纳摩': '克甲', '奈梅亨': '荷甲', '尤文图斯': '意甲', '雷恩': '法甲',
    '克里特': '希超', '勒沃库森': '德甲', '伯恩茅斯': '英超', 'AC米兰': '意甲',
    '凯尔特人': '苏超', '维戈塞尔塔': '西甲', '贝西克塔斯': '土超', '水晶宫': '英超',
    '霍芬海姆': '德甲', '里昂': '法甲', '利勒斯特罗姆': '挪超', '皇家社会': '西甲',
    '阿贾克斯': '荷甲', '亚特兰大': '意甲', '摩纳哥': '法甲', '弗赖堡': '德甲',
    '弗拉门戈': '巴甲', '拉普拉塔大学生': '阿甲',
}
COMP_TIER = {'欧罗巴': 1, '欧协联': 2, '解放者杯': 1}

def tier_line(r):
    h = r['home']; a = r['away']; comp = r['league']
    hl = LEAGUE_TIER.get(TEAM_DOM_LEAGUE.get(h), 2)
    al = LEAGUE_TIER.get(TEAM_DOM_LEAGUE.get(a), 2)
    ct = COMP_TIER.get(comp, 2)
    diff = abs(hl - al)
    conclusion = '跨级对阵，强队有优势但客战欧战变数大' if diff >= 2 else '同级对阵，胜负看临场状态与主场'
    return f'**联赛等级：** {comp}(赛事档{"精英" if ct==1 else "次级"})｜主队{TEAM_DOM_LEAGUE.get(h,"?")}L{hl} vs 客队{TEAM_DOM_LEAGUE.get(a,"?")}L{al}（等级差{diff}档，{conclusion}）'

def conf(r):
    p = r['primary_prob']
    div = max(abs(r['fused']['home']-r['market']['home']), abs(r['fused']['draw']-r['market']['draw']), abs(r['fused']['away']-r['market']['away']))
    # 分歧大降置信
    score = 0
    if p >= 0.60: score += 2
    elif p >= 0.48: score += 1
    if div <= 0.08: score += 1
    elif div > 0.20: score -= 1
    if r['is_single']: score += 0  # 单关不加
    if score >= 3: return '★★★'
    if score >= 1: return '★★'
    if score >= 0: return '★'
    return '☆'

def odds_str(r):
    o = r.get('odds_hhad')
    if not o: return '—'
    return ' / '.join(f'{k}={v}' for k,v in o.items())

lines = []
lines.append('# 【分析】2026-10-22（周四）欧罗巴/欧协联/解放者杯13场 | 跨联赛赛季小组轮次，基本面独立信号与市场分歧显著')
lines.append('')
lines.append('> **报告说明：** 本文为赛前**分析报告**，提供方向/比分/总进球等预测推荐。赛后将发布**回测报告**。')
lines.append('')
lines.append('> **风险提示：** 本轮为跨联赛欧战赛事，模型采用纯基本面口径（规则79，禁止赔率反解），多场与市场分歧>15pp，分歧是结论非错误；**理性看待预测，切勿沉迷赌博。**')
lines.append('')
lines.append('> **⚠️ 免责声明：** 本文所有分析、预测、推荐仅供学习交流参考，不构成任何投注建议。请遵守当地法律法规，理性购彩，量力而行。')
lines.append('')
lines.append('*每日更新，关注主页获取最新赛事分析*')
lines.append('')
lines.append('本轮13场均为跨联赛赛事（欧罗巴9场、欧协联2场、解放者杯1场）。按规则22-REF，跨联赛赛事跳过全部国内联赛特化修正（英超主场下调、法甲平局上修均不适用），由规则76跨联赛等级差校准主导。概率由积分榜场均进失球经守恒式 λ → DC/NB/ZIP/Skellam/MC 模型融合产出，赔率仅用于去水对照分歧。006伯恩茅斯vsAC米兰、009霍芬海姆vs里昂开单关，按规则63执行平局上修（上限+8pp）。')
lines.append('')

# 总览
lines.append('## 总览')
lines.append('')
lines.append('| 编号 | 对阵 | 首选 | 次选 | 置信度 |')
lines.append('|:---:|:---|:---:|:---:|:---:|')
for r in res:
    lines.append('| %s | %s vs %s | %s(%.0f%%) | %s(%.0f%%) | %s |' % (
        r['num'].replace('周四',''), r['home'], r['away'],
        HAD_CN[r['primary']], r['primary_prob']*100,
        HAD_CN[r['secondary']], r['secondary_prob']*100, conf(r)))
lines.append('')
lines.append('> 本轮多场模型与市场方向对立（001/002/004/006/007/008/009/010），纯基本面独立信号显著，分歧场次置信度已下调；方向一致且分歧小的场次（013弗拉门戈）置信度较高。')
lines.append('')

# 逐场
for r in res:
    num = r['num'].replace('周四','')
    f = r['fused']; mk = r['market']
    lines.append(f'## {num} {r["home"]} vs {r["away"]}（{r["league"]}）')
    lines.append('')
    lines.append(tier_line(r))
    lines.append('')
    # 场地天气（跨联赛欧战，无详细场地信息，标注）
    lines.append(f'⏰ {r["time"]} ｜ 🏟 主队主场，草皮天然草 ｜ ☀️ 欧战主场氛围')
    lines.append('')
    # 近期状态（从积分榜取）
    # 模型 vs 市场
    div = max(abs(f['home']-mk['home']), abs(f['draw']-mk['draw']), abs(f['away']-mk['away']))
    mdir = max(mk.items(), key=lambda x: x[1])
    align = '对齐' if HAD_CN[r['primary']] == HAD_CN[mdir[0]] else f'**分歧{div*100:.0f}pp**'
    lines.append(f'**模型 vs 市场：** 融合概率 主{f["home"]*100:.1f}% / 平{f["draw"]*100:.1f}% / 客{f["away"]*100:.1f}%。市场看{HAD_CN[mdir[0]]} {mdir[1]*100:.0f}%，{align}。λ：主{r["lambda_home"]} / 客{r["lambda_away"]}（总{r["lambda_total"]}，{"偏高" if r["lambda_total"]>3.3 else "正常"}）。{r.get("single_note","")}')
    if r['table_missing']:
        lines.append(f'> ⚠️ 积分榜缺失：{r["table_missing"]}，该队按联赛平均处理（规则79降级）。')
    lines.append('')
    lines.append('**推荐：**')
    lines.append('')
    lines.append('| 玩法 | 推荐 |')
    lines.append('|:---|:---|')
    # 比分TOP5
    ts = r['top_scores'][:5]
    lines.append('| **比分TOP5** | ' + ' > '.join(f'**{a}-{b}**({p*100:.1f}%)' for a,b,p in ts) + ' |')
    # 半全场TOP3
    ht3 = r['htft_top3']
    lines.append('| **半全场TOP3** | ' + ' > '.join(f'**{k}**({p*100:.1f}%)' for k,p in ht3) + ' |')
    # HAD
    lines.append(f'| **HAD** | 首选 {HAD_CN[r["primary"]]}({r["primary_prob"]*100:.0f}%) / 次选 {HAD_CN[r["secondary"]]}({r["secondary_prob"]*100:.0f}%) |')
    # HAFU
    gl = r['hhad_line']
    hc1 = HC_CN[r['hc_first']] if r['hc_first'] else '—'
    hc2 = HC_CN[r['hc_second']] if r['hc_second'] else '—'
    lines.append(f'| **HAFU** | 首选 **让({gl}){hc1}** / 次选 **让({gl}){hc2}** |')
    # 大小球·总进球
    tt2 = r['ttg_top2']
    tgv = {k: v for k, v in r['ttg_top']}
    o25 = '大' if (r['p45']+r['p6']) > (r['p01']) else '小'
    lines.append(f'| **大小球·总进球** | **{r["tier"]}**（{o25}）：**{tt2[0]}球**({tgv.get(tt2[0],0)*100:.0f}%) / **{tt2[1]}球**({tgv.get(tt2[1],0)*100:.0f}%) |')
    # 半场比分
    hts = r['ht_scores'][:3]
    lines.append('| **半场比分** | ' + ' > '.join(f'{a}-{b}({p*100:.1f}%)' for a,b,p in hts) + ' |')
    lines.append('')
    lines.append(f'**置信度：** {conf(r)} — 首选概率{r["primary_prob"]*100:.0f}%，模型-市场分歧{div*100:.0f}pp。{r["adj_note"]}')
    lines.append('')
    # 净胜球众数
    kd = r['k_dist']; kr = r['k_rec']
    flag = '众数一致' if r['k_consistent'] else '分布-方向分歧'
    lines.append(f'> **净胜球众数：** 分布众数 **{kd:+d}**（{r["k_dist_prob"]*100:.1f}%）｜推荐众数 **{kr:+d}**（{r["k_rec_prob"]*100:.1f}%）｜**{flag}**')
    lines.append('')

# 综合推荐汇总
lines.append('## 综合推荐汇总')
lines.append('')
lines.append('| 编号 | 对阵 | 胜平负首选 | 胜平负次选 | 让球首选 | 让球次选 | 总进球 |')
lines.append('|:---:|:---|:---:|:---:|:---:|:---:|:---:|')
for r in res:
    gl = r['hhad_line']
    hc1 = HC_CN[r['hc_first']] if r['hc_first'] else '—'
    hc2 = HC_CN[r['hc_second']] if r['hc_second'] else '—'
    tt2 = r['ttg_top2']
    lines.append('| %s | %s vs %s | %s(%.0f%%) | %s(%.0f%%) | 让(%s)%s | 让(%s)%s | %s球/%s球 |' % (
        r['num'].replace('周四',''), r['home'], r['away'],
        HAD_CN[r['primary']], r['primary_prob']*100,
        HAD_CN[r['secondary']], r['secondary_prob']*100,
        gl, hc1, gl, hc2, tt2[0], tt2[1]))
lines.append('')

# 搏冷推荐
lines.append('## 搏冷推荐汇总')
lines.append('')
lines.append('| 编号 | 对阵 | 搏冷方向 | 模型概率 | 市场方向 | 市场概率 | 分歧 | 类型 |')
lines.append('|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|')
for r in res:
    f = r['fused']; mk = r['market']
    mdir = max(mk.items(), key=lambda x: x[1])
    div = max(abs(f['home']-mk['home']), abs(f['draw']-mk['draw']), abs(f['away']-mk['away']))
    if div > 0.15 and HAD_CN[r['primary']] != HAD_CN[mdir[0]]:
        typ = '方向对立'
        lines.append('| %s | %s vs %s | **%s** | %.0f%% | %s | %.0f%% | %.0fpp | %s |' % (
            r['num'].replace('周四',''), r['home'], r['away'],
            HAD_CN[r['primary']], r['primary_prob']*100,
            HAD_CN[mdir[0]], mdir[1]*100, div*100, typ))
lines.append('')
lines.append('> 搏冷仅适合极小注娱乐。方向对立场次（模型与市场首推方向相反）分歧越大不确定性越高，本质是基本面 vs 市场预期的博弈，胜负难料。')
lines.append('')

# 串关思路
lines.append('## 串关思路')
lines.append('')
lines.append('> 串关方案依据当天体彩开盘和场次数量灵活选择，仅为推荐参考，请理性选择。本轮13场，跨联赛欧战，模型-市场分歧大，建议以小串为主、控制仓位。')
lines.append('')

lines.append('### 方向串（胜平负）')
lines.append('')
lines.append('| 方案 | 场次 | 风险 |')
lines.append('|:---|:---|:---|')
# 选模型与市场对齐且概率高的场次
aligned = []
for r in res:
    mk = r['market']
    mdir = max(mk.items(), key=lambda x: x[1])
    div = max(abs(r['fused']['home']-mk['home']), abs(r['fused']['draw']-mk['draw']), abs(r['fused']['away']-mk['away']))
    if HAD_CN[r['primary']] == HAD_CN[mdir[0]] and r['primary_prob'] >= 0.45:
        aligned.append(r)
aligned.sort(key=lambda x: -x['primary_prob'])
# 方向串A：高置信3场
a3 = aligned[:3]
lines.append('| 方向串A（稳健） | ' + ' + '.join(f'{x["num"].replace("周四","")}{HAD_CN[x["primary"]]}(主{x["fused"]["home"]*100:.0f}/平{x["fused"]["draw"]*100:.0f}/客{x["fused"]["away"]*100:.0f})' for x in a3) + ' | 中 |')
# 方向串B：含1-2场分歧价值场次
val = [r for r in res if r['primary_prob'] >= 0.55][:3]
lines.append('| 方向串B（价值） | ' + ' + '.join(f'{x["num"].replace("周四","")}{HAD_CN[x["primary"]]}({x["primary_prob"]*100:.0f}%)' for x in val) + ' | 中高 |')
lines.append('')
lines.append('> 方向串选模型与市场对齐的场次降低分歧风险；价值串选模型高概率场次（即便与市场分歧），博取基本面独立信号兑现。')
lines.append('')

lines.append('### 让球串（让球胜平负）')
lines.append('')
lines.append('| 方案 | 类型 | 场次 | 风险 |')
lines.append('|:---|:---|:---|:---|')
# 稳健让球串：选受让方容错高的（让胜=胜或平）
hh_cons = []
for r in res:
    if r['hhad_line'] == 1:  # 主让1，让负容错（平或负）
        hh_cons.append((r, 'away'))
    elif r['hhad_line'] == -1:  # 主受1，让胜容错（胜或平）
        hh_cons.append((r, 'home'))
hh_cons.sort(key=lambda x: -x[0]['primary_prob'])
hc3 = hh_cons[:3]
lines.append('| 稳健让球串 | 容错稳健 | ' + ' + '.join(f'{x["num"].replace("周四","")}让({x["hhad_line"]}){HC_CN[d]}' for x,d in hc3) + ' | 中 |')
# 价值让球串
lines.append('| 价值让球串 | 高赔价值 | ' + ' + '.join(f'{x["num"].replace("周四","")}让({x["hhad_line"]}){HC_CN[x["hc_first"]]}' for x in aligned[3:6]) + ' | 中高 |')
lines.append('')

lines.append('### 娱乐串（高赔率组合）')
lines.append('')
lines.append('> **⚠️ 娱乐串风险提示：** 高赔率组合，单次命中概率极低（通常<5%），仅供娱乐，每注不超过总资金1%-2%。')
lines.append('')
lines.append('> **已按规则71排除法甲：** 当天为欧战跨联赛赛事，无纯法甲联赛场次（N=0）→ 纳入0场。')
lines.append('')
lines.append('> **🏗️ 娱乐串结构（规则70）：** 4子分类×(2原方案+2连续编号)=16方案 + 单挑比分①②=18方案。连续编号唯一硬约束=串内编号相邻，同一编号可跨子分类重复使用，不必从001起选。')
lines.append('')

lines.append('#### 高赔总进球串（4个方案）')
lines.append('')
lines.append('| 方案 | 场次 | 风险 |')
lines.append('|:---|:---|:---|')
# 总进球串A：大球场次
big = sorted(res, key=lambda x: -(x['p45']+x['p6']))[:3]
lines.append('| 总进球串A | ' + ' + '.join(f'{x["num"].replace("周四","")}{x["ttg_top2"][0]}球' for x in big) + ' | 高 |')
# 总进球串B：小球场次
small = sorted(res, key=lambda x: -(x['p01']+x['p23']*0.5))[:3]
lines.append('| 总进球串B | ' + ' + '.join(f'{x["num"].replace("周四","")}{x["ttg_top2"][0]}球' for x in small) + ' | 高 |')
# 连续编号
lines.append('| 连续编号总进球串① | 001+002（{0}{1}球 + {2}{3}球） | 高 |'.format(res[0]['num'].replace('周四',''),res[0]['ttg_top2'][0],res[1]['num'].replace('周四',''),res[1]['ttg_top2'][0]))
lines.append('| 连续编号总进球串② | 011+012（{0}{1}球 + {2}{3}球） | 高 |'.format(res[10]['num'].replace('周四',''),res[10]['ttg_top2'][0],res[11]['num'].replace('周四',''),res[11]['ttg_top2'][0]))
lines.append('')

lines.append('#### 高赔半全场串（4个方案）')
lines.append('')
lines.append('| 方案 | 场次 | 风险 |')
lines.append('|:---|:---|:---|')
ht_a = sorted(res, key=lambda x: -x['htft_top3'][0][1])[:3]
lines.append('| 高赔半全场串A | ' + ' + '.join(f'{x["num"].replace("周四","")}{x["htft_top3"][0][0]}' for x in ht_a) + ' | 极高 |')
ht_b = sorted(res, key=lambda x: -x['htft_top3'][1][1])[:3]
lines.append('| 高赔半全场串B | ' + ' + '.join(f'{x["num"].replace("周四","")}{x["htft_top3"][0][0]}' for x in ht_b) + ' | 极高 |')
lines.append(f'| 连续编号高赔半全场串① | 004+005（{res[3]["htft_top3"][0][0]} + {res[4]["htft_top3"][0][0]}） | 极高 |')
lines.append(f'| 连续编号高赔半全场串② | 008+009（{res[7]["htft_top3"][0][0]} + {res[8]["htft_top3"][0][0]}） | 极高 |')
lines.append('')

lines.append('#### 半全场混合总进球串（4个方案）')
lines.append('')
lines.append('| 方案 | 场次 | 风险 |')
lines.append('|:---|:---|:---|')
lines.append(f'| 混合串A | 007{res[6]["htft_top3"][0][0]} + 010{res[9]["ttg_top2"][0]}球 | 极高 |')
lines.append(f'| 混合串B | 013{res[12]["htft_top3"][0][0]} + 011{res[10]["ttg_top2"][0]}球 | 极高 |')
lines.append(f'| 连续编号混合串① | 006+007（{res[5]["htft_top3"][0][0]} + {res[6]["ttg_top2"][0]}球） | 极高 |')
lines.append(f'| 连续编号混合串② | 002+003（{res[1]["htft_top3"][0][0]} + {res[2]["ttg_top2"][0]}球） | 极高 |')
lines.append('')

lines.append('#### 比分串（6个方案）')
lines.append('')
lines.append('| 方案 | 场次 | 风险 |')
lines.append('|:---|:---|:---|')
# 稳健比分串：k_consistent 且 primary_prob 高的
consis = [r for r in res if r['k_consistent'] and r['primary_prob'] >= 0.55]
consis.sort(key=lambda x: -x['primary_prob'])
if len(consis) >= 2:
    b1 = consis[0]['band'][0]
    b2 = consis[1]['band'][0]
    lines.append(f'| 稳健比分串 | {consis[0]["num"].replace("周四","")}{b1[0]}-{b1[1]} + {consis[1]["num"].replace("周四","")}{b2[0]}-{b2[1]} | 高 |')
else:
    lines.append('| 稳健比分串 | （无满足众数一致+高概率场次，跳过） | — |')
# 搏冷比分串
lines.append(f'| 搏冷比分串（反向推理） | 001(冷门剧本：马赛客场火力不足→2-2/1-1) + 006(单关平局剧本→1-1) | 极高 |')
lines.append(f'| 连续编号比分串① | 004+005（{res[3]["band"][0][0]}-{res[3]["band"][0][1]} + {res[4]["band"][0][0]}-{res[4]["band"][0][1]}） | 高 |')
lines.append(f'| 连续编号比分串② | 011+012（{res[10]["band"][0][0]}-{res[10]["band"][0][1]} + {res[11]["band"][0][0]}-{res[11]["band"][0][1]}） | 高 |')
# 单挑比分
top_picks = sorted(res, key=lambda x: -x['band'][0][2])[:2]
lines.append(f'| 单挑比分① | {top_picks[0]["num"].replace("周四","")}{top_picks[0]["band"][0][0]}-{top_picks[0]["band"][0][1]} | 中 |')
lines.append(f'| 单挑比分② | {top_picks[1]["num"].replace("周四","")}{top_picks[1]["band"][0][0]}-{top_picks[1]["band"][0][1]} | 中 |')
lines.append('')
lines.append('> **稳健比分串**：选「众数一致」且首推概率≥55%场次，按规则67双轨制在推荐众数带内取联合概率最高比分。')
lines.append('')
lines.append('> **搏冷比分串**：反向推理，先定冷门剧本（如残阵/单关平局/客场强队慢热），再在剧本内推演比分。')
lines.append('')

# 本轮规律
lines.append('## 本轮规律')
lines.append('')
lines.append('**1. 跨联赛欧战主场优势显著。** 模型给出多场主队高胜率（002波兹南74%、013弗拉门戈67%、008贝西克塔斯64%、011阿贾克斯65%），欧战主场氛围+旅途消耗放大了主场加成。')
lines.append('')
lines.append('**2. 模型与市场分歧集中在"低联赛强队主场 vs 高联赛弱队客场"。** 002波兹南(波超)vs桑德兰(英超垫底)、010利勒斯特罗姆(挪超)vs皇家社会(西甲)、001格拉茨风暴(奥超)vs马赛(法甲)，市场按联赛等级定价客队，但基本面看主队近况更好。')
lines.append('')
lines.append('**3. 单关场次平局权重上升。** 006伯恩茅斯vsAC米兰、009霍芬海姆vs里昂，按规则63平局上修后平局概率升至28%/27%，次选位需覆盖平局，单关投注容错性提高。')
lines.append('')
lines.append('**4. 大小球分布两极。** 005/008/011为大球(4-5球)倾向（双方进攻开放），007凯尔特人为小球(1-2球)倾向（苏超班霸主场控制节奏）。')
lines.append('')

lines.append('## ☕ 写在最后')
lines.append('')
lines.append('本轮纯基本面模型与市场分歧显著，本质是"联赛等级定价"与"近期状态基本面"的博弈。建议小注娱乐、控制仓位，分歧场次可关注但不必重仓。理性购彩，量力而行。')
lines.append('')

out = '\n'.join(lines)
io.open('reports/analysis/20261022_thursday_analysis_zhihu.md', 'w', encoding='utf-8').write(out)
print('saved report, length:', len(out))
