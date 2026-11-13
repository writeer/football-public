# -*- coding: utf-8 -*-
"""2026-10-21 周三13场回测：6维度 + 28个串关方案结算"""
import json

D = r'e:\VibeCoding\football\reports\data'
pred = {m['num']: m for m in json.load(open(D + r'\20261021_model_output.json', encoding='utf-8-sig'))}
res = {r['num']: r for r in json.load(open(D + r'\20261021_results_official.json', encoding='utf-8-sig'))}
parlay = json.load(open(D + r'\20261021_parlay.json', encoding='utf-8-sig'))

DIR = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC = {'home': '让胜', 'draw': '让平', 'away': '让负'}
HAFU = {('H', 'H'): '胜胜', ('H', 'D'): '胜平', ('H', 'A'): '胜负',
        ('D', 'H'): '平胜', ('D', 'D'): '平平', ('D', 'A'): '平负',
        ('A', 'H'): '负胜', ('A', 'D'): '负平', ('A', 'A'): '负负'}


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


def score_top5(r):
    picks = []
    for a, b, pr in r['band']:
        picks.append('%d-%d' % (a, b))
        if len(picks) >= 3:
            break
    for a, b, pr in r['top_scores']:
        s = '%d-%d' % (a, b)
        if s not in picks:
            picks.append(s)
        if len(picks) >= 5:
            break
    return picks[:5]


def leg_ok(num, market, pick):
    r = res.get(num)
    if not r:
        return None
    h, a = rl(r['ft'])
    hh, ha = rl(r['ht']) if r.get('ht') else (None, None)
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


rows = []
for num, r in pred.items():
    if num not in res:
        rows.append({'num': num, 'status': 'no_result', 'home': r['home'], 'away': r['away'], 'league': r['league']})
        continue
    h, a = rl(res[num]['ft'])
    ht = res[num].get('ht')
    hh, ha = rl(ht) if ht else (None, None)
    total = h + a
    actual = 'home' if h > a else ('draw' if h == a else 'away')
    had = 'first' if r['primary'] == actual else ('second' if r['secondary'] == actual else 'miss')
    gl = r.get('hhad_line')
    hh_res = None
    if gl is not None:
        adj = (h - a) + gl
        hh_res = 'home' if adj > 0 else ('draw' if adj == 0 else 'away')
    hc = None
    if hh_res:
        hc = 'first' if r['hc_first'] == hh_res else ('second' if r['hc_second'] == hh_res else 'miss')
    ttg = 'hit' if total in (r.get('ttg_top2') or []) else 'miss'
    hafu_actual = HAFU.get((code(hh, ha), code(h, a))) if hh is not None else None
    hafu = 'hit' if hafu_actual in [k for k, _ in r.get('htft_top3', [])] else ('na' if hafu_actual is None else 'miss')
    sc = score_top5(r)
    sc_actual = '%d-%d' % (h, a)
    crs = 'hit' if sc_actual in sc else 'miss'
    tier = 'hit' if tier_hit(r['tier'], total) else 'miss'
    hts = ['%d-%d' % (x, y) for x, y, _ in r.get('ht_scores', [])[:3]]
    ht_hit = 'hit' if hh is not None and ('%d-%d' % (hh, ha)) in hts else ('na' if hh is None else 'miss')

    rows.append({'num': num, 'league': r['league'], 'home': r['home'], 'away': r['away'],
                 'ft': res[num]['ft'], 'ht': ht, 'total': total,
                 'pred_dir': r['primary'], 'pred_dir2': r['secondary'], 'actual_dir': actual, 'had': had,
                 'pred_hc': r['hc_first'], 'pred_hc2': r['hc_second'], 'actual_hc': hh_res, 'hc': hc,
                 'ttg_top2': r.get('ttg_top2'), 'ttg': ttg,
                 'hafu_top3': [k for k, _ in r.get('htft_top3', [])], 'hafu_actual': hafu_actual, 'hafu': hafu,
                 'crs_top5': sc, 'crs_actual': sc_actual, 'crs': crs,
                 'tier': r['tier'], 'tier_hit': tier,
                 'ht_top3': hts, 'ht_actual': '%d-%d' % (hh, ha) if hh is not None else None, 'ht_hit': ht_hit,
                 'lambda': (r['lambda_home'], r['lambda_away']), 'conf': r.get('conf', '')})

