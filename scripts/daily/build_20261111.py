# -*- coding: utf-8 -*-
"""构建 2026-11-11 预测归档（4场日联赛杯）并打印比分带内候选"""
import json, io, os

mo = json.load(io.open('reports/data/20261111_model_output.json', encoding='utf-8'))
raw = {m['matchNumStr']: m for m in json.load(io.open('reports/data/20261111_raw.json', encoding='utf-8'))['matches']}

CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC_CN = {'home': '让胜', 'draw': '让平', 'away': '让负'}
HF_CN = {'HH': '胜胜', 'HD': '胜平', 'HA': '胜负', 'DH': '平胜', 'DD': '平平',
         'DA': '平负', 'AH': '负胜', 'AD': '负平', 'AA': '负负'}


def band(lam, ttg):
    over = sum(ttg[k] for k in ('3', '4', '5', '6', '7+'))
    if lam < 1.5: name = '闷战超小球'
    elif lam < 2.5: name = '小球' if ttg['1'] >= ttg['3'] else '常规正常球'
    elif lam < 3.5: name = '常规正常球'
    elif lam < 5.0: name = '大球'
    elif lam < 6.0: name = '超大球'
    else: name = '穿盘可能'
    side = '大' if over > 0.5 else '小'
    cover = '3-5球' if lam > 3.5 else ''
    return name, side, cover, round(over * 100, 1), round((1 - over) * 100, 1)


CONF = {'周三001': '★', '周三002': '★', '周三003': '★', '周三004': '★★', '周三005': '★', '周三006': '☆'}

SINGLE = {'周三004'}


def r63(p):
    """L63 单关上修：平局上修后归一化"""
    first = max(p['home'], p['draw'], p['away'])
    second = sorted([p['home'], p['draw'], p['away']], reverse=True)[1]
    gap = (first - second) * 100
    if gap <= 10:
        mult, tier = 1.13, '≤10pp'
    elif gap <= 20:
        mult, tier = 1.11, '≤20pp'
    else:
        mult, tier = 1.08, '≥20pp'
    d0 = p['draw']
    d1 = d0 * mult
    tot = p['home'] + d1 + p['away']
    q = {'home': p['home'] / tot, 'draw': d1 / tot, 'away': p['away'] / tot}
    return q, gap, tier, mult, d0, d1


