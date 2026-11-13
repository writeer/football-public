# -*- coding: utf-8 -*-
"""2026-11-04 周三12场回测：体彩官方赛果 vs 赛前推荐（全维度 + 分置信度 + 串关）"""
import json, io, os

RAW = 'reports/data/20261104_results_20261104_20261105.json'
PRED = 'reports/data/20261104_predictions.json'


def parse_score(s):
    h, a = str(s).split(':')
    return int(h), int(a)


def had_of(h, a):
    return 'home' if h > a else ('draw' if h == a else 'away')


HC_CN = {1: '胜', 0: '平', -1: '负'}


def hc_of(h, a, line):
    d = (h - a) + line
    return '胜' if d > 0 else ('平' if d == 0 else '负')


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


def main():
    data = json.load(io.open(RAW, encoding='utf-8'))
    lst = data['value']['matchResult']
    actual = {}
    for m in lst:
        if not m.get('sectionsNo999'):
            continue
        fh, fa = parse_score(m['sectionsNo999'])
        hh, ha = parse_score(m['sectionsNo1'] or '0:0')
        actual[m['matchNumStr']] = dict(fh=fh, fa=fa, hh=hh, ha=ha,
                                       line=int(m['goalLine']), single=int(m.get('bettingSingle') or 0),
                                       status=m.get('matchStatus'), date=m.get('matchDate'))
    os.makedirs('memory/backtests/20261104_wednesday', exist_ok=True)
    io.open('memory/backtests/20261104_wednesday/results_official.json', 'w', encoding='utf-8').write(
        json.dumps(lst, ensure_ascii=False, indent=1))

    preds = json.load(io.open(PRED, encoding='utf-8'))
    mo = json.load(io.open('reports/data/20261104_model_output.json', encoding='utf-8'))

    rows = []
    for p in preds:
        num = p['num']
        a = actual.get(num)
        if not a:
            rows.append({'num': num, 'status': 'pending'})
            continue
        fh, fa, hh, ha = a['fh'], a['fa'], a['hh'], a['ha']
        g = fh + fa
        dirn = had_of(fh, fa)
        hc = hc_of(fh, fa, p['handicap']['line'])
        hafu = hafu_of(hh, ha, fh, fa)
        score = f'{fh}-{fa}'
        ht = f'{hh}-{ha}'
        ttg = ttg_label(g)
        lo, hi = tier_range(p['ttg']['tier'])
        ttg_dist = mo[num]['ttg']
        p_small = sum(float(ttg_dist[k]) for k in ['0', '1', '2'])
        ou_pick = '小' if p_small > 0.5 else '大'
        ou_actual = '小' if g <= 2 else '大'

        r = {
            'num': num, 'match': f"{p['home']} vs {p['away']}", 'conf': p['confidence'],
            'league': p['league'], 'is_single': p['is_single'],
            'score': score, 'ht': ht, 'goals': g,
            'actual': {'had': dirn, 'hc': hc, 'hafu': hafu, 'score': score, 'ht': ht, 'goals': g,
                       'ou': ou_actual, 'single_api': a['single'], 'line': p['handicap']['line']},
            'pred': {'had_first': p['had']['first'], 'had_second': p['had']['second'],
                     'hc_first': p['hhad']['first'], 'hc_second': p['hhad']['second'],
                     'ttg_first': p['ttg']['first'], 'ttg_second': p['ttg']['second'],
                     'tier': p['ttg']['tier'], 'hafu': p['hafu']['top3'],
                     'cr': [c['score'] for c in p['scoreTop5']],
                     'ht': [c['score'] for c in p['htScoreTop3']],
                     'ou': ou_pick, 'ou_p_small': round(p_small, 4),
                     'had_first_prob': p['had']['firstProb']},
            'had_primary': p['had']['first'] == dirn,
            'had_combined': p['had']['first'] == dirn or p['had']['second'] == dirn,
            'hc_primary': p['hhad']['first'] == hc,
            'hc_combined': p['hhad']['first'] == hc or p['hhad']['second'] == hc,
            'cr_top5': score in [c['score'] for c in p['scoreTop5']],
            'cr_top1': p['scoreTop5'][0]['score'] == score,
            'ttg_top2': ttg in [str(p['ttg']['first']), str(p['ttg']['second'])],
            'ttg_top1': str(p['ttg']['first']) == ttg,
            'hafu_top3': hafu in p['hafu']['top3'],
            'hafu_top1': p['hafu']['top3'][0] == hafu,
            'ht_top3': ht in [c['score'] for c in p['htScoreTop3']],
            'ht_top1': p['htScoreTop3'][0]['score'] == ht,
            'tier_hit': lo <= g <= hi,
            'ou_hit': ou_pick == ou_actual,
        }
        rows.append(r)

    # 串关（与赛前报告 7 注逐条对应）
    PARLAYS = [
        ('方向A（三串一）', 3.76, [('周三006', 'had', 'home'), ('周三008', 'had', 'home'), ('周三009', 'had', 'home')]),
        ('方向B（二串一）', 3.61, [('周三006', 'had', 'home'), ('周三007', 'had', 'home')]),
        ('让球A（二串一）', 4.93, [('周三008', 'hc', '胜'), ('周三009', 'hc', '胜')]),
        ('娱乐① 011负负×012负负', 4.86, [('周三011', 'hafu', '负负'), ('周三012', 'hafu', '负负')]),
        ('娱乐② 003 2球×004 3球', 12.25, [('周三003', 'ttg', '2'), ('周三004', 'ttg', '3')]),
        ('娱乐③ 010负负×011负负', 4.26, [('周三010', 'hafu', '负负'), ('周三011', 'hafu', '负负')]),
        ('娱乐④ 001 0-1×002 0-1', 64.00, [('周三001', 'score', '0-1'), ('周三002', 'score', '0-1')]),
    ]

    def leg_hit(num, market, pick):
        a = actual[num]
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
        parlays.append({'label': label, 'odds': odds, 'legs': [f'{l[0]} {l[1]} {l[2]}' for l in legs],
                        'leg_hits': hits, 'hit': all(hits),
                        'failed_leg': next((f'{l[0]} {l[1]} {l[2]}' for l, h in zip(legs, hits) if not h), None)})

    dims = ['had_primary', 'had_combined', 'hc_primary', 'hc_combined', 'cr_top5', 'cr_top1',
            'ttg_top2', 'ttg_top1', 'hafu_top3', 'hafu_top1', 'ht_top3', 'ht_top1',
            'tier_hit', 'ou_hit']

    def rate(key, subset=None):
        arr = [r for r in rows if r.get('status') != 'pending' and (subset is None or subset(r))]
        hit = sum(1 for r in arr if r[key])
        return hit, len(arr), (round(hit / len(arr) * 100, 1) if arr else None)

    summary = {k: dict(zip(['hit', 'n', 'pct'], rate(k))) for k in dims}

    buckets = {}
    for c in ['★★★', '★★', '★']:
        sub = (lambda cc: (lambda r: r['conf'] == cc))(c)
        buckets[c] = {
            'n': sum(1 for r in rows if r.get('conf') == c),
            'had_primary': rate('had_primary', sub),
            'had_combined': rate('had_combined', sub),
            'hc_primary': rate('hc_primary', sub),
            'hc_combined': rate('hc_combined', sub),
            'hafu_top3': rate('hafu_top3', sub),
            'cr_top5': rate('cr_top5', sub),
            'ttg_top2': rate('ttg_top2', sub),
            'ht_top3': rate('ht_top3', sub),
            'tier': rate('tier_hit', sub),
            'ou': rate('ou_hit', sub),
        }

    stake = len(parlays)
    ret = sum(p['odds'] for p in parlays if p['hit'])
    parlay = {'n': len(parlays), 'hit': sum(1 for p in parlays if p['hit']),
              'stake': stake, 'return': round(ret, 2), 'profit': round(ret - stake, 2),
              'roi_pct': round((ret - stake) / stake * 100, 1)}

    out = {'date': '2026-11-04', 'day': '周三', 'n': len(rows), 'rows': rows,
           'summary': summary, 'buckets': buckets, 'parlays': parlays, 'parlay_summary': parlay,
           'source': '体彩官方 getUniformMatchResultV1（matchBeginDate=2026-11-04~2026-11-05）；sectionsNo999=全场、sectionsNo1=半场'}
    for path in ['reports/data/20261104_backtest_summary.json', 'memory/backtests/20261104_wednesday/backtest.json']:
        io.open(path, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
    io.open('memory/backtests/20261104_wednesday/rows.json', 'w', encoding='utf-8').write(
        json.dumps(rows, ensure_ascii=False, indent=1))

    print('n=', len(rows), 'pending=', [r['num'] for r in rows if r.get('status') == 'pending'])
    for k in dims:
        print(f'{k:15s}', summary[k])
    print('buckets', json.dumps(buckets, ensure_ascii=False))
    print('--- per match ---')
    for r in rows:
        if r.get('status') == 'pending':
            continue
        print(r['num'], r['conf'], r['score'], 'HT', r['ht'], '| HAD', r['actual']['had'],
              r['had_primary'], r['had_combined'],
              '| HC', r['actual']['hc'], r['hc_primary'], r['hc_combined'],
              '| CR', r['cr_top5'], '| TTG', r['actual']['goals'], r['ttg_top2'],
              '| HAFU', r['actual']['hafu'], r['hafu_top3'],
              '| HT', r['ht_top3'], '| tier', r['tier_hit'], '| OU', r['pred']['ou'], r['actual']['ou'], r['ou_hit'])
    print('--- parlays ---')
    for p in parlays:
        print(('HIT ' if p['hit'] else 'MISS'), p['label'], p['odds'], 'failed:', p['failed_leg'])
    print('parlay', parlay)


if __name__ == '__main__':
    main()
