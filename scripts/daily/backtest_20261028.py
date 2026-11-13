# -*- coding: utf-8 -*-
"""2026-10-28 周三 17 场回测（15 场已结算 + 2 场待结算）：7 维命中 + 22 个串关方案结算"""
import json, io

D = r'e:\VibeCoding\football\reports\data'
pred = {m['num']: m for m in json.load(io.open(D + r'\20261028_predictions.json', encoding='utf-8-sig'))}
res = {r['num']: r for r in json.load(io.open(D + r'\20261028_results_official.json', encoding='utf-8-sig'))}

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
        'crs_top5': crs_pick, 'crs_actual': crs_actual, 'crs': crs,
        'tier': rec['tier'], 'tier_hit': tier,
        'ht_top3': ht_pick, 'ht_actual': ht_actual, 'ht_hit': ht_hit,
        'lambda': (p['model']['lambda_home'], p['model']['lambda_away']),
        'conf': p['conf'],
        'k_dist': p['k_dist'], 'k_rec': p['k_rec'], 'k_consistent': p['k_consistent'],
        'line': s.get('line'),
    })

json.dump(rows, io.open(D + r'\20261028_backtest_rows.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

settled = [x for x in rows if x.get('status') != 'pending']
M = {'first': '首中', 'second': '次中', 'miss': '未中'}
print('=' * 150)
print('%-7s %-9s %-6s %-5s %-4s %-14s %-4s %-15s %-4s %-8s %-3s %-12s %-3s %-6s %-3s %-3s' % (
    '编号', '联赛', '比分', '半场', '总球', '方向(首%%)/次(%%)', '方向', '让球(首)/次', '让球', '总进球', '总', '半全场TOP3', '半全', '比分TOP5首位', '比分', '档位'))
print('=' * 150)
for x in rows:
    if x.get('status') == 'pending':
        print('%-7s %-9s 待结算（官方 matchResultStatus=1）' % (x['num'], x['league'])); continue
    print('%-7s %-9s %-6s %-5s %-4d %-14s %-4s %-15s %-4s %-8s %-3s %-12s %-3s %-6s %-3s %-3s' % (
        x['num'], x['league'], x['ft'], x['ht'], x['total'],
        '%s%.1f/%s%.1f' % (DIR[x['pred_dir']], x['p_dir'][{'home': 0, 'draw': 1, 'away': 2}[x['pred_dir']]],
                           DIR[x['pred_dir2']], x['p_dir'][{'home': 0, 'draw': 1, 'away': 2}[x['pred_dir2']]]),
        M[x['had']],
        HC[x['pred_hc']] + '/' + HC[x['pred_hc2']], M[x['hc']],
        '/'.join(str(t) + '球' for t in x['ttg_top2']), '✅' if x['ttg'] == 'hit' else '❌',
        '/'.join(x['hafu_top3']), '✅' if x['hafu'] == 'hit' else '❌',
        x['crs_top5'][0], '✅' if x['crs'] == 'hit' else '❌',
        '✅' if x['tier_hit'] == 'hit' else '❌', ))
print('=' * 150)


def stat(key, first_only=False):
    if first_only:
        n = sum(1 for x in settled if x.get(key) == 'first')
    else:
        n = sum(1 for x in settled if x.get(key) in ('first', 'second', 'hit'))
    return n, len(settled), n / len(settled) * 100


print('方向 首选 %d/%d=%.1f%% ｜含次选 %d/%d=%.1f%%' % (*stat('had', True), *stat('had')))
print('让球 首选 %d/%d=%.1f%% ｜含次选 %d/%d=%.1f%%' % (*stat('hc', True), *stat('hc')))
print('总进球TOP2 %d/%d=%.1f%%' % stat('ttg'))
print('半全场TOP3 %d/%d=%.1f%%' % stat('hafu'))
print('比分TOP5 %d/%d=%.1f%%' % stat('crs'))
print('大小球六档 %d/%d=%.1f%%' % stat('tier_hit'))
print('半场比分TOP3 %d/%d=%.1f%%' % stat('ht_hit'))
print('场均进球 %.2f ｜ 大2.5 %d/%d ｜ 平局 %d/%d' % (
    sum(x['total'] for x in settled) / len(settled),
    sum(1 for x in settled if x['total'] >= 3), len(settled),
    sum(1 for x in settled if x['actual_dir'] == 'draw'), len(settled)))
tot_hist = {}
for x in settled:
    tot_hist[x['total']] = tot_hist.get(x['total'], 0) + 1
print('总进球分布', dict(sorted(tot_hist.items())))

# ---- 串关（与分析报告一一对应，22 个方案） ----
P = [
    ('方向串A（稳健）', '方向串', 2.01, [('006', 'had', 'home'), ('005', 'had', 'away'), ('002', 'had', 'home')]),
    ('方向串B（价值）', '方向串', 3.63, [('002', 'had', 'home'), ('016', 'had', 'home'), ('010', 'had', 'away')]),
    ('稳健让球串', '让球串', 8.10, [('007', 'hhad', 'home'), ('004', 'hhad', 'home'), ('001', 'hhad', 'away')]),
    ('价值让球串', '让球串', 17.93, [('005', 'hhad', 'away'), ('006', 'hhad', 'home'), ('002', 'hhad', 'draw')]),
    ('半全场串A', '混合串', 13.76, [('006', 'hafu', '胜胜'), ('005', 'hafu', '负负'), ('002', 'hafu', '平胜')]),
    ('半全场串B', '混合串', 33.70, [('016', 'hafu', '胜胜'), ('010', 'hafu', '负负'), ('003', 'hafu', '平负')]),
    ('方向+半全场A', '混合串', 3.80, [('006', 'had', 'home'), ('016', 'hafu', '胜胜')]),
    ('方向+半全场B', '混合串', 4.99, [('014', 'had', 'away'), ('011', 'hafu', '胜胜')]),
    ('连续编号混合串A', '混合串', 15.18, [('012', 'hafu', '平胜'), ('013', 'ttg', 3)]),
    ('连续编号混合串B', '混合串', 16.15, [('015', 'hafu', '负负'), ('016', 'ttg', 2)]),
    ('总进球串A', '总进球串', 80.04, [('001', 'ttg', 2), ('008', 'ttg', 4), ('017', 'ttg', 3)]),
    ('总进球串B', '总进球串', 42.77, [('005', 'ttg', 3), ('010', 'ttg', 2), ('016', 'ttg', 2)]),
    ('连续编号总进球串①', '总进球串', 12.21, [('006', 'ttg', 2), ('007', 'ttg', 2)]),
    ('连续编号总进球串②', '总进球串', 10.87, [('013', 'ttg', 3), ('014', 'ttg', 2)]),
    ('高赔半全场串A', '高赔半全场串', 971.25, [('005', 'hafu', '平平'), ('013', 'hafu', '平胜'), ('001', 'hafu', '平负')]),
    ('高赔半全场串B', '高赔半全场串', 649.69, [('002', 'hafu', '平平'), ('004', 'hafu', '胜胜'), ('017', 'hafu', '负负')]),
    ('连续编号高赔半全场串①', '高赔半全场串', 32.79, [('001', 'hafu', '负负'), ('002', 'hafu', '平胜')]),
    ('连续编号高赔半全场串②', '高赔半全场串', 18.76, [('014', 'hafu', '平负'), ('015', 'hafu', '负负')]),
    ('混合串A', '半全场混合', 7.96, [('006', 'hafu', '胜胜'), ('005', 'ttg', 3)]),
    ('混合串B', '半全场混合', 11.96, [('016', 'hafu', '胜胜'), ('008', 'ttg', 4)]),
    ('连续编号混合总进球串①', '半全场混合', 18.72, [('011', 'hafu', '平胜'), ('012', 'ttg', 2)]),
    ('连续编号混合总进球串②', '半全场混合', 19.14, [('016', 'hafu', '平胜'), ('017', 'ttg', 3)]),
    ('稳健比分串', '比分串', 49.00, [('006', 'crs', '2-1'), ('005', 'crs', '1-2')]),
    ('搏冷比分串（反向推理）', '比分串', 55.25, [('004', 'crs', '1-1'), ('014', 'crs', '1-1')]),
    ('连续编号比分串①', '比分串', 45.50, [('005', 'crs', '1-2'), ('006', 'crs', '1-0')]),
    ('连续编号比分串②', '比分串', 112.00, [('005', 'crs', '2-3'), ('006', 'crs', '2-1')]),
    ('单挑比分①（015 单关）', '单挑比分', 8.00, [('015', 'crs', '1-1')]),
    ('单挑比分②', '单挑比分', 6.00, [('016', 'crs', '1-1')]),
]

KEY = lambda n: '周三' + n


def leg_ok(num, market, pick):
    s = res.get(KEY(num))
    if not s or not s.get('ft'):
        return None
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht'])
    if market == 'had':
        return ('home' if h > a else ('draw' if h == a else 'away')) == pick
    if market == 'hhad':
        adj = (h - a) + pred[KEY(num)]['recommendation']['hc_line']
        return ('home' if adj > 0 else ('draw' if adj == 0 else 'away')) == pick
    if market == 'crs':
        return ('%d-%d' % (h, a)) == str(pick)
    if market == 'ttg':
        return (h + a) == int(pick)
    if market == 'hafu':
        return HAFU[(code(hh, ha), code(h, a))] == pick
    return None


def leg_text(num, market, pick):
    s = res.get(KEY(num))
    if not s or not s.get('ft'):
        return '%s 待结算' % num
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht'])
    if market == 'had':
        return '%s %s(%s)' % (num, DIR[pick], s['ft'])
    if market == 'hhad':
        return '%s 让(%+d)%s(%s)' % (num, pred[KEY(num)]['recommendation']['hc_line'], HC[pick], s['ft'])
    if market == 'ttg':
        return '%s %d球(实%d球)' % (num, pick, h + a)
    if market == 'hafu':
        return '%s %s(实%s)' % (num, pick, HAFU[(code(hh, ha), code(h, a))])
    if market == 'crs':
        return '%s %s(实%s)' % (num, pick, s['ft'])
    return num


print()
print('=' * 170)
print('%-26s %-10s %-6s %-9s %s' % ('方案', '类型', '结果', '赔率', '逐腿（实际）'))
print('=' * 170)
hit = 0
stake = ret = 0.0
out_parlays = []
for name, cat, odds, legs in P:
    oks = [leg_ok(*lg) for lg in legs]
    pend = any(o is None for o in oks)
    allok = all(o is True for o in oks) and not pend
    stake += 1
    if allok:
        hit += 1; ret += odds
    out_parlays.append({'name': name, 'cat': cat, 'odds': odds, 'hit': allok,
                        'pending': pend,
                        'legs': [{'match': lg[0], 'market': lg[1], 'pick': lg[2], 'ok': o}
                                 for lg, o in zip(legs, oks)],
                        'results': [leg_text(*lg) for lg in legs]})
    marks = []
    for lg, o in zip(legs, oks):
        mark = '✅' if o is True else ('⏳' if o is None else '❌')
        marks.append(leg_text(*lg) + ' ' + mark)
    tag = '✅中' if allok else ('⏳待' if pend else '❌失')
    print('%-26s %-10s %-6s %-9.2f %s' % (name, cat, tag, odds, ' ｜ '.join(marks)))
print('=' * 170)
played = [p for p in out_parlays if not p['pending']]
print('串关命中 %d/%d=%.1f%%（另有 %d 个方案含未结算场次）' % (hit, len(played), hit / len(played) * 100, len(out_parlays) - len(played)))
for cat in ['方向串', '让球串', '混合串', '总进球串', '高赔半全场串', '半全场混合', '比分串']:
    sub = [s for s in out_parlays if s['cat'] == cat]
    done = [s for s in sub if not s['pending']]
    print('  %-10s %d/%d%s' % (cat, sum(1 for s in sub if s['hit']), len(done),
                               ('（含%d待结算）' % (len(sub) - len(done))) if len(sub) != len(done) else ''))

json.dump({'rows': rows, 'parlays': out_parlays},
          io.open(D + r'\20261028_backtest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved 20261028_backtest.json')
