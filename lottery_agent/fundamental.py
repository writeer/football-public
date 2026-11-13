# -*- coding: utf-8 -*-
"""规则79：基本面 λ 计算（唯一入口，禁止赔率反解）。

概率生成链路：
    积分榜场均进失球 → 攻击/防守强度 → 守恒式 λ → 分布模型 → 概率

赔率不参与本模块任何一步；赔率只在外部 de_vig 后用于对照分歧与计算 EV。
"""
from __future__ import annotations

from .config import LEAGUE_PROFILES

SHRINK_K = 6.0          # 样本量收缩强度（场次）：赛季初小样本向联赛均值回归
LAMBDA_MIN = 0.25
LAMBDA_MAX = 4.5

# 竞彩中文联赛名 → LEAGUE_PROFILES 键名（避免落 default）
LEAGUE_ALIAS = {
    '韩职': '韩K', '韩K联': '韩K', 'K联赛': '韩K',
    '美职联': '美职', '美国职业大联盟': '美职',
    '日职联': '日职', 'J联赛': '日职',
}


def _profile(league):
    key = LEAGUE_ALIAS.get(league, league)
    return LEAGUE_PROFILES.get(key, LEAGUE_PROFILES['default'])


def league_baseline(table_rows):
    """从本赛季积分榜算联赛场均总进球；无有效样本返回 None。

    口径：sum(goals_for) 为全联赛总进球，sum(played) 为球队-场次，
    每场涉及两队，故场均总进球 = 2 * sum(goals_for) / sum(played)。
    """
    goals = games = 0
    for row in table_rows or []:
        played = row.get('played') or 0
        if played <= 0:
            continue
        gf = row.get('goals_for')
        if gf is None:
            gf = (row.get('avg_goals_scored') or 0.0) * played
        goals += gf
        games += played
    if games <= 0:
        return None
    return 2.0 * goals / games


def strength(row, per_side):
    """攻击/防守强度系数（1.0 = 联赛平均），按场次向 1.0 收缩。"""
    played = row.get('played') or 0
    scored = row.get('avg_goals_scored') or 0.0
    conceded = row.get('avg_goals_conceded') or 0.0
    w = played / (played + SHRINK_K) if played > 0 else 0.0
    attack = 1.0 + (scored / per_side - 1.0) * w
    defense = 1.0 + (conceded / per_side - 1.0) * w
    return max(attack, 0.30), max(defense, 0.30)


def fundamental_lambdas(home_row, away_row, league, table_rows=None,
                        home_advantage=None, adjustments=None):
    """由基本面数据计算 λ_home / λ_away。

    参数
    ----
    home_row / away_row : dict
        积分榜单行，需含 avg_goals_scored / avg_goals_conceded / played
        （建议一并带 team 名称便于留痕）。
    league : str
        中文联赛名（用于 LEAGUE_PROFILES 取主场系数与基准）。
    table_rows : list[dict]
        该联赛本赛季全体积分榜行；提供时用实际联赛均进球替代硬编码基准。
    home_advantage : float | None
        主场加成覆盖（规则72 空场/中立场传 1.0，部分关闭按裁决折减）；
        None 时取联赛基准。
    adjustments : dict | None
        基本面修正（伤停/战意/赛程/等级差等），键：
        lh / la：攻击 λ 乘数；dt：总进球增量（按比例分摊）。

    返回
    ----
    dict: lambda_home / lambda_away / league_avg / home_adv /
          atk_home / def_home / atk_away / def_away / basis
    """
    prof = _profile(league)
    measured = league_baseline(table_rows)
    league_avg = measured if measured else prof['avg_goals']
    basis = '本赛季积分榜实际均值' if measured else 'LEAGUE_PROFILES 静态基准'

    home_adv = prof['home_advantage'] if home_advantage is None else float(home_advantage)
    per_side = league_avg / 2.0

    atk_h, def_h = strength(home_row, per_side)
    atk_a, def_a = strength(away_row, per_side)

    # 守恒式主场分摊：两队均为平均队时 λ_home + λ_away == league_avg
    share_h = home_adv / (1.0 + home_adv)
    lh = league_avg * share_h * atk_h * def_a
    la = league_avg * (1.0 - share_h) * atk_a * def_h

    adj = adjustments or {}
    lh *= adj.get('lh', 1.0)
    la *= adj.get('la', 1.0)
    dt = adj.get('dt', 0.0)
    if dt:
        total = lh + la
        lh += dt * lh / total
        la += dt * la / total

    lh = min(max(lh, LAMBDA_MIN), LAMBDA_MAX)
    la = min(max(la, LAMBDA_MIN), LAMBDA_MAX)

    return {
        'lambda_home': lh,
        'lambda_away': la,
        'league_avg': league_avg,
        'home_adv': home_adv,
        'atk_home': atk_h, 'def_home': def_h,
        'atk_away': atk_a, 'def_away': def_a,
        'basis': basis,
    }


def parlay_ev(probs, odds):
    """串关期望值：EV = (∏各腿概率) × 串关赔率。EV<1 即负期望。"""
    joint = 1.0
    for p in probs:
        joint *= p
    return joint, joint * odds
