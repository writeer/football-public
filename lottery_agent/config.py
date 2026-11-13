# -*- coding: utf-8 -*-
"""
竞彩Agent全局配置与常量
"""

# ==================== 模型权重配置 ====================
# 注意：MODEL_WEIGHTS 含 shin/public 等市场项，仅用于探索性对照。
# 规则79 要求概率融合只允许基本面模型，实际融合请使用 FUNDAMENTAL_MODEL_WEIGHTS。
MODEL_WEIGHTS = {
    'dc_nb_zip': 0.35,    # Dixon-Coles/负二项/ZIP 均值
    'skellam': 0.15,      # Skellam进球差
    'elo_pi': 0.15,       # Elo/Pi评级
    'shin': 0.15,         # Shin赔率校准（市场，禁止进入规则79融合）
    'public': 0.10,       # 网友/公众意见（市场，禁止进入规则79融合）
    'ai_opta': 0.05,      # AI模型
    'ordinal': 0.05,      # 有序逻辑回归
}

# 规则79 合规融合权重：全部来自基本面/历史数据，无市场项
FUNDAMENTAL_MODEL_WEIGHTS = {
    'dc_nb_zip': 0.55,
    'skellam': 0.20,
    'elo_pi': 0.20,
    'ordinal': 0.05,
}

# 比分融合权重
SCORE_WEIGHTS = {
    'dc': 0.40,
    'nb': 0.30,
    'zip': 0.15,
    'mc': 0.15,
}

# ==================== Dixon-Coles默认参数 ====================
DC_RHO_DEFAULT = -0.13          # 低比分修正参数
DC_TIME_DECAY_XI = 0.003        # 时间衰减速率
HT_RATIO_DEFAULT = 0.42         # 上半场进球占比

# ==================== 联赛基准参数 ====================
LEAGUE_PROFILES = {
    '英超': {'avg_goals': 2.65, 'vmr': 1.15, 'home_advantage': 1.35, 'defensive': False, 'over_dispersed': False},
    '西甲': {'avg_goals': 2.50, 'vmr': 1.10, 'home_advantage': 1.38, 'defensive': False, 'over_dispersed': False},
    '德甲': {'avg_goals': 2.85, 'vmr': 1.35, 'home_advantage': 1.32, 'defensive': False, 'over_dispersed': True},
    '意甲': {'avg_goals': 2.35, 'vmr': 1.05, 'home_advantage': 1.40, 'defensive': True, 'over_dispersed': False},
    '法甲': {'avg_goals': 2.30, 'vmr': 1.08, 'home_advantage': 1.38, 'defensive': True, 'over_dispersed': False},
    '荷甲': {'avg_goals': 3.10, 'vmr': 1.45, 'home_advantage': 1.30, 'defensive': False, 'over_dispersed': True},
    '葡超': {'avg_goals': 2.45, 'vmr': 1.12, 'home_advantage': 1.42, 'defensive': False, 'over_dispersed': False},
    '英冠': {'avg_goals': 2.55, 'vmr': 1.18, 'home_advantage': 1.33, 'defensive': False, 'over_dispersed': False},
    '瑞超': {'avg_goals': 2.60, 'vmr': 1.20, 'home_advantage': 1.35, 'defensive': False, 'over_dispersed': False},
    '挪超': {'avg_goals': 2.80, 'vmr': 1.30, 'home_advantage': 1.32, 'defensive': False, 'over_dispersed': True},
    '日职': {'avg_goals': 2.45, 'vmr': 1.10, 'home_advantage': 1.35, 'defensive': False, 'over_dispersed': False},
    '韩K': {'avg_goals': 2.35, 'vmr': 1.08, 'home_advantage': 1.38, 'defensive': True, 'over_dispersed': False},
    '美职': {'avg_goals': 2.90, 'vmr': 1.25, 'home_advantage': 1.28, 'defensive': False, 'over_dispersed': False},
    '巴甲': {'avg_goals': 2.45, 'vmr': 1.10, 'home_advantage': 1.35, 'defensive': False, 'over_dispersed': False},
    '芬超': {'avg_goals': 2.55, 'vmr': 1.15, 'home_advantage': 1.40, 'defensive': False, 'over_dispersed': False},
    '法乙': {'avg_goals': 2.58, 'vmr': 1.12, 'home_advantage': 1.41, 'defensive': True, 'over_dispersed': False},
    # 欧冠：2026-10-21 规则80，当季联赛阶段实测4.16球/场（45场），收缩30% → 3.9；淘汰赛恢复2.55
    '欧冠': {'avg_goals': 3.9, 'vmr': 1.12, 'home_advantage': 1.25, 'defensive': False, 'over_dispersed': False},
    '欧联': {'avg_goals': 2.50, 'vmr': 1.15, 'home_advantage': 1.28, 'defensive': False, 'over_dispersed': False},
    '世界杯': {'avg_goals': 2.41, 'vmr': 1.08, 'home_advantage': 1.15, 'defensive': False, 'over_dispersed': False},
    '欧洲杯': {'avg_goals': 2.35, 'vmr': 1.05, 'home_advantage': 1.18, 'defensive': False, 'over_dispersed': False},
    '美洲杯': {'avg_goals': 2.40, 'vmr': 1.10, 'home_advantage': 1.20, 'defensive': False, 'over_dispersed': False},
    'default': {'avg_goals': 2.50, 'vmr': 1.12, 'home_advantage': 1.35, 'defensive': False, 'over_dispersed': False},
}

