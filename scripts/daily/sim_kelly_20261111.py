# -*- coding: utf-8 -*-
"""虚拟本金凯利模拟盘（2026-11-11 首日）
只读已有模型输出与官方赔率，不重跑模型；只做单关，不含串关。
"""
import json, io, math

OUT_JSON = 'reports/sim/kelly_sim_ledger.json'
MODEL = 'reports/data/20261111_model_output.json'
FINAL = 'reports/data/20261111_predictions_final.json'

INIT_BAL = 10000.0
FRACTION = 0.25
MAX_BET_PCT = 0.05
MAX_DAY_PCT = 0.20
MIN_STAKE = 2.0
# 虚构世界设定（非现实债务、非真实资金）：只把"超过初始本金 10,000 的部分"计为可还款额
DEBT_PRINCIPAL = 100000.0
REPAY_FLOOR = 10000.0
TARGET_BALANCE = REPAY_FLOOR + DEBT_PRINCIPAL  # 余额达到 110,000 视为虚构债务清零

# 正式赛果（体彩官方 getUniformMatchResultV1，lastUpdate 2026-11-12 08:32:51）
RESULTS = {
    '周三001': {'score': '2:3', 'ht': '2:1', 'line': 1},
    '周三002': {'score': '0:1', 'ht': '0:0', 'line': -1},
    '周三003': {'score': '1:2', 'ht': '0:0', 'line': 1},
    '周三004': {'score': '2:0', 'ht': '0:0', 'line': -1},
    '周三005': {'score': '0:4', 'ht': '0:2', 'line': -1},
    '周三006': {'score': '5:2', 'ht': '3:0', 'line': -1},
}
CONF = {'周三001': '★', '周三002': '★', '周三003': '★',
        '周三004': '★★', '周三005': '★', '周三006': '☆'}
HAD_FIRST = {'周三001': ('主胜', 'home'), '周三002': ('客胜', 'away'), '周三003': ('客胜', 'away'),
             '周三004': ('主胜', 'home'), '周三005': ('主胜', 'home'), '周三006': ('主胜', 'home')}
HAD_SECOND = {'周三001': ('客胜', 'away'), '周三002': ('平', 'draw'), '周三003': ('主胜', 'home'),
              '周三004': ('平', 'draw'), '周三005': ('平', 'draw'), '周三006': ('平', 'draw')}
HHAD_NAME = {'home': '让胜', 'draw': '让平', 'away': '让负'}
HAFU_NAME = {'HH': '胜胜', 'HD': '胜平', 'HA': '胜负', 'DH': '平胜',
             'DD': '平平', 'DA': '平负', 'AH': '负胜', 'AD': '负平', 'AA': '负负'}


def devig(odds_map):
    inv = {k: 1.0 / v for k, v in odds_map.items() if v}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}, s


def kelly(p, odds):
    b = odds - 1.0
    q = 1.0 - p
    return (b * p - q) / b


def candidates(mk, m, final_p):
    """六维推荐表内的候选项（选场仍以胜率优先，凯利只算注额）"""
    num = m['num']
    cands = []

    # HAD：仅 ★★ 场次可投方向（★ 场次缓释，☆ 弃权不投）
    if CONF[num] == '★★' and m['odds']['had']:
        dv, _ = devig(m['odds']['had'])
        for tag, (name, key) in (('首选', HAD_FIRST[num]), ('次选', HAD_SECOND[num])):
            cands.append({'market': 'HAD', 'selection': name, 'odds': m['odds']['had'][key],
                          'p': final_p[key] / 100.0, 'pi': dv[key], 'tier': tag})

    # HHAD：前二选项（让球盘对方向要求较宽，★ 场次可投）
    if m['odds']['hhad']:
        h = m['odds']['hhad']
        key_of = {'home': 'win', 'draw': 'push', 'away': 'lose'}
        om = {'home': h['home'], 'draw': h['draw'], 'away': h['away']}
        dv, _ = devig(om)
        order = sorted(['home', 'draw', 'away'], key=lambda k: -m['handicap'][key_of[k]])
        for rank, k in enumerate(order[:2]):
            cands.append({'market': 'HHAD', 'selection': HHAD_NAME[k], 'odds': om[k],
                          'p': m['handicap'][key_of[k]],
                          'pi': dv[k], 'tier': '首选' if rank == 0 else '次选'})

    # TTG：首推档 TOP2
    if m['odds']['ttg']:
        dv, _ = devig(m['odds']['ttg'])
        for g in sorted(m['ttg'], key=lambda x: -m['ttg'][x])[:2]:
            cands.append({'market': 'TTG', 'selection': f'总进球{g}', 'odds': m['odds']['ttg'].get(g),
                          'p': m['ttg'][g], 'pi': dv.get(g), 'tier': '首推档'})

    # HAFU：TOP3
    if m['odds']['hafu']:
        dv, _ = devig(m['odds']['hafu'])
        for code in list(m['htft'].keys())[:3]:
            cands.append({'market': 'HAFU', 'selection': HAFU_NAME[code], 'odds': m['odds']['hafu'].get(code),
                          'p': m['htft'][code], 'pi': dv.get(code), 'tier': 'TOP3'})

    # 比分：TOP5，且 p≥8%（沿用规则67 第⑤步候选下限）
    if m['odds']['crs']:
        dv, _ = devig(m['odds']['crs'])
        for sc, p in m['top_scores'][:5]:
            if p < 0.08:
                continue
            cands.append({'market': 'CRS', 'selection': f'比分{sc}', 'odds': m['odds']['crs'].get(sc),
                          'p': p, 'pi': dv.get(sc), 'tier': 'TOP5'})

    out = []
    for c in cands:
        if not c['odds'] or not c['pi']:
            continue
        c['edge_pp'] = round((c['p'] - c['pi']) * 100, 2)
        c['edge_ratio'] = round(c['p'] / c['pi'], 3)
        c['kelly_full'] = round(kelly(c['p'], c['odds']), 4)
        out.append(c)
    return out


