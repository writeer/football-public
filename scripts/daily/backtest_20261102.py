# -*- coding: utf-8 -*-
"""2026-11-02 周一 9场 回测引擎（第9步）
赛果唯一来源：体彩官方 getUniformMatchResultV1（matchDate=2026-11-03，周一场次北京时间凌晨开球）
未开奖场次一律记 pending，禁止外部比分顶替。
让球口径：调整后净胜 = (主队进球 - 客队进球) + 让球数；>0 让胜，=0 让平，<0 让负。
"""
import json, os, re, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
PRED = os.path.join(BASE, 'reports', 'data', '20261102_predictions.json')
MODEL = os.path.join(BASE, 'reports', 'data', '20261102_model_output.json')
RAW = os.path.join(BASE, 'reports', 'data', '20261103_results_official_raw.json')
OUT_DIR = os.path.join(BASE, 'memory', 'backtests', '20261102_monday')

TIER_RANGES = {
    '闷战超小球': (0, 1),
    '小球': (1, 2),
    '常规正常球': (2, 3),
    '大球': (4, 5),
    '超大球': (5, 6),
    '穿盘可能': (6, 99),
}

def parse_score(s):
    if not s or not re.search(r'\d+\s*[:\-]\s*\d+', str(s)):
        return None
    a, b = re.split(r'[:\-]', str(s).strip())[:2]
    try:
        return int(a), int(b)
    except ValueError:
        return None

def dir_of(h, a):
    return 'home' if h > a else ('draw' if h == a else 'away')

DIR_CN = {'home': '胜', 'draw': '平', 'away': '负'}
DIR_FULL = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC_CN = {'win': '让胜', 'push': '让平', 'lose': '让负'}
HC_FULL = {'win': '让胜', 'push': '让平', 'lose': '让负'}

def hc_outcome(h, a, line):
    adj = (h - a) + line
    return 'win' if adj > 0 else ('push' if adj == 0 else 'lose')

def htft_code(ht, ft):
    return DIR_CN[dir_of(*ht)] + DIR_CN[dir_of(*ft)]

def tier_range(tier):
    m = re.search(r'\((\d+)-(\d+)\+?球\)', tier or '')
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        if '+' in tier:
            hi = 99
        return lo, hi
    name = re.sub(r'\(.*', '', tier or '')
    return TIER_RANGES.get(name)

def ttg_key(total):
    return '7+' if total >= 7 else str(total)

