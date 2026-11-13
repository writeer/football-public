# -*- coding: utf-8 -*-
"""
2026-10-07 周三竞彩6场比赛分析
按照AGENTS.md 10步管道执行
002开单关 → 规则63平局上修
"""

import sys
sys.path.insert(0, r'e:\VibeCoding\football')

import json
import numpy as np
from scipy import stats as sp_stats
from lottery_agent.models import (
    DixonColesModel, NegativeBinomialModel, ZIPModel,
    SkellamModel, MonteCarloSimulator, OddsCalibrator,
    HTFTModel
)
from lottery_agent.config import LEAGUE_PROFILES

# ============================================================
# 周三6场比赛数据（比赛编号日期：261007）
# ============================================================
matches = [
    {
        "match_num": "周三001",
        "league": "芬超",
        "home_team": "赫尔辛基火花",
        "away_team": "国际图尔库",
        "home_rank": "芬超第4",
        "away_rank": "芬超第2",
        "match_time": "2026-10-08 00:00",
        "odds": {"home": 3.90, "draw": 3.70, "away": 1.66},
        "hhad_odds": {"home": 1.94, "draw": 3.37, "away": 3.15, "goal_line": 1},
        "is_single": False,
        "stadium_status": "正常",
        "note": "主队受让1球，客队国际图尔库排名更高",
    },
    {
        "match_num": "周三002",
        "league": "巴甲",
        "home_team": "巴西国际",
        "away_team": "科林蒂安",
        "home_rank": "巴甲第18",
        "away_rank": "巴甲第14",
        "match_time": "2026-10-08 06:30",
        "odds": {"home": 2.13, "draw": 2.87, "away": 3.21},
        "hhad_odds": {"home": 4.90, "draw": 3.57, "away": 1.55, "goal_line": -1},
        "is_single": True,  # 用户告知：002开单关
        "stadium_status": "正常",
        "note": "巴西国际排名低但主场让1球，主场优势明显",
    },
    {
        "match_num": "周三003",
        "league": "巴甲",
        "home_team": "瑞模贝雷",
        "away_team": "格雷米奥",
        "home_rank": "巴甲第19",
        "away_rank": "巴甲第17",
        "match_time": "2026-10-08 06:30",
        "odds": {"home": 2.03, "draw": 3.13, "away": 3.15},
        "hhad_odds": {"home": 4.42, "draw": 3.65, "away": 1.59, "goal_line": -1},
        "is_single": False,
        "stadium_status": "正常",
        "note": "降级区对决，瑞模贝雷排名更低但主场让球",
    },
    {
        "match_num": "周三004",
        "league": "巴甲",
        "home_team": "布拉干蒂诺RB",
        "away_team": "米拉索尔",
        "home_rank": "巴甲第11",
        "away_rank": "巴甲第15",
        "match_time": "2026-10-08 06:30",
        "odds": {"home": 1.62, "draw": 3.60, "away": 4.28},
        "hhad_odds": {"home": 3.08, "draw": 3.25, "away": 2.01, "goal_line": -1},
        "is_single": False,
        "stadium_status": "正常",
        "note": "布拉干蒂诺RB主场优势明显",
    },
    {
        "match_num": "周三005",
        "league": "巴甲",
        "home_team": "维多利亚",
        "away_team": "沙佩科恩斯",
        "home_rank": "巴甲第13",
        "away_rank": "巴甲第20",
        "match_time": "2026-10-08 07:00",
        "odds": {"home": 1.43, "draw": 4.00, "away": 5.55},
        "hhad_odds": {"home": 2.64, "draw": 3.08, "away": 2.35, "goal_line": -1},
        "is_single": False,
        "stadium_status": "正常",
        "note": "维多利亚主场迎战副班长沙佩科恩斯",
    },
    {
        "match_num": "周三006",
        "league": "巴甲",
        "home_team": "博塔弗戈",
        "away_team": "瓦斯科达伽马",
        "home_rank": "巴甲第12",
        "away_rank": "巴甲第16",
        "match_time": "2026-10-08 07:30",
        "odds": {"home": 2.77, "draw": 3.35, "away": 2.13},
        "hhad_odds": {"home": 1.53, "draw": 3.95, "away": 4.50, "goal_line": 1},
        "is_single": False,
        "stadium_status": "正常",
        "note": "里约德比，博塔弗戈主场受让1球",
    },
]


