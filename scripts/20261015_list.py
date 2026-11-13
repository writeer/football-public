# -*- coding: utf-8 -*-
import sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'sporttery_bridge/python')
from sporttery_client import get_matches

ms = get_matches()
with open('reports/data/20261015_matches_raw.json', 'w', encoding='utf-8') as f:
    json.dump(ms, f, ensure_ascii=False, indent=2)

for m in ms['matches']:
    h = m['home']; a = m['away']; l = m['league']
    had = m.get('had', {}) or {}
    hh = m.get('hhad', {}) or {}
    bs = m.get('bettingSingle', '?')
    print(f"{m['matchNumStr']} | {l['abbName']:6s} | {m['matchDate']} {m['matchTime']} | "
          f"{h['abbName']:10s}{h.get('rank','')} vs {a['abbName']:10s}{a.get('rank','')} | "
          f"HAD {had.get('h','-')}/{had.get('d','-')}/{had.get('a','-')} | "
          f"HHAD {hh.get('h','-')}/{hh.get('d','-')}/{hh.get('a','-')}(让{hh.get('goal','-')}) | 单关={bs}")