# ==================== 空场/中立场主场加成覆盖（规则72，第一级别） ====================
# 来源：2026-08-09 本菲卡 vs 维塞乌（空场执行处罚 → 碾压局 2-2 爆 9 倍冷平）
#       2026-09-28 罗马尼亚 vs 波黑（欧足联空场处罚 → 2-4 被爆冷）
STADIUM_STATUSES = ('正常', '空场', '部分关闭', '中立场')
PARTIAL_CLOSURE_THRESHOLD = 0.30     # 关闭座位比例阈值
PARTIAL_CLOSURE_HIGH_FACTOR = 0.50   # 关闭比例≥30% → 主场加成部分折半
PARTIAL_CLOSURE_LOW_FACTOR = 0.85    # 关闭比例<30%  → 主场加成部分×0.85
NEUTRAL_VENUE_FACTOR = 1.0           # 空场/中立场 → 乘数置1.0（完全撤回首场优势）


def resolve_home_advantage(league, stadium_status='正常', closure_ratio=None):
    """
    规则72：按场地状态解析主场加成乘数。

    返回 dict:
      - factor:           用于替换联赛 home_advantage 的乘数
      - override_applied: 是否触发覆盖（True 时模型须以 factor 替换联赛基准）
      - crush_allowed:    是否允许判定为"碾压局"（空场/中立场=False）
      - note:             说明

    口径说明（"加成部分"口径，非乘数本身）：
      正常          → factor = 联赛基准
      空场 / 中立场 → factor = 1.0（完全撤回）
      部分关闭≥30%  → factor = 1 + (基准-1) × 0.50
      部分关闭<30%  → factor = 1 + (基准-1) × 0.85
    """
    base = LEAGUE_PROFILES.get(league, LEAGUE_PROFILES['default'])['home_advantage']
    status = stadium_status or '正常'

    if status == '正常':
        return {'factor': base, 'override_applied': False,
                'crush_allowed': True, 'note': '正常开放观众，按联赛基准'}

    if status in ('空场', '中立场'):
        return {'factor': NEUTRAL_VENUE_FACTOR, 'override_applied': True,
                'crush_allowed': False,
                'note': f'{status}：撤回首场优势(乘数置1.0)，且禁止判定为碾压局'}

    if status == '部分关闭':
        ratio = closure_ratio if closure_ratio is not None else 1.0
        boost = base - 1.0
        part = (PARTIAL_CLOSURE_HIGH_FACTOR if ratio >= PARTIAL_CLOSURE_THRESHOLD
                else PARTIAL_CLOSURE_LOW_FACTOR)
        factor = 1.0 + boost * part
        return {'factor': factor, 'override_applied': True, 'crush_allowed': True,
                'note': f'部分关闭(关闭比例{ratio:.0%})：主场加成部分×{part:.2f} → {factor:.4f}'}

    return {'factor': base, 'override_applied': False, 'crush_allowed': True,
            'note': f'未知 stadium_status="{status}"，按正常处理'}


