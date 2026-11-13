# -*- coding: utf-8 -*-
"""登记 2026-10-17 规则67试用台账（待赛果）"""
import json

res = {x['num']: x for x in json.load(open('reports/data/20261017_model_output.json', encoding='utf-8'))}
nums = ['周六002', '周六003', '周六021', '周六022', '周六010']
rows = []
recs = []
for n in nums:
    r = res[n]
    band = ' > '.join(f"{a}-{b}({p*100:.1f}%)" for a, b, p in r['band'][:3])
    kd = '平' if r['k_dist'] == 0 else ('主胜' if r['k_dist'] > 0 else '客胜')
    had = {'home': '主胜', 'draw': '平', 'away': '客胜'}[r['primary']]
    diff = '一致' if r['k_consistent'] else '**分歧**'
    rows.append(f"| {n[-3:]} | {r['home']} vs {r['away']} | {r['league']} | {r['k_dist']:+d}（{r['k_dist_prob']*100:.1f}%） | {r['k_rec']:+d}（{r['k_rec_prob']*100:.1f}%） | {band} | {r['ttg_top'][0][0]}球/{r['ttg_top'][1][0]}球 | {kd} | {had} | {diff} | 待赛果 | — |")
    recs.append({
        'date': '2026-10-17', 'caliber': '双轨制', 'match_num': n[-3:],
        'match': f"{r['home']}vs{r['away']}", 'league': r['league'],
        'k_dist': {'value': r['k_dist'], 'pct': r['k_dist_prob']},
        'k_rec': {'value': r['k_rec'], 'pct': r['k_rec_prob']},
        'band_top3': [f'{a}-{b}' for a, b, _ in r['band'][:3]],
        'ttg': f"{r['ttg_top'][0][0]}/{r['ttg_top'][1][0]}",
        'k_dist_dir': kd, 'had_dir': had, 'divergent': not r['k_consistent'],
        'pred_score': {'002': '2:1', '003': '2:1', '021': '2:1', '022': '1:2', '010': '1:3'}[n[-3:]],
        'actual': '待赛果', 'verdict': 'pending'
    })

block = """
## 2026-10-17（周六）登记（待赛果）

| 编号 | 对阵 | 联赛 | 分布众数 k_dist | 推荐众数 k_rec | 带内候选TOP3 | 首推总进球档 | k_dist方向 | HAD首推方向 | 是否分歧 | 实际比分 | 判定 |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---:|:---|:---|
""" + '\n'.join(rows) + """
>
> 本轮用于**正向流程**的比分场次：002+021（稳健比分串）、002+003（连续编号比分串①）、021+022（连续编号比分串②）、022（单挑①）、010（单挑②）；去重后计入 **5 场**（002/003/010/021/022）。
> 004/020/006等「分布-方向分歧」场次已按规则67剔出全部正向比分子分类（仅保留搏冷/娱乐用途），不登记入本台账。
> **比分串结构与比分**：稳健=002 2-1 + 021 2-1；连续①=002 2-1 + 003 2-1；连续②=021 2-1 + 022 1-2；单挑①=022 1-3；单挑②=010 1-3。
> **状态**：5场全部 pending，待赛后回填实际比分与判定。
"""

with open('memory/trials/score_parlay_trial.md', 'a', encoding='utf-8') as f:
    f.write(block)

p = 'memory/trials/score_parlay_trial.json'
d = json.load(open(p, encoding='utf-8'))
d['updated'] = '2026-10-17'
d['cumulative']['pending_matches'] = 5
d['cumulative']['pending_note'] = '2026-10-17周六新增5场（002/003/010/021/022）待赛果回填；004/020/006等分歧场不登记'
d['records'].extend(recs)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('trial updated; pending', d['cumulative']['pending_matches'], 'records', len(d['records']))
