# -*- coding: utf-8 -*-
"""2026-11-08 联赛积分榜刷新（football-charts MCP，当前轮次）
覆盖当日场次涉及联赛：西甲/芬超/荷甲/挪超/英超/意甲/德甲/瑞超/法甲/葡超
"""
import sys, io, json
from pathlib import Path
sys.path.insert(0, str(Path('football_mcp/python').resolve()))
from football_mcp_client import call_tool

MAP = {
    'spain1': 'table_spain1.json', 'finland1': 'table_finland1.json',
    'holland1': 'table_holland1.json', 'norway': 'table_norway.json',
    'premier': 'table_premier.json', 'italy1': 'table_italy1.json',
    'germany1': 'table_germany1.json', 'sweden1': 'table_sweden1.json',
    'france1': 'table_france1.json', 'portugal1': 'table_portugal1.json',
}

rows_out = {}
for key, fn in MAP.items():
    d = call_tool('football-charts', 'get_league_table', {'league': key}, timeout=240)
    t = d.get('table') or []
    rows = []
    for r in t:
        played = r.get('played') or 0
        gf = r.get('goals_for') or r.get('gf') or 0
        ga = r.get('goals_against') or r.get('ga') or 0
        rows.append({
            'team': r.get('team'), 'position': r.get('position'), 'played': played,
            'won': r.get('won'), 'drawn': r.get('drawn'), 'lost': r.get('lost'),
            'goals_for': gf, 'goals_against': ga,
            'avg_goals_scored': round(gf / played, 3) if played else 0,
            'avg_goals_conceded': round(ga / played, 3) if played else 0,
            'points': r.get('points'), 'last_5_form': None, 'last_5_points': None,
        })
    rows_out[key] = {'league': d.get('league'), 'season': d.get('season'), 'table': rows}
    json.dump(rows_out[key], io.open('reports/data/' + fn, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    played = sorted({r['played'] for r in rows})
    print(fn, d.get('season'), len(rows), 'played', played)
