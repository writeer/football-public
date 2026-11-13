# -*- coding: utf-8 -*-
"""
竞彩Agent — 数学模型库
整合 Dixon-Coles / 负二项 / ZIP / Skellam / 蒙特卡洛 / 赔率校准
"""

import numpy as np
from scipy import stats
from scipy.optimize import brentq
from scipy.special import comb
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

from .config import (
    DC_RHO_DEFAULT, MONTE_CARLO_CONFIG, LEAGUE_PROFILES, HT_RATIO_DEFAULT
)


# ============================================================
# 1. Dixon-Coles 修正泊松模型
# ============================================================

class DixonColesModel:
    """Dixon-Coles 修正泊松模型 — 足彩工业标准"""

    def __init__(self, rho=DC_RHO_DEFAULT):
        self.rho = rho
        self.max_goals = MONTE_CARLO_CONFIG['max_goals']

    def tau(self, h, a, lambda_h, lambda_a):
        """低比分膨胀系数"""
        if h == 0 and a == 0:
            return 1 - lambda_h * lambda_a * self.rho
        elif h == 0 and a == 1:
            return 1 + lambda_h * self.rho
        elif h == 1 and a == 0:
            return 1 + lambda_a * self.rho
        elif h == 1 and a == 1:
            return 1 - self.rho
        return 1.0

    def score_prob(self, h, a, lambda_h, lambda_a):
        """单场比分概率"""
        tau_val = self.tau(h, a, lambda_h, lambda_a)
        p_h = stats.poisson.pmf(h, lambda_h)
        p_a = stats.poisson.pmf(a, lambda_a)
        return max(p_h * p_a * tau_val, 0)

    def compute_matrix(self, lambda_h, lambda_a):
        """生成完整比分概率矩阵"""
        max_g = self.max_goals
        matrix = np.zeros((max_g, max_g))
        for i in range(max_g):
            for j in range(max_g):
                matrix[i, j] = self.score_prob(i, j, lambda_h, lambda_a)
        # 归一化
        total = matrix.sum()
        if total > 0:
            matrix /= total
        return matrix

    def outcome_probs(self, lambda_h, lambda_a):
        """胜平负概率"""
        mat = self.compute_matrix(lambda_h, lambda_a)
        home_win = sum(mat[i, j] for i in range(self.max_goals) for j in range(self.max_goals) if i > j)
        draw = sum(mat[i, i] for i in range(self.max_goals))
        away_win = 1 - home_win - draw
        return {'home': home_win, 'draw': draw, 'away': away_win}

    def top_scores(self, lambda_h, lambda_a, n=10):
        """Top N 比分及概率"""
        mat = self.compute_matrix(lambda_h, lambda_a)
        scores = []
        for i in range(self.max_goals):
            for j in range(self.max_goals):
                scores.append((i, j, mat[i, j]))
        scores.sort(key=lambda x: -x[2])
        return scores[:n]


# ============================================================
# 2. 负二项分布模型
# ============================================================

class NegativeBinomialModel:
    """负二项分布 — 过离散联赛首选"""

    def __init__(self, gamma_disp=0.10):
        self.gamma_disp = gamma_disp
        self.max_goals = MONTE_CARLO_CONFIG['max_goals']

    def pmf(self, x, mu):
        """负二项PMF"""
        alpha = 1.0 / (self.gamma_disp * mu) if mu > 0 else 1e6
        p = alpha / (alpha + mu)
        return stats.nbinom.pmf(x, alpha, p)

    def compute_matrix(self, lambda_h, lambda_a):
        """生成比分概率矩阵"""
        max_g = self.max_goals
        matrix = np.zeros((max_g, max_g))
        for i in range(max_g):
            for j in range(max_g):
                p_h = self.pmf(i, lambda_h)
                p_a = self.pmf(j, lambda_a)
                matrix[i, j] = p_h * p_a
        total = matrix.sum()
        if total > 0:
            matrix /= total
        return matrix

    def outcome_probs(self, lambda_h, lambda_a):
        """胜平负概率"""
        max_g = self.max_goals
        mat = self.compute_matrix(lambda_h, lambda_a)
        home_win = sum(mat[i, j] for i in range(max_g) for j in range(max_g) if i > j)
        draw = sum(mat[i, i] for i in range(max_g))
        away_win = 1 - home_win - draw
        return {'home': home_win, 'draw': draw, 'away': away_win}

    def top_scores(self, lambda_h, lambda_a, n=10):
        """Top N 比分"""
        mat = self.compute_matrix(lambda_h, lambda_a)
        scores = []
        for i in range(self.max_goals):
            for j in range(self.max_goals):
                scores.append((i, j, mat[i, j]))
        scores.sort(key=lambda x: -x[2])
        return scores[:n]