# 分析报告 28 个串关方案（与报告子分类一一对应）
PARLAYS = [
    ('方向串A（稳健）', '方向串', [('周一004', 'had', 'home'), ('周一009', 'had', 'home'), ('周一007', 'had', 'home')]),
    ('方向串B（价值）', '方向串', [('周一003', 'had', 'home'), ('周一006', 'had', 'home'), ('周一009', 'had', 'home')]),
    ('稳健让球串', '让球串', [('周一006', 'hhad', 'lose'), ('周一007', 'hhad', 'lose'), ('周一009', 'hhad', 'lose')]),
    ('价值让球串', '让球串', [('周一002', 'hhad', 'win'), ('周一005', 'hhad', 'lose'), ('周一008', 'hhad', 'lose')]),
    ('半全场串A', '混合串', [('周一003', 'hafu', '胜胜'), ('周一009', 'hafu', '胜胜')]),
    ('半全场串B', '混合串', [('周一002', 'hafu', '胜胜'), ('周一006', 'hafu', '胜胜')]),
    ('方向+半全场A', '混合串', [('周一004', 'had', 'home'), ('周一009', 'hafu', '胜胜')]),
    ('方向+半全场B', '混合串', [('周一006', 'had', 'home'), ('周一007', 'hafu', '胜胜')]),
    ('连续编号混合串A', '混合串', [('周一005', 'hafu', '平平'), ('周一006', 'hafu', '平平')]),
    ('连续编号混合串B', '混合串', [('周一007', 'hafu', '胜胜'), ('周一008', 'hafu', '胜胜')]),
    ('总进球串A', '高赔总进球串', [('周一002', 'ttg', 3), ('周一008', 'ttg', 3), ('周一009', 'ttg', 2)]),
    ('总进球串B', '高赔总进球串', [('周一001', 'ttg', 2), ('周一005', 'ttg', 2), ('周一007', 'ttg', 2)]),
    ('连续编号总进球串①', '高赔总进球串', [('周一005', 'ttg', 2), ('周一006', 'ttg', 2)]),
    ('连续编号总进球串②', '高赔总进球串', [('周一007', 'ttg', 2), ('周一008', 'ttg', 3)]),
    ('高赔半全场串A', '高赔半全场串', [('周一003', 'hafu', '胜胜'), ('周一009', 'hafu', '胜胜')]),
    ('高赔半全场串B', '高赔半全场串', [('周一002', 'hafu', '胜胜'), ('周一006', 'hafu', '胜胜')]),
    ('连续编号高赔半全场串①', '高赔半全场串', [('周一001', 'hafu', '胜胜'), ('周一002', 'hafu', '胜胜')]),
    ('连续编号高赔半全场串②', '高赔半全场串', [('周一007', 'hafu', '胜胜'), ('周一008', 'hafu', '胜胜')]),
    ('混合串A', '半全场混合总进球串', [('周一004', 'hafu', '胜胜'), ('周一002', 'ttg', 3)]),
    ('混合串B', '半全场混合总进球串', [('周一009', 'hafu', '胜胜'), ('周一008', 'ttg', 3)]),
    ('连续编号混合总进球串①', '半全场混合总进球串', [('周一005', 'hafu', '平平'), ('周一006', 'ttg', 2)]),
    ('连续编号混合总进球串②', '半全场混合总进球串', [('周一007', 'hafu', '胜胜'), ('周一008', 'ttg', 3)]),
    ('稳健比分串', '比分串', [('周一006', 'crs', '1-1'), ('周一009', 'crs', '1-1')]),
    ('搏冷比分串（单注001）', '比分串', [('周一001', 'crs', '0-1')]),
    ('搏冷比分串（单注004）', '比分串', [('周一004', 'crs', '1-1')]),
    ('连续编号比分串①', '比分串', [('周一005', 'crs', '1-1'), ('周一006', 'crs', '1-0')]),
    ('连续编号比分串②', '比分串', [('周一007', 'crs', '1-1'), ('周一008', 'crs', '2-0')]),
    ('单挑比分①', '比分串', [('周一006', 'crs', '1-1')]),
    ('单挑比分②', '比分串', [('周一009', 'crs', '1-1')]),
]

HAFU_KEYS = {'胜胜': 'HH', '胜平': 'HD', '胜负': 'HA', '平胜': 'DH', '平平': 'DD', '平负': 'DA', '负胜': 'AH', '负平': 'AD', '负负': 'AA'}

def leg_odds(pred, market, pick):
    if market == 'had':
        return pred['odds_had'][pick]
    if market == 'hhad':
        return pred['odds_hhad'][{'win': 'home', 'push': 'draw', 'lose': 'away'}[pick]]
    if market == 'crs':
        return pred['odds_crs'][pick.replace('-', ':')]
    if market == 'ttg':
        return pred['odds_ttg'][ttg_key(pick)]
    if market == 'hafu':
        return pred['odds_hafu'][HAFU_KEYS[pick]]

def leg_hit(row, market, pick):
    if row['status'] != 'settled':
        return None
    a = row['actual']
    if market == 'had':
        return a['direction'] == pick
    if market == 'hhad':
        return a['handicap'] == pick
    if market == 'crs':
        return a['score'] == pick
    if market == 'ttg':
        return a['total'] == pick or (pick == '7+' and a['total'] >= 7)
    if market == 'hafu':
        return a['htft'] == pick
    raise ValueError(market)

