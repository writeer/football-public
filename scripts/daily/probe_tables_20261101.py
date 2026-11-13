# -*- coding: utf-8 -*-
"""刷新 2026-11-01 分析所需联赛积分榜（football-charts MCP），仅取本赛季当前榜"""
import sys, io, json
from pathlib import Path
sys.path.insert(0, str(Path('football_mcp/python').resolve()))
from football_mcp_client import call_tool

LEAGUES = ['japan1', 'korea1', 'australia', 'holland1', 'italy1', 'spain1',
           'sweden1', 'norway', 'germany1', 'premier', 'portugal1', 'france1']

try:
    print([l for l in call_tool('football-charts', 'list_leagues', {}, timeout=180)])
except Exception as e:
    print('list_leagues failed:', e)

for lg in LEAGUES:
    try:
        d = call_tool('football-charts', 'get_league_table', {'league': lg}, timeout=240)
        s = json.dumps(d, ensure_ascii=False)
        print(lg, 'ok len', len(s), s[:220].replace('\n', ' '))
    except Exception as e:
        print(lg, 'FAIL', e)
