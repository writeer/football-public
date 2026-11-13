import json
import math
from itertools import product

def poisson(k, lam):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

def calc_match(match_num, home_team, away_team, lam_h, lam_a, league, rule65_tier=0, rule63=False, el_second_leg=False, first_leg_gap=0, confidence_base=3):
    """
    Calculate full probability matrix for a match.
    rule65_tier: 0=none, 1=Tier1(+0.1-0.2), 2=Tier2(+0.3), 3=Tier3(+0.4)
    rule63: whether single-match betting is open
    el_second_leg: whether this is EL second leg
    first_leg_gap: aggregate goal difference from first leg
    """
    # Apply Rule 65 lambda up-modification
    r65_adj = {0: 0, 1: 0.15, 2: 0.3, 3: 0.4}[rule65_tier]
    if r65_adj > 0:
        # Split between home and away (favor stronger team)
        if lam_h > lam_a:
            lam_h += r65_adj * 0.6
            lam_a += r65_adj * 0.4
        else:
            lam_h += r65_adj * 0.4
            lam_a += r65_adj * 0.6

    # Apply EL second leg corrections (L009-L011)
    if el_second_leg:
        if first_leg_gap >= 3:
            # L010/L011: conservative play, lambda down 12%
            lam_h *= 0.92
            lam_a *= 0.88
        elif first_leg_gap <= 1:
            # L009: draw probability up (handled in post-processing)
            pass

    # Generate score matrix (0-5 x 0-5)
    max_goals = 6
    matrix = {}
    for h, a in product(range(max_goals), range(max_goals)):
        matrix[(h, a)] = poisson(h, lam_h) * poisson(a, lam_a)

    # HAD probabilities
    home_win = sum(v for (h, a), v in matrix.items() if h > a)
    draw = sum(v for (h, a), v in matrix.items() if h == a)
    away_win = sum(v for (h, a), v in matrix.items() if h < a)
    total = home_win + draw + away_win
    home_win /= total
    draw /= total
    away_win /= total

    # Apply Rule 63 (single-match draw up-modification)
    r63_adj = 0
    if rule63:
        gap = abs(home_win - draw) * 100
        if gap <= 10:
            r63_adj = 0.13
        elif gap <= 20:
            r63_adj = 0.11
        else:
            r63_adj = 0.08
        draw += r63_adj
        # Compress H/A proportionally
        if home_win > away_win:
            home_win -= r63_adj * (home_win / (home_win + away_win))
            away_win -= r63_adj * (away_win / (home_win + away_win))
        else:
            away_win -= r63_adj * (away_win / (home_win + away_win))
            home_win -= r63_adj * (home_win / (home_win + away_win))

    # EL second leg draw up (L009)
    if el_second_leg and first_leg_gap <= 1:
        draw += 0.06
        if home_win > away_win:
            home_win -= 0.03
        else:
            away_win -= 0.03
    elif el_second_leg and first_leg_gap >= 3:
        draw += 0.04

    # Normalize
    total = home_win + draw + away_win
    home_win /= total
    draw /= total
    away_win /= total

    # TTG probabilities
    ttg = {}
    for goals in range(8):
        if goals < 6:
            prob = sum(v for (h, a), v in matrix.items() if h + a == goals)
        else:
            prob = sum(v for (h, a), v in matrix.items() if h + a >= 6)
        ttg[goals] = prob / total

    # Score TOP sorted by probability
    scores_sorted = sorted(matrix.items(), key=lambda x: x[1], reverse=True)
    top5_scores = [(f"{h}:{a}", prob/total) for (h, a), prob in scores_sorted[:5]]

    # Half-time scores (lambda * 0.45)
    ht_lam_h = lam_h * 0.45
    ht_lam_a = lam_a * 0.45
    ht_matrix = {}
    for h, a in product(range(4), range(4)):
        ht_matrix[(h, a)] = poisson(h, ht_lam_h) * poisson(a, ht_lam_a)
    
    ht_scores_sorted = sorted(ht_matrix.items(), key=lambda x: x[1], reverse=True)
    ht_top3 = [(f"{h}:{a}", prob) for (h, a), prob in ht_scores_sorted[:3]]

    # HTFT (half-time/full-time)
    htft = {}
    ht_w = sum(v for (h, a), v in ht_matrix.items() if h > a)
    ht_d = sum(v for (h, a), v in ht_matrix.items() if h == a)
    ht_l = sum(v for (h, a), v in ht_matrix.items() if h < a)
    
    # Simplified HTFT calculation
    combos = {
        "胜胜": ht_w * home_win,
        "胜平": ht_w * draw,
        "胜负": ht_w * away_win,
        "平胜": ht_d * home_win,
        "平平": ht_d * draw,
        "平负": ht_d * away_win,
        "负胜": ht_l * home_win,
        "负平": ht_l * draw,
        "负负": ht_l * away_win,
    }
    htft_total = sum(combos.values())
    for k in combos:
        combos[k] /= htft_total
    htft_sorted = sorted(combos.items(), key=lambda x: x[1], reverse=True)

    # Print results
    print(f"\n{'='*80}")
    print(f"{match_num} {home_team} vs {away_team} ({league})")
    print(f"Lambda: H={lam_h:.2f} A={lam_a:.2f} Total={lam_h+lam_a:.2f}")
    print(f"Rule65: Tier={rule65_tier} adj={r65_adj}")
    print(f"Rule63: {'YES' if rule63 else 'NO'} adj={r63_adj:.2f}")
    print(f"EL 2nd leg: {el_second_leg}, first leg gap: {first_leg_gap}")
    print(f"\nHAD: 主胜={home_win*100:.1f}% 平={draw*100:.1f}% 客胜={away_win*100:.1f}%")
    
    # HAD recommendation
    had_sorted = [("主胜", home_win), ("平", draw), ("客胜", away_win)]
    had_sorted.sort(key=lambda x: x[1], reverse=True)
    print(f"HAD首选: {had_sorted[0][0]}({had_sorted[0][1]*100:.1f}%) 次选: {had_sorted[1][0]}({had_sorted[1][1]*100:.1f}%)")
    
    print(f"\nTTG:")
    for g in range(7):
        label = f"{g}球" if g < 6 else "7+球"
        print(f"  {label}: {ttg[g]*100:.1f}%")
    ttg_sorted = sorted(ttg.items(), key=lambda x: x[1], reverse=True)
    print(f"TTG首选: {ttg_sorted[0][0]}球({ttg_sorted[0][1]*100:.1f}%) 次选: {ttg_sorted[1][0]}球({ttg_sorted[1][1]*100:.1f}%)")
    
    print(f"\n比分TOP5:")
    for score, prob in top5_scores:
        print(f"  {score}: {prob*100:.1f}%")
    
    print(f"\n半场比分TOP3:")
    for score, prob in ht_top3:
        print(f"  {score}: {prob*100:.1f}%")
    
    print(f"\n半全场TOP3:")
    for name, prob in htft_sorted[:3]:
        print(f"  {name}: {prob*100:.1f}%")
    
    return {
        "match": match_num,
        "lambda_h": round(lam_h, 2),
        "lambda_a": round(lam_a, 2),
        "had": {"home": round(home_win*100, 1), "draw": round(draw*100, 1), "away": round(away_win*100, 1)},
        "ttg_top2": [(ttg_sorted[0][0], round(ttg_sorted[0][1]*100, 1)), (ttg_sorted[1][0], round(ttg_sorted[1][1]*100, 1))],
        "crs_top5": [(s, round(p*100, 1)) for s, p in top5_scores],
        "htft_top3": [(n, round(p*100, 1)) for n, p in htft_sorted[:3]],
        "ht_top3": [(s, round(p*100, 1)) for s, p in ht_top3],
    }


