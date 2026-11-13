# -*- coding: utf-8 -*-
"""2026-10-18 报告审核（第8步）：A-G 结构 + G13-G24 格式 + 规则硬校验"""
import io, re, json

P = 'reports/analysis/20261018_sunday_analysis_zhihu.md'
t = io.open(P, encoding='utf-8').read()
R = json.load(io.open('reports/data/20261018_model_output.json', encoding='utf-8'))
issues = []

# 1 场次数
secs = re.findall(r'^## (周日\d{3}|周一\d{3}) ', t, re.M)
print('逐场章节数：', len(secs), '去重：', len(set(secs)))
if len(set(secs)) != 33:
    issues.append('逐场章节不足33场')

# 2 场地天气行
venue = len(re.findall(r'^⏰ ', t, re.M))
print('场地天气行：', venue)
if venue != 33:
    issues.append('场地天气行 %d/33' % venue)

# 3 净胜球众数行
k = len(re.findall(r'净胜球众数：', t))
print('净胜球众数行：', k)
if k != 33:
    issues.append('净胜球众数行 %d/33' % k)

# 4 身价/伤停段落
print('身价对比段：', t.count('**身价对比：**'), '伤停段：', t.count('**伤停：**'))
if t.count('**身价对比：**') != 33 or t.count('**伤停：**') != 33:
    issues.append('身价/伤停段落不是33段')

# 5 让平硬校验（L216）：让平≥20% 必须在前二
for r in R:
    if r['hhad_draw_prob'] is not None and r['hhad_draw_prob'] >= 0.20:
        if 'draw' not in (r['hc_first'], r['hc_second']):
            issues.append('%s 让平%.1f%%未进前二' % (r['num'], r['hhad_draw_prob'] * 100))
print('让平≥20%场次：', sum(1 for r in R if (r['hhad_draw_prob'] or 0) >= 0.20))

# 6 娱乐串方案数
ent = t.split('### 娱乐串')[1].split('## 本轮规律')[0]
plans = len(re.findall(r'^\| (?!方案|:)[^|]*(串|单挑)[^|]*\|', ent, re.M))
print('娱乐串方案行（含表头过滤后）：', plans)

# 7 法甲排除标注
print('法甲排除标注：', '已按规则71排除法甲' in t)
if '已按规则71排除法甲' not in t:
    issues.append('缺法甲排除标注')

# 8 单关三场
for n in ['周日001', '周日010', '周日021']:
    if '单关平局上修' not in t.split('## ' + n)[1][:2000]:
        issues.append('%s 未标注单关平局上修' % n)

# 9 禁词/规则编号（G15）
bad = re.findall(r'规则(?!32|71|76)\d+', t)
print('非允许规则编号出现：', sorted(set(bad)))

# 10 综合汇总行数
syn = t.split('## 综合推荐汇总')[1].split('## 搏冷推荐汇总')[0]
rows = [l for l in syn.split('\n') if l.startswith('| 周')]
print('综合汇总行：', len(rows))

# 11 比分串试用台账字段
print('试用期标注：', '试用期' in t)

# 12 空场/部分关闭披露
print('部分关闭披露：', t.count('部分关闭'), ' 空场：', t.count('空场'))

print('\n问题：', issues if issues else '无')
