# -*- coding: utf-8 -*-
"""2026-11-09（周一）竞彩在售全部场次全玩法赔率 → reports/data/20261109_raw.json"""
import sys, io, json
from pathlib import Path
sys.path.insert(0, str(Path('football_mcp/python').resolve()))
from football_mcp_client import call_tool

data = call_tool('sporttery-odds', 'get_matches', {'pools': 'had,hhad,crs,ttg,hafu'}, timeout=240)
out = 'reports/data/20261109_raw.json'
io.open(out, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1))
ms = data.get('matches') or []
print('updatedAt', data.get('updatedAt'), 'count', len(ms))
for m in ms:
    h = m.get('home') or {}; a = m.get('away') or {}
    print(m.get('matchNumStr'), m.get('matchDate'), m.get('matchTime'),
          (m.get('league') or {}).get('abbName'), h.get('abbName'), h.get('rank'),
          'vs', a.get('abbName'), a.get('rank'),
          '| single=', m.get('bettingSingle'),
          '| pools=', sorted((m.get('markets') or {}).keys()))
print('saved', out)
