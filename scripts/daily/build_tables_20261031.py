# -*- coding: utf-8 -*-
"""2026-10-31 联赛积分榜刷新（Transfermarkt 26/27 / bundesliga.com，截至10-31）
覆盖：日职J1(12轮)、日乙J2(12-13轮)、意甲(8-9轮)、荷甲(10轮)、德甲补门兴。
其余联赛沿用已有当季积分榜（英超7轮、英冠12轮、西甲10轮、韩职31轮、澳超2轮、挪超24轮）。
"""
import json, os

SRC_J1 = [
    (1, 'Machida', 12, 8, 3, 1, 30, 10, 27), (2, 'FC Tokyo', 12, 8, 3, 1, 27, 8, 27),
    (3, 'Sanfrecce Hiroshima', 12, 8, 2, 2, 29, 10, 26), (4, 'Kashiwa Reysol', 12, 8, 1, 3, 25, 19, 25),
    (5, 'Vissel Kobe', 12, 7, 2, 3, 18, 11, 23), (6, 'Kawasaki Frontale', 12, 6, 4, 2, 25, 18, 22),
    (7, 'Urawa Reds', 12, 7, 0, 5, 21, 23, 21), (8, 'Kashima Antlers', 12, 6, 2, 4, 25, 21, 20),
    (9, 'Yokohama F. Marinos', 12, 4, 6, 2, 16, 12, 18), (10, 'Okayama', 12, 5, 1, 6, 15, 17, 16),
    (11, 'Nagoya Grampus', 12, 4, 2, 6, 14, 18, 14), (12, 'Cerezo Osaka', 12, 3, 5, 4, 12, 19, 14),
    (13, 'Shimizu S-Pulse', 12, 4, 2, 6, 10, 20, 14), (14, 'V-Varen Nagasaki', 12, 3, 3, 6, 15, 19, 12),
    (15, 'Gamba Osaka', 12, 2, 5, 5, 14, 21, 11), (16, 'Kyoto', 12, 2, 4, 6, 15, 23, 10),
    (17, 'Mito', 12, 2, 3, 7, 12, 22, 9), (18, 'Verdy', 12, 1, 5, 6, 9, 21, 8),
    (19, 'Avispa Fukuoka', 12, 2, 1, 9, 13, 21, 7), (20, 'Chiba', 12, 1, 4, 7, 12, 24, 7),
]

SRC_J2 = [
    (1, 'Vegalta Sendai', 12, 8, 3, 1, 21, 9, 27), (2, 'Albirex Niigata', 12, 7, 2, 3, 17, 20, 23),
    (3, 'Toyama', 12, 6, 4, 2, 23, 11, 22), (4, 'Yokohama FC', 13, 6, 4, 3, 25, 16, 22),
    (5, 'Omiya Ardija', 13, 5, 6, 2, 23, 16, 21), (6, 'Shonan Bellmare', 12, 4, 7, 1, 13, 11, 19),
    (7, 'Oita Trinita', 12, 4, 6, 2, 16, 9, 18), (8, 'Miyazaki', 12, 4, 5, 3, 17, 16, 17),
    (9, 'Tokushima', 13, 5, 2, 6, 11, 13, 17), (10, 'Iwaki', 12, 5, 1, 6, 19, 18, 16),
    (11, 'Fujieda MYFC', 13, 3, 6, 4, 15, 14, 15), (12, 'Iwata', 12, 4, 3, 5, 13, 14, 15),
    (13, 'Sagan Tosu', 12, 4, 2, 6, 12, 15, 14), (14, 'Hokkaido Consadole Sapporo', 12, 4, 2, 6, 15, 19, 14),
    (15, 'Hachinohe', 12, 4, 2, 6, 10, 20, 14), (16, 'Montedio Yamagata', 12, 4, 1, 7, 11, 11, 13),
    (17, 'Blaublitz', 12, 3, 4, 5, 13, 14, 13), (18, 'Tochigi City', 12, 3, 3, 6, 19, 20, 12),
    (19, 'Imabari', 12, 3, 2, 7, 15, 25, 11), (20, 'Kofu', 12, 3, 1, 8, 9, 26, 10),
]

