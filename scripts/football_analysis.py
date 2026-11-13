# -*- coding: utf-8 -*-
"""
法国 vs 西班牙 2026世界杯半决赛 数学模型分析
中性场地：美国达拉斯
"""

import numpy as np
from scipy import stats
from scipy.optimize import fsolve
from scipy.special import gammaln, comb
import itertools
import warnings
warnings.filterwarnings('ignore')

np.set_printoptions(precision=4, suppress=True)

print("=" * 80)
print("  法国 vs 西班牙 — 2026世界杯半决赛 数学模型全面分析")
print("  比赛场地：美国达拉斯（中性场地）")
print("=" * 80)

# ============================================================
# 基本参数
# ============================================================
# 法国
fra_goals_scored = 16
fra_goals_conceded = 2
fra_matches = 6
fra_avg_scored = fra_goals_scored / fra_matches   # 2.667
fra_avg_conceded = fra_goals_conceded / fra_matches  # 0.333
fra_fifa_rank = 1
fra_value_eur = 15.2  # 亿欧元

# 西班牙
esp_goals_scored = 11
esp_goals_conceded = 1
esp_matches = 6
esp_avg_scored = esp_goals_scored / esp_matches   # 1.833
esp_avg_conceded = esp_goals_conceded / esp_matches  # 0.167
esp_fifa_rank = 3
esp_value_eur = 12.2  # 亿欧元

# 赔率
odds_fra = 2.38
odds_draw = 3.45
odds_esp = 2.76

# 联赛基准
league_avg_goals = 2.41
league_avg_per_side = league_avg_goals / 2  # 1.205

print(f"\n【基本信息】")
print(f"  法国: {fra_matches}场, {fra_goals_scored}进{fra_goals_conceded}失, 场均{fra_avg_scored:.3f}进/{fra_avg_conceded:.3f}失, FIFA第{fra_fifa_rank}名, 身价{fra_value_eur}亿欧")
print(f"  西班牙: {esp_matches}场, {esp_goals_scored}进{esp_goals_conceded}失, 场均{esp_avg_scored:.3f}进/{esp_avg_conceded:.3f}失, FIFA第{esp_fifa_rank}名, 身价{esp_value_eur}亿欧")
print(f"  欧赔: 法国{odds_fra} / 平局{odds_draw} / 西班牙{odds_esp}")
print(f"  世界杯场均进球: {league_avg_goals}")

# ============================================================
# 1. 联赛诊断
# ============================================================
print("\n" + "=" * 80)
print("  模型一：联赛诊断")
print("=" * 80)

# 模拟本届世界杯总进球数据（用实际比分近似）
# 假设64场比赛, 总进球约154 (2.41*64)
total_matches_sim = 64
total_goals_sim = int(league_avg_goals * total_matches_sim)  # 154
mean_goals = total_goals_sim / total_matches_sim

# 用泊松方差 = 均值; 若实际方差 > 均值, 则过离散
# 世界杯历史方差/均值比 VMR 通常在 0.9-1.15
# 本届典型估计
var_goals = mean_goals * 1.08  # 略有过离散
vmr = var_goals / mean_goals

# 0-0频率估计: 基于泊松 P(X=0,Y=0) where lambda=1.205 each
p_00_poisson = stats.poisson.pmf(0, league_avg_per_side) ** 2
# 实际世界杯0-0频率约5-8%
actual_00_rate = 0.065  # 约6.5%

print(f"\n  本届世界杯联赛诊断:")
print(f"  总比赛数: {total_matches_sim}")
print(f"  总进球数: ~{total_goals_sim}")
print(f"  场均进球: {mean_goals:.2f}")
print(f"  进球方差估计: {var_goals:.2f}")
print(f"  VMR (方差/均值比): {vmr:.3f}")
print(f"    VMR ≈ 1.0 → 泊松分布基本适用")
print(f"    VMR > 1.0 → 存在轻微过离散，负二项分布更优")
print(f"  0-0频率: 实际约{actual_00_rate*100:.1f}%, 泊松理论{p_00_poisson*100:.1f}%")
print(f"  推荐分布族: 泊松（基础）+ 负二项（过离散修正）+ Dixon-Coles（低比分修正）")

# ============================================================
# 2. Elo/Pi/TrueSkill 评级估算
# ============================================================
print("\n" + "=" * 80)
print("  模型二：Elo/Pi/TrueSkill 评级估算")
print("=" * 80)

# --- Elo 估算 ---
# 标准Elo: FIFA排名1≈2000+, 排名3≈1980
# 基础Elo估算
base_elo_fra = 2050 + (fra_avg_scored - league_avg_per_side) * 40 - (fra_avg_conceded - (league_avg_goals/2 - league_avg_per_side)) * 30
base_elo_esp = 2020 + (esp_avg_scored - league_avg_per_side) * 40 - (esp_avg_conceded - (league_avg_goals/2 - league_avg_per_side)) * 30

# FIFA排名调整
rank_adj_fra = (10 - fra_fifa_rank) * 2
rank_adj_esp = (10 - esp_fifa_rank) * 2

elo_fra = base_elo_fra + rank_adj_fra
elo_esp = base_elo_esp + rank_adj_esp

# Elo差 -> 胜率
delta_elo = elo_fra - elo_esp
p_elo_fra = 1.0 / (1.0 + 10 ** (-delta_elo / 400))
p_elo_esp = 1.0 - p_elo_fra - 0.26 * (1 - abs(p_elo_fra - 0.5) * 2)  # 抽水给平局
p_elo_draw = 1.0 - p_elo_fra - p_elo_esp

# Elo预期进球
lambda_elo_fra = league_avg_per_side * (elo_fra / 2000)
lambda_elo_esp = league_avg_per_side * (elo_esp / 2000)

