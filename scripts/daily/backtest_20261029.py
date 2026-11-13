# -*- coding: utf-8 -*-
"""2026-10-29 周四 7 场回测（6 场已结算 + 1 场待结算）：6 维命中 + 19 个串关方案结算
输出：
  reports/data/20261029_backtest.json / 20261029_backtest_rows.json
  reports/backtest/backtest_20261029_thursday_zhihu.md
"""
import json, io, os

D = r'e:\VibeCoding\football\reports\data'
pred = {m['num']: m for m in json.load(io.open(D + r'\20261029_predictions.json', encoding='utf-8-sig'))}
res = {r['num']: r for r in json.load(io.open(D + r'\20261029_results_official.json', encoding='utf-8-sig'))}

HAFU = {('H', 'H'): '胜胜', ('H', 'D'): '胜平', ('H', 'A'): '胜负',
        ('D', 'H'): '平胜', ('D', 'D'): '平平', ('D', 'A'): '平负',
        ('A', 'H'): '负胜', ('A', 'D'): '负平', ('A', 'A'): '负负'}
DIR = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC = {'home': '让胜', 'draw': '让平', 'away': '让负'}


def rl(s):
    a, b = [int(x) for x in str(s).replace(':', '-').split('-')]
    return a, b


def code(h, a):
    return 'H' if h > a else ('D' if h == a else 'A')


def tier_hit(tier, total):
    m = {'闷战超小球(0-1球)': total <= 1, '小球(1-2球)': total in (1, 2),
         '常规正常球(2-3球)': total in (2, 3), '大球(4-5球)': total in (4, 5),
         '超大球(5-6球)': total in (5, 6), '穿盘可能(6-7+球)': total >= 6}
    return m.get(tier, False)


rows = []
for num in sorted(pred):
    p, s = pred[num], res.get(num)
    rec = p['recommendation']
    if not s or not s.get('ft'):
        rows.append({'num': num, 'league': p['league'], 'home': p['home'], 'away': p['away'],
                     'status': 'pending', 'conf': p['conf']})
        continue
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht'])
    total = h + a
    actual = 'home' if h > a else ('draw' if h == a else 'away')
    had = 'first' if rec['had_primary'] == actual else ('second' if rec['had_secondary'] == actual else 'miss')

    gl = rec.get('hc_line')
    adj = (h - a) + gl
    hh_res = 'home' if adj > 0 else ('draw' if adj == 0 else 'away')
    hc = 'first' if rec['hc_primary'] == hh_res else ('second' if rec['hc_secondary'] == hh_res else 'miss')

    ttg = 'hit' if total in rec['ttg_top2'] else 'miss'
    hafu_actual = HAFU[(code(hh, ha), code(h, a))]
    hafu_pick = [x[0] for x in rec['htft_top3']]
    hafu = 'hit' if hafu_actual in hafu_pick else 'miss'

    crs_pick = [x['score'] for x in rec['cr_top5']]
    crs_actual = '%d-%d' % (h, a)
    crs = 'hit' if crs_actual in crs_pick else 'miss'
    crs_rank = (crs_pick.index(crs_actual) + 1) if crs == 'hit' else None

    ht_pick = [x['score'] for x in rec['ht_score']]
    ht_actual = '%d-%d' % (hh, ha)
    ht_hit = 'hit' if ht_actual in ht_pick else 'miss'

    tier = 'hit' if tier_hit(rec['tier'], total) else 'miss'

    rows.append({
        'num': num, 'league': p['league'], 'home': p['home'], 'away': p['away'],
        'ft': s['ft'], 'ht': s['ht'], 'total': total,
        'pred_dir': rec['had_primary'], 'pred_dir2': rec['had_secondary'],
        'p_dir': (round(p['model']['home'] * 100, 1), round(p['model']['draw'] * 100, 1), round(p['model']['away'] * 100, 1)),
        'actual_dir': actual, 'had': had,
        'hhad_line': gl, 'pred_hc': rec['hc_primary'], 'pred_hc2': rec['hc_secondary'], 'actual_hc': hh_res, 'hc': hc,
        'ttg_top2': rec['ttg_top2'], 'ttg': ttg,
        'hafu_top3': hafu_pick, 'hafu_actual': hafu_actual, 'hafu': hafu,
        'crs_top5': crs_pick, 'crs_actual': crs_actual, 'crs': crs, 'crs_rank': crs_rank,
        'tier': rec['tier'], 'tier_hit': tier,
        'ht_top3': ht_pick, 'ht_actual': ht_actual, 'ht_hit': ht_hit,
        'lambda': (p['model']['lambda_home'], p['model']['lambda_away']),
        'conf': p['conf'],
        'k_dist': p['k_dist'], 'k_rec': p['k_rec'], 'k_consistent': p['k_consistent'],
        'line': s.get('line'),
    })

