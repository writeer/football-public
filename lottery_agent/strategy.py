# -*- coding: utf-8 -*-
"""回测教训 L241–L245 的代码化实现。

原则（规则79）：
  - 概率只由基本面模型（DC/NB/ZIP/Skellam/MC）融合得出；
  - 市场去水概率只用于“分歧/一致性”对照，不进入任何融合权重；
  - 缺失数据（身价/近5场半场记录）一律显式标注，不用臆测值替代。
"""
from __future__ import annotations

# 基本面模型融合权重（沿用 20261101 已验证口径，全部为基本面分布模型）
FUNDAMENTAL_FUSION_WEIGHTS = {
    'dc': 0.34,
    'nb': 0.22,
    'zip': 0.13,
    'sk': 0.14,
    'mc': 0.17,
}

# L241 阈值
MODEL_GAP_DUAL = 0.05      # 模型主/客概率差 < 5pp → 强制双选
MARKET_STRONG = 0.65       # 市场强推线
MODEL_WEAK = 0.55          # 模型弱支持线

# L242 阈值
VALUE_GAP_BIG = 5.0        # 身价差 ≥5 倍
LAMBDA_GAP_BIG = 1.0       # λ 差 ≥1.0
LOW_TOTAL_LAMBDA = 2.6     # 双方 λ 合计 <2.6

# L243 阈值
VALUE_GAP_SCORE = 4.0      # 身价差 ≥4 倍
LAMBDA_GAP_SCORE = 1.0     # 身价缺失时的实力差替代门槛（披露后使用）

# L245 阈值
PARLAY_MIN_PRIMARY = 0.55

TIER_LADDER = [
    '闷战超小球(0-1球)',
    '小球(1-2球)',
    '常规正常球(2-3球)',
    '大球(4-5球)',
    '超大球(5-6球)',
    '穿盘可能(6-7+球)',
]


def fuse_outcomes(dc, nb, zp, sk, mc, weights=None):
    """规则79：仅基本面模型融合，市场概率不参与。"""
    w = weights or FUNDAMENTAL_FUSION_WEIGHTS
    fused = {
        k: (w['dc'] * dc[k] + w['nb'] * nb[k] + w['zip'] * zp[k]
            + w['sk'] * sk[k] + w['mc'] * mc[k])
        for k in ('home', 'draw', 'away')
    }
    total = sum(fused.values())
    if total <= 0:
        raise ValueError('基本面融合概率非法：总和为0')
    return {k: v / total for k, v in fused.items()}


def select_direction(model, market=None, is_single=False):
    """L241：方向首选/双选/单关口径。

    ① 模型主客概率差 <5pp → 强制双选；
    ② 市场强推（≥65%）且模型不支持（<55%）→ 首选保持模型侧，并披露分歧；
    ③ 单关取模型-市场分歧最小的一侧（仅作单关参考，不改变首选方向）。
    """
    order = sorted(model, key=lambda k: -model[k])
    top1, top2 = order[0], order[1]
    notes = []
    dual = abs(model['home'] - model['away']) < MODEL_GAP_DUAL
    if dual:
        notes.append('L241① 模型主客差%.1fpp<5pp → 强制双选' % (
            abs(model['home'] - model['away']) * 100))

    primary = top1
    if market:
        market_top = max(market, key=lambda k: market[k])
        if market[market_top] >= MARKET_STRONG and model[market_top] < MODEL_WEAK:
            # 首选保持模型概率最高侧，不因市场强推改取低概率侧
            notes.append('L241② 市场强推%s %.1f%% 但模型仅%.1f%% → 首选保持模型侧%s并披露分歧' % (
                market_top, market[market_top] * 100, model[market_top] * 100, primary))
    secondary = next(k for k in order if k != primary)

    single_pick = None
    if is_single:
        if market:
            single_pick = min(order[:2], key=lambda k: abs(model[k] - market[k]))
            notes.append('L241③ 单关取分歧最小侧%s（%.1fpp）' % (
                single_pick, abs(model[single_pick] - market[single_pick]) * 100))
        else:
            single_pick = primary

    return {
        'primary': primary,
        'secondary': secondary,
        'dual': dual,
        'single_pick': single_pick,
        'notes': notes,
    }


