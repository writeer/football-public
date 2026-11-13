# -*- coding: utf-8 -*-
"""追加 2026-10-18 比分串试用台账登记（规则67双轨制·赛前登记，赛果待回填）"""
import json, io

R = {r['num']: r for r in json.load(io.open('reports/data/20261018_model_output.json', encoding='utf-8'))}
DIR = {'home': '主胜', 'draw': '平', 'away': '客胜'}
NUM = ['周日018', '周日003', '周日010', '周日011', '周日016', '周日017', '周日024', '周一001']
USE = {
    '周日018': '稳健比分串 0-1', '周日003': '稳健比分串 2-1',
    '周日010': '连续编号比分串① 1-1', '周日011': '连续编号比分串① 2-1',
    '周日016': '连续编号比分串② 1-2', '周日017': '连续编号比分串② 0-1',
    '周日024': '单挑比分① 3-1', '周一001': '单挑比分② 2-1',
}
L = []
L.append('')
L.append('## 2026-10-18（周日）登记（赛前登记，赛果待 10-19 回填）')
L.append('')
L.append('| 编号 | 对阵 | 联赛 | 分布众数 k_dist | 推荐众数 k_rec | 带内候选TOP3 | 首推总进球档 | k_dist方向 | HAD首推方向 | 是否分歧 | 用途 | 实际比分 | 判定 |')
L.append('|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---:|:---|:---:|:---|')
for n in NUM:
    r = R[n]
    band = ' > '.join('%d-%d(%.1f%%)' % (a, b, p * 100) for a, b, p in r['band'][:3])
    kd = r['k_dist']
    kr = r['k_rec']
    kd_dir = '主胜' if kd >= 1 else ('平' if kd == 0 else '客胜')
    L.append('| %s | %s vs %s（%s） | %s | %+d（%.1f%%） | %+d（%.1f%%） | %s | %d球/%d球 | %s | %s | %s | %s | 待回填 | 待判 |' % (
        n.replace('周日', '').replace('周一', '周一'),
        r['home'], r['away'], r['league'],
        r['league'], kd, r['k_dist_prob'] * 100, kr, r['k_rec_prob'] * 100,
        band, r['ttg_top2'][0], r['ttg_top2'][1], kd_dir, DIR[r['primary']],
        '一致' if r['k_consistent'] else '**分歧**', USE[n]))
L.append('')
L.append('> 本轮比分串共使用 8 场（去重）：018/003（稳健比分串）、010/011（连续编号①）、016/017（连续编号②）、024/周一001（单挑①②）。其中**众数一致场 3 场**（018、003、024），其余 5 场为分歧场（仅记录、不计入精确命中率口径）。')
L.append('> **转正条件**：累计≥20场且比分精确命中率≥60%。当前仍处试用期，本轮 8 场赛果待 10-19 回测后回填。')
L.append('')

io.open('memory/trials/score_parlay_trial.md', 'a', encoding='utf-8').write('\n'.join(L))
print('ledger appended', len(L))
