# -*- coding: utf-8 -*-
"""输出 11-03 全玩法赔率摘要（供报告与串关取赔）"""
import json, io, itertools

ms = json.load(io.open('reports/data/20261103_matches.json', encoding='utf-8'))
lines = []
def odds_of(outs, key):
    for o in outs:
        if o['key'] == key: return o['odds']
    return None

for m in ms:
    lines.append(f"\n### {m['num']} {m['league']} {m['home']} vs {m['away']} | 单关API={m['betting_single']} gl={m['hhad']['goalLine'] if m.get('hhad') else 'NA'}")
    if m.get('had'):
        h = {o['key']: o['odds'] for o in m['had']}
        d = m['had']
        inv = [1/o['odds'] for o in d]; s = sum(inv)
        lines.append(f"HAD 主{h['home']} 平{h['draw']} 客{h['away']} | 去水 {'/'.join(f'{x/s*100:.1f}%' for x in inv)}")
    if m.get('hhad'):
        h = {o['key']: o['odds'] for o in m['hhad']['outcomes']}
        lines.append(f"HHAD({m['hhad']['goalLine']}) 让胜{h['home']} 让平{h['draw']} 让负{h['away']}")
    if m.get('ttg'):
        lines.append('TTG ' + ' '.join(f"{o['key']}={o['odds']}" for o in m['ttg']))
    if m.get('hafu'):
        lines.append('HAFU ' + ' '.join(f"{o['key']}={o['odds']}" for o in m['hafu']))
    if m.get('crs'):
        srt = sorted(m['crs'], key=lambda o: o['odds'])[:14]
        lines.append('CRS(低赔14) ' + ' '.join(f"{o['key']}={o['odds']}" for o in srt))

txt = '\n'.join(lines)
io.open('reports/data/odds_summary_20261103.txt', 'w', encoding='utf-8').write(txt)
print(txt)
