# -*- coding: utf-8 -*-
"""提取 2026-10-17 周六场次（30场）为模型工作文件"""
import json

SRC = 'reports/data/20261017_matches_raw.json'
OUT = 'reports/data/20261017_saturday_matches.json'

d = json.load(open(SRC, encoding='utf-8-sig'))['data']
ms = [m for m in d['matches'] if m['matchNumStr'].startswith('周六')]
out = []
for m in ms:
    mk = m['markets']
    def oc(pool):
        p = mk.get(pool) or {}
        return [{'key': o.get('key'), 'odds': o.get('odds'), 'noVig': o.get('noVigProb')} for o in p.get('outcomes', [])]
    out.append({
        'num': m['matchNumStr'],
        'matchId': m['matchId'],
        'time': m['matchDate'] + ' ' + m['matchTime'],
        'league': m['league']['abbName'],
        'league_all': m['league']['allName'],
        'home': m['home']['allName'],
        'away': m['away']['allName'],
        'home_rank': m['home'].get('rank', ''),
        'away_rank': m['away'].get('rank', ''),
        'had': oc('had'),
        'hhad': {'goalLine': (mk.get('hhad') or {}).get('goalLine'), 'outcomes': oc('hhad')},
        'ttg': oc('ttg'),
        'hafu': oc('hafu'),
        'crs': oc('crs'),
    })
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved', OUT, len(out))
for x in out:
    print(x['num'], x['time'], x['league'], x['home'], 'vs', x['away'])