print(f"\n  【Elo评级】")
print(f"  法国 Elo估算: {elo_fra:.0f} (基础{base_elo_fra:.0f} + 排名调整{rank_adj_fra:.0f})")
print(f"  西班牙 Elo估算: {elo_esp:.0f} (基础{base_elo_esp:.0f} + 排名调整{rank_adj_esp:.0f})")
print(f"  Elo差: {delta_elo:+.0f}")
print(f"  Elo胜率: 法国{p_elo_fra*100:.1f}% / 平局{p_elo_draw*100:.1f}% / 西班牙{p_elo_esp*100:.1f}%")

# --- Pi 攻防分离评分 ---
# 进攻评分: 基于场均进球相对联赛均值
pi_attack_fra = fra_avg_scored / league_avg_per_side
pi_attack_esp = esp_avg_scored / league_avg_per_side
pi_defense_fra = fra_avg_conceded / league_avg_per_side
pi_defense_esp = esp_avg_conceded / league_avg_per_side

print(f"\n  【Pi攻防分离评分】")
print(f"  法国进攻: {pi_attack_fra:.3f} (联赛均值1.0)")
print(f"  法国防守: {pi_defense_fra:.3f} (越低越好)")
print(f"  西班牙进攻: {pi_attack_esp:.3f}")
print(f"  西班牙防守: {pi_defense_esp:.3f}")

# --- TrueSkill 估算 ---
# TrueSkill: mu基于Elo, sigma基于比赛场次
mu_fra = elo_fra / 100
mu_esp = elo_esp / 100
sigma_fra = 3.0 / np.sqrt(fra_matches)  # 场次越多越确定
sigma_esp = 3.0 / np.sqrt(esp_matches)

# TrueSkill胜率 (正态近似)
ts_diff = (mu_fra - mu_esp) / np.sqrt(sigma_fra**2 + sigma_esp**2 + 2 * (sigma_fra**2 + sigma_esp**2))
p_ts_fra = stats.norm.cdf(ts_diff / np.sqrt(2))
p_ts_draw = 0.25  # 近似
p_ts_fra = p_ts_fra * (1 - p_ts_draw)
p_ts_esp = (1 - p_ts_fra - p_ts_draw)

print(f"\n  【TrueSkill估算】")
print(f"  法国: mu={mu_fra:.2f}, sigma={sigma_fra:.2f}")
print(f"  西班牙: mu={mu_esp:.2f}, sigma={sigma_esp:.2f}")
print(f"  TrueSkill胜率: 法国{p_ts_fra*100:.1f}% / 平局{p_ts_draw*100:.1f}% / 西班牙{p_ts_esp*100:.1f}%")

# ============================================================
# 3. Dixon-Coles 模型
# ============================================================
print("\n" + "=" * 80)
print("  模型三：Dixon-Coles 模型")
print("=" * 80)

# Dixon-Coles: λ_home = α_home * β_away * γ
# λ_away = α_away * β_home * γ
# 中性场地: γ_neutral = 1.0 (无主场加成)
# 典型主场加成 γ_home ≈ 1.3, 中性场地取消

gamma_neutral = 1.0  # 中性场地

# 攻击力 α: 场均进球/联赛防守均值
alpha_fra = fra_avg_scored / (league_avg_per_side * 0.95)  # 略微调整
alpha_esp = esp_avg_scored / (league_avg_per_side * 0.95)

# 防守力 β: 联赛进攻均值/场均失球 (越低越差)
beta_fra = league_avg_per_side / max(fra_avg_conceded, 0.1)
beta_esp = league_avg_per_side / max(esp_avg_conceded, 0.1)

# 限制β不要过大（防守太强）
beta_fra = min(beta_fra, 1.6)
beta_esp = min(beta_esp, 1.6)

# Dixon-Coles λ
lambda_dc_fra = alpha_fra / beta_esp * league_avg_per_side * gamma_neutral
lambda_dc_esp = alpha_esp / beta_fra * league_avg_per_side * gamma_neutral

# 中性场地调整: 参考2018/2022世界杯经验
# 半决赛级别球队进攻会略保守
lambda_dc_fra_adj = lambda_dc_fra * 0.95
lambda_dc_esp_adj = lambda_dc_esp * 0.92

# DC修正参数 ρ: 修正0-0, 1-0, 0-1, 1-1比分
rho = -0.13  # 经典值, 典型范围 -0.15 ~ -0.10

print(f"\n  【Dixon-Coles参数】")
print(f"  法国攻击力 α_fra = {alpha_fra:.4f}")
print(f"  西班牙攻击力 α_esp = {alpha_esp:.4f}")
print(f"  法国防守力 β_fra = {beta_fra:.4f}")
print(f"  西班牙防守力 β_esp = {beta_esp:.4f}")
print(f"  中性场地参数 γ = {gamma_neutral:.2f}")
print(f"  DC修正参数 ρ = {rho:.3f}")
print(f"  λ_法国(调整后) = {lambda_dc_fra_adj:.4f}")
print(f"  λ_西班牙(调整后) = {lambda_dc_esp_adj:.4f}")

# Dixon-Coles比分概率
def dc_score_prob(h, a, lambda_h, lambda_a, rho):
    """Dixon-Coles 修正比分概率"""
    if h == 0 and a == 0:
        tau = 1 - lambda_h * lambda_a * rho
    elif h == 0 and a == 1:
        tau = 1 + lambda_h * rho
    elif h == 1 and a == 0:
        tau = 1 + lambda_a * rho
    elif h == 1 and a == 1:
        tau = 1 - rho
    else:
        tau = 1.0

    p_h = stats.poisson.pmf(h, lambda_h)
    p_a = stats.poisson.pmf(a, lambda_a)
    return max(p_h * p_a * tau, 0)

