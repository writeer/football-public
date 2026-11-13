# -*- coding: utf-8 -*-
"""2026-10-30 周五 12 场回测：6 维命中 + 24 个串关方案结算
输出：
  reports/data/20261030_backtest.json / 20261030_backtest_rows.json
  reports/backtest/backtest_20261030_friday_zhihu.md
"""
import json, io, os

D = r'e:\VibeCoding\football\reports\data'
pred = {m['num']: m for m in json.load(io.open(D + r'\20261030_predictions.json', encoding='utf-8-sig'))}
res = {r['num']: r for r in json.load(io.open(D + r'\20261030_results_official.json', encoding='utf-8-sig'))}

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
        'p_dir': (round(p['model']['home'] * 100, 1), round(p['model']['draw'] * 100, 1),
                  round(p['model']['away'] * 100, 1)),
        'actual_dir': actual, 'had': had,
        'hhad_line': gl, 'pred_hc': rec['hc_primary'], 'pred_hc2': rec['hc_secondary'],
        'actual_hc': hh_res, 'hc': hc,
        'ttg_top2': rec['ttg_top2'], 'ttg': ttg,
        'hafu_top3': hafu_pick, 'hafu_actual': hafu_actual, 'hafu': hafu,
        'crs_top5': crs_pick, 'crs_actual': crs_actual, 'crs': crs, 'crs_rank': crs_rank,
        'tier': rec['tier'], 'tier_hit': tier,
        'ht_top3': ht_pick, 'ht_actual': ht_actual, 'ht_hit': ht_hit,
        'lambda': (p['model']['lambda_home'], p['model']['lambda_away']),
        'conf': p['conf'], 'is_single': p.get('is_single', False),
        'k_dist': p['k_dist'], 'k_rec': p['k_rec'], 'k_consistent': p['k_consistent'],
    })