# ============================================================
# 3. ZIP / ZINB 零膨胀模型
# ============================================================

class ZIPModel:
    """零膨胀泊松 — 防守型联赛神器"""

    def __init__(self, phi_home=0.05, phi_away=0.05):
        self.phi_home = phi_home
        self.phi_away = phi_away
        self.max_goals = MONTE_CARLO_CONFIG['max_goals']

    def pmf(self, x, lambda_zip, phi):
        """ZIP PMF"""
        if x == 0:
            return phi + (1 - phi) * stats.poisson.pmf(0, lambda_zip)
        return (1 - phi) * stats.poisson.pmf(x, lambda_zip)

    def compute_matrix(self, lambda_h, lambda_a):
        """生成比分概率矩阵"""
        max_g = self.max_goals
        matrix = np.zeros((max_g, max_g))
        for i in range(max_g):
            for j in range(max_g):
                p_h = self.pmf(i, lambda_h, self.phi_home)
                p_a = self.pmf(j, lambda_a, self.phi_away)
                matrix[i, j] = p_h * p_a
        total = matrix.sum()
        if total > 0:
            matrix /= total
        return matrix

    def outcome_probs(self, lambda_h, lambda_a):
        """胜平负概率"""
        mat = self.compute_matrix(lambda_h, lambda_a)
        home_win = sum(mat[i, j] for i in range(self.max_goals) for j in range(self.max_goals) if i > j)
        draw = sum(mat[i, i] for i in range(self.max_goals))
        away_win = 1 - home_win - draw
        return {'home': home_win, 'draw': draw, 'away': away_win}

    def top_scores(self, lambda_h, lambda_a, n=10):
        """Top N 比分"""
        mat = self.compute_matrix(lambda_h, lambda_a)
        scores = []
        for i in range(self.max_goals):
            for j in range(self.max_goals):
                scores.append((i, j, mat[i, j]))
        scores.sort(key=lambda x: -x[2])
        return scores[:n]


# ============================================================
# 4. Skellam 进球差模型
# ============================================================

class SkellamModel:
    """Skellam分布 — 直接预测进球差"""

    def outcome_probs(self, lambda_h, lambda_a):
        """胜平负概率"""
        home = stats.skellam.sf(0, lambda_h, lambda_a)
        draw = stats.skellam.pmf(0, lambda_h, lambda_a)
        away = 1 - home - draw
        return {'home': home, 'draw': draw, 'away': away}

    def goal_diff_probs(self, lambda_h, lambda_a, diff_range=4):
        """进球差概率分布"""
        result = {}
        for d in range(-diff_range, diff_range + 1):
            p = stats.skellam.pmf(d, lambda_h, lambda_a)
            if d > 0:
                result[f'主+{d}'] = p
            elif d == 0:
                result['平'] = p
            else:
                result[f'客{abs(d)}'] = p
        return result


# ============================================================
# 5. 蒙特卡洛模拟
# ============================================================

class MonteCarloSimulator:
    """蒙特卡洛模拟 — 10000场随机模拟"""

    def __init__(self, n_sim=None, seed=None):
        self.n_sim = n_sim or MONTE_CARLO_CONFIG['n_simulations']
        self.seed = seed or MONTE_CARLO_CONFIG['random_seed']
        np.random.seed(self.seed)

    def negbin_sample(self, mu, gamma_disp, n):
        """负二项采样"""
        r = 1.0 / (gamma_disp * mu) if mu > 0 else 1e6
        p = r / (r + mu)
        return np.random.negative_binomial(r, p, n)

    def simulate(self, lambda_h, lambda_a, gamma_disp=0.10, use_nb=True):
        """运行模拟"""
        if use_nb:
            home_goals = self.negbin_sample(lambda_h, gamma_disp, self.n_sim)
            away_goals = self.negbin_sample(lambda_a, gamma_disp, self.n_sim)
        else:
            home_goals = np.random.poisson(lambda_h, self.n_sim)
            away_goals = np.random.poisson(lambda_a, self.n_sim)

        home_win = np.sum(home_goals > away_goals) / self.n_sim
        draw = np.sum(home_goals == away_goals) / self.n_sim
        away_win = np.sum(home_goals < away_goals) / self.n_sim

        total_goals = home_goals + away_goals
        under_25 = np.sum(total_goals < 2.5) / self.n_sim
        over_25 = 1 - under_25

        # 比分频率
        score_counts = Counter(zip(home_goals.tolist(), away_goals.tolist()))
        top_scores = sorted(score_counts.items(), key=lambda x: -x[1])[:10]

        # 总进球分布
        goal_dist = {}
        for g in range(8):
            goal_dist[g] = np.sum(total_goals == g) / self.n_sim
        goal_dist['7+'] = np.sum(total_goals >= 7) / self.n_sim

        return {
            'home_win': home_win,
            'draw': draw,
            'away_win': away_win,
            'over_25': over_25,
            'under_25': under_25,
            'top_scores': top_scores,
            'goal_distribution': goal_dist,
            'home_mean': home_goals.mean(),
            'away_mean': away_goals.mean(),
        }


