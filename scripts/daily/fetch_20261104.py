# -*- coding: utf-8 -*-
"""2026-11-04（周三）体彩竞彩赔率抓取 → reports/data/20261104_raw.json"""
import sys, io, json
from pathlib import Path
sys.path.insert(0, str(Path('football_mcp/python').resolve()))
from football_mcp_client import call_tool

data = call_tool('sporttery-odds', 'get_matches', {'pools': 'had,hhad,crs,ttg,hafu'}, timeout=180)
out = 'reports/data/20261104_raw.json'
io.open(out, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1))
groups = data.get('matches') or (data.get('data') or {}).get('matches') or []
print('updatedAt', data.get('updatedAt'), 'matchCount', len(groups))
from collections import Counter
print('dates', Counter(g.get('matchNumDate') for g in groups))
print('saved', out)
