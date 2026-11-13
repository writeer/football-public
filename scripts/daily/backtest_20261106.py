# -*- coding: utf-8 -*-
"""2026-11-06 周五14场回测：体彩官方赛果 vs 赛前推荐（全维度 + 分档 + 8注串关）"""
import json, io, os, pathlib

BASE = pathlib.Path(r"e:\VibeCoding\football")
PRED = BASE / "reports/data/20261106_predictions_final.json"
PRED2 = BASE / "memory/predictions/20261106_friday/prediction.json"
OUT_SUM = BASE / "reports/data/20261106_backtest_summary.json"
OUT_DIR = BASE / "memory/backtests/20261106_friday"


def parse_score(s):
    h, a = str(s).split(':')
    return int(h), int(a)


def had_of(h, a):
    return 'home' if h > a else ('draw' if h == a else 'away')


def hc_of(h, a, line):
    d = (h - a) + line
    return 'win' if d > 0 else ('push' if d == 0 else 'lose')


def hafu_of(hh, ha, fh, fa):
    ht = '胜' if hh > ha else ('平' if hh == ha else '负')
    ft = '胜' if fh > fa else ('平' if fh == fa else '负')
    return ht + ft


def ttg_label(g):
    return '7+' if g >= 7 else str(g)


def tier_range(tier):
    if '闷战' in tier: return (0, 1)
    if '小球' in tier: return (1, 2)
    if '常规' in tier: return (2, 3)
    if '大球' in tier: return (4, 5)
    if '超大' in tier: return (5, 6)
    if '穿盘' in tier: return (6, 99)
    return (0, 0)


def band_of(g):
    if g <= 1: return '闷战超小球(0-1球)'
    if g == 2: return '小球(1-2球)'
    if g == 3: return '常规正常球(2-3球)'
    if g in (4, 5): return '大球(4-5球)'
    if g == 6: return '超大球(5-6球)'
    return '穿盘可能(6-7+球)'