def estimate_lambdas(market_h, market_d, market_a, league_avg, ha_factor):
    """从市场概率和联赛场均进球估算lambda_h, lambda_a"""
    league_draw_rate = 0.28
    draw_diff = market_d - league_draw_rate
    total_goals = league_avg * (1.0 - draw_diff * 1.2)
    
    strength_ratio = (market_h / market_a) ** 0.6
    strength_ratio *= ha_factor ** 0.4
    
    lambda_h = total_goals * strength_ratio / (1 + strength_ratio)
    lambda_a = total_goals / (1 + strength_ratio)
    
    lambda_h = max(0.5, min(3.0, lambda_h))
    lambda_a = max(0.4, min(2.8, lambda_a))
    
    return lambda_h, lambda_a


def handicap_skellam(lambda_h, lambda_a, handicap):
    """计算让球胜平负概率"""
    threshold = -handicap
    hw = sp_stats.skellam.sf(threshold, lambda_h, lambda_a)
    d = sp_stats.skellam.pmf(threshold, lambda_h, lambda_a)
    aw = sp_stats.skellam.cdf(threshold - 1, lambda_h, lambda_a)
    return {"home": hw, "draw": d, "away": aw}


def analyze_match(match):
    """单场比赛完整分析"""
    league = match["league"]
    profile = LEAGUE_PROFILES.get(league, LEAGUE_PROFILES["default"])
    
    dc = DixonColesModel()
    nb = NegativeBinomialModel()
    zip_model = ZIPModel()
    skellam = SkellamModel()
    mc = MonteCarloSimulator()
    htft = HTFTModel(dc)
    
    odds_h = match["odds"]["home"]
    odds_d = match["odds"]["draw"]
    odds_a = match["odds"]["away"]
    
    # 去水概率（市场隐含）
    inv_h = 1.0 / odds_h
    inv_d = 1.0 / odds_d
    inv_a = 1.0 / odds_a
    total_inv = inv_h + inv_d + inv_a
    market_h = inv_h / total_inv
    market_d = inv_d / total_inv
    market_a = inv_a / total_inv
    
    # Shin模型校准
    calibrator = OddsCalibrator(odds_h, odds_d, odds_a)
    shin_result = calibrator.shin()
    shin_probs = [shin_result['home'], shin_result['draw'], shin_result['away']]
    
    # 估算lambda
    league_avg = profile["avg_goals"]
    ha_factor = profile["home_advantage"]
    lambda_h, lambda_a = estimate_lambdas(market_h, market_d, market_a, league_avg, ha_factor)
    
    # 模型计算
    dc_probs = dc.outcome_probs(lambda_h, lambda_a)
    nb_probs = nb.outcome_probs(lambda_h, lambda_a)
    zip_probs = zip_model.outcome_probs(lambda_h, lambda_a)
    mc_result = mc.simulate(lambda_h, lambda_a)
    mc_probs = {"home": mc_result["home_win"], "draw": mc_result["draw"], "away": mc_result["away_win"]}
    
    # DC比分矩阵
    dc_matrix = dc.compute_matrix(lambda_h, lambda_a)
    
    # 让球概率
    hhad_line = match["hhad_odds"]["goal_line"]
    hhad_probs = handicap_skellam(lambda_h, lambda_a, hhad_line)
    
    # 总进球分布
    total_goals_dist = {}
    for t in range(8):
        p = sum(dc_matrix[i, t-i] for i in range(max(0, t-7), min(t+1, 8)) if t-i >= 0 and t-i < 8)
        total_goals_dist[t] = p
    
    # 半全场
    htft_result = htft.predict(lambda_h, lambda_a)
    htft_probs = {item["htft"]: item["probability"] for item in htft_result}
    top_htft = [(item["htft"], item["probability"]) for item in htft_result[:6]]
    
    # 净胜球分布
    goal_diff_dist = {}
    for diff in range(-7, 8):
        if diff >= 0:
            p = sum(dc_matrix[diff+j, j] for j in range(8-diff))
        else:
            p = sum(dc_matrix[j, j-diff] for j in range(8+diff))
        goal_diff_dist[diff] = p
    
    # 净胜球众数
    k_dist = max(goal_diff_dist.items(), key=lambda x: x[1])[0]
    k_dist_prob = goal_diff_dist[k_dist]
    
    # 多模型融合基础概率
    weights = {"dc": 0.35, "nb": 0.25, "zip": 0.15, "shin": 0.15, "market": 0.10}
    
    fused_probs = {
        "home": (
            weights["dc"] * dc_probs["home"] +
            weights["nb"] * nb_probs["home"] +
            weights["zip"] * zip_probs["home"] +
            weights["shin"] * shin_probs[0] +
            weights["market"] * market_h
        ),
        "draw": (
            weights["dc"] * dc_probs["draw"] +
            weights["nb"] * nb_probs["draw"] +
            weights["zip"] * zip_probs["draw"] +
            weights["shin"] * shin_probs[1] +
            weights["market"] * market_d
        ),
        "away": (
            weights["dc"] * dc_probs["away"] +
            weights["nb"] * nb_probs["away"] +
            weights["zip"] * zip_probs["away"] +
            weights["shin"] * shin_probs[2] +
            weights["market"] * market_a
        ),
    }
    
    # 归一化
    total = sum(fused_probs.values())
    fused_probs = {k: v/total for k, v in fused_probs.items()}
    
    # 规则63：单关平局上修
    is_single = match.get("is_single", False)
    single_adjust_note = ""
    final_probs = dict(fused_probs)
    
    if is_single:
        first_prob = max(fused_probs.values())
        draw_prob = fused_probs["draw"]
        gap_pp = (first_prob - draw_prob) * 100
        
        if gap_pp <= 10:
            adjust = 0.14
        elif gap_pp <= 20:
            adjust = 0.11
        else:
            adjust = 0.09
        
        adjust = min(adjust, 0.18)
        
        old_draw = final_probs["draw"]
        new_draw = min(old_draw + adjust, 0.65)
        actual_adjust = new_draw - old_draw
        
        non_draw_total = final_probs["home"] + final_probs["away"]
        if non_draw_total > 0:
            ratio_h = final_probs["home"] / non_draw_total
            ratio_a = final_probs["away"] / non_draw_total
            final_probs["home"] -= actual_adjust * ratio_h
            final_probs["away"] -= actual_adjust * ratio_a
        final_probs["draw"] = new_draw
        
        total = sum(final_probs.values())
        final_probs = {k: v/total for k, v in final_probs.items()}
        
        single_adjust_note = f"单关平局上修+{actual_adjust*100:.1f}%（差距{gap_pp:.1f}pp→档位{adjust*100:.0f}%）"
    
    # 确定首推和次选
    sorted_probs = sorted(final_probs.items(), key=lambda x: -x[1])
    primary = sorted_probs[0][0]
    secondary = sorted_probs[1][0]
    primary_prob = sorted_probs[0][1]
    secondary_prob = sorted_probs[1][1]
    
    # 方向内净胜球众数（k_rec）
    if primary == "home":
        candidates = {k: v for k, v in goal_diff_dist.items() if k >= 1}
    elif primary == "away":
        candidates = {k: v for k, v in goal_diff_dist.items() if k <= -1}
    else:
        candidates = {k: v for k, v in goal_diff_dist.items() if k == 0}
    
    if candidates:
        k_rec = max(candidates.items(), key=lambda x: x[1])[0]
        k_rec_prob = candidates[k_rec]
    else:
        k_rec = k_dist
        k_rec_prob = k_dist_prob
    
    k_consistent = (
        (primary == "home" and k_dist >= 1) or
        (primary == "away" and k_dist <= -1) or
        (primary == "draw" and k_dist == 0)
    )
    
    # 让球推荐
    hhad_sorted = sorted(hhad_probs.items(), key=lambda x: -x[1])
    hhad_primary = hhad_sorted[0][0]
    hhad_primary_prob = hhad_sorted[0][1]
    
    # 总进球档位
    ttg_probs = {}
    for t in ["0", "1", "2", "3", "4", "5", "6", "7+"]:
        if t == "7+":
            ttg_probs[t] = sum(v for k, v in total_goals_dist.items() if k >= 7)
        else:
            ttg_probs[t] = total_goals_dist.get(int(t), 0)
    ttg_sorted = sorted(ttg_probs.items(), key=lambda x: -x[1])
    
    # 比分TOP5（方向内展开）
    def generate_score_candidates(k_rec_val, primary_dir, dc_matrix_val, top_n=5):
        candidates = []
        max_g = 8
        for i in range(max_g):
            for j in range(max_g):
                diff = i - j
                prob = dc_matrix_val[i, j]
                if prob < 0.005:
                    continue
                if primary_dir == "home" and diff < 1:
                    continue
                if primary_dir == "away" and diff > -1:
                    continue
                if primary_dir == "draw" and diff != 0:
                    continue
                candidates.append((i, j, prob, diff))
        candidates.sort(key=lambda x: -x[2])
        return candidates[:top_n]
    
    top5_scores = generate_score_candidates(k_rec, primary, dc_matrix, 5)
    
    # 置信度评估
    confidence_score = 0
    if primary_prob >= 0.55:
        confidence_score += 2
    elif primary_prob >= 0.45:
        confidence_score += 1
    
    gap = primary_prob - secondary_prob
    if gap >= 0.15:
        confidence_score += 1
    elif gap >= 0.08:
        confidence_score += 0.5
    
    model_homes = [dc_probs["home"], nb_probs["home"], zip_probs["home"], shin_probs[0]]
    model_std = np.std(model_homes)
    if model_std < 0.03:
        confidence_score += 1
    elif model_std < 0.06:
        confidence_score += 0.5
    
    if match.get("stadium_status") == "空场":
        confidence_score -= 1
    
    if confidence_score >= 3:
        confidence = "高"
    elif confidence_score >= 1.5:
        confidence = "中"
    elif confidence_score >= 0.5:
        confidence = "低"
    else:
        confidence = "极低"
    
    result = {
        "match_num": match["match_num"],
        "league": league,
        "home_team": match["home_team"],
        "away_team": match["away_team"],
        "home_rank": match["home_rank"],
        "away_rank": match["away_rank"],
        "match_time": match["match_time"],
        "is_single": is_single,
        "stadium_status": match.get("stadium_status", "正常"),
        "note": match.get("note", ""),
        "lambda_home": round(lambda_h, 3),
        "lambda_away": round(lambda_a, 3),
        "market_probs": {"home": round(market_h, 4), "draw": round(market_d, 4), "away": round(market_a, 4)},
        "fused_probs": {k: round(v, 4) for k, v in fused_probs.items()},
        "final_probs": {k: round(v, 4) for k, v in final_probs.items()},
        "primary": primary,
        "secondary": secondary,
        "primary_prob": round(primary_prob, 4),
        "secondary_prob": round(secondary_prob, 4),
        "hhad_line": hhad_line,
        "hhad_probs": {k: round(v, 4) for k, v in hhad_probs.items()},
        "hhad_primary": hhad_primary,
        "hhad_primary_prob": round(hhad_primary_prob, 4),
        "ttg_probs": {k: round(v, 4) for k, v in ttg_probs.items()},
        "ttg_sorted": [(k, round(v, 4)) for k, v in ttg_sorted],
        "top5_scores": [(s[0], s[1], round(s[2], 4)) for s in top5_scores],
        "top3_htft": [(ht, round(p, 4)) for ht, p in top_htft[:3]],
        "k_dist": k_dist,
        "k_dist_prob": round(k_dist_prob, 4),
        "k_rec": k_rec,
        "k_rec_prob": round(k_rec_prob, 4),
        "k_consistent": k_consistent,
        "confidence": confidence,
        "confidence_score": round(confidence_score, 2),
        "single_adjust_note": single_adjust_note,
        "odds": match["odds"],
        "hhad_odds": match["hhad_odds"],
    }
    
    return result