# ============================================================
# 6. 赔率校准模型
# ============================================================

class OddsCalibrator:
    """赔率校准 — Shin模型 / Power去水 / 归一化"""

    def __init__(self, odds_home, odds_draw, odds_away):
        self.odds = {'home': odds_home, 'draw': odds_draw, 'away': odds_away}
        self.raw_probs = {k: 1.0 / v for k, v in self.odds.items()}
        self.overround = sum(self.raw_probs.values())

    def normalize(self):
        """归一化去水"""
        return {k: v / self.overround for k, v in self.raw_probs.items()}

    def shin(self):
        """Shin模型去水"""
        raw = np.array([self.raw_probs['home'], self.raw_probs['draw'], self.raw_probs['away']])

        def equation(z):
            if z <= 0 or z >= 1:
                return 999
            denom = 2 * (1 - z)
            if denom == 0:
                return 999
            probs = (np.sqrt(z**2 + 4 * (1 - z) * raw) - z) / denom
            return probs.sum() - 1.0

        try:
            z_sol = brentq(equation, 1e-6, 0.99, xtol=1e-12)
            denom = 2 * (1 - z_sol)
            probs = (np.sqrt(z_sol**2 + 4 * (1 - z_sol) * raw) - z_sol) / denom
            if probs.sum() > 1.05 or any(p < 0 for p in probs):
                raise ValueError("Shin unconverged")
            return {'home': probs[0], 'draw': probs[1], 'away': probs[2], 'z': z_sol}
        except Exception:
            # fallback to normalize
            norm = self.normalize()
            return {'home': norm['home'], 'draw': norm['draw'], 'away': norm['away'], 'z': 0.07}

    def power(self, k=0.6):
        """Power去水"""
        raw_vals = [self.raw_probs['home'], self.raw_probs['draw'], self.raw_probs['away']]
        powered = [v ** k for v in raw_vals]
        total = sum(powered)
        return {'home': powered[0]/total, 'draw': powered[1]/total, 'away': powered[2]/total}

    def all_methods(self):
        """返回所有校准方法结果"""
        return {
            'raw': self.raw_probs,
            'normalize': self.normalize(),
            'shin': self.shin(),
            'power': self.power(),
            'overround': self.overround,
            'margin': (self.overround - 1) * 100,
        }

    def ev(self, model_probs):
        """期望值计算"""
        shin_probs = self.shin()
        ev = {}
        for outcome in ['home', 'draw', 'away']:
            p = shin_probs[outcome]
            o = self.odds[outcome]
            ev[outcome] = p * o - 1
        return ev


# ============================================================
# 7. Elo/Pi 评级计算
# ============================================================

class TeamRating:
    """球队实力评级 — Elo + Pi + TrueSkill"""

    def __init__(self, league='default', home_advantage_override=None):
        self.profile = LEAGUE_PROFILES.get(league, LEAGUE_PROFILES['default'])
        self.league_avg = self.profile['avg_goals']
        self.league_per_side = self.league_avg / 2
        # 规则72（第一级别）：空场/中立场/部分关闭时以 override 替换联赛主场加成基准。
        # override=None 表示正常，使用联赛基准（保持既有行为不变）。
        self.home_advantage_override = home_advantage_override
        self.home_advantage = (
            self.profile['home_advantage']
            if home_advantage_override is None
            else float(home_advantage_override)
        )

    def elo_rating(self, team_data, opponent_data, is_home=True):
        """
        计算Elo评分
        team_data: {avg_scored, avg_conceded, fifa_rank, matches}
        """
        base = 2000
        score_adj = (team_data.get('avg_scored', 1.2) - self.league_per_side) * 40
        defense_adj = -(team_data.get('avg_conceded', 1.2) - self.league_per_side) * 30
        rank_adj = (10 - min(team_data.get('fifa_rank', 50), 50)) * 2

        elo = base + score_adj + defense_adj + rank_adj
        return max(elo, 1200)

    def elo_probs(self, elo_home, elo_away):
        """Elo差转胜率"""
        delta = elo_home - elo_away
        p_home = 1.0 / (1.0 + 10 ** (-delta / 400))
        # 给平局分配概率
        draw_factor = 0.26 * (1 - abs(p_home - 0.5) * 2)
        p_draw = draw_factor
        p_away = 1 - p_home - p_draw
        return {'home': p_home, 'draw': p_draw, 'away': max(p_away, 0)}

    def pi_rating(self, team_data):
        """Pi攻防分离评分 - 相对于联赛均值的强度系数"""
        league_per_side = self.league_avg / 2
        attack = team_data.get('avg_scored', league_per_side) / league_per_side
        defense = team_data.get('avg_conceded', league_per_side) / league_per_side
        return {'attack': attack, 'defense': defense}

    def pi_lambda(self, home_data, away_data):
        """Pi评分转期望进球 - 标准Dixon-Coles乘法方法"""
        pi_h = self.pi_rating(home_data)
        pi_a = self.pi_rating(away_data)

        league_per_side = self.league_avg / 2

        # 标准Dixon-Coles: lambda = 攻击强度 × 对手防守强度 × 联赛基准 × 主场优势
        # 规则72：self.home_advantage 已含空场/中立场覆盖（正常时等于联赛基准）
        lambda_h = pi_h['attack'] * pi_a['defense'] * league_per_side * self.home_advantage
        lambda_a = pi_a['attack'] * pi_h['defense'] * league_per_side

        # 限制在合理范围 (0.3 - 4.0)
        lambda_h = min(max(lambda_h, 0.3), 4.0)
        lambda_a = min(max(lambda_a, 0.3), 4.0)

        return lambda_h, lambda_a


