# -*- coding: utf-8 -*-
"""
2026-10-08 周四回测验证脚本
"""
import json

with open(r'e:\VibeCoding\football\reports\data\analysis_20261008.json', 'r', encoding='utf-8') as f:
    predictions = json.load(f)

# 实际赛果（体彩官网+多源交叉验证）
results = {
    "周四001": {"ht_score": "3-0", "ft_score": "6-0", "home_goals": 6, "away_goals": 0, "total_goals": 6, "result": "home", "htft": "主-主"},
    "周四002": {"ht_score": "0-1", "ft_score": "0-1", "home_goals": 0, "away_goals": 1, "total_goals": 1, "result": "away", "htft": "客-客"},
    "周四003": {"ht_score": "0-2", "ft_score": "2-2", "home_goals": 2, "away_goals": 2, "total_goals": 4, "result": "draw", "htft": "客-平"},
    "周四004": {"ht_score": "1-0", "ft_score": "1-0", "home_goals": 1, "away_goals": 0, "total_goals": 1, "result": "home", "htft": "主-主"},
    "周四005": {"ht_score": "1-0", "ft_score": "4-0", "home_goals": 4, "away_goals": 0, "total_goals": 4, "result": "home", "htft": "主-主"},
    "周四006": {"ht_score": "1-0", "ft_score": "1-0", "home_goals": 1, "away_goals": 0, "total_goals": 1, "result": "home", "htft": "主-主"},
}

# 003单关平局上修后的概率（之前计算的）
# 上修后：客胜43.2% / 平35.5% / 主胜21.3%
match003_updated = {
    "home": 0.213, "draw": 0.355, "away": 0.432
}

dir_map = {"home": "主胜", "draw": "平", "away": "客胜"}

print("=" * 100)
print("周四6场回测验证")
print("=" * 100)

stats = {
    "dir_first": 0, "dir_second": 0, "dir_miss": 0,
    "hhad_first": 0, "hhad_second": 0, "hhad_miss": 0,
    "ttg_hit": 0, "ttg_miss": 0,
    "htft_hit": 0, "htft_miss": 0,
    "score_hit": 0, "score_miss": 0,
    "div_dir_first": 0, "div_dir_total": 0,
    "cons_dir_first": 0, "cons_dir_total": 0,
}

