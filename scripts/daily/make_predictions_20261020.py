# -*- coding: utf-8 -*-
"""2026-10-20（周二）10场：生成 predictions.json（6维度+赔率）与 parlay.json（串关方案）"""
import json, io, sys
sys.stdout.reconfigure(encoding='utf-8')

MODEL = 'reports/data/20261020_model_output.json'
PRED = 'reports/data/20261020_predictions.json'
PARLAY = 'reports/data/20261020_parlay.json'

MODELS = json.load(io.open(MODEL, encoding='utf-8'))
by = {m['num']: m for m in MODELS}

# 规则46 + 规则8/11/28：置信度（总控裁决）
CONF = {
    '周二001': ('★★', '模型主胜49.8% vs 市场60.7%，分歧10.9pp；双方合计11人伤停（规则11上限★★）；斯拉维亚后防3人缺阵支撑主胜，但首选不足50%'),
    '周二002': ('★', '模型客胜51.9% vs 市场74.4%，分歧22.5pp（规则8：严重分歧，仅极小注）；萨巴赫国内18:1极端数据经身价/等级差校准后仍偏高'),
    '周二003': ('★★', '模型主胜60.2%与市场60.6%高度对齐；但双方合计15人伤停/成疑（规则11上限★★）；朴次茅斯锋线真空'),
    '周二004': ('★★', '模型主胜49.5% vs 市场59.8%，分歧10.3pp；那不勒斯5人缺阵、两翼受损；首选不足50%'),
    '周二005': ('★★', '模型主胜85.5%与市场83.2%对齐；但双方合计8人伤停（规则11降级）'),
    '周二006': ('★★', '单关场次；模型客胜57.9% vs 市场40.2%（规则8分歧17.7pp），仅按方向参考、不宜重注'),
    '周二007': ('★', '模型主胜47.2% vs 市场66.0%，分歧18.8pp（规则8）；利物浦右路5人缺阵+单关平局上修'),
    '周二008': ('★★', '模型主胜73.0% vs 市场85.4%，分歧12.4pp；曼城轮换风险（哈兰德等4人评估）'),
    '周二009': ('★★', '模型主胜42.0% vs 市场29.5%，分歧12.5pp；双方合计5人伤停（规则46上限★★）'),
    '周二010': ('★★', '模型主胜67.3%与市场63.2%对齐；PSV 9人伤兵（规则11降级）'),
}

DIR_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC_CN = {'home': '让胜', 'draw': '让平', 'away': '让负'}

preds = []
for m in MODELS:
    num = m['num']
    conf, conf_reason = CONF[num]
    crs = [(f'{a}-{b}', p) for a, b, p in m['top_scores'][:5]]
    band = [(f'{a}-{b}', p) for a, b, p in m['band'][:3]]
    ht3 = m['htft_top3']
    hts = [(f'{a}-{b}', p) for a, b, p in m['ht_scores'][:3]]
    ttg = m['ttg_top2']
    tg = m['tg']
    rec = {
        'num': num, 'league': m['league'], 'home': m['home'], 'away': m['away'],
        'kickoff': m['time'], 'is_single': m['is_single'],
        'stadium_status': '正常',
        'lambda': {'home': m['lambda_home'], 'away': m['lambda_away'], 'total': m['lambda_total'],
                   'source': 'fundamental(rule79)', 'rule76': m['rule76'], 'value_mult': m['value_mult']},
        'model_prob': m['fused'], 'market_prob': m['market'],
        'primary': {'dir': m['primary'], 'cn': DIR_CN[m['primary']], 'prob': m['primary_prob']},
        'secondary': {'dir': m['secondary'], 'cn': DIR_CN[m['secondary']], 'prob': m['secondary_prob']},
        'had': {'odds': m['odds_had'], 'single_note': m['single_note']},
        'hhad': {'line': m['hhad_line'], 'odds': m['odds_hhad'],
                 'first': {'dir': m['hc_first'], 'cn': HC_CN[m['hc_first']],
                           'prob': (m['hhad_model'] or {}).get(m['hc_first']) if m['hhad_model'] else None},
                 'second': {'dir': m['hc_second'], 'cn': HC_CN[m['hc_second']],
                            'prob': (m['hhad_model'] or {}).get(m['hc_second']) if m['hhad_model'] else None},
                 'model': m['hhad_model'], 'market': m['hhad_market']},
        'crs_top5': crs, 'ttg_top2': [{'goals': g, 'prob': tg[str(g)], 'odds': m['odds_ttg'].get(str(g))} for g in ttg],
        'tier': m['tier'], 'p01': m['p01'], 'p23': m['p23'], 'p45': m['p45'], 'p6': m['p6'],
        'hafu_top3': [{'code': c, 'prob': p, 'odds': m['odds_hafu'].get({'胜胜': 'HH', '胜平': 'HD', '胜负': 'HA', '平胜': 'DH', '平平': 'DD', '平负': 'DA', '负胜': 'AH', '负平': 'AD', '负负': 'AA'}[c])} for c, p in ht3],
        'ht_scores_top3': hts,
        'k_dist': {'value': m['k_dist'], 'prob': m['k_dist_prob']},
        'k_rec': {'value': m['k_rec'], 'prob': m['k_rec_prob']},
        'k_consistent': m['k_consistent'], 'band_top3': band,
        'confidence': conf, 'confidence_reason': conf_reason,
        'adj_note': m['adj_note'], 'odds_had': m['odds_had'], 'odds_hhad': m['odds_hhad'],
        'odds_ttg': m['odds_ttg'], 'odds_hafu': m['odds_hafu'], 'odds_crs': m['odds_crs'],
    }
    preds.append(rec)

