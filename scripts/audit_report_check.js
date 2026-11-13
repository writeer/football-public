const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const file = process.argv[2];
if (!file) {
  console.error('用法: node scripts/audit_report_check.js <报告md路径>');
  process.exit(2);
}
const abs = path.isAbsolute(file) ? file : path.join(root, file);
const md = fs.readFileSync(abs, 'utf8');
const lines = md.split(/\r?\n/);

const out = { file: path.relative(root, abs), generated_at: new Date().toISOString(), checks: {}, counts: {} };

// 【回测】报告走独立检查分支；【分析】报告沿用下方原有 13 项检查
function runBacktest(md, lines, out) {
  // 1. 标题
  out.checks.title = /^# 【回测】\d{4}-\d{2}-\d{2}（周.）回测报告 \| .+/.test(lines[0]) ? 'PASS' : 'FAIL';
  out.counts.title_line = lines[0];

  // 2. 开头固定块顺序
  const headKeys = ['报告说明', '风险提示', '免责声明', '每日更新'];
  const headPos = headKeys.map(k => lines.findIndex(l => l.includes(k)));
  out.checks.header_block = headPos.every((p, i) => p >= 0 && (i === 0 || p > headPos[i - 1])) ? 'PASS' : 'FAIL';
  out.counts.header_positions = Object.fromEntries(headKeys.map((k, i) => [k, headPos[i]]));

  // 3. 顶层章
  const chapters = lines.filter(l => /^## /.test(l)).map(l => l.replace(/^## /, '').trim());
  out.counts.chapters = chapters;
  const expected = ['总览', '逐场回测', '命中率统计', '串关回测', '关键发现', '待改进', '写在最后'];
  const missing = expected.filter(e => !chapters.some(c => c.includes(e)));
  const extra = chapters.filter(c => !expected.some(e => c.includes(e)));
  out.checks.chapter_order = missing.length === 0 && extra.length === 0 ? 'PASS' : 'FAIL';
  out.counts.missing_chapters = missing;
  out.counts.extra_chapters = extra;

  // 4. 逐场 10 部分
  const secs = [];
  for (let i = 0; i < lines.length; i++) {
    if (/^### 周四\d{3} /.test(lines[i])) {
      let end = lines.length;
      for (let j = i + 1; j < lines.length; j++) {
        if (/^#{2,3} /.test(lines[j])) { end = j; break; }
      }
      secs.push({ title: lines[i].replace(/^### /, ''), body: lines.slice(i, end).join('\n') });
    }
  }
  const parts = [
    ['赛果', /赛果：/],
    ['方向', /\| \*\*方向\*\* \|/],
    ['让球', /\| \*\*让球\*\* \|/],
    ['总进球TOP2', /\| \*\*总进球TOP2\*\* \|/],
    ['半全场TOP3', /\| \*\*半全场TOP3\*\* \|/],
    ['比分TOP5', /\| \*\*比分TOP5\*\* \|/],
    ['半场比分TOP3', /\| \*\*半场比分TOP3\*\* \|/],
    ['大小球方向', /\| \*\*大小球方向（2\.5）\*\* \|/],
    ['大小球六档', /\| \*\*大小球六档（L74）\*\* \|/],
    ['点评', /^> /m]
  ];
  out.counts.per_match = secs.map(s => ({
    match: s.title,
    missing_parts: parts.filter(([, re]) => !re.test(s.body)).map(([n]) => n)
  }));
  out.checks.per_match_parts = secs.length === 6 && out.counts.per_match.every(m => m.missing_parts.length === 0) ? 'PASS' : 'FAIL';

  // 5. 总览表：6 行、≤13 列
  const ovStart = lines.findIndex(l => /^## 总览/.test(l));
  let ovEnd = lines.length;
  for (let j = ovStart + 1; j < lines.length; j++) { if (/^## /.test(lines[j])) { ovEnd = j; break; } }
  const ov = lines.slice(ovStart, ovEnd).filter(l => /^\|/.test(l.trim()));
  const ovCols = ov.length ? ov[0].trim().replace(/^\||\|$/g, '').split('|').length : 0;
  const ovRows = ov.filter(l => /^\| 周四\d{3} /.test(l.trim())).length;
  out.counts.overview = { columns: ovCols, rows: ovRows };
  out.checks.overview_table = ovCols > 0 && ovCols <= 13 && ovRows === 6 ? 'PASS' : 'FAIL';

  // 6. 命中统计覆盖全部维度
  const dims = ['方向(首选+次选)', '方向(仅首选)', '让球(首选+次选)', '让球(仅首选)', '总进球TOP2', '半全场TOP3', '比分TOP5', '半场比分TOP3', '大小球方向', '大小球六档'];
  const missDims = dims.filter(d => !md.includes(d));
  out.counts.missing_stats_dimensions = missDims;
  out.checks.stats_dimensions = missDims.length === 0 ? 'PASS' : 'FAIL';

  // 7. ★★/★/☆ 分档
  out.checks.tier_split = /^\| ★★ \|/m.test(md) && /^\| ★ \|/m.test(md) && /^\| ☆ \|/m.test(md) ? 'PASS' : 'FAIL';

  // 8. 串关逐注核对
  const pStart = lines.findIndex(l => /^## 串关回测/.test(l));
  let pEnd = lines.length;
  for (let j = pStart + 1; j < lines.length; j++) { if (/^## /.test(lines[j])) { pEnd = j; break; } }
  const pLines = lines.slice(pStart, pEnd);
  const pRows = pLines.filter(l => /^\| (方向串|稳健让球串|价值让球串|半全场串|方向\+半全场|连续编号混合串|总进球串|总进球连续|高赔半全场|半全场混合总进球|比分串|比分单挑)/.test(l.trim())).length;
  const pBody = pLines.join('\n');
  out.counts.parlay_rows = pRows;
  out.checks.parlay_audit = pRows >= 23 && /注数命中率/.test(pBody) && /ROI/.test(pBody) && /6\/23/.test(pBody) ? 'PASS' : 'FAIL';

  // 9. 模拟盘：正文只留一行指引（AGENTS 82§4；模板为七章），并交叉台账结算完整性（M12）
  const ledgerChapters = chapters.filter(c => c.includes('模拟盘'));
  const betIdMentions = (md.match(/20261112-\d{2}/g) || []).length;
  const pointerLines = lines.filter(l => l.includes('kelly_sim_ledger.json'));
  const pointerOk = ledgerChapters.length === 0 && betIdMentions === 0 && pointerLines.length >= 1 && /虚构/.test(pointerLines.join(''));

  let ledgerOk = false;
  const ledgerInfo = {};
  try {
    const led = JSON.parse(fs.readFileSync(path.join(root, 'reports/sim/kelly_sim_ledger.json'), 'utf8'));
    const days = Array.isArray(led.days) ? led.days : [];
    const bets = days.reduce((acc, d) => acc.concat(d.bets || []), []);
    const unsettled = bets.filter(b => b.settled !== true);
    const incomplete = bets.filter(b => !b.official_score || typeof b.hit !== 'boolean' || typeof b.payout !== 'number');
    const last = days[days.length - 1] || {};
    const dayBets = last.bets || [];
    const sum = (arr, k) => Math.round(arr.reduce((s, x) => s + (Number(x[k]) || 0), 0) * 100) / 100;
    const near = (a, b, tol = 0.02) => Math.abs((Number(a) || 0) - (Number(b) || 0)) <= tol;
    const stakeSum = sum(dayBets, 'stake');
    const payoutSum = sum(dayBets, 'payout');
    ledgerInfo.bets_total = bets.length;
    ledgerInfo.unsettled_count = unsettled.length;
    ledgerInfo.unsettled_ids = unsettled.map(b => b.bet_id || b.id || b.match_num);
    ledgerInfo.incomplete_ids = incomplete.map(b => b.bet_id || b.id || b.match_num);
    ledgerInfo.audit_unsettled = led.settlement_audit ? led.settlement_audit.unsettled_remaining : null;
    ledgerInfo.last_day = {
      date: last.date,
      staked_total: last.staked_total, stake_sum: stakeSum,
      payout_total: last.payout_total, payout_sum: payoutSum,
      profit: last.profit, profit_sum: Math.round((payoutSum - stakeSum) * 100) / 100,
      balance_chain: Math.round(((Number(last.start_balance) || 0) + (Number(last.profit) || 0)) * 100) / 100,
      end_balance: last.end_balance
    };
    ledgerInfo.top_balance = led.balance;
    ledgerOk = unsettled.length === 0 && incomplete.length === 0 &&
      Number(ledgerInfo.audit_unsettled) === 0 && ledgerInfo.audit_unsettled !== null &&
      near(led.balance, last.end_balance) &&
      near(last.staked_total, stakeSum) && near(last.payout_total, payoutSum) &&
      near(last.profit, payoutSum - stakeSum) &&
      near((Number(last.start_balance) || 0) + (Number(last.profit) || 0), last.end_balance);
  } catch (e) {
    ledgerInfo.error = e.message;
  }
  out.counts.settlement_ledger = {
    pointer: { ledger_chapters: ledgerChapters, bet_id_mentions: betIdMentions, pointer_lines: pointerLines.length, is_virtual: /虚构/.test(pointerLines.join('')) },
    ledger: ledgerInfo
  };
  out.checks.settlement_ledger = pointerOk && ledgerOk ? 'PASS' : 'FAIL';

  // 10. 官方赛果来源
  out.checks.official_source = /体彩官方/.test(md) && /getUniformMatchResultV1/.test(md) && /待结算\s*0\s*场/.test(md) ? 'PASS' : 'FAIL';

  // 11. 无分割线
  out.counts.hr_count = lines.filter(l => l.trim() === '---').length;
  out.checks.no_hr = out.counts.hr_count === 0 ? 'PASS' : 'FAIL';

  // 12. 无「规则XX」表述
  const ruleHits = [];
  lines.forEach((l, i) => { if (/规则\d/.test(l)) ruleHits.push({ line: i + 1, text: l.trim().slice(0, 60) }); });
  out.counts.rule_mentions = ruleHits;
  out.checks.no_rule_xx = ruleHits.length === 0 ? 'PASS' : 'FAIL';

  // 13. 表格列数 ≤14
  const wide = [];
  lines.forEach((l, i) => {
    if (/^\|.*\|$/.test(l.trim())) {
      const cols = l.trim().replace(/^\||\|$/g, '').split('|').length;
      if (cols > 14) wide.push({ line: i + 1, cols, text: l.trim().slice(0, 60) });
    }
  });
  out.counts.wide_tables = wide;
  out.checks.table_columns = wide.length === 0 ? 'PASS' : 'FAIL';

  // 14. 结尾话术与模板逐字比对
  let closing = 'PASS';
  try {
    const tpl = fs.readFileSync(path.join(root, 'templates/closing_remarks.md'), 'utf8').replace(/\r/g, '');
    const tail = md.split(/## ☕ 写在最后/)[1] || '';
    const norm = s => s.replace(/\s+/g, '');
    if (!norm(tpl).includes(norm(tail.slice(0, 60)))) closing = 'FAIL';
  } catch (e) { closing = 'FAIL'; }
  out.checks.closing = closing;

  out.warnings = [];
}

if (/^# 【回测】/.test(lines[0])) {
  runBacktest(md, lines, out);
  const failed = Object.entries(out.checks).filter(([, v]) => v === 'FAIL').map(([k]) => k);
  const warned = Object.entries(out.checks).filter(([, v]) => v === 'WARN').map(([k]) => k);
  out.summary = { total_checks: Object.keys(out.checks).length, failed_count: failed.length, failed, warned_count: warned.length, warned };
  console.log(JSON.stringify(out, null, 2));
  process.exit(0);
}

// 1. 标题
out.checks.title = /^# 【分析】.+（.+）\d+场.+ \| .+/.test(lines[0]) ? 'PASS' : 'FAIL';
out.counts.title_line = lines[0];
const WD = (lines[0].match(/（(周[一二三四五六日])）/) || [])[1] || '周四';
const RE_MATCH_HEAD = new RegExp('^## ' + WD + '\\d{3} ');
out.counts.weekday = WD;

// 2. 开头固定块顺序
const headKeys = ['报告说明', '风险提示', '免责声明', '近5日置信度命中率', '每日更新'];
const headPos = headKeys.map(k => lines.findIndex(l => l.includes(k)));
const headSorted = headPos.every((p, i) => p >= 0 && (i === 0 || p > headPos[i - 1]));
out.checks.header_block = headSorted ? 'PASS' : 'FAIL';
out.counts.header_positions = Object.fromEntries(headKeys.map((k, i) => [k, headPos[i]]));

// 3. 顶层章
const chapters = lines.filter(l => /^## /.test(l)).map(l => l.replace(/^## /, '').trim());
out.counts.chapters = chapters;
const expected = ['总览', '综合推荐汇总', '搏冷推荐汇总', '串关思路', '本轮规律', '写在最后'];
const missing = expected.filter(e => !chapters.some(c => c.includes(e)));
const extra = chapters.filter(c => !expected.some(e => c.includes(e)) && !RE_MATCH_HEAD.test('## ' + c));
out.checks.chapter_order = missing.length === 0 && extra.length === 0 ? 'PASS' : 'FAIL';
out.counts.missing_chapters = missing;
out.counts.extra_chapters = extra;

// 4. 逐场 8 部分 + 附项
const matchHead = chapters.filter(c => RE_MATCH_HEAD.test('## ' + c));
const sections = [];
for (let i = 0; i < lines.length; i++) {
  if (RE_MATCH_HEAD.test(lines[i])) {
    let end = lines.length;
    for (let j = i + 1; j < lines.length; j++) if (/^## /.test(lines[j])) { end = j; break; }
    sections.push({ title: lines[i].replace(/^## /, ''), body: lines.slice(i, end).join('\n') });
  }
}
const parts = [
  ['联赛等级', /联赛等级/], ['场地天气', /⏰ \d{2}:\d{2}.*🏟/], ['基本面', /FIFA|组前 \d 轮|Elo/],
  ['身价', /身价对比/], ['伤停', /伤停/], ['模型vs市场', /模型 vs 市场/],
  ['比分推演', /比分推演/], ['推荐表', /\| \*\*比分TOP5\*\*/], ['置信度', /置信度：/],
  ['净胜球众数', /净胜球众数/]
];
out.counts.per_match = sections.map(s => {
  const miss = parts.filter(([, re]) => !re.test(s.body)).map(([n]) => n);
  return { match: s.title, missing_parts: miss };
});
out.checks.per_match_parts = out.counts.per_match.every(m => m.missing_parts.length === 0) ? 'PASS' : 'FAIL';

// 5. 推荐表行序（6行）
out.counts.reco_row_order = sections.map(s => {
  const tablePart = s.body.split('**推荐：**')[1] || '';
  const rows = ['比分TOP5', '半全场TOP3', 'HAD', 'HAFU', '大小球·总进球', '半场比分']
    .map(k => tablePart.indexOf(k));
  return { match: s.title, six_rows: rows.every(v => v > 0), ascending: rows.every((v, i) => i === 0 || v > rows[i - 1]) };
});
out.checks.reco_table = out.counts.reco_row_order.every(r => r.six_rows && r.ascending) ? 'PASS' : 'FAIL';

// 6. 表格列数
const wide = [];
let tableCount = 0;
lines.forEach((l, i) => {
  if (/^\|.*\|$/.test(l.trim())) {
    const cols = l.trim().replace(/^\||\|$/g, '').split('|').length;
    if (cols > 1) tableCount++;
    if (cols > 7) wide.push({ line: i + 1, cols, text: l.trim().slice(0, 60) });
  }
});
out.counts.tables = tableCount;
out.counts.wide_tables = wide;
out.checks.table_columns = wide.length === 0 ? 'PASS' : 'FAIL';

// 7. 格式禁令
out.counts.hr_count = lines.filter(l => l.trim() === '---').length;
out.checks.no_hr = out.counts.hr_count === 0 ? 'PASS' : 'FAIL';
const ruleHits = [];
lines.forEach((l, i) => { if (/规则\d/.test(l)) ruleHits.push({ line: i + 1, text: l.trim().slice(0, 60) }); });
out.counts.rule_mentions = ruleHits;
out.checks.no_rule_xx = ruleHits.length === 0 ? 'PASS' : 'FAIL';

// 8. 单关三处（仅当本期存在单关场时校验；无单关则校验「已声明未开单关」）
const singleNum = (md.match(new RegExp('(' + WD + '\\d{3}) 为单关场')) || [])[1];
let single;
if (singleNum) {
  single = {
    header: /单关/.test(lines.slice(0, 20).join('\n')),
    overview_note: new RegExp(singleNum + ' 为单关场').test(md),
    match_section: new RegExp(singleNum).test(md) && /bettingSingle/.test(sections.find(s => s.title.startsWith(singleNum))?.body || '')
  };
} else {
  single = { no_single_declared: /bettingSingle=0/.test(md) && /未开单关/.test(md) };
}
out.counts.single_001 = single;
out.counts.single_number = singleNum || null;
out.checks.single_001_three_places = Object.values(single).every(Boolean) ? 'PASS' : 'FAIL';

// 9. 串关小节与方案计数
const sub = {};
for (const name of ['方向串（胜平负）', '让球串（让球胜平负）', '混合串（半全场+方向混合）', '娱乐串（高赔率组合）']) {
  sub[name] = md.includes('### ' + name);
}
const ent = ['高赔总进球串', '高赔半全场串', '半全场混合总进球串', '比分串'];
out.counts.entertainment_subcats = Object.fromEntries(ent.map(e => [e, md.includes('#### ' + e)]));
out.checks.link_sections = Object.values(sub).every(Boolean) && Object.values(out.counts.entertainment_subcats).every(Boolean) ? 'PASS' : 'FAIL';
out.counts.french_league_note = /已按 L71 排除法甲/.test(md);

// 10. 写在最后：与模板逐字比对
let closing = 'PASS';
try {
  const tpl = fs.readFileSync(path.join(root, 'templates/closing_remarks.md'), 'utf8');
  const tail = md.split(/## ☕ 写在最后/)[1] || '';
  const tplBody = tpl.replace(/\r/g, '');
  const norm = s => s.replace(/\s+/g, '');
  if (!norm(tplBody).includes(norm(tail.slice(0, 60)))) closing = 'FAIL';
} catch (e) { closing = 'FAIL'; }
out.checks.closing = closing;

// 11. 模拟盘仅一行指引
out.checks.sim_one_line = /虚拟本金凯利模拟盘注单见/.test(md) && !/^## .*模拟盘/.test(md) ? 'PASS' : 'FAIL';

// 12. 关键信息完整性：场地/天气/身价/伤停/首发（全缺失 FAIL，≥3 项缺失 WARN）
const infoKeys = [
  ['场地', b => !/🏟/.test(b) || /场地信息缺失/.test(b)],
  ['天气', b => !/(⛅|🌫|🌦|🌧|🌙|☁|☀|❄|⛈)/.test(b) || /天气信息缺失/.test(b)],
  ['身价', b => !/身价/.test(b) || /身价[^\n]{0,40}(信息缺失|未取得)/.test(b)],
  ['伤停', b => !/伤停/.test(b) || /伤停[^\n]{0,80}(信息缺失|未取得)/.test(b)],
  ['首发', b => !/首发/.test(b) || /首发[^\n]{0,60}(信息缺失|未取得|未公布)/.test(b)]
];
out.counts.info_completeness = sections.map(s => {
  const miss = infoKeys.filter(([, fn]) => fn(s.body)).map(([n]) => n);
  const level = miss.length === infoKeys.length ? 'FAIL' : (miss.length >= 3 ? 'WARN' : 'PASS');
  return { match: s.title, missing: miss, level, missing_word_count: (s.body.match(/信息缺失/g) || []).length };
});
const lv = out.counts.info_completeness.map(x => x.level);
out.checks.info_completeness = lv.includes('FAIL') ? 'FAIL' : (lv.includes('WARN') ? 'WARN' : 'PASS');
out.warnings = out.counts.info_completeness
  .filter(x => x.level !== 'PASS')
  .map(x => `${x.match}: 关键信息缺 ${x.missing.length}/5（${x.missing.join('、')}）→ ${x.level}`);

// 汇总
const failed = Object.entries(out.checks).filter(([, v]) => v === 'FAIL').map(([k]) => k);
const warned = Object.entries(out.checks).filter(([, v]) => v === 'WARN').map(([k]) => k);
out.summary = { total_checks: Object.keys(out.checks).length, failed_count: failed.length, failed, warned_count: warned.length, warned };

console.log(JSON.stringify(out, null, 2));
