# -*- coding: utf-8 -*-
"""2026-11-09（周一）在售轮次预测归档 JSON"""
import json, io, os
from pathlib import Path

model = json.load(io.open('reports/data/20261109_model_output.json', encoding='utf-8'))
raw = json.load(io.open('reports/data/20261109_raw.json', encoding='utf-8'))
byn = {m['matchNumStr']: m for m in raw['matches']}

META = {
    '周二001': dict(league='英锦标赛', home='伯顿', away='诺茨郡', time='2026-11-11 03:00',
                    conf='★', first='主胜', second='平',
                    tags='北区F组；同联赛英甲15 vs 英甲17；EFL Trophy轮换不确定；伤停/首发/身价信息缺失'),
    '周二002': dict(league='英锦标赛', home='布罗姆利', away='米尔顿', time='2026-11-11 03:30',
                    conf='★★', first='客胜', second='平',
                    tags='南区H组；同联赛英甲24 vs 英甲12；布罗姆利场均失2.54；伤停/首发/身价信息缺失'),
    '周三005': dict(league='英锦标赛', home='谢周三', away='阿克宁顿', time='2026-11-12 03:00',
                    conf='★★', first='主胜', second='平',
                    tags='北区A组；跨级英甲9 vs 英乙9；英乙进攻×0.85；伤停/首发/身价信息缺失'),
    '周三006': dict(league='英锦标赛', home='巴恩斯利', away='奥德汉姆', time='2026-11-12 03:00',
                    conf='★', first='主胜', second='平',
                    tags='北区G组；跨级英甲23 vs 英乙18；巴恩斯利近12场2胜；伤停/首发/身价信息缺失'),
}

TTG2 = {'周二001': ['2', '1'], '周二002': ['4', '3'], '周三005': ['2', '3'], '周三006': ['2', '1']}
BAND = {'周二001': ('小球', '小'), '周二002': ('大球', '大'),
        '周三005': ('常规正常球', '大'), '周三006': ('小球', '小')}

out = []
for num, md in META.items():
    m = model[num]
    p = m['probs_final']
    mk = m['market']
    had_o = {o['key']: o['odds'] for o in byn[num]['markets']['had']['outcomes']}
    hhad_m = byn[num]['markets']['hhad']
    hafu_o = {o['key']: o['odds'] for o in byn[num]['markets']['hafu']['outcomes']}
    crs_o = {o['key']: o['odds'] for o in byn[num]['markets']['crs']['outcomes']}
    ttg_o = {o['key']: o['odds'] for o in byn[num]['markets']['ttg']['outcomes']}
    first_p = p['home'] if md['first'] == '主胜' else (p['draw'] if md['first'] == '平' else p['away'])
    second_p = p['home'] if md['second'] == '主胜' else (p['draw'] if md['second'] == '平' else p['away'])
    div = {}
    for k in ['home', 'draw', 'away']:
        div[k] = round((p[k] - mk[k]) * 100, 1)
    hc = m['handicap']
    if hc['win'] >= hc['push'] and hc['win'] >= hc['lose']:
        h_first, h_second = '让胜', '让平' if hc['push'] >= hc['lose'] else '让负'
    elif hc['push'] >= hc['lose']:
        h_first, h_second = '让平', '让胜' if hc['win'] >= hc['lose'] else '让负'
    else:
        h_first, h_second = '让负', '让胜' if hc['win'] >= hc['push'] else '让平'
    row = {
        'num': num, 'league': md['league'], 'home': md['home'], 'away': md['away'],
        'time': md['time'], 'is_single': False, 'single_note': '接口 bettingSingle=0（未开单关）；用户端如显示单关请以用户端为准（L273）',
        'confidence': md['conf'],
        'probs': {k: round(v * 100, 1) for k, v in p.items()},
        'first': md['first'], 'second': md['second'],
        'firstProb': round(first_p * 100, 1), 'secondProb': round(second_p * 100, 1),
        'lambda': {'home': round(m['lambda']['home'], 2), 'away': round(m['lambda']['away'], 2),
                   'total': round(m['lambda']['total'], 2)},
        'market': {k: round(v * 100, 1) for k, v in mk.items() if k != 'overround'},
        'divergence': div, 'band': {'name': BAND[num][0], 'side': BAND[num][1]},
        'scoreTop5': [{'score': s, 'p': round(pp * 100, 1), 'odds': crs_o.get(s.replace('-', ':'))} for s, pp in m['top_scores'][:5]],
        'hafuTop3': [{'key': k, 'p': round(v * 100, 1), 'odds': hafu_o.get(k)} for k, v in list(m['htft'].items())[:3]],
        'htScoreTop3': [{'score': s, 'p': round(pp * 100, 1)} for s, pp in m['ht_scores'][:3]],
        'ttgTop2': [{'goals': g, 'p': round(m['ttg'][g] * 100, 1), 'odds': ttg_o.get(g)} for g in TTG2[num]],
        'over25': round(sum(v for k, v in m['ttg'].items() if k in ['3', '4', '5', '6', '7+']) * 100, 1),
        'under25': round(sum(v for k, v in m['ttg'].items() if k in ['0', '1', '2']) * 100, 1),
        'handicap': {'line': hc['line'], 'win': round(hc['win'] * 100, 1), 'push': round(hc['push'] * 100, 1),
                     'lose': round(hc['lose'] * 100, 1), 'first': h_first, 'second': h_second,
                     'firstProb': round(max(hc['win'], hc['push'], hc['lose']) * 100, 1)},
        'odds': {'had': had_o, 'hhad': {'line': hhad_m['goalLine'], **{o['key']: o['odds'] for o in hhad_m['outcomes']}},
                 'hafu': hafu_o, 'crs': crs_o, 'ttg': ttg_o},
        'k_dist': {'k': m['k_dist']['k'], 'p': round(m['k_dist']['p'] * 100, 1)},
        'k_rec': {'k': m['k_rec']['k'], 'p': round(m['k_rec']['p'] * 100, 1)},
        'tags': md['tags'], 'actual': None,
    }
    out.append(row)

json.dump(out, io.open('reports/data/20261109_predictions.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(out, io.open('reports/data/20261109_predictions_final.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
Path('memory/predictions/20261109_monday').mkdir(parents=True, exist_ok=True)
json.dump(out, io.open('memory/predictions/20261109_monday/prediction.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for r in out:
    print(r['num'], r['home'], 'vs', r['away'], '|', r['first'], r['firstProb'], '/', r['second'], r['secondProb'],
          '| 让', r['handicap']['first'], r['handicap']['firstProb'], '/', r['handicap']['second'],
          '| TTG', r['ttgTop2'], '| 大小', r['band'], '| 分歧', r['divergence'])
print('saved')