def goal_band(lam_h, lam_a, dist, league=None, value_ratio=None):
    """L242：进球档位以实力差优先，联赛标签只作背景。

    dist: {p01, p23, p45, p6, p_over25, top_total}
    ① 身价差≥5倍或λ差≥1.0 → 档位下限抬到“大球(4-5球)”；
    ② 双方λ合计<2.6 → 档位上限压到“小球(1-2球)”；
    ③ 联赛风格与实力差冲突 → 实力差优先。
    身价缺失时仅以λ差判定，并披露。
    """
    lam_gap = abs(lam_h - lam_a)
    lam_total = lam_h + lam_a
    base_idx = _base_tier_index(dist)
    triggers = []
    if value_ratio is not None and value_ratio >= VALUE_GAP_BIG:
        triggers.append('身价差%.2f倍≥5' % value_ratio)
    if lam_gap >= LAMBDA_GAP_BIG:
        triggers.append('λ差%.2f≥1.0' % lam_gap)

    idx = base_idx
    notes = []
    if triggers:
        idx = max(idx, TIER_LADDER.index('大球(4-5球)'))
        notes.append('L242① 实力差触发（%s）→ 档位下限抬至大球' % '、'.join(triggers))
        if value_ratio is None:
            notes.append('L242 身价数据缺失，仅以λ差判定（已披露）')
    if lam_total < LOW_TOTAL_LAMBDA and not triggers:
        idx = min(idx, TIER_LADDER.index('小球(1-2球)'))
        notes.append('L242② λ合计%.2f<2.6 → 档位上限压至小球' % lam_total)
    elif lam_total < LOW_TOTAL_LAMBDA and triggers:
        notes.append('L242③ λ合计%.2f<2.6 与实力差冲突 → 以实力差优先' % lam_total)

    tier = TIER_LADDER[idx]
    if triggers:
        over_under = '大'
    elif idx <= TIER_LADDER.index('小球(1-2球)'):
        over_under = '小'
    else:
        over_under = '大' if dist.get('p_over25', 0) > 0.5 else '小'

    return {
        'tier': tier,
        'over_under': over_under,
        'lambda_gap': round(lam_gap, 3),
        'triggers': triggers,
        'notes': notes,
    }


def _base_tier_index(dist):
    p01 = dist.get('p01', 0)
    p6 = dist.get('p6', 0)
    top_total = dist.get('top_total', 2)
    if p6 >= 0.25:
        return TIER_LADDER.index('穿盘可能(6-7+球)')
    if p01 >= 0.40:
        return TIER_LADDER.index('闷战超小球(0-1球)')
    if top_total <= 1:
        return TIER_LADDER.index('小球(1-2球)')
    if top_total in (2, 3):
        return TIER_LADDER.index('常规正常球(2-3球)')
    if top_total == 4:
        return TIER_LADDER.index('大球(4-5球)')
    if top_total == 5:
        return TIER_LADDER.index('超大球(5-6球)')
    return TIER_LADDER.index('穿盘可能(6-7+球)')


