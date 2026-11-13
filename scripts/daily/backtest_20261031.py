# -*- coding: utf-8 -*-
"""2026-10-31 周六 28 场：结算 6 维 + 26 个串关方案"""
import json, io

D = r'e:\VibeCoding\football\reports\data'
pred = {m['num']: m for m in json.load(io.open(D + r'\20261031_predictions.json', encoding='utf-8-sig'))}
res = {r['num']: r for r in json.load(io.open(D + r'\20261031_results_official.json', encoding='utf-8-sig'))}

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
        'kickoff': p['kickoff'],
    })

settled = [x for x in rows if x.get('status') != 'pending']
N = len(settled)


def stat(key, first_only=False):
    n = sum(1 for x in settled if x.get(key) == ('first' if first_only else ('first', 'second', 'hit'))) if False else \
        sum(1 for x in settled if (x.get(key) in ('first', 'second', 'hit')))
    if first_only:
        n = sum(1 for x in settled if x.get(key) == 'first')
    return n, N, n / N * 100


# ---- 串关（与 20261031 分析报告一一对应，26 个方案） ----
P = [
    ('方向串A（稳健）', '方向串', 3.55, [('024', 'had', 'home'), ('010', 'had', 'home'), ('018', 'had', 'home')]),
    ('方向串B（价值）', '方向串', 4.45, [('003', 'had', 'home'), ('008', 'had', 'away'), ('006', 'had', 'home')]),
    ('稳健让球串', '让球串', 2.21, [('017', 'hhad', 'home'), ('015', 'hhad', 'home')]),
    ('价值让球串', '让球串', 13.69, [('024', 'hhad', 'draw'), ('026', 'hhad', 'draw')]),
    ('方向+半全场A', '混合串', 2.44, [('024', 'had', 'home'), ('021', 'hafu', '负负')]),
    ('方向+半全场B', '混合串', 5.46, [('018', 'had', 'home'), ('026', 'hafu', '胜胜')]),
    ('连续编号混合串A', '混合串', 7.04, [('017', 'had', 'home'), ('018', 'hafu', '胜胜')]),
    ('连续编号混合串B', '混合串', 7.93, [('019', 'hafu', '负负'), ('020', 'ttg', 2)]),
    ('总进球串A', '总进球串', 86.48, [('003', 'ttg', 4), ('006', 'ttg', 4), ('014', 'ttg', 4)]),
    ('总进球串B', '总进球串', 49.15, [('010', 'ttg', 3), ('018', 'ttg', 2), ('026', 'ttg', 2)]),
    ('连续编号总进球串①', '总进球串', 11.56, [('017', 'ttg', 2), ('018', 'ttg', 2)]),
    ('连续编号总进球串②', '总进球串', 18.27, [('023', 'ttg', 3), ('024', 'ttg', 2)]),
    ('高赔半全场串A', '高赔半全场串', 10.27, [('003', 'hafu', '胜胜'), ('021', 'hafu', '负负'), ('024', 'hafu', '胜胜')]),
    ('高赔半全场串B', '高赔半全场串', 8.11, [('010', 'hafu', '胜胜'), ('019', 'hafu', '负负'), ('027', 'hafu', '胜胜')]),
    ('连续编号高赔半全场串①', '高赔半全场串', 11.40, [('001', 'hafu', '平负'), ('002', 'hafu', '胜胜')]),
    ('连续编号高赔半全场串②', '高赔半全场串', 27.00, [('025', 'hafu', '平胜'), ('026', 'hafu', '胜胜')]),
    ('混合串A', '半全场混合', 13.40, [('018', 'hafu', '胜胜'), ('003', 'ttg', 4)]),
    ('混合串B', '半全场混合', 8.61, [('021', 'hafu', '负负'), ('024', 'ttg', 2)]),
    ('连续编号混合总进球串①', '半全场混合', 17.60, [('015', 'ttg', 2), ('016', 'hafu', '负负')]),
    ('连续编号混合总进球串②', '半全场混合', 7.93, [('019', 'hafu', '负负'), ('020', 'ttg', 2)]),
    ('稳健比分串', '比分串', 47.25, [('024', 'crs', '2-0'), ('005', 'crs', '1-1')]),
    ('搏冷比分串（反向推理）', '比分串', 136.50, [('006', 'crs', '1-2'), ('022', 'crs', '1-2')]),
    ('连续编号比分串①', '比分串', 52.31, [('003', 'crs', '2-1'), ('004', 'crs', '1-2')]),
    ('连续编号比分串②', '比分串', 68.00, [('017', 'crs', '2-1'), ('018', 'crs', '1-0')]),
    ('单挑比分①', '单挑比分', 7.00, [('024', 'crs', '2-0')]),
    ('单挑比分②', '单挑比分', 7.00, [('027', 'crs', '3-0')]),
]