for pred in predictions:
    mn = pred["match_num"]
    res = results[mn]
    
    print(f"\n{'='*80}")
    print(f"{mn} {pred['home_team']} vs {pred['away_team']} ({pred['league']})")
    print(f"  赛果: {res['ft_score']} (半场{res['ht_score']}) | 总进球{res['total_goals']}球 | {dir_map[res['result']]} | 半全场{res['htft']}")
    print(f"  分歧状态: {'⚠️分歧' if not pred['k_consistent'] else '✅一致'} (k_dist={pred['k_dist']})")
    
    # 方向 - 003用单关上修后的概率
    if mn == "周四003":
        probs = match003_updated
        sorted_dir = sorted(probs.items(), key=lambda x: -x[1])
        primary = sorted_dir[0][0]
        primary_prob = sorted_dir[0][1]
        secondary = sorted_dir[1][0]
        secondary_prob = sorted_dir[1][1]
        print(f"  方向(单关上修后): 首选{dir_map[primary]}({primary_prob*100:.1f}%)/次选{dir_map[secondary]}({secondary_prob*100:.1f}%)")
    else:
        primary = pred["primary"]
        primary_prob = pred["primary_prob"]
        secondary = pred["secondary"]
        secondary_prob = pred["secondary_prob"]
        print(f"  方向: 首选{dir_map[primary]}({primary_prob*100:.1f}%)/次选{dir_map[secondary]}({secondary_prob*100:.1f}%)")
    
    actual_dir = res["result"]
    
    if actual_dir == primary:
        dir_status = "✅首"
        stats["dir_first"] += 1
        if not pred['k_consistent']:
            stats["div_dir_first"] += 1
        else:
            stats["cons_dir_first"] += 1
    elif actual_dir == secondary:
        dir_status = "✅次"
        stats["dir_second"] += 1
    else:
        dir_status = "❌"
        stats["dir_miss"] += 1
    
    if not pred['k_consistent']:
        stats["div_dir_total"] += 1
    else:
        stats["cons_dir_total"] += 1
    
    print(f"  → 实际{dir_map[actual_dir]} → {dir_status}")
    
    # 让球
    hhad_line = pred["hhad_line"]
    hhad_probs = pred["hhad_probs"]
    hhad_sorted = sorted(hhad_probs.items(), key=lambda x: -x[1])
    hhad_first = hhad_sorted[0][0]
    hhad_second = hhad_sorted[1][0]
    
    home_goals = res["home_goals"]
    away_goals = res["away_goals"]
    
    if hhad_line > 0:
        adj_home = home_goals + hhad_line
        adj_away = away_goals
    else:
        adj_home = home_goals + hhad_line
        adj_away = away_goals
    
    if adj_home > adj_away:
        hhad_actual = "home"
    elif adj_home == adj_away:
        hhad_actual = "draw"
    else:
        hhad_actual = "away"
    
    if hhad_actual == hhad_first:
        hhad_status = "✅首"
        stats["hhad_first"] += 1
    elif hhad_actual == hhad_second:
        hhad_status = "✅次"
        stats["hhad_second"] += 1
    else:
        hhad_status = "❌"
        stats["hhad_miss"] += 1
    
    print(f"  让球({hhad_line:+d}): 首选让{dir_map[hhad_first]}({hhad_probs[hhad_first]*100:.1f}%)/次选让{dir_map[hhad_second]}({hhad_probs[hhad_second]*100:.1f}%) → 让球后{adj_home}-{adj_away}=让{dir_map[hhad_actual]} → {hhad_status}")
    
    # 总进球
    ttg_sorted = pred["ttg_sorted"]
    ttg_first = int(ttg_sorted[0][0])
    ttg_second = int(ttg_sorted[1][0])
    actual_ttg = res["total_goals"]
    
    if actual_ttg == ttg_first:
        ttg_status = "✅首"
        stats["ttg_hit"] += 1
    elif actual_ttg == ttg_second:
        ttg_status = "✅(2)"
        stats["ttg_hit"] += 1
    else:
        ttg_status = f"❌(实际{actual_ttg}球)"
        stats["ttg_miss"] += 1
    
    print(f"  总进球: 预测{ttg_first}球({ttg_sorted[0][1]*100:.1f}%)/{ttg_second}球({ttg_sorted[1][1]*100:.1f}%) → 实际{actual_ttg}球 → {ttg_status}")
    
    # 半全场
    htft_top3 = [item[0] for item in pred["top3_htft"]]
    actual_htft = res["htft"]
    
    if actual_htft == htft_top3[0]:
        htft_status = "✅首"
        stats["htft_hit"] += 1
    elif actual_htft in htft_top3[1:]:
        idx = htft_top3.index(actual_htft) + 1
        htft_status = f"✅({idx})"
        stats["htft_hit"] += 1
    else:
        htft_status = f"❌(实际{actual_htft})"
        stats["htft_miss"] += 1
    
    print(f"  半全场: 预测{'/'.join(htft_top3)} → 实际{actual_htft} → {htft_status}")
    
    # 比分
    top5 = pred["top5_scores"]
    actual_score = f"{home_goals}-{away_goals}"
    score_hit = False
    for i, (h, a, p) in enumerate(top5):
        if h == home_goals and a == away_goals:
            score_hit = True
            print(f"  比分: 实际{actual_score} → ✅(TOP{i+1}, {p*100:.1f}%)")
            stats["score_hit"] += 1
            break
    if not score_hit:
        print(f"  比分: 预测{','.join([f'{s[0]}-{s[1]}' for s in top5])} → 实际{actual_score} → ❌")
        stats["score_miss"] += 1

# 汇总
n = len(predictions)
print(f"\n{'='*80}")
print("命中率统计")
print(f"{'='*80}")
print(f"方向(首选+次选): {stats['dir_first']+stats['dir_second']}/{n} = {(stats['dir_first']+stats['dir_second'])/n*100:.1f}%")
print(f"  首选命中: {stats['dir_first']}/{n} = {stats['dir_first']/n*100:.1f}%")
print(f"  次选命中: {stats['dir_second']}/{n} = {stats['dir_second']/n*100:.1f}%")
print(f"  未中: {stats['dir_miss']}/{n}")
print(f"让球(首选+次选): {stats['hhad_first']+stats['hhad_second']}/{n} = {(stats['hhad_first']+stats['hhad_second'])/n*100:.1f}%")
print(f"  首选命中: {stats['hhad_first']}/{n} = {stats['hhad_first']/n*100:.1f}%")
print(f"  次选命中: {stats['hhad_second']}/{n} = {stats['hhad_second']/n*100:.1f}%")
print(f"  未中: {stats['hhad_miss']}/{n}")
print(f"总进球TOP2: {stats['ttg_hit']}/{n} = {stats['ttg_hit']/n*100:.1f}%")
print(f"半全场TOP3: {stats['htft_hit']}/{n} = {stats['htft_hit']/n*100:.1f}%")
print(f"比分TOP5: {stats['score_hit']}/{n} = {stats['score_hit']/n*100:.1f}%")
print()
print(f"分歧场次首选命中率: {stats['div_dir_first']}/{stats['div_dir_total']} = {stats['div_dir_first']/max(1,stats['div_dir_total'])*100:.1f}%")
print(f"一致场次首选命中率: {stats['cons_dir_first']}/{stats['cons_dir_total']} = {stats['cons_dir_first']/max(1,stats['cons_dir_total'])*100:.1f}%")
