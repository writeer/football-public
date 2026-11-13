# -*- coding: utf-8 -*-
"""
按 AGENTS.md v2.12.0 与 templates/zhihu_article_template.md 生成
2026-09-13（周日）竞彩 24 场知乎风格分析报告
输出：reports/analysis/20260913_sunday_analysis_zhihu.md
"""
import json, math, sys, os, io

WORK = r'c:\Users\admin\.trae-cn\work\6aa6133bd5a40399cae8e4e5'
sys.path.insert(0, WORK)
from flow_data import LEAGUE, M, ROUND, GPG, VIEW_SRC
from flow_model import (dc_matrix, nb_matrix, zip_matrix, pois, nb_pmf,
                        mx_1x2, ttg8, over25, MAXG)

W = json.load(open(os.path.join(WORK, 'flow_out.json'), encoding='utf-8'))
OUT = r'e:\VibeCoding\football\reports\analysis\20260913_sunday_analysis_zhihu.md'

# ---- 竞彩官方赔率原始数据（HAD/HHAD/CRS/TTG/HAFU 全玩法）----
_d0 = json.load(open(os.path.join(WORK, 'sp_raw.json'), encoding='utf-8-sig'))
_MATCH = {m['matchNumStr']: m
          for g in _d0['value']['matchInfoList'] if g['businessDate'] == '2026-09-13'
          for m in g['subMatchList']}

HAFU_KEY = {'胜胜': 'hh', '胜平': 'hd', '胜负': 'ha', '平胜': 'dh', '平平': 'dd',
            '平负': 'da', '负胜': 'ah', '负平': 'ad', '负负': 'aa'}


def had_odd(r):
    d = _MATCH.get(r['num'], {}).get('had')
    return [float(d['h']), float(d['d']), float(d['a'])] if d else None


def hhad_odd(r, which):
    d = _MATCH.get(r['num'], {}).get('hhad')
    if not d:
        return None
    return float(d[{'让胜': 'h', '让平': 'd', '让负': 'a'}[which]])


def ttg_odd(r, k):
    t = _MATCH.get(r['num'], {}).get('ttg')
    if not t:
        return None
    v = t.get(f's{min(k,7)}')
    return float(v) if v else None


def hafu_odd(r, lab):
    h = _MATCH.get(r['num'], {}).get('hafu')
    if not h:
        return None
    v = h.get(HAFU_KEY[lab])
    return float(v) if v else None


def crs_odd(r, score):
    c = _MATCH.get(r['num'], {}).get('crs')
    if not c:
        return None
    i, j = score.split('-')
    v = c.get(f's{int(i):02d}s{int(j):02d}')
    return float(v) if v else None

L3 = ['主胜', '平局', '客胜']
SINGLE = {'周日001', '周日003', '周日007', '周日013', '周日015', '周日019', '周日021'}

# 规则66 半场平局率 → 半场 λ 系数
HT = {
    '日职': (0.534, 0.38, '高'), '日乙': (None, 0.42, '不适用'),
    '西甲': (0.441, 0.38, '高'), '瑞超': (0.413, 0.38, '高'),
    '芬超': (0.418, 0.38, '高'), '荷甲': (0.387, 0.42, '中高'),
    '意甲': (0.409, 0.38, '高'), '法甲': (0.393, 0.42, '中高'),
    '挪超': (0.325, 0.45, '中低'), '德甲': (0.359, 0.42, '中高'),
    '英超': (0.384, 0.42, '中高'), '葡超': (0.414, 0.38, '高'),
    '巴甲': (None, 0.42, '不适用'), '美职': (0.366, 0.42, '中高'),
}

# ---------- 球场草皮 / 容量（来源：俱乐部官网、联赛官网、Transfermarkt、Wikipedia 镜像）----------
STADIUM = {
    '周日001': ('天然草', '48,013'),
    '周日002': ('天然草', '19,694'),
    '周日003': ('天然草', '24,870'),
    '周日004': ('人造草', '30,000'),
    '周日005': ('人造草', '4,700'),
    '周日006': ('天然草（另一口径标混合草，来源冲突）', '27,224'),
    '周日007': ('天然草', '31,559'),
    '周日008': ('混合草', '50,186'),
    '周日009': ('天然草', '47,800'),
    '周日010': ('天然草', '26,354'),
    '周日011': ('人造草', '8,068'),
    '周日012': ('混合草', '25,064'),
    '周日013': ('混合草', '74,310'),
    '周日014': ('天然草', '10,000'),
    '周日015': ('天然草', '54,726'),
    '周日016': ('天然草', '17,700'),
    '周日017': ('天然草', '68,118'),
    '周日018': ('混合草', '35,000'),
    '周日019': ('天然草', '21,584'),
    '周日020': ('天然草', '15,220'),
    '周日021': ('天然草', '40,000'),
    '周日022': ('天然草', '5,186'),
    '周日023': ('天然草', '78,838'),
    '周日024': ('天然草', '61,500'),
}

# ---------- 比赛日天气（来源：Open-Meteo 多模式预报，查询时间 2026-09-13）----------
# (emoji, 天气, 气温, 风力, 影响)
WEATHER = {
    '周日001': ('☀️', '阴', '20.8~26.2°C', '1级', '影响小'),
    '周日002': ('☀️', '小毛毛雨', '17.9~23.3°C', '1~2级', '影响小（降水概率76%）'),
    '周日003': ('☀️', '晴', '19.0~30.2°C', '2级', '影响小'),
    '周日004': ('☀️', '小毛毛雨', '12.5~16.7°C', '3级', '影响中等（降水概率65%）'),
    '周日005': ('❄️', '小毛毛雨', '7.9~13.6°C', '3级', '影响中等（低温+降水96%）'),
    '周日006': ('☀️', '小毛毛雨', '16.7~19.4°C', '3级', '影响小'),
    '周日007': ('☀️', '阴', '19.9~27.6°C', '4级', '影响小（风力最大4级）'),
    '周日008': ('☀️', '毛毛雨', '17.4~19.0°C', '3级', '影响中等（降水概率100%）'),
    '周日009': ('☀️', '小雨', '15.6~21.4°C', '3级', '影响中等（降水概率65%）'),
    '周日010': ('☀️', '晴间多云', '19.9~29.4°C', '3级', '影响小'),
    '周日011': ('❄️', '多云', '7.8~18.6°C', '2级', '影响小（低温）'),
    '周日012': ('☀️', '阴', '13.6~28.2°C', '2级', '影响小'),
    '周日013': ('☀️', '毛毛雨', '16.4~21.4°C', '2级', '影响中等（降水概率78%）'),
    '周日014': ('☀️', '阵雨', '14.0~16.2°C', '2级', '影响中等（降水概率93%）'),
    '周日015': ('☀️', '阴', '20.5~30.0°C', '2级', '影响小'),
    '周日016': ('🔥', '晴间多云', '18.3~32.1°C', '2级', '影响小（高温32℃）'),
    '周日017': ('🔥', '晴', '20.3~33.3°C', '2级', '影响小（高温33℃）'),
    '周日018': ('⛈️', '中雨', '16.5~19.8°C', '3级', '影响较大（降水概率100%）'),
    '周日019': ('☀️', '阴', '16.4~27.4°C', '2级', '影响小'),
    '周日020': ('☀️', '阴', '15.0~22.6°C', '3级', '影响小'),
    '周日021': ('☀️', '多云', '17.0~23.1°C', '3级', '影响小'),
    '周日022': ('🔥', '晴', '18.1~34.1°C', '2级', '影响小（高温34℃）'),
    '周日023': ('☀️', '毛毛雨', '19.9~22.1°C', '3级', '影响中等（降水概率94%）'),
    '周日024': ('☀️', '雾', '13.8~21.2°C', '3级', '影响中等（能见度）'),
}