def leg_ok(num, market, pick):
    s = res.get('周六' + num)
    if not s or not s.get('ft'):
        return None
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht'])
    if market == 'had':
        return ('home' if h > a else ('draw' if h == a else 'away')) == pick
    if market == 'hhad':
        adj = (h - a) + pred['周六' + num]['recommendation']['hc_line']
        return ('home' if adj > 0 else ('draw' if adj == 0 else 'away')) == pick
    if market == 'crs':
        return ('%d-%d' % (h, a)) == str(pick)
    if market == 'ttg':
        return (h + a) == int(pick)
    if market == 'hafu':
        return HAFU[(code(hh, ha), code(h, a))] == pick
    return None


def leg_text(num, market, pick):
    s = res.get('周六' + num)
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht'])
    if market == 'had':
        return '%s %s(%s)' % (num, DIR[pick], s['ft'])
    if market == 'hhad':
        return '%s 让(%+d)%s(%s)' % (num, pred['周六' + num]['recommendation']['hc_line'], HC[pick], s['ft'])
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
          io.open(D + r'\20261031_backtest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(rows, io.open(D + r'\20261031_backtest_rows.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('=== 6维 ===')
print('方向 首选 %d/%d=%.1f%% 含次选 %d/%d=%.1f%%' % (*stat('had', True), *stat('had')))
print('让球 首选 %d/%d=%.1f%% 含次选 %d/%d=%.1f%%' % (*stat('hc', True), *stat('hc')))
print('总进球TOP2 %d/%d=%.1f%%' % stat('ttg'))
print('半全场TOP3 %d/%d=%.1f%%' % stat('hafu'))
print('比分TOP5 %d/%d=%.1f%%' % stat('crs'))
print('半场比分TOP3 %d/%d=%.1f%%' % stat('ht_hit'))
print('大小球六档 %d/%d=%.1f%%' % stat('tier_hit'))
print('进球分布', [x['total'] for x in settled], '场均%.2f' % (sum(x['total'] for x in settled) / N))
print('平局', sum(1 for x in settled if x['actual_dir'] == 'draw'), '大2.5', sum(1 for x in settled if x['total'] >= 3))
print('=== 串关 %d/%d 回收%.2f 投入%d ===' % (hit, len(out_parlays), ret, len(out_parlays)))
for q in out_parlays:
    print(('✅' if q['hit'] else '❌'), q['name'], q['odds'], '|', ' / '.join(
        '%s%s%s' % (lg['match'], lg['market'], '✔' if lg['ok'] else '✘') for lg in q['legs']))
print('=== 逐场 ===')
for x in settled:
    print(x['num'], x['ft'], 'HT', x['ht'], '| 方向', DIR[x['pred_dir']], DIR[x['pred_dir2']], '→', DIR[x['actual_dir']], x['had'],
          '| 让', x['hhad_line'], HC[x['pred_hc']], HC[x['pred_hc2']], '→', HC[x['actual_hc']], x['hc'],
          '| TTG', x['ttg_top2'], '实', x['total'], x['ttg'],
          '| HAFU', x['hafu_top3'], '实', x['hafu_actual'], x['hafu'],
          '| CRS', x['crs_top5'], '实', x['crs_actual'], x['crs'], x['crs_rank'],
          '| HT', x['ht_top3'], '实', x['ht_actual'], x['ht_hit'],
          '| 档', x['tier'], x['tier_hit'], '| conf', x['conf'])
print('sorted by conf')
for x in sorted(settled, key=lambda y: y['conf'], reverse=True):
    print(x['conf'], x['num'], x['had'], x['hc'], x['ttg'])

# ---------------- 报告生成 ----------------
L = []
A = L.append
A('# 【回测】2026-11-01（周日）10-31周六28场回测 | 方向含次选24/28、比分TOP5仅9/28，串关5/26首次回正')
A('')
A('> **报告说明：** 本文为赛后**回测报告**（标题标注【回测】），对比预测与实际结果并统计命中率。赛前**分析报告**（标题标注【分析】）提供方向/比分/总进球等预测推荐。历史报告可去主页查找。')
A('')
A('> **风险提示：** 回测结果仅供参考，历史命中不代表未来表现。赔率数据以采集时为准。**理性看待预测，切勿沉迷赌博。**')
A('')
A('> **⚠️ 免责声明：** 本文所有回测数据、命中率统计、教训分析仅供学习交流参考，不构成任何投注建议。回测结果具有时效性，历史命中不代表未来表现。内容仅供参考，如有错漏请谅解。请遵守当地法律法规，理性购彩，量力而行。')
A('')
A('*每日更新，关注主页获取最新赛事分析*')
A('')
A('10-31 共 28 场（001-028，005/006/025 单关），全部已结算。**方向首选 18/28=64.3%、含次选 24/28=85.7%**，是规则79口径下覆盖最好的一轮；**半场比分 TOP3 22/28=78.6%、半全场 TOP3 20/28=71.4%** 也站得住。真正的短板换成了两处：**让球首选 10/28=35.7%**（+1 盘 13 场全押让胜，只兑现 6 场）和**比分 TOP5 9/28=32.1%**（0-0 全场缺席）。串关 **5/26=19.2%、回收 32.77/投入 26、ROI +26.0%**，是 10-19 以来首次回正。')
A('')
A('## 总览')
A('')
A('| 编号 | 对阵 | 赛事 | 预测方向(首选/次选) | 实际方向 | 命中 | 让球 | 让球命中 | 总进球 | 进球命中 | 半全场TOP3 | 半全场命中 | 比分TOP5首位 | 比分命中 |')
A('|:---:|:---|:---|:---|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|')
mk = {'first': '✅首', 'second': '✅次', 'miss': '❌'}
for x in rows:
    cells = [
        x['num'].replace('周六', ''),
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
A('> 命中汇总：方向首选 18/28=64.3%｜含次选 24/28=85.7%｜让球首选 10/28=35.7%｜含次选 15/28=53.6%｜总进球TOP2 14/28=50.0%｜半全场TOP3 20/28=71.4%｜比分TOP5 9/28=32.1%｜半场比分TOP3 22/28=78.6%｜大小球档位 14/28=50.0%。')
A('')
A('## 逐场回测')

NOTE = {
 '001': '方向首选客胜（模型50.5%/市场54.5%）命中，半全场"负负"、半场0-1也中；但0-4的净胜4球把让(+1)让胜与"常规2-3球"档一起打穿，TTG给2/3球、比分TOP5上限1-2。',
 '002': '次选客胜兜住（首选主胜51%落空），让(-1)让负首选、TTG 3球、比分1-2第5位、半场0-1四线命中；唯半全场实际"负负"不在TOP3（给胜胜/平胜/平平）——次选方向与半全场TOP3脱节。',
 '003': '首选主胜（60.5%）、TTG 4球、半全场胜胜、半场1-0全中；但4-0把让(-1)让平/让负双杀，比分上限3-1，而档位却给到"穿盘可能(6-7+球)"——单场跳了两档。',
 '004': '低星场里最完整的一场：次选平兜住、让(+1)让胜首选、TTG 2球、比分1-1第1位、半场0-0、半全场平平全中，六维只差首选方向（客胜→平）。',
 '005': '单关。首选平（35%）命中、让(+1)让胜、半场0-0命中；但比分TOP5给1-1/1-2/2-1/2-2/0-2，偏偏没有0-0，半全场TOP3也没有"平平"，TTG 3/2球与实际0球是本轮最大偏差。',
 '006': '单关。首选主胜、半场0-0、半全场"平胜"命中；让(-1)实际让胜（净胜2球），模型让负/让平双错，TTG 3/4球与实际2球、比分TOP5无2-0。',
 '007': '首选客胜（54%）命中、半全场负负、半场0-1；1-3净负2球让(+1)打成让负，模型让胜/让平双错，TTG 2/3球差2球、比分上限1-2。',
 '008': '首选客胜、半全场负负、比分0-2第3位、半场0-1、TTG 2球、档位常规——五线命中；唯让(+1)实际让负，模型双选让胜/让平。',
 '009': '首选主胜、TTG 3球、半全场平胜、比分2-1第2位，让(-1)让平由次选兜住；唯半场1-1不在TOP3（0-0/1-0/0-1）。',
 '010': '次选客胜兜住（首选主胜60%落空）、让(-1)让负次选、半全场负负；但2-4共6球，TTG 3/4球、常规档、比分TOP5（上限1-2）、半场（给0-0/1-0/1-1，实际1-2）全部落空。',
 '011': '首选客胜、TTG 2球、半全场负负、比分0-2第3位、半场0-1、档位常规五线命中；让(+1)实际让负，模型让胜/让平双错。',
 '012': '次选客胜兜住、让(+1)让平次选兜住、TTG 3球、比分1-2第3位、半场1-0；唯半全场实际"胜负"（1-0→1-2）不在TOP3，属"半场领先被翻"路径缺口。',
 '013': '分歧场标出的场次，实际0-0：首选客胜/次选主胜双错，TTG 3/2球、档位常规、比分TOP5无0-0、半全场TOP3无平平；只有让(-1)让负与半场0-0命中。',
 '014': '首选主胜、让(+1)让胜、半全场平胜、半场0-0命中；但档位给"大球(4-5球)"、TTG 4/3球，实际2球，比分TOP5也没有2-0。',
 '015': '首选主胜、让(+1)让胜、半全场胜胜命中；3-1净胜2球，TTG 2/3球差2球、比分上限2-0、半场2-0不在TOP3。',
 '016': '搏客队失败：首选客胜/次选平双错（实际主队2-0），让(-1)让负/让平也双错（实际让胜）；命中TTG 2球、半全场胜胜、半场1-0、档位常规。',
 '017': '次选平兜住、让(+1)让胜首选、半场0-1命中；TTG 2/3球与实际4球、比分上限2-1、半全场实际"负平"（0-1→2-2）不在TOP3。',
 '018': '首选主胜、TTG 2球、半全场胜胜、比分2-0第3位、半场1-0、档位常规——六维中五；唯让(-1)实际让胜（净胜2球），模型让负/让平双错。',
 '019': '首选客胜、TTG 3球、半全场负负、半场0-1、档位常规命中；让(+1)让胜/让平双错（净负3球→让负），比分TOP5上限0-2。',
 '020': '搏客队失败：首选客胜/次选平双错（实际3-0），让(-1)让负/让平双错（实际让胜），半全场实际"胜胜"也不在TOP3（给负负/平平/平负）；仅TTG 3球、半场1-0、档位常规命中。',
 '021': '首选客胜（58%）、半全场负负命中，混合串A与高赔半全场串A的这条腿兑现；但2-5共7球，TTG 3/2球、常规档、比分上限1-3、半场（给0-0/0-1/1-1，实际0-4）全被打穿。',
 '022': '首选主胜、TTG 2球、半全场胜胜、半场1-0、档位常规；让(-1)实际让胜，模型让负/让平双错，比分TOP5无2-0；搏冷比分串的1-2同步落空。',
 '023': '分歧场标出的场次，实际2-2：首选主胜/次选客胜双错，TTG 3/2球、常规档、比分TOP5无2-2、半全场实际"胜平"不在TOP3；只有让(-2)让负与半场1-0命中。',
 '024': '本轮唯一六维全中：首选主胜（71.8%）、TTG 3球、半全场胜胜、比分2-1第4位、半场2-0、档位常规，让(-1)让平由次选兜住——强弱差清晰、主场碾压的教科书样本。',
 '025': '单关。首选主胜（37.9%）命中、让(+1)让胜、半全场胜胜；但3-1共4球高出TTG 3/2球，比分上限2-2，半场3-1不在TOP3（给0-0/1-0/0-1）——德比半场定调被低估。',
 '026': '次选平兜住、让(-1)让负首选、TTG 2球、比分1-1第1位、半场1-0、档位常规；唯半全场实际"胜平"（1-0→1-1）不在TOP3。',
 '027': '首选主胜（77%）、半全场胜胜命中；但6-1净胜5球，让(-3)实际让胜（模型让负/让平双错），TTG 4/3球与7球、档位"大球"与7球、比分上限3-1、半场（给1-0/0-0/2-0，实际4-0）全部落空。',
 '028': '首选主胜、半全场胜胜、半场1-0命中，让(-1)让平次选兜住；但TTG 3/4球与实际1球、档位常规、比分TOP5无1-0（给1-1/2-1/3-1/2-2/1-2）。',
}

for x in settled:
    p = pred[x['num']]
    A('### %s %s vs %s（%s）' % (x['num'].replace('周六', ''), x['home'], x['away'], x['league']))
    A('')
    t = x['kickoff'][:5]
    d = '11-01 ' if int(t.split(':')[0]) < 6 else '10-31 '
    A('⏰ %s%s ｜ 🏟 %s ｜ **%s**' % (d, t, p['venue']['name'], x['ft']))
    A('')
    A('**赛果：** 半场%s → 全场%s ｜ 总进球%d ｜ %s' % (x['ht'], x['ft'], x['total'], DIR[x['actual_dir']]))
    A('')
    A('| 维度 | 预测 | 实际 | 命中 |')
    A('|:---|:---|:---|:---:|')
    mk2 = {'first': '✅首中', 'second': '✅次中', 'miss': '❌'}
    A('| **方向** | %s / %s | %s | %s |' % (DIR[x['pred_dir']], DIR[x['pred_dir2']], DIR[x['actual_dir']], mk2[x['had']]))
    A('| **让球** | 让(%+d)%s / 让(%+d)%s | 让(%+d)%s | %s |' % (
        x['hhad_line'], HC[x['pred_hc']], x['hhad_line'], HC[x['pred_hc2']],
        x['hhad_line'], HC[x['actual_hc']], mk2[x['hc']]))
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
    A('> %s' % NOTE.get(x['num'].replace('周六', ''), ''))
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
dir_miss = [x['num'].replace('周六', '') for x in settled if x['had'] == 'miss']
hc_miss = [x['num'].replace('周六', '') for x in settled if x['hc'] == 'miss']
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
A('**按置信度分层：** ★★★（024/027）首选 2/2 ｜★★（14场）首选 9/14、含次选 12/14 ｜★（004/005/008/012/016/017）首选 2/6、含次选 5/6 ｜☆（006/013/014/015/022/025）首选 5/6、含次选 5/6 —— 星级与方向命中依旧反向，最低星的一档反而最稳。')
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
A('> 串关 **%d/%d=%.1f%%**（回收 %.2f / 投入 %d，ROI **%+.1f%%**），是 10-19 以来首次回正。命中的 5 个方案全部含"方向腿或半全场腿"：方向串B（003主胜+008客胜+006主胜，4.45）、稳健让球串（017让胜+015让胜，2.21）、方向+半全场A（024主胜+021负负，2.44）、高赔半全场串A（003胜胜+021负负+024胜胜，10.27）、混合串A（018胜胜+003 4球，13.40）。' % (
    hit, len(out_parlays), hit / len(out_parlays) * 100, ret, len(out_parlays),
    (ret - len(out_parlays)) / len(out_parlays) * 100))
A('')
A('> **8 个比分串/单挑全灭**（含 136.50 倍的搏冷比分串）：稳健串的 024 2-0 被 2-1 顶掉、005 1-1 被 0-0 顶掉，连续编号①的 003 2-1/004 1-2 双双落空。比分串在 28 场样本里依旧不具备可投性。')
A('')
A('## 关键发现')
A('')
A('**1. 方向含次选 85.7% 是规则79口径下最好的一轮，首选 64.3% 也首次站上 60%。** 4 场未中分成两类：016/020 是"搏客队"主动站到了主队大胜的对立面（实际 2-0/3-0）；013/023 是模型自身分歧场，实际都打成平局——两场次选都给了另一侧胜负方向，**平局仍然没有进双选**。')
A('')
A('**2. 让球成为唯一系统性短板（首选35.7%、含次选53.6%）。** 13 场让(+1)的首选清一色"让胜"（受让方不败），只兑现 6 场；13 场让(-1)有 10 场首选"让负"，而实际主队打出让胜的有 6 场、让负只有 4 场。**"无条件净胜球众数"在强弱分明的德甲/西甲把让球盘当成了"少输当赢"。**')
A('')
A('**3. 进球端回到 50%，但两端极端场同时失手。** 0 球场次（005/013）与 ≥6 球三场（010 6球、021 7球、027 7球）全部不在 TOP2；003 反而把 4 球的比赛档位给到"穿盘可能(6-7+球)"——**档位在单场上跳两档**，和 10-30 的"联赛标签压过实力差"是同一个病。')
A('')
A('**4. 比分 TOP5 32.1% 是本轮最弱维度，0-0 全场缺席。** 005 首选平局却只给 1-1、013 实际 0-0 也不在池内；净胜≥2 的覆盖同样薄（015/025 的 3-1、003 的 4-0、021 的 2-5、027 的 6-1 全部在外）。**比分池的"零封/闷平"这一格从来没有被主动放进去。**')
A('')
A('**5. 半全场 71.4% 但 TOP3 与首选方向脱节。** 005/013 两场平局首选，TOP3 分别是"负负/胜胜/平负"与"负负/胜胜/平负"——**没有一条"平平"**；002 次选客胜、实际负负，TOP3 也没有负负。这是可以直接修的硬 bug，不是概率问题。')
A('')
A('**6. 串关 5/26、ROI +26.0%，首次回正。** 赢的全部是"方向腿+半全场腿"结构，说明 10-30 的结论（方向腿+半全场腿是唯一可复制的结构）在本轮得到正向验证；输的 21 个方案里，8 个比分/单挑、5 个总进球串是主要出血点。')
A('')
A('## 待改进')
A('')
A('- **让球首选结构性修正**：±1 盘把"让平"设为强制第二席；让(-1) 且模型主胜≥45% 时首选不得给让负；让(+1) 且客队概率≥45% 时首选不得给让胜。')
A('- **半全场 TOP3 与首选方向绑定**：平局首选场次必须含"平平"，客胜次选场次必须含"负负"，主胜首选场次必须含"胜胜"；此项作为报告审核器的硬校验。')
A('- **比分池强制补两格**：平局首选场必含 0-0；主胜首选且净胜球众数≥2 时必含 2-0 或 3-1。')
A('- **档位禁止单场跳两档**：一次只能上/下移一档；涉及 0-1 球与 ≥6 球的两端场次，全天 TOP2 各留一场覆盖。')
A('- **比分串/单挑继续暂停**，串关资金集中到"方向腿+半全场腿"与首选让球腿；单注≤1% 的娱乐串仍只作娱乐。')
A('')
A('## ☕ 写在最后')
A('')
A('28 场里最值钱的一条不是 85.7% 的方向覆盖，而是那句"让球盘被当成了少输当赢"。方向能到 64%，说明基本面链路是通的；让球和比分掉队，说明**同一套净胜球众数在不同盘口上需要不同的边界条件**——这不是模型不行，是规则还没跟上。')
A('')
A('盈利是逻辑兑现，未盈利是方差未回归。拉长周期看，方法论不会骗人。')
A('')
A('你们的支持，决定了我能把这事做多久。')
A('')

out = '\n'.join(L)
import os
os.makedirs(r'e:\VibeCoding\football\reports\backtest', exist_ok=True)
io.open(r'e:\VibeCoding\football\reports\backtest\backtest_20261031_saturday_zhihu.md', 'w', encoding='utf-8').write(out)
print('saved report chars', len(out))
