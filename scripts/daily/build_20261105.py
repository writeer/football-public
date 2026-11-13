# -*- coding: utf-8 -*-
"""2026-11-05 周四 13场推荐口径生成：规则63单关上修 + L266/L267/L268/L270/L272"""
import json

M = json.load(open('reports/data/20261105_model_output.json', encoding='utf-8'))
ORDER = ['周四%03d' % i for i in range(1, 14)]

BANDS = [
    ('闷战超小球(0-1球)', ['0', '1']),
    ('小球(1-2球)', ['1', '2']),
    ('常规正常球(2-3球)', ['2', '3']),
    ('大球(4-5球)', ['4', '5']),
    ('超大球(5-6球)', ['5', '6']),
    ('穿盘可能(6-7+球)', ['6', '7+']),
]

HAFU_QUOTA = {'home': ['HH', 'DH', 'AH'], 'away': ['AA', 'DA', 'HA'], 'draw': ['DD', 'DH', 'DA']}
HAFU_CN = {'HH': '胜胜', 'HD': '胜平', 'HA': '胜负', 'DH': '平胜', 'DD': '平平', 'DA': '平负',
           'AH': '负胜', 'AD': '负平', 'AA': '负负'}
HAFU_REV = {v: k for k, v in HAFU_CN.items()}


def r63(p, gap_tier=None):
    """规则63：平局上修后归一化；返回 (新概率, 档位, 系数, 上修前平局, 上修后平局原始值)"""
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


# 规则32 残阵人工传导（仅 007：特拉布宗11人伤病+3人未报名，主胜不作首选）
# 说明：模型 λ 已按残阵下调，但主胜仍以37.1%微弱领先；按规则32/L253 将首选改为客胜、次选平，
# 并在报告中记录“模型首选 vs 规则32首选”的冲突事实。
OVERRIDE = {
    '周四007': {'first': 'away', 'second': 'draw',
                'reason': '规则32/L253 残阵降级：特拉布宗11人伤病+3人未报名，主胜37.1%不作首选'},
}