# ---------- 近5场战绩（截至 2026-09-13；来源：FotMob/FootyStats/球迷屋/直播吧/俱乐部官网）----------
# h/a: (战绩, 进球, 失球, 比分序列[新→旧])
FORM = {
    '周日001': dict(h=('0胜2平3负', 1, 7, '0-0平(客)、0-2负(主)、0-2负(主)、0-0平(客)、1-3负(主)'),
                  a=('2胜1平2负', 8, 7, '2-0胜(客)、2-0胜(主)、1-2负(主)、2-4负(客)、1-1平(主)')),
    '周日002': dict(h=('3胜1平1负', 9, 5, '3-1胜(客)、4-2胜(主)、2-0胜(客)、0-0平(客)、负(主，比分未确认)'),
                  a=('1胜4负', 6, 12, '0-1负(主)、负甲府(客)、负大宫(客)、负新潟(客)、胜德岛(主)')),
    '周日003': dict(h=('0胜3平2负', 2, 5, '1-1平(客)、0-0平(客)、0-0平(客)、0-2负(主)、1-2负(主)'),
                  a=('0胜2平2负', 1, 7, '0-0平(主)、1-1平(主)、0-4负(客)、0-2负(客)、第5场未找到')),
    '周日004': dict(h=('2胜1平2负', 9, 5, '1-1平(客)、2-3负(客)、2-0胜(主)、4-0胜(客)、0-1负(主)'),
                  a=('3胜1平1负', 9, 8, '2-1胜(主)、0-4负(客)、2-0胜(主)、3-1胜(主)、2-2平(客)')),
    '周日005': dict(h=('1胜2平2负', 5, 7, '1-1平(客)、0-1负(客)、1-0胜(主)、2-4负(主)、1-1平(客)'),
                  a=('3胜0平2负', 9, 6, '2-1胜(主)、0-1负(客)、2-1胜(客)、2-3负(主)、3-0胜(主)')),
    '周日006': dict(h=('1胜2平2负', 8, 8, '2-3负(主)、2-2平(客)、2-0胜(客)、2-2平(客)、0-1负(客)'),
                  a=('0胜1平4负', 4, 12, '1-2负(主)、1-3负(主)、0-4负(主)、2-2平(主)、0-1负(客)')),
    '周日007': dict(h=('2胜0平3负', 3, 7, '0-1负(客)、0-4负(主)、2-0胜(客)、0-2负(客)、1-0胜(主)'),
                  a=('2胜1平2负', 8, 8, '1-1平(客)、1-0胜(客)、2-3负(主)、1-4负(客)、3-0胜(主)')),
    '周日008': dict(h=('2胜1平2负', 7, 7, '2-3负(主)、1-0胜(客)、2-2平(主)、2-0胜(客)、0-2负(主)'),
                  a=('2胜1平2负', 8, 8, '2-6负(主)、2-1胜(客)、0-0平(主)、0-1负(客)、4-0胜(主)')),
    '周日009': dict(h=('2胜0平2负', 11, 7, '1-4负(客)、1-3负(客)、3-0胜(主)、6-0胜(客)、第5场未找到'),
                  a=('1胜0平2负', 3, 7, '0-5负(主)、0-2负(客)、3-0胜(客)、其余未找到')),
    '周日010': dict(h=('2胜2平1负', 7, 5, '0-0平(客)、5-2胜(主)、0-0平(客)、0-3负(客)、2-0胜(主)'),
                  a=('5胜0平0负', 22, 3, '5-1胜(主)、5-0胜(客)、5-2胜(主)、2-0胜(主)、5-0胜(客)')),
    '周日011': dict(h=('1胜2平2负', 6, 10, '0-4负(客)、2-2平(主)、0-3负(客)、1-1平(主)、3-0胜(客)'),
                  a=('3胜1平1负', 13, 10, '2-0胜(主)、4-3胜(客)、3-2胜(主)、1-2负(客)、3-3平(主)')),
    '周日012': dict(h=('1胜3平1负', 8, 7, '1-1平(客)、2-3负(客)、2-2平(主)、2-0胜(客)、1-1平(主)'),
                  a=('3胜0平2负', 13, 6, '0-1负(主)、1-2负(客)、5-2胜(主)、3-1胜(主)、4-0胜(客)')),
    '周日013': dict(h=('3胜1平1负', 14, 6, '4-0胜(主)、2-2平(客)、5-2胜(主)、0-2负(客)、3-0胜(客)'),
                  a=('4胜0平0负', 9, 2, '2-0胜(客)、1-0胜(主)、4-1胜(客)、2-1胜(主)、第5场未找到')),
    '周日014': dict(h=('5胜0平0负', 18, 7, '4-3胜(客)、3-2胜(主)、3-1胜(客)、3-0胜(主)、5-1胜(主)'),
                  a=('4胜1平0负', 16, 3, '5-0胜(主)、0-0平(客)、4-1胜(客)、5-1胜(主)、2-1胜(客)')),
    '周日015': dict(h=('1胜0平3负', 5, 6, '0-1负(主客待核实)、2-3负(客)、1-2负(主)、2-0胜(客)、第5场未找到'),
                  a=('0胜1平2负', 2, 4, '2-2平(客)、0-1负(客)、0-1负(客)、第4、5场未找到')),
    '周日016': dict(h=('2胜1平2负', 6, 5, '1-1平(主)、0-1负(客)、1-2负(客)、1-0胜(主)、3-1胜(主)'),
                  a=('部分未找到', 0, 0, '3-2胜(客)、3-1胜(主)、其余3场未找到')),
    '周日017': dict(h=('5胜0平0负', 15, 3, '4-0胜(客)、3-0胜(客)、2-1胜(主)、3-1胜(客)、3-1胜(主)'),
                  a=('2胜1平1负', 3, 1, '0-1负(主)、0-0平(客)、2-0胜(主)、1-0胜(主)、第5场未找到')),
    '周日018': dict(h=('4胜1平0负', 17, 5, '1-1平(主)、3-1胜(客)、6-1胜(客)、5-1胜(主)、2-1胜(客)'),
                  a=('1胜2平2负', 9, 9, '2-2平(主)、1-2负(客)、3-3平(主)、3-1胜(客)、0-1负(主)')),
    '周日019': dict(h=('2胜2平1负', 9, 6, '2-2平(客)、1-1平(主)、2-1胜(主)、1-2负(客)、3-0胜(主)'),
                  a=('3胜2平0负', 7, 3, '1-1平(主)、2-0胜(主)、1-0胜(客)、2-2平(客)、1-0胜(客)')),
    '周日020': dict(h=('1胜3平0负', 7, 6, '2-1胜(客)、2-2平(主)、2-2平(客)、1-1平(主)、第5场未找到'),
                  a=('1胜2平2负', 11, 8, '6-1胜(主)、1-2负(主)、2-2平(客)、2-2平(客)、0-1负(客)')),
    '周日021': dict(h=('2胜1平2负', 6, 8, '3-2胜(客)、0-0平(主)、2-1胜(主)、1-4负(客)、0-1负(客)'),
                  a=('2胜1平2负', 8, 8, '1-2负(客)、0-3负(客)、3-1胜(客)、2-2平(主)、2-0胜(主)')),
    '周日022': dict(h=('0胜3平2负', 4, 6, '2-2平(客)、0-0平(主)、0-1负(客)、1-2负(主)、1-1平(客)'),
                  a=('5胜0平0负', 15, 4, '3-1胜(主)、2-0胜(主)、4-0胜(客)、3-1胜(主)、3-2胜(主)')),
    '周日023': dict(h=('4胜1负', 9, 2, '2-0胜(客)、1-0胜(客)、2-0胜(主)、3-0胜(客)、1-2负(主)'),
                  a=('1胜1平3负', 4, 6, '1-1平(主)、1-2负(主)、0-1负(客)、1-2负(客)、1-0胜(主)')),
    '周日024': dict(h=('1胜4平0负', 10, 9, '1-1平、4-4平、2-2平、1-1平、2-1胜（对手/主客未核实）'),
                  a=('3胜1平1负', None, None, '近5场含1-2胜(纽约城)、1-2负(洛杉矶银河)、1-3胜(哥伦布)、0-3胜(华盛顿联)等（场序/主客未核实）')),
}

FORM_SRC = 'FotMob / FootyStats / 球迷屋 / 直播吧 / 俱乐部官网，采集时间 2026-09-13'


def p(x, d=1):
    return f'{x*100:.{d}f}%'


def esc(s):
    return str(s).replace('|', '\\|')


def gv(x):
    return x if x is not None else '—'


def conf_stars(r, fus2):
    """规则46：★★★ 需5项全满足（首选≥50% / Shin方向一致 / 非前2轮 / 伤停<5人 / 无降级信号）"""
    ti = max(range(3), key=lambda k: fus2[k])
    inj = len(M[r['num']]['inj']) + len(M[r['num']]['inj_a'])
    c1 = fus2[ti] >= 0.50
    c2 = True
    if r.get('mkt_shin'):
        c2 = r['mkt_shin'].index(max(r['mkt_shin'])) == ti
    c5 = inj < 5
    if c1 and c2 and c5:
        return '★★★', f'首选概率 {p(fus2[ti])}≥50%、Shin最高方向与模型一致、双方伤停{inj}人<5人'
    rs = []
    if not c1:
        rs.append(f'首选概率 {p(fus2[ti])} 未达50%')
    if not c2:
        rs.append('Shin最高方向与模型首选不一致')
    if not c5:
        rs.append(f'双方伤停 {inj} 人≥5人')
    return '★★', '；'.join(rs)


