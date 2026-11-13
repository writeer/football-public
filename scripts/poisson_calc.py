import math
import json

def poisson(k, lam):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def dixon_coles_adj(i, j, lam_h, lam_a):
    """Dixon-Coles low-score adjustment (rho param)"""
    rho = 0.13
    if i == 0 and j == 0:
        return 1 - (rho * lam_h)
    elif i == 0 and j == 1:
        return 1 + (rho * lam_h)
    elif i == 1 and j == 0:
        return 1 + (rho * lam_a)
    elif i == 1 and j == 1:
        return 1 - (rho * lam_a)
    return 1.0

def calc_match(lh, la, max_goals=8):
    matrix = {}
    total = 0
    for i in range(max_goals+1):
        for j in range(max_goals+1):
            p = poisson(i, lh) * poisson(j, la) * dixon_coles_adj(i, j, lh, la)
            matrix[(i,j)] = p
            total += p
    # normalize
    for k in matrix:
        matrix[k] /= total
    # HAD
    had_h = sum(p for (i,j),p in matrix.items() if i>j)
    had_d = sum(p for (i,j),p in matrix.items() if i==j)
    had_a = sum(p for (i,j),p in matrix.items() if i<j)
    # TTG
    ttg = {}
    for g in range(max_goals+1):
        ttg[g] = sum(p for (i,j),p in matrix.items() if i+j==g)
    # CRS top8
    crs_sorted = sorted(matrix.items(), key=lambda x: -x[1])[:8]
    # HTFT (half: lambda*0.45)
    hlh, hla = lh*0.45, la*0.45
    hmatrix = {}
    htotal = 0
    for i in range(5):
        for j in range(5):
            p = poisson(i, hlh) * poisson(j, hla) * dixon_coles_adj(i, j, hlh, hla)
            hmatrix[(i,j)] = p
            htotal += p
    for k in hmatrix:
        hmatrix[k] /= htotal
    # half result
    hr_h = sum(p for (i,j),p in hmatrix.items() if i>j)
    hr_d = sum(p for (i,j),p in hmatrix.items() if i==j)
    hr_a = sum(p for (i,j),p in hmatrix.items() if i<j)
    # hafu combos (half->full)
    hafu = {}
    for (hi,hj),hp in hmatrix.items():
        hres = 'h' if hi>hj else ('d' if hi==hj else 'a')
        for (fi,fj),fp in matrix.items():
            fres = 'h' if fi>fj else ('d' if fi==fj else 'a')
            key = hres+fres
            hafu[key] = hafu.get(key,0) + hp*fp
    hafu_sorted = sorted(hafu.items(), key=lambda x:-x[1])[:6]
    # half score top3
    hcrs_sorted = sorted(hmatrix.items(), key=lambda x:-x[1])[:3]
    return {
        'had': (round(had_h*100,1), round(had_d*100,1), round(had_a*100,1)),
        'ttg': {g: round(ttg[g]*100,1) for g in range(7)},
        'ttg_top': sorted(ttg.items(), key=lambda x:-x[1])[:4],
        'crs_top': [(f"{i}-{j}", round(p*100,1)) for (i,j),p in crs_sorted],
        'hafu_top': [(k, round(v*100,1)) for k,v in hafu_sorted],
        'hcrs_top': [(f"{i}-{j}", round(p*100,1)) for (i,j),p in hcrs_sorted],
        'half_res': (round(hr_h*100,1), round(hr_d*100,1), round(hr_a*100,1)),
    }

# lambda parameters set by 总控 based on injury/league/fixture/form
matches = {
    '001_意甲_博洛尼亚vs拉齐奥': (1.82, 1.18),   # 博洛尼亚主场+拉齐奥7人后防残阵×1.15, 拉齐奥进攻端伤×0.85, 新赛季+0.15
    '002_沙职_新未来SCvs胡巴卡德': (0.90, 1.70),  # 信息缺失,客队大热,保守
    '003_瑞超_马尔默vs佐加顿斯': (1.40, 1.25),    # 同分势均力敌,双方残阵
    '004_西甲_奥萨苏纳vs莱万特': (1.35, 0.85),    # 奥萨苏纳主场+莱万特残阵惨败
    '005_沙职_吉达联合vs拉斯决心': (2.20, 0.60),  # 身价碾压10x+交锋全胜+对手惨败,大球
    '006_意甲_罗马vs佛罗伦萨': (1.50, 1.10),      # 罗马主场+交锋碾压,新赛季+0.15
    '007_法乙_兰斯vs阿纳西': (1.35, 1.00),        # 法乙主场加强,阿纳西状态好但客场
    '008_英超_富勒姆vs切尔西': (1.40, 1.30),      # 富勒姆主场爆冷Big6+切尔西4人残阵,新赛季
    '009_葡超_吉维森特vs卡萨皮亚': (1.35, 0.70),  # 吉维森特主场+卡萨皮亚2连败惨败,小球
    '010_西甲_马拉加vs拉科': (1.10, 1.00),        # 双方保级/升班马,小球闷战
    '011_巴甲_博塔弗戈vs巴竞技': (1.20, 1.15),    # 双方残阵,巴甲平局高
}

results = {}
for name, (lh, la) in matches.items():
    r = calc_match(lh, la)
    results[name] = {'lh': lh, 'la': la, **r}

for name, r in results.items():
    print(f"\n===== {name} (lh={r['lh']}, la={r['la']}) =====")
    print(f"  HAD: 主{r['had'][0]}% / 平{r['had'][1]}% / 客{r['had'][2]}%")
    tt = ', '.join(f"{g}球:{p*100:.1f}%" for g,p in r['ttg_top'])
    print(f"  TTG top: {tt}")
    print(f"  CRS top5: {r['crs_top'][:5]}")
    print(f"  HAFU top6: {r['hafu_top']}")
    print(f"  HalfCRS top3: {r['hcrs_top']}")
    print(f"  HalfRes: 主{r['half_res'][0]}% / 平{r['half_res'][1]}% / 客{r['half_res'][2]}%")

# save to json
with open(r'e:\VibeCoding\football\reports\data\260824_poisson_matrix.json', 'w', encoding='utf-8') as f:
    json.dump({k: {kk: (vv if not isinstance(vv, dict) else {str(k2):v2 for k2,v2 in vv.items()}) for kk,vv in v.items()} for k,v in results.items()}, f, ensure_ascii=False, indent=2)
print("\nSaved to reports/data/260824_poisson_matrix.json")
