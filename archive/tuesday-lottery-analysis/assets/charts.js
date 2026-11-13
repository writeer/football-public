// charts.js - ECharts configurations for Tuesday Lottery Analysis Report
// Color scheme matching the dark pitch-green theme
(function() {
  'use strict';

  var C = {
    bg: '#1a2f1d',
    ink: '#e8e8e0',
    muted: '#8a9a85',
    rule: '#2a3f2a',
    accent: '#4ade80',
    accent2: '#f59e0b',
    home: '#4ade80',
    draw: '#f59e0b',
    away: '#f87171',
    over: '#f87171',
    under: '#4ade80'
  };

  var textStyle = { color: C.muted, fontSize: 11, fontFamily: 'system-ui,sans-serif' };
  var titleStyle = { color: C.ink, fontSize: 13, fontWeight: 'bold', fontFamily: 'system-ui,sans-serif' };

  // ========== CHART: Overview (Horizontal grouped bar) ==========
  (function() {
    var dom = document.getElementById('chart-overview');
    if (!dom) return;
    var chart = echarts.init(dom);
    var matches = ['201 济州vs江原', '202 全北vs大田', '203 蔚山vs仁川', '204 米内罗vs巴伊亚', '205 萨巴赫vs库奥皮奥', '206 奥胡斯vs波兹南', '207 格拉茨vs哈茨'];
    var home = [28.8, 47.1, 40.1, 43.7, 39.5, 31.3, 61.0];
    var draw = [30.0, 27.1, 30.4, 28.4, 30.3, 27.7, 23.6];
    var away = [41.2, 25.8, 29.5, 27.9, 30.2, 41.0, 15.3];

    chart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: C.bg, borderColor: C.rule, textStyle: { color: C.ink, fontSize: 12 } },
      legend: { bottom: 0, textStyle: { color: C.muted, fontSize: 11 }, data: ['主胜', '平局', '客胜'], itemGap: 24 },
      grid: { left: '3%', right: '4%', bottom: '12%', top: '8%', containLabel: true },
      xAxis: { type: 'value', max: 100, axisLabel: { color: C.muted, formatter: '{value}%' }, splitLine: { lineStyle: { color: C.rule, type: 'dashed' } }, axisLine: { lineStyle: { color: C.rule } } },
      yAxis: { type: 'category', data: matches, axisLabel: { color: C.ink, fontSize: 11 }, axisLine: { lineStyle: { color: C.rule } }, axisTick: { show: false } },
      series: [
        { name: '主胜', type: 'bar', data: home, itemStyle: { color: C.home, borderRadius: [0, 4, 4, 0] }, barGap: '10%', label: { show: true, position: 'right', color: C.home, fontSize: 10, formatter: function(p) { return p.value > 8 ? p.value + '%' : ''; } } },
        { name: '平局', type: 'bar', data: draw, itemStyle: { color: C.draw, borderRadius: [0, 4, 4, 0] }, label: { show: true, position: 'right', color: C.draw, fontSize: 10, formatter: function(p) { return p.value > 8 ? p.value + '%' : ''; } } },
        { name: '客胜', type: 'bar', data: away, itemStyle: { color: C.away, borderRadius: [0, 4, 4, 0] }, label: { show: true, position: 'right', color: C.away, fontSize: 10, formatter: function(p) { return p.value > 8 ? p.value + '%' : ''; } } }
      ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

  // ========== Score distribution charts for each match ==========
  var scoreData = {
    '201': { scores: ['0-1','1-1','1-0','0-0','0-2','2-1','2-0','1-2','2-2','3-0'], probs: [14.4,12.6,11.1,10.8,10.5,8.7,8.2,6.5,5.4,4.2] },
    '202': { scores: ['1-0','1-1','0-1','2-0','0-0','2-1','1-2','0-2','3-0','2-2'], probs: [13.5,11.9,9.8,9.2,8.8,8.3,7.5,6.9,5.6,5.0] },
    '203': { scores: ['1-0','1-1','0-1','0-0','2-0','2-1','1-2','0-2','2-2','3-0'], probs: [14.5,13.0,12.0,11.5,9.0,8.0,7.5,6.5,5.5,4.5] },
    '204': { scores: ['1-0','1-1','0-1','2-0','0-0','2-1','1-2','0-2','2-2','3-0'], probs: [13.7,12.4,10.7,9.8,9.2,8.5,7.8,7.0,5.8,5.2] },
    '205': { scores: ['1-0','1-1','0-0','0-1','2-0','0-2','2-1','1-2','2-2','3-0'], probs: [14.4,13.1,12.0,10.5,9.5,8.5,8.0,7.0,5.5,4.5] },
    '206': { scores: ['1-1','0-1','1-0','0-0','2-1','1-2','0-2','2-0','2-2','3-0'], probs: [12.3,12.2,10.0,9.8,9.5,8.8,8.0,7.5,6.5,5.5] },
    '207': { scores: ['1-0','2-0','1-1','0-0','3-0','2-1','0-1','3-1','2-2','4-0'], probs: [16.5,13.9,9.7,9.0,8.5,8.0,6.5,6.0,5.5,5.0] }
  };

  Object.keys(scoreData).forEach(function(id) {
    var dom = document.getElementById('chart-scores-' + id);
    if (!dom) return;
    var chart = echarts.init(dom);
    var d = scoreData[id];
    var yData = d.scores.slice().reverse();
    var xData = d.probs.slice().reverse();

    var colors = yData.map(function(s) {
      var parts = s.split('-');
      var h = parseInt(parts[0]), a = parseInt(parts[1]);
      if (h > a) return C.home;
      if (h < a) return C.away;
      return C.draw;
    });

    chart.setOption({
      backgroundColor: 'transparent',
      title: { text: '比分概率分布', left: 'center', textStyle: { color: C.ink, fontSize: 12, fontWeight: 'bold' } },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: C.bg, borderColor: C.rule, textStyle: { color: C.ink, fontSize: 12 }, formatter: function(p) { return p[0].name + ': ' + p[0].value + '%'; } },
      grid: { left: '12%', right: '8%', top: '14%', bottom: '4%', containLabel: true },
      xAxis: { type: 'value', max: 20, axisLabel: { color: C.muted, formatter: '{value}%' }, splitLine: { lineStyle: { color: C.rule, type: 'dashed' } }, axisLine: { lineStyle: { color: C.rule } } },
      yAxis: { type: 'category', data: yData, axisLabel: { color: C.ink, fontSize: 11, fontWeight: 'bold' }, axisLine: { lineStyle: { color: C.rule } }, axisTick: { show: false } },
      series: [{
        type: 'bar', data: xData.map(function(v, i) { return { value: v, itemStyle: { color: colors[i], borderRadius: [0, 4, 4, 0] } }; }),
        barWidth: '60%',
        label: { show: true, position: 'right', color: C.muted, fontSize: 10, formatter: '{c}%' }
      }]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  });

  // ========== CHART: Over/Under Comparison ==========
  (function() {
    var dom = document.getElementById('chart-over-under');
    if (!dom) return;
    var chart = echarts.init(dom);
    var matches = ['201 济州vs江原', '202 全北vs大田', '203 蔚山vs仁川', '204 米内罗vs巴伊亚', '205 萨巴赫vs库奥皮奥', '206 奥胡斯vs波兹南', '207 格拉茨vs哈茨'];
    var over = [37.7, 43.0, 35.0, 40.4, 35.0, 44.3, 43.0];
    var under = [62.3, 57.0, 65.0, 59.6, 65.0, 55.7, 57.0];
    var lines = ['2.25', '2.5', '2.25', '2.5', '2.25', '2.5', '2.75'];

    chart.setOption({
      backgroundColor: 'transparent',
      title: { text: '大小球预测概率对比', left: 'center', textStyle: { color: C.ink, fontSize: 13, fontWeight: 'bold' } },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: C.bg, borderColor: C.rule, textStyle: { color: C.ink, fontSize: 12 }, formatter: function(ps) { var r = ps[0].name + '<br/>'; ps.forEach(function(p) { r += p.marker + p.seriesName + ': ' + p.value + '%<br/>'; }); return r + '盘口线: ' + lines[ps[0].dataIndex]; } },
      legend: { bottom: 0, textStyle: { color: C.muted, fontSize: 11 }, data: ['大球', '小球'], itemGap: 32 },
      grid: { left: '3%', right: '4%', bottom: '14%', top: '12%', containLabel: true },
      xAxis: { type: 'category', data: matches, axisLabel: { color: C.ink, fontSize: 10, rotate: 25 }, axisLine: { lineStyle: { color: C.rule } }, axisTick: { show: false } },
      yAxis: { type: 'value', max: 100, axisLabel: { color: C.muted, formatter: '{value}%' }, splitLine: { lineStyle: { color: C.rule, type: 'dashed' } }, axisLine: { lineStyle: { color: C.rule } } },
      series: [
        { name: '大球', type: 'bar', data: over, itemStyle: { color: C.over, borderRadius: [6, 6, 0, 0] }, barWidth: '40%', label: { show: true, position: 'top', color: C.over, fontSize: 10, formatter: '{c}%' } },
        { name: '小球', type: 'bar', data: under, itemStyle: { color: C.under, borderRadius: [6, 6, 0, 0] }, barWidth: '40%', label: { show: true, position: 'top', color: C.under, fontSize: 10, formatter: '{c}%' } }
      ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

  // ========== CHART: Radar - Model Consistency ==========
  (function() {
    var dom = document.getElementById('chart-radar');
    if (!dom) return;
    var chart = echarts.init(dom);

    // Using the standard deviation of model predictions as a measure of consensus
    // Lower std = higher consensus. We'll flip it: consensus = 100 - std*10
    var matchLabels = ['201 济州vs江原', '202 全北vs大田', '203 蔚山vs仁川', '204 米内罗vs巴伊亚', '205 萨巴赫vs库奥皮奥', '206 奥胡斯vs波兹南', '207 格拉茨vs哈茨'];

    // Compute std dev for each match's home/draw/away predictions
    // 201: home [28.7,28.9,28.1,27.2,32.1] std=1.87, draw [27.6,28.5,28.7,33.1,29.4] std=2.17, away [43.7,42.6,43.2,39.8,38.5] std=2.29
    // 202: home [46.9,45.4,46.1,41.2,49.9] std=3.13, draw [25.4,26.7,27.0,32.6,26.6] std=2.86, away [27.6,27.9,26.9,26.2,23.5] std=1.72
    // 203: home [40.6,39.9,40.2,35.4,42.9] std=2.72, draw [29.0,29.5,29.8,36.1,28.8] std=3.07, away [30.4,30.5,30.0,28.5,28.4] std=1.04
    // 204: home [44.1,42.8,43.4,38.6,45.0] std=2.45, draw [26.7,27.6,28.0,33.7,28.0] std=2.76, away [29.3,29.6,28.6,27.8,27.0] std=1.10
    // 205: home [40.5,40.1,40.2,38.4,39.9] std=0.83, draw [29.2,29.6,29.8,32.3,29.6] std=1.25, away [30.3,30.4,30.0,29.3,30.6] std=0.51
    // 206: home [31.0,31.1,30.5,29.6,33.1] std=1.28, draw [26.0,26.7,27.1,30.6,28.0] std=1.78, away [43.0,42.2,42.5,39.8,38.9] std=1.84
    // 207: home [64.5,61.9,63.9,58.7,59.2] std=2.63, draw [21.5,23.5,22.7,27.8,24.1] std=2.39, away [14.0,14.6,13.3,13.5,16.7] std=1.41

    // Consensus score: inverse of average std dev, scaled to 0-100
    var avgStd = [2.11, 2.57, 2.28, 2.10, 0.86, 1.63, 2.14];
    var consensus = avgStd.map(function(s) { return Math.max(0, Math.min(100, 100 - s * 20)); });

    chart.setOption({
      backgroundColor: 'transparent',
      title: { text: '模型预测一致性评分 (越高越一致)', left: 'center', textStyle: { color: C.ink, fontSize: 13, fontWeight: 'bold' } },
      tooltip: { trigger: 'axis', backgroundColor: C.bg, borderColor: C.rule, textStyle: { color: C.ink, fontSize: 12 } },
      grid: { left: '3%', right: '4%', bottom: '8%', top: '14%', containLabel: true },
      xAxis: { type: 'category', data: matchLabels, axisLabel: { color: C.ink, fontSize: 10, rotate: 25 }, axisLine: { lineStyle: { color: C.rule } }, axisTick: { show: false } },
      yAxis: { type: 'value', max: 100, axisLabel: { color: C.muted, formatter: '{value}' }, splitLine: { lineStyle: { color: C.rule, type: 'dashed' } }, axisLine: { lineStyle: { color: C.rule } } },
      series: [{
        type: 'bar',
        data: consensus.map(function(v, i) {
          var color = v >= 70 ? C.home : (v >= 50 ? C.draw : C.away);
          return { value: v, itemStyle: { color: color, borderRadius: [6, 6, 0, 0] } };
        }),
        barWidth: '50%',
        label: { show: true, position: 'top', color: C.muted, fontSize: 10, formatter: '{c}' },
        markLine: {
          silent: true,
          data: [{ yAxis: 70, name: '高一致', lineStyle: { color: C.home, type: 'dashed', width: 1.5 }, label: { color: C.home, fontSize: 10, formatter: '高一致' } },
                 { yAxis: 50, name: '中等', lineStyle: { color: C.draw, type: 'dashed', width: 1.5 }, label: { color: C.draw, fontSize: 10, formatter: '中等' } }]
        }
      }]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  })();

})();