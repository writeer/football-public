# -*- coding: utf-8 -*-
"""抓取 MLS(usa1) 与巴甲(brazil1) 积分榜，并刷新 024/025 所需球队数据"""
import sys, io, json
from pathlib import Path
sys.path.insert(0, str(Path('football_mcp/python').resolve()))
from football_mcp_client import call_tool

for key, fn in [('usa1', 'table_usa1.json'), ('brazil1', 'table_brazil1.json')]:
    d = call_tool('football-charts', 'get_league_table', {'league': key}, timeout=240)
    rows = []
    for r in d.get('table') or []:
        p = r.get('played') or 0
        gf = r.get('goals_for') or 0
        ga = r.get('goals_against') or 0
        rows.append({'team': r.get('team'), 'position': r.get('position'), 'played': p,
                     'won': r.get('won'), 'drawn': r.get('drawn'), 'lost': r.get('lost'),
                     'goals_for': gf, 'goals_against': ga,
                     'avg_goals_scored': round(gf / p, 3) if p else 0,
                     'avg_goals_conceded': round(ga / p, 3) if p else 0,
                     'points': r.get('points'), 'last_5_form': None, 'last_5_points': None})
    json.dump({'league': d.get('league'), 'season': d.get('season'), 'table': rows},
              io.open('reports/data/' + fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(fn, d.get('season'), len(rows), [r['team'] for r in rows][:24])
