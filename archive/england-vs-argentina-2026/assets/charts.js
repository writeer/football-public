(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var eng = style.getPropertyValue('--eng').trim();
  var arg = style.getPropertyValue('--arg').trim();
  var draw = style.getPropertyValue('--draw').trim();

  // --- Chart 1: Model Comparison ---
  var chart1 = echarts.init(document.getElementById('chart-models'), null, { renderer: 'svg' });
  var models = ['DC\u4fee\u6b63\u6cca\u677e', '\u8d1f\u4e8c\u9879\u5206\u5e03', 'ZIP\u96f6\u81a8\u80c0\u6cca\u677e', '\u53cc\u53d8\u91cf\u6cca\u677e', 'Skellam', '\u8499\u7279\u5361\u6d1b', 'Opta\u8d85\u7b97', 'Elo/Pi', '\u52a0\u6743\u878d\u5408'];
  var engData = [36.0, 35.5, 34.9, 34.5, 34.7, 36.3, 39.1, 42.0, 37.4];
  var drawData = [23.4, 25.1, 26.0, 26.4, 25.8, 23.4, 29.3, 28.0, 26.3];
  var argData = [40.6, 39.4, 39.1, 39.1, 39.3, 40.3, 31.6, 30.0, 36.3];

  chart1.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true, backgroundColor: bg2, borderColor: rule, textStyle: { color: ink, fontSize: 12 } },
    legend: { data: ['\u82f1\u683c\u5170\u80dc', '\u5e73\u5c40', '\u963f\u6839\u5ef7\u80dc'], top: 0, textStyle: { color: muted, fontSize: 11 }, itemWidth: 14, itemHeight: 8 },
    grid: { left: 100, right: 30, top: 40, bottom: 20 },
    xAxis: { type: 'value', max: 50, axisLabel: { color: muted, fontSize: 11, formatter: '{value}%' }, axisLine: { lineStyle: { color: rule } }, splitLine: { lineStyle: { color: rule, type: 'dashed' } } },
    yAxis: { type: 'category', data: models, axisLabel: { color: muted, fontSize: 11 }, axisLine: { lineStyle: { color: rule } }, axisTick: { show: false } },
    series: [
      { name: '\u82f1\u683c\u5170\u80dc', type: 'bar', stack: 'total', data: engData, itemStyle: { color: eng }, barWidth: 14, emphasis: { focus: 'series' } },
      { name: '\u5e73\u5c40', type: 'bar', stack: 'total', data: drawData, itemStyle: { color: draw }, emphasis: { focus: 'series' } },
      { name: '\u963f\u6839\u5ef7\u80dc', type: 'bar', stack: 'total', data: argData, itemStyle: { color: arg }, emphasis: { focus: 'series' } }
    ]
  });
  window.addEventListener('resize', function() { chart1.resize(); });

  // --- Chart 2: Score Top 10 ---
  var chart2 = echarts.init(document.getElementById('chart-scores'), null, { renderer: 'svg' });
  var scores = ['1-1', '0-1', '1-0', '1-2', '2-1', '0-0', '0-2', '2-0', '2-2', '1-3'];
  var scoreProbs = [11.1, 10.4, 9.7, 8.1, 7.6, 6.7, 6.7, 5.8, 5.4, 3.9];
  var scoreColors = scores.map(function(s) {
    var h = parseInt(s[0]), a = parseInt(s[2]);
    if (h > a) return eng;
    if (h < a) return arg;
    return draw;
  });

  chart2.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true, backgroundColor: bg2, borderColor: rule, textStyle: { color: ink, fontSize: 12 }, formatter: function(p) { return p[0].name + ': ' + p[0].value + '%'; } },
    grid: { left: 60, right: 40, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: scores, axisLabel: { color: ink, fontSize: 13, fontWeight: 700, fontFamily: 'BigShoulders, sans-serif' }, axisLine: { lineStyle: { color: rule } }, axisTick: { show: false } },
    yAxis: { type: 'value', max: 14, axisLabel: { color: muted, fontSize: 11, formatter: '{value}%' }, axisLine: { lineStyle: { color: rule } }, splitLine: { lineStyle: { color: rule, type: 'dashed' } } },
    series: [{
      type: 'bar',
      data: scoreProbs.map(function(v, i) { return { value: v, itemStyle: { color: scoreColors[i] } }; }),
      barWidth: 28,
      label: { show: true, position: 'top', color: muted, fontSize: 10, formatter: '{c}%' }
    }]
  });
  window.addEventListener('resize', function() { chart2.resize(); });

  // --- Chart 3: Total Goals ---
  var chart3 = echarts.init(document.getElementById('chart-goals'), null, { renderer: 'svg' });
  var goalLabels = ['0\u7403', '1\u7403', '2\u7403', '3\u7403', '4\u7403', '4+\u7403'];
  var poissonG = [6.7, 18.1, 24.5, 22.0, 14.9, 28.6];
  var nbG = [11.5, 20.2, 21.3, 17.4, 12.2, 29.5];
  var zipG = [14.2, 16.7, 22.5, 20.3, 13.7, 26.3];
  var mcG = [5.1, 20.6, 23.5, 21.7, 15.4, 29.0];
  var recG = [9.4, 18.9, 23.0, 20.4, 14.1, 28.4];

  chart3.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true, backgroundColor: bg2, borderColor: rule, textStyle: { color: ink, fontSize: 12 } },
    legend: { data: ['\u6cca\u677e', '\u8d1f\u4e8c\u9879', 'ZIP', '\u8499\u7279\u5361\u6d1b', '\u63a8\u8350'], top: 0, textStyle: { color: muted, fontSize: 11 }, itemWidth: 14, itemHeight: 8 },
    grid: { left: 45, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: goalLabels, axisLabel: { color: ink, fontSize: 12 }, axisLine: { lineStyle: { color: rule } }, axisTick: { show: false } },
    yAxis: { type: 'value', max: 35, axisLabel: { color: muted, fontSize: 11, formatter: '{value}%' }, axisLine: { lineStyle: { color: rule } }, splitLine: { lineStyle: { color: rule, type: 'dashed' } } },
    series: [
      { name: '\u6cca\u677e', type: 'line', data: poissonG, smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { width: 2, color: muted }, itemStyle: { color: muted } },
      { name: '\u8d1f\u4e8c\u9879', type: 'line', data: nbG, smooth: true, symbol: 'diamond', symbolSize: 6, lineStyle: { width: 2, color: accent2 + '99' }, itemStyle: { color: accent2 + '99' } },
      { name: 'ZIP', type: 'line', data: zipG, smooth: true, symbol: 'triangle', symbolSize: 6, lineStyle: { width: 2, color: draw }, itemStyle: { color: draw } },
      { name: '\u8499\u7279\u5361\u6d1b', type: 'line', data: mcG, smooth: true, symbol: 'rect', symbolSize: 5, lineStyle: { width: 2, color: arg + '99', type: 'dashed' }, itemStyle: { color: arg + '99' } },
      { name: '\u63a8\u8350', type: 'bar', data: recG, barWidth: 20, itemStyle: { color: accent, opacity: 0.25 }, label: { show: true, position: 'top', color: accent, fontSize: 10, fontWeight: 700, formatter: '{c}%' } }
    ]
  });
  window.addEventListener('resize', function() { chart3.resize(); });

  // --- Chart 4: Half-Time/Full-Time ---
  var chart4 = echarts.init(document.getElementById('chart-htft'), null, { renderer: 'svg' });
  var htftLabels = ['\u5e73\u8d1f', '\u5e73\u80dc', '\u8d1f\u8d1f', '\u8d1f\u80dc', '\u80dc\u8d1f', '\u5e73\u5e73', '\u80dc\u80dc', '\u8d1f\u5e73', '\u80dc\u5e73'];
  var htftProbs = [17.57, 15.52, 12.29, 11.16, 10.47, 10.14, 9.59, 6.70, 6.56];
  var htftColors = htftLabels.map(function(l) {
    if (l === '\u5e73\u8d1f' || l === '\u8d1f\u8d1f' || l === '\u80dc\u8d1f') return arg;
    if (l === '\u5e73\u80dc' || l === '\u8d1f\u80dc' || l === '\u80dc\u80dc') return eng;
    return draw;
  });

  chart4.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true, backgroundColor: bg2, borderColor: rule, textStyle: { color: ink, fontSize: 12 }, formatter: function(p) { return p[0].name + ': ' + p[0].value + '%'; } },
    grid: { left: 55, right: 40, top: 15, bottom: 35 },
    xAxis: { type: 'category', data: htftLabels, axisLabel: { color: ink, fontSize: 12, fontWeight: 700, fontFamily: 'BigShoulders, sans-serif' }, axisLine: { lineStyle: { color: rule } }, axisTick: { show: false } },
    yAxis: { type: 'value', max: 20, axisLabel: { color: muted, fontSize: 11, formatter: '{value}%' }, axisLine: { lineStyle: { color: rule } }, splitLine: { lineStyle: { color: rule, type: 'dashed' } } },
    series: [{
      type: 'bar',
      data: htftProbs.map(function(v, i) { return { value: v, itemStyle: { color: htftColors[i] } }; }),
      barWidth: 24,
      label: { show: true, position: 'top', color: muted, fontSize: 10, formatter: '{c}%' }
    }]
  });
  window.addEventListener('resize', function() { chart4.resize(); });
})();