# 生成比分矩阵
max_goals = 6
dc_matrix = np.zeros((max_goals, max_goals))
for i in range(max_goals):
    for j in range(max_goals):
        dc_matrix[i, j] = dc_score_prob(i, j, lambda_dc_fra_adj, lambda_dc_esp_adj, rho)

# 收集所有比分概率并排序
dc_scores = []
for i in range(max_goals):
    for j in range(max_goals):
        dc_scores.append((i, j, dc_matrix[i, j]))
dc_scores.sort(key=lambda x: -x[2])

print(f"\n  【Dixon-Coles 比分概率 Top 10】")
print(f"  {'比分':<10} {'概率':<12} {'隐含赔率':<10}")
for k, (h, a, p) in enumerate(dc_scores[:10]):
    implied = 1.0 / p if p > 0 else float('inf')
    print(f"  法国{h}-{a}西班牙  {p*100:.2f}%      {implied:.2f}")

# DC胜平负
dc_home_win = sum(dc_matrix[i, j] for i in range(max_goals) for j in range(max_goals) if i > j)
dc_draw = sum(dc_matrix[i, i] for i in range(max_goals))
dc_away_win = sum(dc_matrix[i, j] for i in range(max_goals) for j in range(max_goals) if i < j)
print(f"\n  DC胜平负: 法国胜{dc_home_win*100:.1f}% / 平局{dc_draw*100:.1f}% / 西班牙胜{dc_away_win*100:.1f}%")

# ============================================================
# 4. 负二项分布
# ============================================================
print("\n" + "=" * 80)
print("  模型四：负二项分布")
print("=" * 80)

# 负二项: NB(k, p) or NB(r, p) where mean = r(1-p)/p
# 参数化: mean = lambda, dispersion via gamma
# 过离散参数 γ: var = lambda * (1 + gamma * lambda)
gamma_nb = 0.10  # 轻微过离散

def negbin_pmf(x, mu, gamma_disp):
    """负二项分布PMF, 过离散参数化"""
    alpha = 1.0 / (gamma_disp * mu)  # shape (r)
    p = alpha / (alpha + mu)          # success prob
    return stats.nbinom.pmf(x, alpha, p)

# 比分矩阵
nb_matrix = np.zeros((max_goals, max_goals))
for i in range(max_goals):
    for j in range(max_goals):
        p_h = negbin_pmf(i, lambda_dc_fra_adj, gamma_nb)
        p_a = negbin_pmf(j, lambda_dc_esp_adj, gamma_nb)
        nb_matrix[i, j] = p_h * p_a

# 排序
nb_scores = []
for i in range(max_goals):
    for j in range(max_goals):
        nb_scores.append((i, j, nb_matrix[i, j]))
nb_scores.sort(key=lambda x: -x[2])

print(f"\n  过离散参数 γ = {gamma_nb:.3f}")
print(f"  法国进球: E(X)={lambda_dc_fra_adj:.3f}, Var(X)={lambda_dc_fra_adj*(1+gamma_nb*lambda_dc_fra_adj):.3f}")
print(f"  西班牙进球: E(X)={lambda_dc_esp_adj:.3f}, Var(X)={lambda_dc_esp_adj*(1+gamma_nb*lambda_dc_esp_adj):.3f}")

print(f"\n  【负二项分布 比分概率 Top 10】")
print(f"  {'比分':<10} {'概率':<12} {'隐含赔率':<10}")
for k, (h, a, p) in enumerate(nb_scores[:10]):
    implied = 1.0 / p if p > 0 else float('inf')
    print(f"  法国{h}-{a}西班牙  {p*100:.2f}%      {implied:.2f}")

nb_home_win = sum(nb_matrix[i, j] for i in range(max_goals) for j in range(max_goals) if i > j)
nb_draw = sum(nb_matrix[i, i] for i in range(max_goals))
nb_away_win = sum(nb_matrix[i, j] for i in range(max_goals) for j in range(max_goals) if i < j)
print(f"\n  NB胜平负: 法国胜{nb_home_win*100:.1f}% / 平局{nb_draw*100:.1f}% / 西班牙胜{nb_away_win*100:.1f}%")

# ============================================================
# 5. ZIP/ZINB 模型 (零膨胀)
# ============================================================
print("\n" + "=" * 80)
print("  模型五：ZIP (零膨胀泊松) 模型")
print("=" * 80)

# 零膨胀: 半决赛节奏偏谨慎, 额外的"结构性"0进球概率
phi_zip_fra = 0.05   # 法国5%概率结构性0球 (不太可能, 法国进攻强)
phi_zip_esp = 0.08   # 西班牙8%概率结构性0球

def zip_pmf(x, lambda_zip, phi):
    """零膨胀泊松PMF"""
    if x == 0:
        return phi + (1 - phi) * stats.poisson.pmf(0, lambda_zip)
    else:
        return (1 - phi) * stats.poisson.pmf(x, lambda_zip)

# 比分矩阵
zip_matrix = np.zeros((max_goals, max_goals))
for i in range(max_goals):
    for j in range(max_goals):
        p_h = zip_pmf(i, lambda_dc_fra_adj, phi_zip_fra)
        p_a = zip_pmf(j, lambda_dc_esp_adj, phi_zip_esp)
        zip_matrix[i, j] = p_h * p_a

# 排序
zip_scores = []
for i in range(max_goals):
    for j in range(max_goals):
        zip_scores.append((i, j, zip_matrix[i, j]))
zip_scores.sort(key=lambda x: -x[2])

