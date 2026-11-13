// 生成 2026-11-02 周一006 单场预测JSON（归档用）
const fs = require('fs');
const path = require('path');
const matches = JSON.parse(fs.readFileSync('reports/data/20261102_matches.json', 'utf8'));
const m = matches.find(x => x.num === '周一006');
const md = JSON.parse(fs.readFileSync('reports/data/20261102_006_model.json', 'utf8'));

const oddsObj = (arr) => Object.fromEntries(arr.map(o => [o.key, o.odds]));
const crs = oddsObj(m.crs).crs || oddsObj(m.crs);

const out = {
  num: m.num,
  league: '英超',
  home: m.home,
  away: m.away,
  kickoff: m.time,
  match_date: m.match_date,
  is_single: true,
  single_source: '用户告知（2026-11-02）',
  rule63: '平赔3.25>3.20，按L166不触发规则63平局上修；平局概率来自DC低比分修正+双方平局倾向',
  value_eur: { home: 712100000, away: 436800000, ratio: 1.63, source: 'Transfermarkt 26/27' },
  injuries: {
    home_count: 5,
    away_count: 2,
    detail: {
      home: [
        '利夫拉门托（左后卫/膝伤，09-19起，缺阵，Fotmob/球迷屋/利物浦回声报）',
        '雅旺（门将/腿筋，09-30起，缺阵，Fotmob/球迷屋/利物浦回声报）',
        '麦利（中场/肌肉，10-18起，出战成疑；回声报doubtful vs Fotmob unavailable矛盾）',
        '帕尔多（前锋/患病，10-18起，出战成疑；回声报hoped to return vs Fotmob unavailable矛盾）',
        '奥苏拉（前锋/踝伤，10-29起，出战成疑；回声报/ReadNewcastle vs Fotmob unavailable矛盾）'
      ],
      away: [
        '布兰斯韦特（中卫/脑震荡，缺2场，已确认复出，埃弗顿官网10-30）',
        '格拉利什（左边锋/纪律处罚非伤病，10-29起，出战成疑，DAZN/埃弗顿官网）'
      ]
    }
  },
  venue: {
    name: '圣詹姆斯公园球场', city: '纽卡斯尔', capacity: 52729, pitch: '天然草',
    status: '正常', status_note: '无空场/部分关闭公告，门票在售'
  },
  weather: { temp: '7~11℃', desc: '晴转阴', wind: '西南风3级、阵风19mph', impact: '无影响' },
  h2h: {
    summary: '近7次交手纽卡1胜2平4负、进8失12；埃弗顿近两次做客SJP全胜（2-3、0-1），23/24赛季1-1。',
    rhythm: '近5次交锋场均3.2球；最近两次SJP合计5球，低比分与对攻样本并存。',
    lam_shift: [-0.02, 0.02]
  },
  stadium: { factor: 1.10, override_applied: false, note: '正常开放，英超主场系数1.10（规则68）' },
  odds_had: oddsObj(m.had),
  odds_hhad: { ...oddsObj(m.hhad.outcomes), handicap: m.hhad.goalLine },
  odds_crs: oddsObj(m.crs),
  odds_ttg: oddsObj(m.ttg),
  odds_hafu: oddsObj(m.hafu),
  model: {
    home: +md.probs_final.home.toFixed(4),
    draw: +md.probs_final.draw.toFixed(4),
    away: +md.probs_final.away.toFixed(4),
    lambda_home: md.lambda.home,
    lambda_away: md.lambda.away,
    lambda_total: md.lambda.total,
    lambda_base: [1.35, 1.12],
    dc_rho: md.dc_rho,
    draw_inflate: md.draw_inflate,
    vmr: md.vmr,
    poisson: md.poisson,
    negative_binomial: md.negative_binomial,
    skellam: md.skellam,
    monte_carlo: md.monte_carlo,
    market: md.shin,
    market_note: '体彩HAD归一化去水 41.0/27.0/31.9',
    h2h_shift: [-0.02, 0.02],
    xg: { home: 9.1, away: 10.1, source: 'Fotmob 26/27（8轮）', conflict: 'footdujour给埃弗顿xG 12.4，取保守口径' },
    rule65: '不触发（非同级别强弱碾压，λ_total 2.47低于联赛均值2.86）'
  },
  recommendation: {
    had_primary: 'home', had_primary_prob: +md.probs_final.home.toFixed(4),
    had_secondary: 'draw', had_secondary_prob: +md.probs_final.draw.toFixed(4),
    hc_primary: 'away', hc_secondary: 'draw', hc_line: -1,
    hc_probs: md.handicap_minus1,
    ttg_top2: [2, 3], tier: '常规正常球(2-3球)', over_under: '小',
    htft_top3: [['胜胜', +md.htft.HH.toFixed(4)], ['平平', +md.htft.DD.toFixed(4)], ['平胜', +md.htft.DH.toFixed(4)]],
    cr_top5: ['1-1', '1-0', '2-1', '0-1', '1-2'].map(s => ({ score: s, prob: +md.top_scores.find(x => x[0] === s)[1].toFixed(4), odds: crs[s.replace('-', ':')] })),
    ht_score: md.ht_scores.slice(0, 3).map(x => ({ score: x[0], prob: +x[1].toFixed(4) })),
    k_dist: { k: md.k_dist.k, p: +md.k_dist.p.toFixed(4) },
    k_rec: { k: md.k_rec.k, p: +md.k_rec.p.toFixed(4) },
    single_plan: [
      { type: '主推', market: 'HAD', pick: '主胜', odds: 2.14, prob: +md.probs_final.home.toFixed(4) },
      { type: '稳健替代', market: 'HHAD(-1)', pick: '让负', odds: 1.52, prob: +md.handicap_minus1.lose.toFixed(4) },
      { type: '高赔娱乐', market: 'CRS', pick: '1-1', odds: crs['1:1'], prob: +md.top_scores.find(x => x[0] === '1-1')[1].toFixed(4) }
    ],
    confidence: '★★中',
    confidence_reason: '主胜40.1%与市场41.0%对齐、四模型一致；但首选<45%、平+客59.9%、SJP交锋两连败、5人伤停名单，按规则46不满足★★★'
  },
  notes: [
    '引用L241：单关取模型-市场分歧最小一侧→主胜（-0.9pp）',
    '引用L253：让(-1)且主胜<55%，首选允许让负；让平已进次选',
    '引用L255：一球盘口场TOP5含1-0/0-1；分布-方向分歧，不进入稳健比分串',
    '引用L256：半全场TOP3绑定方向并保留半场≠全场路径（平胜）',
    '引用L166/L209：平赔3.25>3.20不上修；首选<45%且平局≥26%，次选给平局'
  ],
  data_sources: [
    '体彩官方接口（2026-11-02 12:29更新）',
    'Premier League官网积分榜/球队动态',
    '埃弗顿官网10-30伤停公告',
    '利物浦回声报10-31伤停',
    'Fotmob（伤停/xG/H2H）',
    '球迷屋（近10场/进失球分布，未验证，仅参考）',
    'NUFC.com（SJP交锋史/赛程）',
    'Met Office（纽卡斯尔天气）'
  ]
};

const dir = 'memory/predictions/20261102_monday';
fs.mkdirSync(dir, { recursive: true });
fs.writeFileSync('reports/data/20261102_predictions.json', JSON.stringify([out], null, 2), 'utf8');
fs.writeFileSync(path.join(dir, 'prediction.json'), JSON.stringify([out], null, 2), 'utf8');
console.log('saved, crs keys:', Object.keys(crs).length);
