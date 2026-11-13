# -*- coding: utf-8 -*-
"""2026-10-27 周二 10 场回测：7 维命中 + 26 个串关方案结算"""
import json, io

D = r'e:\VibeCoding\football\reports\data'
pred = {m['num']: m for m in json.load(io.open(D + r'\20261027_model_output.json', encoding='utf-8-sig'))}
res = {r['num']: r for r in json.load(io.open(D + r'\20261027_results_official.json', encoding='utf-8-sig'))}

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
    r = pred[num]
    s = res.get(num)
    if not s or not s.get('ft'):
        rows.append({'num': num, 'status': 'no_result'}); continue
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht']) if s.get('ht') else (None, None)
    total = h + a
    actual = 'home' if h > a else ('draw' if h == a else 'away')
    had = 'first' if r['primary'] == actual else ('second' if r['secondary'] == actual else 'miss')
    gl = r.get('hhad_line')
    hh_res = None
    if gl is not None:
        adj = (h - a) + gl
        hh_res = 'home' if adj > 0 else ('draw' if adj == 0 else 'away')
    hc = ('first' if r['hc_first'] == hh_res else ('second' if r['hc_second'] == hh_res else 'miss')) if hh_res else None
    ttg = 'hit' if total in (r.get('ttg_top2') or []) else 'miss'
    hafu_actual = HAFU.get((code(hh, ha), code(h, a))) if hh is not None else None
    hafu = 'hit' if hafu_actual in [k for k, _ in r.get('htft_top3', [])] else ('na' if hafu_actual is None else 'miss')
    sc = ['%d-%d' % (x, y) for x, y, _ in r.get('top_scores', [])[:5]]
    sc_actual = '%d-%d' % (h, a)
    crs = 'hit' if sc_actual in sc else 'miss'
    tier = 'hit' if tier_hit(r['tier'], total) else 'miss'
    hts = ['%d-%d' % (x, y) for x, y, _ in r.get('ht_scores', [])[:3]]
    ht_hit = 'hit' if hh is not None and ('%d-%d' % (hh, ha)) in hts else ('na' if hh is None else 'miss')
    rows.append({'num': num, 'league': r['league'], 'home': r['home'], 'away': r['away'],
                 'ft': s['ft'], 'ht': s['ht'], 'total': total,
                 'pred_dir': r['primary'], 'pred_dir2': r['secondary'], 'actual_dir': actual, 'had': had,
                 'hhad_line': gl, 'pred_hc': r['hc_first'], 'pred_hc2': r['hc_second'], 'actual_hc': hh_res, 'hc': hc,
                 'ttg_top2': r.get('ttg_top2'), 'ttg': ttg,
                 'hafu_top3': [k for k, _ in r.get('htft_top3', [])], 'hafu_actual': hafu_actual, 'hafu': hafu,
                 'crs_top5': sc, 'crs_actual': sc_actual, 'crs': crs,
                 'tier': r['tier'], 'tier_hit': tier,
                 'ht_top3': hts, 'ht_actual': '%d-%d' % (hh, ha) if hh is not None else None, 'ht_hit': ht_hit,
                 'lambda': (r['lambda_home'], r['lambda_away']), 'conf': r.get('conf', ''),
                 'p': (round(r['fused']['home'] * 100, 1), round(r['fused']['draw'] * 100, 1), round(r['fused']['away'] * 100, 1))})

