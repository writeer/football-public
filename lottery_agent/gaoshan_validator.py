# -*- coding: utf-8 -*-
"""
竞彩Agent — 高山流水数据验证模块
利用历史统计数据对当前预测进行交叉验证
"""

import json
import os
from collections import defaultdict


class GaoshanValidator:
    """高山流水历史数据验证器"""

    def __init__(self, data_path=None, stats_path=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = data_path or os.path.join(base_dir, 'memory', 'gaoshan_parsed_matches.json')
        self.stats_path = stats_path or os.path.join(base_dir, 'memory', 'gaoshan_stats.json')
        self.matches = []
        self.stats = {}
        self.league_stats = {}
        self._load_data()

    def _load_data(self):
        """加载高山流水数据"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.matches = json.load(f)
        except Exception as e:
            print(f"[Gaoshan] 警告: 无法加载比赛数据: {e}")
            self.matches = []

        try:
            with open(self.stats_path, 'r', encoding='utf-8') as f:
                self.stats = json.load(f)
        except Exception as e:
            print(f"[Gaoshan] 警告: 无法加载统计数据: {e}")
            self.stats = {}

        # 构建联赛级统计
        self._build_league_stats()

    def _build_league_stats(self):
        """按联赛聚合统计"""
        if not self.stats:
            return

        sport_by_league = self.stats.get('sport_by_league', {})
        for league, data in sport_by_league.items():
            total = data.get('total', 0)
            correct = data.get('dir_correct', 0)
            if total > 0:
                self.league_stats[league] = {
                    'total': total,
                    'accuracy': correct / total,
                    'score_correct': data.get('score_correct', 0) / total if total > 0 else 0,
                }

    def find_match(self, home_team, away_team, league=None):
        """查找特定比赛的历史记录（模糊匹配）"""
        results = []
        for m in self.matches:
            if m.get('home_team', '').replace('|', '').strip() == home_team and \
               m.get('away_team', '').replace('|', '').strip() == away_team:
                if league is None or m.get('league') == league:
                    results.append(m)
        return results

    def get_league_accuracy(self, league):
        """获取联赛方向命中率"""
        if league in self.league_stats:
            return self.league_stats[league]['accuracy']
        # 返回整体平均
        total = self.stats.get('matches_with_sport', 0)
        correct = self.stats.get('sport_direction_correct', 0)
        if total > 0:
            return correct / total
        return 0.467  # 默认整体命中率

    def get_league_score_accuracy(self, league):
        """获取联赛比分命中率"""
        if league in self.league_stats:
            return self.league_stats[league]['score_correct']
        return 0.09  # 默认比分命中率

    def validate_direction(self, model_direction, league, home_team, away_team):
        """
        验证模型方向与高山流水历史表现的一致性
        返回: {'confidence_adjustment': +/-1, 'reason': str, 'league_accuracy': float}
        """
        league_acc = self.get_league_accuracy(league)

        # 如果联赛样本太少，不做调整
        if self.league_stats.get(league, {}).get('total', 0) < 20:
            return {
                'confidence_adjustment': 0,
                'reason': f"{league}样本不足(<20场)，高山验证跳过",
                'league_accuracy': league_acc,
            }

        # 查找同联赛同主队的历史
        historical = self.find_match(home_team, away_team, league)
        if historical:
            # 有历史交锋记录
            last = historical[-1]
            sport_dir = last.get('sport', {}).get('direction') if not last.get('sport', {}).get('none', True) else None
            if sport_dir:
                if sport_dir == model_direction:
                    return {
                        'confidence_adjustment': 1,
                        'reason': f"历史交锋高山方向'{sport_dir}'与模型一致，联赛命中率{league_acc:.1%}",
                        'league_accuracy': league_acc,
                        'historical_match': last,
                    }
                else:
                    return {
                        'confidence_adjustment': -1,
                        'reason': f"历史交锋高山方向'{sport_dir}'与模型'{model_direction}'矛盾，联赛命中率{league_acc:.1%}",
                        'league_accuracy': league_acc,
                        'historical_match': last,
                    }

        # 无历史交锋，仅使用联赛统计
        if league_acc > 0.50:
            return {
                'confidence_adjustment': 0,
                'reason': f"{league}高山方向命中率{league_acc:.1%}，略高于随机，保持模型原判断",
                'league_accuracy': league_acc,
            }
        else:
            return {
                'confidence_adjustment': 0,
                'reason': f"{league}高山方向命中率{league_acc:.1%}，接近随机，模型判断独立使用",
                'league_accuracy': league_acc,
            }

    def get_league_ranking(self):
        """获取高山流水各联赛命中率排名"""
        ranked = sorted(
            self.league_stats.items(),
            key=lambda x: x[1]['accuracy'],
            reverse=True
        )
        return ranked

    def summary(self):
        """数据摘要"""
        return {
            'total_matches': len(self.matches),
            'total_with_sport': self.stats.get('matches_with_sport', 0),
            'overall_direction_accuracy': self.stats.get('sport_direction_correct', 0) / self.stats.get('matches_with_sport', 1) if self.stats.get('matches_with_sport', 0) > 0 else 0,
            'leagues_available': list(self.league_stats.keys()),
            'top_leagues': self.get_league_ranking()[:5],
        }
