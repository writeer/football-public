const fs = require('fs');
const filePath = 'e:\\VibeCoding\\football\\reports\\analysis\\20260830_sunday_analysis_zhihu.md';
let content = fs.readFileSync(filePath, 'utf8');
let lines = content.split('\n');
let changes = 0;

// 1. Replace half-time/full-time format: 胜/胜 → 胜胜, 平/负 → 平负, etc.
//    Only in recommendation table rows and deduction text
lines = lines.map(line => {
  let original = line;
  // Replace X/Y format for half-full results (胜/胜, 平/负, etc.)
  line = line.replace(/(胜|平|负)\/(胜|平|负)/g, '$1$2');
  if (line !== original) changes++;
  return line;
});

// 2. Replace score format: **X:Y** → **X-Y** (in CRS TOP5 rows)
lines = lines.map(line => {
  let original = line;
  // Replace bold scores like **1:2** → **1-2**
  line = line.replace(/\*\*(\d):(\d+)\*\*/g, '**$1-$2**');
  if (line !== original) changes++;
  return line;
});

// 3. Replace half-time score format: X:Y( → X-Y( (in half-time score rows)
lines = lines.map(line => {
  let original = line;
  // Replace half-time scores like 0:1(15%) → 0-1(15%)
  // Only match pattern digit:digit( which is specific to score+probability
  line = line.replace(/(\d):(\d)\(/g, '$1-$2(');
  if (line !== original) changes++;
  return line;
});

// 4. Remove standalone --- divider lines (template says no dividers for zhihu)
lines = lines.map(line => {
  if (line.trim() === '---') {
    changes++;
    return ''; // Replace with empty line
  }
  return line;
});

// 5. Clean up multiple consecutive empty lines (max 2)
let result = [];
let emptyCount = 0;
for (let line of lines) {
  if (line.trim() === '') {
    emptyCount++;
    if (emptyCount <= 2) result.push(line);
  } else {
    emptyCount = 0;
    result.push(line);
  }
}

content = result.join('\n');
fs.writeFileSync(filePath, content, 'utf8');
console.log('Format fixes applied. Lines changed: ' + changes);
console.log('Total lines after cleanup: ' + result.length);
