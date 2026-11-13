# -*- coding: utf-8 -*-
"""2026-11-03 需要的国内联赛积分榜抓取 → reports/data/tables_20261103.json"""
import sys, io, json
from pathlib import Path
sys.path.insert(0, str(Path('football_mcp/python').resolve()))
from football_mcp_client import call_tool

LEAGUES = ['australia','japan1','china','thai1','korea1','turkey1','germany1',
           'austria1','slovakia1','holland1','italy1','premier','spain1','france1','norway']

out = {}
for lg in LEAGUES:
    try:
        r = call_tool('football-charts', 'get_league_table', {'league': lg}, timeout=120)
        out[lg] = r
        rows = (r.get('data') or {}).get('table') or (r.get('data') or {}).get('rows') or []
        print(lg, 'OK rows', len(rows))
    except Exception as e:
        print(lg, 'FAIL', e)
        out[lg] = {'error': str(e)}

io.open('reports/data/tables_20261103.json','w',encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print('saved reports/data/tables_20261103.json')
