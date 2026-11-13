# -*- coding: utf-8 -*-
"""2026-11-06 周五 14 场推荐口径：规则63单关上修(007) + L266/L267/L270/L272/L280"""
import json

M = json.load(open('reports/data/20261106_model_output.json', encoding='utf-8'))
ORDER = ['周五%03d' % i for i in range(1, 15)]

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

# 置信度：★★★ 首选≥60%且与市场分歧≤7pp；★★ 首选45-59%或单关；★ 首选<45%或分歧≥10pp
CONF = {
    '周五001': '★★★', '周五002': '★★', '周五003': '★★★', '周五004': '★★',
    '周五005': '★', '周五006': '★★', '周五007': '★★', '周五008': '★',
    '周五009': '★★', '周五010': '★★', '周五011': '★', '周五012': '★★',
    '周五013': '★', '周五014': '★',
}

LEAGUE_LEVEL = {
    '周五001': ('澳超', 4), '周五002': ('德乙', 3), '周五003': ('瑞超', 4), '周五004': ('法乙', 3),
    '周五005': ('荷甲', 1), '周五006': ('荷乙', 4), '周五007': ('德甲', 1), '周五008': ('意甲', 1),
    '周五009': ('法甲', 1), '周五010': ('英超', 1), '周五011': ('英冠', 3), '周五012': ('西甲', 1),
    '周五013': ('葡超', 2), '周五014': ('巴甲', 2),
}


# L282 残阵降级：一方伤停≥7人且模型首选领先<5pp → 改判对手方向
# 011 德比郡约10人缺阵（什莫迪克斯、阿吉曼、卡辛、克拉克、福索、穆尔金等），
# 模型主胜37.4%仅领先客胜32.8% 4.6pp，触发改判客胜；次选平29.8%。
OVERRIDE = {
    '周五011': {'first': 'away', 'second': 'draw',
                'reason': 'L282 残阵降级：德比郡约10人缺阵，主胜37.4%仅领先4.6pp（<5pp），改判客胜'},
}


def r63(p):
    first = max(p['home'], p['draw'], p['away'])
    second = sorted([p['home'], p['draw'], p['away']], reverse=True)[1]
    gap = (first - second) * 100
    if gap <= 10:
        mult, tier = 1.13, '≤10pp'
    elif gap <= 20:
        mult, tier = 1.11, '≤20pp'
    else:
        mult, tier = 1.08, '≥20pp'
    d0 = p['draw']; d1 = d0 * mult
    tot = p['home'] + d1 + p['away']
    q = {'home': p['home'] / tot, 'draw': d1 / tot, 'away': p['away'] / tot}
    return q, gap, tier, mult, d0, d1


out = []
for num in ORDER:
    r = M[num]
    p0 = dict(r['probs_final'])
    p = dict(p0)
    single = (num == '周五007')  # 用户端告知；接口 bettingSingle=false（L273 以用户端为准）
    sm = None
    if single:
        q, gap, tier, mult, d0, d1 = r63(p)
        p = q
        sm = {'is_single': True, 'source': '用户赛前告知（投注端）',
              'api_bettingSingle': False, 'conflict': '接口 bettingSingle=false 与用户投注端“007为单关”冲突，以用户为准（L273）',
              'gap_pp': round(gap, 1), 'tier': tier, 'multiplier': mult,
              'draw_before_pct': round(d0 * 100, 2), 'draw_after_raw_pct': round(d1 * 100, 2),
              'final': {k: round(v * 100, 1) for k, v in p.items()},
              'first_under_50': round(max(p.values()) * 100, 1) < 50,
              'note': '首选<50%，按L277记作主胜/平双首选，上修只把平局抬进次选'}

    dirs = sorted(p.items(), key=lambda x: -x[1])
    first_key, first_p = dirs[0]
    second_key, second_p = dirs[1]
    override_reason = None
    if num in OVERRIDE:
        ov = OVERRIDE[num]
        first_key, second_key = ov['first'], ov['second']
        first_p, second_p = p[first_key], p[second_key]
        override_reason = ov['reason']

    quota = HAFU_QUOTA[first_key]
    hafu = [(c, r['htft'].get(c, 0.0)) for c in quota]
    hafu_sorted = sorted(hafu, key=lambda x: -x[1])

    ttg_pts = [(k, v) for k, v in r['ttg'].items()]
    ttg_top2 = sorted(ttg_pts, key=lambda x: -x[1])[:2]
    band_probs = {name: sum(r['ttg'][k] for k in ks) for name, ks in BANDS}
    band_name = max(band_probs.items(), key=lambda x: x[1])
    band_sorted = sorted(band_probs.items(), key=lambda x: -x[1])

    # L280 让球双轨：非结构首选 + 结构腿次选（结构腿≥50%或全场最高才占次选）
    h = r['handicap']; line = h['line']
    if line == 1: structure = 'win'
    elif line == -1: structure = 'lose'
    elif line == 2: structure = 'win'
    elif line == -2: structure = 'lose'
    else: structure = None
    hp = {'win': h['win'], 'push': h['push'], 'lose': h['lose']}
    non_struct = sorted(((k, v) for k, v in hp.items() if k != structure), key=lambda x: -x[1])
    hc_second = non_struct[1]
    hc_note = '次选=非结构腿'
    if structure and hp[structure] >= 0.50:
        hc_second = (structure, hp[structure])
        hc_note = '结构腿≥50%，按L280强制占次选位'

    mk = r['market']
    div = round((p[first_key] - mk[first_key]) * 100, 1) if mk else None

    odds = r['odds']
    out.append({
        'num': num, 'home': r['home'], 'away': r['away'], 'league': r['league'], 'time': r['time'],
        'league_level': LEAGUE_LEVEL[num], 'confidence': CONF[num],
        'lambda': r['lambda'], 'probs': {k: round(v * 100, 1) for k, v in p.items()},
        'probs_pre_single': {k: round(v * 100, 1) for k, v in p0.items()} if single else None,
        'first': first_key, 'second': second_key, 'firstProb': round(p[first_key] * 100, 1),
        'secondProb': round(p[second_key] * 100, 1),
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
                     'second': hc_second[0], 'secondProb': round(hc_second[1] * 100, 1),
                     'structure': structure, 'structureProb': round(hp[structure] * 100, 1) if structure else None,
                     'note': hc_note},
        'market': ({k: round(v * 100, 1) for k, v in mk.items() if k != 'overround'} if mk else None),
        'divergence': div,
        'odds': odds,
        'k_dist': r['k_dist'], 'k_rec': r['k_rec'],
    })

for o in out:
    print(o['num'], o['confidence'], o['home'], 'vs', o['away'], '|', o['league'], o['time'], '| λ', o['lambda']['home'], o['lambda']['away'])
    print('  HAD', o['probs'], '首选', o['first'], o['firstProb'], '次选', o['second'], o['secondProb'],
          '| 市场', o['market'], '| 分歧', o['divergence'])
    if o['single_match']: print('  单关', o['single_match'])
    print('  比分TOP5', o['scoreTop5'])
    print('  TTG', o['ttgTop2'], '| 档', o['band'], o['bandProb'], '| 全档', o['bandSorted'])
    print('  半全场', o['hafuTop3'], '| 半场比分', o['htScoreTop3'])
    print('  让球 line', o['handicap']['line'], o['handicap']['first'], o['handicap']['firstProb'],
          '| 次选', o['handicap']['second'], o['handicap']['secondProb'], '|', o['handicap']['note'])
    print()

json.dump(out, open('reports/data/20261106_predictions.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved reports/data/20261106_predictions.json')