json.dump(rows, open(D + r'\20261021_backtest_rows.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---- 串关 ----
done = [x for x in rows if x.get('status') != 'no_result']
print('=' * 118)
print('%-9s %-8s %-6s %-5s %-5s %-5s %-5s %-5s %-5s' % ('编号', '联赛', '比分', 'HAD', '让球', 'TTG', 'HAFU', '比分', '档位'))
print('=' * 118)
for x in done:
    print('%-9s %-8s %-6s %-5s %-5s %-5s %-5s %-5s %-5s' % (
        x['num'], x['league'], x['ft'],
        {'first': '首✅', 'second': '次✅', 'miss': '❌'}[x['had']],
        {'first': '首✅', 'second': '次✅', 'miss': '❌', None: '—'}[x['hc']],
        {'hit': '✅', 'miss': '❌'}[x['ttg']],
        {'hit': '✅', 'miss': '❌', 'na': '—'}[x['hafu']],
        {'hit': '✅', 'miss': '❌'}[x['crs']],
        {'hit': '✅', 'miss': '❌'}[x['tier_hit']]))


def stat(key, first_only=False):
    if first_only:
        n = sum(1 for x in done if x[key] == 'first')
    else:
        n = sum(1 for x in done if x.get(key) in ('first', 'second', 'hit'))
    return n, len(done), n / len(done) * 100


print('=' * 118)
a, b = stat('had', True), stat('had')
print('HAD  首选 %d/%d=%.1f%% ｜含次选 %d/%d=%.1f%%' % (a[0], a[1], a[2], b[0], b[1], b[2]))
a, b = stat('hc', True), stat('hc')
print('让球 首选 %d/%d=%.1f%% ｜含次选 %d/%d=%.1f%%' % (a[0], a[1], a[2], b[0], b[1], b[2]))
print('TTG TOP2 %d/%d=%.1f%%' % stat('ttg'))
print('HAFU TOP3 %d/%d=%.1f%%' % stat('hafu'))
print('比分 TOP5 %d/%d=%.1f%%' % stat('crs'))
print('大小球档位 %d/%d=%.1f%%' % stat('tier_hit'))
print('半场比分TOP3 %d/%d=%.1f%%' % stat('ht_hit'))

print()
print('=' * 118)
print('%-22s %-52s %-6s %-7s %s' % ('串关方案', '逐腿', '结果', '赔率', '回报'))
print('=' * 118)
hit = 0
stake = ret = 0.0
settled = []
for p in parlay:
    marks, allok, pending = [], True, False
    for lg in p['legs']:
        ok = leg_ok(lg['num'], lg['market'], lg['pick'])
        if ok is None:
            pending = True
            marks.append('%s待定' % lg['num'][2:])
        else:
            marks.append('%s%s' % (lg['num'][2:], '✅' if ok else '❌'))
            allok = allok and ok
    stake += 1
    if pending:
        settled.append((p, 'pending', 0))
        print('%-22s %-52s %-6s %-7.2f %s' % (p['name'], ' '.join(marks), '⏳待', p['odds'], '—'))
        continue
    ret += p['odds'] if allok else 0
    hit += 1 if allok else 0
    settled.append((p, 'hit' if allok else 'miss', p['odds']))
    print('%-22s %-52s %-6s %-7.2f %s' % (p['name'], ' '.join(marks), '✅中' if allok else '❌失',
                                          p['odds'], ('%.2f' % p['odds']) if allok else '0'))
print('=' * 118)
print('命中 %d/%d=%.1f%% ｜ 投入 %.0f 单位，回收 %.2f，净 %+.2f（ROI %+.1f%%）' % (
    hit, len(parlay), hit / len(parlay) * 100, stake, ret, ret - stake, (ret / stake - 1) * 100))
json.dump([{'name': p['name'], 'cat': p['cat'], 'odds': p['odds'], 'status': s} for p, s, _ in settled],
          open(D + r'\20261021_parlay_settled.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
