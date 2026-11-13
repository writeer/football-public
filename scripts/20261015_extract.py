# -*- coding: utf-8 -*-
"""提取13场全玩法赔率，生成结构化摘要"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

d = json.load(open('reports/data/20261015_matches_raw.json', encoding='utf-8'))

def get_outcome(market, key):
    if not market: return None
    for o in market.get('outcomes', []):
        if o.get('key') == key:
            return o
    return None

summary = []
for m in d['matches']:
    mk = m.get('markets', {})
    had = mk.get('had'); hhad = mk.get('hhad')
    crs = mk.get('crs'); ttg = mk.get('ttg'); hafu = mk.get('hafu')

    # HAD
    hh = get_outcome(had,'home'); dr = get_outcome(had,'draw'); aw = get_outcome(had,'away')
    # HHAD
    hh_h = get_outcome(hhad,'home'); hh_d = get_outcome(hhad,'draw'); hh_a = get_outcome(hhad,'away')
    # 让球数
    handicap = hhad.get('goalLine') if hhad else None

    # CRS 比分赔率（取TOP）
    crs_list = []
    if crs:
        for o in crs.get('outcomes', []):
            crs_list.append((o.get('labelZh'), o.get('odds'), o.get('noVigProb',0)))
        crs_list.sort(key=lambda x: -(x[2] or 0))

    # TTG 总进球
    ttg_list = []
    if ttg:
        for o in ttg.get('outcomes', []):
            ttg_list.append((o.get('labelZh'), o.get('odds'), o.get('noVigProb',0)))
        ttg_list.sort(key=lambda x: -(x[2] or 0))

    # HAFU 半全场
    hafu_list = []
    if hafu:
        for o in hafu.get('outcomes', []):
            hafu_list.append((o.get('labelZh'), o.get('odds'), o.get('noVigProb',0)))
        hafu_list.sort(key=lambda x: -(x[2] or 0))

    row = {
        'num': m['matchNumStr'],
        'league': m['league']['abbName'],
        'time': f"{m['matchDate']} {m['matchTime']}",
        'home': m['home']['abbName'], 'home_rank': m['home'].get('rank',''),
        'away': m['away']['abbName'], 'away_rank': m['away'].get('rank',''),
        'had': {'h':hh and hh['odds'], 'd':dr and dr['odds'], 'a':aw and aw['odds'],
                'p_h':hh and hh.get('noVigProb'), 'p_d':dr and dr.get('noVigProb'), 'p_a':aw and aw.get('noVigProb'),
                'returnRate': had and had.get('returnRate')},
        'hhad': {'goal': handicap,
                 'h':hh_h and hh_h['odds'], 'd':hh_d and hh_d['odds'], 'a':hh_a and hh_a['odds'],
                 'p_h':hh_h and hh_h.get('noVigProb'), 'p_d':hh_d and hh_d.get('noVigProb'), 'p_a':hh_a and hh_a.get('noVigProb')},
        'crs_top': crs_list[:8],
        'ttg_top': ttg_list,
        'hafu_top': hafu_list,
    }
    summary.append(row)

with open('reports/data/20261015_odds_summary.json','w',encoding='utf-8') as f:
    json.dump(summary,f,ensure_ascii=False,indent=2)

# 打印紧凑摘要
for r in summary:
    print(f"\n=== {r['num']} {r['league']} {r['time']} ===")
    print(f"  {r['home']}{r['home_rank']} vs {r['away']}{r['away_rank']}")
    h=r['had']
    def fp(v): return f"{v:.1%}" if v is not None else "  -  "
    print(f"  HAD: 主{h['h']}({fp(h['p_h'])}) 平{h['d']}({fp(h['p_d'])}) 客{h['a']}({fp(h['p_a'])}) 返还率{fp(h['returnRate'])}")
    hh=r['hhad']
    print(f"  HHAD(让{hh['goal']}): 胜{hh['h']}({fp(hh['p_h'])}) 平{hh['d']}({fp(hh['p_d'])}) 负{hh['a']}({fp(hh['p_a'])})")
    print(f"  CRS TOP5: " + ", ".join([f"{x[0]}({x[1]})" for x in r['crs_top'][:5]]))
    print(f"  TTG: " + ", ".join([f"{x[0]}球({x[1]})" for x in r['ttg_top'][:5]]))
    print(f"  HAFU TOP4: " + ", ".join([f"{x[0]}({x[1]})" for x in r['hafu_top'][:4]]))