def settle(p):
    """按体彩官方赛果结算（仅三路让球/HAD/总进球/半全场/比分）"""
    r = RESULTS[p['num']]
    hs, as_ = [int(x) for x in r['score'].split(':')]
    hh, ah = [int(x) for x in r['ht'].split(':')]
    sel, mk = p['selection'], p['market']
    if mk == 'HHAD':
        d = (hs - as_) + r['line']
        res = '让胜' if d > 0 else ('让平' if d == 0 else '让负')
        return res, res == sel
    if mk == 'HAD':
        res = '主胜' if hs > as_ else ('平' if hs == as_ else '客胜')
        return res, res == sel
    if mk == 'TTG':
        g = hs + as_
        res = f'总进球{g if g <= 6 else "7+"}'
        return res, sel == (f'总进球{g}' if g <= 6 else '总进球7+')
    if mk == 'HAFU':
        r1 = '胜' if hh > ah else ('平' if hh == ah else '负')
        r2 = '胜' if hs > as_ else ('平' if hs == as_ else '负')
        res = r1 + r2
        return res, res == sel
    if mk == 'CRS':
        res = f'比分{hs}-{as_}'
        return res, res == sel
    return '-', False


def debt_snapshot(prev_balance, end_balance, rolling_days):
    """虚构债务进度：可还款额 = max(0, 余额 − 10,000)，余额达到 110,000 视为清零"""
    repay_prev = max(0.0, prev_balance - REPAY_FLOOR)
    repay_end = max(0.0, end_balance - REPAY_FLOOR)
    remaining = round(DEBT_PRINCIPAL - repay_end, 2)
    g_day = math.log(end_balance / prev_balance) if prev_balance > 0 else 0.0
    logs = [math.log(b / a) for a, b in rolling_days[-5:]]
    g_roll = sum(logs) / len(logs) if logs else 0.0

    def need(g):
        if g <= 0 or end_balance <= 0:
            return None
        return round(math.log(TARGET_BALANCE / end_balance) / g, 1)

    return {
        'repay_rule': '余额超过初始本金 10,000 的部分计为可还款额（本金不动），余额达到 110,000 视为虚构债务清零',
        'repayable_before': round(repay_prev, 2),
        'repayable_after': round(repay_end, 2),
        'repaid_today': round(repay_end - repay_prev, 2),
        'remaining_debt': remaining,
        'progress_pct': round(repay_end / DEBT_PRINCIPAL * 100, 3),
        'daily_log_growth_pct': round((math.exp(g_day) - 1) * 100, 3),
        'rolling5_log_growth_pct': round((math.exp(g_roll) - 1) * 100, 3),
        'rolling_window_days': len(logs),
        'days_to_clear_rolling5': need(g_roll),
        'days_to_clear_first_day': need(g_day),
        'days_to_clear_zero_growth': None,
        'estimate_note': ('当前速度为负（g≤0），无法估算剩余交易日' if (g_roll <= 0 or g_day <= 0)
                          else '按 ln(110000/当前余额)/g 外推，非预测'),
        'negative_growth_flag': bool(g_day < 0),
    }