# ============================================================
# 8. 半全场预测
# ============================================================

class HTFTModel:
    """半全场胜平负预测"""

    def __init__(self, dc_model=None, ht_ratio=None):
        self.dc = dc_model or DixonColesModel()
        self.ht_ratio = HT_RATIO_DEFAULT if ht_ratio is None else ht_ratio

    def predict(self, lambda_h, lambda_a, rho=-0.13, n=5):
        """预测半全场 Top N（全比分区间求和后归一化，避免截断丢尾）"""
        lambda_ht_h = lambda_h * self.ht_ratio
        lambda_ht_a = lambda_a * self.ht_ratio
        lambda_lt_h = lambda_h - lambda_ht_h
        lambda_lt_a = lambda_a - lambda_ht_a

        max_g = self.dc.max_goals
        ht_p = np.zeros((max_g, max_g))
        for ht_h in range(max_g):
            for ht_a in range(max_g):
                ht_p[ht_h, ht_a] = self.dc.score_prob(ht_h, ht_a, lambda_ht_h, lambda_ht_a)
        lt_p_h = stats.poisson.pmf(np.arange(max_g), lambda_lt_h)
        lt_p_a = stats.poisson.pmf(np.arange(max_g), lambda_lt_a)

        htft_results = {}
        for ht_h in range(max_g):
            for ht_a in range(max_g):
                p_ht = ht_p[ht_h, ht_a]
                if p_ht <= 0:
                    continue
                ht_result = 'H' if ht_h > ht_a else ('D' if ht_h == ht_a else 'A')
                for lt_h in range(max_g):
                    if lt_p_h[lt_h] <= 0:
                        continue
                    for lt_a in range(max_g):
                        if lt_p_a[lt_a] <= 0:
                            continue
                        ft_h = ht_h + lt_h
                        ft_a = ht_a + lt_a
                        ft_result = 'H' if ft_h > ft_a else ('D' if ft_h == ft_a else 'A')
                        key = f"{ht_result}/{ft_result}"
                        htft_results[key] = htft_results.get(key, 0) + p_ht * lt_p_h[lt_h] * lt_p_a[lt_a]

        total = sum(htft_results.values())
        if total <= 0:
            return []
        result_labels = {'H': '主', 'D': '平', 'A': '客'}
        sorted_results = sorted(htft_results.items(), key=lambda x: -x[1])

        formatted = []
        for key, prob in sorted_results[:n]:
            ht_label = result_labels[key[0]]
            ft_label = result_labels[key[2]]
            formatted.append({
                'htft': f"{ht_label}-{ft_label}",
                'code': key,
                'probability': prob / total,
            })
        return formatted


# ============================================================
# 9. 联赛诊断
# ============================================================

