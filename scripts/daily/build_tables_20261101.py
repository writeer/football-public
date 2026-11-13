# -*- coding: utf-8 -*-
"""2026-11-01 联赛积分榜刷新（football-charts MCP，当前轮次）
覆盖：japan1/korea1/australia/holland1/italy1/spain1/sweden1/norway/germany1/premier/portugal1/france1
巴西杯（淘汰赛）与美职（MLS）另行确认。
"""
import sys, io, json
from pathlib import Path
sys.path.insert(0, str(Path('football_mcp/python').resolve()))
from football_mcp_client import call_tool

MAP = {
    'japan1': 'table_japan1.json', 'korea1': 'table_korea1.json',
    'australia': 'table_australia.json', 'holland1': 'table_holland1.json',
    'italy1': 'table_italy1.json', 'spain1': 'table_spain1.json',
    'sweden1': 'table_sweden1.json', 'norway': 'table_norway.json',
    'germany1': 'table_germany1.json', 'premier': 'table_premier.json',
    'portugal1': 'table_portugal1.json', 'france1': 'table_france1.json',
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
    json.dump({'league': d.get('league'), 'season': d.get('season'), 'table': rows},
              io.open('reports/data/' + fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    played = sorted({r['played'] for r in rows})
    print(fn, d.get('season'), len(rows), 'played', played)

# 探联赛 key：找美职/巴西
try:
    lg = call_tool('football-charts', 'list_leagues', {}, timeout=180)
    names = json.dumps(lg, ensure_ascii=False)
    for kw in ['usa', 'mls', 'brazil', 'brasil']:
        idx = names.lower().find(kw)
        print('KW', kw, names[max(0, idx - 80):idx + 120].replace('\n', ' ') if idx >= 0 else 'not found')
except Exception as e:
    print('list fail', e)
