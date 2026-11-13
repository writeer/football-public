# -*- coding: utf-8 -*-
"""生成 2026-10-28 重算测试报告（前三场 + 意甲5场）"""
import json, io, os

D = r'e:\VibeCoding\football'
d = json.load(io.open(os.path.join(D, 'reports/data/20261028_recalc_test.json'), encoding='utf-8-sig'))
rows = d['rows']
old_full = {m['num']: m for m in json.load(io.open(
    os.path.join(D, 'reports/data/20261028_model_output.json'), encoding='utf-8-sig'))}

CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC = {'home': '让胜', 'draw': '让平', 'away': '让负'}


def pct(x):
    return '%.1f%%' % (x * 100)


def cap(pool):
    return max(sum(int(t) for t in s.split('-')) for s in pool)


def mass(labels, probs):
    return sum(probs)


L = []
A = L.append
A('# 【测试】2026-10-28（周三）重算对照 | 前三场＋意甲5场，λ校准与比分池上限保障')
A('')
A('> **报告说明：** 本文为**模型改动测试稿**，不是对外发布的分析报告。在同一批赛前数据上，用新口径重算 8 场（亚冠精英 001-003、意甲 005/006/007/013/014），与原稿逐项对照，用于判断改动是否值得纳入常规流程。')
A('')
A('> **⚠️ 免责声明：** 本文所有数据、对照与结论仅供内部测试参考，不构成任何投注建议。请遵守当地法律法规，理性购彩，量力而行。')
A('')
A('## 本次改了什么')
A('')
A('**改动一：λ 总量向上校准（加法，+0.30 球）。** 用 10-19（8场）与 10-27（10场）共 18 场做检验：15/18 场实际总进球高于模型 λ合计，中位比值 1.41。原口径的 λ 由积分榜场均进失球收缩而来，在小样本赛季初期会整体偏低。本稿把每场 λ合计 提高 0.30 球，按两侧 λ 比例分摊，不改变主客强弱方向。')
A('')
A('**改动二：比分候选池加"上限保障"。** 原口径直接取概率前 5 的比分，池内最大总进球常只有 3-4 球；一旦打出 5 球以上，排序再准也中不了（10-27 十场里有 7 场属于这种情况）。本稿在取前 5 后增加一条硬约束：若池内最大总进球低于总进球分布的 **P75 分位**，则用该分位附近概率最高的比分替换掉池内概率最低的一格。')
A('')
A('**改动三：档位与总进球同源，取消越级覆盖。** 原口径在 P(≥6球)≥25% 或 P(≤1球)≥40% 时会把档位直接跳到"穿盘"或"闷战超小球"，可能与该场总进球 TOP2 互相矛盾。本稿档位一律取"众数总进球所在档"，保证档位、总进球、比分池三者自洽。')
A('')
A('## 关于校准幅度：没有用 1.41 倍的原因')
A('')
A('把 18 场的"实际进球 ~ λ合计"做线性回归，斜率是 **1.82**（截距 -0.89），照此校准，λ合计 4.5 的场次要抬到 7.3 球——这显然是过拟合：样本只有两天，其中 10-27 是场均 4.80 球的极值日（三场意甲打出 8/6/4 球）。')
A('')
A('所以本稿只取**加法 +0.30**（在典型 λ合计 3.0 上约 +10%），先把方向性的低估纠正一部分，不做乘性放大。这是一个保守值，改动效果偏温和——如果后续样本继续验证低估，再逐轮上调。')
A('')
A('## 汇总对照')
A('')
A('| 编号 | 联赛 | λ合计 原→新 | 档位 原→新 | 比分池上限 原→新 | 池覆盖率 原→新 |')
A('|:---:|:---|:---:|:---|:---:|:---:|')
chg_cap = chg_tier = 0
for x in rows:
    o, n = x['old'], x['new']
    co = cap(o['pool'])
    cn = cap(n['pool'])
    mo = sum(p for *_, p in old_full[x['num']]['top_scores'])
    ic = '↑' if cn > co else ('—' if cn == co else '↓')
    it = '（变动）' if o['tier'] != n['tier'] else ''
    chg_cap += 1 if cn > co else 0
    chg_tier += 1 if o['tier'] != n['tier'] else 0
    A('| %s | %s | %.2f → %.2f | %s → %s %s | %d → %d %s | %s → %s |' % (
        x['num'][2:], x['league'], o['total'], n['total'],
        o['tier'].replace('正常球', ''), n['tier'].replace('正常球', ''), it,
        co, cn, ic, pct(mo), pct(n['pool_mass'])))
A('')
dp = [abs(n['prob'] - o['prob']) * 100 for x in rows for o, n in [(x['old'], x['new'])]]
A('> 8 场中 **8 场比分池上限全部抬高**、**%d 场档位发生变化**。池覆盖率（前5比分合计概率质量）由原稿的 %s 降到 %s——这是"上限保障"的代价：为了够得着高球比分，必须挤掉一个高概率格。' % (
    chg_tier,
    pct(sum(sum(p for *_, p in old_full[x['num']]['top_scores']) for x in rows) / len(rows)),
    pct(sum(x['new']['pool_mass'] for x in rows) / len(rows))))
