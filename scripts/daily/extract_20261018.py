import json, io, re

SRC = 'reports/data/20261018_matches_raw.json'
OUT = 'reports/data/20261018_matches.json'
raw = io.open(SRC, encoding='utf-8-sig').read()
j = json.loads(raw)
ms = j['data']['matches']
out = []
for x in ms:
    mk = x.get('markets') or {}
    had = mk.get('had') or {}
    hhad = mk.get('hhad') or {}
    crs = mk.get('crs') or {}
    ttg = mk.get('ttg') or {}
    hafu = mk.get('hafu') or {}
    out.append({
        'num': x['matchNumStr'],
        'matchId': x['matchId'],
        'time': x['matchDate'] + ' ' + x['matchTime'],
        'league': x['league']['abbName'],
        'league_all': x['league']['allName'],
        'home': x['home']['abbName'],
        'away': x['away']['abbName'],
        'home_all': x['home']['allName'],
        'away_all': x['away']['allName'],
        'home_rank': x['home'].get('rank') or '',
        'away_rank': x['away'].get('rank') or '',
        'betting_single': x.get('bettingSingle'),
        'had': [{'key': o['key'], 'odds': o['odds'], 'noVig': o.get('noVigProb')} for o in had.get('outcomes', [])],
        'hhad': {'goalLine': hhad.get('goalLine'),
                 'outcomes': [{'key': o['key'], 'odds': o['odds'], 'noVig': o.get('noVigProb')} for o in hhad.get('outcomes', [])]} if hhad else None,
        'crs': [{'key': o['key'], 'odds': o['odds'], 'noVig': o.get('noVigProb')} for o in crs.get('outcomes', [])],
        'ttg': [{'key': o['key'], 'odds': o['odds'], 'noVig': o.get('noVigProb')} for o in ttg.get('outcomes', [])],
        'hafu': [{'key': o['key'], 'odds': o['odds'], 'noVig': o.get('noVigProb')} for o in hafu.get('outcomes', [])],
    })
json.dump(out, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved', OUT, len(out))
for m in out:
    print(m['num'], m['league'], m['home'], 'vs', m['away'], 'hhad', (m['hhad'] or {}).get('goalLine'), 'crs', len(m['crs']), 'hafu', len(m['hafu']))
