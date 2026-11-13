# -*- coding: utf-8 -*-
import json, io
ms = json.load(io.open('reports/data/20261104_matches.json', encoding='utf-8'))
for m in ms:
    had = {o['key']: o['odds'] for o in m.get('had', [])}
    inv = [1/had['home'], 1/had['draw'], 1/had['away']]; s = sum(inv)
    mk = {k: round(v/s*100, 1) for k, v in zip(['home', 'draw', 'away'], inv)}
    hh = m.get('hhad')
    hhs = ''
    if hh:
        hho = {o['key']: o['odds'] for o in hh['outcomes']}
        hhs = f"line={hh['goalLine']} " + ' '.join(f"{k}:{hho[k]}" for k in ['home', 'draw', 'away'])
    ttg = ' '.join(f"{o['key']}:{o['odds']}" for o in m.get('ttg', [])[:6])
    hafu = ' '.join(f"{o['key']}:{o['odds']}" for o in sorted(m.get('hafu', []), key=lambda x: x['odds'])[:4])
    print(f"{m['num']} {m['league']} {m['home']}({m['home_rank']}) vs {m['away']}({m['away_rank']}) {m['match_date']} {m['time']}")
    print(f"   HAD {had} 去水%={mk}  单关={m['betting_single']}")
    print(f"   HHAD {hhs}")
    print(f"   TTG {ttg}")
    print(f"   HAFU低赔 {hafu}")
