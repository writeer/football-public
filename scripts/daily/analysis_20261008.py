# -*- coding: utf-8 -*-
"""
2026-10-08 周四竞彩6场比赛分析
按照AGENTS.md 10步管道执行
"""

import sys
sys.path.insert(0, r'e:\VibeCoding\football')

import json
import numpy as np
from lottery_agent.models import (
    DixonColesModel, NegativeBinomialModel, ZIPModel,
    SkellamModel, MonteCarloSimulator, OddsCalibrator,
    HTFTModel
)
from lottery_agent.config import LEAGUE_PROFILES

# ============================================================
# 比赛数据（6场）
# ============================================================
matches = [
    {
        "match_num": "周四001",
        "league": "芬超",
        "home_team": "赫尔辛基",
        "away_team": "瓦萨",
        "home_rank": "芬超第3",
        "away_rank": "芬超第5",
        "match_time": "2026-10-08 23:00",
        "odds": {"home": 1.43, "draw": 4.20, "away": 5.20},
        "hhad_odds": {"home": 2.40, "draw": 3.35, "away": 2.42, "goal_line": -1},
        "is_single": False,
        "stadium_status": "正常",
    },
    {
        "match_num": "周四002",
        "league": "芬超",
        "home_team": "库奥皮奥",
        "away_team": "AC奥卢",
        "home_rank": "芬超第1",
        "away_rank": "芬超第6",
        "match_time": "2026-10-09 00:00",
        "odds": {"home": 1.41, "draw": 3.95, "away": 6.00},
        "hhad_odds": {"home": 2.43, "draw": 3.18, "away": 2.48, "goal_line": -1},
        "is_single": True,  # 用户告知：002开单关
        "stadium_status": "正常",
    },
    {
        "match_num": "周四003",
        "league": "巴甲",
        "home_team": "桑托斯",
        "away_team": "弗拉门戈",
        "home_rank": "巴甲第8",
        "away_rank": "巴甲第1",
        "match_time": "2026-10-09 06:30",
        "odds": {"home": 4.02, "draw": 3.60, "away": 1.66},
        "hhad_odds": {"home": 1.96, "draw": 3.40, "away": 3.08, "goal_line": 1},
        "is_single": False,
        "stadium_status": "正常",
    },
    {
        "match_num": "周四004",
        "league": "巴甲",
        "home_team": "巴拉纳竞技",
        "away_team": "米内罗竞技",
        "home_rank": "巴甲第3",
        "away_rank": "巴甲第7",
        "match_time": "2026-10-09 07:00",
        "odds": {"home": 1.95, "draw": 3.12, "away": 3.38},
        "hhad_odds": {"home": 4.15, "draw": 3.55, "away": 1.65, "goal_line": -1},
        "is_single": False,
        "stadium_status": "正常",
    },
    {
        "match_num": "周四005",
        "league": "巴甲",
        "home_team": "弗鲁米嫩塞",
        "away_team": "科里蒂巴",
        "home_rank": "巴甲第4",
        "away_rank": "巴甲第9",
        "match_time": "2026-10-09 08:30",
        "odds": {"home": 1.33, "draw": 4.25, "away": 7.05},
        "hhad_odds": {"home": 2.15, "draw": 3.33, "away": 2.75, "goal_line": -1},
        "is_single": False,
        "stadium_status": "正常",
    },
    {
        "match_num": "周四006",
        "league": "巴甲",
        "home_team": "帕尔梅拉斯",
        "away_team": "巴伊亚",
        "home_rank": "巴甲第2",
        "away_rank": "巴甲第5",
        "match_time": "2026-10-09 08:30",
        "odds": {"home": 1.42, "draw": 4.00, "away": 5.70},
        "hhad_odds": {"home": 2.40, "draw": 3.28, "away": 2.45, "goal_line": -1},
        "is_single": False,
        "stadium_status": "正常",
    },
]