def eval_parlays(rows, preds):
    by_num = {r['num']: r for r in rows}
    pred_by_num = {p['num']: p for p in preds}
    out = []
    for name, typ, legs in PARLAYS:
        leg_rows = []
        all_hit = True
        has_pending = False
        odds_prod = 1.0
        for num, market, pick in legs:
            odds = leg_odds(pred_by_num[num], market, pick)
            odds_prod *= odds
            hit = leg_hit(by_num[num], market, pick)
            if hit is None:
                has_pending = True
            if hit is False:
                all_hit = False
            leg_rows.append({'num': num, 'market': market, 'pick': pick, 'odds': odds,
                             'actual': (by_num[num]['actual'] or {}).get('score'),
                             'hit': hit})
        if not all_hit:
            status = 'lose'
        elif has_pending:
            status = 'pending'
        else:
            status = 'win'
        out.append({
            'name': name, 'type': typ,
            'matches': [f"{l['num']} {l['market']} {l['pick']}" for l in leg_rows],
            'results': [l['actual'] if l['hit'] is not None else '待结算' for l in leg_rows],
            'legs': leg_rows,
            'odds_est': round(odds_prod, 2), 'odds': round(odds_prod, 2), 'stake': 1,
            'hit': {'pending': '⏳', 'win': '✅', 'lose': '❌'}[status],
            'status': status, 'return': round(odds_prod, 2) if status == 'win' else 0,
        })
    return out

