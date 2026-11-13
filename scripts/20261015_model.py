# -*- coding: utf-8 -*-
"""13场DC模型计算：从HAD概率+TTG赔率反推lambda，生成比分矩阵与净胜球分布"""
import json, io, sys, math
from itertools import product
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 每场: (编号, 主p, 平p, 客p, TTG各球数概率(从赔率反推), 让球goalLine, 备注修正)
# TTG赔率→概率：取TTG outcomes的noVigProb
odds = json.load(open('reports/data/20261015_odds_summary.json', encoding='utf-8'))

def poisson(k, lam):
    return math.exp(-lam) * lam**k / math.factorial(k)

def dc_matrix(lh, la, maxg=10):
    """Dixon-Coles简化（用独立Poisson近似，rho修正暂忽略）"""
    M = [[poisson(i, lh)*poisson(j, la) for j in range(maxg+1)] for i in range(maxg+1)]
    s = sum(sum(r) for r in M)
    return [[v/s for v in r] for r in M]

def infer_lambdas(p_h, p_d, p_a, ttg_probs):
    """用网格搜索找lambda使得DC的主/平/客概率和TTG分布最接近目标"""
    # 目标总进球lambda：从TTG加权均值估算
    # ttg_probs: {0:p, 1:p, ..., 7:p}
    mean_goals = sum(k*p for k,p in ttg_probs.items())
    best = None
    for lh10 in range(5, 40):
        for la10 in range(3, 35):
            lh = lh10/10; la = la10/10
            M = dc_matrix(lh, la)
            ph = sum(M[i][j] for i in range(11) for j in range(11) if i>j)
            pd = sum(M[i][i] for i in range(11))
            pa = sum(M[i][j] for i in range(11) for j in range(11) if i<j)
            # TTG
            ttg_pred = {}
            for k in range(8):
                ttg_pred[k] = sum(M[i][j] for i in range(11) for j in range(11) if i+j==k)
            err = (ph-p_h)**2 + (pd-p_d)**2 + (pa-p_a)**2
            for k in range(7):
                err += 2.0*(ttg_pred.get(k,0)-ttg_probs.get(k,0))**2
            # mean goals penalty
            tg_mean = sum(k*ttg_pred.get(k,0) for k in range(11))
            err += 0.5*(tg_mean-mean_goals)**2
            if best is None or err < best[0]:
                best = (err, lh, la, ph, pd, pa, ttg_pred)
    return best

# 单关修正（规则63）：001/008平局上修+7%
single_draw = {'周四001': 0.07, '周四008': 0.07}

# 法甲非PSG平局上修（规则69）：**仅适用于法甲联赛（Ligue 1）场次**
# ⚠️ 跨联赛赛事（欧战/杯赛/友谊赛）不适用——法甲"平局多"是法甲联赛内部球队同质化的产物，
#    跨国对战（欧罗巴/欧冠等）不存在该前提（用户 2026-10-15 纠正）。
# 本场001里昂、010马赛均为欧罗巴联赛阶段 → 不上修。
ligue1_draw = {}