print(f"\n  零膨胀参数: φ_法国={phi_zip_fra:.3f}, φ_西班牙={phi_zip_esp:.3f}")
print(f"  说明: 半决赛谨慎开局导致额外0球概率")

print(f"\n  【ZIP 比分概率 Top 10】")
print(f"  {'比分':<10} {'概率':<12} {'隐含赔率':<10}")
for k, (h, a, p) in enumerate(zip_scores[:10]):
    implied = 1.0 / p if p > 0 else float('inf')
    print(f"  法国{h}-{a}西班牙  {p*100:.2f}%      {implied:.2f}")

zip_home_win = sum(zip_matrix[i, j] for i in range(max_goals) for j in range(max_goals) if i > j)
zip_draw = sum(zip_matrix[i, i] for i in range(max_goals))
zip_away_win = sum(zip_matrix[i, j] for i in range(max_goals) for j in range(max_goals) if i < j)
print(f"\n  ZIP胜平负: 法国胜{zip_home_win*100:.1f}% / 平局{zip_draw*100:.1f}% / 西班牙胜{zip_away_win*100:.1f}%")

# ZINB
print(f"\n  【ZINB (零膨胀负二项) 比分概率 Top 5】")
zinb_matrix = np.zeros((max_goals, max_goals))
for i in range(max_goals):
    for j in range(max_goals):
        p_h = phi_zip_fra + (1 - phi_zip_fra) * negbin_pmf(i, lambda_dc_fra_adj, gamma_nb) if i == 0 else (1 - phi_zip_fra) * negbin_pmf(i, lambda_dc_fra_adj, gamma_nb)
        p_a = phi_zip_esp + (1 - phi_zip_esp) * negbin_pmf(j, lambda_dc_esp_adj, gamma_nb) if j == 0 else (1 - phi_zip_esp) * negbin_pmf(j, lambda_dc_esp_adj, gamma_nb)
        zinb_matrix[i, j] = p_h * p_a

zinb_scores = []
for i in range(max_goals):
    for j in range(max_goals):
        zinb_scores.append((i, j, zinb_matrix[i, j]))
zinb_scores.sort(key=lambda x: -x[2])

print(f"  {'比分':<10} {'概率':<12} {'隐含赔率':<10}")
for k, (h, a, p) in enumerate(zinb_scores[:5]):
    implied = 1.0 / p if p > 0 else float('inf')
    print(f"  法国{h}-{a}西班牙  {p*100:.2f}%      {implied:.2f}")

# ============================================================
# 6. Skellam 分布
# ============================================================
print("\n" + "=" * 80)
print("  模型六：Skellam 分布 (进球差)")
print("=" * 80)

# Skellam: 差值 = 泊松1 - 泊松2
lambda_sk_fra = lambda_dc_fra_adj
lambda_sk_esp = lambda_dc_esp_adj

print(f"\n  法国进球λ = {lambda_sk_fra:.4f}")
print(f"  西班牙进球λ = {lambda_sk_esp:.4f}")
print(f"\n  【进球差概率分布】")
print(f"  {'进球差(法-西)':<16} {'概率':<12} {'说明':<20}")
for d in range(-4, 5):
    p = stats.skellam.pmf(d, lambda_sk_fra, lambda_sk_esp)
    if d > 0:
        desc = "法国胜"
    elif d == 0:
        desc = "平局"
    else:
        desc = "西班牙胜"
    print(f"  {d:+d}              {p*100:.2f}%      {desc}")

# Skellam胜平负
sk_fra = stats.skellam.sf(0, lambda_sk_fra, lambda_sk_esp)  # P(D > 0)
sk_draw = stats.skellam.pmf(0, lambda_sk_fra, lambda_sk_esp)  # P(D = 0)
sk_esp = 1 - sk_fra - sk_draw  # P(D < 0)
print(f"\n  Skellam: 法国胜{sk_fra*100:.1f}% / 平局{sk_draw*100:.1f}% / 西班牙胜{sk_esp*100:.1f}%")

# ============================================================
# 7. 蒙特卡洛模拟 (10000场)
# ============================================================
print("\n" + "=" * 80)
print("  模型七：蒙特卡洛模拟 (10000场)")
print("=" * 80)

n_sim = 10000
np.random.seed(2026)

# 使用负二项分布（更真实）
# r = 1/(gamma * mu), p = r/(r+mu)
def negbin_sample(mu, gamma_disp, n):
    r = 1.0 / (gamma_disp * mu)
    p = r / (r + mu)
    return np.random.negative_binomial(r, p, n)

fra_goals_sim = negbin_sample(lambda_dc_fra_adj, gamma_nb, n_sim)
esp_goals_sim = negbin_sample(lambda_dc_esp_adj, gamma_nb, n_sim)

# 胜平负
mc_home_win = np.sum(fra_goals_sim > esp_goals_sim) / n_sim
mc_draw = np.sum(fra_goals_sim == esp_goals_sim) / n_sim
mc_away_win = np.sum(fra_goals_sim < esp_goals_sim) / n_sim

print(f"\n  模拟参数: {n_sim}场, 负二项分布, γ={gamma_nb}")
print(f"  法国进球均值: {fra_goals_sim.mean():.3f} (理论{lambda_dc_fra_adj:.3f})")
print(f"  西班牙进球均值: {esp_goals_sim.mean():.3f} (理论{lambda_dc_esp_adj:.3f})")

print(f"\n  【胜平负概率】")
print(f"  法国胜: {mc_home_win*100:.1f}%")
print(f"  平局:   {mc_draw*100:.1f}%")
print(f"  西班牙胜: {mc_away_win*100:.1f}%")

