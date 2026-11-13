# -*- coding: utf-8 -*-
"""
周四003单关平局上修计算 + 分歧规则补充
基于周三回测经验更新
"""
import json

with open(r'e:\VibeCoding\football\reports\data\analysis_20261008.json', 'r', encoding='utf-8') as f:
    matches = json.load(f)

# 003桑托斯vs弗拉门戈
match003 = matches[2]  # 索引2
print("=" * 60)
print(f"周四003 {match003['home_team']} vs {match003['away_team']}")
print(f"  原始: 主胜{match003['final_probs']['home']*100:.1f}% / 平{match003['final_probs']['draw']*100:.1f}% / 客胜{match003['final_probs']['away']*100:.1f}%")
print(f"  首推: {match003['primary']} ({match003['primary_prob']*100:.1f}%)")
print(f"  k_dist={match003['k_dist']}({match003['k_dist_prob']*100:.1f}%), k_consistent={match003['k_consistent']}")

# 规则63：单关平局上修
first_prob = match003['primary_prob']  # 客胜49.2%
draw_prob = match003['final_probs']['draw']  # 平局26.5%
gap_pp = (first_prob - draw_prob) * 100
print(f"\n  首推与平局差距: {gap_pp:.1f}pp")

if gap_pp <= 10:
    adjust = 0.14
    print(f"  档位: ≤10pp → 上修14%")
elif gap_pp <= 20:
    adjust = 0.11
    print(f"  档位: ≤20pp → 上修11%")
else:
    adjust = 0.09
    print(f"  档位: >20pp → 上修9%")

adjust = min(adjust, 0.18)

# 计算上修后概率
home_p = match003['final_probs']['home']
draw_p = match003['final_probs']['draw']
away_p = match003['final_probs']['away']

new_draw = min(draw_p + adjust, 0.65)
actual_adjust = new_draw - draw_p

# 从胜负方向按比例扣除
non_draw = home_p + away_p
ratio_home = home_p / non_draw
ratio_away = away_p / non_draw

new_home = home_p - actual_adjust * ratio_home
new_away = away_p - actual_adjust * ratio_away

# 归一化
total = new_home + new_draw + new_away
new_home /= total
new_draw /= total
new_away /= total

print(f"\n  上修后: 主胜{new_home*100:.1f}% / 平{new_draw*100:.1f}% / 客胜{new_away*100:.1f}%")
print(f"  实际上修: +{actual_adjust*100:.1f}%")

# 新首推/次选
probs = {"home": new_home, "draw": new_draw, "away": new_away}
sorted_probs = sorted(probs.items(), key=lambda x: -x[1])
print(f"  新首推: {sorted_probs[0][0]} ({sorted_probs[0][1]*100:.1f}%)")
print(f"  新次选: {sorted_probs[1][0]} ({sorted_probs[1][1]*100:.1f}%)")
print(f"  首-次差距: {(sorted_probs[0][1]-sorted_probs[1][1])*100:.1f}pp")

# 分歧规则分析
print(f"\n  分歧状态: {'是（k_dist=0平局，首推客胜）' if not match003['k_consistent'] else '否'}")
print(f"  周三回测教训: 4场分歧场次3场打出平局 → 分歧场次平局价值被低估")
print(f"  综合判断: 分歧+单关双重加持，平局价值极高")

# 004巴拉纳竞技vs米内罗竞技（分歧场次）
match004 = matches[3]
print("\n" + "=" * 60)
print(f"周四004 {match004['home_team']} vs {match004['away_team']}")
print(f"  原始: 主胜{match004['final_probs']['home']*100:.1f}% / 平{match004['final_probs']['draw']*100:.1f}% / 客胜{match004['final_probs']['away']*100:.1f}%")
print(f"  k_dist={match004['k_dist']}({match004['k_dist_prob']*100:.1f}%), k_consistent={match004['k_consistent']}")
print(f"  分歧状态: {'是（k_dist=0平局，首推主胜）' if not match004['k_consistent'] else '否'}")
print(f"  周三回测教训: 分歧场次平局概率被低估 → 平局价值提升")

print("\n" + "=" * 60)
print("周四6场分歧汇总")
for m in matches:
    div = "⚠️分歧" if not m['k_consistent'] else "✅一致"
    print(f"  {m['match_num']}: k_dist={m['k_dist']}, {div}, 首推{m['primary']}({m['primary_prob']*100:.1f}%)")