SRC_ITA = [
    (1, 'Lazio', 9, 8, 1, 0, 22, 7, 25), (2, 'Inter', 8, 7, 1, 0, 23, 10, 22),
    (3, 'AS Roma', 9, 6, 3, 0, 23, 8, 21), (4, 'Como', 9, 6, 2, 1, 17, 8, 20),
    (5, 'AC Milan', 8, 5, 3, 0, 16, 7, 18), (6, 'Frosinone', 8, 4, 2, 2, 17, 13, 14),
    (7, 'Juventus', 8, 4, 2, 2, 11, 8, 14), (8, 'Torino', 9, 4, 1, 4, 14, 14, 13),
    (9, 'Cagliari', 9, 4, 1, 4, 8, 13, 13), (10, 'Napoli', 8, 3, 2, 3, 13, 10, 11),
    (11, 'Atalanta', 8, 3, 1, 4, 14, 15, 10), (12, 'Lecce', 8, 3, 0, 5, 9, 14, 9),
    (13, 'Bologna', 8, 2, 2, 4, 8, 10, 8), (14, 'Sassuolo', 9, 2, 2, 5, 14, 22, 8),
    (15, 'Monza', 8, 2, 1, 5, 15, 18, 7), (16, 'Genoa', 8, 2, 1, 5, 6, 13, 7),
    (17, 'Udinese', 8, 1, 1, 6, 9, 18, 4), (18, 'Fiorentina', 8, 1, 1, 6, 9, 19, 4),
    (19, 'Parma', 8, 1, 1, 6, 5, 15, 4), (20, 'Venezia', 8, 1, 0, 7, 6, 17, 3),
]

SRC_NED = [
    (1, 'Feyenoord', 10, 7, 3, 0, 32, 11, 24), (2, 'Ajax', 10, 6, 3, 1, 29, 13, 21),
    (3, 'PSV', 10, 6, 2, 2, 28, 13, 20), (4, 'Twente', 10, 6, 2, 2, 19, 10, 20),
    (5, 'AZ Alkmaar', 10, 6, 2, 2, 20, 12, 20), (6, 'Sittard', 10, 5, 3, 2, 17, 17, 18),
    (7, 'Heerenveen', 10, 4, 3, 3, 18, 13, 15), (8, 'Groningen', 10, 4, 3, 3, 24, 21, 15),
    (9, 'G.A. Eagles', 10, 3, 5, 2, 23, 23, 14), (10, 'Cambuur', 10, 3, 3, 4, 19, 22, 12),
    (11, 'Utrecht', 10, 3, 3, 4, 17, 27, 12), (12, 'Nijmegen', 10, 2, 5, 3, 17, 18, 11),
    (13, 'Excelsior', 10, 3, 2, 5, 16, 19, 11), (14, 'Sparta Rotterdam', 10, 2, 3, 5, 17, 24, 9),
    (15, 'Zwolle', 10, 2, 2, 6, 11, 23, 8), (16, 'Telstar', 10, 1, 3, 6, 12, 21, 6),
    (17, 'Den Haag', 10, 1, 3, 6, 13, 23, 6), (18, 'Willem II', 10, 0, 2, 8, 10, 32, 2),
]


def rows_from(src):
    out = []
    for pos, team, p, w, d, l, gf, ga, pts in src:
        out.append({
            'team': team, 'position': pos, 'played': p, 'won': w, 'drawn': d, 'lost': l,
            'goals_for': gf, 'goals_against': ga,
            'avg_goals_scored': round(gf / p, 3), 'avg_goals_conceded': round(ga / p, 3),
            'points': pts, 'last_5_form': None, 'last_5_points': None,
        })
    return out


def save(fn, league, rows, season='2026-2027'):
    json.dump({'league': league, 'season': season, 'table': rows},
              open(os.path.join('reports/data', fn), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(fn, len(rows))


save('table_japan1.json', '日职', rows_from(SRC_J1))
save('table_japan2.json', '日乙', rows_from(SRC_J2))
save('table_italy1.json', '意甲', rows_from(SRC_ITA))
save('table_holland1.json', '荷甲', rows_from(SRC_NED))

# 德甲：补门兴（bundesliga.com 10-31：7轮 1胜0平6负 11:22 3分）
p = 'reports/data/table_germany1.json'
d = json.load(open(p, encoding='utf-8-sig'))
names = {r['team'] for r in d['table']}
if 'Monchengladbach' not in names:
    d['table'].append({
        'team': 'Monchengladbach', 'position': 18, 'played': 7, 'won': 1, 'drawn': 0, 'lost': 6,
        'goals_for': 11, 'goals_against': 22,
        'avg_goals_scored': round(11 / 7, 3), 'avg_goals_conceded': round(22 / 7, 3),
        'points': 3, 'last_5_form': None, 'last_5_points': None,
    })
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('table_germany1.json', len(d['table']))