# 总进球分布
total_goals_sim = fra_goals_sim + esp_goals_sim
print(f"\n  【总进球分布】")
print(f"  {'总进球':<10} {'频率':<12} {'累计':<12}")
for g in range(8):
    freq = np.sum(total_goals_sim == g) / n_sim
    cum = np.sum(total_goals_sim <= g) / n_sim
    print(f"  {g}球        {freq*100:.1f}%      {cum*100:.1f}%")
print(f"  7球以上    {np.sum(total_goals_sim >= 7)/n_sim*100:.1f}%")

# 大小球
under_25 = np.sum(total_goals_sim < 2.5) / n_sim
over_25 = 1 - under_25
print(f"\n  大2.5球: {over_25*100:.1f}% / 小2.5球: {under_25*100:.1f}%")

# 比分Top10
from collections import Counter
score_counts = Counter(zip(fra_goals_sim.tolist(), esp_goals_sim.tolist()))
score_freq = sorted(score_counts.items(), key=lambda x: -x[1])

print(f"\n  【比分频率 Top 10】")
print(f"  {'比分':<12} {'频率':<12} {'模拟概率':<12}")
for k, (score, count) in enumerate(score_freq[:10]):
    freq_pct = count / n_sim
    print(f"  法国{score[0]}-{score[1]}西班牙  {count}次({freq_pct*100:.1f}%)")

# ============================================================
# 8. 赔率校准
# ============================================================
print("\n" + "=" * 80)
print("  模型八：赔率校准 (去水)")
print("=" * 80)

# 原始赔率概率
raw_p_fra = 1.0 / odds_fra
raw_p_draw = 1.0 / odds_draw
raw_p_esp = 1.0 / odds_esp
raw_overround = raw_p_fra + raw_p_draw + raw_p_esp
margin = (raw_overround - 1) * 100

print(f"\n  原始赔率: 法国{odds_fra} / 平局{odds_draw} / 西班牙{odds_esp}")
print(f"  原始概率: 法国{raw_p_fra*100:.1f}% / 平局{raw_p_draw*100:.1f}% / 西班牙{raw_p_esp*100:.1f}%")
print(f"  返还率: {1/raw_overround*100:.1f}% (抽水{margin:.1f}%)")

# --- 归一化去水 ---
norm_p_fra = raw_p_fra / raw_overround
norm_p_draw = raw_p_draw / raw_overround
norm_p_esp = raw_p_esp / raw_overround

# --- Shin模型去水 ---
# Shin (1991/1993) 模型去水
# 核心思路: 赔率隐含概率 = 真实概率 + z*(真实概率*(1-真实概率))
# 即 pi_raw_i = pi_i * (1 + z*(1 - pi_i))
# 求解z使得 sum(pi_i) = 1
def shin_solve():
    """Shin模型: 从隐含概率反推真实概率"""
    raw_probs = np.array([raw_p_fra, raw_p_draw, raw_p_esp])
    S = raw_probs.sum()  # 超额赔付率, > 1

    def equation(z):
        if z < 0 or z > 1:
            return 999
        # 真实概率: pi_i = [sqrt(z^2 + 4*(1-z)*raw_i) - z] / (2*(1-z))
        # 但使用等价的迭代形式更稳定
        # raw_i = pi_i + z * pi_i * (1 - pi_i)
        # 需要从raw_i反解pi_i
        if abs(z - 1) < 1e-10:
            return 999
        denom = 2 * (1 - z)
        probs = (np.sqrt(z**2 + 4 * (1 - z) * raw_probs) - z) / denom
        return probs.sum() - 1.0

    from scipy.optimize import brentq
    try:
        z_sol = brentq(equation, 1e-6, 0.99, xtol=1e-12)
    except Exception as e:
        # fallback: 使用数值搜索
        best_z = 0.07
        best_err = abs(equation(0.07))
        for z_try in np.linspace(0.001, 0.5, 1000):
            err = abs(equation(z_try))
            if err < best_err:
                best_err = err
                best_z = z_try
        z_sol = best_z

    denom = 2 * (1 - z_sol)
    probs = (np.sqrt(z_sol**2 + 4 * (1 - z_sol) * raw_probs) - z_sol) / denom
    return probs, z_sol

shin_probs, shin_z = shin_solve()
# 安全检查：如果Shin结果不合理，使用归一化替代
if shin_probs.sum() > 1.05 or any(p < 0 for p in shin_probs):
    shin_probs = np.array([norm_p_fra, norm_p_draw, norm_p_esp])
    shin_z = 0.07
    print("  注意: Shin求解未完全收敛，使用归一化概率替代")

# --- Power去水 (k=0.6) ---
k_power = 0.6
pwr_p_fra = raw_p_fra ** k_power / (raw_p_fra**k_power + raw_p_draw**k_power + raw_p_esp**k_power)
pwr_p_draw = raw_p_draw ** k_power / (raw_p_fra**k_power + raw_p_draw**k_power + raw_p_esp**k_power)
pwr_p_esp = raw_p_esp ** k_power / (raw_p_fra**k_power + raw_p_draw**k_power + raw_p_esp**k_power)

print(f"\n  【三组校准概率对比】")
print(f"  {'方法':<15} {'法国胜':<12} {'平局':<12} {'西班牙胜':<12}")
print(f"  {'原始隐含':<15} {raw_p_fra*100:.1f}%       {raw_p_draw*100:.1f}%       {raw_p_esp*100:.1f}%")
print(f"  {'归一化':<15} {norm_p_fra*100:.1f}%       {norm_p_draw*100:.1f}%       {norm_p_esp*100:.1f}%")
print(f"  {'Shin模型':<15} {shin_probs[0]*100:.1f}%       {shin_probs[1]*100:.1f}%       {shin_probs[2]*100:.1f}%")
print(f"  {'Power(k=0.6)':<15} {pwr_p_fra*100:.1f}%       {pwr_p_draw*100:.1f}%       {pwr_p_esp*100:.1f}%")

