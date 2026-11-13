const matches = [
  {
    id: '001', league: '国际赛', home: '日本', away: '委内瑞拉',
    lh: 2.0, la: 0.7, single: false,
    hhad: -1, hadOdds: [1.18, 5.15, 11.5], hhadOdds: [1.71, 3.65, 3.7]
  },
  {
    id: '002', league: '国际赛', home: '韩国', away: '乌拉圭',
    lh: 1.5, la: 0.9, single: false,
    hhad: -1, hadOdds: [2.31, 3.05, 2.71], hhadOdds: [5.18, 3.9, 1.47]
  },
  {
    id: '003', league: '欧国联', home: '亚美尼亚', away: '黑山',
    lh: 1.25, la: 1.05, single: false,
    hhad: -1, hadOdds: [2.5, 3.05, 2.5], hhadOdds: [5.75, 4.15, 1.4]
  },
  {
    id: '004', league: '欧国联', home: '土耳其', away: '意大利',
    lh: 1.1, la: 1.3, single: true,
    hhad: 1, hadOdds: [2.65, 3.3, 2.23], hhadOdds: [1.5, 4.1, 4.6]
  },
  {
    id: '005', league: '欧国联', home: '比利时', away: '法国',
    lh: 1.3, la: 1.2, single: true,
    hhad: 1, hadOdds: [3.55, 3.71, 1.73], hhadOdds: [1.87, 3.65, 3.12]
  },
  {
    id: '006', league: '欧国联', home: '罗马尼亚', away: '波黑',
    lh: 1.35, la: 0.85, single: false,
    hhad: -1, hadOdds: [1.92, 3.22, 3.35], hhadOdds: [4.05, 3.58, 1.66]
  },
  {
    id: '007', league: '欧国联', home: '瑞典', away: '波兰',
    lh: 1.4, la: 0.8, single: false,
    hhad: -1, hadOdds: [1.82, 3.4, 3.5], hhadOdds: [3.45, 3.65, 1.77]
  },
  {
    id: '008', league: '欧国联', home: '北爱尔兰', away: '匈牙利',
    lh: 1.0, la: 0.8, single: false,
    hhad: 1, hadOdds: [2.6, 2.87, 2.52], hhadOdds: [1.39, 4.1, 6.05]
  }
];

function poisson(k, lambda) {
  return Math.exp(-lambda) * Math.pow(lambda, k) / factorial(k);
}

function factorial(n) {
  let r = 1;
  for (let i = 2; i <= n; i++) r *= i;
  return r;
}

const N = 8; // matrix size