def main():
    preds = json.load(io.open(PRED, encoding='utf-8'))
    raw = json.load(io.open(BASE / "reports/data/20261106_results_official_raw.json", encoding='utf-8'))

    actual, pending = {}, []
    for m in raw:
        num = m.get('numStr') or ('周五' + str(m['num'])[-3:])
        if not m.get('no999'):
            pending.append(num)
            actual[num] = {'pending': True, 'single': int(m.get('single') or 0),
                           'line': int(m['goalLine'])}
            continue
        fh, fa = parse_score(m['no999'])
        hh, ha = parse_score(m.get('no1') or '0:0')
        actual[num] = dict(fh=fh, fa=fa, hh=hh, ha=ha, line=int(m['goalLine']),
                           single=int(m.get('single') or 0), status=m.get('status'),
                           resultStatus=m.get('resultStatus'), date=m.get('date'))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    io.open(OUT_DIR / 'results_official.json', 'w', encoding='utf-8').write(
        json.dumps(raw, ensure_ascii=False, indent=1))

    rows = []
    for p in preds:
        num = p['num']
        a = actual.get(num)
        if not a or a.get('pending'):
            rows.append({'num': num, 'match': f"{p['home']} vs {p['away']}", 'conf': p['confidence'],
                         'status': 'pending', 'single_api': (a or {}).get('single')})
            continue
        fh, fa, hh, ha = a['fh'], a['fa'], a['hh'], a['ha']
        g = fh + fa
        dirn = had_of(fh, fa)
        hc = hc_of(fh, fa, p['handicap']['line'])
        hafu = hafu_of(hh, ha, fh, fa)
        score, ht = f'{fh}-{fa}', f'{hh}-{ha}'
        ttg = ttg_label(g)
        lo, hi = tier_range(p['band'])
        band = band_of(g)
        ou_pick = '小' if p['under25'] > 50 else '大'
        ou_actual = '小' if g <= 2 else '大'

        r = {
            'num': num, 'match': f"{p['home']} vs {p['away']}", 'conf': p['confidence'],
            'league': p['league'], 'is_single': p['is_single'], 'single_api': a['single'],
            'score': score, 'ht': ht, 'goals': g,
            'actual': {'had': dirn, 'hc': hc, 'hafu': hafu, 'score': score, 'ht': ht, 'goals': g,
                       'ou': ou_actual, 'single_api': a['single'], 'line': p['handicap']['line'],
                       'band': band},
            'pred': {'had_first': p['first'], 'had_second': p['second'],
                     'had_first_prob': p['firstProb'], 'had_second_prob': p['secondProb'],
                     'hc_first': p['handicap']['first'], 'hc_second': p['handicap']['second'],
                     'hc_first_prob': p['handicap']['firstProb'],
                     'structure_leg': p['handicap']['structure'],
                     'structure_prob': p['handicap']['structureProb'],
                     'ttg_first': p['ttgTop2'][0][0], 'ttg_second': p['ttgTop2'][1][0],
                     'tier': p['band'],
                     'hafu': [x[0] for x in p['hafuTop3']],
                     'cr': [x[0] for x in p['scoreTop5']],
                     'ht': [x[0] for x in p['htScoreTop3']],
                     'ou': ou_pick, 'ou_p_under': round(p['under25'], 4),
                     'override': p.get('override_reason')},
            'had_primary': p['first'] == dirn,
            'had_combined': p['first'] == dirn or p['second'] == dirn,
            'hc_primary': p['handicap']['first'] == hc,
            'hc_combined': p['handicap']['first'] == hc or p['handicap']['second'] == hc,
            'hc_structure_hit': p['handicap']['structure'] == hc,
            'cr_top5': score in [x[0] for x in p['scoreTop5']],
            'cr_top1': p['scoreTop5'][0][0] == score,
            'ttg_top2': ttg in [p['ttgTop2'][0][0], p['ttgTop2'][1][0]],
            'ttg_top1': p['ttgTop2'][0][0] == ttg,
            'hafu_top3': hafu in [x[0] for x in p['hafuTop3']],
            'hafu_top1': p['hafuTop3'][0][0] == hafu,
            'ht_top3': ht in [x[0] for x in p['htScoreTop3']],
            'ht_top1': p['htScoreTop3'][0][0] == ht,
            'tier_hit': lo <= g <= hi,
            'ou_hit': ou_pick == ou_actual,
            'band': band,
        }
        rows.append(r)

    PARLAYS = [
        ('#1 方向2串1（005客×014客）', 4.70,
         [('周五005', 'had', 'away'), ('周五014', 'had', 'away')]),
        ('#2 方向2串1（011客×013客）', 8.11,
         [('周五011', 'had', 'away'), ('周五013', 'had', 'away')]),
        ('#3 方向2串1（005客×008平）', 6.90,
         [('周五005', 'had', 'away'), ('周五008', 'had', 'draw')]),
        ('#4 方向2串1（014客×011客）', 5.85,
         [('周五014', 'had', 'away'), ('周五011', 'had', 'away')]),
        ('#5 方向2串1（013客×008平）', 10.30,
         [('周五013', 'had', 'away'), ('周五008', 'had', 'draw')]),
        ('#6 半全场连续串①（001-002）', 9.69,
         [('周五001', 'hafu', '胜胜'), ('周五002', 'hafu', '平胜')]),
        ('#7 半全场连续串②（003-004）', 8.01,
         [('周五003', 'hafu', '胜胜'), ('周五004', 'hafu', '平胜')]),
        ('#8 半全场连续串③（012-013）', 15.68,
         [('周五012', 'hafu', '胜胜'), ('周五013', 'hafu', '平胜')]),
    ]

    def leg_hit(num, market, pick):
        a = actual.get(num)
        if not a or a.get('pending'):
            return None
        if market == 'had':
            return had_of(a['fh'], a['fa']) == pick
        if market == 'hc':
            return hc_of(a['fh'], a['fa'], a['line']) == pick
        if market == 'ttg':
            return ttg_label(a['fh'] + a['fa']) == pick
        if market == 'hafu':
            return hafu_of(a['hh'], a['ha'], a['fh'], a['fa']) == pick
        if market == 'score':
            return f"{a['fh']}-{a['fa']}" == pick
        return False

    parlays = []
    for label, odds, legs in PARLAYS:
        hits = [leg_hit(*l) for l in legs]
        resolved = False if any(h is False for h in hits) else (None if any(h is None for h in hits) else True)
        parlays.append({'label': label, 'odds': odds,
                        'legs': [f'{l[0]} {l[1]} {l[2]}' for l in legs],
                        'leg_hits': hits, 'hit': resolved,
                        'failed_leg': next((f'{l[0]} {l[1]} {l[2]}' for l, h in zip(legs, hits) if h is False), None)})

    dims = ['had_primary', 'had_combined', 'hc_primary', 'hc_combined', 'cr_top5', 'cr_top1',
            'ttg_top2', 'ttg_top1', 'hafu_top3', 'hafu_top1', 'ht_top3', 'ht_top1',
            'tier_hit', 'ou_hit']

    settled = [r for r in rows if r.get('status') != 'pending']

    def rate(key, subset=None):
        arr = [r for r in settled if subset is None or subset(r)]
        hit = sum(1 for r in arr if r[key])
        return hit, len(arr), (round(hit / len(arr) * 100, 1) if arr else None)

    summary = {k: dict(zip(['hit', 'n', 'pct'], rate(k))) for k in dims}
    buckets = {}
    for c in ['★★★', '★★', '★']:
        sub = (lambda cc: (lambda r: r['conf'] == cc))(c)
        buckets[c] = {
            'n': sum(1 for r in settled if r['conf'] == c),
            'had_primary': rate('had_primary', sub), 'had_combined': rate('had_combined', sub),
            'hc_primary': rate('hc_primary', sub), 'hc_combined': rate('hc_combined', sub),
            'hafu_top3': rate('hafu_top3', sub), 'cr_top5': rate('cr_top5', sub),
            'ttg_top2': rate('ttg_top2', sub), 'ht_top3': rate('ht_top3', sub),
            'tier': rate('tier_hit', sub), 'ou': rate('ou_hit', sub),
        }

    stake = len(parlays)
    ret = sum(p['odds'] for p in parlays if p['hit'])
    parlay_sum = {'n': len(parlays), 'hit': sum(1 for p in parlays if p['hit']),
                  'stake': stake, 'return': round(ret, 2), 'profit': round(ret - stake, 2),
                  'roi_pct': round((ret - stake) / stake * 100, 1)}

    out = {'date': '2026-11-06', 'day': '周五', 'n': len(rows), 'settled_n': len(settled),
           'pending': pending, 'rows': rows, 'summary': summary, 'buckets': buckets,
           'parlays': parlays, 'parlay_summary': parlay_sum,
           'source': '体彩官方 getUniformMatchResultV1（matchBeginDate=2026-11-06~2026-11-07，matchNumStr 含「周五」）；sectionsNo999=全场、sectionsNo1=半场；14场全部开奖，无待结算'}
    for path in [OUT_SUM, OUT_DIR / 'backtest.json']:
        io.open(path, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
    io.open(OUT_DIR / 'rows.json', 'w', encoding='utf-8').write(
        json.dumps(rows, ensure_ascii=False, indent=1))

    # 回填 actual/backtest 到双路径 prediction.json
    for target in [PRED, PRED2]:
        data = json.load(io.open(target, encoding='utf-8'))
        for m in data:
            a = actual.get(m['num'])
            if not a or a.get('pending'):
                continue
            m['actual'] = {
                'score': f"{a['fh']}-{a['fa']}", 'ht_score': f"{a['hh']}-{a['ha']}",
                'direction': had_of(a['fh'], a['fa']), 'handicap': hc_of(a['fh'], a['fa'], a['line']),
                'total_goals': a['fh'] + a['fa'],
                'hafu': hafu_of(a['hh'], a['ha'], a['fh'], a['fa']),
                'ou': '小' if (a['fh'] + a['fa']) <= 2 else '大',
                'single_api': a['single'], 'settled': True,
                'source': '体彩官方 getUniformMatchResultV1（sectionsNo999/sectionsNo1）',
            }
        io.open(target, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1))

    print('n=', len(rows), 'settled=', len(settled), 'pending=', pending)
    for k in dims:
        print(f'{k:16s}', summary[k])
    print('buckets', json.dumps(buckets, ensure_ascii=False))
    print('--- per match ---')
    for r in rows:
        if r.get('status') == 'pending':
            print(r['num'], 'PENDING', 'single_api=', r.get('single_api'))
            continue
        print(r['num'], r['conf'], r['score'], 'HT', r['ht'], '| HAD', r['actual']['had'],
              r['had_primary'], r['had_combined'],
              '| HC', r['actual']['hc'], r['hc_primary'], r['hc_combined'],
              'struct', r['pred']['structure_leg'], r['hc_structure_hit'],
              '| CR', r['cr_top5'], '| TTG', r['ttg_top2'], '| HAFU', r['actual']['hafu'], r['hafu_top3'],
              '| HT', r['ht_top3'], '| tier', r['tier_hit'], '| OU', r['pred']['ou'], r['actual']['ou'], r['ou_hit'])
    print('--- parlays ---')
    for p in parlays:
        print(('HIT ' if p['hit'] else ('VOID' if p['hit'] is None else 'MISS')), p['label'], p['odds'],
              'failed:', p['failed_leg'], p['leg_hits'])
    print('parlay', parlay_sum)


if __name__ == '__main__':
    main()