preds = []
for key in sorted(mo):
    r = mo[key]
    raw_p = r['probs_final']
    uplift = None
    if key in SINGLE:
        q, gap, tier, mult, d0, d1 = r63(raw_p)
        before = sorted(raw_p.items(), key=lambda x: -x[1])
        after = sorted(q.items(), key=lambda x: -x[1])
        uplift = {
            'gap_pp': round(gap, 1), 'tier': tier, 'mult': mult,
            'draw_before': round(d0 * 100, 1), 'draw_after_raw': round(d1 * 100, 1),
            'probs_before': {k: round(v * 100, 1) for k, v in raw_p.items()},
            'probs_after': {k: round(v * 100, 1) for k, v in q.items()},
            'second_before': CN[before[1][0]], 'second_after': CN[after[1][0]],
            'second_changed': before[1][0] != after[1][0],
            'l277_dual': q[after[0][0]] < 0.50,
        }
        p = {k: round(v * 100, 1) for k, v in q.items()}
    else:
        p = {k: round(v * 100, 1) for k, v in raw_p.items()}
    order = sorted(p.items(), key=lambda x: -x[1])
    first, second = order[0], order[1]

    mk = r['market']
    div = {k: round(p[k] - mk[k] * 100, 1) for k in p}

    hc = r['handicap']; line = hc['line']
    hco = r['odds']['hhad']
    # 让球按赔率升序取前二
    horder = sorted([('home', hco['home']), ('draw', hco['draw']), ('away', hco['away'])], key=lambda x: x[1])
    hfirst, hsecond = horder[0][0], horder[1][0]
    hprob = {'home': hc['win'], 'draw': hc['push'], 'away': hc['lose']}

    ttg = r['ttg']
    ttg_sorted = sorted(ttg.items(), key=lambda x: -x[1])
    badname, side, cover, over25, under25 = band(r['lambda']['total'], ttg)

    od = r['odds']
    scoreTop5 = []
    for s, pr in r['top_scores'][:5]:
        scoreTop5.append({'score': s, 'p': round(pr * 100, 1), 'odds': od['crs'].get(s)})
    hafuTop3 = [{'key': HF_CN[k], 'code': k, 'p': round(v * 100, 1), 'odds': od['hafu'].get(k)}
                for k, v in list(r['htft'].items())[:3]]
    htTop3 = [{'score': s, 'p': round(v * 100, 1)} for s, v in r['ht_scores'][:3]]
    ttgTop2 = [{'goals': g, 'p': round(v * 100, 1), 'odds': od['ttg'].get(g)} for g, v in ttg_sorted[:2]]

    preds.append({
        'num': key, 'league': r['league'], 'home': r['home'], 'away': r['away'],
        'time': raw[key]['matchDate'] + ' ' + r['time'][:5],
        'is_single': key in SINGLE,
        'single_note': ('用户投注端告知为单关；接口 bettingSingle=0，按 L273 以用户端为准并做单关上修'
                        if key in SINGLE else
                        '接口 bettingSingle=0（未开单关）；用户端如显示单关请以用户端为准（L273）'),
        'single_uplift': uplift,
        'confidence': CONF[key],
        'probs': p, 'first': CN[first[0]], 'second': CN[second[0]],
        'firstProb': first[1], 'secondProb': second[1],
        'lambda': {k: round(v, 3) for k, v in r['lambda'].items()},
        'market': {k: round(v * 100, 1) for k, v in mk.items() if k != 'overround'},
        'divergence': div,
        'band': {'name': badname, 'side': side, 'cover': cover},
        'scoreTop5': scoreTop5, 'hafuTop3': hafuTop3, 'htScoreTop3': htTop3,
        'ttgTop2': ttgTop2, 'over25': over25, 'under25': under25,
        'handicap': {'line': line, 'win': round(hc['win'] * 100, 1), 'push': round(hc['push'] * 100, 1),
                     'lose': round(hc['lose'] * 100, 1), 'first': HC_CN[hfirst], 'second': HC_CN[hsecond],
                     'firstProb': round(hprob[hfirst] * 100, 1), 'secondProb': round(hprob[hsecond] * 100, 1)},
        'odds': {'had': od['had'], 'hhad': {'line': line, 'home': hco['home'], 'draw': hco['draw'], 'away': hco['away']},
                 'hafu': od['hafu'], 'crs': od['crs'], 'ttg': od['ttg']},
        'kDist': {'k': r['k_dist']['k'], 'p': round(r['k_dist']['p'] * 100, 1)},
        'kRec': {'k': r['k_rec']['k'], 'p': round(r['k_rec']['p'] * 100, 1)},
        'divergence_flag': ('众数一致' if (('home' if r['k_dist']['k'] > 0 else ('draw' if r['k_dist']['k'] == 0 else 'away')) == first[0]) else '分布-方向分歧'),
        'top_scores_raw': r['top_scores'],
        'kdist': {str(k): round(v * 100, 1) for k, v in r['kdist'].items()},
        'tags': r['tags'],
    })

os.makedirs('memory/predictions/20261111_wednesday', exist_ok=True)
io.open('reports/data/20261111_predictions.json', 'w', encoding='utf-8').write(
    json.dumps(preds, ensure_ascii=False, indent=1))
io.open('reports/data/20261111_predictions_final.json', 'w', encoding='utf-8').write(
    json.dumps(preds, ensure_ascii=False, indent=1))
io.open('memory/predictions/20261111_wednesday/prediction.json', 'w', encoding='utf-8').write(
    json.dumps(preds, ensure_ascii=False, indent=1))

for x in preds:
    print(x['num'], x['home'], 'vs', x['away'], '|', x['first'], x['firstProb'], '/', x['second'], x['secondProb'],
          '|', x['confidence'], '| 让', x['handicap']['line'], x['handicap']['first'], x['handicap']['firstProb'],
          x['handicap']['second'], x['handicap']['secondProb'], '| 档', x['band'], '| TTG', x['ttgTop2'],
          '| k', x['kDist'], x['kRec'], x['divergence_flag'])
    print('   比分TOP5', [(a['score'], a['p'], a['odds']) for a in x['scoreTop5']])
    print('   半全场', [(a['key'], a['p'], a['odds']) for a in x['hafuTop3']], '半场', x['htScoreTop3'])

print('\n=== 比分带内候选（k_rec 带内按联合概率 TOP3） ===')
for x in preds:
    k = x['kRec']['k']
    bandc = [(s, pr) for s, pr in x['top_scores_raw'] if int(s.split('-')[0]) - int(s.split('-')[1]) == k]
    bandc.sort(key=lambda t: -t[1])
    print(x['num'], 'k_rec', k, [(s, round(pr * 100, 1), x['odds']['crs'].get(s)) for s, pr in bandc[:3]])
print('saved predictions')