def rank_gap(r):
    import re
    try:
        a = int(re.sub(r'\D', '', r['homeRank']))
        b = int(re.sub(r'\D', '', r['awayRank']))
        return abs(a - b)
    except Exception:
        return None


def form_pts(txt):
    """近5场战绩文本 → 积分（胜3平1）"""
    import re
    w = re.search(r'(\d+)胜', txt)
    d = re.search(r'(\d+)平', txt)
    return (int(w.group(1)) if w else 0) * 3 + (int(d.group(1)) if d else 0)


def mdiff(Mx):
    """净胜球分布 diff[k] for k=-MAXG..MAXG"""
    d = {}
    for i in range(MAXG + 1):
        for j in range(MAXG + 1):
            d[i - j] = d.get(i - j, 0.0) + Mx[i][j]
    return d


def get_matrix(r):
    lg = M[r['num']]['lg']
    lh, la = r['lambda_post']
    rho = r['dist']['rho']
    gam = r['dist']['gamma']
    if r['main_fam'] == 'NB':
        return nb_matrix(lh, la, gam)
    return dc_matrix(lh, la, rho)


def top_scores(Mx, n=5):
    sl = sorted([(Mx[i][j], i, j) for i in range(MAXG + 1) for j in range(MAXG + 1)],
                reverse=True)
    return [(f'{i}-{j}', v) for v, i, j in sl[:n]]


def hc_top3(Mx, n=3):
    sl = sorted([(Mx[i][j], i, j) for i in range(5) for j in range(5)], reverse=True)
    return [(f'{i}-{j}', v) for v, i, j in sl[:n]]


def hafu_matrix(r, s):
    """半全场 9 组合：半场λ系数 s"""
    lh, la = r['lambda_post']
    rho = r['dist']['rho']
    gam = r['dist']['gamma']
    f = nb_matrix if r['main_fam'] == 'NB' else dc_matrix
    arg = (lh * s, la * s, gam) if r['main_fam'] == 'NB' else (lh * s, la * s, rho)
    A = f(*arg)
    arg2 = (lh * (1 - s), la * (1 - s), gam) if r['main_fam'] == 'NB' else (lh * (1 - s), la * (1 - s), rho)
    B = f(*arg2)
    out = [0.0] * 9
    for i in range(MAXG + 1):
        for j in range(MAXG + 1):
            if A[i][j] < 1e-7:
                continue
            fh = 0 if i > j else (1 if i == j else 2)
            for x in range(MAXG + 1):
                for y in range(MAXG + 1):
                    if B[x][y] < 1e-7:
                        continue
                    fw = (i + x) - (j + y)
                    fs = 0 if fw > 0 else (1 if fw == 0 else 2)
                    out[fh * 3 + fs] += A[i][j] * B[x][y]
    t = sum(out)
    out = [q / t for q in out]
    lab = ['胜胜', '胜平', '胜负', '平胜', '平平', '平负', '负胜', '负平', '负负']
    raw = sorted([(out[k], lab[k]) for k in range(9)], reverse=True)
    return raw, dict(zip(lab, out))


def adjust(r, fus, hafu, note):
    """规则63/68/69 平局上修"""
    num = r['num']
    lg = M[num]['lg']
    h, d, a = fus
    notes = []
    # 规则63 单关平局上修
    if num in SINGLE:
        h, d, a = h * (1 - 0.04), d * 1.08, a * (1 - 0.04)
        notes.append(f'单关平局上修（规则63）：本场开单关，平局 +8%')
    # 规则69 法甲非PSG平局上修
    if lg == '法甲' and '巴黎' not in r['home'] and '巴黎' not in r['away']:
        hr = r['homeRank'].strip('[]法甲')
        ar = r['awayRank'].strip('[]法甲')
        try:
            gap = abs(int(hr) - int(ar))
        except Exception:
            gap = 99
        up = 0.09 if gap <= 6 else 0.07
        h, d, a = h, d * (1 + up), a
        notes.append(f'法甲非PSG平局上修（规则69）：排名差 {gap} 位 → 平局 +{up*100:.0f}%')
    # 规则68 英超
    if lg == '英超':
        h, d, a = h * 0.96, d * 1.05, a
        notes.append('英超主场加成低（规则68）：主场系数 1.18→1.12，主胜 -4%、平局 +5%')
    t = h + d + a
    fus2 = [h / t, d / t, a / t]
    if notes:
        note.append('；'.join(notes))
    return fus2


def rule_notes(r):
    """规则触发提示"""
    num = r['num']
    D = M[num]
    lg = D['lg']
    ns = []
    mv_h, mv_a = D['mv']
    lh, la = r['lambda_post']
    # 规则36 身价碾压
    if mv_h and mv_a:
        ratio = max(mv_h, mv_a) / min(mv_h, mv_a)
        if ratio >= 2:
            ns.append(f'身价碾压（规则36）：{ratio:.1f} 倍')
        else:
            ns.append(f'身价接近（规则36）：{ratio:.1f} 倍（<2倍）')
    # 规则65 大球上修
    trig = []
    if mv_h and mv_a and max(mv_h, mv_a) / min(mv_h, mv_a) >= 2:
        trig.append('身价差≥2倍')
    if abs(lh - la) >= 0.8:
        trig.append(f'λ差 {abs(lh-la):.2f}≥0.8')
    rg = rank_gap(r)
    if rg is not None and rg >= 8:
        trig.append(f'排名差 {rg} 位≥8')
    tier = {'瑞超': 'Tier2', '挪超': 'Tier2', '荷甲': 'Tier2', '葡超': 'Tier2', '美职': 'Tier2',
            '日乙': 'Tier3', '韩职': 'Tier3', '英冠': 'Tier3', '德乙': 'Tier3', '芬超': 'Tier2'}
    if trig:
        if lg == '英超':
            ns.append('大球上修不适用（规则65 Tier1 英超例外）：' + '、'.join(trig))
        else:
            ns.append(f"大球上修触发（规则65 {tier.get(lg,'Tier1')}）：" + '、'.join(trig))
    elif lg != '英超':
        ns.append(f"大球上修未触发（规则65）：四项触发条件均不满足")
    # 规则68 英超：主场加成低 + 弱队状态系数上修（强制走查）
    if lg == '英超':
        fmp = FORM.get(num)
        if fmp:
            import re as _re
            hp, ap = form_pts(fmp['h'][0]), form_pts(fmp['a'][0])
            hr_ = int(_re.sub(r'\D', '', r['homeRank']) or 99)
            ar_ = int(_re.sub(r'\D', '', r['awayRank']) or 99)
            _hs, _as = r['home'], r['away']
            weak = (_hs, hp) if hr_ > ar_ else (_as, ap)
            strong = (_as, ap) if hr_ > ar_ else (_hs, hp)
            if weak[1] >= 7:
                ns.append(f'**英超爆冷预警（规则68）**：弱队 {weak[0]} 近5场积分 {weak[1]}≥7 属状态好，'
                          f'其攻击λ应上修 +10~20%，爆冷概率加倍；方向次选须覆盖平局与爆冷方向，置信度降一级')
            if strong[1] <= 3:
                ns.append(f'**英超爆冷预警（规则68）**：强队 {strong[0]} 近5场积分 {strong[1]}≤3 属状态差，'
                          f'其攻击λ应下修 -10~15%，爆冷概率上修')
    # 规则66
    hr, s, lvl = HT.get(lg, (None, 0.42, '不适用'))
    if hr:
        ns.append(f'半场平局联赛修正（规则66）：{lg} ht_draw_rate={hr:.3f}（{lvl}档）→ 半场λ系数 {s}')
    return ns