# ============ MATCH DATA ============
# Based on research findings, odds calibration, and rule applications

# 001: Plzen vs Red Star (EL 2nd leg, Red Star 3-0 up)
# Red Star leading 3-0, away but will play conservatively
# Plzen at home, new coach, needs chase but weaker
# Value: 2.18x → Rule65 Tier3 triggered
# L010/L011: EL 2nd leg gap≥3 → conservative, lambda down
# No single-match
r001 = calc_match("周四001", "比尔森", "贝尔格莱德红星", 
    lam_h=1.10, lam_a=0.85, league="欧联附加赛次回合",
    rule65_tier=3, rule63=False, el_second_leg=True, first_leg_gap=3)

# 002: Omonia vs Sint-Truiden (EL 2nd leg, STVV 1-0 up)
# STVV 1-0 up from 94th min goal
# Omonia strong at home but missing key striker (Yovetici suspended) + others
# Value: 1.59x → Rule65 NOT triggered
# L009: EL 2nd leg gap≤1 → draw up
# No single-match
r002 = calc_match("周四002", "奥莫尼亚", "圣图尔登",
    lam_h=1.05, lam_a=0.90, league="欧联附加赛次回合",
    rule65_tier=0, rule63=False, el_second_leg=True, first_leg_gap=1)

# 003: Salzburg vs Mjallby (EL 2nd leg, Salzburg 1-0 up) — 单关
# Salzburg massive favorite (5.97x), 1-0 up
# Salzburg 8 injuries but Tabakovic fit (4 EL goals)
# Mjallby 11th in Allsvenskan, poor form
# Rule65: 5.97x → Tier3 +0.4 TRIGGERED
# Rule63: single-match, but L032: massive favorite → don't push draw
# L050: first leg gap≤1 → confidence downgrade
r003 = calc_match("周四003", "萨尔茨堡", "米亚尔比",
    lam_h=2.00, lam_a=0.50, league="欧联附加赛次回合",
    rule65_tier=3, rule63=True, el_second_leg=True, first_leg_gap=1)

