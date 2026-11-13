# -*- coding: utf-8 -*-
"""串关选场辅助：打印每场赔率/概率/让球/总进球/半全场，便于人工组串"""
import json, io

ms = json.load(io.open('reports/data/20261101_model_output.json', encoding='utf-8'))
CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
for r in ms:
    had = r.get('odds_had') or {}
    mkt = r.get('market') or {}
    print('{} {} vs {} [{}]{}'.format(r['num'], r['home'], r['away'], r['league'],
                                      ' 单关' if r['is_single'] else ''))
    print('   模型 {} {:.1f} | {} {:.1f} | {} {:.1f}   市场 {} {:.1f} | {} {:.1f} | {} {:.1f}'.format(
        CN[r['primary']], r['primary_prob'] * 100, CN[r['secondary']], r['secondary_prob'] * 100,
        CN[r['third']], r['third_prob'] * 100,
        '主', mkt['home'] * 100, '平', mkt['draw'] * 100, '客', mkt['away'] * 100))
    print('   HAD赔率 H{} D{} A{}  | 让{} H{} D{} A{}'.format(
        had.get('home'), had.get('draw'), had.get('away'), r['hhad_line'],
        (r.get('odds_hhad') or {}).get('home'), (r.get('odds_hhad') or {}).get('draw'),
        (r.get('odds_hhad') or {}).get('away')))
    print('   让球模型 H{:.1f} D{:.1f} A{:.1f} → {} / {}'.format(
        (r['hhad_model'] or {}).get('home', 0) * 100, (r['hhad_model'] or {}).get('draw', 0) * 100,
        (r['hhad_model'] or {}).get('away', 0) * 100, CN.get(r['hc_first'], ''), CN.get(r['hc_second'], '')))
    print('   总进球TOP2 {} 赔率 {}  |  半全场TOP3 {} 赔率 {}'.format(
        r['ttg_top2'], {k: r['odds_ttg'].get(k) for k in [str(x) for x in r['ttg_top2']]},
        [k for k, _ in r['htft_top3']],
        {k: r['odds_hafu'].get({'胜胜': 'HH', '胜平': 'HD', '胜负': 'HA', '平胜': 'DH',
                                '平平': 'DD', '平负': 'DA', '负胜': 'AH', '负平': 'AD',
                                '负负': 'AA'}.get(k, k)) for k, _ in r['htft_top3']}))
    print('   比分TOP5 {} 赔率 {}'.format(
        ['%d-%d' % (a, b) for a, b, _ in r['top_scores']],
        {'%d-%d' % (a, b): r['odds_crs'].get('S%d:S%d' % (a, b), r['odds_crs'].get('%d:%d' % (a, b)))
         for a, b, _ in r['top_scores']}))
