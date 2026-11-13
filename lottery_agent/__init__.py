# -*- coding: utf-8 -*-
"""
竞彩Agent — 足球比赛全方位分析系统

基于以下理论框架：
- Dixon-Coles 修正泊松模型
- 负二项分布 / ZIP零膨胀模型
- Skellam 进球差模型
- 蒙特卡洛模拟
- Shin赔率校准
- Elo/Pi实力评级
- 高山流水历史数据交叉验证

用法：
    from lottery_agent import MatchAnalyzer, LotteryAgent

    # 单场比赛分析
    analyzer = MatchAnalyzer(match_data)
    result = analyzer.analyze()

    # 批量竞彩分析
    agent = LotteryAgent(matches_data)
    report = agent.generate_report()
"""

from .analyzer import MatchAnalyzer
from .multi_analyzer import LotteryAgent
from .models import (
    DixonColesModel, NegativeBinomialModel, ZIPModel,
    SkellamModel, MonteCarloSimulator, OddsCalibrator,
    TeamRating, HTFTModel, LeagueDiagnosis
)
from .gaoshan_validator import GaoshanValidator
from .report_generator import ReportGenerator

__version__ = '1.0.0'
__all__ = [
    'MatchAnalyzer',
    'LotteryAgent',
    'DixonColesModel',
    'NegativeBinomialModel',
    'ZIPModel',
    'SkellamModel',
    'MonteCarloSimulator',
    'OddsCalibrator',
    'TeamRating',
    'HTFTModel',
    'LeagueDiagnosis',
    'GaoshanValidator',
    'ReportGenerator',
]
