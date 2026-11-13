# -*- coding: utf-8 -*-
"""2026-11-08（周日）体彩竞彩赔率抓取 → reports/data/20261108_raw.json"""
import sys, io, json, datetime
from pathlib import Path
sys.path.insert(0, str(Path('football_mcp/python').resolve()))
from football_mcp_client import call_tool

data = call_tool('sporttery-odds', 'get_matches', {'pools': 'had,hhad,crs,ttg,hafu'}, timeout=180)
data['fetched_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
out = 'reports/data/20261108_raw.json'
io.open(out, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1))
groups = data.get('matches') or (data.get('data') or {}).get('matches') or []
print('updatedAt', data.get('updatedAt'), 'fetched_at', data['fetched_at'], 'matchCount', len(groups))
dates = {}
for g in groups:
    dates[g.get('matchNumDate')] = dates.get(g.get('matchNumDate'), 0) + 1
print('dates', dates)
print('saved', out)