def build_ledger(picks, skipped, bal, raw_total, scale):
    start = bal
    bets = []
    for i, p in enumerate(picks, 1):
        res, hit = settle(p)
        payout = round(p['stake'] * p['odds'], 2) if hit else 0.0
        bets.append({
            'bet_id': f'20261111-{i:02d}',
            'match_num': p['num'], 'league': p['league'],
            'home': p['home'], 'away': p['away'],
            'confidence': p['confidence'],
            'market': p['market'], 'selection': p['selection'],
            'odds_source': '体彩官方计算器接口（赛前在售赔率，非赛后）',
            'odds': p['odds'],
            'model_p': round(p['p'] * 100, 2),
            'market_p_raw': round(100 / p['odds'], 2),
            'market_p_devig': round(p['pi'] * 100, 2),
            'edge_pp': p['edge_pp'], 'edge_ratio': p['edge_ratio'],
            'kelly_full_pct': round(p['kelly_full'] * 100, 2),
            'kelly_fraction': FRACTION,
            'kelly_applied_pct': round(p['kelly_full'] * FRACTION * 100, 3),
            'stake_raw': p['stake_raw'],
            'cap_binding': '单注5%上限' if p['stake_raw'] > start * MAX_BET_PCT else '无',
            'stake': p['stake'],
            'stake_pct_of_balance': round(p['stake'] / start * 100, 2),
            'settled': True,
            'official_score': RESULTS[p['num']]['score'],
            'official_ht': RESULTS[p['num']]['ht'],
            'result': res, 'hit': hit,
            'payout': payout,
            'profit': round(payout - p['stake'], 2),
        })
    staked = round(sum(b['stake'] for b in bets), 2)
    payout = round(sum(b['payout'] for b in bets), 2)
    end = round(start + payout - staked, 2)
    day = {
        'date': '2026-11-11',
        'label': '2026-11-11（周三001-006，6场）',
        'start_balance': start,
        'stake_cap_total': round(start * MAX_DAY_PCT, 2),
        'stake_raw_total': round(raw_total, 2),
        'stake_scale_applied': round(scale, 4),
        'staked_total': staked,
        'payout_total': payout,
        'profit': round(payout - staked, 2),
        'return_rate': round(payout / staked * 100, 2) if staked else None,
        'end_balance': end,
        'debt_progress': debt_snapshot(start, end, [(start, end)]),
        'balance_change_pct': round((end - start) / start * 100, 3),
        'bets': bets,
        'no_bet': skipped,
        'note': '首日：5场有合格标的，004 因四分之一凯利注额 1.50 元低于最小注额 2 元不下注；006 为☆方向弃权场次，不下注。',
    }
    return day


