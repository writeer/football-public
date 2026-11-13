// 解析 2026-10-27 体彩原始数据 → matches.json
import fs from 'fs';

let rawStr = fs.readFileSync('reports/data/20261027_raw.json', 'utf8');
if (rawStr.charCodeAt(0) === 0xFEFF) rawStr = rawStr.slice(1);
const raw = JSON.parse(rawStr);
const groups = raw.value.matchInfoList;

const HAD_KEYS = { 'h': 'home', 'd': 'draw', 'a': 'away' };
const HAFU_KEYS = {
  'hh': 'HH', 'hd': 'HD', 'ha': 'HA',
  'dh': 'DH', 'dd': 'DD', 'da': 'DA',
  'ah': 'AH', 'ad': 'AD', 'aa': 'AA',
};

function parseOdds(rawPool, keyMap) {
  if (!rawPool) return null;
  const out = [];
  for (const [code, key] of Object.entries(keyMap)) {
    if (rawPool[code] !== undefined && rawPool[code] !== null && rawPool[code] !== '') {
      out.push({ key, odds: parseFloat(rawPool[code]) });
    }
  }
  return out.length ? out : null;
}

function parseTTG(rawTTG) {
  if (!rawTTG) return null;
  const out = [];
  for (let i = 0; i <= 7; i++) {
    const k = 's' + i;
    if (rawTTG[k] !== undefined && rawTTG[k] !== null && rawTTG[k] !== '') {
      out.push({ key: String(i), odds: parseFloat(rawTTG[k]) });
    }
  }
  return out.length ? out : null;
}

function parseCRS(rawCRS) {
  if (!rawCRS) return null;
  const out = [];
  for (const [code, val] of Object.entries(rawCRS)) {
    if (code.startsWith('s') && !code.endsWith('f') && !code.includes('goalLine') && !code.includes('update')) {
      // s01s02 → 1:2
      const m = code.match(/^s(\d+)s(\d+)$/);
      if (m && val !== '' && val !== undefined) {
        const homeScore = parseInt(m[1], 10);
        const awayScore = parseInt(m[2], 10);
        if (!isNaN(homeScore) && !isNaN(awayScore)) {
          out.push({ key: `${homeScore}:${awayScore}`, odds: parseFloat(val) });
        }
      }
    }
  }
  return out.length ? out : null;
}

function de_vig(oddsList) {
  const inv = oddsList.map(o => 1 / o.odds);
  const s = inv.reduce((a, b) => a + b, 0);
  return oddsList.map((o, i) => ({ ...o, noVig: inv[i] / s }));
}

const matches = [];
for (const g of groups) {
  if (g.matchNumDate !== '261027') continue;
  const sms = typeof g.subMatchList === 'string' ? JSON.parse(g.subMatchList) : g.subMatchList;
  for (const sm of sms) {
    const match = {
      num: sm.matchNumStr,
      league: sm.leagueAbbName,
      home: sm.homeTeamAllName,
      away: sm.awayTeamAllName,
      home_rank: (sm.homeRank || '').replace(/[\[\]]/g, ''),
      away_rank: (sm.awayRank || '').replace(/[\[\]]/g, ''),
      time: sm.matchTime || '',
      match_date: sm.matchDate || '',
      betting_single: sm.bettingSingle === '1' || sm.bettingSingle === 1,
    };

    const had = parseOdds(sm.had, HAD_KEYS);
    if (had) match.had = de_vig(had);

    if (sm.hhad) {
      const gl_str = sm.hhad.goalLineValue || sm.hhad.goalLine || '';
      const gl = gl_str ? parseFloat(gl_str) : null;
      const hhad_out = parseOdds(sm.hhad, HAD_KEYS);
      if (hhad_out) {
        match.hhad = { goalLine: gl, outcomes: de_vig(hhad_out) };
      }
    }

    const ttg = parseTTG(sm.ttg);
    if (ttg) match.ttg = de_vig(ttg);

    const hafu = parseOdds(sm.hafu, HAFU_KEYS);
    if (hafu) match.hafu = de_vig(hafu);

    const crs = parseCRS(sm.crs);
    if (crs) match.crs = de_vig(crs);

    matches.push(match);
  }
}

fs.writeFileSync('reports/data/20261027_matches.json', JSON.stringify(matches, null, 2), 'utf8');
console.log(`Parsed ${matches.length} matches`);
for (const m of matches) {
  const had_s = m.had ? `H${m.had.find(o=>o.key==='home')?.odds} D${m.had.find(o=>o.key==='draw')?.odds} A${m.had.find(o=>o.key==='away')?.odds}` : 'noHAD';
  const hhad_s = m.hhad ? `(gl${m.hhad.goalLine})` : '';
  const ttg_s = m.ttg ? `TTG: ${m.ttg.length}项` : '';
  const crs_s = m.crs ? `CRS: ${m.crs.length}项` : '';
  console.log(`  ${m.num} ${m.league} ${m.home}[${m.home_rank}] vs ${m.away}[${m.away_rank}] ${had_s} ${hhad_s} ${ttg_s} ${crs_s} 单关=${m.betting_single}`);
}
