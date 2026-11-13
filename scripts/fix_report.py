#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix HAD row, half-time score row, and confidence paragraph for all 27 matches."""

import re
import math

file_path = r"e:\VibeCoding\football\reports\html\20260816_sunday_analysis_zhihu.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

lines = content.split("\n")

# Step 1: Build confidence map from 总览 table
conf_map = {}
for line in lines:
    m = re.match(r'^\| (\d{3}) \| .+ \| .+ \| .+ \| (★+) \|', line)
    if m:
        conf_map[m.group(1)] = m.group(2)

print(f"Confidence map entries: {len(conf_map)}")
for k in sorted(conf_map.keys()):
    print(f"  {k} -> {conf_map[k]}")

# Poisson PMF
def poisson_pmf(k, lam):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

# Generate top 3 half-time scores
def get_ht_scores(lh, la):
    ht_h = lh * 0.45
    ht_a = la * 0.45
    scores = []
    for h in range(4):
        for a in range(4):
            p = poisson_pmf(h, ht_h) * poisson_pmf(a, ht_a)
            scores.append((f"{h}-{a}", p))
    scores.sort(key=lambda x: x[1], reverse=True)
    top3 = scores[:3]
    return " > ".join(f"{s}({round(p*100)}%)" for s, p in top3)

# Direction name mapping
dir_names = {
    'home': '主胜',
    'draw': '平局',
    'away': '客胜'
}

# Process lines
output = []
current_match = None
model_home = model_draw = model_away = 0
lambda_h = lambda_a = 0.0
in_rec_table = False
fixed_had = 0
fixed_ht = 0
fixed_conf = 0
skipped_dup_conf = 0

i = 0
while i < len(lines):
    line = lines[i]

    # Detect match section start
    m = re.match(r'^## (\d{3}) ', line)
    if m:
        current_match = m.group(1)
        model_home = model_draw = model_away = 0
        lambda_h = lambda_a = 0.0
        in_rec_table = False

    # Extract model probabilities
    m = re.search(r'融合概率.*?主胜\s*(\d+)%.*?平\s*(\d+)%.*?客\s*(\d+)%', line)
    if m:
        model_home = int(m.group(1))
        model_draw = int(m.group(2))
        model_away = int(m.group(3))

    # Extract lambda values
    m = re.search(r'λ：主\s*([\d.]+).*?客\s*([\d.]+)', line)
    if m:
        lambda_h = float(m.group(1))
        lambda_a = float(m.group(2))

    # Track recommendation table
    if '**推荐：**' in line:
        in_rec_table = True
    if line.startswith('---'):
        in_rec_table = False

    # Skip misplaced 置信度 before the rule trigger note or model line
    # (the one that appears between 伤停 and the > blockquote)
    if re.match(r'^\*\*置信度：\*\*\s+—', line) and not in_rec_table:
        # Check if next non-empty line is > blockquote or **模型
        next_i = i + 1
        while next_i < len(lines) and lines[next_i].strip() == '':
            next_i += 1
        if next_i < len(lines) and (lines[next_i].startswith('>') or lines[next_i].startswith('**模型')):
            skipped_dup_conf += 1
            print(f"  Skip dup 置信度 at line {i+1} for {current_match}")
            i += 1
            continue

    # Fix HAD row: placeholder "| **HAD** | 首选 (%) / 次选 (%) |"
    if '| **HAD** | 首选 (%) / 次选 (%) |' in line:
        if model_home > 0 or model_draw > 0 or model_away > 0:
            probs = [
                ('home', model_home),
                ('draw', model_draw),
                ('away', model_away)
            ]
            probs.sort(key=lambda x: x[1], reverse=True)
            first_dir = dir_names[probs[0][0]]
            first_prob = probs[0][1]
            second_dir = dir_names[probs[1][0]]
            second_prob = probs[1][1]
            line = f"| **HAD** | 首选 {first_dir}({first_prob}%) / 次选 {second_dir}({second_prob}%) |"
            fixed_had += 1
            print(f"  Fixed HAD for {current_match}: {first_dir}({first_prob}%) / {second_dir}({second_prob}%)")

    # Fix 半场比分 row with placeholder values
    if '| **半场比分** |' in line and ('100%' in line or '(0%)' in line):
        if lambda_h > 0 and lambda_a > 0:
            ht_scores = get_ht_scores(lambda_h, lambda_a)
            line = f"| **半场比分** | {ht_scores} |"
            fixed_ht += 1
            print(f"  Fixed 半场比分 for {current_match}: {ht_scores}")

    # Fix 置信度 paragraph after recommendation table (missing star level)
    if re.match(r'^\*\*置信度：\*\*\s+—', line) and in_rec_table:
        if current_match and current_match in conf_map:
            conf = conf_map[current_match]
            reason = re.sub(r'^\*\*置信度：\*\*\s+—\s*', '', line)
            line = f"**置信度：** {conf} — {reason}"
            fixed_conf += 1
            print(f"  Fixed 置信度 for {current_match}: {conf}")

    output.append(line)
    i += 1

# Write output
with open(file_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print(f"\nDone! Total lines: {len(output)}")
print(f"Fixed: HAD={fixed_had}, 半场比分={fixed_ht}, 置信度={fixed_conf}, Skipped dup 置信度={skipped_dup_conf}")
