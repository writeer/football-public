# -*- coding: utf-8 -*-
"""
竞彩Agent — 单场比赛分析器
整合所有模型，输出完整的8维度分析结果
"""

import numpy as np
from scipy import stats

from .models import (
    DixonColesModel, NegativeBinomialModel, ZIPModel,
    SkellamModel, MonteCarloSimulator, OddsCalibrator,
    TeamRating, HTFTModel, LeagueDiagnosis, H2HPsychology
)
from .gaoshan_validator import GaoshanValidator
from .config import (
    FUNDAMENTAL_MODEL_WEIGHTS, SCORE_WEIGHTS, INJURY_IMPACT,
    CONFIDENCE_THRESHOLDS, REPORT_CONFIG, H2H_PSYCHOLOGY_CONFIG,
    resolve_home_advantage
)


class MatchAnalyzer:
    """单场比赛全方位分析器"""

    def __init__(self, match_data, gaoshan_validator=None):
        """
        match_data: dict with keys:
            - match_id: 比赛编号
            - league: 联赛名称
            - home_team: 主队名
            - away_team: 客队名
            - odds_home, odds_draw, odds_away: 赔率
            - home_data: {avg_scored, avg_conceded, fifa_rank, matches, market_value(万欧元), ...}
            - away_data: {avg_scored, avg_conceded, fifa_rank, matches, market_value(万欧元), ...}
            - injuries: [{team, player, position, importance}, ...]
            - notes: 特殊说明（可选）
            - home_value / away_value: 球队总身价（万欧元，可选，优先级低于 home_data/away_data 中的 market_value）
            - stadium_status: 场地状态（规则72，第一级别）：正常/空场/部分关闭/中立场，默认"正常"
            - closure_ratio: 部分关闭时的看台关闭比例（0~1，可选）
        """
        self.data = match_data
        self.league = match_data.get('league', 'default')
        self.home_team = match_data['home_team']
        self.away_team = match_data['away_team']

        # 规则72（第一级别）：空场/中立场 → 撤回首场优势，且禁止判定为"碾压局"
        self.stadium_status = match_data.get('stadium_status', '正常') or '正常'
        self.closure_ratio = match_data.get('closure_ratio')
        self.ha_rule72 = resolve_home_advantage(
            self.league, self.stadium_status, self.closure_ratio
        )
        self.home_advantage_override = (
            self.ha_rule72['factor'] if self.ha_rule72['override_applied'] else None
        )
        self.crush_allowed = self.ha_rule72['crush_allowed']

        # 初始化模型
        self.dc = DixonColesModel()
        self.nb = NegativeBinomialModel()
        self.zip_model = ZIPModel()
        self.skellam = SkellamModel()
        self.mc = MonteCarloSimulator()
        self.rating = TeamRating(self.league, self.home_advantage_override)
        self.htft = HTFTModel(self.dc)
        self.diagnosis = LeagueDiagnosis()

        # 高山验证器
        self.gaoshan = gaoshan_validator or GaoshanValidator()

        # 历史交锋心理权重
        self.h2h_psychology = H2HPsychology()
        self.h2h_result = None  # 在analyze中计算

        # 计算lambda基准
        self.lambda_home_raw, self.lambda_away_raw = self._compute_base_lambda()

        # 应用伤停修正
        self.lambda_home_injury, self.lambda_away_injury = self._apply_injury_adjustment()

        # 注意：历史交锋心理修正将在analyze中动态应用（需要输入数据）
        self.lambda_home = self.lambda_home_injury
        self.lambda_away = self.lambda_away_injury

    def _compute_base_lambda(self):
        """计算基准期望进球（基于Pi Rating）"""
        home_data = self.data.get('home_data', {})
        away_data = self.data.get('away_data', {})
        # 主场加成已在 TeamRating.pi_lambda 内施加（含规则72空场/中立场覆盖），
        # 2026-09-29 修正：此处原先又乘了一次 home_advantage，构成重复施加（等效 base²），
        # 使"碾压局"主队 λ 系统性偏高；已移除该重复项。
        lambda_h, lambda_a = self.rating.pi_lambda(home_data, away_data)

        # xG校准 - 向xG回归（xG是更稳定的预测指标）
        # 混合系数：70%保持实际数据 + 30%向xG回归
        xg_home = home_data.get('xg_avg')
        xg_away = away_data.get('xg_avg')
        actual_home = home_data.get('avg_scored', self.rating.league_per_side)
        actual_away = away_data.get('avg_scored', self.rating.league_per_side)
        if xg_home and xg_home > 0 and actual_home > 0:
            blend_h = 0.7 + 0.3 * (xg_home / actual_home)
            lambda_h *= blend_h
        if xg_away and xg_away > 0 and actual_away > 0:
            blend_a = 0.7 + 0.3 * (xg_away / actual_away)
            lambda_a *= blend_a

        # 再次限制在合理范围
        lambda_h = min(max(lambda_h, 0.3), 4.0)
        lambda_a = min(max(lambda_a, 0.3), 4.0)

        return lambda_h, lambda_a

    def _apply_injury_adjustment(self):
        """应用伤停修正"""
        lambda_h = self.lambda_home_raw
        lambda_a = self.lambda_away_raw

        injuries = self.data.get('injuries', [])
        home_injuries = [i for i in injuries if i.get('team') == 'home']
        away_injuries = [i for i in injuries if i.get('team') == 'away']

        # 主队伤停
        for inj in home_injuries:
            imp = inj.get('importance', 'key')
            pos = inj.get('position', 'midfield')
            coeff = INJURY_IMPACT.get(imp, INJURY_IMPACT['key'])

            if pos in ['forward', 'winger']:
                lambda_h *= coeff['attack_mult']
            elif pos in ['defender', 'goalkeeper']:
                lambda_a *= (2 - coeff['defense_mult'])  # 对手进攻增强
            else:
                lambda_h *= (1 + coeff['log_lambda_adj'] * 0.5)

        # 客队伤停
        for inj in away_injuries:
            imp = inj.get('importance', 'key')
            pos = inj.get('position', 'midfield')
            coeff = INJURY_IMPACT.get(imp, INJURY_IMPACT['key'])

            if pos in ['forward', 'winger']:
                lambda_a *= coeff['attack_mult']
            elif pos in ['defender', 'goalkeeper']:
                lambda_h *= (2 - coeff['defense_mult'])
            else:
                lambda_a *= (1 + coeff['log_lambda_adj'] * 0.5)

        # 确保lambda为正
        lambda_h = max(lambda_h, 0.1)
        lambda_a = max(lambda_a, 0.1)

        return lambda_h, lambda_a

    def analyze(self):
        """执行完整分析，返回结构化结果"""
        # 0. 历史交锋心理权重（在模型计算前应用）
        h2h_history = self.data.get('h2h_history', [])
        self.h2h_result = self.h2h_psychology.compute(h2h_history)
        
        # 应用心理修正到lambda
        self.lambda_home = self.lambda_home_injury * self.h2h_result['lambda_home_adj']
        self.lambda_away = self.lambda_away_injury * self.h2h_result['lambda_away_adj']
        
        # 1. 联赛诊断
        league_diag = self.diagnosis.diagnose(self.league)

        # 2. 赔率校准
        calibrator = OddsCalibrator(
            self.data['odds_home'],
            self.data['odds_draw'],
            self.data['odds_away']
        )
        odds_calibration = calibrator.all_methods()

        # 3. 各模型计算
        # DC模型
        dc_outcome = self.dc.outcome_probs(self.lambda_home, self.lambda_away)
        dc_scores = self.dc.top_scores(self.lambda_home, self.lambda_away, n=10)

        # 负二项
        nb_outcome = self.nb.outcome_probs(self.lambda_home, self.lambda_away)
        nb_scores = self.nb.top_scores(self.lambda_home, self.lambda_away, n=10)

        # ZIP（仅防守联赛启用）
        if league_diag['use_zip']:
            zip_outcome = self.zip_model.outcome_probs(self.lambda_home, self.lambda_away)
            zip_scores = self.zip_model.top_scores(self.lambda_home, self.lambda_away, n=10)
        else:
            zip_outcome = dc_outcome
            zip_scores = dc_scores

        # Skellam
        sk_outcome = self.skellam.outcome_probs(self.lambda_home, self.lambda_away)

        # 蒙特卡洛
        gamma_disp = 0.15 if league_diag['over_dispersed'] else 0.10
        mc_result = self.mc.simulate(self.lambda_home, self.lambda_away, gamma_disp=gamma_disp)

        # 4. Elo评级
        home_data = self.data.get('home_data', {})
        away_data = self.data.get('away_data', {})
        elo_home = self.rating.elo_rating(home_data, away_data, is_home=True)
        elo_away = self.rating.elo_rating(away_data, home_data, is_home=False)
        elo_outcome = self.rating.elo_probs(elo_home, elo_away)

        # 5. 加权融合
        dc_nb_zip_avg = {
            'home': (dc_outcome['home'] + nb_outcome['home'] + zip_outcome['home']) / 3,
            'draw': (dc_outcome['draw'] + nb_outcome['draw'] + zip_outcome['draw']) / 3,
            'away': (dc_outcome['away'] + nb_outcome['away'] + zip_outcome['away']) / 3,
        }

        # 历史交锋心理权重信号（独立信号源）
        h2h_bias = self.h2h_result['outcome_bias'] if self.h2h_result else {'home': 0.333, 'draw': 0.333, 'away': 0.333}
        h2h_weight = H2H_PSYCHOLOGY_CONFIG['weight_in_fusion']
        
        # 当心理效应强度足够大时才启用独立权重，否则将权重回拨给主模型
        h2h_strength = self.h2h_result.get('strength', 0) if self.h2h_result else 0
        effective_h2h_weight = h2h_weight * min(h2h_strength * 2, 1.0)  # 强度0.5时达到全权重
        
        # 调整其他权重比例（保持总和为1）
        weight_scale = (1 - effective_h2h_weight) / (1 - h2h_weight) if h2h_weight < 1 else 0
        
        w = FUNDAMENTAL_MODEL_WEIGHTS
        final = {}
        for outcome in ['home', 'draw', 'away']:
            # 规则79：仅基本面模型融合；市场去水概率只用于分歧与EV对照
            base_fusion = (
                w['dc_nb_zip'] * dc_nb_zip_avg[outcome] +
                w['skellam'] * sk_outcome[outcome] +
                w['elo_pi'] * elo_outcome[outcome] +
                w['ordinal'] * dc_nb_zip_avg[outcome]
            )
            # 加入心理权重信号
            final[outcome] = base_fusion * weight_scale + effective_h2h_weight * h2h_bias[outcome]

        # 归一化
        total = sum(final.values())
        final = {k: v / total for k, v in final.items()}

        # 6. 比分融合
        final_scores = {}
        for (h, a), p_dc in [(s[:2], s[2]) for s in dc_scores]:
            p_nb = next((s[2] for s in nb_scores if s[:2] == (h, a)), 0)
            p_zip = next((s[2] for s in zip_scores if s[:2] == (h, a)), 0)
            p_mc = next((count / self.mc.n_sim for score, count in mc_result['top_scores'] if score == (h, a)), 0)

            p_combined = (
                SCORE_WEIGHTS['dc'] * p_dc +
                SCORE_WEIGHTS['nb'] * p_nb +
                SCORE_WEIGHTS['zip'] * p_zip +
                SCORE_WEIGHTS['mc'] * p_mc
            )
            final_scores[(h, a)] = p_combined

        final_scores_sorted = sorted(final_scores.items(), key=lambda x: -x[1])[:10]

        # 7. 半全场
        htft_results = self.htft.predict(self.lambda_home, self.lambda_away)

        # 8. 置信度评估
        confidence = self._evaluate_confidence(
            dc_outcome, nb_outcome, sk_outcome, elo_outcome,
            odds_calibration['shin'], final, league_diag
        )

        # 9. 高山验证
        model_direction = '胜' if final['home'] > max(final['draw'], final['away']) else \
                         ('平' if final['draw'] > final['away'] else '负')
        gaoshan_validation = self.gaoshan.validate_direction(
            model_direction, self.league, self.home_team, self.away_team
        )

        # 应用高山调整
        confidence['score'] += gaoshan_validation['confidence_adjustment']
        confidence['gaoshan'] = gaoshan_validation

        # 10. 模型与市场分歧检测
        divergence = {}
        for outcome in ['home', 'draw', 'away']:
            div = final[outcome] - odds_calibration['shin'][outcome]
            divergence[outcome] = div

        # 11. EV计算
        ev = calibrator.ev(final)

        # 组装结果
        result = {
            'match_info': {
                'match_id': self.data.get('match_id', ''),
                'league': self.league,
                'home_team': self.home_team,
                'away_team': self.away_team,
                'odds': {
                    'home': self.data['odds_home'],
                    'draw': self.data['odds_draw'],
                    'away': self.data['odds_away'],
                },
                # 球队总身价（万欧元，来自 home_data/away_data.market_value 或顶层字段）
                'home_value': self.data.get('home_data', {}).get('market_value', self.data.get('home_value')),
                'away_value': self.data.get('away_data', {}).get('market_value', self.data.get('away_value')),
            },
            'league_diagnosis': league_diag,
            'lambda': {
                'home_raw': self.lambda_home_raw,
                'away_raw': self.lambda_away_raw,
                'home_final': self.lambda_home,
                'away_final': self.lambda_away,
            },
            # 规则72（第一级别）：场地状态与主场加成覆盖留痕
            'stadium': {
                'stadium_status': self.stadium_status,
                'closure_ratio': self.closure_ratio,
                'home_advantage_base': self.rating.profile['home_advantage'],
                'home_advantage_override': self.home_advantage_override,
                'override_applied': self.ha_rule72['override_applied'],
                'crush_match_allowed': self.crush_allowed,
                'note': self.ha_rule72['note'],
            },
            'ratings': {
                'elo': {'home': elo_home, 'away': elo_away},
                'pi': {
                    'home': self.rating.pi_rating(home_data),
                    'away': self.rating.pi_rating(away_data),
                },
            },
            'model_outcomes': {
                'dc': dc_outcome,
                'nb': nb_outcome,
                'zip': zip_outcome if league_diag['use_zip'] else None,
                'skellam': sk_outcome,
                'elo': elo_outcome,
                'monte_carlo': {
                    'home': mc_result['home_win'],
                    'draw': mc_result['draw'],
                    'away': mc_result['away_win'],
                },
                'shin': odds_calibration['shin'],
            },
            'odds_calibration': odds_calibration,
            'final_probabilities': final,
            'final_scores': final_scores_sorted,
            'goal_distribution': mc_result['goal_distribution'],
            'over_under': {
                'over_25': mc_result['over_25'],
                'under_25': mc_result['under_25'],
            },
            'htft': htft_results,
            'confidence': confidence,
            'divergence': divergence,
            'ev': ev,
            'injuries': self.data.get('injuries', []),
            'notes': self.data.get('notes', ''),
            'h2h_psychology': self.h2h_result,
        }

        return result

    def _evaluate_confidence(self, dc, nb, sk, elo, shin, final, league_diag):
        """置信度综合评估"""
        score = 0
        details = {}

        # A. 模型一致度 (权重40%)
        for outcome in ['home', 'draw', 'away']:
            values = [dc[outcome], nb[outcome], sk[outcome], elo[outcome]]
            std = np.std(values)
            if std < 0.05:
                details['model_consistency'] = '高度一致'
                score += 1
            elif std > 0.10:
                details['model_consistency'] = '严重分歧'
                score -= 1
            else:
                details['model_consistency'] = '中度一致'

        # B. 赔率对齐度 (权重25%)
        for outcome in ['home', 'draw', 'away']:
            diff = abs(final[outcome] - shin[outcome])
            if diff < 0.03:
                details['odds_alignment'] = '高度对齐'
                score += 1
            elif diff > 0.08:
                details['odds_alignment'] = '显著偏离'
                score -= 1
            else:
                details['odds_alignment'] = '对齐度一般'

        # C. 数据质量 (权重20%)
        if league_diag['vmr'] > 1.5:
            details['data_quality'] = '过离散严重'
            score -= 1
        else:
            details['data_quality'] = '数据稳定'
            score += 1

        home_matches = self.data.get('home_data', {}).get('matches', 0)
        away_matches = self.data.get('away_data', {}).get('matches', 0)
        if home_matches < 5 or away_matches < 5:
            details['sample_size'] = '样本不足'
            score -= 1
        else:
            details['sample_size'] = '样本充足'

        # D. 外部验证 (权重15%) - 高山在analyze中补充
        details['external'] = '待高山验证'

        # 评级
        if score >= CONFIDENCE_THRESHOLDS['high']:
            level = 'high'
            stars = '★★★'
        elif score >= CONFIDENCE_THRESHOLDS['medium']:
            level = 'medium'
            stars = '★★'
        elif score >= CONFIDENCE_THRESHOLDS['low']:
            level = 'low'
            stars = '★'
        else:
            level = 'very_low'
            stars = '☆'

        # E. 规则72（第一级别）：空场/中立场 → 置信度**强制降一级**（等级降级，非扣分）
        #    撤回主场加成后首选概率<45% → 再降一级（次选须含平局）
        if self.ha_rule72['override_applied']:
            ladder = ['very_low', 'low', 'medium', 'high']
            star_map = {'very_low': '☆', 'low': '★', 'medium': '★★', 'high': '★★★'}
            biggest = max(final.values())
            drops = 1 + (1 if biggest < 0.45 else 0)
            idx = max(0, ladder.index(level) - drops)
            details['stadium_rule72'] = (
                f'{self.stadium_status}：撤回首场优势 → 等级降{drops}级'
                f'（{stars}→{star_map[ladder[idx]]}，首选概率{biggest:.1%}）'
                + ('；次选必含平局' if biggest < 0.45 else '')
            )
            level, stars = ladder[idx], star_map[ladder[idx]]
        else:
            details['stadium_rule72'] = None

        return {
            'score': score,
            'level': level,
            'stars': stars,
            'details': details,
        }

    def get_recommendation(self, analysis_result):
        """从分析结果生成推荐"""
        final = analysis_result['final_probabilities']
        confidence = analysis_result['confidence']
        ev = analysis_result['ev']

        # 推荐方向
        max_prob = max(final, key=final.get)
        direction_map = {'home': '主胜', 'draw': '平局', 'away': '客胜'}
        recommended = direction_map[max_prob]

        # 推荐比分
        top_scores = analysis_result['final_scores']
        recommended_score = f"{top_scores[0][0][0]}-{top_scores[0][0][1]}"
        alt_score1 = f"{top_scores[1][0][0]}-{top_scores[1][0][1]}"
        alt_score2 = f"{top_scores[2][0][0]}-{top_scores[2][0][1]}"

        # 总进球
        ou = analysis_result['over_under']
        total_goals_rec = '大2.5' if ou['over_25'] > 0.55 else ('小2.5' if ou['under_25'] > 0.55 else '2-3球')

        # 半全场
        htft = analysis_result['htft']
        htft_rec = htft[0]['htft'] if htft else '未知'

        # 是否有正EV
        positive_ev = any(v > 0 for v in ev.values())

        return {
            'direction': recommended,
            'direction_prob': final[max_prob],
            'confidence': confidence,
            'scores': {
                'primary': recommended_score,
                'alt1': alt_score1,
                'alt2': alt_score2,
            },
            'total_goals': total_goals_rec,
            'htft': htft_rec,
            'positive_ev': positive_ev,
            'ev_details': ev,
        }