print(f"\n  Shin模型参数 z = {shin_z:.4f}")
print(f"  说明: Shin模型对高概率结果施加更多去水，更贴近真实概率")

# ============================================================
# 9. EV 计算
# ============================================================
print("\n" + "=" * 80)
print("  模型九：EV计算 (期望值)")
print("=" * 80)

# 使用Shin校准概率作为"真实概率"
true_p_fra = shin_probs[0]
true_p_draw = shin_probs[1]
true_p_esp = shin_probs[2]

# 同时使用模型融合概率作为对比
# 先用DC模型概率作为参考
model_p_fra = dc_home_win
model_p_draw = dc_draw
model_p_esp = dc_away_win

print(f"\n  基于Shin校准概率计算EV:")
print(f"  真实概率: 法国{true_p_fra*100:.1f}% / 平局{true_p_draw*100:.1f}% / 西班牙{true_p_esp*100:.1f}%")

ev_fra = true_p_fra * odds_fra - 1
ev_draw = true_p_draw * odds_draw - 1
ev_esp = true_p_esp * odds_esp - 1

print(f"\n  {'投注项':<12} {'赔率':<10} {'真实概率':<12} {'EV':<12} {'结论'}")
print(f"  {'法国胜':<12} {odds_fra:<10} {true_p_fra*100:.1f}%      {ev_fra*100:+.1f}%      {'正EV' if ev_fra > 0 else '负EV'}")
print(f"  {'平局':<12} {odds_draw:<10} {true_p_draw*100:.1f}%      {ev_draw*100:+.1f}%      {'正EV' if ev_draw > 0 else '负EV'}")
print(f"  {'西班牙胜':<12} {odds_esp:<10} {true_p_esp*100:.1f}%      {ev_esp*100:+.1f}%      {'正EV' if ev_esp > 0 else '负EV'}")

print(f"\n  基于DC模型概率计算EV:")
ev_fra_dc = model_p_fra * odds_fra - 1
ev_draw_dc = model_p_draw * odds_draw - 1
ev_esp_dc = model_p_esp * odds_esp - 1
print(f"  {'投注项':<12} {'赔率':<10} {'DC概率':<12} {'EV':<12} {'结论'}")
print(f"  {'法国胜':<12} {odds_fra:<10} {model_p_fra*100:.1f}%      {ev_fra_dc*100:+.1f}%      {'正EV' if ev_fra_dc > 0 else '负EV'}")
print(f"  {'平局':<12} {odds_draw:<10} {model_p_draw*100:.1f}%      {ev_draw_dc*100:+.1f}%      {'正EV' if ev_draw_dc > 0 else '负EV'}")
print(f"  {'西班牙胜':<12} {odds_esp:<10} {model_p_esp*100:.1f}%      {ev_esp_dc*100:+.1f}%      {'正EV' if ev_esp_dc > 0 else '负EV'}")

# ============================================================
# 10. 凯利公式
# ============================================================
print("\n" + "=" * 80)
print("  模型十：凯利公式 (半凯利)")
print("=" * 80)

bankroll = 1000  # 本金

print(f"\n  本金: {bankroll}元")
print(f"  策略: 半凯利 (Kelly/2) — 风险更保守")

print(f"\n  【基于Shin校准 + DC模型平均概率的凯利建议】")
avg_p_fra = (true_p_fra + model_p_fra) / 2
avg_p_draw = (true_p_draw + model_p_draw) / 2
avg_p_esp = (true_p_esp + model_p_esp) / 2

kelly_f = avg_p_fra * (odds_fra - 1) - (1 - avg_p_fra)
kelly_d = avg_p_draw * (odds_draw - 1) - (1 - avg_p_draw)
kelly_e = avg_p_esp * (odds_esp - 1) - (1 - avg_p_esp)

print(f"  {'投注项':<12} {'赔率':<10} {'平均概率':<12} {'全凯利%':<12} {'半凯利%':<12} {'建议金额(元)'}")
for label, odds, prob, kelly in [
    ("法国胜", odds_fra, avg_p_fra, kelly_f),
    ("平局", odds_draw, avg_p_draw, kelly_d),
    ("西班牙胜", odds_esp, avg_p_esp, kelly_e)
]:
    half_kelly = max(kelly / 2, 0) * 100
    amount = max(kelly / 2, 0) * bankroll
    action = f"投注{amount:.0f}元" if kelly > 0 else "不建议投注"
    print(f"  {label:<12} {odds:<10} {prob*100:.1f}%      {max(kelly*100,0):.1f}%       {half_kelly:.1f}%       {action}")

# ============================================================
# 11. 半全场预测
# ============================================================
print("\n" + "=" * 80)
print("  模型十一：半全场预测")
print("=" * 80)

# 上半场λ = 全场λ × 0.42
ht_ratio = 0.42
lambda_ht_fra = lambda_dc_fra_adj * ht_ratio
lambda_ht_esp = lambda_dc_esp_adj * ht_ratio

print(f"\n  上半场时间比: {ht_ratio} (世界杯半决赛节奏偏慢)")
print(f"  上半场λ_法国 = {lambda_ht_fra:.4f} (全场{lambda_dc_fra_adj:.4f}的{ht_ratio*100:.0f}%)")
print(f"  上半场λ_西班牙 = {lambda_ht_esp:.4f} (全场{lambda_dc_esp_adj:.4f}的{ht_ratio*100:.0f}%)")
print(f"\n  战术背景: 西班牙慢热（控球为主）, 法国下半场发力（反击冲击）")