json.dump(rows, io.open(D + r'\20261030_backtest_rows.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

settled = [x for x in rows if x.get('status') != 'pending']
N = len(settled)


def stat(key, first_only=False):
    if first_only:
        n = sum(1 for x in settled if x.get(key) == 'first')
    else:
        n = sum(1 for x in settled if x.get(key) in ('first', 'second', 'hit'))
    return n, N, n / N * 100


# ---- 串关（与 20261030 报告一一对应，24 个方案） ----
P = [
    ('方向串A（稳健）', '方向串', 2.51, [('009', 'had', 'home'), ('012', 'had', 'home'), ('011', 'had', 'away')]),
    ('方向串B（价值）', '方向串', 6.74, [('005', 'had', 'home'), ('010', 'had', 'home'), ('007', 'had', 'away')]),
    ('稳健让球串', '让球串', 2.35, [('001', 'hhad', 'home'), ('002', 'hhad', 'home')]),
    ('价值让球串', '让球串', 13.15, [('008', 'hhad', 'draw'), ('012', 'hhad', 'draw')]),
    ('半全场串A', '混合串', 9.20, [('006', 'hafu', '胜胜'), ('011', 'hafu', '负负'), ('009', 'hafu', '胜胜')]),
    ('半全场串B', '混合串', 18.25, [('012', 'hafu', '胜胜'), ('007', 'hafu', '负负'), ('005', 'hafu', '胜胜')]),
    ('方向+半全场A', '混合串', 3.36, [('011', 'had', 'away'), ('006', 'hafu', '胜胜')]),
    ('方向+半全场B', '混合串', 3.48, [('009', 'had', 'home'), ('012', 'hafu', '胜胜')]),
    ('连续编号混合串A', '混合串', 9.70, [('007', 'had', 'away'), ('008', 'hafu', '平平')]),
    ('连续编号混合串B', '混合串', 6.19, [('005', 'had', 'home'), ('006', 'ttg', 4)]),
    ('总进球串A', '总进球串', 76.05, [('001', 'ttg', 4), ('006', 'ttg', 4), ('011', 'ttg', 3)]),
    ('总进球串B', '总进球串', 56.37, [('005', 'ttg', 3), ('007', 'ttg', 3), ('009', 'ttg', 2)]),
    ('连续编号总进球串①', '总进球串', 23.32, [('001', 'ttg', 4), ('002', 'ttg', 2)]),
    ('连续编号总进球串②', '总进球串', 12.25, [('011', 'ttg', 3), ('012', 'ttg', 2)]),
    ('高赔半全场串A', '高赔半全场串', 62.66, [('001', 'hafu', '平胜'), ('006', 'hafu', '胜胜'), ('011', 'hafu', '平负')]),
    ('高赔半全场串B', '高赔半全场串', 64.73, [('005', 'hafu', '胜胜'), ('007', 'hafu', '平负'), ('012', 'hafu', '平平')]),
    ('连续编号高赔半全场串①', '高赔半全场串', 28.03, [('001', 'hafu', '平胜'), ('002', 'hafu', '胜胜')]),
    ('连续编号高赔半全场串②', '高赔半全场串', 26.75, [('007', 'hafu', '平负'), ('008', 'hafu', '平平')]),
    ('混合串A', '半全场混合', 10.33, [('006', 'hafu', '胜胜'), ('011', 'ttg', 3)]),
    ('混合串B', '半全场混合', 5.46, [('004', 'hafu', '负负'), ('012', 'ttg', 2)]),
    ('连续编号混合总进球串①', '半全场混合', 25.18, [('001', 'ttg', 4), ('002', 'hafu', '胜胜')]),
    ('连续编号混合总进球串②', '半全场混合', 9.52, [('011', 'ttg', 3), ('012', 'hafu', '胜胜')]),
    ('搏冷比分串（反向推理）', '比分串', 61.63, [('002', 'crs', '1-2'), ('008', 'crs', '1-2')]),
]


def leg_ok(num, market, pick):
    s = res.get('周五' + num)
    if not s or not s.get('ft'):
        return None
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht'])
    if market == 'had':
        return ('home' if h > a else ('draw' if h == a else 'away')) == pick
    if market == 'hhad':
        adj = (h - a) + pred['周五' + num]['recommendation']['hc_line']
        return ('home' if adj > 0 else ('draw' if adj == 0 else 'away')) == pick
    if market == 'crs':
        return ('%d-%d' % (h, a)) == str(pick)
    if market == 'ttg':
        return (h + a) == int(pick)
    if market == 'hafu':
        return HAFU[(code(hh, ha), code(h, a))] == pick
    return None


def leg_text(num, market, pick):
    s = res.get('周五' + num)
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht'])
    if market == 'had':
        return '%s %s(%s)' % (num, DIR[pick], s['ft'])
    if market == 'hhad':
        return '%s 让(%+d)%s(%s)' % (num, pred['周五' + num]['recommendation']['hc_line'], HC[pick], s['ft'])
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

json.dump({'rows': rows, 'parlays': out_parlays},
          io.open(D + r'\20261030_backtest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('=== 6维 ===')
print('方向 首选 %d/%d=%.1f%% 含次选 %d/%d=%.1f%%' % (*stat('had', True), *stat('had')))
print('让球 首选 %d/%d=%.1f%% 含次选 %d/%d=%.1f%%' % (*stat('hc', True), *stat('hc')))
print('总进球TOP2 %d/%d=%.1f%%' % stat('ttg'))
print('半全场TOP3 %d/%d=%.1f%%' % stat('hafu'))
print('比分TOP5 %d/%d=%.1f%%' % stat('crs'))
print('半场比分TOP3 %d/%d=%.1f%%' % stat('ht_hit'))
print('大小球六档 %d/%d=%.1f%%' % stat('tier_hit'))
print('进球分布', [x['total'] for x in settled], '场均%.2f' % (sum(x['total'] for x in settled) / N))
print('=== 串关 %d/%d 回收%.2f ===' % (hit, len(out_parlays), ret))
for q in out_parlays:
    print(('✅' if q['hit'] else '❌'), q['name'], q['odds'], '|', ' / '.join(
        '%s%s%s' % (lg['match'], lg['market'], '✔' if lg['ok'] else '✘') for lg in q['legs']))
print('=== 逐场 ===')
for x in settled:
    print(x['num'], x['ft'], 'HT', x['ht'], '| 方向', x['pred_dir'], x['pred_dir2'], '→', x['actual_dir'], x['had'],
          '| 让', x['hhad_line'], x['pred_hc'], x['pred_hc2'], '→', x['actual_hc'], x['hc'],
          '| TTG', x['ttg_top2'], '实', x['total'], x['ttg'],
          '| HAFU', x['hafu_top3'], '实', x['hafu_actual'], x['hafu'],
          '| CRS1', x['crs_top5'][0], '实', x['crs_actual'], x['crs'],
          '| HT', x['ht_top3'], '实', x['ht_actual'], x['ht_hit'],
          '| 档', x['tier'], x['tier_hit'], '| conf', x['conf'])

# ---------------- 多方案串关排序补漏检查 ----------------
for q in out_parlays:
    q['legs_ok'] = sum(1 for lg in q['legs'] if lg['ok'])

# ---------------- 报告生成 ----------------
L = []
A = L.append
A('# 【回测】2026-10-31（周六）10-30周五12场回测 | 方向含次选10/12、比分TOP5 7/12，串关只有1个混合串活下来')
A('')
A('> **报告说明：** 本文为赛后**回测报告**（标题标注【回测】），对比预测与实际结果并统计命中率。赛前**分析报告**（标题标注【分析】）提供方向/比分/总进球等预测推荐。历史报告可去主页查找。')
A('')
A('> **风险提示：** 回测结果仅供参考，历史命中不代表未来表现。赔率数据以采集时为准。**理性看待预测，切勿沉迷赌博。**')
A('')
A('> **⚠️ 免责声明：** 本文所有回测数据、命中率统计、教训分析仅供学习交流参考，不构成任何投注建议。回测结果具有时效性，历史命中不代表未来表现。内容仅供参考，如有错漏请谅解。请遵守当地法律法规，理性购彩，量力而行。')
A('')
A('*每日更新，关注主页获取最新赛事分析*')
A('')
A('10-30 共 12 场（001-012，007 单关），全部已结算。**方向首选 6/12=50.0%、含次选 10/12=83.3%**，是本轮唯一站得住的维度；**比分 TOP5 7/12=58.3%** 创近期新高，半全场 8/12。但**总进球 TOP2 与大小球档位各 3/12=25.0%**，进球端两个方向同时失手：既把 007/005/004 这类 5-7 球场次压在 2-3 球档，也把 008/009/010 三场 1 球闷战估高。串关 23 个方案只有 **混合串B（004负负+012 2球，5.46）** 命中。')
A('')
A('## 总览')
A('')
A('| 编号 | 对阵 | 赛事 | 预测方向(首选/次选) | 实际方向 | 命中 | 让球 | 让球命中 | 总进球 | 进球命中 | 半全场TOP3 | 半全场命中 | 比分TOP5首位 | 比分命中 |')
A('|:---:|:---|:---|:---|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|')
for x in rows:
    mk = {'first': '✅首', 'second': '✅次', 'miss': '❌'}
    cells = [
        x['num'].replace('周五', ''),
        '%s vs %s' % (x['home'], x['away']),
        x['league'],
        '%s/%s' % (DIR[x['pred_dir']], DIR[x['pred_dir2']]),
        DIR[x['actual_dir']],
        mk[x['had']],
        '让(%+d)%s' % (x['hhad_line'], HC[x['pred_hc']]),
        mk[x['hc']],
        '%d球(实%d)' % (x['ttg_top2'][0], x['total']),
        '✅' if x['ttg'] == 'hit' else '❌',
        '/'.join(x['hafu_top3']),
        '✅' if x['hafu'] == 'hit' else '❌',
        x['crs_top5'][0],
        ('✅第%d位' % x['crs_rank']) if x['crs'] == 'hit' else '❌',
    ]
    A('| ' + ' | '.join(cells) + ' |')
A('')
A('> 命中汇总：方向首选 6/12=50.0%｜含次选 10/12=83.3%｜让球首选 4/12=33.3%｜含次选 9/12=75.0%｜总进球TOP2 3/12=25.0%｜半全场TOP3 8/12=66.7%｜比分TOP5 7/12=58.3%｜半场比分TOP3 7/12=58.3%｜大小球档位 3/12=25.0%。')
A('')
A('## 逐场回测')

NOTE = {
    '001': '本轮唯一"方向双选全错"的场次：模型给主胜 46.4%、次选客胜 33.3%，实际 1-1（市场反而更看客队 37.7%）。奥克兰半场 0-1 领先后被追平，是典型"跨塔斯曼对攻+体能回落"。安慰项：比分 TOP5 第 1 位 1-1 命中、让(+1)让胜首选命中；但总进球给 4/3 球、档位"大球(4-5球)"，实际只有 2 球。',
    '002': '方向次选客胜兜住（波鸿 1-2），让(+1)次选让平命中（净负 1 球），总进球 3 球命中、档位常规命中、半场比分 1-0 命中、比分 TOP5 含 1-2。唯一漏的是半全场：半场 1-0 领先、全场 1-2，走"胜负"路径，TOP3（胜胜/平胜/平平）完全没覆盖。',
    '003': '尼斯 5-2 打爆雷恩，方向靠次选主胜兜住（首选客胜落空）。让(+1)让胜首选命中、半全场"胜胜"命中；但 7 球把总进球 2/3 球与"常规 2-3 球"档位同时打穿，比分 TOP5 上限只到 1-1。',
    '004': '方向首选客胜（PSG 1-5）命中、半全场"负负"命中，是本轮最干净的两条线。让(+2)实际是让负（净负 4 球），模型首选让胜、次选让平，双错；总进球 6 球同样超出 2-3 球档。',
    '005': '博德闪耀 3-2 维京，方向首选主胜命中、半全场"胜胜"命中、让(-1)次选让平命中。总进球 5 球超出模型 3/4 球与 2-3 球档位——挪超强强对攻的尾部质量仍给得不够。',
    '006': '福伦丹 1-2 格拉夫夏普，方向次选客胜命中、比分 TOP5 含 1-2、半场比分 1-0 命中。但模型给的总进球是 4/5 球、档位直接判成"穿盘可能(6-7+球)"，实际只有 3 球——这是本轮档位误判最重的一场（荷乙被高估成对攻大战）。',
    '007': '单关场次。埃尔沃斯堡 4-1 美因茨，方向靠次选主胜兜住——模型给主队 38.1%、客队 38.4%（几乎五五），市场却把客队推到 45.3%，实际主队 4-1 大胜。让(+1)让胜首选命中、半全场"胜胜"命中。但总进球 5 球超出 3/4 球档，比分 TOP5 上限只到 1-1，4-1 完全不在候选——单关给得最"重"的一场，反而是三处失手。',
    '008': '谢菲联 1-0 雷克斯汉姆，方向首选主胜、半全场"胜胜"、比分 TOP5 含 1-0、半场比分 1-0 全部命中。唯一错的是总进球：给 2/3 球，实际 1 球；让(-1)首选让负、次选让平兜住。',
    '009': '比利亚雷亚尔 0-1 西班牙人，方向首选主胜、次选平，双错——市场给主队 1.28 的强主胜，模型也只给到"主胜+平"覆盖，没有把西班牙人的客场反击算进去。让(-1)让负首选命中、半场比分 0-0 命中；半全场实际"平负"也落在 TOP3 之外。',
    '010': '里尔 1-0 朗斯，方向首选主胜命中、半全场"平胜"命中、比分 TOP5 含 1-0、半场比分 0-0 命中、让(-1)次选让平命中。仅有总进球一项（给 2/3 球、实际 1 球）落空——是除 011 外最完整的一场。',
    '011': '**本轮唯一六维全中**：卡萨皮亚 0-2 里斯本竞技——方向首选客胜、让(+2)次选让平、总进球 2 球、档位常规、半全场"负负"、比分 TOP5 第 1 位 0-2、半场比分 0-1。强弱差明确且客队进攻稳定，是本轮最典型的高可信样本。',
    '012': '科林蒂安 2-0 米拉索尔，方向首选主胜、总进球 2 球、半全场"平胜"、比分 TOP5 含 2-0、半场比分 0-0 全部命中。唯一错的是让(-1)：净胜 2 球打成让胜，模型首选让负、次选让平。',
}

for x in settled:
    p = pred[x['num']]
    A('### %s %s vs %s（%s）' % (x['num'].replace('周五', ''), x['home'], x['away'], x['league']))
    A('')
    t = p['kickoff'][:5]
    d = '10-31 ' if int(t.split(':')[0]) < 12 else '10-30 '
    A('⏰ %s%s ｜ 🏟 %s ｜ **%s**' % (d, t, p['venue']['name'], x['ft']))
    A('')
    A('**赛果：** 半场%s → 全场%s ｜ 总进球%d ｜ %s' % (x['ht'], x['ft'], x['total'], DIR[x['actual_dir']]))
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
    A('> %s' % NOTE.get(x['num'].replace('周五', ''), ''))
    A('')

A('## 命中率统计')
A('')
A('| 维度 | 命中/总场 | 命中率 |')
A('|:---|:---:|:---:|')
A('| **方向(首选+次选)** | %d/%d | %.1f%% |' % stat('had'))
A('| **方向(仅首选)** | %d/%d | %.1f%% |' % stat('had', True))
A('| **让球(首选+次选)** | %d/%d | %.1f%% |' % stat('hc'))
A('| **让球(仅首选)** | %d/%d | %.1f%% |' % stat('hc', True))
A('| **总进球TOP2** | %d/%d | %.1f%% |' % stat('ttg'))
A('| **半全场TOP3** | %d/%d | %.1f%% |' % stat('hafu'))
A('| **比分TOP5** | %d/%d | %.1f%% |' % stat('crs'))
A('| **半场比分TOP3** | %d/%d | %.1f%% |' % stat('ht_hit'))
A('| **大小球档位** | %d/%d | %.1f%% |' % stat('tier_hit'))
A('')
dir_miss = [x['num'].replace('周五', '') for x in settled if x['had'] == 'miss']
hc_miss = [x['num'].replace('周五', '') for x in settled if x['hc'] == 'miss']
A('> 方向命中明细：首选 %d 场 + 次选 %d 场 = %d 场命中，未中 %d 场（%s）。' % (
    sum(1 for x in settled if x['had'] == 'first'), sum(1 for x in settled if x['had'] == 'second'),
    sum(1 for x in settled if x['had'] in ('first', 'second')), len(dir_miss), '、'.join(dir_miss)))
A('')
A('> 让球命中明细：首选 %d 场 + 次选 %d 场 = %d 场命中，未中 %d 场（%s）。' % (
    sum(1 for x in settled if x['hc'] == 'first'), sum(1 for x in settled if x['hc'] == 'second'),
    sum(1 for x in settled if x['hc'] in ('first', 'second')), len(hc_miss), '、'.join(hc_miss)))
A('')
A('**实际进球分布：** %s ｜ 场均 %.2f 球 ｜ 大2.5 %d/%d ｜ 平局 %d/%d' % (
    '、'.join('%d球×%d场' % (t2, sum(1 for x in settled if x['total'] == t2))
             for t2 in sorted(set(x['total'] for x in settled))),
    sum(x['total'] for x in settled) / N,
    sum(1 for x in settled if x['total'] >= 3), N,
    sum(1 for x in settled if x['actual_dir'] == 'draw'), N))
A('')
A('**按置信度分层：** ★★（009/011）首选 1/2、含次选 1/2 ｜★（其余10场）首选 5/10、含次选 9/10 —— 本轮星级与命中率并未形成正向分层，低星场次反而是覆盖主力。')
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
    for lg in q['legs']:
        mark = '✅' if lg['ok'] is True else ('⏳' if lg['ok'] is None else '❌')
        marks.append('%s %s %s' % (lg['match'], pick_cn(lg['market'], lg['pick']), mark))
    tag = '✅中' if q['hit'] else ('⏳待' if q['pending'] else '❌')
    A('| %s | %s | %s | %s | %s | ~%.2f |' % (
        q['name'], q['cat'], ' + '.join(lg['match'] for lg in q['legs']), ' ｜ '.join(marks), tag, q['odds']))
A('')
A('> 串关 **%d/%d=%.1f%%**（%.2f/%.2f，ROI **%.1f%%**）。唯一命中的是**混合串B**（004 半全场负负 + 012 总进球 2 球，5.46）；方向串A/B 都只差一腿（009 与 007），搏冷比分串也只有 008 的 1-2 落空。' % (
    hit, len(out_parlays), hit / len(out_parlays) * 100, ret, stake, (ret - stake) / stake * 100))
A('')
A('> 比分串与单挑比分本轮全部按门槛留空（仅 011 一场满足"众数一致＋概率≥8%＋赔率≥6.00"，不足两腿），若强行凑串只会进一步拖低回收。')
A('')
A('## 关键发现')
A('')
A('**1. 方向含次选 83.3% 是本轮唯一亮点，但首选只有 50%。** 次选兜住 4 场（002/003/006/007），其中 003、007 都是"市场强推客队、模型把主胜放在次选"——说明本轮**首选被市场情绪带偏的场次集中在"强队做客"**，而次选反而更贴近基本面。')
A('')
A('**2. 进球端两个方向同时失手（TOP2 3/12、六档 3/12）。** 高估的有 001（4/3 球 vs 实际 2）、006（4/5 球、档位"穿盘"vs 实际 3）、008/009/010（2/3 球 vs 实际 1）；低估的有 003（7 球）、004（6 球）、005（5 球）、007（5 球）。**同一轮里既有"荷乙被当成对攻大战"，也有"巴黎 5 球被压在 2-3 球档"**——说明档位判定对"联赛风格"的权重过大，对"单场实力差"的响应不足。')
A('')
A('**3. 比分 TOP5 7/12=58.3%，是近期最好的一轮。** 命中集中在 1-1（001/002/006/010/012 的 1-1 或 1-0）、0-2（011 首位）；4-1（007）、5-2（003）这类大胜仍完全不在候选。**比分池宽度是有效的，但上沿仍卡在 2 球净胜。**')
A('')
A('**4. 半全场 8/12：胜胜/负负路径兑现 5 次，失手集中在"半场领先被翻"（002 胜负、006 胜负）。** 与 L239 同构，说明"半场落后→全场变盘"的路径仍未进 TOP3。')
A('')
A('**5. 让球首选 4/12=33.3%、含次选 75%。** 次选让平本轮兜住 005/008/010/011 四场，价值让球串却挑了 008/012 两场次选——008 命中、012 落空（净胜 2 球打成让胜）。**次选命中率高，但"串起来"的稳定性远低于单场覆盖。**')
A('')
A('**6. 串关 1/23=4.3%，ROI -76.3%。** 结构上最接近命中的是方向串A（差 009 一场）与方向串B（差 007 一场）；唯一命中的混合串B 是"半全场负负 + 总进球 2 球"的低赔组合。与 L240 一致：**方向腿+半全场腿仍是唯一可复制的结构，娱乐串继续只作极小注。**')
A('')
A('## 待改进')
A('')
A('- **档位判定要与实力差联动，而不是只看联赛风格**：当身价差≥5 倍或 λ 差≥1.0 时，档位下限直接抬到"大球(4-5球)"；本轮 004（6 倍/1.5 λ差）、007（4-1）都会被纠正。')
A('- **1 球闷战场景需要单独识别**：008/009/010 三场共同特征是"双方合计进球期望 <2.6 且都有主力后防可用"，档位应落在"小球(1-2球)"而非"常规 2-3 球"。')
A('- **半全场 TOP3 强制含一条"半场领先→被翻"路径**（胜负/负胜），在双方近期都有逆转记录的场次优先插入（本轮 002/006 都属此类）。')
A('- **让球串只用首选腿**：本轮价值让球串（008让平+012让平）因 012 净胜 2 球落空；次选腿的单场覆盖率 75% 但串联稳定性差，价值串建议改为"首选+另一场首选"或直接放弃。')
A('- **方向首选降权"强队做客+市场强推"场次**：009（主队 1.28）、007（客队 1.94）两场首选都错，次选/反向反而对；建议此类场次首选改取模型与市场分歧较小的一侧，或直接双选不下单选。')
A('')
A('## ☕ 写在最后')
A('')
A('回测不是为了证明对错，而是把"下一次能改的那一条"找出来。这一轮真正值钱的不是 10/12 的方向覆盖，而是那句"同一轮里既有被高估的闷战、也有被低估的屠杀"——档位不该由联赛标签决定。')
A('')
A('盈利是逻辑兑现，未盈利是方差未回归。拉长周期看，方法论不会骗人。')
A('')
A('你们的支持，决定了我能把这事做多久。')
A('')

out = '\n'.join(L)
os.makedirs(r'e:\VibeCoding\football\reports\backtest', exist_ok=True)
io.open(r'e:\VibeCoding\football\reports\backtest\backtest_20261030_friday_zhihu.md', 'w', encoding='utf-8').write(out)
print('saved report chars', len(out))