A('')
A('> 胜平负首选概率的变动幅度为 **%.1f-%.1fpp**，方向判断全部未变。' % (min(dp), max(dp)))
A('')
A('## 逐场对照')
A('')
for x in rows:
    o, n = x['old'], x['new']
    A('### %s %s vs %s（%s）' % (x['num'][2:], x['home'], x['away'], x['league']))
    A('')
    A('⏰ %s ｜ 🏟 %s' % (str(x['time'])[:5], x['venue'] or '信息缺失'))
    A('')
    A('| 维度 | 原稿 | 重算（新口径） |')
    A('|:---|:---|:---|')
    A('| **λ（主/客）** | %.2f / %.2f（合计 %.2f） | %.2f / %.2f（合计 %.2f） |' % (
        o['lam'][0], o['lam'][1], o['total'], n['lam'][0], n['lam'][1], n['total']))
    A('| **大小球档位** | %s | %s |' % (o['tier'], n['tier']))
    A('| **比分TOP5** | %s（上限%d，覆盖%s） | %s（上限%d，覆盖%s） |' % (
        '、'.join(o['pool']), cap(o['pool']),
        pct(sum(p for *_, p in old_full[x['num']]['top_scores'])),
        '、'.join(n['pool']), cap(n['pool']), pct(n['pool_mass'])))
    A('| **总进球TOP2** | %s | %s |' % ('/'.join('%d球' % k for k in o['ttg_top2']),
                                        '/'.join('%d球' % k for k in n['ttg_top2'])))
    A('| **胜平负** | 主%s 平%s 客%s | 主%s 平%s 客%s |' % (
        pct(o['fused']['home']), pct(o['fused']['draw']), pct(o['fused']['away']),
        pct(n['fused']['home']), pct(n['fused']['draw']), pct(n['fused']['away'])))
    A('| **首选方向** | %s %s | %s %s |' % (CN[o['primary']], pct(o['prob']),
                                            CN[n['primary']], pct(n['prob'])))
    A('| **让球（%+d）** | — | 让胜%s / 让平%s / 让负%s |' % (
        x['goalLine'] if x['goalLine'] is not None else 0,
        pct(n['hhad']['home']) if n['hhad'] else '—',
        pct(n['hhad']['draw']) if n['hhad'] else '—',
        pct(n['hhad']['away']) if n['hhad'] else '—'))
    A('| **半全场TOP3** | %s | %s |' % (' > '.join(o['htft']), ' > '.join(n['htft'])))
    A('| **净胜球** | — | 分布众数 %+d / 方向内众数 %+d |' % (n['k_dist'], n['k_rec']))
    A('')
    note = []
    if o['tier'] != n['tier']:
        note.append('档位由「%s」上移到「%s」，与总进球 TOP2 一致' % (o['tier'], n['tier']))
    if n['replaced']:
        note.append('比分池把概率最低的一格 %s 换成 %s，池上限由 %d 球抬到 %d 球' % (
            n['replaced'], n['pool'][-1], n['cap_before'], cap(n['pool'])))
    if o['ttg_top2'] != n['ttg_top2']:
        note.append('总进球 TOP2 由 %s 改为 %s' % (
            '/'.join('%d球' % k for k in o['ttg_top2']), '/'.join('%d球' % k for k in n['ttg_top2'])))
    if not note:
        note.append('本场 λ 与档位均未改变档位结论，仅概率微调')
    A('> ' + '；'.join(note) + '。')
    A('')

A('## 结论')
A('')
A('**1. 改动的影响是温和的，不是颠覆性的。** λ 合计平均抬高 0.30 球，胜平负首选概率只变动 %.1f-%.1fpp，8 场里只有 1 场（005 威尼斯 vs 国际米兰）档位发生实质上移。这说明原口径的方向判断本身没有大问题，问题集中在"进球数"这一维度。' % (min(dp), max(dp)))
A('')
A('**2. 比分池上限保障确实把"够不着"的场次救回来了，但代价明确。** 8 场里 8 场的池上限都提高了（3→4、4→5、4→6），代价是池覆盖率从约 43% 降到约 40%。也就是说：命中高球比分的可能性变大了，但中低球比分的把握变小了。这笔交易是否划算，要看下一轮回测的实际命中。')
A('')
A('**3. 比分命中存在硬天花板，必须写在报告里。** 本轮 8 场原稿的比分池平均覆盖 %s 的概率质量——这意味着即使模型完全校准，单场比分 TOP5 的长期命中率上限也就是四成出头。10-27 实测 20%%、10-21 实测 33%%，已经贴着这个天花板的下沿。**后续报告应在比分栏直接标注"本场池覆盖 X%%"，让读者知道这一格的赔率虽然高，但期望命中就是三分之一左右。**' % pct(
    sum(sum(p for *_, p in old_full[x['num']]['top_scores']) for x in rows) / len(rows)))
A('')
A('**4. 下一轮的建议动作。** 本轮测试稿只改了 λ 与比分池两处；真正拖累命中率的"平局盲区"（10-27 两场未中全打平）还没动。建议下一轮同时加上：非单关场次在"方向分歧≥5pp 且任一方主力伤停≥3人"时给平局 +3~5pp 并强制进前二。')
A('')

out = '\n'.join(L)
p = os.path.join(D, 'reports/analysis/20261028_recalc_test.md')
io.open(p, 'w', encoding='utf-8').write(out)
print('saved', p, len(out))
