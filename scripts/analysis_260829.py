# -*- coding: utf-8 -*-
"""
周六2026-08-29 竞彩分析脚本
27场比赛完整分析 — 总控综合判断
"""
import json, math, os
from datetime import datetime

# ============ 工具函数 ============

def shin_probabilities(had_odds):
    """Shin模型去抽水"""
    if not had_odds or len(had_odds) != 3:
        return [0.33, 0.34, 0.33]
    # 简化Shin: 使用noVigProb
    # 已有noVigProb直接使用
    return had_odds

def poisson_pmf(k, lam):
    """泊松分布PMF"""
    if lam <= 0:
        return 1e-10 if k == 0 else 1e-10
    return (lam ** k * math.exp(-lam)) / math.factorial(k)

def dc_adjust(p, i, j, lam_h, lam_a, rho=0.1):
    """Dixon-Coles低比分修正"""
    if i == 0 and j == 0:
        return p * (1 + lam_h * lam_a * rho)
    elif i == 0 and j == 1:
        return p * (1 - lam_h * rho)
    elif i == 1 and j == 0:
        return p * (1 - lam_a * rho)
    elif i == 1 and j == 1:
        return p * (1 + rho)
    return p

def calc_score_matrix(lam_h, lam_a, rho=0.1, max_goals=8):
    """DC模型比分概率矩阵"""
    matrix = []
    for i in range(max_goals + 1):
        row = []
        for j in range(max_goals + 1):
            p = poisson_pmf(i, lam_h) * poisson_pmf(j, lam_a)
            p = dc_adjust(p, i, j, lam_h, lam_a, rho)
            row.append(p)
        matrix.append(row)
    # 归一化
    total = sum(sum(row) for row in matrix)
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            matrix[i][j] /= total
    return matrix

def calc_ttg(matrix, max_goals=7):
    """总进球分布"""
    ttg = [0.0] * (max_goals + 1)
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            total = i + j
            if total <= max_goals:
                ttg[total] += matrix[i][j]
            else:
                ttg[max_goals] += matrix[i][j]
    return ttg

def calc_hafu(matrix, lam_h, lam_a):
    """半全场概率（简化版）"""
    # 上半场lambda = 全场 * 0.42
    half_lam_h = lam_h * 0.42
    half_lam_a = lam_a * 0.42
    
    half_matrix = calc_score_matrix(half_lam_h, half_lam_a, rho=0.15, max_goals=4)
    
    hafu = {
        '胜胜': 0, '胜平': 0, '胜负': 0,
        '平胜': 0, '平平': 0, '平负': 0,
        '负胜': 0, '负平': 0, '负负': 0
    }
    
    for hi in range(min(4, len(half_matrix))):
        for hj in range(min(4, len(half_matrix[hi]))):
            half_p = half_matrix[hi][hj]
            half_result = '胜' if hi > hj else ('平' if hi == hj else '负')
            
            for fi in range(len(matrix)):
                for fj in range(len(matrix[fi])):
                    full_result = '胜' if fi > fj else ('平' if fi == fj else '负')
                    # 简化：下半场比分 = 全场 - 上半场
                    second_half_i = fi - hi
                    second_half_j = fj - hj
                    if second_half_i < 0 or second_half_j < 0:
                        continue
                    second_p = poisson_pmf(second_half_i, max(0.01, lam_h - half_lam_h)) * \
                               poisson_pmf(second_half_j, max(0.01, lam_a - half_lam_a))
                    
                    key = half_result + full_result
                    if key in hafu:
                        hafu[key] += half_p * second_p
    
    # 归一化
    total = sum(hafu.values())
    if total > 0:
        for k in hafu:
            hafu[k] /= total
    return hafu

def calc_match_probs(lam_h, lam_a, rho=0.1):
    """计算比赛结果概率"""
    matrix = calc_score_matrix(lam_h, lam_a, rho)
    
    home_win = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix[i])) if i > j)
    draw = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix[i])) if i == j)
    away_win = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix[i])) if i < j)
    
    ttg = calc_ttg(matrix)
    
    # 比分TOP10
    scores = []
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            scores.append((f"{i}:{j}", matrix[i][j], i, j))
    scores.sort(key=lambda x: x[1], reverse=True)
    
    hafu = calc_hafu(matrix, lam_h, lam_a)
    hafu_sorted = sorted(hafu.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'home_win': home_win,
        'draw': draw,
        'away_win': away_win,
        'ttg': ttg,
        'scores_top10': scores[:10],
        'hafu_top3': hafu_sorted[:3]
    }

def confidence_rating(model_probs, shin_probs, data_quality='medium'):
    """置信度评级"""
    # 模型一致度（简化：DC vs Shin差异）
    diffs = [abs(model_probs[i] - shin_probs[i]) for i in range(3)]
    avg_diff = sum(diffs) / 3
    
    score = 0
    if avg_diff < 0.03:
        score += 2
    elif avg_diff < 0.05:
        score += 1
    elif avg_diff > 0.08:
        score -= 1
    
    if data_quality == 'high':
        score += 1
    elif data_quality == 'low':
        score -= 1
    
    if score >= 2:
        return '★★★', '高'
    elif score >= 1:
        return '★★', '中'
    elif score >= 0:
        return '★', '低'
    else:
        return '☆', '极低'

# ============ 比赛数据 ============

