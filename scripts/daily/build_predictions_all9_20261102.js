// 生成 2026-11-02 全部9场预测JSON（归档/回测用）
const fs = require('fs');
const matches = JSON.parse(fs.readFileSync('reports/data/20261102_matches.json', 'utf8'));
const model = JSON.parse(fs.readFileSync('reports/data/20261102_model_output.json', 'utf8'));
const meta = {
  '周一001': { conf: '★', scores: ['1-0', '1-1', '2-0', '0-0', '2-1'], hafu: ['胜胜', '平胜', '平平'], ttg: [2, 3], tier: '常规正常球(2-3球)', ou: '小' },
  '周一002': { conf: '★', scores: ['1-1', '2-1', '1-2', '2-2', '2-0'], hafu: ['胜胜', '平胜', '负负'], ttg: [3, 2], tier: '常规正常球(2-3球)', ou: '大' },
  '周一003': { conf: '★', scores: ['1-1', '1-0', '0-0', '2-0', '0-1'], hafu: ['胜胜', '平胜', '平平'], ttg: [2, 3], tier: '常规正常球(2-3球)', ou: '小' },
  '周一004': { conf: '★', scores: ['1-0', '2-0', '1-1', '0-0', '2-1'], hafu: ['胜胜', '平胜', '平平'], ttg: [2, 3], tier: '常规正常球(2-3球)', ou: '小' },
  '周一005': { conf: '★', scores: ['1-1', '0-0', '1-0', '0-1', '1-2'], hafu: ['平平', '胜胜', '平胜'], ttg: [2, 1], tier: '常规正常球(2-3球)', ou: '小' },
  '周一006': { conf: '★★', scores: ['1-1', '1-0', '2-1', '0-1', '1-2'], hafu: ['胜胜', '平平', '平胜'], ttg: [2, 3], tier: '常规正常球(2-3球)', ou: '小' },
  '周一007': { conf: '★★', scores: ['1-1', '1-0', '2-1', '2-0', '0-0'], hafu: ['胜胜', '平胜', '平平'], ttg: [2, 3], tier: '常规正常球(2-3球)', ou: '小' },
  '周一008': { conf: '★', scores: ['2-0', '2-1', '3-0', '1-1', '1-0'], hafu: ['胜胜', '平胜', '平平'], ttg: [3, 2], tier: '常规正常球(2-3球)', ou: '大' },
  '周一009': { conf: '★', scores: ['1-1', '1-0', '2-1', '2-0', '0-1'], hafu: ['胜胜', '平胜', '平平'], ttg: [2, 3], tier: '常规正常球(2-3球)', ou: '大' }
};
const hafuMap = { '胜胜': 'HH', '胜平': 'HD', '胜负': 'HA', '平胜': 'DH', '平平': 'DD', '平负': 'DA', '负胜': 'AH', '负平': 'AD', '负负': 'AA' };

const out = [];
for (const [num, md] of Object.entries(model)) {
  const raw = matches.find(m => m.num === num);
  const mt = meta[num];
  const p = md.probs_final;
  let primary, secondary, primaryProb, secondaryProb, hcLine = raw.hhad ? raw.hhad.goalLine : null;
  if (num === '周一008') {
    primary = 'hhad_lose'; secondary = 'hhad_push';
    primaryProb = md.handicap.lose; secondaryProb = md.handicap.push;
  } else {
    const order = ['home', 'draw', 'away'].sort((a, b) => p[b] - p[a]);
    primary = order[0]; secondary = order[1];
    primaryProb = p[primary]; secondaryProb = p[secondary];
  }
  const hc = md.handicap;
  // 让球首选：L253 主胜>=55% 时禁止让负
  let hcPrimary, hcSecondary, hcPrimaryProb, hcSecondaryProb;
  if (num === '周一008') {
    hcPrimary = 'lose'; hcSecondary = 'push';
  } else if (p.home >= 0.55) {
    hcPrimary = 'win'; hcSecondary = 'push';
  } else {
    const hcOrder = ['win', 'push', 'lose'].sort((a, b) => hc[b] - hc[a]);
    hcPrimary = hcOrder[0]; hcSecondary = hcOrder[1];
  }
  hcPrimaryProb = hc[hcPrimary]; hcSecondaryProb = hc[hcSecondary];

  const hadOdds = raw.had ? Object.fromEntries(raw.had.map(o => [o.key, o.odds])) : null;
  const hhadOdds = raw.hhad ? { handicap: raw.hhad.goalLine, ...Object.fromEntries(raw.hhad.outcomes.map(o => [o.key, o.odds])) } : null;
  const crsOdds = Object.fromEntries(raw.crs.map(o => [o.key, o.odds]));
  const ttgOdds = Object.fromEntries(raw.ttg.map(o => [o.key, o.odds]));
  const hafuOdds = Object.fromEntries(raw.hafu.map(o => [o.key, o.odds]));

  out.push({
    num, league: md.league, home: md.home, away: md.away,
    kickoff: raw.time, match_date: raw.match_date,
    is_single: num === '周一006',
    confidence: mt.conf,
    lambda: md.lambda,
    model: { home: p.home, draw: p.draw, away: p.away },
    market: md.market,
    handicap: hc,
    odds_had: hadOdds, odds_hhad: hhadOdds, odds_crs: crsOdds, odds_ttg: ttgOdds, odds_hafu: hafuOdds,
    recommendation: {
      had_primary: primary, had_primary_prob: primaryProb,
      had_secondary: secondary, had_secondary_prob: secondaryProb,
      hc_line: hcLine, hc_primary: hcPrimary, hc_primary_prob: hcPrimaryProb,
      hc_secondary: hcSecondary, hc_secondary_prob: hcSecondaryProb,
      cr_top5: mt.scores.map(s => ({ score: s, prob: md.top_scores.find(x => x[0] === s)[1], odds: crsOdds[s.replace('-', ':')] })),
      hafu_top3: mt.hafu.map(x => ({ pick: x, prob: md.htft[hafuMap[x]] })),
      ttg_top2: mt.ttg, tier: mt.tier, over_under: mt.ou,
      ht_score: md.ht_scores.slice(0, 3).map(x => ({ score: x[0], prob: x[1] })),
      k_dist: md.k_dist, k_rec: md.k_rec
    }
  });
}

fs.writeFileSync('reports/data/20261102_predictions.json', JSON.stringify(out, null, 2), 'utf8');
fs.mkdirSync('memory/predictions/20261102_monday', { recursive: true });
fs.writeFileSync('memory/predictions/20261102_monday/prediction.json', JSON.stringify(out, null, 2), 'utf8');
console.log('saved', out.length, 'matches');
for (const x of out) console.log(x.num, x.confidence, x.recommendation.had_primary, (x.recommendation.had_primary_prob * 100).toFixed(1), x.recommendation.hc_primary, (x.recommendation.hc_primary_prob * 100).toFixed(1));