json.dump(preds, io.open(PRED, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---------------- 串关 ----------------
O = {m['num']: m for m in MODELS}


def crs_odds(num, score):
    return O[num]['odds_crs'].get(score)


def ttg_odds(num, g):
    return O[num]['odds_ttg'].get(str(g))


def had_odds(num, side):
    return (O[num]['odds_had'] or {}).get(side)


def hhad_odds(num, side):
    return (O[num]['odds_hhad'] or {}).get(side)


def hafu_odds(num, code):
    rev = {'胜胜': 'HH', '胜平': 'HD', '胜负': 'HA', '平胜': 'DH', '平平': 'DD', '平负': 'DA', '负胜': 'AH', '负平': 'AD', '负负': 'AA'}
    return O[num]['odds_hafu'].get(rev[code])


def prod(vals):
    r = 1.0
    for v in vals:
        r *= v
    return round(r, 2)


parlay = {
    'date': '2026-10-20',
    'rule71_filter': '当天非PSG法甲0场 → 娱乐串纳入0场',
    'direction': [
        {'name': '方向串A', 'cluster': 'B+C+E',
         'legs': [{'num': '周二003', 'pick': '主胜', 'odds': had_odds('周二003', 'home'), 'prob': O['周二003']['fused']['home']},
                  {'num': '周二002', 'pick': '客胜', 'odds': had_odds('周二002', 'away'), 'prob': O['周二002']['fused']['away']},
                  {'num': '周二001', 'pick': '主胜', 'odds': had_odds('周二001', 'home'), 'prob': O['周二001']['fused']['home']}],
         'odds': None},
    ],
    'handicap': [
        {'name': '稳健让球串', 'cluster': 'C+D',
         'legs': [{'num': '周二002', 'pick': '让(+2)胜', 'odds': hhad_odds('周二002', 'home'), 'prob': O['周二002']['hhad_model']['home']},
                  {'num': '周二009', 'pick': '让(+1)胜', 'odds': hhad_odds('周二009', 'home'), 'prob': O['周二009']['hhad_model']['home']}],
         'odds': None},
    ],
    'mixed_thought': [
        {'name': '混合串（方向+让球）', 'cluster': 'B+D+A',
         'legs': [{'num': '周二003', 'pick': '主胜', 'odds': had_odds('周二003', 'home')},
                  {'num': '周二009', 'pick': '让(+1)胜', 'odds': hhad_odds('周二009', 'home')},
                  {'num': '周二004', 'pick': '主胜', 'odds': had_odds('周二004', 'home')}],
         'odds': None},
    ],
    'entertainment': {
        'ttg': [
            {'name': '总进球串A', 'legs': [{'num': '周二006', 'pick': '5球', 'odds': ttg_odds('周二006', 5)},
                                            {'num': '周二010', 'pick': '4球', 'odds': ttg_odds('周二010', 4)},
                                            {'num': '周二005', 'pick': '4球', 'odds': ttg_odds('周二005', 4)}]},
            {'name': '总进球串B', 'legs': [{'num': '周二008', 'pick': '4球', 'odds': ttg_odds('周二008', 4)},
                                            {'num': '周二004', 'pick': '3球', 'odds': ttg_odds('周二004', 3)},
                                            {'num': '周二001', 'pick': '3球', 'odds': ttg_odds('周二001', 3)}]},
            {'name': '连续编号总进球串①', 'legs': [{'num': '周二001', 'pick': '3球', 'odds': ttg_odds('周二001', 3)},
                                                    {'num': '周二002', 'pick': '2球', 'odds': ttg_odds('周二002', 2)}]},
            {'name': '连续编号总进球串②', 'legs': [{'num': '周二009', 'pick': '3球', 'odds': ttg_odds('周二009', 3)},
                                                    {'num': '周二010', 'pick': '4球', 'odds': ttg_odds('周二010', 4)}]},
        ],
        'hafu': [
            {'name': '高赔半全场串A', 'legs': [{'num': '周二001', 'pick': '平胜', 'odds': hafu_odds('周二001', '平胜')},
                                                {'num': '周二008', 'pick': '胜胜', 'odds': hafu_odds('周二008', '胜胜')},
                                                {'num': '周二003', 'pick': '平胜', 'odds': hafu_odds('周二003', '平胜')}]},
            {'name': '高赔半全场串B', 'legs': [{'num': '周二009', 'pick': '平胜', 'odds': hafu_odds('周二009', '平胜')},
                                                {'num': '周二004', 'pick': '胜胜', 'odds': hafu_odds('周二004', '胜胜')},
                                                {'num': '周二002', 'pick': '平平', 'odds': hafu_odds('周二002', '平平')}]},
            {'name': '连续编号高赔半全场串①', 'legs': [{'num': '周二001', 'pick': '平胜', 'odds': hafu_odds('周二001', '平胜')},
                                                        {'num': '周二002', 'pick': '平负', 'odds': hafu_odds('周二002', '平负')}]},
            {'name': '连续编号高赔半全场串②', 'legs': [{'num': '周二009', 'pick': '平胜', 'odds': hafu_odds('周二009', '平胜')},
                                                        {'num': '周二010', 'pick': '胜胜', 'odds': hafu_odds('周二010', '胜胜')}]},
        ],
        'mix': [
            {'name': '混合串A', 'legs': [{'num': '周二006', 'pick': '5球', 'odds': ttg_odds('周二006', 5)},
                                          {'num': '周二003', 'pick': '胜胜', 'odds': hafu_odds('周二003', '胜胜')},
                                          {'num': '周二008', 'pick': '胜胜', 'odds': hafu_odds('周二008', '胜胜')}]},
            {'name': '混合串B', 'legs': [{'num': '周二005', 'pick': '胜胜', 'odds': hafu_odds('周二005', '胜胜')},
                                          {'num': '周二007', 'pick': '3球', 'odds': ttg_odds('周二007', 3)},
                                          {'num': '周二004', 'pick': '2球', 'odds': ttg_odds('周二004', 2)}]},
            {'name': '连续编号混合总进球串①', 'legs': [{'num': '周二006', 'pick': '5球', 'odds': ttg_odds('周二006', 5)},
                                                        {'num': '周二007', 'pick': '胜胜', 'odds': hafu_odds('周二007', '胜胜')}]},
            {'name': '连续编号混合总进球串②', 'legs': [{'num': '周二009', 'pick': '胜胜', 'odds': hafu_odds('周二009', '胜胜')},
                                                        {'num': '周二010', 'pick': '4球', 'odds': ttg_odds('周二010', 4)}]},
        ],
        'crs': [
            {'name': '稳健比分串', 'legs': [{'num': '周二005', 'pick': '3-0', 'odds': crs_odds('周二005', '3:0'), 'prob': 0.114},
                                            {'num': '周二010', 'pick': '3-1', 'odds': crs_odds('周二010', '3:1'), 'prob': 0.080}]},
            {'name': '搏冷比分串（反向推理）', 'legs': [{'num': '周二002', 'pick': '1-0', 'odds': crs_odds('周二002', '1:0'), 'script': '多特远征巴库+轮换→萨巴赫主场爆冷'},
                                                    {'num': '周二006', 'pick': '2-1', 'odds': crs_odds('周二006', '2:1'), 'script': '巴萨双中卫+右后卫缺阵→PSG主场抢攻得手'}],
             'note': '反向推理，不计入规则67试用台账'},
            {'name': '连续编号比分串①', 'legs': [], 'note': '空缺：005+006虽相邻且两场均"众数一致"，但006带内最高仅6.1%（<8%胜率门槛）；008/010虽一致但被009隔开。不以不达标场次凑编号'},
            {'name': '连续编号比分串②', 'legs': [], 'note': '同上'},
            {'name': '单挑比分①', 'legs': [{'num': '周二005', 'pick': '4-0', 'odds': crs_odds('周二005', '4:0'), 'prob': 0.105}]},
            {'name': '单挑比分②', 'legs': [{'num': '周二008', 'pick': '3-1', 'odds': crs_odds('周二008', '3:1'), 'prob': 0.082}]},
        ],
    },
}

for group in ('direction', 'handicap', 'mixed_thought'):
    for p in parlay[group]:
        p['odds'] = prod([l['odds'] for l in p['legs']])
for grp in parlay['entertainment'].values():
    for p in grp:
        if p['legs']:
            p['odds'] = prod([l['odds'] for l in p['legs']])

json.dump(parlay, io.open(PARLAY, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# 控制台摘要
for p in preds:
    print(p['num'], p['home'], 'vs', p['away'], '|', p['primary']['cn'], '%.1f%%' % (p['primary']['prob'] * 100),
          '/', p['secondary']['cn'], '%.1f%%' % (p['secondary']['prob'] * 100), '| 让', p['hhad']['line'],
          p['hhad']['first']['cn'], '/', p['hhad']['second']['cn'], '| TTG', [t['goals'] for t in p['ttg_top2']], p['tier'], '|', p['confidence'])
print('--- parlay ---')
print(json.dumps(parlay, ensure_ascii=False, indent=1)[:2000])
print('saved', PRED, PARLAY)