out = []
for num in ORDER:
    r = M[num]
    p = dict(r['probs_final'])
    single = (num == '周四002')
    sm = None
    if single:
        q, gap, tier, mult, d0, d1 = r63(p)
        p = q
        sm = {'is_single': True, 'source': '用户赛前告知（投注端）',
              'api_bettingSingle': False, 'conflict': '接口 bettingSingle=false 与用户投注端“002为单关”冲突，以用户为准',
              'gap_pp': round(gap, 1), 'tier': tier, 'multiplier': mult,
              'draw_before_pct': round(d0 * 100, 2), 'draw_after_raw_pct': round(d1 * 100, 2),
              'final': {k: round(v * 100, 1) for k, v in p.items()},
              'second_after': 'draw' if p['draw'] >= max(p['home'], p['away']) else None}

    dirs = sorted(p.items(), key=lambda x: -x[1])
    first_key, first_p = dirs[0]
    second_key, second_p = dirs[1]
    override_reason = None
    if num in OVERRIDE:
        ov = OVERRIDE[num]
        first_key, second_key = ov['first'], ov['second']
        first_p, second_p = p[first_key], p[second_key]
        override_reason = ov['reason']

    # 半全场TOP3（L267 固定配额）
    quota = HAFU_QUOTA[first_key]
    hafu = []
    for c in quota:
        hafu.append((c, r['htft'].get(c, 0.0)))
    # 补齐：若配额位之外还有非配额组合概率高于第三位，不影响配额（配额永久保留）
    hafu_sorted = sorted(hafu, key=lambda x: -x[1])

    # 总进球TOP2（模型单点最高两项）
    ttg_pts = [(k, v) for k, v in r['ttg'].items()]
    ttg_top2 = sorted(ttg_pts, key=lambda x: -x[1])[:2]
    band_probs = {name: sum(r['ttg'][k] for k in ks) for name, ks in BANDS}
    band_name = max(band_probs.items(), key=lambda x: x[1])

    # 大小球六档：主档 + 次档
    band_sorted = sorted(band_probs.items(), key=lambda x: -x[1])

    # 让球（L268 结构腿剔除）
    h = r['handicap']
    line = h['line']
    if line == 1:
        structure = 'win'      # +1让胜
    elif line == -1:
        structure = 'lose'     # -1让负
    elif line == 2:
        structure = 'win'      # +2让胜
    elif line == -2:
        structure = 'lose'     # -2让负（同构结构腿）
    else:
        structure = None
    hp = {'win': h['win'], 'push': h['push'], 'lose': h['lose']}
    non_struct = sorted(((k, v) for k, v in hp.items() if k != structure), key=lambda x: -x[1])

    # 市场分歧
    mk = r['market']
    div = None
    if mk:
        div = round((p[first_key] - mk[first_key]) * 100, 1)

    odds = r['odds']
    out.append({
        'num': num, 'home': r['home'], 'away': r['away'], 'league': r['league'], 'time': r['time'],
        'lambda': r['lambda'], 'probs': {k: round(v * 100, 1) for k, v in p.items()},
        'first': first_key, 'second': second_key, 'firstProb': round(first_p * 100, 1),
        'secondProb': round(second_p * 100, 1),
        'is_single': single, 'single_match': sm, 'override_reason': override_reason,
        'over25': round((1 - sum(r['ttg'][k] for k in ('0', '1', '2'))) * 100, 1),
        'under25': round(sum(r['ttg'][k] for k in ('0', '1', '2')) * 100, 1),
        'scoreTop5': [(s, round(v * 100, 1)) for s, v in r['top_scores'][:5]],
        'scoreTop10': [(s, round(v * 100, 1)) for s, v in r['top_scores'][:10]],
        'ttgTop2': [(k, round(v * 100, 1)) for k, v in ttg_top2],
        'band': band_name[0], 'bandProb': round(band_name[1] * 100, 1),
        'bandSorted': [(a, round(b * 100, 1)) for a, b in band_sorted],
        'ttgFull': [(k, round(v * 100, 1)) for k, v in r['ttg'].items()],
        'hafuTop3': [(HAFU_CN[c], round(v * 100, 1)) for c, v in hafu_sorted],
        'hafuAll': [(HAFU_CN[k], round(v * 100, 1)) for k, v in r['htft'].items()],
        'htScoreTop3': [(s, round(v * 100, 1)) for s, v in r['ht_scores'][:3]],
        'handicap': {'line': line, 'win': round(h['win'] * 100, 1), 'push': round(h['push'] * 100, 1),
                     'lose': round(h['lose'] * 100, 1),
                     'first': non_struct[0][0], 'firstProb': round(non_struct[0][1] * 100, 1),
                     'second': non_struct[1][0], 'secondProb': round(non_struct[1][1] * 100, 1),
                     'structure': structure, 'structureProb': round(hp[structure] * 100, 1) if structure else None},
        'market': ({k: round(v * 100, 1) for k, v in mk.items() if k != 'overround'} if mk else None),
        'divergence': div,
        'odds': odds,
        'k_dist': r['k_dist'], 'k_rec': r['k_rec'],
    })

# 打印
for o in out:
    print(o['num'], o['home'], 'vs', o['away'], '|', o['league'], o['time'], '| λ', o['lambda']['home'], o['lambda']['away'])
    print('  HAD', o['probs'], '首选', o['first'], o['firstProb'], '次选', o['second'], o['secondProb'],
          '| 市场', o['market'], '| 分歧', o['divergence'])
    print('  比分TOP5', o['scoreTop5'])
    print('  TTG', o['ttgTop2'], '| 档', o['band'], o['bandProb'], '| 全档', o['bandSorted'])
    print('  半全场', o['hafuTop3'], '| 半场比分', o['htScoreTop3'])
    print('  让球 line', o['handicap']['line'], o['handicap']['win'], o['handicap']['push'], o['handicap']['lose'],
          '| 首选', o['handicap']['first'], o['handicap']['firstProb'],
          '| 次选', o['handicap']['second'], o['handicap']['secondProb'],
          '| 结构腿', o['handicap']['structure'], o['handicap']['structureProb'])
    print('  赔率 HAD', o['odds']['had'], 'HHAD', o['odds']['hhad'], 'TTG', o['odds']['ttg'], 'HAFU', o['odds']['hafu'])
    print()

json.dump(out, open('reports/data/20261105_predictions.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved reports/data/20261105_predictions.json')