def main():
    print("=" * 80)
    print("2026-10-07 周三竞彩6场比赛分析报告")
    print("=" * 80)
    
    results = []
    for match in matches:
        print(f"\n{'='*60}")
        print(f"分析 {match['match_num']} {match['league']}: {match['home_team']} vs {match['away_team']}")
        result = analyze_match(match)
        results.append(result)
        
        print(f"  比赛时间: {result['match_time']}")
        print(f"  {result['note']}")
        print(f"  单关状态: {'是 ⭐' if result['is_single'] else '否'}")
        if result['single_adjust_note']:
            print(f"  单关调整: {result['single_adjust_note']}")
        print(f"  λ主={result['lambda_home']}, λ客={result['lambda_away']}")
        print(f"  市场隐含: 主胜{result['market_probs']['home']*100:.1f}% / 平{result['market_probs']['draw']*100:.1f}% / 客胜{result['market_probs']['away']*100:.1f}%")
        print(f"  综合概率: 主胜{result['final_probs']['home']*100:.1f}% / 平{result['final_probs']['draw']*100:.1f}% / 客胜{result['final_probs']['away']*100:.1f}%")
        print(f"  首推: {result['primary']} ({result['primary_prob']*100:.1f}%)")
        print(f"  次选: {result['secondary']} ({result['secondary_prob']*100:.1f}%)")
        print(f"  让球({result['hhad_line']:+d}): 首推{result['hhad_primary']} ({result['hhad_primary_prob']*100:.1f}%)")
        print(f"  净胜球: k_dist={result['k_dist']}({result['k_dist_prob']*100:.1f}%) / k_rec={result['k_rec']}({result['k_rec_prob']*100:.1f}%) / {'一致' if result['k_consistent'] else '分歧'}")
        print(f"  置信度: {result['confidence']} ({result['confidence_score']})")
        print(f"  比分TOP5: {', '.join([f'{s[0]}-{s[1]}({s[2]*100:.1f}%)' for s in result['top5_scores']])}")
        print(f"  总进球: {', '.join([f'{k}球({v*100:.1f}%)' for k, v in result['ttg_sorted'][:3]])}")
    
    # 保存JSON
    output_path = r"e:\VibeCoding\football\reports\data\analysis_20261007_wednesday.json"
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n\n分析结果已保存到: {output_path}")
    return results


if __name__ == "__main__":
    results = main()