for (const m of matches) {
  // Apply rule 63: single game draw upshift
  let drawBoost = m.single ? 0.08 : 0;

  // Build score matrix
  const matrix = [];
  for (let i = 0; i <= N; i++) {
    matrix[i] = [];
    for (let j = 0; j <= N; j++) {
      matrix[i][j] = poisson(i, m.lh) * poisson(j, m.la);
    }
  }

  // HAD probabilities
  let pHome = 0, pDraw = 0, pAway = 0;
  for (let i = 0; i <= N; i++) {
    for (let j = 0; j <= N; j++) {
      if (i > j) pHome += matrix[i][j];
      else if (i === j) pDraw += matrix[i][j];
      else pAway += matrix[i][j];
    }
  }

  // Apply draw boost
  if (drawBoost > 0) {
    let scale = (pHome + pAway - drawBoost) / (pHome + pAway);
    pHome *= scale;
    pAway *= scale;
    pDraw += drawBoost;
  }

  // Normalize
  const total = pHome + pDraw + pAway;

  // Score TOP5
  const scores = [];
  for (let i = 0; i <= N; i++) {
    for (let j = 0; j <= N; j++) {
      scores.push({ score: `${i}:${j}`, i, j, prob: matrix[i][j], total: i + j, diff: i - j });
    }
  }
  scores.sort((a, b) => b.prob - a.prob);
  const top5 = scores.slice(0, 5);

  // TTG
  const ttg = [];
  for (let t = 0; t <= 2 * N; t++) {
    let p = 0;
    for (let i = 0; i <= N; i++) {
      for (let j = 0; j <= N; j++) {
        if (i + j === t) p += matrix[i][j];
      }
    }
    ttg.push({ goals: t, prob: p });
  }
  ttg.sort((a, b) => b.prob - a.prob);
  const ttgTop2 = ttg.slice(0, 2);

  // HHAD (handicap)
  let pHHadH = 0, pHHadD = 0, pHHadA = 0;
  for (let i = 0; i <= N; i++) {
    for (let j = 0; j <= N; j++) {
      let adj = (i - j) + m.hhad; // adjusted net goals
      if (adj > 0) pHHadH += matrix[i][j];
      else if (adj === 0) pHHadD += matrix[i][j];
      else pHHadA += matrix[i][j];
    }
  }

  // HTFT (half-time full-time)
  // Half-time lambda = full-time * 0.45 (or 0.38/0.42 based on league)
  let htFactor = 0.45;
  if (m.league === '欧国联') htFactor = 0.45; // Nations League ht_draw_rate = null, use default
  if (m.league === '国际赛') htFactor = 0.42; // International friendly ht_draw_rate ~0.38-0.43, use 0.42

  const lht = m.lh * htFactor;
  const lat = m.la * htFactor;

  const htMatrix = [];
  for (let i = 0; i <= 5; i++) {
    htMatrix[i] = [];
    for (let j = 0; j <= 5; j++) {
      htMatrix[i][j] = poisson(i, lht) * poisson(j, lat);
    }
  }

  // HTFT combinations
  const htft = {};
  // For each HT result, distribute to FT result proportionally
  const htResults = {};
  for (let i = 0; i <= 5; i++) {
    for (let j = 0; j <= 5; j++) {
      let key;
      if (i > j) key = 'H'; else if (i === j) key = 'D'; else key = 'A';
      if (!htResults[key]) htResults[key] = 0;
      htResults[key] += htMatrix[i][j];
    }
  }

  // Simplified HTFT: use conditional approach
  // HH = HT home win → FT home win
  // HD = HT home win → FT draw
  // HA = HT home win → FT away win
  // DH = HT draw → FT home win
  // DD = HT draw → FT draw
  // DA = HT draw → FT away win
  // AH = HT away win → FT home win
  // AD = HT away win → FT draw
  // AA = HT away win → FT away win

  // Simplified: P(FT|HT) based on direction continuity
  const pHT_H = htResults['H'] || 0;
  const pHT_D = htResults['D'] || 0;
  const pHT_A = htResults['A'] || 0;

  // Conditional probabilities (simplified)
  const htftList = [
    { code: '胜胜', prob: pHT_H * (pHome / (pHome + pDraw + pAway)) * 0.80 + pHT_H * 0.10 },
    { code: '平胜', prob: pHT_D * (pHome / (pHome + pDraw + pAway)) * 0.60 },
    { code: '平平', prob: pHT_D * (pDraw / (pHome + pDraw + pAway)) * 0.70 + pHT_D * 0.10 },
    { code: '负负', prob: pHT_A * (pAway / (pHome + pDraw + pAway)) * 0.80 + pHT_A * 0.10 },
    { code: '平负', prob: pHT_D * (pAway / (pHome + pDraw + pAway)) * 0.60 },
    { code: '胜负', prob: pHT_H * (pAway / (pHome + pDraw + pAway)) * 0.30 },
    { code: '负胜', prob: pHT_A * (pHome / (pHome + pDraw + pAway)) * 0.30 },
    { code: '负平', prob: pHT_A * (pDraw / (pHome + pDraw + pAway)) * 0.40 },
    { code: '胜平', prob: pHT_H * (pDraw / (pHome + pDraw + pAway)) * 0.40 },
  ];
  htftList.sort((a, b) => b.prob - a.prob);
  const htftTop3 = htftList.slice(0, 3);

  // HT score TOP3
  const htScores = [];
  for (let i = 0; i <= 5; i++) {
    for (let j = 0; j <= 5; j++) {
      htScores.push({ score: `${i}:${j}`, prob: htMatrix[i][j] });
    }
  }
  htScores.sort((a, b) => b.prob - a.prob);
  const htTop3 = htScores.slice(0, 3);

  // Net goal distribution (for rule 52a and 67)
  const netGoals = {};
  for (let i = 0; i <= N; i++) {
    for (let j = 0; j <= N; j++) {
      const k = i - j;
      if (!netGoals[k]) netGoals[k] = 0;
      netGoals[k] += matrix[i][j];
    }
  }

  // k_dist: unconditional mode
  let kDist = null, kDistProb = 0;
  for (const k in netGoals) {
    if (netGoals[k] > kDistProb) {
      kDistProb = netGoals[k];
      kDist = parseInt(k);
    }
  }

  // k_rec: direction-conditional mode
  let hadFirstDir;
  if (pHome >= pDraw && pHome >= pAway) hadFirstDir = 'home';
  else if (pAway >= pDraw && pAway >= pHome) hadFirstDir = 'away';
  else hadFirstDir = 'draw';

  let kRec = null, kRecProb = 0;
  for (const k in netGoals) {
    const ki = parseInt(k);
    if (hadFirstDir === 'home' && ki >= 1) {
      if (netGoals[k] > kRecProb) { kRecProb = netGoals[k]; kRec = ki; }
    } else if (hadFirstDir === 'away' && ki <= -1) {
      if (netGoals[k] > kRecProb) { kRecProb = netGoals[k]; kRec = ki; }
    } else if (hadFirstDir === 'draw' && ki === 0) {
      kRecProb = netGoals[k]; kRec = 0;
    }
  }

  // Score candidates within k_rec band
  const bandCandidates = [];
  for (let i = 0; i <= N; i++) {
    for (let j = 0; j <= N; j++) {
      if (i - j === kRec) {
        bandCandidates.push({ score: `${i}:${j}`, i, j, prob: matrix[i][j], total: i + j });
      }
    }
  }
  bandCandidates.sort((a, b) => b.prob - a.prob);

  // Determine direction for display
  let hadFirst, hadSecond;
  if (pHome >= pDraw && pHome >= pAway) {
    hadFirst = '主胜';
    hadSecond = pDraw >= pAway ? '平' : '客胜';
  } else if (pAway >= pDraw && pAway >= pHome) {
    hadFirst = '客胜';
    hadSecond = pDraw >= pHome ? '平' : '主胜';
  } else {
    hadFirst = '平';
    hadSecond = pHome >= pAway ? '主胜' : '客胜';
  }

  // HHAD first/second
  let hhadFirst, hhadSecond;
  if (pHHadH >= pHHadD && pHHadH >= pHHadA) {
    hhadFirst = '让胜';
    hhadSecond = pHHadD >= pHHadA ? '让平' : '让负';
  } else if (pHHadD >= pHHadH && pHHadD >= pHHadA) {
    hhadFirst = '让平';
    hhadSecond = pHHadH >= pHHadA ? '让胜' : '让负';
  } else {
    hhadFirst = '让负';
    hhadSecond = pHHadH >= pHHadD ? '让胜' : '让平';
  }

  // Apply rule 52a: handicap first choice from unconditional net goal mode
  // k_dist determines handicap first choice
  if (m.hhad === -1) { // home gives 1 goal
    if (kDist >= 2) { hhadFirst = '让胜'; hhadSecond = pHHadD >= pHHadA ? '让平' : '让负'; }
    else if (kDist === 1) { hhadFirst = '让平'; hhadSecond = pHHadH >= pHHadA ? '让胜' : '让负'; }
    else if (kDist === 0) { hhadFirst = '让负'; hhadSecond = pHHadH >= pHHadD ? '让胜' : '让平'; }
    else if (kDist <= -1) { hhadFirst = '让负'; hhadSecond = pHHadD >= pHHadH ? '让平' : '让胜'; }
  } else if (m.hhad === 1) { // home receives 1 goal
    if (kDist >= 1) { hhadFirst = '让胜'; hhadSecond = pHHadD >= pHHadA ? '让平' : '让负'; }
    else if (kDist === 0) { hhadFirst = '让胜'; hhadSecond = pHHadD >= pHHadA ? '让平' : '让负'; }
    else if (kDist === -1) { hhadFirst = '让平'; hhadSecond = pHHadH >= pHHadA ? '让胜' : '让负'; }
    else { hhadFirst = '让负'; hhadSecond = pHHadH >= pHHadD ? '让胜' : '让平'; }
  }

  // Output
  const consistency = kDist === kRec ? '众数一致' : '分布-方向分歧';
  const kDistDir = kDist > 0 ? '主胜' : (kDist < 0 ? '客胜' : '平');
  const matchConsistency = kDistDir === hadFirst ? '众数一致' : '分布-方向分歧';

  console.log(`\n=== ${m.id} ${m.home} vs ${m.away} (${m.league})${m.single ? ' [单关]' : ''} ===`);
  console.log(`Lambda: 主${m.lh} / 客${m.la} (总${(m.lh + m.la).toFixed(2)})`);
  console.log(`HAD: 主胜 ${(pHome * 100).toFixed(1)}% | 平 ${(pDraw * 100).toFixed(1)}% | 客胜 ${(pAway * 100).toFixed(1)}%`);
  console.log(`HAD首选: ${hadFirst} | 次选: ${hadSecond}`);
  console.log(`HHAD(${m.hhad}): 让胜 ${(pHHadH * 100).toFixed(1)}% | 让平 ${(pHHadD * 100).toFixed(1)}% | 让负 ${(pHHadA * 100).toFixed(1)}%`);
  console.log(`HHAD首选: 让(${m.hhad})${hhadFirst} | 次选: 让(${m.hhad})${hhadSecond}`);
  console.log(`比分TOP5: ${top5.map(s => `${s.score}(${(s.prob * 100).toFixed(1)}%)`).join(' > ')}`);
  console.log(`TTG TOP2: ${ttgTop2.map(t => `${t.goals}球(${(t.prob * 100).toFixed(1)}%)`).join(' / ')}`);
  console.log(`半全场TOP3: ${htftTop3.map(h => `${h.code}(${(h.prob * 100).toFixed(1)}%)`).join(' > ')}`);
  console.log(`半场比分TOP3: ${htTop3.map(h => `${h.score}(${(h.prob * 100).toFixed(1)}%)`).join(' > ')}`);
  console.log(`净胜球众数: 分布众数 ${kDist}(${(kDistProb * 100).toFixed(1)}%) | 推荐众数 ${kRec}(${(kRecProb * 100).toFixed(1)}%) | ${matchConsistency}`);
  console.log(`带内候选: ${bandCandidates.slice(0, 3).map(c => `${c.score}(${(c.prob * 100).toFixed(1)}%)`).join(' > ')}`);
}
