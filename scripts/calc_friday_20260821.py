# -*- coding: utf-8 -*-
"""周五2026-08-21模型计算脚本 — DC比分矩阵/TTG分布/半全场/让球概率"""
import sys, json, io
sys.path.insert(0, r"E:\VibeCoding\football")
from lottery_agent.models import DixonColesModel, SkellamModel, HTFTModel

dc = DixonColesModel()
sk = SkellamModel()
ht = HTFTModel()

def calc(lh, la):
    """输入lambda，输出6维度"""
    mat = dc.compute_matrix(lh, la)
    # 比分TOP10
    scores = []
    for i in range(dc.max_goals):
        for j in range(dc.max_goals):
            scores.append((i, j, mat[i, j]))
    scores.sort(key=lambda x: -x[2])
    top_scores = [{"score": f"{i}-{j}", "prob": round(p*100, 1)} for i, j, p in scores[:10]]
    # 方向概率（DC）
    dc_out = dc.outcome_probs(lh, la)
    sk_out = sk.outcome_probs(lh, la)
    # 融合（DC 0.7 + Skellam 0.3 权重示意）
    fused = {k: dc_out[k]*0.7 + sk_out[k]*0.3 for k in ['home', 'draw', 'away']}
    # TTG分布
    ttg = {g: 0.0 for g in range(8)}
    for i in range(dc.max_goals):
        for j in range(dc.max_goals):
            g = i + j
            if g < 8:
                ttg[g] += mat[i, j]
            else:
                ttg[7] += mat[i, j]
    ttg_top = sorted(ttg.items(), key=lambda x: -x[1])[:5]
    ttg_list = [{"goals": g if g < 7 else "7+", "prob": round(p*100, 1)} for g, p in ttg_top]
    # 半全场
    htft = ht.predict(lh, la)
    htft_list = [{"htft": h['htft'], "prob": round(h['probability']*100, 1)} for h in htft[:5]]
    # 半场比分
    lh_ht, la_ht = lh*0.42, la*0.42
    mat_ht = dc.compute_matrix(lh_ht, la_ht)
    ht_scores = []
    for i in range(dc.max_goals):
        for j in range(dc.max_goals):
            ht_scores.append((i, j, mat_ht[i, j]))
    ht_scores.sort(key=lambda x: -x[2])
    ht_top = [{"score": f"{i}-{j}", "prob": round(p*100, 1)} for i, j, p in ht_scores[:3]]
    # 让球概率（-1球）
    lh_m1, la_m1 = lh - 1, la
    hh = dc.outcome_probs(lh_m1, la)  # 让-1后主胜=净胜2+；平=净胜1；客胜=平或负
    return {
        "lambda": {"home": lh, "away": la},
        "dc": {k: round(v*100, 1) for k, v in dc_out.items()},
        "skellam": {k: round(v*100, 1) for k, v in sk_out.items()},
        "fused": {k: round(v*100, 1) for k, v in fused.items()},
        "score_top10": top_scores,
        "ttg_top5": ttg_list,
        "htft_top5": htft_list,
        "ht_score_top3": ht_top,
        "hcap_m1": {
            "home_win": round(hh['home']*100, 1),
            "draw": round(hh['draw']*100, 1),
            "away_win": round(hh['away']*100, 1)
        }
    }

if __name__ == "__main__":
    # 用法：python calc_friday_20260821.py <lh> <la> [label] [line]
    lh = float(sys.argv[1])
    la = float(sys.argv[2])
    label = sys.argv[3] if len(sys.argv) > 3 else ""
    line = float(sys.argv[4]) if len(sys.argv) > 4 else -1
    res = calc(lh, la)
    # 让球概率（line为负数=主让；正数=主受让）——直接用比分矩阵精确计算：主队实际进球+line vs 客队进球
    mat_full = dc.compute_matrix(lh, la)
    hw = dw = aw = 0.0
    for i in range(dc.max_goals):
        for j in range(dc.max_goals):
            diff = (i + line) - j
            if diff > 0:
                hw += mat_full[i, j]
            elif diff == 0:
                dw += mat_full[i, j]
            else:
                aw += mat_full[i, j]
    res["hcap"] = {
        "line": line,
        "home_win": round(hw*100, 1),
        "draw": round(dw*100, 1),
        "away_win": round(aw*100, 1)
    }
    out = {"label": label, **res}
    print(json.dumps(out, ensure_ascii=False, indent=1))