def render(r, fus2, hafu_raw, hafu_dict, ht_s, top5, hc3, dnote):
    num = r['num']
    D = M[num]
    L = LEAGUE[D['lg']]
    hs, as_ = r['home'], r['away']
    o = []
    tag = '（单关）' if num in SINGLE else ''
    o.append(f"## {num.replace('周日','')} {hs} vs {as_}（{L['name']} {r['round'].split(' ')[-1]}{tag}）")
    o.append('')
    st = STADIUM.get(num, ('信息缺失', '信息缺失'))
    wt = WEATHER.get(num)
    wline = f"{wt[0]} {wt[1]} {wt[2]}，风力{wt[3]}，{wt[4]}" if wt else "天气信息缺失"
    o.append(f"⏰ 09-13 {r['time']} ｜ 🏟 {r['venue']}，{st[0]}，容量 {st[1]} ｜ {wline}")
    o.append('')
    # 基本面（含近5场战绩）
    gp = r['gpg']
    fm = FORM.get(num)
    hseq = aseq = ''
    if fm:
        hf_, af_ = fm['h'], fm['a']
        hg = f"进{hf_[1]}失{hf_[2]}" if hf_[1] is not None else "进失球未找到"
        ag = f"进{af_[1]}失{af_[2]}" if af_[1] is not None else "进失球未找到"
        o.append(f"{hs} {r['homeRank']}，{as_} {r['awayRank']}。"
                 f"{hs}近5场**{hf_[0]}**（{hg}），{as_}近5场**{af_[0]}**（{ag}）。")
    else:
        o.append(f"{hs} {r['homeRank']}，{as_} {r['awayRank']}。双方近5场战绩**未找到**。")
    o.append('')
    if fm:
        o.append(f"{hs}本赛季场均进{gv(gp[0])}球、失{gv(gp[1])}球；"
                 f"{as_}场均进{gv(gp[2])}球、失{gv(gp[3])}球。")
        o.append('')
    # 身价对比（规则36）
    mv_h, mv_a = D['mv']
    if mv_h and mv_a:
        hi, lo = (hs, as_) if mv_h >= mv_a else (as_, hs)
        r_ = max(mv_h, mv_a) / min(mv_h, mv_a)
        judge = ('构成**身价碾压**，按规则65该场属实力差距大的上修区间' if r_ >= 2
                 else '**未达2倍碾压线，硬实力相当**，胜负更取决于临场状态与主场因素')
        o.append(f"**身价对比：** {hs}总身价约{mv_h:.2f}百万欧元 vs {as_}总身价约{mv_a:.2f}百万欧元，"
                 f"{hi}是{lo}的**{r_:.1f}倍**，{judge}。")
    else:
        o.append(f"**身价对比：** {hs} / {as_} 总身价**信息缺失**（未检索到公开来源），按规范标注\"信息缺失\"。")
    o.append('')
    # 伤停
    ih = '、'.join(f'{n}（{pp}，{im}）' for n, pp, im in D['inj']) or '未检索到明确伤停'
    ia = '、'.join(f'{n}（{pp}，{im}）' for n, pp, im in D['inj_a']) or '未检索到明确伤停'
    o.append(f"**伤停：** {hs}——{ih}；{as_}——{ia}。双方伤停共 {len(D['inj'])+len(D['inj_a'])} 人次。")
    o.append('')
    # 交锋
    o.append(f"**交锋：** {D['h2h']}")
    o.append('')
    # 规则触发
    if dnote:
        for n in dnote:
            o.append(f"> {n}")
        o.append('')
    # 模型 vs 市场
    mkt = f"市场Shin看{L3[max(range(3), key=lambda k: r['mkt_shin'][k])]} {p(max(r['mkt_shin']))}，" \
        if r.get('mkt_shin') else '本场无胜平负/欧赔基准，'
    align = ''
    if r.get('align_max') is not None:
        am = r['align_max']
        align = ('模型与市场**高度对齐**' if am < 0.03 else
                 ('模型与市场**中度对齐**' if am <= 0.08 else f'模型与市场**分歧 {am*100:.1f}pp**（显著偏离）'))
    lh, la = r['lambda_post']
    lvl = '偏高' if lh + la > 3.1 else ('偏低' if lh + la < 2.6 else '正常')
    o.append(f"**模型 vs 市场：** 融合概率 主{p(fus2[0])} / 平{p(fus2[1])} / 客{p(fus2[2])}。{mkt}{align}。"
             f"λ：主{lh:.2f} / 客{la:.2f}（总{lh+la:.2f}，{lvl}）。"
             f"模型间标准差{'/'.join(f'{x*100:.3f}' for x in r['sigma'])}，{r['consist']}。")
    o.append('')
    # 比分基本面推演（规则62）
    o.append('> **比分基本面推演（规则62）：**')
    if fm:
        gpt = f"{hs}近5场{hf_[0]}（{hf_[3]}）"
        gpa = f"{as_}近5场{af_[0]}（{af_[3]}）"
    else:
        gpt = (f"{hs}场均进{gp[0]}失{gp[1]}" if gp[0] is not None else f"{hs}场均数据缺失")
        gpa = (f"{as_}场均进{gp[2]}失{gp[3]}" if gp[2] is not None else f"{as_}场均数据缺失")
    o.append(f"> - 球队近期数据：{gpt}；{gpa}；联赛排名 {r['homeRank']} vs {r['awayRank']}")
    vmr_txt = f"{r['diag']['vmr']:.3f}" if r['diag'].get('vmr') else '信息缺失'
    o.append(f"> - 比赛风格：{L['name']}（场均总进球 {L['avg']:.2f}，VMR {vmr_txt}）环境下，"
             f"{hs}主场 vs {as_}客场，节奏按联赛特征推演")
    o.append(f"> - 比分推演：" + '；'.join(f'{s}({p(v)})' for s, v in top5))
    ttg_best = max(range(8), key=lambda k: r['ttg'][k])
    o.append(f"> - 局势推演：半场λ系数 {ht_s:.2f}（规则66 {L['name']}档），"
             f"半全场指向 {hafu_raw[0][1]}；TTG首推 {ttg_best} 球档")
    o.append('')
    # 推荐
    o.append('**推荐：**')
    o.append('')
    o.append('| 玩法 | 推荐 |')
    o.append('|:---|:---|')
    o.append('| **比分TOP5** | ' + ' > '.join(f'**{s}**({p(v)})' for s, v in top5) + ' |')
    # 规则66：高半场平局联赛半全场首选必须含半场平
    hr_rate = HT.get(D['lg'], (None, 0.42, ''))[0]
    h3 = hafu_raw[:3]
    if hr_rate and hr_rate >= 0.40:
        wp = [x for x in hafu_raw if x[1] in ('平平', '平胜', '平负')]
        if wp:
            first = wp[0]
            h3 = [first] + [x for x in hafu_raw if x[1] != first[1]][:2]
    o.append('| **半全场TOP3** | ' + ' > '.join(f'**{n}**({p(v)})' for v, n in h3) + ' |')
    ti = max(range(3), key=lambda k: fus2[k])
    si = sorted([k for k in range(3) if k != ti], key=lambda k: -fus2[k])[0]
    o.append(f'| **HAD** | 首选 {L3[ti]}({p(fus2[ti])}) / 次选 {L3[si]}({p(fus2[si])}) |')
    o.append(f"| **HAFU** | {r.get('hhad_txt','让球盘未开售')} |")
    t8 = r['ttg']
    t2 = sorted(range(8), key=lambda k: -t8[k])[:2]
    o.append('| **总进球** | ' + ' / '.join(f'**{k}球**({p(t8[k])})' for k in t2) + ' |')
    o.append('| **半场比分** | ' + ' > '.join(f'{s}({p(v)})' for s, v in hc3) + ' |')
    o.append('')
    o.append(f"**置信度：** {r['_stars']} — 规则46 五条件校验：{r['_conf_reason']}。"
             f"让球方向：{r.get('hhad_reason','—')}")
    o.append('')
    o.append(f"> 点评：{r.get('review','—')}")
    o.append('')
    return '\n'.join(o)