def score_pool(top_scores, primary, lam_gap, value_ratio=None, keep=5):
    """L243：比分池上沿修正。

    首选主胜且身价差≥4倍（身价缺失时以λ差≥1.0替代并披露）→
    TOP5 强制含 1 个净胜≥3 的比分（3-0/4-1）；客胜同理含 1-3/1-4。
    强制比分标记 tail=True，只用于单关/娱乐串。
    """
    scores = list(top_scores[:keep])
    notes = []
    forced = None
    strength_ok = False
    if value_ratio is not None and value_ratio >= VALUE_GAP_SCORE:
        strength_ok = True
    elif value_ratio is None and lam_gap >= LAMBDA_GAP_SCORE:
        strength_ok = True
        notes.append('L243 身价数据缺失，以λ差%.2f≥1.0替代实力门槛（已披露）' % lam_gap)

    if strength_ok and primary in ('home', 'away'):
        need_sign = 1 if primary == 'home' else -1
        has_tail = any((h - a) * need_sign >= 3 for h, a, _ in scores)
        if not has_tail:
            cands = [(h, a, p) for h, a, p in top_scores
                     if (h - a) * need_sign >= 3 and (h, a, p) not in scores]
            if cands:
                forced = max(cands, key=lambda x: x[2])
                dropped = scores[-1] if len(scores) >= keep else None
                if dropped is not None:
                    scores = scores[:keep - 1] + [forced]
                    notes.append('L243 强制补净胜≥3比分%d-%d（原末位%d-%d移出TOP%d）' % (
                        forced[0], forced[1], dropped[0], dropped[1], keep))
                else:
                    scores.append(forced)
                    notes.append('L243 强制补净胜≥3比分%d-%d（池未满，直接追加）' % (
                        forced[0], forced[1]))
    return {'scores': scores, 'forced': forced, 'tail_only': forced is not None, 'notes': notes}


def htft_pool(htft_sorted, home_choke=None, away_choke=None, keep=3):
    """L244：半场领先被翻路径覆盖。

    home_choke / away_choke：近5场“半场领先最终输球”次数（无法获取时传 None）。
    ≥2 次 → TOP3 强制插入 HA（主队半场领先被翻）或 AH（客队半场领先被翻）；
    强制项只作覆盖提示，不计入主推。
    """
    picks = list(htft_sorted[:keep])
    notes = []
    forced = []
    if home_choke is not None and home_choke >= 2 and 'HA' not in [k for k, _ in picks]:
        pick = next((x for x in htft_sorted if x[0] == 'HA'), None)
        if pick:
            picks = picks[:keep - 1] + [pick]
            forced.append('HA')
            notes.append('L244 主队近5场%d次半场领先被翻 → 强制插入HA（覆盖提示，不计主推）' % home_choke)
    if away_choke is not None and away_choke >= 2 and 'AH' not in [k for k, _ in picks]:
        pick = next((x for x in htft_sorted if x[0] == 'AH'), None)
        if pick:
            picks = picks[:keep - 1] + [pick]
            forced.append('AH')
            notes.append('L244 客队近5场%d次半场领先被翻 → 强制插入AH（覆盖提示，不计主推）' % away_choke)
    if home_choke is None and away_choke is None:
        notes.append('L244 近5场半场领先被翻数据缺失 → 未触发（需人工补充）')
    return {'picks': picks, 'forced': forced, 'notes': notes}


def handicap_pick(hc_model, line, primary, k_rec):
    """让球口径（含极端分差）。

    hc_model: {home: 让胜, draw: 让平, away: 让负}（已按盘口折算）。
    |k_rec|≥3 的极端分差 → 直接取首选方向侧，禁止用“让平”作为首选；
    常规分差 → 取概率最大侧，首选为平局时取让平。
    """
    notes = []
    if abs(k_rec) >= 3 and primary in ('home', 'away'):
        pick = primary
        notes.append('极端分差（净胜%+d）→ 让球首选取%s，不采用让平口径' % (k_rec, pick))
    elif primary == 'draw':
        pick = 'draw'
    else:
        pick = max(('home', 'draw', 'away'), key=lambda k: hc_model.get(k, 0))
        notes.append('常规分差 → 让球取概率最大侧%s' % pick)
    return {'pick': pick, 'notes': notes}


def parlay_leg_eligible(prob, model_side, market_side):
    """L245①：方向串腿 = 首选≥55% 且模型-市场同向。"""
    return prob >= PARLAY_MIN_PRIMARY and market_side is not None and model_side == market_side


def value_handicap_parlay_ok(legs):
    """L245②：价值让球串禁止两腿全用次选（至少一腿为首选）。"""
    return any(x.get('is_primary') for x in legs)


def entertainment_stake_ok(total_bankroll, stake):
    """L245③：娱乐串单注≤总资金1%。"""
    return total_bankroll > 0 and stake <= total_bankroll * 0.01