# ==================== 伤停影响系数 ====================
INJURY_IMPACT = {
    'core': {'attack_mult': 0.80, 'defense_mult': 0.85, 'log_lambda_adj': -0.25},      # 核心（身价前5/队长/射手王）
    'key': {'attack_mult': 0.90, 'defense_mult': 0.92, 'log_lambda_adj': -0.15},       # 主力
    'rotation': {'attack_mult': 0.97, 'defense_mult': 0.98, 'log_lambda_adj': -0.05},  # 轮换
    'bench': {'attack_mult': 1.00, 'defense_mult': 1.00, 'log_lambda_adj': 0.00},      # 替补
}

# ==================== 置信度评级阈值 ====================
CONFIDENCE_THRESHOLDS = {
    'high': 3,      # 综合得分>=3 → 高置信度
    'medium': 1,    # 1~2 → 中置信度
    'low': 0,       # 0 → 低置信度
    'very_low': -999,  # <0 → 极低
}

PROBABILITY_THRESHOLDS = {
    'high': 0.55,
    'medium': 0.45,
    'low': 0.35,
}

# ==================== 串关配置 ====================
PARLAY_CONFIG = {
    'max_matches': 8,           # 最大串关场数
    'min_confidence_for_parlay': 1,  # 参与串关的最小置信度（中置信度）
    'conservative_threshold': 0.55,  # 稳健串关概率阈值
    'aggressive_threshold': 0.45,    # 激进串关概率阈值
}

# ==================== 蒙特卡洛配置 ====================
MONTE_CARLO_CONFIG = {
    'n_simulations': 10000,
    'random_seed': 2026,
    'max_goals': 8,
}

# ==================== 报告配置 ====================
REPORT_CONFIG = {
    'top_scores': 10,       # 显示前N个比分
    'top_htft': 5,          # 显示前N个半全场
    'show_divergence_threshold': 0.15,  # 模型与市场分歧>15%时标注
}

# ==================== 历史交锋心理权重配置 ====================
H2H_PSYCHOLOGY_CONFIG = {
    'weight_in_fusion': 0.06,       # 在加权融合中的权重（与AI/OptA同级）
    'time_decay_half_life': 365,    # 时间衰减半衰期（天）
    'min_matches': 3,               # 最少有效交锋场数
    'max_lambda_adjust': 0.15,      # lambda最大调整幅度（±15%）
    'suppression_threshold': 3,     # 连续压制触发阈值（场）
    'clean_sheet_threshold': 2,     # 连续零封触发阈值（场）
    'venue_reversal_threshold': 0.6, # 主场优势反转阈值（主场胜率<此值）
    'goal_trend_threshold': 0.3,    # 进球趋势显著阈值
}

# ==================== 高山流水验证配置 ====================
GAOSHAN_CONFIG = {
    'data_path': 'gaoshan_parsed_matches.json',
    'stats_path': 'gaoshan_stats.json',
    'min_samples_for_league': 20,  # 联赛最少样本数才使用统计
    'confidence_boost_when_aligned': 1,  # 方向一致时置信度+1
    'confidence_penalty_when_contradict': -1,  # 方向矛盾时置信度-1
}

# ==================== 颜色配置（HTML报告） ====================
COLORS = {
    'primary': '#1a73e8',
    'success': '#34a853',
    'warning': '#fbbc04',
    'danger': '#ea4335',
    'info': '#4285f4',
    'text': '#202124',
    'text_secondary': '#5f6368',
    'bg': '#f8f9fa',
    'border': '#dadce0',
}
