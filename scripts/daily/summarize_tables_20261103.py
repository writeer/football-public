# -*- coding: utf-8 -*-
"""汇总 tables_20261103.json → 文本摘要（供报告与模型输入）"""
import json, io

d = json.load(io.open('reports/data/tables_20261103.json', encoding='utf-8'))
TARGETS = {
 'australia': ['Newcastle'],
 'japan1': ['Kashiwa'],
 'china': ['Shanghai Port', 'Beijing Guoan'],
 'thai1': ['Port'],
 'korea1': ['Daejeon'],
 'turkey1': ['Galatasaray'],
 'germany1': ['Stuttgart', 'Bayern'],
 'austria1': ['LASK'],
 'slovakia1': ['Slovan'],
 'holland1': ['Feyenoord'],
 'italy1': ['Inter', 'Roma'],
 'premier': ['Manchester United', 'Man United', 'Aston Villa'],
 'spain1': ['Atletico', 'Barcelona', 'Villarreal'],
 'france1': ['Paris Saint', 'PSG', 'Lille'],
 'norway': ['Bodo', 'Bodø'],
}
lines = []
for lg, r in d.items():
    tab = r.get('table') or []
    if not tab:
        lines.append(f"{lg} EMPTY"); continue
    tot_p = sum(t['played'] for t in tab)
    avg_gf = sum(t['goals_for'] for t in tab)/tot_p
    avg_ga = sum(t['goals_against'] for t in tab)/tot_p
    lines.append(f"=== {lg} | season {r.get('season')} | teams {len(tab)} | 联赛场均进 {avg_gf:.2f} 失 {avg_ga:.2f}")
    for t in tab:
        nm = t['team']
        if lg == 'thai1' or any(k.lower() in nm.lower() for k in TARGETS.get(lg, [])):
            lines.append(f"  {t['position']:>2} {nm:<26} P{t['played']:>2} {t['won']}-{t['drawn']}-{t['lost']} pts{t['points']:>3} "
                  f"GF{t['goals_for']:>3}/GA{t['goals_against']:>3} 场进{t['avg_goals_scored']:.2f}/场失{t['avg_goals_conceded']:.2f} "
                  f"主进{t.get('home_goals_avg')}/客进{t.get('away_goals_avg')} 近5:{t.get('last_5_form')} 大2.5:{t.get('over_25_percentage')}%")
alltxt = "\n".join(lines)
io.open('reports/data/tables_summary_20261103.txt','w',encoding='utf-8').write(alltxt)
print(alltxt)