def analyze_match(match):
    """单场比赛完整分析"""
    league = match["league"]
    profile = LEAGUE_PROFILES.get(league, LEAGUE_PROFILES["default"])
    
    # 初始化模型
    dc = DixonColesModel()
    nb = NegativeBinomialModel()
    zip_model = ZIPModel()
    skellam = SkellamModel()
    mc = MonteCarloSimulator()
    htft = HTFTModel(dc)
    # 从赔率反推lambda
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
    
    # 基于赔率和联赛场均进球反推lambda
    # 使用Pi Rating方法估算
    league_avg = profile["avg_goals"]
    ha_factor = profile["home_advantage"]
    
    # 简单反推：主客队期望进球比 ≈ sqrt(主胜概率/客胜概率) × 主场优势
    # 更精确的做法：用Dixon-Coles拟合
    # 基于赔率和联赛场均进球估算lambda
    # 方法：以赔率去水概率为锚点，用联赛场均进球分配主客队lambda
    def estimate_lambdas(market_h, market_d, market_a, league_avg, ha_factor):
        """从市场概率和联赛场均进球估算lambda_h, lambda_a"""
        # 总期望进球：基于联赛场均，根据平局率调整
        # 平局率高 → 两队实力接近 → 总进球可能偏少
        # 平局率低 → 实力差距大 → 总进球可能偏多
        league_draw_rate = 0.28  # 芬超巴甲均约28%
        draw_diff = market_d - league_draw_rate
        total_goals = league_avg * (1.0 - draw_diff * 1.2)
        
        # 主客队lambda分配
        # 主胜概率高 → 主队lambda高
        # 用平方根比分配更符合泊松模型特性
        strength_ratio = (market_h / market_a) ** 0.6
        # 主场优势加成
        strength_ratio *= ha_factor ** 0.4
        
        lambda_h = total_goals * strength_ratio / (1 + strength_ratio)
        lambda_a = total_goals / (1 + strength_ratio)
        
        # 合理性校验
        lambda_h = max(0.6, min(3.0, lambda_h))
        lambda_a = max(0.5, min(2.5, lambda_a))
        
        return lambda_h, lambda_a
    
    # 使用市场去水概率作为目标
    lambda_h, lambda_a = estimate_lambdas(market_h, market_d, market_a, league_avg, ha_factor)
    
    # 模型计算
    dc_probs = dc.outcome_probs(lambda_h, lambda_a)
    nb_probs = nb.outcome_probs(lambda_h, lambda_a)
    zip_probs = zip_model.outcome_probs(lambda_h, lambda_a)
    skellam_probs = skellam.outcome_probs(lambda_h, lambda_a)
    mc_result = mc.simulate(lambda_h, lambda_a)
    mc_probs = {"home": mc_result["home_win"], "draw": mc_result["draw"], "away": mc_result["away_win"]}
    
    # DC比分矩阵
    dc_matrix = dc.compute_matrix(lambda_h, lambda_a)
    top_scores_dc = dc.top_scores(lambda_h, lambda_a, 10)
    
    # Skellam让球（手动计算）
    hhad_line = match["hhad_odds"]["goal_line"]
    # 让球胜平负：调整净胜球阈值
    # hhad_line=-1表示主队让1球 → 主队净胜≥2球=让胜，净胜=1球=让平，净胜≤0球=让负
    from scipy import stats as sp_stats
    def handicap_skellam(lambda_h, lambda_a, handicap):
        """handicap: 主队让球数（正数为主让，负数为客让）"""
        # 调整后的净胜球 = 实际净胜球 + handicap
        # 例如：handicap=-1（主让1球）→ 调整后净胜 = 实际净胜 - 1
        # 让胜 = 调整后净胜 > 0 → 实际净胜 > -handicap
        # 让平 = 调整后净胜 = 0 → 实际净胜 = -handicap
        # 让负 = 调整后净胜 < 0 → 实际净胜 < -handicap
        threshold = -handicap  # 主队需要净胜的球数
        # 让胜: 净胜 > threshold
        hw = sp_stats.skellam.sf(threshold, lambda_h, lambda_a)
        # 让平: 净胜 = threshold
        d = sp_stats.skellam.pmf(threshold, lambda_h, lambda_a)
        # 让负: 净胜 < threshold
        aw = sp_stats.skellam.cdf(threshold - 1, lambda_h, lambda_a)
        return {"home": hw, "draw": d, "away": aw}
    
    hhad_probs = handicap_skellam(lambda_h, lambda_a, hhad_line)
    
    # 总进球
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
    
    # 净胜球众数（无条件）- k_dist
    k_dist = max(goal_diff_dist.items(), key=lambda x: x[1])[0]
    k_dist_prob = goal_diff_dist[k_dist]
    
    # 净胜球众数（方向内条件）- k_rec
    # 先确定首推方向
    had_fused = {
        "home": (dc_probs["home"] + nb_probs["home"] + zip_probs["home"]) / 3,
        "draw": (dc_probs["draw"] + nb_probs["draw"] + zip_probs["draw"]) / 3,
        "away": (dc_probs["away"] + nb_probs["away"] + zip_probs["away"]) / 3,
    }
    primary_dir = max(had_fused, key=had_fused.get)
    
    # 方向内条件众数
    if primary_dir == "home":
        candidates = {k: v for k, v in goal_diff_dist.items() if k >= 1}
    elif primary_dir == "away":
        candidates = {k: v for k, v in goal_diff_dist.items() if k <= -1}
    else:  # draw
        candidates = {k: v for k, v in goal_diff_dist.items() if k == 0}
    
    if candidates:
        k_rec = max(candidates.items(), key=lambda x: x[1])[0]
        k_rec_prob = candidates[k_rec]
    else:
        k_rec = k_dist
        k_rec_prob = k_dist_prob
    
    k_consistent = (
        (primary_dir == "home" and k_dist >= 1) or
        (primary_dir == "away" and k_dist <= -1) or
        (primary_dir == "draw" and k_dist == 0)
    )
    
    # 规则63：单关平局上修
    is_single = match.get("is_single", False)
    single_adjust_note = ""
    if is_single:
        # 计算平局与首选差距
        first_prob = max(had_fused.values())
        draw_prob = had_fused["draw"]
        gap_pp = (first_prob - draw_prob) * 100  # 百分点
        
        # 按档位上修
        if gap_pp <= 10:
            adjust = 0.14  # +14%
        elif gap_pp <= 20:
            adjust = 0.11  # +11%
        else:
            adjust = 0.09  # +9%
        
        # 累计上限+18%（法甲等其他规则可能叠加，这里单关单独用）
        adjust = min(adjust, 0.18)
        
        # 平局上修，主胜客胜按比例压缩
        old_draw = had_fused["draw"]
        new_draw = min(old_draw + adjust, 0.65)
        actual_adjust = new_draw - old_draw
        # 按比例压缩主胜客胜
        non_draw_total = had_fused["home"] + had_fused["away"]
        if non_draw_total > 0:
            ratio_h = had_fused["home"] / non_draw_total
            ratio_a = had_fused["away"] / non_draw_total
            had_fused["home"] -= actual_adjust * ratio_h
            had_fused["away"] -= actual_adjust * ratio_a
        had_fused["draw"] = new_draw
        
        single_adjust_note = f"单关平局上修+{actual_adjust*100:.1f}%（差距{gap_pp:.1f}pp→档位{adjust*100:.0f}%）"
    
    # 综合概率融合（多模型加权）
    weights = {"dc": 0.35, "nb": 0.25, "zip": 0.15, "shin": 0.15, "market": 0.10}
    
    final_probs = {
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
    
    # 如果是单关，用单关调整后的had_fused替换
    if is_single:
        final_probs = had_fused
    
    # 归一化
    total = sum(final_probs.values())
    final_probs = {k: v/total for k, v in final_probs.items()}
    
    # 确定首推和次选
    sorted_probs = sorted(final_probs.items(), key=lambda x: -x[1])
    primary = sorted_probs[0][0]
    secondary = sorted_probs[1][0]
    primary_prob = sorted_probs[0][1]
    secondary_prob = sorted_probs[1][1]
    
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
    
    # 比分TOP5（用k_rec展开 + 联合概率）
    # 规则67双轨制：k_rec为方向内众数，作为展开锚点
    def generate_score_candidates(k_rec, primary_dir, dc_matrix, top_n=5):
        """基于净胜球锚点在方向内展开比分候选"""
        candidates = []
        max_g = 8
        
        # 收集方向内所有比分
        for i in range(max_g):
            for j in range(max_g):
                diff = i - j
                prob = dc_matrix[i, j]
                if prob < 0.005:
                    continue
                
                # 方向过滤
                if primary_dir == "home" and diff < 1:
                    continue
                if primary_dir == "away" and diff > -1:
                    continue
                if primary_dir == "draw" and diff != 0:
                    continue
                
                candidates.append((i, j, prob, diff))
        
        # 按概率排序
        candidates.sort(key=lambda x: -x[2])
        return candidates[:top_n]
    
    top5_scores = generate_score_candidates(k_rec, primary, dc_matrix, 5)
    
    # 半全场TOP3
    top3_htft = top_htft[:3]
    
    # 置信度评估
    confidence_score = 0
    # 首选概率
    if primary_prob >= 0.55:
        confidence_score += 2
    elif primary_prob >= 0.45:
        confidence_score += 1
    
    # 首选与次选差距
    gap = primary_prob - secondary_prob
    if gap >= 0.15:
        confidence_score += 1
    elif gap >= 0.08:
        confidence_score += 0.5
    
    # 模型一致性
    model_homes = [dc_probs["home"], nb_probs["home"], zip_probs["home"], shin_probs[0]]
    model_std = np.std(model_homes)
    if model_std < 0.03:
        confidence_score += 1
    elif model_std < 0.06:
        confidence_score += 0.5
    
    # 空场降一级
    if match.get("stadium_status") == "空场":
        confidence_score -= 1
    
    # 置信度等级
    if confidence_score >= 3:
        confidence = "高"
    elif confidence_score >= 1.5:
        confidence = "中"
    elif confidence_score >= 0.5:
        confidence = "低"
    else:
        confidence = "极低"
    
    # 组装结果
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
        "lambda_home": round(lambda_h, 3),
        "lambda_away": round(lambda_a, 3),
        "market_probs": {"home": round(market_h, 4), "draw": round(market_d, 4), "away": round(market_a, 4)},
        "dc_probs": {k: round(v, 4) for k, v in dc_probs.items()},
        "nb_probs": {k: round(v, 4) for k, v in nb_probs.items()},
        "zip_probs": {k: round(v, 4) for k, v in zip_probs.items()},
        "shin_probs": [round(p, 4) for p in shin_probs],
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
        "ttg_sorted": ttg_sorted,
        "top5_scores": [(s[0], s[1], round(s[2], 4)) for s in top5_scores],
        "top3_htft": [(ht, round(p, 4)) for ht, p in top3_htft],
        "k_dist": k_dist,
        "k_dist_prob": round(k_dist_prob, 4),
        "k_rec": k_rec,
        "k_rec_prob": round(k_rec_prob, 4),
        "k_consistent": k_consistent,
        "goal_diff_dist": {str(k): round(v, 4) for k, v in goal_diff_dist.items()},
        "confidence": confidence,
        "confidence_score": round(confidence_score, 2),
        "single_adjust_note": single_adjust_note,
    }
    
    return result