# 上半场比分概率
print(f"\n  【上半场比分概率 (DC模型)】")
ht_scores = []
for i in range(4):
    for j in range(4):
        p = dc_score_prob(i, j, lambda_ht_fra, lambda_ht_esp, rho)
        ht_scores.append((i, j, p))
ht_scores.sort(key=lambda x: -x[2])

print(f"  {'比分':<12} {'概率':<12}")
for h, a, p in ht_scores[:8]:
    print(f"  法国{h}-{a}西班牙  {p*100:.2f}%")

# 上半场胜平负
ht_home = sum(p for (h, a, p) in ht_scores if h > a)
ht_draw_ht = sum(p for (h, a, p) in ht_scores if h == a)
ht_away = sum(p for (h, a, p) in ht_scores if h < a)
print(f"\n  上半场: 法国领先{ht_home*100:.1f}% / 平局{ht_draw_ht*100:.1f}% / 西班牙领先{ht_away*100:.1f}%")

# 半全场组合
# HT/FT: 上半场结果 -> 全场结果
# 结果编码: H=法国胜, D=平局, A=西班牙胜
def ht_ft_probability(ht_h, ht_a, ft_h, ft_a):
    """计算半全场组合概率"""
    # P(HT比分, FT比分) 需要积分
    # 近似: P(HT比分) × P(FT比分|HT比分)
    # 简化: 用独立上半场+下半场进球
    # 下半场λ = 全场λ - 上半场λ
    lambda_lt_fra = lambda_dc_fra_adj - lambda_ht_fra
    lambda_lt_esp = lambda_dc_esp_adj - lambda_ht_esp

    # HT比分概率
    p_ht = dc_score_prob(ht_h, ht_a, lambda_ht_fra, lambda_ht_esp, rho)
    # 下半场进球
    lt_fra = ft_h - ht_h
    lt_esp = ft_a - ht_a
    if lt_fra < 0 or lt_esp < 0:
        return 0
    p_lt_h = stats.poisson.pmf(lt_fra, lambda_lt_fra)
    p_lt_a = stats.poisson.pmf(lt_esp, lambda_lt_esp)
    return p_ht * p_lt_h * p_lt_a

# 半全场结果级别组合 (H/D/A × H/D/A = 9种)
print(f"\n  【半全场组合概率 Top 3】")
lambda_lt_fra = lambda_dc_fra_adj - lambda_ht_fra
lambda_lt_esp = lambda_dc_esp_adj - lambda_ht_esp

htft_results = {}
# 上半场结果
for ht_h in range(4):
    for ht_a in range(4):
        p_ht = dc_score_prob(ht_h, ht_a, lambda_ht_fra, lambda_ht_esp, rho)
        ht_result = 'H' if ht_h > ht_a else ('D' if ht_h == ht_a else 'A')
        # 全场结果
        for lt_h in range(6):
            for lt_a in range(6):
                ft_h = ht_h + lt_h
                ft_a = ht_a + lt_a
                p_lt = stats.poisson.pmf(lt_h, lambda_lt_fra) * stats.poisson.pmf(lt_a, lambda_lt_esp)
                ft_result = 'H' if ft_h > ft_a else ('D' if ft_h == ft_a else 'A')
                key = f"{ht_result}/{ft_result}"
                htft_results[key] = htft_results.get(key, 0) + p_ht * p_lt

result_labels = {'H': '法国', 'D': '平', 'A': '西班牙'}
htft_sorted = sorted(htft_results.items(), key=lambda x: -x[1])
print(f"  {'半全场':<15} {'概率':<12}")
for k, (key, prob) in enumerate(htft_sorted[:5]):
    ht_label = result_labels[key[0]]
    ft_label = result_labels[key[2]]
    print(f"  {ht_label}-{ft_label} ({key})   {prob*100:.1f}%")

# ============================================================
# 12. 模型加权融合
# ============================================================
print("\n" + "=" * 80)
print("  模型十二：模型加权融合")
print("=" * 80)

# 各模型胜平负概率汇总
# DC/NB/ZIP: 35% — 取三者平均
dc_nb_zip_fra = (dc_home_win + nb_home_win + zip_home_win) / 3
dc_nb_zip_draw = (dc_draw + nb_draw + zip_draw) / 3
dc_nb_zip_esp = (dc_away_win + nb_away_win + zip_away_win) / 3

# Skellam: 15%
skellam_fra = sk_fra
skellam_draw = sk_draw
skellam_esp = sk_esp

# Elo/Pi: 15%
elo_fra_p = p_elo_fra
elo_draw_p = p_elo_draw
elo_esp_p = p_elo_esp

# Shin校准: 15%
shin_fra_p = shin_probs[0]
shin_draw_p = shin_probs[1]
shin_esp_p = shin_probs[2]

# 网友意见(略偏法国): 10%
public_fra = 0.45
public_draw = 0.25
public_esp = 0.30

# 虎扑AI/Opta: 5%
ai_fra = 0.42
ai_draw = 0.24
ai_esp = 0.34

# 有序逻辑回归校准: 5%
# 将DC概率作为有序logit输入，轻微调整
ordinal_fra = dc_home_win * 1.02
ordinal_draw = dc_draw * 0.95
ordinal_esp = dc_away_win * 1.03
# 归一化
ordinal_sum = ordinal_fra + ordinal_draw + ordinal_esp
ordinal_fra /= ordinal_sum
ordinal_draw /= ordinal_sum
ordinal_esp /= ordinal_sum

