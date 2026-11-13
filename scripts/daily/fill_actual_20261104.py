# -*- coding: utf-8 -*-
"""回填 2026-11-04 预测 JSON 的实际结果与命中字段"""
import json, io

RES = 'reports/data/20261104_results_20261104_20261105.json'
TARGETS = ['reports/data/20261104_predictions.json', 'memory/predictions/20261104_wednesday/prediction.json']

data = json.load(io.open(RES, encoding='utf-8'))
actual = {}
for m in data['value']['matchResult']:
    if not m.get('sectionsNo999'):
        continue
    fh, fa = map(int, m['sectionsNo999'].split(':'))
    hh, ha = map(int, (m.get('sectionsNo1') or '0:0').split(':'))
    actual[m['matchNumStr']] = dict(fh=fh, fa=fa, hh=hh, ha=ha, line=int(m['goalLine']),
                                    single=int(m.get('bettingSingle') or 0))

HC = {1: '胜', 0: '平', -1: '负'}


def hc_sign(d):
    return HC[1] if d > 0 else (HC[0] if d == 0 else HC[-1])


def had(h, a):
    return 'home' if h > a else ('draw' if h == a else 'away')


def hafu(hh, ha, fh, fa):
    x = '胜' if hh > ha else ('平' if hh == ha else '负')
    y = '胜' if fh > fa else ('平' if fh == fa else '负')
    return x + y


def tier_range(t):
    for k, r in [('闷战', (0, 1)), ('小球', (1, 2)), ('常规', (2, 3)), ('大球', (4, 5)), ('超大', (5, 6)), ('穿盘', (6, 99))]:
        if k in t:
            return r
    return (0, 0)


mo = json.load(io.open('reports/data/20261104_model_output.json', encoding='utf-8'))

for path in TARGETS:
    preds = json.load(io.open(path, encoding='utf-8'))
    for p in preds:
        a = actual.get(p['num'])
        if not a:
            continue
        g = a['fh'] + a['fa']
        d = had(a['fh'], a['fa'])
        hc = hc_sign((a['fh'] - a['fa']) + a['line'])
        hf = hafu(a['hh'], a['ha'], a['fh'], a['fa'])
        sc = f"{a['fh']}-{a['fa']}"
        ht = f"{a['hh']}-{a['ha']}"
        tg = str(g) if g < 7 else '7+'
        lo, hi = tier_range(p['ttg']['tier'])
        dist = mo[p['num']]['ttg']
        p_small = sum(float(dist[k]) for k in ['0', '1', '2'])
        ou = '小' if p_small > 0.5 else '大'
        p['actual'] = {
            'score': sc, 'ht_score': ht, 'direction': d, 'handicap': hc,
            'total_goals': g, 'hafu': hf, 'ou': ('小' if g <= 2 else '大'),
            'single_api': a['single'], 'settled': True,
            'source': '体彩官方 getUniformMatchResultV1（sectionsNo999/sectionsNo1）',
        }
        p['backtest'] = {
            'had_primary': p['had']['first'] == d,
            'had_cover': p['had']['first'] == d or p['had']['second'] == d,
            'hc_primary': p['hhad']['first'] == hc,
            'hc_cover': p['hhad']['first'] == hc or p['hhad']['second'] == hc,
            'score_top5': sc in [c['score'] for c in p['scoreTop5']],
            'ttg_top2': tg in [str(p['ttg']['first']), str(p['ttg']['second'])],
            'hafu_top3': hf in p['hafu']['top3'],
            'ht_top3': ht in [c['score'] for c in p['htScoreTop3']],
            'tier': lo <= g <= hi,
            'ou': ou == ('小' if g <= 2 else '大'),
        }
        if a['single'] and not p['is_single']:
            p['single_note'] = (p.get('single_note') or '') + '｜赛后交叉验证：赛果接口 bettingSingle=1，赛前在售接口该字段滞后，未按单关做规则63上修'
    io.open(path, 'w', encoding='utf-8').write(json.dumps(preds, ensure_ascii=False, indent=1))
    print('updated', path, len(preds))
