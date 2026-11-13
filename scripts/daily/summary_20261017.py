# -*- coding: utf-8 -*-
"""汇总模型输出，供报告撰写使用"""
import json

res = json.load(open('reports/data/20261017_model_output.json', encoding='utf-8'))
lines = []
for r in res:
    score_by_key = {f'{k}': v for k, v in r['odds_crs'].items()}
    def co(a, b):
        return r['odds_crs'].get(f'{a}:{b}')
    band = [(f'{a}-{b}', round(p*100,1), co(a,b)) for a,b,p in r['band'][:5]]
    top = [(f'{a}-{b}', round(p*100,1), co(a,b)) for a,b,p in r['top_scores'][:6]]
    ttg = [(k, round(p*100,1), r['odds_ttg'].get(str(k))) for k,p in r['ttg_top'][:4]]
    hafu = [(k, round(p*100,1), r['odds_hafu'].get({'胜胜':'HH','胜平':'HD','胜负':'HA','平胜':'DH','平平':'DD','平负':'DA','负胜':'AH','负平':'AD','负负':'AA'}[k])) for k,p in r['htft'][:4]]
    ht = [(f'{a}-{b}', round(p*100,1)) for a,b,p in r['ht_scores'][:3]]
    lines.append(
        f"{r['num']} {r['home']} vs {r['away']} | {r['league']} | 单关{'是' if r['is_single'] else '否'}\n"
        f"  λ {r['lambda_home']}/{r['lambda_away']} 总{r['lambda_total']} | 融合 主{r['fused']['home']*100:.1f} 平{r['fused']['draw']*100:.1f} 客{r['fused']['away']*100:.1f}\n"
        f"  首选{r['primary']} {r['primary_prob']*100:.1f}% / 次选{r['secondary']} {r['secondary_prob']*100:.1f}%\n"
        f"  让球({r['hhad_line']}) 模型 主{r['hhad_model']['home']*100:.1f}/平{r['hhad_model']['draw']*100:.1f}/客{r['hhad_model']['away']*100:.1f} "
        f"赔率 {r['odds_hhad']}\n"
        f"  k_dist {r['k_dist']}({r['k_dist_prob']*100:.1f}%) k_rec {r['k_rec']}({r['k_rec_prob']*100:.1f}%) {'一致' if r['k_consistent'] else '分歧'}\n"
        f"  带内 {band}\n  全矩阵TOP {top}\n  TTG {ttg}\n  HAFU {hafu}\n  半场 {ht}\n"
    )
print('\n'.join(lines))