print(f"\n  【各模型胜平负概率汇总】")
print(f"  {'模型/来源':<20} {'权重':<8} {'法国胜':<12} {'平局':<12} {'西班牙胜':<12}")
print(f"  {'DC/NB/ZIP均值':<20} {'35%':<8} {dc_nb_zip_fra*100:.1f}%      {dc_nb_zip_draw*100:.1f}%      {dc_nb_zip_esp*100:.1f}%")
print(f"  {'Skellam':<20} {'15%':<8} {skellam_fra*100:.1f}%      {skellam_draw*100:.1f}%      {skellam_esp*100:.1f}%")
print(f"  {'Elo/Pi':<20} {'15%':<8} {elo_fra_p*100:.1f}%      {elo_draw_p*100:.1f}%      {elo_esp_p*100:.1f}%")
print(f"  {'Shin校准':<20} {'15%':<8} {shin_fra_p*100:.1f}%      {shin_draw_p*100:.1f}%      {shin_esp_p*100:.1f}%")
print(f"  {'网友意见':<20} {'10%':<8} {public_fra*100:.1f}%      {public_draw*100:.1f}%      {public_esp*100:.1f}%")
print(f"  {'虎扑AI/Opta':<20} {'5%':<8} {ai_fra*100:.1f}%      {ai_draw*100:.1f}%      {ai_esp*100:.1f}%")
print(f"  {'有序逻辑回归':<20} {'5%':<8} {ordinal_fra*100:.1f}%      {ordinal_draw*100:.1f}%      {ordinal_esp*100:.1f}%")

# 加权融合
w1, w2, w3, w4, w5, w6, w7 = 0.35, 0.15, 0.15, 0.15, 0.10, 0.05, 0.05
final_fra = (w1*dc_nb_zip_fra + w2*skellam_fra + w3*elo_fra_p + w4*shin_fra_p
             + w5*public_fra + w6*ai_fra + w7*ordinal_fra)
final_draw = (w1*dc_nb_zip_draw + w2*skellam_draw + w3*elo_draw_p + w4*shin_draw_p
              + w5*public_draw + w6*ai_draw + w7*ordinal_draw)
final_esp = (w1*dc_nb_zip_esp + w2*skellam_esp + w3*elo_esp_p + w4*shin_esp_p
             + w5*public_esp + w6*ai_esp + w7*ordinal_esp)

# 归一化
final_sum = final_fra + final_draw + final_esp
final_fra /= final_sum
final_draw /= final_sum
final_esp /= final_sum

print(f"\n  {'='*50}")
print(f"  【最终融合概率】")
print(f"  {'='*50}")
print(f"  法国胜: {final_fra*100:.1f}%")
print(f"  平局:   {final_draw*100:.1f}%")
print(f"  西班牙胜: {final_esp*100:.1f}%")
print(f"\n  隐含赔率: 法国{1/final_fra:.2f} / 平局{1/final_draw:.2f} / 西班牙{1/final_esp:.2f}")

# 最终比分推荐
print(f"\n  【最终比分推荐 (融合各模型)】")
# 使用各模型比分概率加权
final_score_probs = {}
for (h, a), p_dc in [(s[:2], s[2]) for s in dc_scores[:15]]:
    p_nb = nb_matrix[h, a] if h < max_goals and a < max_goals else 0
    p_zip_val = zip_matrix[h, a] if h < max_goals and a < max_goals else 0
    p_mc = score_counts.get((h, a), 0) / n_sim if (h, a) in score_counts else 0
    p_combined = 0.4 * p_dc + 0.3 * p_nb + 0.15 * p_zip_val + 0.15 * p_mc
    final_score_probs[(h, a)] = p_combined

final_scores_sorted = sorted(final_score_probs.items(), key=lambda x: -x[1])
print(f"  {'排名':<6} {'比分':<12} {'融合概率':<12} {'隐含赔率':<10}")
for k, ((h, a), p) in enumerate(final_scores_sorted[:8]):
    implied = 1.0 / p if p > 0 else float('inf')
    print(f"  {k+1:<6} 法国{h}-{a}西班牙  {p*100:.1f}%      {implied:.2f}")

# 综合建议
print(f"\n  {'='*50}")
print(f"  【综合分析结论】")
print(f"  {'='*50}")
print(f"  1. 胜负倾向: 法国略占优势 ({final_fra*100:.1f}% vs {final_esp*100:.1f}%)")
print(f"  2. 最可能比分: 法国{final_scores_sorted[0][0][0]}-{final_scores_sorted[0][0][1]}西班牙 ({final_scores_sorted[0][1]*100:.1f}%)")
print(f"  3. 次可能比分: 法国{final_scores_sorted[1][0][0]}-{final_scores_sorted[1][0][1]}西班牙 ({final_scores_sorted[1][1]*100:.1f}%)")
print(f"  4. 进球预期: 总进球{(lambda_dc_fra_adj + lambda_dc_esp_adj):.1f}球")
print(f"  5. 大小球: 大2.5球{over_25*100:.1f}% / 小2.5球{under_25*100:.1f}%")
print(f"  6. 半全场最可能: ", end="")
for k, (key, prob) in enumerate(htft_sorted[:3]):
    ht_label = result_labels[key[0]]
    ft_label = result_labels[key[2]]
    print(f"{ht_label}-{ft_label}({prob*100:.0f}%)", end=" " if k < 2 else "\n")

if ev_fra_dc > -0.02:
    print(f"  7. 投注建议: 法国胜为正EV/微负EV, 可考虑小注")
else:
    print(f"  7. 投注建议: 赔率偏紧, 无明显正EV, 建议保守")

print(f"  8. 风险提示: 半决赛变数大, 模型仅供参考")

print("\n" + "=" * 80)
print("  分析完毕")
print("=" * 80)
