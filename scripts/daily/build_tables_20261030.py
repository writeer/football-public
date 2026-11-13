# -*- coding: utf-8 -*-
"""2026-10-30 联赛积分榜落盘（含场均进失球，供 lottery_agent.fundamental 使用）"""
import json, os

RAW = json.load(open('reports/data/20261030_tables_raw.json', encoding='utf-8'))
CHA = json.load(open('reports/data/20261030_table_championship.json', encoding='utf-8'))

MAP = {
    '澳超': ('australia', 'table_australia.json'),
    '德乙': ('germany2', 'table_germany2.json'),
    '法甲': ('france1', 'table_france1.json'),
    '挪超': ('norway', 'table_norway.json'),
    '荷乙': ('holland2', 'table_holland2.json'),
    '德甲': ('germany1', 'table_germany1.json'),
    '西甲': ('spain1', 'table_spain1.json'),
    '葡超': ('portugal1', 'table_portugal1.json'),
    '巴甲': ('brazil1', 'table_brazil1.json'),
}

for cn, (key, fn) in MAP.items():
    src = RAW[cn]
    rows = []
    for r in src['table']:
        p = r.get('played') or 0
        gf = r.get('goals_for') or 0
        ga = r.get('goals_against') or 0
        rows.append({
            'team': r['team'],
            'position': r.get('position'),
            'played': p,
            'won': r.get('won'), 'drawn': r.get('drawn'), 'lost': r.get('lost'),
            'goals_for': gf, 'goals_against': ga,
            'avg_goals_scored': round(gf / p, 3) if p else 0.0,
            'avg_goals_conceded': round(ga / p, 3) if p else 0.0,
            'points': r.get('points'),
            'last_5_form': r.get('last_5_form'),
            'last_5_points': r.get('last_5_points'),
        })
    out = {'league': cn, 'season': '2026-2027', 'table': rows}
    json.dump(out, open(os.path.join('reports/data', fn), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(fn, len(rows))

rows = []
for r in CHA['table']:
    p = r.get('played') or 0
    gf = r.get('goals_for') or 0
    ga = r.get('goals_against') or 0
    rows.append({
        'team': r['team'], 'position': r.get('position'), 'played': p,
        'won': r.get('won'), 'drawn': r.get('drawn'), 'lost': r.get('lost'),
        'goals_for': gf, 'goals_against': ga,
        'avg_goals_scored': round(gf / p, 3) if p else 0.0,
        'avg_goals_conceded': round(ga / p, 3) if p else 0.0,
        'points': r.get('points'), 'last_5_form': r.get('last_5_form'),
        'last_5_points': r.get('last_5_points'),
    })
json.dump({'league': '英冠', 'season': '2026-2027', 'table': rows},
          open('reports/data/table_championship.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('table_championship.json', len(rows))