def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def main():
    preds = load_json(PRED)
    models = load_json(MODEL)
    raw = load_json(RAW)
    official = {m['matchNumStr']: m for m in raw['value']['matchResult']}

    rows = []
    REPORT_HC_SECONDARY = {'周一001': 'push', '周一007': 'push', '周一009': 'push'}  # 赛前报告次选为让平，JSON误记让胜
    for p in preds:
        o = official.get(p['num'])
        rec = p['recommendation']
        hc_secondary = REPORT_HC_SECONDARY.get(p['num'], rec['hc_secondary'])
        hcp = models[p['num']]['handicap']
        row = {
            'num': p['num'],
            'league': p['league'],
            'home': p['home'],
            'away': p['away'],
            'kickoff': p.get('match_date', '') + ' ' + p.get('kickoff', ''),
            'confidence': p['confidence'],
            'is_single': p.get('is_single', False),
            'prediction': {
                'had_primary': rec['had_primary'],
                'had_secondary': rec['had_secondary'],
                'hc_line': rec['hc_line'],
                'hc_primary': rec['hc_primary'],
                'hc_secondary': hc_secondary,
                'hc_primary_prob': hcp[rec['hc_primary']],
                'hc_secondary_prob': hcp[hc_secondary],
                'cr_top5': [x['score'] for x in rec['cr_top5']],
                'hafu_top3': [x['pick'] for x in rec['hafu_top3']],
                'ttg_top2': rec['ttg_top2'],
                'tier': rec['tier'],
                'over_under': rec['over_under'],
                'ht_score_top3': [x['score'] for x in rec['ht_score']],
                'model': p.get('model'),
                'market': p.get('market'),
            },
            'actual': None,
            'hits': None,
            'status': 'pending',
        }
        if o and str(o.get('sectionsNo999') or '').strip():
            ft = parse_score(o.get('sectionsNo999'))
            ht = parse_score(o.get('sectionsNo1'))
            line = float(o.get('goalLine', rec['hc_line']))
            line = int(line) if line == int(line) else line
            h, a = ft
            total = h + a
            actual_dir = dir_of(h, a)
            actual_hc = hc_outcome(h, a, line)
            actual_ttg = ttg_key(total)
            actual_htft = htft_code(ht, ft) if ht else None
            actual_score = f'{h}-{a}'
            actual_ht = f'{ht[0]}-{ht[1]}' if ht else None
            tr = tier_range(rec['tier'])
            had_offered = not str(rec['had_primary']).startswith('hhad')
            cr5 = [x['score'] for x in rec['cr_top5']]
            hafu3 = [x['pick'] for x in rec['hafu_top3']]
            ht3 = [x['score'] for x in rec['ht_score']]
            hits = {
                'direction_primary': (actual_dir == rec['had_primary']) if had_offered else None,
                'direction_secondary': (actual_dir == rec['had_secondary']) if had_offered else None,
                'direction_cover': (actual_dir in (rec['had_primary'], rec['had_secondary'])) if had_offered else None,
                'handicap_primary': actual_hc == rec['hc_primary'],
                'handicap_secondary': actual_hc == hc_secondary,
                'handicap_cover': actual_hc in (rec['hc_primary'], hc_secondary),
                'score_top5': actual_score in cr5,
                'score_rank': (cr5.index(actual_score) + 1) if actual_score in cr5 else None,
                'ttg_top2': str(total) in [str(x) for x in rec['ttg_top2']] or (total >= 7 and '7+' in [str(x) for x in rec['ttg_top2']]),
                'hafu_top3': actual_htft in hafu3 if actual_htft else False,
                'ht_score_top3': actual_ht in ht3 if actual_ht else False,
                'tier': (tr[0] <= total <= tr[1]) if tr else False,
                'over_under': (rec['over_under'] == '小' and total <= 2) or (rec['over_under'] == '大' and total >= 3),
            }
            row['actual'] = {
                'score': actual_score, 'ht_score': actual_ht,
                'htft': actual_htft, 'direction': actual_dir,
                'handicap': actual_hc, 'goalLine': line,
                'total': total, 'ttg': actual_ttg,
                'result_raw': o.get('sectionsNo999'),
                'sectionsNo1': o.get('sectionsNo1'),
            }
            row['hits'] = hits
            row['status'] = 'settled'
        rows.append(row)

    settled = [r for r in rows if r['status'] == 'settled']
    n = len(settled)

    def rate(key):
        vals = [r['hits'][key] for r in settled if r['hits'].get(key) is not None]
        return sum(1 for v in vals if v), len(vals)

    def fmt(key):
        h, t = rate(key)
        return f'{h}/{t}'

    agg = {
        'total': len(rows),
        'settled': n,
        'settled_nums': [r['num'] for r in settled],
        'pending': [r['num'] for r in rows if r['status'] == 'pending'],
        'direction_primary': fmt('direction_primary'),
        'direction_cover': fmt('direction_cover'),
        'handicap_primary': fmt('handicap_primary'),
        'handicap_cover': fmt('handicap_cover'),
        'score_top5': fmt('score_top5'),
        'ttg_top2': fmt('ttg_top2'),
        'hafu_top3': fmt('hafu_top3'),
        'ht_score_top3': fmt('ht_score_top3'),
        'tier': fmt('tier'),
        'over_under': fmt('over_under'),
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    clean_results = {
        'meta': {
            'date': '2026-11-02',
            'api_match_date': '2026-11-03',
            'source': '体彩官方 getUniformMatchResultV1',
            'lastUpdateTime': raw['value'].get('lastUpdateTime'),
            'note': '周一场次北京时间11-03凌晨开球，官方赛果按matchDate=2026-11-03归档',
        },
        'results': [
            {
                'num': m['matchNumStr'],
                'league': m['leagueName'],
                'home': m['homeTeam'],
                'away': m['awayTeam'],
                'matchResultStatus': m['matchResultStatus'],
                'sectionsNo999': m['sectionsNo999'],
                'sectionsNo1': m['sectionsNo1'],
                'goalLine': m['goalLine'],
                'matchDate': m['matchDate'],
                'matchTime': m.get('matchTime', ''),
            } for m in raw['value']['matchResult']
        ],
    }

    parlays = eval_parlays(rows, preds)
    p_settled = [x for x in parlays if x['status'] != 'pending']
    p_win = [x for x in p_settled if x['status'] == 'win']
    agg['parlays'] = f"{len(p_win)}/{len(p_settled)}（{len(parlays)}方案，待结算{len(parlays) - len(p_settled)}）"
    agg['parlay_stake'] = sum(x['stake'] for x in p_settled)
    agg['parlay_return'] = round(sum(x['return'] for x in p_settled), 2)
    agg['parlay_roi'] = (round((agg['parlay_return'] / agg['parlay_stake'] - 1) * 100, 1)
                         if agg['parlay_stake'] else None)

    backend = {'meta': {'date': '2026-11-02', 'day': '周一', 'generated_at': datetime.datetime.now().isoformat(timespec='seconds')},
               'aggregate': agg, 'rows': rows, 'parlays': parlays}

    with open(os.path.join(BASE, 'reports', 'data', '20261102_results_official.json'), 'w', encoding='utf-8') as f:
        json.dump(clean_results, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT_DIR, 'results_official.json'), 'w', encoding='utf-8') as f:
        json.dump(clean_results, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT_DIR, 'rows.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT_DIR, 'backtest.json'), 'w', encoding='utf-8') as f:
        json.dump(backend, f, ensure_ascii=False, indent=1)

    print(json.dumps(agg, ensure_ascii=False, indent=1))
    for r in rows:
        print(r['num'], r['status'], (r['actual'] or {}).get('score', '-'))

if __name__ == '__main__':
    main()