results = []
for r in odds:
    num = r['num']
    h = r['had']
    if h['p_h'] is None:
        # 011 HAD未开，从HHAD反推：HHAD让-2，让胜41.2%/让平22.7%/让负36.1%
        # 伯恩茅斯让2球，从CRS 2:0/3:0/1:0/4:0反推：主胜大热
        p_h, p_d, p_a = 0.62, 0.18, 0.20
    else:
        p_h, p_d, p_a = h['p_h'], h['p_d'], h['p_a']

    # 应用修正
    draw_boost = single_draw.get(num, 0) + ligue1_draw.get(num, 0)
    p_d_adj = p_d + draw_boost
    # 从主客按比例扣减
    rem = p_h + p_a
    p_h_adj = p_h - draw_boost * (p_h/rem)
    p_a_adj = p_a - draw_boost * (p_a/rem)
    total = p_h_adj + p_d_adj + p_a_adj
    p_h_adj, p_d_adj, p_a_adj = p_h_adj/total, p_d_adj/total, p_a_adj/total

    # TTG概率
    ttg_probs = {}
    for lbl, odd, p in r['ttg_top']:
        # lbl like "2球" or "7+球"
        if '+' in lbl:
            k = 7
        else:
            k = int(lbl.replace('球',''))
        ttg_probs[k] = p or 0.2

    err, lh, la, ph, pd, pa, ttg_pred = infer_lambdas(p_h_adj, p_d_adj, p_a_adj, ttg_probs)
    M = dc_matrix(lh, la)

    # 比分TOP
    scores = []
    for i in range(8):
        for j in range(8):
            scores.append((f"{i}-{j}", M[i][j], i-j))
    scores.sort(key=lambda x: -x[1])

    # 净胜球分布 k = i-j
    kdist = {}
    for i in range(11):
        for j in range(11):
            k = i-j
            kdist[k] = kdist.get(k,0) + M[i][j]
    k_dist = max(kdist.items(), key=lambda x: x[1])

    # k_rec: 首推方向内众数
    if p_h_adj >= p_d_adj and p_h_adj >= p_a_adj:
        direction = 'H'
        cand = {k:v for k,v in kdist.items() if k>=1}
    elif p_a_adj >= p_d_adj:
        direction = 'A'
        cand = {k:v for k,v in kdist.items() if k<=-1}
    else:
        direction = 'D'
        cand = {0: kdist.get(0,0)}
    k_rec = max(cand.items(), key=lambda x: x[1])

    # TTG
    ttg_final = sorted(ttg_pred.items(), key=lambda x: -x[1])

    # HAFU: 简化——用半场lambda=全场*0.44，独立Poisson
    hh_lh, hh_la = lh*0.44, la*0.44
    Mh = dc_matrix(hh_lh, hh_la)
    hh_h = sum(Mh[i][j] for i in range(8) for j in range(8) if i>j)
    hh_d = sum(Mh[i][i] for i in range(8))
    hh_a = sum(Mh[i][j] for i in range(8) for j in range(8) if i<j)
    # 半全场9宫格
    hafu = {}
    for hs_name, hs_p in [('胜',hh_h),('平',hh_d),('负',hh_a)]:
        for fs_name, fs_p in [('胜',ph),('平',pd),('负',pa)]:
            hafu[hs_name+fs_name] = hs_p * fs_p
    hafu_sorted = sorted(hafu.items(), key=lambda x: -x[1])

    # 半场比分TOP
    ht_scores = []
    for i in range(5):
        for j in range(5):
            ht_scores.append((f"{i}-{j}", Mh[i][j]))
    ht_scores.sort(key=lambda x: -x[1])

    # 让球判定（规则52a：无条件净胜球众数）
    gl = r['hhad']['goal'] or 0
    # 调整后净胜 = k + gl  (主让gl为负)
    adj_dist = {}
    for k, v in kdist.items():
        adj = k + gl
        if adj > 0: r_dir = '让胜'
        elif adj == 0: r_dir = '让平'
        else: r_dir = '让负'
        adj_dist[r_dir] = adj_dist.get(r_dir, 0) + v

    res = {
        'num': num, 'home': r['home'], 'away': r['away'], 'league': r['league'],
        'lh': lh, 'la': la, 'lt': lh+la,
        'p_h': p_h_adj, 'p_d': p_d_adj, 'p_a': p_a_adj,
        'direction': direction,
        'crs_top': scores[:8],
        'k_dist': k_dist, 'k_rec': k_rec,
        'ttg': ttg_final[:7],
        'hafu': hafu_sorted[:6],
        'ht_scores': ht_scores[:5],
        'hhad_dist': adj_dist,
        'goal_line': gl,
    }
    results.append(res)

with open('reports/data/20261015_model.json','w',encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)

# 打印
for r in results:
    print(f"\n=== {r['num']} {r['home']} vs {r['away']} ({r['league']}) ===")
    print(f"  λ主={r['lh']:.2f} λ客={r['la']:.2f} λ总={r['lt']:.2f}")
    d = r['direction']
    dname = {'H':'主胜','D':'平','A':'客胜'}[d]
    print(f"  融合: 主{r['p_h']:.1%} 平{r['p_d']:.1%} 客{r['p_a']:.1%} → 首选{dname}")
    print(f"  CRS TOP5: " + ", ".join([f"{x[0]}({x[1]:.1%})" for x in r['crs_top'][:5]]))
    kd = r['k_dist']; kr = r['k_rec']
    mark = '一致' if (kd[0]>0 and d=='H') or (kd[0]<0 and d=='A') or (kd[0]==0 and d=='D') else '分歧'
    print(f"  净胜球: k_dist={kd[0]}({kd[1]:.1%}) | k_rec={kr[0]}({kr[1]:.1%}) | {mark}")
    print(f"  TTG: " + ", ".join([f"{x[0]}球({x[1]:.1%})" for x in r['ttg'][:4]]))
    print(f"  HAFU TOP3: " + ", ".join([f"{x[0]}({x[1]:.1%})" for x in r['hafu'][:3]]))
    print(f"  半场比分: " + ", ".join([f"{x[0]}({x[1]:.1%})" for x in r['ht_scores'][:3]]))
    hd = r['hhad_dist']
    print(f"  让({r['goal_line']}): " + ", ".join([f"{k}{v:.1%}" for k,v in sorted(hd.items(), key=lambda x:-x[1])]))