json.dump(rows, io.open(D + r'\20261027_backtest_rows.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

M = {'first': '首中', 'second': '次中', 'miss': '未中'}
print('=' * 132)
print('%-8s %-10s %-6s %-6s %-4s %-10s %-4s %-9s %-4s %-7s %-4s %-8s %-4s %-7s %-4s %-4s' % (
    '编号', '联赛', '比分', '半场', '总球', '方向(首/次)', '方向', '让球(首/次)', '让球', '总进球', '总进球', '半全场', '半全场', '比分', '比分', '档位'))
print('=' * 132)
for x in rows:
    if x.get('status') == 'no_result':
        print(x['num'], '无赛果'); continue
    print('%-8s %-10s %-6s %-6s %-4d %-10s %-4s %-9s %-4s %-7s %-4s %-8s %-4s %-7s %-4s %-4s' % (
        x['num'], x['league'], x['ft'], x['ht'], x['total'],
        DIR[x['pred_dir']] + '/' + DIR[x['pred_dir2']], M[x['had']],
        (HC[x['pred_hc']] + '/' + HC[x['pred_hc2']]) if x['hhad_line'] is not None else '—',
        M.get(x['hc'], '—'),
        '/'.join(str(t) + '球' for t in x['ttg_top2']), '✅' if x['ttg'] == 'hit' else '❌',
        '/'.join(x['hafu_top3']), '✅' if x['hafu'] == 'hit' else ('—' if x['hafu'] == 'na' else '❌'),
        x['crs_actual'], '✅' if x['crs'] == 'hit' else '❌',
        '✅' if x['tier_hit'] == 'hit' else '❌'))
print('=' * 132)


def stat(key, first_only=False):
    if first_only:
        n = sum(1 for x in rows if x.get(key) == 'first')
    else:
        n = sum(1 for x in rows if x.get(key) in ('first', 'second', 'hit'))
    return n, len(rows), n / len(rows) * 100


print('方向 首选 %d/%d=%.1f%% ｜含次选 %d/%d=%.1f%%' % (*stat('had', True), *stat('had')))
print('让球 首选 %d/%d=%.1f%% ｜含次选 %d/%d=%.1f%%' % (*stat('hc', True), *stat('hc')))
print('总进球TOP2 %d/%d=%.1f%%' % stat('ttg'))
print('半全场TOP3 %d/%d=%.1f%%' % stat('hafu'))
print('比分TOP5 %d/%d=%.1f%%' % stat('crs'))
print('大小球六档 %d/%d=%.1f%%' % stat('tier_hit'))
print('半场比分TOP3 %d/%d=%.1f%%' % stat('ht_hit'))
print('场均进球 %.2f ｜ 大2.5 %d/10' % (sum(x['total'] for x in rows) / len(rows), sum(1 for x in rows if x['total'] >= 3)))

# ---- 串关 ----
P = [
    ('方向串A（稳健）', '方向串', 2.60, [('周二009', 'had', 'home'), ('周二007', 'had', 'home'), ('周二008', 'had', 'home')]),
    ('方向串B（价值）', '方向串', 7.65, [('周二005', 'had', 'away'), ('周二010', 'had', 'away'), ('周二002', 'had', 'home')]),
    ('稳健让球串', '让球串', 6.49, [('周二002', 'hhad', 'home'), ('周二003', 'hhad', 'away'), ('周二001', 'hhad', 'away')]),
    ('价值让球串', '让球串', 6.32, [('周二009', 'hhad', 'home'), ('周二007', 'hhad', 'home'), ('周二008', 'hhad', 'away')]),
    ('半全场串A', '混合串', 23.14, [('周二009', 'hafu', '胜胜'), ('周二005', 'hafu', '负负'), ('周二007', 'hafu', '平胜')]),
    ('半全场串B', '混合串', 159.12, [('周二008', 'hafu', '胜胜'), ('周二001', 'hafu', '负负'), ('周二002', 'hafu', '平平')]),
    ('方向+半全场A', '混合串', 6.17, [('周二009', 'had', 'home'), ('周二002', 'hafu', '平平')]),
    ('方向+半全场B', '混合串', 5.50, [('周二007', 'had', 'home'), ('周二003', 'hafu', '负负')]),
    ('连续编号混合串A', '混合串', 14.88, [('周二007', 'hafu', '平胜'), ('周二008', 'ttg', 3)]),
    ('连续编号混合串B', '混合串', 18.10, [('周二008', 'hafu', '平胜'), ('周二009', 'ttg', 2)]),
    ('总进球串A', '总进球串', 59.45, [('周二001', 'ttg', 3), ('周二006', 'ttg', 2), ('周二004', 'ttg', 4)]),
    ('总进球串B', '总进球串', 53.53, [('周二002', 'ttg', 2), ('周二003', 'ttg', 3), ('周二008', 'ttg', 4)]),
    ('连续编号总进球串①', '总进球串', 12.94, [('周二004', 'ttg', 3), ('周二005', 'ttg', 2)]),
    ('连续编号总进球串②', '总进球串', 13.30, [('周二009', 'ttg', 3), ('周二010', 'ttg', 2)]),
    ('高赔半全场串A', '高赔半全场串', 1183.20, [('周二001', 'hafu', '平负'), ('周二007', 'hafu', '平平'), ('周二010', 'hafu', '胜胜')]),
    ('高赔半全场串B', '高赔半全场串', 292.56, [('周二009', 'hafu', '平平'), ('周二004', 'hafu', '平胜'), ('周二005', 'hafu', '平负')]),
    ('连续编号高赔半全场串①', '高赔半全场串', 21.93, [('周二002', 'hafu', '平平'), ('周二003', 'hafu', '负负')]),
    ('连续编号高赔半全场串②', '高赔半全场串', 30.00, [('周二009', 'hafu', '平胜'), ('周二010', 'hafu', '胜胜')]),
    ('混合串A', '半全场混合', 5.69, [('周二009', 'hafu', '胜胜'), ('周二005', 'ttg', 3)]),
    ('混合串B', '半全场混合', 19.57, [('周二006', 'hafu', '胜胜'), ('周二004', 'ttg', 4)]),
    ('连续编号混合总进球串①', '半全场混合', 14.88, [('周二007', 'hafu', '平胜'), ('周二008', 'ttg', 3)]),
    ('连续编号混合总进球串②', '半全场混合', 14.25, [('周二009', 'hafu', '平胜'), ('周二010', 'ttg', 2)]),
    ('稳健比分串', '比分串', 46.90, [('周二009', 'crs', '1-0'), ('周二007', 'crs', '2-1')]),
    ('搏冷比分串', '比分串', 126.00, [('周二009', 'crs', '1-1'), ('周二007', 'crs', '2-2')]),
    ('连续编号比分串①', '比分串', 45.50, [('周二007', 'crs', '2-1'), ('周二008', 'crs', '2-1')]),
    ('连续编号比分串②', '比分串', 43.55, [('周二008', 'crs', '2-1'), ('周二009', 'crs', '1-0')]),
]


def leg_ok(num, market, pick):
    s = res.get(num)
    if not s or not s.get('ft'):
        return None
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht']) if s.get('ht') else (None, None)
    if market == 'had':
        return ('home' if h > a else ('draw' if h == a else 'away')) == pick
    if market == 'hhad':
        gl = pred[num].get('hhad_line')
        adj = (h - a) + gl
        return ('home' if adj > 0 else ('draw' if adj == 0 else 'away')) == pick
    if market == 'crs':
        return ('%d-%d' % (h, a)) == str(pick)
    if market == 'ttg':
        return (h + a) == int(pick)
    if market == 'hafu':
        if hh is None:
            return None
        return HAFU[(code(hh, ha), code(h, a))] == pick
    return None


def leg_text(num, market, pick):
    s = res[num]
    if market == 'had':
        return '%s %s(%s)' % (num[2:], DIR[pick], s['ft'])
    if market == 'hhad':
        return '%s 让(%+d)%s(%s)' % (num[2:], pred[num]['hhad_line'], HC[pick], s['ft'])
    if market == 'ttg':
        return '%s %d球(%d球)' % (num[2:], pick, sum(rl(s['ft'])))
    if market == 'hafu':
        return '%s %s(%s)' % (num[2:], pick, HAFU[(code(*rl(s['ht'])), code(*rl(s['ft'])))])
    if market == 'crs':
        return '%s %s(%s)' % (num[2:], pick, s['ft'])
    return num


print()
print('=' * 150)
print('%-24s %-10s %-6s %-8s %s' % ('方案', '类型', '结果', '赔率', '逐腿（实际）'))
print('=' * 150)
hit = 0
stake = ret = 0.0
settled = []
for name, cat, odds, legs in P:
    oks = [leg_ok(*lg) for lg in legs]
    allok = all(o is True for o in oks)
    stake += 1
    if allok:
        hit += 1; ret += odds
    settled.append({'name': name, 'cat': cat, 'odds': odds, 'hit': allok,
                    'legs': [{'match': lg[0], 'market': lg[1], 'pick': lg[2],
                              'ok': o, 'text': leg_text(*lg)} for lg, o in zip(legs, oks)]})
    print('%-24s %-10s %-6s %-8.2f %s' % (name, cat, '✅中' if allok else '❌失', odds,
                                          ' ｜ '.join(('%s %s' % (t, '✅' if o else '❌')) for t, o in zip([leg_text(*lg) for lg in legs], oks))))
print('=' * 150)
print('串关命中 %d/%d=%.1f%% ｜ 投入 %.0f 单位，回收 %.2f，净 %+.2f（ROI %+.1f%%）' % (
    hit, len(P), hit / len(P) * 100, stake, ret, ret - stake, (ret / stake - 1) * 100))
for cat in ['方向串', '让球串', '混合串', '总进球串', '高赔半全场串', '半全场混合', '比分串']:
    sub = [s for s in settled if s['cat'] == cat]
    print('  %-8s %d/%d' % (cat, sum(1 for s in sub if s['hit']), len(sub)))

json.dump({'rows': rows, 'parlays': settled}, io.open(D + r'\20261027_backtest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved 20261027_backtest.json')