def main():
    print("=" * 80)
    print("2026-10-08 周四竞彩6场比赛分析报告")
    print("=" * 80)
    
    results = []
    for match in matches:
        print(f"\n{'='*60}")
        print(f"分析 {match['match_num']} {match['league']}: {match['home_team']} vs {match['away_team']}")
        result = analyze_match(match)
        results.append(result)
        
        # 打印摘要
        print(f"  比赛时间: {result['match_time']}")
        print(f"  场地状态: {result['stadium_status']}")
        print(f"  单关状态: {'是' if result['is_single'] else '否'}")
        if result['single_adjust_note']:
            print(f"  单关调整: {result['single_adjust_note']}")
        print(f"  λ主={result['lambda_home']}, λ客={result['lambda_away']}")
        print(f"  市场隐含: 主胜{result['market_probs']['home']*100:.1f}% / 平{result['market_probs']['draw']*100:.1f}% / 客胜{result['market_probs']['away']*100:.1f}%")
        print(f"  综合概率: 主胜{result['final_probs']['home']*100:.1f}% / 平{result['final_probs']['draw']*100:.1f}% / 客胜{result['final_probs']['away']*100:.1f}%")
        print(f"  首推: {result['primary']} ({result['primary_prob']*100:.1f}%)")
        print(f"  次选: {result['secondary']} ({result['secondary_prob']*100:.1f}%)")
        print(f"  让球盘({result['hhad_line']:+d}): 首推{result['hhad_primary']} ({result['hhad_primary_prob']*100:.1f}%)")
        print(f"  净胜球众数: 分布众数={result['k_dist']}({result['k_dist_prob']*100:.1f}%) / 推荐众数={result['k_rec']}({result['k_rec_prob']*100:.1f}%) / {'一致' if result['k_consistent'] else '分歧'}")
        print(f"  置信度: {result['confidence']} ({result['confidence_score']})")
        print(f"  比分TOP5: {', '.join([f'{s[0]}-{s[1]}({s[2]*100:.1f}%)' for s in result['top5_scores']])}")
    
    # 保存JSON
    output_path = r"e:\VibeCoding\football\reports\data\analysis_20261008.json"
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n\n分析结果已保存到: {output_path}")
    return results


if __name__ == "__main__":
    results = main()