class LeagueDiagnosis:
    """联赛诊断 — VMR检测 + 零膨胀检测"""

    def diagnose(self, league='default'):
        """诊断联赛特征"""
        profile = LEAGUE_PROFILES.get(league, LEAGUE_PROFILES['default'])
        vmr = profile['vmr']
        avg_goals = profile['avg_goals']

        # 0-0频率估算
        p_00_poisson = stats.poisson.pmf(0, avg_goals / 2) ** 2
        actual_00 = p_00_poisson * 1.3  # 实际通常略高于泊松理论

        # VMR判断
        if vmr <= 1.05:
            vmr_conclusion = "标准泊松基本适用"
            primary_model = "DC"
        elif vmr <= 1.2:
            vmr_conclusion = "轻微过离散，DC模型优先"
            primary_model = "DC"
        elif vmr <= 1.5:
            vmr_conclusion = "明显过离散，负二项必备"
            primary_model = "NB"
        else:
            vmr_conclusion = "严重过离散，负二项+广义泊松"
            primary_model = "NB"

        # 零膨胀判断
        if actual_00 < 0.05:
            zip_conclusion = "不需要零膨胀"
            use_zip = False
        elif actual_00 < 0.10:
            zip_conclusion = "ZIP可选"
            use_zip = False
        elif actual_00 < 0.15:
            zip_conclusion = "推荐启用ZIP"
            use_zip = True
        else:
            zip_conclusion = "必须启用ZIP+ZINB"
            use_zip = True

        return {
            'league': league,
            'vmr': vmr,
            'vmr_conclusion': vmr_conclusion,
            'primary_model': primary_model,
            'avg_goals': avg_goals,
            'estimated_00_rate': actual_00,
            'zip_conclusion': zip_conclusion,
            'use_zip': use_zip,
            'home_advantage': profile['home_advantage'],
            'defensive': profile['defensive'],
            'over_dispersed': profile['over_dispersed'],
        }

# ============================================================
# 10. 历史交锋心理权重模型
# ============================================================