json.dump(rows, io.open(D + r'\20261029_backtest_rows.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

settled = [x for x in rows if x.get('status') != 'pending']
N = len(settled)


def stat(key, first_only=False):
    if first_only:
        n = sum(1 for x in settled if x.get(key) == 'first')
    else:
        n = sum(1 for x in settled if x.get(key) in ('first', 'second', 'hit'))
    return n, N, n / N * 100


# ---- 串关（与本轮分析报告一一对应，19 个方案） ----
P = [
    ('方向串A（稳健）', '方向串', 2.27, [('001', 'had', 'away'), ('003', 'had', 'home')]),
    ('方向串B（价值）', '方向串', 2.74, [('004', 'had', 'home'), ('002', 'had', 'home')]),
    ('稳健让球串', '让球串', 2.13, [('007', 'hhad', 'home'), ('006', 'hhad', 'away')]),
    ('价值让球串', '让球串', 13.68, [('003', 'hhad', 'draw'), ('005', 'hhad', 'draw')]),
    ('半全场串A', '混合串', 24.10, [('003', 'hafu', '胜胜'), ('001', 'hafu', '负负'), ('004', 'hafu', '平胜')]),
    ('半全场串B', '混合串', 126.14, [('002', 'hafu', '平胜'), ('005', 'hafu', '平平'), ('006', 'hafu', '负负')]),
    ('方向+半全场A', '混合串', 3.83, [('003', 'had', 'home'), ('001', 'hafu', '负负')]),
    ('方向+半全场B', '混合串', 4.52, [('004', 'had', 'home'), ('002', 'hafu', '胜胜')]),
    ('连续编号混合串A', '混合串', 14.66, [('006', 'hafu', '负负'), ('007', 'ttg', 2)]),
    ('总进球串A', '总进球串', 101.52, [('001', 'ttg', 4), ('004', 'ttg', 4), ('006', 'ttg', 4)]),
    ('总进球串B', '总进球串', 50.44, [('002', 'ttg', 3), ('003', 'ttg', 4), ('005', 'ttg', 3)]),
    ('连续编号总进球串①', '总进球串', 14.84, [('003', 'ttg', 4), ('004', 'ttg', 3)]),
    ('高赔半全场串A', '高赔半全场串', 86.42, [('001', 'hafu', '平负'), ('003', 'hafu', '平胜'), ('006', 'hafu', '负负')]),
    ('高赔半全场串B', '高赔半全场串', 105.62, [('002', 'hafu', '平平'), ('005', 'hafu', '平胜'), ('007', 'hafu', '负负')]),
    ('连续编号高赔半全场串①', '高赔半全场串', 22.00, [('001', 'hafu', '平负'), ('002', 'hafu', '平胜')]),
    ('混合串A', '半全场混合', 10.13, [('003', 'hafu', '胜胜'), ('004', 'ttg', 4)]),
    ('混合串B', '半全场混合', 19.84, [('001', 'hafu', '平平'), ('006', 'ttg', 3)]),
    ('连续编号混合总进球串①', '半全场混合', 19.55, [('006', 'hafu', '平胜'), ('007', 'ttg', 3)]),
    ('搏冷比分串（反向推理）', '比分串', 144.00, [('004', 'crs', '1-2'), ('005', 'crs', '1-2')]),
]


def leg_ok(num, market, pick):
    s = res.get('周四' + num)
    if not s or not s.get('ft'):
        return None
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht'])
    if market == 'had':
        return ('home' if h > a else ('draw' if h == a else 'away')) == pick
    if market == 'hhad':
        adj = (h - a) + pred['周四' + num]['recommendation']['hc_line']
        return ('home' if adj > 0 else ('draw' if adj == 0 else 'away')) == pick
    if market == 'crs':
        return ('%d-%d' % (h, a)) == str(pick)
    if market == 'ttg':
        return (h + a) == int(pick)
    if market == 'hafu':
        return HAFU[(code(hh, ha), code(h, a))] == pick
    return None


def leg_text(num, market, pick):
    s = res.get('周四' + num)
    if not s or not s.get('ft'):
        return '%s 待结算' % num
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht'])
    if market == 'had':
        return '%s %s(%s)' % (num, DIR[pick], s['ft'])
    if market == 'hhad':
        return '%s 让(%+d)%s(%s)' % (num, pred['周四' + num]['recommendation']['hc_line'], HC[pick], s['ft'])
    if market == 'ttg':
        return '%s %d球(实%d球)' % (num, pick, h + a)
    if market == 'hafu':
        return '%s %s(实%s)' % (num, pick, HAFU[(code(hh, ha), code(h, a))])
    if market == 'crs':
        return '%s %s(实%s)' % (num, pick, s['ft'])
    return num


hit = 0
stake = ret = 0.0
out_parlays = []
for name, cat, odds, legs in P:
    oks = [leg_ok(*lg) for lg in legs]
    pend = any(o is None for o in oks)
    allok = all(o is True for o in oks) and not pend
    stake += 1
    if allok:
        hit += 1
        ret += odds
    out_parlays.append({'name': name, 'cat': cat, 'odds': odds, 'hit': allok, 'pending': pend,
                        'legs': [{'match': lg[0], 'market': lg[1], 'pick': lg[2], 'ok': o}
                                 for lg, o in zip(legs, oks)],
                        'results': [leg_text(*lg) for lg in legs]})

played = [p for p in out_parlays if not p['pending']]
json.dump({'rows': rows, 'parlays': out_parlays},
          io.open(D + r'\20261029_backtest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---------------- 报告生成 ----------------
L = []
A = L.append
A('# 【回测】2026-10-30（周五）10-29周四7场回测 | 方向4/6、半全场4/6，进球被系统性地打穿')
A('')
A('> **报告说明：** 本文为赛后**回测报告**（标题标注【回测】），对比预测与实际结果并统计命中率。赛前**分析报告**（标题标注【分析】）提供方向/比分/总进球等预测推荐。历史报告可去主页查找。')
A('')
A('> **风险提示：** 回测结果仅供参考，历史命中不代表未来表现。赔率数据以采集时为准。**理性看待预测，切勿沉迷赌博。**')
A('')
A('> **⚠️ 免责声明：** 本文所有回测数据、命中率统计、教训分析仅供学习交流参考，不构成任何投注建议。回测结果具有时效性，历史命中不代表未来表现。内容仅供参考，如有错漏请谅解。请遵守当地法律法规，理性购彩，量力而行。')
A('')
A('*每日更新，关注主页获取最新赛事分析*')
A('')
_ent = [q for q in out_parlays if q['cat'] in ('总进球串', '高赔半全场串', '半全场混合', '比分串')]
_ent_done = [q for q in _ent if not q['pending']]
A('10-29 共 7 场，官方已结算 6 场（007 格雷米奥vs巴拉纳竞技仍为待结算）。**方向首选 4/6=66.7%、含次选 5/6=83.3%**，半全场与半场比分各 4/6，是昨轮唯一"稳"的两块；但**总进球 TOP2 仅 1/6、大小球档位 1/6**，实际场均 3.83 球，模型把三场比赛压在了 2-3 球档——这是本轮最大的翻车点。串关 ' + (
    '%d/%d 已结算，方向串A（2.27）与方向+半全场A（3.83）双响，已结算娱乐串 %d 个方案全灭（另有 %d 个方案待 007 结算）。' % (
        hit, len(played), len(_ent_done), len(_ent) - len(_ent_done))))
A('')
A('## 总览')
A('')
A('| 编号 | 对阵 | 赛事 | 预测方向(首选/次选) | 实际方向 | 命中 | 让球 | 让球命中 | 总进球 | 进球命中 | 半全场TOP3 | 半全场命中 | 比分TOP5 | 比分命中 |')
A('|:---:|:---|:---|:---|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|')
for x in rows:
    if x.get('status') == 'pending':
        A('| %s | %s vs %s | %s | 待结算 | — | ⏳ | — | ⏳ | — | ⏳ | — | ⏳ | — | ⏳ |' % (
            x['num'].replace('周四', ''), x['home'], x['away'], x['league']))
        continue
    mk = {'first': '✅首', 'second': '✅次', 'miss': '❌'}
    A('| %s | %s vs %s | %s | %s/%s | %s | %s | 让(%+d)%s | %s | %d球(实%d) | %s | %s | %s | %s | %s |' % (
        x['num'].replace('周四', ''), x['home'], x['away'], x['league'],
        DIR[x['pred_dir']], DIR[x['pred_dir2']], DIR[x['actual_dir']], mk[x['had']],
        x['hhad_line'], HC[x['pred_hc']], mk[x['hc']],
        x['ttg_top2'][0], x['total'], '✅' if x['ttg'] == 'hit' else '❌',
        '/'.join(x['hafu_top3']), '✅' if x['hafu'] == 'hit' else '❌',
        x['crs_top5'][0], '✅' if x['crs'] == 'hit' else '❌'))
A('')
A('> 命中汇总：方向首选 4/6=66.7%｜含次选 5/6=83.3%｜让球首选 2/6=33.3%｜含次选 4/6=66.7%｜总进球TOP2 1/6=16.7%｜半全场TOP3 4/6=66.7%｜比分TOP5 2/6=33.3%｜半场比分TOP3 4/6=66.7%｜大小球档位 1/6=16.7%。')
A('')
A('## 逐场回测')

NOTE = {
    '001': '客胜命中，是本轮结构最干净的一场：申花缺朱辰杰+吴曦后中轴彻底空洞，町田三中卫把比赛压成低比分消耗战，0-1 与模型"客胜+小球"的方向完全一致；唯一偏差是总进球被压到 1 球（模型给 3/2 球）。让(+1)首选让胜、实际净负 1 球落在让平（次选命中）。',
    '002': '冠军战打出 2-4，是本轮最大冷门：图尔库 29 轮只失 20 球，本场单场丢 4 个。模型首选主胜 44.8% 未中，次选客胜 28.0% 兜住；让(-1)让负（主队不赢）命中。总进球 6 球落在模型 4-5% 的尾部，TOP2（2/3 球）全错。',
    '003': '方向、半全场、半场比分三项全中：弗洛西诺内 5-1 打爆莱切，验证了"莱切两名中卫停赛+两名中场缺阵"的防线崩塌判断。但比分 TOP5 最高只到 3-1（7.6%），5-1 不在候选；总进球 6 球同样被打穿。让(-1)让平首选错、次选让胜命中。',
    '004': '本轮命中面最广的一场：方向首选主胜、半全场胜胜、半场比分 1-0、比分 TOP5 第 3 位 2-0、总进球 2 球、档位"常规正常球"全部命中。哈马比用 0.84 的场均失球守住了天狼星的最强火力，赛前"运气值回落"的判断兑现。唯一错的是让(-1)：净胜 2 球直接打成让胜。',
    '005': '方向（主胜）、半全场（胜胜）命中，埃弗顿 3-1 拿下轮换的纽卡，验证了"纽卡官方表态强阵容但联赛状态差"的基本面判断。但让(-1)让负错（净胜 2 球=让胜），总进球 4 球超出 2-3 球档位。',
    '006': '本轮唯一"方向双选全错"的场次：模型给主胜 42.6% / 客胜 34.4%，实际 2-2。亚特兰大四名中卫全缺、佛罗伦萨意甲失球最多，双方后防都在送球，模型对"残阵对撞→平局"的权重给得不够（平仅 22.9%）。安慰项：让(-1)让负命中、比分 TOP5 第 4 位 2-2 命中、半场比分 0-1 命中。',
}

for x in rows:
    if x.get('status') == 'pending':
        A('### %s %s vs %s（%s）' % (x['num'].replace('周四', ''), x['home'], x['away'], x['league']))
        A('')
        A('⏳ **待结算**：体彩官方 matchResultStatus=1（未开奖/未结算），赛后补录。该场同时是稳健让球串、连续编号混合串A、高赔半全场串B、连续编号混合总进球串①的腿，合计 4 个方案暂计待结算。')
        A('')
        continue
    p = pred[x['num']]
    A('### %s %s vs %s（%s）' % (x['num'].replace('周四', ''), x['home'], x['away'], x['league']))
    A('')
    _t = p['kickoff'][:5]
    _d = '10-30 ' if int(_t.split(':')[0]) < 12 else '10-29 '
    A('⏰ %s%s ｜ 🏟 %s ｜ **%s**' % (_d, _t, p['venue']['name'], x['ft']))
    A('')
    A('**赛果：** 半场%s → 全场%s ｜ 总进球%d ｜ %s' % (x['ht'], x['ft'], x['total'], DIR[x['actual_dir']]))
    A('')
    A('**预测回顾：**')
    A('')
    A('| 维度 | 预测 | 实际 | 命中 |')
    A('|:---|:---|:---|:---:|')
    mk = {'first': '✅首中', 'second': '✅次中', 'miss': '❌'}
    A('| **方向** | %s / %s | %s | %s |' % (DIR[x['pred_dir']], DIR[x['pred_dir2']], DIR[x['actual_dir']], mk[x['had']]))
    A('| **让球** | 让(%+d)%s / 让(%+d)%s | 让(%+d)%s | %s |' % (
        x['hhad_line'], HC[x['pred_hc']], x['hhad_line'], HC[x['pred_hc2']],
        x['hhad_line'], HC[x['actual_hc']], mk[x['hc']]))
    A('| **总进球TOP2** | **%d球** / **%d球** | %d球 | %s |' % (
        x['ttg_top2'][0], x['ttg_top2'][1], x['total'], '✅' if x['ttg'] == 'hit' else '❌'))
    A('| **半全场TOP3** | %s | %s | %s |' % (
        ' > '.join(x['hafu_top3']), x['hafu_actual'], '✅' if x['hafu'] == 'hit' else '❌'))
    A('| **比分TOP5** | %s | **%s** | %s |' % (
        ' > '.join(x['crs_top5']), x['crs_actual'],
        ('✅（第%d位）' % x['crs_rank']) if x['crs'] == 'hit' else '❌'))
    A('| **半场比分TOP3** | %s | %s | %s |' % (
        ' > '.join(x['ht_top3']), x['ht_actual'], '✅' if x['ht_hit'] == 'hit' else '❌'))
    A('| **大小球档位** | %s | %d球 | %s |' % (x['tier'], x['total'], '✅' if x['tier_hit'] == 'hit' else '❌'))
    A('')
    A('> %s' % NOTE.get(x['num'].replace('周四', ''), ''))
    A('')

A('## 命中率统计')
A('')
A('| 维度 | 命中/总场 | 命中率 | 评级 |')
A('|:---|:---:|:---:|:---:||')
A('| **方向(首选+次选)** | %d/%d | %.1f%% | 优秀 |' % stat('had'))
A('| **方向(仅首选)** | %d/%d | %.1f%% | 良好 |' % stat('had', True))
A('| **让球(首选+次选)** | %d/%d | %.1f%% | 一般 |' % stat('hc'))
A('| **让球(仅首选)** | %d/%d | %.1f%% | 较差 |' % stat('hc', True))
A('| **总进球TOP2** | %d/%d | %.1f%% | 较差 |' % stat('ttg'))
A('| **半全场TOP3** | %d/%d | %.1f%% | 优秀 |' % stat('hafu'))
A('| **比分TOP5** | %d/%d | %.1f%% | 一般 |' % stat('crs'))
A('| **半场比分TOP3** | %d/%d | %.1f%% | 优秀 |' % stat('ht_hit'))
A('| **大小球档位** | %d/%d | %.1f%% | 较差 |' % stat('tier_hit'))
A('')
dir_miss = [x['num'].replace('周四', '') for x in settled if x['had'] == 'miss']
hc_miss = [x['num'].replace('周四', '') for x in settled if x['hc'] == 'miss']
A('> 方向命中明细：首选命中%d场 + 次选命中%d场 = 合计%d场命中，未中%d场（%s）。' % (
    sum(1 for x in settled if x['had'] == 'first'), sum(1 for x in settled if x['had'] == 'second'),
    sum(1 for x in settled if x['had'] in ('first', 'second')), len(dir_miss), '、'.join(dir_miss) or '无'))
A('')
A('> 让球命中明细：首选命中%d场 + 次选命中%d场 = 合计%d场命中，未中%d场（%s）；让球仅首选命中%d场（%.1f%%）。' % (
    sum(1 for x in settled if x['hc'] == 'first'), sum(1 for x in settled if x['hc'] == 'second'),
    sum(1 for x in settled if x['hc'] in ('first', 'second')), len(hc_miss), '、'.join(hc_miss) or '无',
    sum(1 for x in settled if x['hc'] == 'first'), stat('hc', True)[2]))
A('')
A('**实际进球分布：** %s ｜ 场均 %.2f 球 ｜ 大2.5 %d/%d ｜ 平局 %d/%d' % (
    '、'.join('%d球×%d场' % (t, sum(1 for x in settled if x['total'] == t))
             for t in sorted(set(x['total'] for x in settled))),
    sum(x['total'] for x in settled) / N,
    sum(1 for x in settled if x['total'] >= 3), N,
    sum(1 for x in settled if x['actual_dir'] == 'draw'), N))
A('')
A('**按置信度分层：** ★★★ 1/1（003）｜★★ 2/3（001/004命中，002未中；含次选3/3）｜★ 1/2（005命中，006未中；含次选2/2）。')
A('')
A('## 串关回测')
A('')
A('| 方案 | 类型 | 场次 | 各场结果 | 串关命中 | 估算赔率 |')
A('|:---|:---|:---|:---|:---:|:---:|')
def pick_cn(market, pick):
    if market == 'had':
        return DIR[pick]
    if market == 'hhad':
        return HC[pick]
    if market == 'ttg':
        return '%d球' % int(pick)
    return str(pick)


for q in out_parlays:
    marks = []
    for lg, o in zip(q['legs'], [x['ok'] for x in q['legs']]):
        mark = '✅' if o is True else ('⏳' if o is None else '❌')
        marks.append('%s %s %s' % (lg['match'], pick_cn(lg['market'], lg['pick']), mark))
    tag = '✅中' if q['hit'] else ('⏳待' if q['pending'] else '❌')
    A('| %s | %s | %s | %s | %s | ~%.2f |' % (
        q['name'], q['cat'], ' + '.join(lg['match'] for lg in q['legs']), ' ｜ '.join(marks), tag, q['odds']))
A('')
A('> 串关命中 %d/%d 个已结算方案（%.1f%%），另有 %d 个方案含待结算场次 007（稳健让球串、连续编号混合串A、高赔半全场串B、连续编号混合总进球串①）。已结算投注 %d 注、回收 %.2f、ROI %.1f%%；计入待结算共 %d 注口径 ROI %.1f%%。' % (
    hit, len(played), hit / len(played) * 100, len(out_parlays) - len(played),
    len(played), ret, (ret - len(played)) / len(played) * 100, len(P), (ret - len(P)) / len(P) * 100))
A('')
A('> **结构复盘：** 唯一稳定的是"方向腿"——方向串A（001客胜+003主胜 2.27）与方向+半全场A（003主胜+001负负 3.83）双响；价值让球串（两场让平）与已结算的 8 个娱乐串（总进球/高赔半全场/混合/搏冷比分）全灭。**娱乐串本轮已结算 0/8，再次验证"高赔组合单轮命中率接近零"**。')
A('')
A('## 关键发现')
A('')
A('**1. 方向盘是唯一回稳的维度：首选 4/6、含次选 5/6。** 与上一轮（10-28 首选 3/15=20%）形成鲜明对比——本轮方向全部由"残阵/战意"这类可验证的基本面主导：申花4人缺阵→客胜、莱切6人缺阵→主胜、哈马比主场决战→主胜、埃弗顿3人成疑+纽卡轮换→主胜。基本面决定论在"信息明确"的场次上依旧成立。')
A('')
A('**2. 进球被系统性低估，是本轮最大问题：总进球 TOP2 1/6、档位 1/6。** 实际进球 1/6/6/2/4/4，场均 3.83 球；三场（002 六球、003 六球、005 四球）全部超出模型 2-3 球档。共同结构是"一方后防拼凑+另一方必须抢分"：莱切两中卫停赛、亚特兰大四中卫缺阵、图尔库单场丢 4 球。**规则65 的 +0.30 上修不足以覆盖后防崩塌的场次。**')
A('')
A('**3. 让球首选仅 2/6，但根因是"净胜球众数=0"口径。** 001（实际净负1）、004（净胜2）、005（净胜2）三场首选全错，其中004/005都是"让(-1)让负"却主队赢两球。无条件众数在"主队强+对手残阵"场景会系统性把让负当首选——这与 9-12 回测（让球旧口径36.7% vs 条件化13.3%）的结论并不矛盾，但说明**该口径在"明确强弱差"场次上仍需单场覆盖让平/让胜**。')
A('')
A('**4. 半全场与半场比分是稳定维度（各 4/6），"胜胜"路径本轮兑现 4 次。** 001负负、003胜胜、004胜胜、005胜胜，四场都是"半场就定调"的比赛；未中的 002（1-2→2-4，半场落后变负负）与 006（0-1→2-2，半场落后变负平）都是"半场≠全场"的变盘路径，与 L223 的历史问题同构。')
A('')
A('**5. 比分 TOP5 2/6，但命中都在第3-4位（004 2-0 第3、006 2-2 第4），TOP1 空白。** 分布形状是对的（大比分方向都进了候选），但峰值位置偏好低比分——003 的 5-1、005 的 3-1 都远超候选上限，说明在"残阵后防"场次应把 3-1/4-1/5-1 这类尾部分布纳入 TOP5。')
A('')
A('**6. 串关 %d/%d=%.1f%%，方向串与方向+半全场是唯一有效结构；已结算娱乐串 0/8。** 这与 L225/L230 的连续结论一致：稳健结构应继续收缩到"方向腿+半全场腿"，娱乐串只作极小注甚至不出。' % (
    hit, len(played), hit / len(played) * 100))
A('')
A('## 待改进')
A('')
A('- **残阵场次的进球 λ 必须有硬上修**：单队后防≥3人缺阵（含停赛）→ 该队失球 λ×1.15~1.25；双方合计≥10人缺阵 → λ_total 额外 +0.3~0.5，且 TTG TOP2 至少含 4 球。本轮 002/003/005 三场都会因此上调。')
A('- **让球在"明确强弱差+对手残阵"场次增加覆盖**：当模型首选方向概率≥55%且让球盘为±1时，首选让球之外必须把"让平"列入次选（本轮 001 即靠次选让平兜住）；该调整只作用于次选覆盖，不改动无条件众数首选口径（口径变更待用户裁决）。')
A('- **比分 TOP5 的尾部分布**：后防≥3人缺阵的场次，TOP5 强制包含 3-1/4-1（或反向 1-3/1-4）之一，避免 5-1/3-1 这类真实打出却完全不在候选的情况。')
A('- **残阵对撞的平局权重**：双方各有≥4人缺阵时，平局概率额外 +4~6pp（本轮 006 平局仅 22.9%，实际 2-2）。')
A('- **娱乐串继续压缩**：本轮 10 个娱乐串 0 命中，建议按 L230 只保留方向串与半全场混合串，其余暂停或严格限注。')
A('')
A('## ☕ 写在最后')
A('')
A('回测不是为了证明对错，而是把"下一次能改的那一条"找出来。这一轮真正值钱的不是 4/6 的方向，而是那句"后防拼凑的场次，进球不能只给 2-3 球"。')
A('')
A('盈利是逻辑兑现，未盈利是方差未回归。拉长周期看，方法论不会骗人。')
A('')
A('你们的支持，决定了我能把这事做多久。')
A('')

out = '\n'.join(L).replace('|:---|:---:|:---:|:---:||', '|:---|:---:|:---:|:---:|')
os.makedirs(r'e:\VibeCoding\football\reports\backtest', exist_ok=True)
io.open(r'e:\VibeCoding\football\reports\backtest\backtest_20261029_thursday_zhihu.md', 'w', encoding='utf-8').write(out)

print('方向 首选 %d/%d=%.1f%% ｜含次选 %d/%d=%.1f%%' % (*stat('had', True), *stat('had')))
print('让球 首选 %d/%d=%.1f%% ｜含次选 %d/%d=%.1f%%' % (*stat('hc', True), *stat('hc')))
print('总进球TOP2 %d/%d=%.1f%%' % stat('ttg'))
print('半全场TOP3 %d/%d=%.1f%%' % stat('hafu'))
print('比分TOP5 %d/%d=%.1f%%' % stat('crs'))
print('大小球六档 %d/%d=%.1f%%' % stat('tier_hit'))
print('半场比分TOP3 %d/%d=%.1f%%' % stat('ht_hit'))
print('串关 %d/%d=%.1f%% 回收%.2f 投入%d（含%d待结算）' % (
    hit, len(played), hit / len(played) * 100, ret, len(P), len(P) - len(played)))
print('saved report')