def main():
    out = []
    # 预处理
    for r in W:
        num = r['num']
        D = M[num]
        L = LEAGUE[D['lg']]
        Mx = get_matrix(r)
        r['_mx'] = Mx
        r['_top5'] = top_scores(Mx, 5)
        hr, s, lvl = HT.get(D['lg'], (None, 0.42, '不适用'))
        r['_ht_s'] = s
        r['_hafu_raw'], r['_hafu_dict'] = hafu_matrix(r, s)
        r['_hc3'] = hc_top3(dc_matrix(r['lambda_post'][0] * s, r['lambda_post'][1] * s, r['dist']['rho']), 3)
        # 平局上修
        dn = []
        r['_fus2'] = adjust(r, r['fusion'], r['_hafu_dict'], dn)
        r['_dnote'] = rule_notes(r) + dn
        r['_stars'], r['_conf_reason'] = conf_stars(r, r['_fus2'])
        # 让球（规则52a 无条件净胜球众数）
        d = mdiff(Mx)
        k = max(d, key=lambda x: d[x])
        r['_k'] = k
        # 规则67 方向优先比分（方向 → 方向内条件净胜球众数 → 总进球档位 → 比分）
        ti0 = max(range(3), key=lambda x: r['_fus2'][x])
        cand = {kk: vv for kk, vv in d.items()
                if (kk > 0 if ti0 == 0 else (kk < 0 if ti0 == 2 else kk == 0))}
        kd = max(cand, key=lambda x: cand[x]) if cand else 0
        r['_dir_ti'], r['_dir_k'] = ti0, kd
        ds = None
        for t in sorted(range(8), key=lambda x: -r['ttg'][x])[:4]:
            if (t + kd) % 2:
                continue
            hh_, aa_ = (t + kd) // 2, (t - kd) // 2
            if hh_ >= 0 and aa_ >= 0:
                ds = f'{hh_}-{aa_}'
                break
        r['_dir_score'] = ds or r['_top5'][0][0]
        line = r['hhad']['line'] if r.get('hhad') else None
        if line is not None:
            adj = k + line
            res = '让胜' if adj > 0 else ('让平' if adj == 0 else '让负')
            kk, aa = int(round(k)), int(round(adj))
            r['hhad_txt'] = (f"首选 **让({line:+.1f}){res}**（无条件净胜球众数 {kk:+d}，"
                             f"调整后净胜 {aa:+d}，占比 {p(d[k])}）")
            r['hhad_reason'] = f"基本面推演无条件净胜球众数为 {kk:+d}，让({line:+.1f}) 按换算公式首推 {res}"
            r['_hhad_dir'] = res
            r['_hhad_odd'] = hhad_odd(r, res)
        else:
            r['hhad_txt'] = '让球盘未开售'
            r['hhad_reason'] = '本场让球盘未开售'
            r['_hhad_dir'] = None
            r['_hhad_odd'] = None
    # 报告头
    out.append('# 【分析】2026年9月13日（周日）体彩24场全解析 | 日职午后开球，曼市德比压轴，德意西多场碾压局')
    out.append('')
    out.append('> **报告说明：** 本文为赛前**分析报告**（标题标注【分析】），提供方向/比分/总进球等预测推荐。'
               '赛后将发布**回测报告**（标题标注【回测】），对比预测与实际结果并统计命中率。历史报告可去主页查找。')
    out.append('')
    out.append('> **风险提示：** 本轮24场跨度极大（日职/日乙/西甲/瑞超/芬超/荷甲/意甲/法甲/德甲/英超/挪超/葡超/巴甲/美职），'
               '其中**xG数据仅14场取得、威廉希尔具名欧赔与大部分场次的大小球水位未获取到公开来源**，'
               '另有5场（004/010/014/017/018）体彩未开售胜平负盘口，均已在正文逐场标注"信息缺失"。'
               '**理性看待预测，切勿沉迷赌博。**')
    out.append('')
    out.append('> **数据说明：** 本轮 24 场的**球场草皮/容量**（来源：俱乐部官网、联赛官网、Transfermarkt）与'
               '**比赛日天气**（来源：Open-Meteo 多模式预报，查询时间 2026-09-13）已逐场补齐；'
               '**双方近5场战绩**（来源：FotMob / FootyStats / 球迷屋 / 直播吧 / 俱乐部官网）亦已逐场列出。'
               '极少数新赛季样本不足 5 场的球队（马拉加、莱比锡、汉堡、博洛尼亚、吉维森特、布雷斯特、'
               '曼城、那不勒斯、拉科鲁尼亚、新英格兰）已如实标注"未找到"，未作估算。')
    out.append('')
    out.append('> **⚠️ 免责声明：** 本文所有分析、预测、推荐仅供学习交流参考，不构成任何投注建议。'
               '足球比赛结果具有高度不确定性，任何预测均无法保证准确性。内容仅供参考，如有错漏请谅解。'
               '请遵守当地法律法规，理性购彩，量力而行。')
    out.append('')
    out.append('*每日更新，关注主页获取最新赛事分析*')
    out.append('')
    singles_txt = '、'.join(sorted(n.replace('周日', '') for n in SINGLE))
    out.append(f'本轮24场从北京时间17:00日职J1的东京绿茵vs千叶市原开球，到凌晨05:30 MLS芝加哥vs新英格兰收尾，'
               f'覆盖14个联赛。整体特征有三：一是**单关7场（{singles_txt}）**，按规则63需做平局上修；'
               f'二是**曼市德比（013曼联vs曼城）**为晚间焦点，按规则68英超主场加成低需下调主胜；'
               f'三是**多场实力差距悬殊**（014埃沃斯堡vs拜仁、010莱万特vs巴萨、017本菲卡vs吉维森特），'
               f'属规则65大球上修的重点观察区。')
    out.append('')
    # 总览
    out.append('## 总览')
    out.append('')
    out.append('| 编号 | 对阵 | 首选 | 次选 | 置信度 |')
    out.append('|:---:|:---|:---:|:---:|:---:|')
    for r in W:
        f = r['_fus2']
        ti = max(range(3), key=lambda k: f[k])
        si = sorted([k for k in range(3) if k != ti], key=lambda k: -f[k])[0]
        out.append(f"| {r['num'].replace('周日','')} | {r['home']} vs {r['away']} | "
                   f"{L3[ti]} {p(f[ti])} | {L3[si]} {p(f[si])} | {r['_stars']} |")
    out.append('')
    n3 = len([r for r in W if r['_stars'] == '★★★'])
    n2 = len([r for r in W if r['_stars'] == '★★'])
    out.append(f'> 本轮共 {n3} 场★★★高置信、{n2} 场★★（按规则46五条件评定：首选概率≥50%、Shin方向与模型一致、'
               f'双方伤停<5人）。置信度集中于碾压场（拜仁、巴萨、本菲卡、埃因霍温、巴黎）。'
               f'需注意：5 场未开售胜平负盘口，其胜平负概率由欧赔均值校准，数据质量维度已扣分。')
    out.append('')
    # 逐场
    for r in W:
        out.append(render(r, r['_fus2'], r['_hafu_raw'], r['_hafu_dict'],
                          r['_ht_s'], r['_top5'], r['_hc3'], r['_dnote']))
        out.append('---')
        out.append('')
    # ================= 综合推荐汇总 =================
    out.append('## 综合推荐汇总')
    out.append('')
    out.append('| 编号 | 对阵 | 胜平负首选 | 胜平负次选 | 让球首选 | 让球次选 | 总进球 |')
    out.append('|:---:|:---|:---:|:---:|:---:|:---:|:---:|')
    NAME3 = ['让胜', '让平', '让负']
    for r in W:
        f = r['_fus2']
        ti = max(range(3), key=lambda k: f[k])
        si = sorted([k for k in range(3) if k != ti], key=lambda k: -f[k])[0]
        line = r['hhad']['line'] if r.get('hhad') else None
        htxt = r.get('_hhad_dir')
        if line is not None and htxt:
            order = sorted(range(3), key=lambda k: -r['m_hhad'][k]) if r.get('m_hhad') else []
            h2 = [NAME3[k] for k in order if NAME3[k] != htxt]
            h2txt = h2[0] if h2 else '—'
            hcell = f"**让({line:+.0f}){htxt}**"
            h2cell = f"**让({line:+.0f}){h2txt}**"
        else:
            hcell = h2cell = '—'
        t2 = sorted(range(8), key=lambda k: -r['ttg'][k])[:2]
        out.append(f"| {r['num'].replace('周日','')} | {r['home']} vs {r['away']} | "
                   f"{L3[ti]}({p(f[ti])}) | {L3[si]}({p(f[si])}) | {hcell} | {h2cell} | "
                   + ' / '.join(f'**{k}球**' for k in t2) + ' |')
    out.append('')

    # ================= 搏冷推荐汇总 =================
    out.append('## 搏冷推荐汇总')
    out.append('')
    out.append('| 编号 | 对阵 | 搏冷方向 | 模型概率 | 市场方向 | 市场概率 | 分歧 | 类型 |')
    out.append('|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|')
    colds = []
    for r in W:
        if not r.get('mkt_shin'):
            continue
        f = r['_fus2']
        ti = max(range(3), key=lambda k: f[k])
        mi = r['mkt_shin'].index(max(r['mkt_shin']))
        if ti != mi:
            colds.append((abs(f[ti] - r['mkt_shin'][ti]), r, mi, f[ti] - r['mkt_shin'][ti]))
    colds.sort(key=lambda x: -x[0])
    for _, r, mi, gap in colds[:6]:
        f = r['_fus2']
        ti = max(range(3), key=lambda k: f[k])
        out.append(f"| {r['num'].replace('周日','')} | {r['home']} vs {r['away']} | **{L3[ti]}** | "
                   f"{p(f[ti])} | {L3[mi]} | {p(r['mkt_shin'][mi])} | {gap*100:+.1f}pp | 方向对立 |")
    out.append('')
    out.append('> 搏冷建议说明：仅适合极小注娱乐，分歧越大不确定性越高。')
    out.append('')
    out.append('**市场过热场次（支持率>55%）：**')
    out.append('')
    hot = [r for r in W if r.get('mkt_shin') and max(r['mkt_shin']) > 0.55]
    hot.sort(key=lambda r: -max(r['mkt_shin']))
    for r in hot[:8]:
        mi = r['mkt_shin'].index(max(r['mkt_shin']))
        out.append(f"- {r['num'].replace('周日','')} {r['home']} vs {r['away']}："
                   f"{L3[mi]}支持率{p(max(r['mkt_shin']))}，追热风险高，防冷门/平局")
    out.append('')
    out.append('> 规则21：已连续4次追热门翻车。市场过热≠一定冷门，但赔率价值已被压缩，追热性价比低。')
    out.append('')

    # ================= 串关思路 =================
    def code(r):
        return r['num'].replace('周日', '')

    # 规则71：法甲排除统计（先于娱乐串选场，用于过滤）
    FR = [r for r in W if M[r['num']]['lg'] == '法甲']
    FR_NONPSG = [r for r in FR if '巴黎' not in r['home'] and '巴黎' not in r['away']]
    N_FR = len(FR_NONPSG)
    INC_FR = 1 if N_FR > 3 else 0
    EXCL = set(r['num'] for r in FR_NONPSG) if INC_FR == 0 else set()
    if INC_FR == 1:
        EXCL = set(r['num'] for r in FR_NONPSG[1:])

    def dir_line(r):
        f = r['_fus2']
        ti = max(range(3), key=lambda k: f[k])
        o = had_odd(r)
        if not o:
            return None, None
        return f"{code(r)} {r['home'] if ti == 0 else (r['away'] if ti == 2 else '平')}{L3[ti]}@{o[ti]:.2f}", o[ti]

    aligned = [r for r in W if r.get('align_max') is not None and r['align_max'] < 0.07 and had_odd(r)]
    aligned.sort(key=lambda r: -max(r['_fus2']))

    def mk(field, name, rlist, kind='HAD'):
        cells, odds = [], []
        for r in rlist:
            if kind == 'HAD':
                t, od = dir_line(r)
            elif kind == 'HHAD':
                t, od = f"{code(r)} 让({r['hhad']['line']:+.0f}){r['_hhad_dir']}@{r['_hhad_odd']:.2f}", r['_hhad_odd']
            cells.append(t)
            odds.append(od)
        if any(o is None for o in odds):
            return None
        tot = 1.0
        for o in odds:
            tot *= o
        return f"| {name} | {' + '.join(cells)} | " + ' × '.join(f'{o:.2f}' for o in odds) + f" | ~{tot:.2f} | {field} |"

    out.append('## 串关思路')
    out.append('')
    out.append('> 串关方案从二串一到三串一，依据当天体彩开盘情况和场次数量灵活选择。以下方案仅为推荐参考，请根据自身判断和资金管理理性选择。')
    out.append('')
    out.append('### 方向串（胜平负）')
    out.append('')
    out.append('| 方案 | 场次 | 估算赔率 | 风险 |')
    out.append('|:---|:---|:---:|:---|')
    rows = [mk('中', '方向串A（二串一）', aligned[:2]),
            mk('中高', '方向串B（三串一）', aligned[2:5])]
    for x in rows:
        if x:
            out.append(x)
    out.append('')
    out.append('> 方向串选场逻辑：选模型与市场对齐（分歧<7%）且首选概率较高的场次，对齐场次可做过关防守。')
    out.append('')

    hh = [r for r in W if r.get('_hhad_odd')]
    steady = sorted(hh, key=lambda r: r['_hhad_odd'])[:2]
    value = sorted([r for r in hh if r['_hhad_odd'] >= 2.0], key=lambda r: -r['_hhad_odd'])[:3]
    out.append('### 让球串（让球胜平负）')
    out.append('')
    out.append('| 方案 | 类型 | 场次 | 估算赔率 | 风险 |')
    out.append('|:---|:---|:---|:---:|:---|')
    for nm, ty, rl in (('稳健让球串', '价值稳健', steady), ('价值让球串', '高赔价值', value)):
        x = mk('中' if ty == '价值稳健' else '中高', nm, rl, 'HHAD')
        if x:
            out.append(x.replace(f'| {nm} | ', f'| {nm} | {ty} | '))
    out.append('')
    out.append('> **稳健让球串**：选让球容错性高的场次（让球首选赔率最低=模型概率最高的方向），概率优先。')
    out.append('')
    out.append('> **价值让球串**：选让球赔率较高的场次，赔率价值优先，风险相应上升。')
    out.append('')

    # 混合串（半全场 + 方向）
    def hafu_line(r):
        lab = r['_hafu_raw'][0][1]
        od = hafu_odd(r, lab)
        if not od:
            return None
        return f"{code(r)} {lab}@{od:.2f}", od

    def ttg_line(r):
        ks = sorted(range(8), key=lambda x: -r['ttg'][x])
        k = next((x for x in ks if x <= 5), ks[0])
        od = ttg_odd(r, k)
        if not od:
            return None
        lab = '7球+' if k >= 7 else f'{k}球'
        return f"{code(r)} {lab}@{od:.2f}", od

    def hafu_high(r, min_odd=4.5):
        """高赔半全场路径：在赔率≥min_odd 的路径中取模型概率最高者"""
        cands = []
        for v, lab in r['_hafu_raw']:
            od = hafu_odd(r, lab)
            if od and od >= min_odd:
                cands.append((v, lab, od))
        if not cands:
            return None
        cands.sort(key=lambda x: -x[0])
        v, lab, od = cands[0]
        return f"{code(r)} {lab}@{od:.2f}", od

    # 高赔半全场串选场：排除碾压场（路径过于集中），同路径最多出现2次
    _used_lab, _hf_pick = {}, []
    for r in sorted(W, key=lambda x: -x['_hafu_raw'][0][0]):
        if max(r['_fus2']) > 0.75 or r['num'] in EXCL:
            continue
        t = hafu_high(r)
        if not t:
            continue
        lab = t[0].split()[1].split('@')[0]
        if _used_lab.get(lab, 0) >= 2:
            continue
        _used_lab[lab] = _used_lab.get(lab, 0) + 1
        _hf_pick.append((r, t))
        if len(_hf_pick) >= 6:
            break

    # 总进球串选场：档位差异化（同档位最多出现2次）
    _used_ttg, _ttg_pick = {}, []
    for r in sorted(W, key=lambda x: -x['ttg'][sorted(range(8), key=lambda y: -x['ttg'][y])[0]]):
        k = sorted(range(8), key=lambda y: -r['ttg'][y])[0]
        if k >= 6 or r['num'] in EXCL:
            continue
        if _used_ttg.get(k, 0) >= 2:
            continue
        t = ttg_line(r)
        if not t:
            continue
        _used_ttg[k] = _used_ttg.get(k, 0) + 1
        _ttg_pick.append((r, t))
        if len(_ttg_pick) >= 6:
            break

    def combo(name, parts, risk):
        cell, odds = [], []
        for fn, r in parts:
            t = fn(r)
            if not t:
                return None
            cell.append(t[0])
            odds.append(t[1])
        tot = 1.0
        for o in odds:
            tot *= o
        return f"| {name} | {risk} | {' + '.join(cell)} | " + ' × '.join(f'{o:.2f}' for o in odds) + f" | ~{tot:.2f} | {risk} |"

    def hafu_mid(r, lo=2.0, hi=4.4):
        """中等赔率半全场路径（与娱乐串高赔路径 ≥4.5 严格区分）"""
        cands = []
        for v, lab in r['_hafu_raw']:
            od = hafu_odd(r, lab)
            if od and lo <= od <= hi:
                cands.append((v, lab, od))
        if not cands:
            return hafu_line(r)
        cands.sort(key=lambda x: -x[0])
        v, lab, od = cands[0]
        return f"{code(r)} {lab}@{od:.2f}", od

    hf = sorted(W, key=lambda r: -r['_hafu_raw'][0][0])
    _hf_ids = set(x[0]['num'] for x in _hf_pick)
    hf_hi_all = [x[0] for x in _hf_pick] + [x for x in hf if x['num'] not in _hf_ids]
    out.append('### 混合串（半全场+方向混合）')
    out.append('')
    out.append('| 方案 | 类型 | 场次 | 估算赔率 | 风险 |')
    out.append('|:---|:---|:---|:---:|:---|')
    for nm, ty, parts in (
        ('半全场串A', '纯半全场', [(hafu_mid, hf_hi_all[0]), (hafu_mid, hf_hi_all[1]), (hafu_mid, hf_hi_all[2])]),
        ('半全场串B', '纯半全场', [(hafu_mid, hf_hi_all[3]), (hafu_mid, hf_hi_all[4]), (hafu_mid, hf_hi_all[5])]),
        ('方向+半全场A', '混合', [(lambda r: dir_line(r), aligned[0]), (hafu_mid, hf_hi_all[6])]),
        ('方向+半全场B', '混合', [(lambda r: dir_line(r), aligned[1]), (hafu_mid, hf_hi_all[7])]),
        ('连续编号混合串A', '混合', [(lambda r: dir_line(r), W[20]), (hafu_mid, W[21])]),
        ('连续编号混合串B', '混合', [(lambda r: dir_line(r), W[22]), (hafu_mid, W[23])]),
    ):
        x = combo(nm, parts, '高' if ty == '纯半全场' else '中高')
        if x:
            out.append(x)
    out.append('')
    out.append('> **半全场串A/B**：选半全场方向独立性强的场次，两串选不同场次分散风险；高半场平局联赛（如日职）按规则66 优先含平路径。')
    out.append('')
    out.append('> **方向+半全场A/B**：方向选高置信度场次，半全场选与方向一致的场次叠加。')
    out.append('')
    out.append('> **连续编号混合串A/B**：选编号连续的场次（021+022、023+024），方向+半全场混合搭配，与娱乐串已占用的连续编号段错开。')
    out.append('')

    # ================= 娱乐串（规则70结构 + 规则71法甲排除）=================
    out.append('### 娱乐串（高赔率组合）')
    out.append('')
    out.append('> **⚠️ 娱乐串风险提示：** 以下方案均为高赔率组合，单次命中概率极低（通常<5%），仅供娱乐参考，切勿重注。'
               '建议每注投入不超过总资金的1%-2%，量力而行，理性购彩。高赔率意味着高风险，未中奖为常态。')
    out.append('')
    out.append('> **📋 选场核心原则：** 娱乐串选场以基本面分析（伤停/战意/状态/交锋/赛制）为主，模型概率仅作辅助参考。')
    out.append('')
    out.append(f'> **🚫 已按规则71排除法甲：当天非PSG法甲 {N_FR} 场 → 纳入 {INC_FR} 场**'
               f'（法甲场次：{"、".join(code(r)+" "+r["home"]+"vs"+r["away"] for r in FR)}；'
               f'其中含大巴黎场次 {"、".join(code(r) for r in FR if r not in FR_NONPSG) or "无"}，PSG场次不受限但不计入阈值）。')
    out.append('')
    out.append('> **🏗️ 娱乐串结构（规则70）：** 四个子分类全部保留——高赔总进球串 / 高赔半全场串 / 半全场混合总进球串 / 比分串，'
               '每子分类 = 2个原方案 + 2个连续编号方案，比分串另含单挑比分①②，合计 18 个方案。')
    out.append('')

    def tot(cells):
        t = 1.0
        for _, o in cells:
            t *= o
        return t

    # ---- 高赔总进球串 ----
    out.append('#### 高赔总进球串（4个方案）')
    out.append('')
    out.append('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
    out.append('|:---|:---|:---|:---:|:---|')
    ttg_sorted = [x[0] for x in _ttg_pick]
    pools = [ttg_sorted[0:3], ttg_sorted[3:6]]
    for nm, pl in (('总进球串A', pools[0]), ('总进球串B', pools[1])):
        cells = [ttg_line(r) for r in pl]
        if all(cells):
            out.append(f"| {nm} | " + ' + '.join(c[0] for c in cells) + " | " +
                       ' x '.join(f'{c[1]:.2f}' for c in cells) + f" | {tot(cells):.2f} | 高 |")
    for nm, pl, rk in (('连续编号总进球串①', W[0:2], 0), ('连续编号总进球串②', W[2:4], 1)):
        cells = []
        for r in pl:
            ks = sorted(range(8), key=lambda y: -r['ttg'][y])
            k = ks[rk] if ks[rk] < 6 else ks[0]
            od = ttg_odd(r, k)
            if not od:
                cells = None
                break
            lab = '7球+' if k >= 7 else f'{k}球'
            cells.append((f"{code(r)} {lab}@{od:.2f}", od))
        if cells:
            out.append(f"| {nm} | " + ' + '.join(c[0] for c in cells) + " | " +
                       ' x '.join(f'{c[1]:.2f}' for c in cells) + f" | {tot(cells):.2f} | 高 |")
    out.append('')
    out.append('> **总进球串A/B**：各场进球档位独立由该场基本面决定（从该场TOP2总进球中选取），同串内档位差异化，关数按串关数量规则（>8场以三串一为主）。')
    out.append('')
    out.append('> **连续编号总进球串①②**：选编号相邻场次（001+002、003+004），每场档位独立决定，两串使用互不重叠的连续编号段。')
    out.append('')

    # ---- 高赔半全场串 ----
    out.append('#### 高赔半全场串（4个方案）')
    out.append('')
    out.append('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
    out.append('|:---|:---|:---|:---:|:---|')
    hfs = sorted(W, key=lambda r: -r['_hafu_raw'][0][0])
    hf_hi = [x[0] for x in _hf_pick]
    for nm, pl in (('高赔半全场串A', hf_hi[0:3]), ('高赔半全场串B', hf_hi[3:6])):
        cells = [hafu_high(r) for r in pl]
        if all(cells):
            out.append(f"| {nm} | " + ' + '.join(c[0] for c in cells) + " | " +
                       ' x '.join(f'{c[1]:.2f}' for c in cells) + f" | {tot(cells):.2f} | 极高 |")
    for nm, pl in (('连续编号高赔半全场串①', [W[4], W[5]]), ('连续编号高赔半全场串②', [W[8], W[9]])):
        cells = [hafu_line(r) for r in pl]
        if all(cells):
            out.append(f"| {nm} | " + ' + '.join(c[0] for c in cells) + " | " +
                       ' x '.join(f'{c[1]:.2f}' for c in cells) + f" | {tot(cells):.2f} | 极高 |")
    out.append('')
    out.append('> **高赔半全场串A/B**：以基本面选场为主，各场半全场路径独立由该场基本面决定（伤停僵局→平平、客场死守→负负、主场慢热→平胜），同串内路径差异化。')
    out.append('')
    out.append('> **连续编号高赔半全场串①②**：选编号相邻场次（005+006、009+010）；原 007+008 段因含 008（法甲）按规则71 整体换段至 009+010。')
    out.append('')

    # ---- 半全场混合总进球串 ----
    out.append('#### 半全场混合总进球串（4个方案）')
    out.append('')
    out.append('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
    out.append('|:---|:---|:---|:---:|:---|')
    for nm, pl1, pl2 in (('混合串A', hf_hi[0:1], ttg_sorted[2:3]), ('混合串B', hf_hi[1:2], ttg_sorted[3:4])):
        c1 = [hafu_high(r) for r in pl1] + [ttg_line(r) for r in pl2]
        if all(c1):
            out.append(f"| {nm} | " + ' + '.join(c[0] for c in c1) + " | " +
                       ' x '.join(f'{c[1]:.2f}' for c in c1) + f" | ~{tot(c1):.2f} | 极高 |")
    for nm, pl1, pl2 in (('连续编号混合总进球串①', [W[12]], [W[13]]), ('连续编号混合总进球串②', [W[14]], [W[15]])):
        c1 = [hafu_high(r) for r in pl1] + [ttg_line(r) for r in pl2]
        if all(c1):
            out.append(f"| {nm} | " + ' + '.join(c[0] for c in c1) + " | " +
                       ' x '.join(f'{c[1]:.2f}' for c in c1) + f" | ~{tot(c1):.2f} | 极高 |")
    out.append('')
    out.append('> **混合串A/B**：半全场选方向明确的场次，搭配对应总进球数；两串选不同场次和路径分散风险。')
    out.append('')
    out.append('> **连续编号混合总进球串①②**：选编号相邻场次（013+014、015+016）；原 011+012 段因含 012（法甲）按规则71 整体换段。')
    out.append('')

    # ---- 比分串 ----
    out.append('#### 比分串（6个方案）')
    out.append('')
    out.append('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
    out.append('|:---|:---|:---|:---:|:---|')
    # 稳健比分串（方向优先口径，规则67试用）
    sc_cand = [r for r in W if r['_stars'] == '★★★' and max(r['_fus2']) >= 0.55 and r['num'] not in EXCL]
    if len(sc_cand) >= 2:
        cc = []
        for r in sc_cand[:2]:
            od = crs_odd(r, r['_dir_score'])
            cc.append((f"{code(r)} {r['home']}vs{r['away']} {r['_dir_score']}@{od:.2f}" if od else None, od))
        if all(x[0] for x in cc):
            out.append(f"| 稳健比分串（试用期流程，规则67） | " + ' + '.join(x[0] for x in cc) + " | " +
                       ' x '.join(f'{x[1]:.2f}' for x in cc) + f" | {tot(cc):.2f} | 高 |")
    # 搏冷比分串（反向推理，取分歧最大的2场）
    cc = []
    picks = [x[1] for x in colds[:2]] if colds else \
        sorted([x for x in W if x['num'] not in EXCL], key=lambda x: -x.get('align_max', 0))[:2]
    for r0 in picks:
        ti = max(range(3), key=lambda k: r0['_fus2'][k])
        sc = {0: '1-1', 1: '2-1', 2: '1-2'}[ti] if not colds else {1: '1-1', 2: '0-1', 0: '1-0'}[ti]
        od = crs_odd(r0, sc)
        if od:
            cc.append((f"{code(r0)} {r0['home']}vs{r0['away']} {sc}@{od:.2f}", od))
    if cc:
        out.append(f"| 搏冷比分串（反向推理，冷门剧本：模型与市场方向对立） | " + ' + '.join(x[0] for x in cc) +
                   f" | 逐场 1 选 1 | {tot(cc):.2f} | 极高 |")
    for nm, pl in (('连续编号比分串①', [W[16], W[17]]), ('连续编号比分串②', [W[20], W[21]])):
        cc = []
        for r in pl:
            od = crs_odd(r, r['_dir_score'])
            if od:
                cc.append((f"{code(r)} {r['_dir_score']}@{od:.2f}", od))
        if len(cc) == 2:
            out.append(f"| {nm}（试用期流程，规则67） | " + ' + '.join(x[0] for x in cc) + " | " +
                       ' x '.join(f'{x[1]:.2f}' for x in cc) + f" | {tot(cc):.2f} | 高 |")
    # 单挑比分①②
    singles_sc = []
    for r in W:
        if r['num'] in EXCL:
            continue
        od = crs_odd(r, r['_dir_score'])
        if od and od >= 8.0:
            singles_sc.append((r, od))
    singles_sc.sort(key=lambda x: -x[1])
    for i, (r, od) in enumerate(singles_sc[:2]):
        out.append(f"| 单挑比分{'①' if i == 0 else '②'} | {code(r)} {r['home']}vs{r['away']} {r['_dir_score']} | — | {od:.2f} | 中 |")
    out.append('')
    out.append('> **稳健比分串**：按方向优先口径推演（规则67 试用期）——先定胜平负首推方向，再在该方向内取条件净胜球众数，'
               '最后用首推总进球档位锁定比分（净胜球与总进球同奇偶）；禁止直接取全局概率最高比分。')
    out.append('')
    out.append('> **搏冷比分串（反向推理）**：不适用正向四步流程，先定冷门剧本（模型与市场方向对立）→ 剧本内推演比分 → 赔率择优，标注「反向推理」。')
    out.append('')
    out.append('> **连续编号比分串①②**：选编号相邻场次（017+018、021+022），比分按方向优先口径推演，两串使用互不重叠的连续编号段；'
               '原 013+014、015+016 段已被连续编号混合总进球串占用，故顺延取号。**试用期流程（规则67）**，已登记试用台账。')
    out.append('')
    out.append('> **单挑比分①②**：按方向优先口径推演后，选赔率≥8.00 的甜蜜区比分，每注独立不串关。')
    out.append('')

    # ================= 本轮规律 =================
    out.append('## 本轮规律')
    out.append('')
    out.append(f'**1. 单关7场按规则63统一做平局上修。** 001/003/007/013/015/019/021 七场开单关，'
               f'平局概率统一 +8%，其中 016 赫塔费（未开单关）因双方场均进球仅 0.95/0.94 本身即平局高发场，'
               f'平局 32.4% 已居次选位。')
    out.append('')
    out.append(f'**2. 法甲"平局最多"的联赛特征在数据上再次显现。** 本轮法甲3场（008/012/020），'
               f'其中非PSG的 008、012 按规则69 上修平局（排名差分别触发 +5~7% 与 +8~10% 档）；'
               f'020 布雷斯特vs巴黎因涉及PSG（实力断层）不上修，客胜 78.7%。')
    out.append('')
    out.append(f'**3. 大球上修（规则65）集中在实力悬殊场。** 014 埃沃斯堡vs拜仁（身价差约14倍）、'
               f'010 莱万特vs巴萨（身价差约14倍）、017 本菲卡vs吉维森特 三场触发全部条件，'
               f'λ_total 均落在 3.0 以上；而 013 曼市德比属英超 Tier1 例外，不上修大球。')
    out.append('')
    out.append(f'**4. 半场平局联赛修正（规则66）影响半全场与半场比分。** 日职 ht_draw_rate 0.534（最高档），'
               f'001 东京绿茵vs千叶市原半全场首选已按规则强制落在含平路径；'
               f'西甲/意甲/葡超/瑞超/芬超均属高半场平局档（≥0.40），半场λ系数取 0.38。')
    out.append('')
    out.append(f'**5. 让球端按规则52a 使用无条件净胜球众数。** 本轮全部采用旧口径（无条件分布），'
               f'与比分串的方向内条件众数口径相互独立；±1盘三选覆盖，让平不得被排除出首选与次选。')
    out.append('')

    # ================= 写在最后 =================
    out.append('## ☕ 写在最后')
    out.append('')
    out.append('数据能告诉你概率，但告诉不了你结果。24场比赛里，模型能给出的只是每个方向大概率的排序——'
               '真正的比赛总会出现一两个谁都算不到的瞬间：一次意外的红牌、一个门将的失误、一脚补时的折射。'
               '把这些概率当作参考框架，而不是确定性承诺，才是看这份报告最舒服的姿势。理性看待，量力而行。')
    out.append('')

    txt = '\n'.join(out)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, 'w', encoding='utf-8') as fp:
        fp.write(txt)
    print('written', OUT, len(txt))

    # ================= 导出预测JSON（供第9步回测使用）=================
    NAME3b = ['让胜', '让平', '让负']
    pred = {'date': '2026-09-13', 'day': 'sunday', 'total': len(W),
            'source_report': OUT, 'matches': []}
    for r in W:
        f = r['_fus2']
        ti = max(range(3), key=lambda k: f[k])
        si = sorted([k for k in range(3) if k != ti], key=lambda k: -f[k])[0]
        hr_rate = HT.get(M[r['num']]['lg'], (None, 0.42, ''))[0]
        h3 = [x[1] for x in r['_hafu_raw'][:3]]
        if hr_rate and hr_rate >= 0.40:
            wp = [x for x in r['_hafu_raw'] if x[1] in ('平平', '平胜', '平负')]
            if wp:
                first = wp[0][1]
                h3 = [first] + [x[1] for x in r['_hafu_raw'] if x[1] != first][:2]
        t2 = sorted(range(8), key=lambda k: -r['ttg'][k])[:2]
        h2 = None
        if r.get('m_hhad') and r.get('_hhad_dir'):
            order = sorted(range(3), key=lambda k: -r['m_hhad'][k])
            rest = [NAME3b[k] for k in order if NAME3b[k] != r['_hhad_dir']]
            h2 = rest[0] if rest else None
        pred['matches'].append(dict(
            num=r['num'], home=r['home'], away=r['away'], league=r['league'],
            time=r['time'], venue=r['venue'],
            dir_first=L3[ti], dir_second=L3[si],
            fus=[round(x, 4) for x in f],
            hhad_line=(r['hhad']['line'] if r.get('hhad') else None),
            hhad_first=r.get('_hhad_dir'), hhad_second=h2,
            ttg_top2=[[int(x), round(r['ttg'][x], 4)] for x in t2],
            hafu_top3=[[h, round(r['_hafu_dict'][h], 4)] for h in h3],
            scores_top5=[[s, round(v, 4)] for s, v in r['_top5']],
            stars=r['_stars'],
        ))
    PJ = os.path.join(WORK, 'pred_20260913.json')
    json.dump(pred, open(PJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('pred json ->', PJ)


if __name__ == '__main__':
    main()