class H2HPsychology:
    """
    历史交锋心理权重模型 — 基于枫桥东/万中足球策略的心理层分析
    
    核心假设：历史交锋中形成的规律不只是数据巧合，会产生真实的心理压制效应：
    - 方向压制：连续N场同一方获胜 → 被压制方信心下降
    - 零封压制：连续被零封 → 进攻方焦虑/防守方信心上升
    - 主场优势反转：交锋中主场反而劣势 → 主场心理阴影
    - 进球趋势：交锋中持续低进球 → 双方趋于保守
    """

    def __init__(self, config=None):
        from .config import H2H_PSYCHOLOGY_CONFIG
        self.cfg = config or H2H_PSYCHOLOGY_CONFIG

    def compute(self, h2h_history):
        """
        计算历史交锋心理权重
        
        h2h_history: list of dict, each with:
            - home_goals: int (当前分析的主队进球)
            - away_goals: int (当前分析的客队进球)
            - date: str or datetime (比赛日期，用于时间衰减)
            - venue: 'home' or 'away' (当前主队在该场是主场还是客场)
            
        Returns: dict with:
            - lambda_home_adj: float (主队lambda调整系数，1.0=无调整)
            - lambda_away_adj: float (客队lambda调整系数)
            - outcome_bias: {'home': float, 'draw': float, 'away': float} (概率偏向修正)
            - psychology_notes: list[str] (心理分析注释)
            - strength: float (心理效应强度 0-1)
            - raw_signals: dict (原始信号详情)
        """
        if not h2h_history or len(h2h_history) < self.cfg['min_matches']:
            return self._neutral_result("交锋样本不足，跳过心理权重")

        # 按时间排序（新→旧）
        matches = sorted(h2h_history, key=lambda x: x.get('date', ''), reverse=True)
        
        # 1. 计算时间衰减权重
        weights = self._time_decay_weights([m.get('date', '') for m in matches])
        
        # 2. 方向压制分析
        suppression = self._direction_suppression(matches, weights)
        
        # 3. 零封压制分析
        clean_sheet = self._clean_sheet_suppression(matches, weights)
        
        # 4. 主场优势反转
        venue_bias = self._home_away_bias(matches, weights)
        
        # 5. 进球趋势
        goal_trend = self._goal_trend(matches, weights)
        
        # 6. 综合lambda调整
        lambda_home_adj = 1.0
        lambda_away_adj = 1.0
        
        # 方向压制 → 被压制方进攻信心下降
        if suppression['strength'] > 0:
            if suppression['dominant_side'] == 'home':
                lambda_away_adj *= (1 - suppression['strength'] * self.cfg['max_lambda_adjust'])
                lambda_home_adj *= (1 + suppression['strength'] * self.cfg['max_lambda_adjust'] * 0.5)
            else:
                lambda_home_adj *= (1 - suppression['strength'] * self.cfg['max_lambda_adjust'])
                lambda_away_adj *= (1 + suppression['strength'] * self.cfg['max_lambda_adjust'] * 0.5)
        
        # 零封压制 → 被零封方进攻lambda下修
        if clean_sheet['strength'] > 0:
            if clean_sheet['victim'] == 'home':
                lambda_home_adj *= (1 - clean_sheet['strength'] * self.cfg['max_lambda_adjust'] * 0.7)
            else:
                lambda_away_adj *= (1 - clean_sheet['strength'] * self.cfg['max_lambda_adjust'] * 0.7)
        
        # 主场优势反转 → 主场lambda下修
        if venue_bias['reversal']:
            lambda_home_adj *= (1 - venue_bias['strength'] * self.cfg['max_lambda_adjust'] * 0.6)
        
        # 进球趋势 → 低进球趋势双方lambda下修
        if goal_trend['low_goal_trend']:
            adj = goal_trend['strength'] * self.cfg['max_lambda_adjust'] * 0.4
            lambda_home_adj *= (1 - adj)
            lambda_away_adj *= (1 - adj)
        
        # 确保lambda为正
        lambda_home_adj = max(lambda_home_adj, 0.85)
        lambda_away_adj = max(lambda_away_adj, 0.85)
        lambda_home_adj = min(lambda_home_adj, 1.15)
        lambda_away_adj = min(lambda_away_adj, 1.15)
        
        # 7. 计算outcome_bias（作为独立信号源）
        outcome_bias = self._compute_outcome_bias(
            suppression, clean_sheet, venue_bias, goal_trend
        )
        
        # 8. 心理效应总强度
        strength = max(
            suppression['strength'],
            clean_sheet['strength'] * 0.8,
            venue_bias['strength'] * 0.7,
            goal_trend['strength'] * 0.5
        )
        
        # 9. 生成注释
        notes = self._generate_notes(suppression, clean_sheet, venue_bias, goal_trend)
        
        return {
            'lambda_home_adj': round(lambda_home_adj, 4),
            'lambda_away_adj': round(lambda_away_adj, 4),
            'outcome_bias': {k: round(v, 4) for k, v in outcome_bias.items()},
            'psychology_notes': notes,
            'strength': round(strength, 4),
            'raw_signals': {
                'suppression': suppression,
                'clean_sheet': clean_sheet,
                'venue_bias': venue_bias,
                'goal_trend': goal_trend,
            }
        }

    def _neutral_result(self, reason):
        """返回中性结果"""
        return {
            'lambda_home_adj': 1.0,
            'lambda_away_adj': 1.0,
            'outcome_bias': {'home': 0.333, 'draw': 0.333, 'away': 0.333},
            'psychology_notes': [reason],
            'strength': 0.0,
            'raw_signals': {},
        }

    def _time_decay_weights(self, dates):
        """计算时间衰减权重（指数衰减）"""
        import datetime
        try:
            # 解析日期
            parsed = []
            for d in dates:
                if isinstance(d, datetime.datetime):
                    parsed.append(d)
                elif isinstance(d, str) and len(d) >= 10:
                    parsed.append(datetime.datetime.strptime(d[:10], '%Y-%m-%d'))
                else:
                    parsed.append(datetime.datetime.now())
            
            most_recent = max(parsed)
            half_life = self.cfg['time_decay_half_life']
            weights = []
            for p in parsed:
                days_diff = (most_recent - p).days
                weight = 0.5 ** (days_diff / half_life)
                weights.append(max(weight, 0.1))  # 最低保留10%权重
            return weights
        except Exception:
            # 回退：线性递减
            n = len(dates)
            return [max(0.1, 1.0 - i * 0.15) for i in range(n)]

    def _direction_suppression(self, matches, weights):
        """方向压制分析：连续同一方获胜的心理效应"""
        n = len(matches)
        if n < 2:
            return {'strength': 0, 'dominant_side': None, 'consecutive': 0, 'weighted_home_rate': 0.5}
        
        # 加权计算各方向胜率
        weighted_home = 0
        weighted_away = 0
        weighted_draw = 0
        total_weight = 0
        
        for m, w in zip(matches, weights):
            hg, ag = m.get('home_goals', 0), m.get('away_goals', 0)
            if hg > ag:
                weighted_home += w
            elif hg < ag:
                weighted_away += w
            else:
                weighted_draw += w
            total_weight += w
        
        if total_weight == 0:
            return {'strength': 0, 'dominant_side': None, 'consecutive': 0, 'weighted_home_rate': 0.5}
        
        home_rate = weighted_home / total_weight
        away_rate = weighted_away / total_weight
        
        # 连续分析（仅看原始序列，不按时间排序的matches已是新→旧）
        consecutive = 1
        dominant = 'home' if matches[0].get('home_goals', 0) > matches[0].get('away_goals', 0) else \
                   ('away' if matches[0].get('home_goals', 0) < matches[0].get('away_goals', 0) else 'draw')
        
        for i in range(1, len(matches)):
            m = matches[i]
            hg, ag = m.get('home_goals', 0), m.get('away_goals', 0)
            current = 'home' if hg > ag else ('away' if hg < ag else 'draw')
            if current == dominant and dominant != 'draw':
                consecutive += 1
            else:
                break
        
        # 强度计算
        threshold = self.cfg['suppression_threshold']
        strength = 0
        if consecutive >= threshold:
            strength = min((consecutive - threshold + 1) * 0.15 + max(home_rate, away_rate) * 0.3, 1.0)
        elif max(home_rate, away_rate) > 0.65:
            strength = (max(home_rate, away_rate) - 0.5) * 0.8
        
        dominant_side = 'home' if home_rate > away_rate else 'away'
        
        return {
            'strength': round(strength, 4),
            'dominant_side': dominant_side if strength > 0 else None,
            'consecutive': consecutive,
            'weighted_home_rate': round(home_rate, 4),
            'weighted_away_rate': round(away_rate, 4),
        }

    def _clean_sheet_suppression(self, matches, weights):
        """零封压制分析：连续被零封对进攻信心的打击"""
        n = len(matches)
        if n < self.cfg['clean_sheet_threshold']:
            return {'strength': 0, 'victim': None, 'consecutive': 0}
        
        # 主队被零封次数（加权）
        home_cs_victim = 0  # 主队被客队零封
        away_cs_victim = 0  # 客队被主队零封
        total_weight = sum(weights)
        
        for m, w in zip(matches, weights):
            hg, ag = m.get('home_goals', 0), m.get('away_goals', 0)
            if hg == 0:
                home_cs_victim += w
            if ag == 0:
                away_cs_victim += w
        
        if total_weight == 0:
            return {'strength': 0, 'victim': None, 'consecutive': 0}
        
        home_cs_rate = home_cs_victim / total_weight
        away_cs_rate = away_cs_victim / total_weight
        
        # 连续零封分析
        def count_consecutive_cs(side):
            """统计某一方连续被零封的场数"""
            count = 0
            for m in matches:
                if side == 'home' and m.get('home_goals', 0) == 0:
                    count += 1
                elif side == 'away' and m.get('away_goals', 0) == 0:
                    count += 1
                else:
                    break
            return count
        
        home_consec = count_consecutive_cs('home')
        away_consec = count_consecutive_cs('away')
        
        threshold = self.cfg['clean_sheet_threshold']
        strength = 0
        victim = None
        
        if home_consec >= threshold or home_cs_rate > 0.5:
            strength = max(min((home_consec - threshold + 1) * 0.2 + home_cs_rate * 0.3, 1.0), strength)
            victim = 'home'
        if away_consec >= threshold or away_cs_rate > 0.5:
            new_strength = max(min((away_consec - threshold + 1) * 0.2 + away_cs_rate * 0.3, 1.0), 0)
            if new_strength > strength:
                strength = new_strength
                victim = 'away'
        
        return {
            'strength': round(strength, 4),
            'victim': victim,
            'consecutive': max(home_consec, away_consec),
            'home_cs_rate': round(home_cs_rate, 4),
            'away_cs_rate': round(away_cs_rate, 4),
        }

    def _home_away_bias(self, matches, weights):
        """主场优势反转分析：交锋中主场方反而表现差"""
        # 筛选出当前主队为主场的交锋
        home_venue_matches = [(m, w) for m, w in zip(matches, weights) if m.get('venue') == 'home']
        
        if len(home_venue_matches) < 2:
            return {'reversal': False, 'strength': 0, 'home_venue_win_rate': 0.5}
        
        weighted_home_wins = 0
        total_weight = 0
        
        for m, w in home_venue_matches:
            hg, ag = m.get('home_goals', 0), m.get('away_goals', 0)
            if hg > ag:
                weighted_home_wins += w
            total_weight += w
        
        if total_weight == 0:
            return {'reversal': False, 'strength': 0, 'home_venue_win_rate': 0.5}
        
        home_win_rate = weighted_home_wins / total_weight
        threshold = self.cfg['venue_reversal_threshold']
        
        reversal = home_win_rate < threshold
        strength = 0
        if reversal:
            strength = min((threshold - home_win_rate) / threshold, 1.0)
        
        return {
            'reversal': reversal,
            'strength': round(strength, 4),
            'home_venue_win_rate': round(home_win_rate, 4),
            'home_venue_matches': len(home_venue_matches),
        }

    def _goal_trend(self, matches, weights):
        """进球趋势分析：交锋中进球数持续偏低/偏高"""
        if len(matches) < 3:
            return {'low_goal_trend': False, 'high_goal_trend': False, 'strength': 0, 'avg_goals': 2.5}
        
        total_goals = 0
        total_weight = 0
        under_25_count = 0
        
        for m, w in zip(matches, weights):
            goals = m.get('home_goals', 0) + m.get('away_goals', 0)
            total_goals += goals * w
            total_weight += w
            if goals < 2.5:
                under_25_count += w
        
        if total_weight == 0:
            return {'low_goal_trend': False, 'high_goal_trend': False, 'strength': 0, 'avg_goals': 2.5}
        
        avg_goals = total_goals / total_weight
        under_rate = under_25_count / total_weight
        threshold = self.cfg['goal_trend_threshold']
        
        # 低进球趋势：场均<2.0 且 小球率>60%
        low_goal = avg_goals < 2.0 and under_rate > 0.6
        high_goal = avg_goals > 3.0 and under_rate < 0.4
        
        strength = 0
        if low_goal:
            strength = min((2.0 - avg_goals) / 2.0 + (under_rate - 0.6) * 0.5, 1.0)
        elif high_goal:
            strength = min((avg_goals - 3.0) / 2.0 + (0.4 - under_rate) * 0.5, 1.0)
        
        return {
            'low_goal_trend': low_goal,
            'high_goal_trend': high_goal,
            'strength': round(strength, 4),
            'avg_goals': round(avg_goals, 2),
            'under_25_rate': round(under_rate, 4),
        }

    def _compute_outcome_bias(self, suppression, clean_sheet, venue_bias, goal_trend):
        """综合各信号计算胜平负概率偏向"""
        bias = {'home': 0.333, 'draw': 0.333, 'away': 0.333}
        
        # 方向压制 → 偏向主导方
        if suppression['strength'] > 0 and suppression['dominant_side']:
            dom = suppression['dominant_side']
            adj = suppression['strength'] * 0.08
            bias[dom] += adj
            # 从概率最低的方向扣除
            min_key = min(bias, key=bias.get)
            bias[min_key] -= adj
        
        # 零封压制 → 偏向零封实施方（被零封方的对手）
        if clean_sheet['strength'] > 0 and clean_sheet['victim']:
            victim = clean_sheet['victim']
            beneficiary = 'away' if victim == 'home' else 'home'
            adj = clean_sheet['strength'] * 0.06
            bias[beneficiary] += adj
            min_key = min(bias, key=bias.get)
            bias[min_key] -= adj
        
        # 主场优势反转 → 偏向客队
        if venue_bias['reversal']:
            adj = venue_bias['strength'] * 0.05
            bias['away'] += adj
            min_key = min(bias, key=bias.get)
            bias[min_key] -= adj
        
        # 低进球趋势 → 偏向平局
        if goal_trend['low_goal_trend']:
            adj = goal_trend['strength'] * 0.05
            bias['draw'] += adj
            min_key = min(bias, key=bias.get)
            bias[min_key] -= adj
        
        # 归一化
        total = sum(bias.values())
        if total > 0:
            bias = {k: v / total for k, v in bias.items()}
        
        return bias

    def _generate_notes(self, suppression, clean_sheet, venue_bias, goal_trend):
        """生成心理分析注释"""
        notes = []
        
        if suppression['strength'] > 0:
            if suppression['consecutive'] >= 3:
                notes.append(
                    f"【方向压制】连续{suppression['consecutive']}场交锋由"
                    f"{'主队' if suppression['dominant_side'] == 'home' else '客队'}"
                    f"主导（加权胜率{suppression['weighted_home_rate']*100:.0f}%），"
                    f"心理压制强度{suppression['strength']:.2f}"
                )
            else:
                notes.append(
                    f"【方向压制】交锋中{'主队' if suppression['dominant_side'] == 'home' else '客队'}"
                    f"占优（胜率{suppression['weighted_home_rate']*100:.0f}%），存在心理优势"
                )
        
        if clean_sheet['strength'] > 0:
            notes.append(
                f"【零封压制】{'主队' if clean_sheet['victim'] == 'home' else '客队'}"
                f"近{clean_sheet['consecutive']}次交锋被零封，"
                f"进攻信心可能受挫（强度{clean_sheet['strength']:.2f}）"
            )
        
        if venue_bias['reversal']:
            notes.append(
                f"【主场阴影】交锋中主场胜率仅{venue_bias['home_venue_win_rate']*100:.0f}%，"
                f"存在主场心理劣势（强度{venue_bias['strength']:.2f}）"
            )
        
        if goal_trend['low_goal_trend']:
            notes.append(
                f"【进球惯性】交锋场均仅{goal_trend['avg_goals']:.1f}球，"
                f"双方可能延续保守态势"
            )
        elif goal_trend['high_goal_trend']:
            notes.append(
                f"【对攻惯性】交锋场均{goal_trend['avg_goals']:.1f}球，"
                f"对攻心理可能延续"
            )
        
        if not notes:
            notes.append("【心理层面】交锋历史无明显心理压制信号")
        
        return notes