def main():
    model = json.load(io.open(MODEL, encoding='utf-8'))
    fin = {x['num']: x for x in json.load(io.open(FINAL, encoding='utf-8'))}

    print('num  市场      选项     赔率   模型p   隐含p(去水)  优势pp  优势比  全凯利  四分之一')
    picks, skipped = [], []
    for num, m in model.items():
        if CONF[num] == '☆':
            print(f'{num}  ☆ 方向弃权（首选37.4%与第三选项31.2%差6.2pp<8pp）→ 不下注')
            skipped.append({'match_num': num, 'home': m['home'], 'away': m['away'],
                            'reason': '☆ 方向弃权：首选37.4%与第三选项31.2%仅差6.2pp（<8pp，L284），方向不成立'})
            continue
        f = fin[num]
        final_p = {'home': f['probs']['home'], 'draw': f['probs']['draw'], 'away': f['probs']['away']}
        cands = candidates(None, m, final_p)
        ok = [c for c in cands if c['edge_ratio'] >= 1.15 and c['edge_pp'] >= 3.0 and c['kelly_full'] > 0]
        if not ok:
            print(f'{num}  无合格标的（{CONF[num]}）')
            skipped.append({'match_num': num, 'home': m['home'], 'away': m['away'],
                            'reason': '无满足"优势比≥1.15 且 优势≥3pp"的推荐项'})
            continue
        # 选场仍以胜率优先：合格项中取模型概率最高者，凯利只决定注额
        ok.sort(key=lambda c: (-c['p'], -c['edge_ratio']))
        best = ok[0]
        print(f"{num}  {best['market']:<8} {best['selection']:<8} {best['odds']:<6} "
              f"{best['p']*100:5.1f}% {best['pi']*100:8.1f}% {best['edge_pp']:8.2f} "
              f"{best['edge_ratio']:7.3f} {best['kelly_full']*100:7.2f}% {best['kelly_full']*25:6.2f}%")
        best.update({'num': num, 'home': m['home'], 'away': m['away'],
                     'league': m['league'], 'confidence': CONF[num]})
        picks.append(best)

    bal = INIT_BAL
    cap_bet = bal * MAX_BET_PCT
    day_cap = bal * MAX_DAY_PCT
    raw_total = 0.0
    for p in picks:
        p['stake_raw'] = round(bal * FRACTION * p['kelly_full'], 2)
        raw_total += p['stake_raw']
    scale = min(1.0, day_cap / raw_total) if raw_total > day_cap else 1.0
    kept = []
    for p in picks:
        st = min(p['stake_raw'] * scale, cap_bet)
        p['stake'] = round(st, 2) if st >= MIN_STAKE else 0.0
        if p['stake'] <= 0:
            skipped.append({'match_num': p['num'], 'home': p['home'], 'away': p['away'],
                            'reason': f"合格（{p['market']} {p['selection']} {p['odds']}，优势比{p['edge_ratio']}），"
                                      f"但四分之一凯利注额 {st:.2f} 元低于最小注额 {MIN_STAKE:.0f} 元 → 不下注"})
        else:
            kept.append(p)
    print('\n单日上限', round(day_cap, 2), '原始合计', round(raw_total, 2), '缩放', round(scale, 4))
    for p in kept:
        print(p['num'], p['market'], p['selection'], '注额', p['stake'])

    day = build_ledger(kept, skipped, bal, raw_total, scale)
    ledger = {
        'schema_version': '1.0',
        'kind': 'virtual_bankroll_kelly_sim',
        'created_at': '2026-11-11',
        'last_updated': '2026-11-12',
        'disclaimer': '虚拟本金模拟盘，非真实资金、非真实盈亏；与真实台账（VitaTrack）完全隔离，不得引用为实际收益。'
                      'virtual_world 段为纯虚构设定，不是现实债务，也不构成还债承诺。',
        'virtual_world': {
            'is_fictional': True,
            'warning': '虚构设定：以下债务为虚构世界设定，非现实债务、非真实资金，不写入 VitaTrack，不与真实盈亏混算。',
            'debt_principal': DEBT_PRINCIPAL,
            'currency': 'CNY',
            'repay_source': 'kelly_sim_balance',
            'repay_rule': 'balance_excess_over_initial',
            'repay_rule_text': '只有余额超过初始本金 10,000.00 的部分计为可还款额，本金 10,000.00 不动；'
                               '余额达到 110,000.00（本金 + 债务）视为虚构债务清零。不采用"余额全额可还"。',
            'remaining_debt': day['debt_progress']['remaining_debt'],
            'progress_pct': day['debt_progress']['progress_pct'],
        },
        'initial_balance': INIT_BAL,
        'balance': day['end_balance'],
        'peak_balance': max(INIT_BAL, day['end_balance']),
        'drawdown_from_peak_pct': round((max(INIT_BAL, day['end_balance']) - day['end_balance']) / max(INIT_BAL, day['end_balance']) * 100, 2),
        'params': {
            'fraction_kelly': FRACTION,
            'fraction_reason': '模型概率存在系统性误差，全凯利对 p 的误差呈一阶放大；1/4 凯利把注额对 p 误差的敏感度降至 1/4，'
                               '同时保留正期望下的指数型增长。可用档位 1/2、1/4、1/8，默认固定 1/4，不随行情切换。',
            'max_bet_pct_of_balance': MAX_BET_PCT,
            'max_day_pct_of_balance': MAX_DAY_PCT,
            'min_stake': MIN_STAKE,
            'drawdown_rule': {'peak_drawdown_ge_20pct': '分数凯利降为 1/8',
                              'peak_drawdown_ge_30pct': '停手观察，直到回撤收窄至 <20% 或创新峰值'},
            'per_match_max_bets': 1,
            'parlay_allowed': False,
            'parlay_reason': '串关各腿概率高度相关且凯利不支持相关注单，串关不进入模拟盘',
        },
        'rules': {
            'candidate_pool': '仅取该场六维推荐表已列出的选项（HAD 首选/次选、让球前二、总进球首推档TOP2、半全场TOP3、比分TOP5且p≥8%）',
            'entry_threshold': 'p/(去水隐含概率) ≥ 1.15 且 p − 去水隐含概率 ≥ 3pp 且 全凯利 > 0',
            'devig': '比例去水：pi_i = (1/o_i) / Σ_j(1/o_j)，因体彩三路返还率约 87-93%，直接用 1/o 会系统性低估市场概率',
            'confidence_gate': '☆ 场次一律不投；★★ 可投方向性玩法（HAD）；★ 只投非方向玩法（让球/总进球/半全场/比分）',
            'selection_order': '合格项中按模型概率降序取第一（胜率优先），凯利只用于计算注额',
            'probability_source': 'HAD 用 L63 平局上修后的最终概率；让球/总进球/半全场/比分用模型原始矩阵概率',
            'odds_timing': '下注时点赔率（赛前在售），非赛后赔率',
        },
        'days': [day],
    }
    import os
    os.makedirs('reports/sim', exist_ok=True)
    json.dump(ledger, io.open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\nend balance', day['end_balance'], 'profit', day['profit'], 'staked', day['staked_total'], 'payout', day['payout_total'])
    for b in day['bets']:
        print(' ', b['bet_id'], b['match_num'], b['market'], b['selection'], b['odds'], b['stake'], '->', b['result'], 'HIT' if b['hit'] else 'MISS', b['profit'])


if __name__ == '__main__':
    main()