# 004: Aarhus vs Benfica (EL 2nd leg, Benfica 3-1 up)
# Benfica massive favorite (10.4x), 3-1 up, just won 7-0!
# Aarhus 10th in Danish Superliga, poor form
# Rule65: 10.4x → Tier3 +0.4 TRIGGERED
# L024: strong team hot → lambda up
# Benfica injuries: Pavlidis, Bah, Bruma
# No single-match
r004 = calc_match("周四004", "奥胡斯", "本菲卡",
    lam_h=0.90, lam_a=1.80, league="欧联附加赛次回合",
    rule65_tier=3, rule63=False, el_second_leg=True, first_leg_gap=2)

# 005: Ferencvaros vs Trabzonspor (EL 2nd leg, Ferencvaros 1-0 up)
# Ferencvaros 1-0 up from away goal
# Trabzonspor 4.1x value but MASSIVE EL ineligibility (8+ players out)
# Ferencvaros good form, no injuries
# Rule65: 4.1x → triggered but Trabzonspor heavily depleted
# L050: first leg gap≤1 → confidence downgrade
# No single-match
r005 = calc_match("周四005", "费伦茨瓦罗斯", "特拉布宗体育",
    lam_h=1.30, lam_a=0.95, league="欧联附加赛次回合",
    rule65_tier=2, rule63=False, el_second_leg=True, first_leg_gap=1)

# 006: Anderlecht vs Kairat (EL 2nd leg, Anderlecht 3-0 up) — 单关
# Anderlecht massive favorite (9.9x), 3-0 up
# Kairat tiny (€9.20m), poor form, already eliminated from CL
# Rule65: 9.9x → Tier3 +0.4 TRIGGERED
# L011: EL 2nd leg gap≥3 → conservative, lambda down 12%
# Rule63: single-match, but L032: massive favorite → don't push draw
r006 = calc_match("周四006", "安德莱赫特", "阿拉木图凯拉特",
    lam_h=1.70, lam_a=0.50, league="欧联附加赛次回合",
    rule65_tier=3, rule63=True, el_second_leg=True, first_leg_gap=3)

# 007: Celta vs Osasuna (La Liga Matchday 1) — 单关
# Celta 6th last season, strong at home
# Osasuna 16th last season, poor away
# Value: 2.4x → Rule65 Tier1 light +0.15
# L035: new season → lambda up +0.5
# Rule63: single-match → draw up +8%
# H2H: Celta 3W 2L, high-scoring
# Celta injuries: Borja Iglesias (doubtful), 3 long-term out
r007 = calc_match("周四007", "维戈塞尔塔", "奥萨苏纳",
    lam_h=1.45, lam_a=1.00, league="西甲第1轮",
    rule65_tier=1, rule63=True, el_second_leg=False, first_leg_gap=0)

# 008: Barcelona vs Athletic Bilbao (La Liga Matchday 1)
# Barcelona massive favorite (5.3x), 5-0 win vs Elche last week
# Athletic: 3-1 loss to Sevilla, 4 consecutive losses
# H2H: Barcelona 5W 0D 0L, 15-0 goals!
# Rule65: 5.3x → Tier1 light +0.15 (but Barcelona already scoring)
# L035: new season → lambda up
# L041: high confidence + conservative = contradiction → align TTG up
# Barcelona injuries: de Jong, Bardghji (ACL), Gavi doubtful
# Athletic injuries: Eguiluz (ACL), Vivian, Berchiche suspended
r008 = calc_match("周四008", "巴塞罗那", "毕尔巴鄂竞技",
    lam_h=2.20, lam_a=0.60, league="西甲第1轮",
    rule65_tier=1, rule63=False, el_second_leg=False, first_leg_gap=0)

# 009: Internacional vs Gremio (Copa do Brasil QF 1st leg)
# Historic Gre-Nal derby!
# Internacional: 15th in Brasileirao, poor form (1W in 10)
# Gremio: 16th in Brasileirao, poor form, away poor
# Internacional: Rochet (GK) out, Mercado (CB) out → defensive crisis
# Gremio: Kannemann suspended, but Nico Williams available
# H2H: 2026 4 meetings - 1W 1W 2D
# Rule65: Brazilian Cup = Tier3, but value gap unclear
# L005: Cup 1st leg → stoppage time equalizer risk
# Brazilian Cup: draw rate high (28%+)
r009 = calc_match("周四009", "巴西国际", "格雷米奥",
    lam_h=1.15, lam_a=1.00, league="巴西杯1/4决赛首回合",
    rule65_tier=0, rule63=False, el_second_leg=False, first_leg_gap=0)

# Save results
results = [r001, r002, r003, r004, r005, r006, r007, r008, r009]
with open(r'e:\VibeCoding\football\reports\data\260827_thursday_predictions.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n\n{'='*80}")
print("All 9 matches calculated. Results saved to 260827_thursday_predictions.json")