matches_data = {
    "001": {
        "league": "日职", "tier": "Tier2", "home": "水户蜀葵", "away": "町田泽维",
        "rank_h": 7, "rank_a": 1, "single": False, "time": "17:00",
        "value_h": 10.5, "value_a": 19.6, "value_diff": 1.87,
        "goalLine": 1, "league_avg_goals": 2.52, "league_draw_rate": 0.26,
        "injuries_h": "一门+2中卫+后腰缺阵(防线严重残缺)", "injuries_a": "小川航基(中锋)缺阵",
        "h2h": "近2次2-2平局; 同主客近5次2胜2平1负",
        "form_h": "3轮1胜1平1负, 近10场1胜1平8负(极度低迷)", "form_a": "3轮3连胜进10失4, 榜首",
        "context": "町田多线作战(亚冠); 水户防线严重伤停但进攻端有火力(3场5球)",
        "shin_probs": [0.198, 0.259, 0.543],
        "lambda_base_h": 1.0, "lambda_base_a": 1.8,
        "new_season_round": 4, "rule65_trigger": True, "rule65_tier": "Tier2"
    },
    "002": {
        "league": "日职", "tier": "Tier2", "home": "清水鼓动", "away": "柏太阳神",
        "rank_h": 15, "rank_a": 2, "single": True, "time": "17:30",
        "value_h": 13.55, "value_a": 18.43, "value_diff": 1.36,
        "goalLine": 1, "league_avg_goals": 2.52, "league_draw_rate": 0.26,
        "injuries_h": "7+人缺阵(前锋红牌停赛+后卫停赛+多人伤伤)", "injuries_a": "3名中场伤停",
        "h2h": "柏已成克星: 近5次4胜1平; 2025年双杀零封; 同主客1胜1平3负",
        "form_h": "3轮1胜2负进1球, 近2轮0进球", "form_a": "3轮3连胜进9球, 场均3球",
        "context": "清水严重残阵; 柏太阳神8月25日藤尾翔太转会",
        "shin_probs": [0.246, 0.270, 0.484],
        "lambda_base_h": 0.9, "lambda_base_a": 2.0,
        "new_season_round": 4, "rule65_trigger": True, "rule65_tier": "Tier2"
    },
    "003": {
        "league": "日乙", "tier": "Tier3", "home": "大宫松鼠", "away": "湘南海洋",
        "rank_h": 1, "rank_a": 2, "single": False, "time": "18:00",
        "value_h": 11.35, "value_a": 8.23, "value_diff": 1.38,
        "goalLine": -1, "league_avg_goals": 2.49, "league_draw_rate": 0.234,
        "injuries_h": "一门伤缺(替补门将经验少); 前锋山本出战成疑", "injuries_a": "无具体伤停",
        "h2h": "大宫同主客历史碾压: 6胜4平0负; 近6次5胜1平",
        "form_h": "3轮3连胜进8失3, 榜首", "form_a": "3轮2胜1平进2失0, 防守固若金汤",
        "context": "大宫一门伤停; 湘南3轮0失球; 日乙Tier3但小球率52%",
        "shin_probs": [0.493, 0.257, 0.250],
        "lambda_base_h": 1.6, "lambda_base_a": 0.8,
        "new_season_round": 4, "rule65_trigger": True, "rule65_tier": "Tier3"
    },
    "004": {
        "league": "韩职", "tier": "Tier3", "home": "蔚山现代", "away": "金泉尚武",
        "rank_h": 3, "rank_a": 11, "single": True, "time": "18:30",
        "value_h": 14.30, "value_a": 14.25, "value_diff": 1.00,
        "goalLine": -1, "league_avg_goals": 2.48, "league_draw_rate": 0.30,
        "injuries_h": "2后卫伤停; 佩德里尼奥伤; 3名外援前锋复出(利好)", "injuries_a": "无具体伤停信息",
        "h2h": "近10次金泉2胜3平5负; 最近2次: 1-2(蔚山客胜)、0-0(平)",
        "form_h": "25轮11胜4平10负, 近3连败, 主场场均失2球", "form_a": "25轮4胜15平6负, 平局大师(60%)",
        "context": "蔚山3连败+外援复出; 金泉平局率极高(15/25=60%)",
        "shin_probs": [0.454, 0.269, 0.277],
        "lambda_base_h": 1.4, "lambda_base_a": 1.0,
        "new_season_round": 26, "rule65_trigger": True, "rule65_tier": "Tier3"
    },
    "006": {
        "league": "英超", "tier": "Tier1(例外)", "home": "利物浦", "away": "诺丁汉",
        "rank_h": 10, "rank_a": 15, "single": True, "time": "19:30",
        "value_h": 963, "value_a": 550, "value_diff": 1.75,
        "goalLine": -1, "league_avg_goals": 2.86, "league_draw_rate": 0.242,
        "injuries_h": "基耶萨+戈麦斯+布拉德利+莱奥尼+埃基蒂克缺阵", "injuries_a": "吉布斯-怀特可能复出; 新援德拉普待定",
        "h2h": "森林近2次安菲尔德全胜(3-0, 1-0)! 但上次交锋利物浦1-0绝杀",
        "form_h": "首轮2-2纽卡(99分钟点球绝平); 新帅伊劳拉首秀", "form_a": "首轮0-1负利兹+联赛杯0-2利兹; 2连败0进球",
        "context": "利物浦主场首秀; 森林安菲尔德魔咒(近2次全胜); 但森林状态极差",
        "shin_probs": [0.656, 0.197, 0.148],
        "lambda_base_h": 2.2, "lambda_base_a": 0.8,
        "new_season_round": 2, "rule65_trigger": True, "rule65_tier": "Tier1(英超例外)"
    },
    "008": {
        "league": "瑞超", "tier": "Tier2", "home": "埃夫斯堡", "away": "代格福什",
        "rank_h": 5, "rank_a": 14, "single": False, "time": "21:00",
        "value_h": 16.65, "value_a": 7.4, "value_diff": 2.25,
        "goalLine": -1, "league_avg_goals": 2.65, "league_draw_rate": 0.25,
        "injuries_h": "无具体伤停信息", "injuries_a": "中场核心停赛+2后卫伤停(防守大幅减员)",
        "h2h": "同主客4场1胜2平1负(无优势); 全部交锋近10次7胜2平1负",
        "form_h": "18轮7胜7平4负; 近5场3胜1平1负回升", "form_a": "18轮4胜4平10负; 近2连败",
        "context": "埃夫斯堡身价碾压2.25倍; 代格福什中场核心停赛+防线残缺",
        "shin_probs": [0.615, 0.228, 0.157],
        "lambda_base_h": 2.0, "lambda_base_a": 0.8,
        "new_season_round": 19, "rule65_trigger": True, "rule65_tier": "Tier2"
    },
    "009": {
        "league": "德甲", "tier": "Tier1", "home": "埃沃斯堡", "away": "勒沃库森",
        "rank_h": 7, "rank_a": 3, "single": True, "time": "21:30",
        "value_h": 59.10, "value_a": 463.95, "value_diff": 7.85,
        "goalLine": 1, "league_avg_goals": 3.21, "league_draw_rate": 0.243,
        "injuries_h": "赛弗特+齐默尔舍德伤缺", "injuries_a": "泰里耶+本塞吉尔+安德里希+阿达米伤缺(前场多人缺阵)",
        "h2h": "仅2次交锋各1胜: 埃沃4-3勒沃(7球)、勒沃3-0埃沃(3球), 场均5球!",
        "form_h": "德乙第2名升级, 近10场6胜2平2负; 德乙进攻最强(64球)", "form_a": "近10场7胜1平2负; 德国杯4-0威斯巴登",
        "context": "埃沃斯堡历史首场德甲主场! 载入史册; 勒沃身价7.85倍碾压; 交锋场均5球",
        "shin_probs": [0.179, 0.211, 0.610],
        "lambda_base_h": 1.2, "lambda_base_a": 2.5,
        "new_season_round": 1, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "010": {
        "league": "德甲", "tier": "Tier1", "home": "莱红牛", "away": "门兴",
        "rank_h": 14, "rank_a": 5, "single": False, "time": "21:30",
        "value_h": 506, "value_a": 129, "value_diff": 3.9,
        "goalLine": -1, "league_avg_goals": 3.21, "league_draw_rate": 0.243,
        "injuries_h": "门将十字韧带+后卫内收肌+中场伤缺; 前锋膝手术", "injuries_a": "3人长期伤缺",
        "h2h": "近3场2次0-0/1-0低球闷战; 近16场莱比锡9胜3平4负",
        "form_h": "近6场4胜2负; 德国杯6-0特里尔; 上赛季第14", "form_a": "德国杯5-0; 季前6连胜; 上赛季第5",
        "context": "德甲首轮; 交锋低球闷战特征; 莱比锡身价3.9倍碾压",
        "shin_probs": [0.619, 0.206, 0.175],
        "lambda_base_h": 2.0, "lambda_base_a": 0.9,
        "new_season_round": 1, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "011": {
        "league": "德甲", "tier": "Tier1", "home": "柏林联合", "away": "法兰克福",
        "rank_h": 16, "rank_a": 6, "single": False, "time": "21:30",
        "value_h": 127, "value_a": 348, "value_diff": 2.8,
        "goalLine": -1, "league_avg_goals": 3.21, "league_draw_rate": 0.243,
        "injuries_h": "2门将伤+前锋跟腱伤+后卫小腿伤(门将危机)", "injuries_a": "7人伤停(中场+后卫+前锋)但阵容深度厚",
        "h2h": "近年主场2平; 历史法兰克福占优",
        "form_h": "伤病满营; 上赛季第16(保级)", "form_a": "上赛季第6; 转会净收入+46.95m",
        "context": "德甲首轮; 柏林联合门将危机; 法兰克福7人伤停但深度厚",
        "shin_probs": [0.367, 0.260, 0.372],
        "lambda_base_h": 1.2, "lambda_base_a": 1.6,
        "new_season_round": 1, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "012": {
        "league": "德甲", "tier": "Tier1", "home": "科隆", "away": "霍芬海姆",
        "rank_h": 8, "rank_a": 11, "single": False, "time": "21:30",
        "value_h": 124, "value_a": 302, "value_diff": 2.4,
        "goalLine": 1, "league_avg_goals": 3.21, "league_draw_rate": 0.243,
        "injuries_h": "前锋肌肉伤+2后卫伤缺", "injuries_a": "前锋停赛+后卫伤+中场停赛",
        "h2h": "近6次主场队从未获胜! 科隆上次主场胜2015年; 近5场科隆2胜2平1负",
        "form_h": "热身2-1胜皇家社会; 上赛季第8", "form_a": "上赛季第4(45分/22场); 状态出色",
        "context": "德甲首轮; 主场队6场不胜魔咒; 交锋大球倾向",
        "shin_probs": [0.322, 0.248, 0.430],
        "lambda_base_h": 1.3, "lambda_base_a": 1.8,
        "new_season_round": 1, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "013": {
        "league": "德甲", "tier": "Tier1", "home": "美因茨", "away": "帕德博恩",
        "rank_h": 12, "rank_a": 13, "single": False, "time": "21:30",
        "value_h": 175, "value_a": 46, "value_diff": 3.8,
        "goalLine": -1, "league_avg_goals": 3.21, "league_draw_rate": 0.243,
        "injuries_h": "2前锋伤+2中场伤缺", "injuries_a": "2中场伤+前锋伤+后卫伤(长期)",
        "h2h": "美因茨4胜1平0负, 进17失4! 绝对碾压",
        "form_h": "上赛季第12", "form_a": "德乙第3升级(附加赛逆转); 近10场5胜3平2负",
        "context": "德甲首轮; 美因茨身价3.8倍碾压+交锋统治; 帕德博恩升班马",
        "shin_probs": [0.615, 0.217, 0.168],
        "lambda_base_h": 2.2, "lambda_base_a": 0.7,
        "new_season_round": 1, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "014": {
        "league": "英超", "tier": "Tier1(例外)", "home": "考文垂", "away": "赫尔城",
        "rank_h": 17, "rank_a": 6, "single": False, "time": "22:00",
        "value_h": 292, "value_a": 144, "value_diff": 2.0,
        "goalLine": -1, "league_avg_goals": 2.86, "league_draw_rate": 0.242,
        "injuries_h": "前锋大腿伤+2后卫伤缺", "injuries_a": "6人伤缺! 被迫5后卫+单箭头",
        "h2h": "近2次0-0闷平; 兰帕德赫尔城克星(球员+教练不败)",
        "form_h": "首轮0-3负阿森纳; 联赛杯4-2胜; 升班马", "form_a": "首轮2-0胜曼联(爆冷)! 联赛杯5-4胜; 升班马",
        "context": "英超第2轮; 考文垂身价2倍碾压; 赫尔城6人伤缺; 兰帕德克星因素",
        "shin_probs": [0.543, 0.256, 0.201],
        "lambda_base_h": 1.7, "lambda_base_a": 0.9,
        "new_season_round": 2, "rule65_trigger": True, "rule65_tier": "Tier1(英超例外)"
    },
    "015": {
        "league": "英超", "tier": "Tier1(例外)", "home": "伯恩茅斯", "away": "埃弗顿",
        "rank_h": 13, "rank_a": 5, "single": True, "time": "22:00",
        "value_h": 575, "value_a": 471, "value_diff": 1.2,
        "goalLine": -1, "league_avg_goals": 2.86, "league_draw_rate": 0.242,
        "injuries_h": "2后卫伤+前锋伤+门将停赛", "injuries_a": "2中场伤缺(含新援)+1中场存疑",
        "h2h": "伯恩茅斯近10次7胜0平3负; 近3次主场全胜; 但上次主场0-1负",
        "form_h": "首轮1-2负曼城(射正4/5); 近6主场仅1胜", "form_a": "首轮2-0胜水晶宫; 联赛杯4-0; 状态火热",
        "context": "英超第2轮开单关; 伯恩茅斯主场交锋占优; 埃弗顿状态更好",
        "shin_probs": [0.474, 0.264, 0.262],
        "lambda_base_h": 1.5, "lambda_base_a": 1.2,
        "new_season_round": 2, "rule65_trigger": True, "rule65_tier": "Tier1(英超例外)"
    },
    "016": {
        "league": "西甲", "tier": "Tier1", "home": "莱万特", "away": "贝蒂斯",
        "rank_h": 17, "rank_a": 5, "single": False, "time": "23:00",
        "value_h": 87, "value_a": 260, "value_diff": 3.0,
        "goalLine": 1, "league_avg_goals": 2.48, "league_draw_rate": 0.285,
        "injuries_h": "前锋十字韧带(12月复出)", "injuries_a": "门将肩伤+中场肌肉伤+前锋膝伤(存疑)+后卫伤",
        "h2h": "同主客近年大球: 4-3, 4-2, 2-4, 2-2! 场均4.25球",
        "form_h": "2轮0进球3失球(1平1负)", "form_a": "2轮2胜0失球! 防守极佳",
        "context": "西甲第3轮; 贝蒂斯身价3倍碾压+防守极佳; H2H大球历史",
        "shin_probs": [0.291, 0.277, 0.432],
        "lambda_base_h": 1.0, "lambda_base_a": 1.6,
        "new_season_round": 3, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "017": {
        "league": "法甲", "tier": "Tier1", "home": "斯特拉斯堡", "away": "朗斯",
        "rank_h": 18, "rank_a": 3, "single": True, "time": "23:15",
        "value_h": 302, "value_a": 172, "value_diff": 1.75,
        "goalLine": 1, "league_avg_goals": 2.68, "league_draw_rate": 0.273,
        "injuries_h": "中场红牌停赛(首轮红牌)", "injuries_a": "后防线5人伤停/停赛! 防守大幅减员",
        "h2h": "近6场1胜2平3负; 近5场1胜2平2负",
        "form_h": "近10场2胜1平7负(极差); 首轮0-4惨败马赛+红牌", "form_a": "近10场7胜2平1负(极佳); 首轮5-2大胜+超级杯1-0巴黎",
        "context": "法甲第2轮开单关; 斯特拉斯堡极差+红牌停赛; 朗斯状态极佳但后防5人缺",
        "shin_probs": [0.283, 0.253, 0.464],
        "lambda_base_h": 1.1, "lambda_base_a": 1.8,
        "new_season_round": 2, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "018": {
        "league": "挪超", "tier": "Tier2", "home": "维京", "away": "奥勒松",
        "rank_h": 2, "rank_a": 15, "single": False, "time": "23:00",
        "value_h": 49, "value_a": 12, "value_diff": 4.0,
        "goalLine": -2, "league_avg_goals": 2.82, "league_draw_rate": 0.23,
        "injuries_h": "刚踢完欧冠附加赛(3-1胜萨格勒布), 体能消耗", "injuries_a": "阵容单薄",
        "h2h": "近5场3胜1平1负; 历史28场11胜11负6平(均势!)",
        "form_h": "近5场2胜2平1负; 主场8胜1负; 挪超卫冕冠军第2", "form_a": "第15(保级区); 上轮5-5平(!) 防守极差",
        "context": "挪超第19轮; 维京身价4倍碾压+主场龙; 奥勒松防守极差(上轮5-5); 欧冠体能消耗",
        "shin_probs": [0.770, 0.136, 0.093],
        "lambda_base_h": 2.8, "lambda_base_a": 0.5,
        "new_season_round": 19, "rule65_trigger": True, "rule65_tier": "Tier2"
    },
    "019": {
        "league": "英超", "tier": "Tier1(例外)", "home": "热刺", "away": "纽卡斯尔",
        "rank_h": 18, "rank_a": 11, "single": True, "time": "00:30",
        "value_h": 795, "value_a": 586, "value_diff": 1.35,
        "goalLine": -1, "league_avg_goals": 2.86, "league_draw_rate": 0.242,
        "injuries_h": "13+人伤停!(麦迪逊+库卢+西蒙斯等多名核心) 极残", "injuries_a": "队长后卫伤+中场伤+后卫伤+前锋伤",
        "h2h": "纽卡近2赛季客场连胜热刺(1-2, 1-2)! 同主客0胜2平1负",
        "form_h": "首轮负(第18); 新帅弗兰克未取胜", "form_a": "首轮2-2平利物浦; 状态稳健",
        "context": "英超第2轮开单关; 热刺极残阵(13+人缺); 纽卡客场连胜魔咒; 新援马尔穆什首秀",
        "shin_probs": [0.430, 0.254, 0.316],
        "lambda_base_h": 1.3, "lambda_base_a": 1.5,
        "new_season_round": 2, "rule65_trigger": True, "rule65_tier": "Tier1(英超例外)"
    },
    "020": {
        "league": "德甲", "tier": "Tier1", "home": "多特蒙德", "away": "汉堡",
        "rank_h": 4, "rank_a": 10, "single": False, "time": "00:30",
        "value_h": 529, "value_a": 117, "value_diff": 4.5,
        "goalLine": -1, "league_avg_goals": 3.21, "league_draw_rate": 0.243,
        "injuries_h": "中场老将十字韧带+中卫脚踝伤", "injuries_a": "4人伤缺",
        "h2h": "多特近5年主场对汉堡100%胜! 近5次4胜1平",
        "form_h": "近10场5胜1平4负; 超级杯1-2负拜仁; 首轮11赛季不败(10胜1平)", "form_a": "近10场5胜1平4负; 时隔7年重返德甲",
        "context": "德甲首轮; 多特4.5倍碾压+首轮不败纪录; 汉堡时隔7年返德甲",
        "shin_probs": [0.732, 0.165, 0.103],
        "lambda_base_h": 2.6, "lambda_base_a": 0.6,
        "new_season_round": 1, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "021": {
        "league": "意甲", "tier": "Tier1", "home": "蒙扎", "away": "乌迪内斯",
        "rank_h": 18, "rank_a": 11, "single": False, "time": "00:30",
        "value_h": 0, "value_a": 0, "value_diff": 1.0,
        "goalLine": 1, "league_avg_goals": 2.63, "league_draw_rate": 0.273,
        "injuries_h": "队长中场膝伤+中场伤+翼卫伤+膝伤", "injuries_a": "后卫停赛+后卫膝伤+中场内收肌伤(休1月)",
        "h2h": "近5次2胜3平2负(均势); 4/5次双方进球! 同主客1胜1平2负",
        "form_h": "首轮1-4负国米; 主场8场不胜(魔咒); 上赛季意乙主场15胜6负", "form_a": "首轮1-1平科莫; 近4场不败(3胜1平)",
        "context": "意甲第2轮; 蒙扎主场魔咒+双方残阵; 交锋4/5次双方进球",
        "shin_probs": [0.314, 0.300, 0.385],
        "lambda_base_h": 1.2, "lambda_base_a": 1.4,
        "new_season_round": 2, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "022": {
        "league": "意甲", "tier": "Tier1", "home": "佛罗伦萨", "away": "弗罗西诺内",
        "rank_h": 19, "rank_a": 15, "single": True, "time": "00:30",
        "value_h": 310, "value_a": 45, "value_diff": 6.9,
        "goalLine": -1, "league_avg_goals": 2.63, "league_draw_rate": 0.273,
        "injuries_h": "后卫十字韧带(长期)+基恩(前锋核心,转会科莫!)", "injuries_a": "无伤停报告, 阵容完整",
        "h2h": "主场近5年100%胜! 近6次2胜3平1负; 最大比分5-1",
        "form_h": "首轮0-1负; 近5场1胜2平2负; 第19", "form_a": "首轮0-1负尤文; 杯赛4-1胜",
        "context": "意甲第2轮开单关; 佛罗伦萨身价6.9倍碾压+主场H2H全胜; 但基恩离队锋线真空",
        "shin_probs": [0.590, 0.233, 0.177],
        "lambda_base_h": 1.8, "lambda_base_a": 0.7,
        "new_season_round": 2, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "023": {
        "league": "意甲", "tier": "Tier1", "home": "萨索洛", "away": "都灵",
        "rank_h": 12, "rank_a": 13, "single": False, "time": "00:30",
        "value_h": 0, "value_a": 0, "value_diff": 1.0,
        "goalLine": -1, "league_avg_goals": 2.63, "league_draw_rate": 0.273,
        "injuries_h": "中场伤+后卫十字韧带; 贝拉尔迪复出!(利好)", "injuries_a": "6人伤缺但阵容近满配",
        "h2h": "萨索洛主场十年魔咒: 1胜9平6负! 都灵连续8次客场进球",
        "form_h": "近5场1胜1平3负; 贝拉尔迪+伊泽斯复出", "form_a": "首轮1-0胜帕尔马; 近5场状态良好",
        "context": "意甲第2轮; 萨索洛主场十年魔咒; 贝拉尔迪复出; 都灵客场连续进球",
        "shin_probs": [0.426, 0.286, 0.288],
        "lambda_base_h": 1.3, "lambda_base_a": 1.3,
        "new_season_round": 2, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "024": {
        "league": "荷甲", "tier": "Tier2", "home": "阿尔克马", "away": "前进之鹰",
        "rank_h": 1, "rank_a": 2, "single": False, "time": "00:45",
        "value_h": 0, "value_a": 0, "value_diff": 1.0,
        "goalLine": -1, "league_avg_goals": 3.18, "league_draw_rate": 0.215,
        "injuries_h": "后卫腹股沟伤+中场膝伤(2027年1月回归)+后卫轻伤(存疑)", "injuries_a": "后卫腿伤+伤+十字韧带伤",
        "h2h": "阿尔克马11胜1负5平! 主场绝对优势; 近2次1-1、2-2平",
        "form_h": "3战全胜(进7失0)! 近5场全胜进15失3", "form_a": "2胜1平(进5失0)! 第2名",
        "context": "荷甲第4轮; 双方全胜/不败+防守都极佳; 阿尔克马主场H2H碾压",
        "shin_probs": [0.703, 0.170, 0.127],
        "lambda_base_h": 2.4, "lambda_base_a": 0.8,
        "new_season_round": 4, "rule65_trigger": True, "rule65_tier": "Tier2"
    },
    "025": {
        "league": "西甲", "tier": "Tier1", "home": "皇家社会", "away": "西班牙人",
        "rank_h": 19, "rank_a": 9, "single": False, "time": "01:00",
        "value_h": 350, "value_a": 100, "value_diff": 3.5,
        "goalLine": -1, "league_avg_goals": 2.48, "league_draw_rate": 0.285,
        "injuries_h": "后卫膝伤+中场肌肉伤+中场伤", "injuries_a": "后卫停赛+普阿多(队长前锋核心)十字韧带!+基克(前锋)腿筋伤!",
        "h2h": "皇社15胜7平7负; 近6次4胜2平0负; 同主客近5年占优",
        "form_h": "0胜0平2负! 两连败第19", "form_a": "1胜1负第9; 首轮3-0大胜莱万特; 次轮1-2负皇马",
        "context": "西甲第3轮; 皇社两连败; 西班牙人锋线双核全伤(普阿多+基克)",
        "shin_probs": [0.485, 0.269, 0.246],
        "lambda_base_h": 1.5, "lambda_base_a": 0.9,
        "new_season_round": 3, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "026": {
        "league": "葡超", "tier": "Tier2", "home": "维塞乌", "away": "波尔图",
        "rank_h": 12, "rank_a": 2, "single": False, "time": "01:00",
        "value_h": 20, "value_a": 426, "value_diff": 21.3,
        "goalLine": 1, "league_avg_goals": 2.52, "league_draw_rate": 0.265,
        "injuries_h": "中场主力大腿伤", "injuries_a": "前锋十字韧带(长期)+中场腓骨骨折+前锋大腿伤(存疑); 但右后卫+门将复出",
        "h2h": "近5次波尔图全胜! 进14失1! 绝对统治",
        "form_h": "2轮0胜0平2负(第12); 近10场3胜5平2负", "form_a": "3战全胜零封! 近5场全胜进9失1",
        "context": "葡超第4轮; 波尔图身价21倍碾压+3场零封+H2H绝对统治; 维塞乌2轮不胜",
        "shin_probs": [0.090, 0.172, 0.738],
        "lambda_base_h": 0.5, "lambda_base_a": 2.8,
        "new_season_round": 4, "rule65_trigger": True, "rule65_tier": "Tier2"
    },
    "027": {
        "league": "意甲", "tier": "Tier1", "home": "尤文图斯", "away": "帕尔马",
        "rank_h": 8, "rank_a": 16, "single": False, "time": "02:45",
        "value_h": 500, "value_a": 80, "value_diff": 6.25,
        "goalLine": -2, "league_avg_goals": 2.63, "league_draw_rate": 0.273,
        "injuries_h": "伊尔迪兹(核心前锋)骨折缺阵3个月!+弗拉霍维奇背伤+后卫大腿伤+前锋伤+中场停赛", "injuries_a": "中场腹股沟手术(长期)+大腿伤",
        "h2h": "尤文对帕尔马28胜(意甲历史); 帕尔马上次安联取胜2015年!",
        "form_h": "首轮1-0胜; 近10场仅丢6球(场均0.7); 主场6场4胜1平1负", "form_a": "首轮0-1负卡利亚里; 近5场低迷",
        "context": "意甲第2轮; 尤文主场绝对优势+防守顶尖; 但伊尔迪兹骨折重创进攻; 帕尔马升班马",
        "shin_probs": [0.790, 0.142, 0.068],
        "lambda_base_h": 2.2, "lambda_base_a": 0.5,
        "new_season_round": 2, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "028": {
        "league": "西甲", "tier": "Tier1", "home": "塞维利亚", "away": "马竞",
        "rank_h": 4, "rank_a": 6, "single": True, "time": "03:30",
        "value_h": 300, "value_a": 661, "value_diff": 2.2,
        "goalLine": 1, "league_avg_goals": 2.48, "league_draw_rate": 0.285,
        "injuries_h": "中场肌肉伤", "injuries_a": "阿尔瓦雷斯(核心前锋)转会不出场!+瑟洛特(中锋)肌肉伤+后卫停赛+中场伤(存疑)",
        "h2h": "塞维利亚主场近3场连胜! 上次交锋塞维2-1马竞; 但历史马竞65球>塞维43球",
        "form_h": "2轮2胜0失球! 暂居榜首; 近5场4胜1负", "form_a": "1胜1平0负第5; 近5场2胜1平2负",
        "context": "西甲第3轮开单关; 塞维利亚开局完美+主场3连胜; 马竞双中锋全缺(阿尔瓦雷斯转会+瑟洛特伤)",
        "shin_probs": [0.250, 0.269, 0.482],
        "lambda_base_h": 1.3, "lambda_base_a": 1.4,
        "new_season_round": 3, "rule65_trigger": True, "rule65_tier": "Tier1"
    },
    "029": {
        "league": "美职", "tier": "Tier2", "home": "华盛顿", "away": "洛杉矶FC",
        "rank_h": 11, "rank_a": 3, "single": False, "time": "07:30",
        "value_h": 31.55, "value_a": 58.70, "value_diff": 1.86,
        "goalLine": 1, "league_avg_goals": 2.68, "league_draw_rate": 0.24,
        "injuries_h": "后卫停赛+后卫大腿伤+前锋腿伤", "injuries_a": "前锋伤+门将伤+后卫伤+中场伤+中场伤",
        "h2h": "华盛顿0胜! 洛杉矶FC 2胜; 近3次: 1-0, 0-4, 1-1",
        "form_h": "近5场1胜2平2负; 近11场10不败(大量平局); 东部第11", "form_a": "近6场1胜3平2负; 西部第3",
        "context": "美职进行中; 华盛顿从未胜洛杉矶FC; 华盛顿近11场10不败但大量平局; 洛杉矶有孙兴慜",
        "shin_probs": [0.263, 0.253, 0.484],
        "lambda_base_h": 1.1, "lambda_base_a": 1.4,
        "new_season_round": 0, "rule65_trigger": True, "rule65_tier": "Tier2"
    }
}

# ============ 规则应用 + 模型计算 ============

results = {}

for num, m in matches_data.items():
    lam_h = m['lambda_base_h']
    lam_a = m['lambda_base_a']
    
    # 规则35: 新赛季lambda上修 (L035/L021/L017连续多轮升级)
    if m['new_season_round'] > 0:
        if m['new_season_round'] <= 2:
            lam_h += 0.5
            lam_a += 0.5
        elif m['new_season_round'] <= 4:
            lam_h += 0.3
            lam_a += 0.3
    
    # 规则65: 大球上修
    tier = m['rule65_tier']
    if 'Tier3' in tier:
        lam_h += 0.4
        lam_a += 0.4
    elif 'Tier2' in tier:
        lam_h += 0.3
        lam_a += 0.3
    elif 'Tier1' in tier and '例外' not in tier:
        lam_h += 0.15
        lam_a += 0.15
    
    # 规则63: 单关平局上修
    if m['single']:
        # 根据L032/L029: 残阵/碾压场不上修平局
        # 检查是否适用
        if m['value_diff'] >= 2.0 or '极残' in m.get('injuries_h', ''):
            # 碾压场或残阵场→不上修平局(L032)
            pass
        else:
            # 平局上修8-15%
            pass  # 在概率计算后应用
    
    # DC模型计算
    probs = calc_match_probs(lam_h, lam_a, rho=0.1)
    
    # 规则63: 单关平局上修(在模型概率上)
    if m['single'] and m['value_diff'] < 2.0 and '极残' not in m.get('injuries_h', ''):
        draw_prob = probs['draw']
        home_prob = probs['home_win']
        away_prob = probs['away_win']
        
        # 平局与首选差距
        max_prob = max(home_prob, away_prob)
        gap = max_prob - draw_prob
        
        if gap <= 0.10:
            upfix = 0.12
        elif gap <= 0.20:
            upfix = 0.10
        else:
            upfix = 0.08
        
        upfix = min(upfix, 0.15)
        probs['draw'] += upfix
        if home_prob > away_prob:
            probs['home_win'] -= upfix * 0.6
            probs['away_win'] -= upfix * 0.4
        else:
            probs['away_win'] -= upfix * 0.6
            probs['home_win'] -= upfix * 0.4
    
    # 置信度
    stars, conf = confidence_rating(
        [probs['home_win'], probs['draw'], probs['away_win']],
        m['shin_probs'],
        'medium'
    )
    
    # TTG推荐
    ttg = probs['ttg']
    ttg_recs = []
    for i in range(min(5, len(ttg))):
        ttg_recs.append((i, ttg[i]))
    ttg_recs.sort(key=lambda x: x[1], reverse=True)
    
    # 比分TOP5(规则62: 由推演决定, 模型校核)
    score_recs = probs['scores_top10'][:5]
    
    # 半全场TOP3
    hafu_recs = probs['hafu_top3']
    
    # 方向推荐
    if probs['home_win'] > probs['away_win'] and probs['home_win'] > probs['draw']:
        direction = '主胜'
        direction_2nd = '平局' if probs['draw'] > probs['away_win'] else '客胜'
    elif probs['away_win'] > probs['home_win'] and probs['away_win'] > probs['draw']:
        direction = '客胜'
        direction_2nd = '平局' if probs['draw'] > probs['home_win'] else '主胜'
    else:
        direction = '平局'
        direction_2nd = '主胜' if probs['home_win'] > probs['away_win'] else '客胜'
    
    results[num] = {
        **m,
        'lam_h_final': lam_h,
        'lam_a_final': lam_a,
        'probs': probs,
        'stars': stars,
        'confidence': conf,
        'direction': direction,
        'direction_2nd': direction_2nd,
        'ttg_top2': ttg_recs[:2],
        'scores_top5': score_recs,
        'hafu_top3': hafu_recs,
        'home_win_pct': round(probs['home_win'] * 100, 1),
        'draw_pct': round(probs['draw'] * 100, 1),
        'away_win_pct': round(probs['away_win'] * 100, 1),
    }

# ============ 输出结果摘要 ============

print("=" * 120)
print("周六2026-08-29 竞彩分析结果摘要（27场）")
print("=" * 120)
print()
for num in sorted(results.keys()):
    r = results[num]
    print(f"{r['league']:4s} 周六{num} | {r['home']:8s} vs {r['away']:8s} | "
          f"λ:{r['lam_h_final']:.1f}-{r['lam_a_final']:.1f} | "
          f"主{r['home_win_pct']:5.1f}% 平{r['draw_pct']:5.1f}% 客{r['away_win_pct']:5.1f}% | "
          f"方向:{r['direction']}({r['stars']}) | "
          f"TTG:{r['ttg_top2'][0][0]}/{r['ttg_top2'][1][0]}球 | "
          f"比分:{r['scores_top5'][0][0]}/{r['scores_top5'][1][0]} | "
          f"{'单关' if r['single'] else ''}")

# ============ 串关推荐 ============

print("\n" + "=" * 80)
print("串关推荐方案")
print("=" * 80)

# 方向串（稳健）
print("\n【方向串 A】（稳健）")
parlay_a = ['013', '020', '026']
for num in parlay_a:
    r = results[num]
    print(f"  周六{num} {r['home']} vs {r['away']}: {r['direction']} ({r['stars']})")

# 让球串
print("\n【让球串 B】（价值）")
parlay_b = ['020', '026', '018']
for num in parlay_b:
    r = results[num]
    print(f"  周六{num} {r['home']} vs {r['away']}: 让{r['goalLine']}球 {r['direction']}")

# 混合串
print("\n【混合串 C】")
parlay_c = ['013', '020', '026']
for num in parlay_c:
    r = results[num]
    print(f"  周六{num} {r['home']} vs {r['away']}: {r['direction']}")

# 娱乐串
print("\n【娱乐串 D】（混合）")
parlay_d = ['027', '020', '026']
for num in parlay_d:
    r = results[num]
    print(f"  周六{num} {r['home']} vs {r['away']}: 比分{r['scores_top5'][0][0]}")

# ============ 保存结果 ============

output = {
    'date': '2026-08-29',
    'weekday': '周六',
    'total_matches': len(results),
    'single_matches': [num for num, r in results.items() if r['single']],
    'matches': {},
    'parlays': {
        'A_方向串': parlay_a,
        'B_让球串': parlay_b,
        'C_混合串': parlay_c,
        'D_娱乐串': parlay_d,
    }
}

for num, r in results.items():
    output['matches'][num] = {
        'league': r['league'],
        'home': r['home'],
        'away': r['away'],
        'time': r['time'],
        'single': r['single'],
        'lambda_h': round(r['lam_h_final'], 2),
        'lambda_a': round(r['lam_a_final'], 2),
        'home_win': r['home_win_pct'],
        'draw': r['draw_pct'],
        'away_win': r['away_win_pct'],
        'direction': r['direction'],
        'direction_2nd': r['direction_2nd'],
        'confidence': r['confidence'],
        'stars': r['stars'],
        'ttg_top2': [r['ttg_top2'][0][0], r['ttg_top2'][1][0]],
        'scores_top5': [s[0] for s in r['scores_top5']],
        'hafu_top3': [h[0] for h in r['hafu_top3']],
        'goalLine': r['goalLine'],
        'value_diff': r['value_diff'],
        'h2h': r['h2h'],
        'injuries_h': r['injuries_h'],
        'injuries_a': r['injuries_a'],
        'context': r['context'],
    }

with open(r'e:\VibeCoding\football\reports\data\260829_analysis_results.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n分析结果已保存到: reports/data/260829_analysis_results.json")
print(f"共分析 {len(results)} 场比赛")
