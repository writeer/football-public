# -*- coding: utf-8 -*-
"""
竞彩Agent — 多场比赛批量分析与串关优化
"""

import json
import itertools
from datetime import datetime

from .analyzer import MatchAnalyzer
from .gaoshan_validator import GaoshanValidator
from .config import PARLAY_CONFIG, CONFIDENCE_THRESHOLDS, REPORT_CONFIG


class LotteryAgent:
    """竞彩批量分析Agent"""

    def __init__(self, matches_data, ticket_id=None):
        """
        matches_data: list of match_data dicts
        ticket_id: 彩票期号（如 '26094'）
        """
        self.matches_data = matches_data
        self.ticket_id = ticket_id or datetime.now().strftime('%Y%m%d')
        self.results = []
        self.gaoshan = GaoshanValidator()
        self.recommendations = []

    def analyze_all(self):
        """分析所有比赛"""
        print(f"[LotteryAgent] 开始分析 {len(self.matches_data)} 场比赛...")

        for i, match_data in enumerate(self.matches_data):
            match_id = match_data.get('match_id', f'M{i+1}')
            print(f"  [{match_id}] {match_data['home_team']} vs {match_data['away_team']}")

            analyzer = MatchAnalyzer(match_data, gaoshan_validator=self.gaoshan)
            result = analyzer.analyze()
            rec = analyzer.get_recommendation(result)

            self.results.append({
                'analysis': result,
                'recommendation': rec,
            })

        print(f"[LotteryAgent] 分析完成")
        return self.results

    def generate_parlay_suggestions(self):
        """生成串关建议"""
        if not self.results:
            self.analyze_all()

        # 筛选高置信度比赛
        qualified = []
        for r in self.results:
            conf = r['analysis']['confidence']
            rec = r['recommendation']

            # 串关最低门槛：中置信度及以上
            if conf['score'] >= PARLAY_CONFIG['min_confidence_for_parlay']:
                prob = rec['direction_prob']
                direction = rec['direction']
                match_info = r['analysis']['match_info']

                qualified.append({
                    'match_id': match_info['match_id'],
                    'match': f"{match_info['home_team']} vs {match_info['away_team']}",
                    'direction': direction,
                    'probability': prob,
                    'confidence': conf,
                    'odds': self._get_odds_for_direction(r['analysis'], direction),
                    'result_ref': r,
                })

        # 按概率降序排列
        qualified.sort(key=lambda x: -x['probability'])

        suggestions = {
            'conservative': [],   # 稳健型：高置信度+高概率
            'balanced': [],       # 平衡型：中高概率组合
            'aggressive': [],     # 激进型：包含分歧机会
            'all_qualified': qualified,
        }

        # 稳健2串1：选概率最高的两场
        if len(qualified) >= 2:
            top2 = qualified[:2]
            if all(q['probability'] >= PARLAY_CONFIG['conservative_threshold'] for q in top2):
                suggestions['conservative'].append({
                    'type': '2串1',
                    'matches': top2,
                    'combined_prob': top2[0]['probability'] * top2[1]['probability'],
                    'combined_odds': top2[0]['odds'] * top2[1]['odds'],
                    'risk_level': '低',
                })

        # 稳健3串1：选概率最高的三场
        if len(qualified) >= 3:
            top3 = qualified[:3]
            if all(q['probability'] >= PARLAY_CONFIG['conservative_threshold'] for q in top3):
                suggestions['conservative'].append({
                    'type': '3串1',
                    'matches': top3,
                    'combined_prob': top3[0]['probability'] * top3[1]['probability'] * top3[2]['probability'],
                    'combined_odds': top3[0]['odds'] * top3[1]['odds'] * top3[2]['odds'],
                    'risk_level': '中',
                })

        # 平衡型：2串1（第一场高概率+第二场分歧机会）
        if len(qualified) >= 2:
            # 找有模型与市场分歧的比赛
            divergence_matches = []
            for r in self.results:
                div = r['analysis']['divergence']
                max_div = max(abs(v) for v in div.values())
                if max_div > 0.10:
                    match_info = r['analysis']['match_info']
                    rec = r['recommendation']
                    divergence_matches.append({
                        'match_id': match_info['match_id'],
                        'match': f"{match_info['home_team']} vs {match_info['away_team']}",
                        'direction': rec['direction'],
                        'probability': rec['direction_prob'],
                        'divergence': max_div,
                        'odds': self._get_odds_for_direction(r['analysis'], rec['direction']),
                        'result_ref': r,
                    })

            if divergence_matches and qualified:
                div_match = max(divergence_matches, key=lambda x: x['divergence'])
                safe_match = qualified[0]
                suggestions['balanced'].append({
                    'type': '2串1（高概率+分歧）',
                    'matches': [safe_match, div_match],
                    'combined_prob': safe_match['probability'] * div_match['probability'],
                    'combined_odds': safe_match['odds'] * div_match['odds'],
                    'risk_level': '中',
                    'note': f"{div_match['match']} 模型与市场分歧 {div_match['divergence']:.1%}",
                })

        # 激进型：包含冷门方向的2串1
        aggressive_candidates = []
        for r in self.results:
            final = r['analysis']['final_probabilities']
            rec = r['recommendation']
            # 找不是概率最高的方向但概率>30%的
            sorted_probs = sorted(final.items(), key=lambda x: -x[1])
            if len(sorted_probs) >= 2:
                second_best = sorted_probs[1]
                if second_best[1] >= 0.30:
                    direction_map = {'home': '主胜', 'draw': '平局', 'away': '客胜'}
                    aggressive_candidates.append({
                        'match_id': r['analysis']['match_info']['match_id'],
                        'match': f"{r['analysis']['match_info']['home_team']} vs {r['analysis']['match_info']['away_team']}",
                        'direction': direction_map[second_best[0]],
                        'probability': second_best[1],
                        'odds': self._get_odds_for_direction(r['analysis'], direction_map[second_best[0]]),
                        'result_ref': r,
                    })

        if len(aggressive_candidates) >= 2:
            ac = aggressive_candidates[:2]
            suggestions['aggressive'].append({
                'type': '2串1（双冷门）',
                'matches': ac,
                'combined_prob': ac[0]['probability'] * ac[1]['probability'],
                'combined_odds': ac[0]['odds'] * ac[1]['odds'],
                'risk_level': '高',
            })

        self.parlay_suggestions = suggestions
        return suggestions

    def _get_odds_for_direction(self, analysis, direction):
        """根据推荐方向获取对应赔率"""
        odds = analysis['match_info']['odds']
        direction_map = {'主胜': 'home', '平局': 'draw', '客胜': 'away'}
        key = direction_map.get(direction, 'home')
        return odds.get(key, 1.0)

    def generate_summary(self):
        """生成分析摘要"""
        if not self.results:
            self.analyze_all()

        summary = {
            'ticket_id': self.ticket_id,
            'total_matches': len(self.results),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'high_confidence': [],
            'medium_confidence': [],
            'low_confidence': [],
            'divergence_alerts': [],
            'direction_distribution': {'主胜': 0, '平局': 0, '客胜': 0},
        }

        for r in self.results:
            rec = r['recommendation']
            conf = r['analysis']['confidence']
            match_id = r['analysis']['match_info']['match_id']
            match_name = r['analysis']['match_info']['home_team'] + ' vs ' + r['analysis']['match_info']['away_team']

            summary['direction_distribution'][rec['direction']] += 1

            if conf['level'] == 'high':
                summary['high_confidence'].append({
                    'match_id': match_id,
                    'match': match_name,
                    'direction': rec['direction'],
                    'prob': rec['direction_prob'],
                })
            elif conf['level'] == 'medium':
                summary['medium_confidence'].append({
                    'match_id': match_id,
                    'match': match_name,
                    'direction': rec['direction'],
                    'prob': rec['direction_prob'],
                })
            else:
                summary['low_confidence'].append({
                    'match_id': match_id,
                    'match': match_name,
                    'direction': rec['direction'],
                    'prob': rec['direction_prob'],
                })

            # 模型与市场分歧预警
            div = r['analysis']['divergence']
            max_div_key = max(div, key=lambda k: abs(div[k]))
            if abs(div[max_div_key]) > REPORT_CONFIG['show_divergence_threshold']:
                direction_map = {'home': '主胜', 'draw': '平局', 'away': '客胜'}
                summary['divergence_alerts'].append({
                    'match_id': match_id,
                    'match': match_name,
                    'direction': direction_map[max_div_key],
                    'model_prob': r['analysis']['final_probabilities'][max_div_key],
                    'market_prob': r['analysis']['odds_calibration']['shin'][max_div_key],
                    'divergence': div[max_div_key],
                })

        return summary

    def generate_report(self, output_path=None):
        """生成完整报告"""
        if not self.results:
            self.analyze_all()

        if not hasattr(self, 'parlay_suggestions'):
            self.generate_parlay_suggestions()

        summary = self.generate_summary()

        report = {
            'ticket_id': self.ticket_id,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'summary': summary,
            'matches': self.results,
            'parlay_suggestions': self.parlay_suggestions,
            'gaoshan_summary': self.gaoshan.summary(),
        }

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"[LotteryAgent] 报告已保存至 {output_path}")

        return report
