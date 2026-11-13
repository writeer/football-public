const fs = require('fs');
const odds = JSON.parse(fs.readFileSync('reports/data/monday_odds_parsed.json', 'utf8').replace(/^\uFEFF/, ''));

// λ parameters (post fundamental/league adjustment) & draw boost for single games
const params = {
  '周一001': { lh: 2.00, la: 0.70, single: false },
  '周一002': { lh: 1.50, la: 0.90, single: false },
  '周一003': { lh: 1.25, la: 1.05, single: false },
  '周一004': { lh: 1.10, la: 1.30, single: true },
  '周一005': { lh: 1.30, la: 1.20, single: true },
  '周一006': { lh: 1.35, la: 0.85, single: false },
  '周一007': { lh: 1.40, la: 0.80, single: false },
  '周一008': { lh: 1.00, la: 0.80, single: false }
};

const N = 8;
const fact = n => { let r = 1; for (let i = 2; i <= n; i++) r *= i; return r; };
const pois = (k, l) => Math.exp(-l) * Math.pow(l, k) / fact(k);

// half-time factor: friendly 0.42, nations league 0.45
const out = { date: '2026-09-28', weekday: '周一', matches: [] };

for (const num in params) {
  const p = params[num];
  const o = odds[num];
  const M = [];
  for (let i = 0; i <= N; i++) { M[i] = []; for (let j = 0; j <= N; j++) M[i][j] = pois(i, p.lh) * pois(j, p.la); }
  let pH = 0, pD = 0, pA = 0;
  for (let i = 0; i <= N; i++) for (let j = 0; j <= N; j++) { if (i > j) pH += M[i][j]; else if (i === j) pD += M[i][j]; else pA += M[i][j]; }
  if (p.single) { const sc = (pH + pA - 0.08) / (pH + pA); pH *= sc; pA *= sc; pD += 0.08; }
  const tot = pH + pD + pA; pH /= tot; pD /= tot; pA /= tot;

  const scores = [];
  for (let i = 0; i <= N; i++) for (let j = 0; j <= N; j++) scores.push({ score: `${i}-${j}`, prob: +M[i][j].toFixed(4) });
  scores.sort((a, b) => b.prob - a.prob);

  const ttg = [];
  for (let t = 0; t <= 2 * N; t++) { let s = 0; for (let i = 0; i <= N; i++) for (let j = 0; j <= N; j++) if (i + j === t) s += M[i][j]; ttg.push({ goals: t, prob: +s.toFixed(4) }); }
  ttg.sort((a, b) => b.prob - a.prob);

  let hH = 0, hD = 0, hA = 0;
  for (let i = 0; i <= N; i++) for (let j = 0; j <= N; j++) { const adj = (i - j) + o.hhad.goalLine; if (adj > 0) hH += M[i][j]; else if (adj === 0) hD += M[i][j]; else hA += M[i][j]; }

  const netGoals = {};
  for (let i = 0; i <= N; i++) for (let j = 0; j <= N; j++) { const k = i - j; netGoals[k] = (netGoals[k] || 0) + M[i][j]; }
  let kDist = null, kDistP = 0;
  for (const k in netGoals) if (netGoals[k] > kDistP) { kDistP = netGoals[k]; kDist = +k; }

  const dir = pH >= pD && pH >= pA ? 'home' : (pA >= pD && pA >= pH ? 'away' : 'draw');
  let kRec = null, kRecP = 0;
  for (const k in netGoals) {
    const ki = +k;
    if ((dir === 'home' && ki >= 1) || (dir === 'away' && ki <= -1) || (dir === 'draw' && ki === 0)) {
      if (netGoals[k] > kRecP) { kRecP = netGoals[k]; kRec = ki; }
    }
  }
  const band = [];
  for (let i = 0; i <= N; i++) for (let j = 0; j <= N; j++) if (i - j === kRec) band.push({ score: `${i}-${j}`, prob: +M[i][j].toFixed(4) });
  band.sort((a, b) => b.prob - a.prob);

  const kDistDir = kDist > 0 ? '主胜' : (kDist < 0 ? '客胜' : '平');
  const hadFirst = dir === 'home' ? '主胜' : (dir === 'away' ? '客胜' : '平');

  out.matches.push({
    matchNum: num, home: o.home, away: o.away, league: o.league, single: o.single,
    lambda_home: p.lh, lambda_away: p.la,
    prob_had: { home: +pH.toFixed(4), draw: +pD.toFixed(4), away: +pA.toFixed(4) },
    prob_hhad: { win: +hH.toFixed(4), draw: +hD.toFixed(4), lose: +hA.toFixed(4) },
    odds_had: o.had,
    odds_hhad: { handicap: o.hhad.goalLine, ...o.hhad.odds },
    odds_crs: o.crs, odds_ttg: o.ttg, odds_hafu: o.hafu,
    crs_top5: scores.slice(0, 5).map(s => ({ score: s.score, prob: s.prob })),
    ttg_top2: ttg.slice(0, 2),
    net_goal: { k_dist: kDist, k_dist_prob: +kDistP.toFixed(4), k_rec: kRec, k_rec_prob: +kRecP.toFixed(4), k_dist_dir: kDistDir, had_first: hadFirst, consistent: kDistDir === hadFirst },
    band_top3: band.slice(0, 3)
  });
}
fs.mkdirSync('memory/predictions', { recursive: true });
fs.writeFileSync('memory/predictions/20260928_monday_predictions.json', JSON.stringify(out, null, 2), 'utf8');
console.log('OK -> memory/predictions/20260928_monday_predictions.json');
console.log('matches:', out.matches.length);
out.matches.forEach(m => console.log(`${m.matchNum} ${m.home}vs${m.away} | k_dist=${m.net_goal.k_dist} k_rec=${m.net_goal.k_rec} ${m.net_goal.consistent ? '一致' : '分歧'}`));
