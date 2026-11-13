(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var blue = style.getPropertyValue('--blue').trim();

  // ===== Chart 1: Probability Comparison =====
  var chart1 = echarts.init(document.getElementById('chart-compare'), null, { renderer: 'svg' });

  var matchNames = ['#208 利勒vsKFUM', '#204 仁川vs全北', '#213 莫尔德vs布兰'];
  var directions = ['主胜', '客胜', '主胜'];

  var fusedProbs = [63.7, 40.9, 60.8];
  var shinProbs = [57.8, 39.3, 56.1];

  chart1.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true },
    legend: {
      data: ['模型融合概率', 'Shin市场概率'],
      bottom: 0,
      textStyle: { color: ink, fontSize: 12 }
    },
    grid: { left: 100, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'value',
      max: 70,
      axisLabel: { color: muted, formatter: '{value}%' },
      splitLine: { lineStyle: { color: rule } },
      axisLine: { lineStyle: { color: rule } }
    },
    yAxis: {
      type: 'category',
      data: matchNames,
      axisLabel: { color: ink, fontSize: 13 },
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false }
    },
    series: [
      {
        name: 'Shin市场概率',
        type: 'bar',
        data: shinProbs.map(function(v, i) { return { value: v, name: directions[i] }; }),
        barWidth: 10,
        itemStyle: { color: accent2, borderRadius: [0, 3, 3, 0] },
        label: {
          show: true,
          position: 'right',
          color: accent2,
          fontSize: 11,
          formatter: '{c}%',
          fontWeight: 600
        },
        z: 1
      },
      {
        name: '模型融合概率',
        type: 'bar',
        data: fusedProbs.map(function(v, i) { return { value: v, name: directions[i] }; }),
        barWidth: 16,
        itemStyle: { color: accent, borderRadius: [0, 3, 3, 0] },
        label: {
          show: true,
          position: 'right',
          color: accent,
          fontSize: 12,
          formatter: '{c}%',
          fontWeight: 700
        },
        z: 2
      }
    ]
  });
  window.addEventListener('resize', function() { chart1.resize(); });

  // ===== Chart 2: Score Distribution Heatmap =====
  var chart2 = echarts.init(document.getElementById('chart-scores'), null, { renderer: 'svg' });

  var scores = ['0:0', '1:0', '2:0', '1:1', '2:1', '0:1', '0:2', '3:0', '1:2', '2:2'];

  var rawScores208 = [9.3, 16.0, 13.9, 9.1, 8.5, 5.9, 4.0, 8.3, 3.1, 3.0];
  var rawScores204 = [11.8, 11.7, 5.3, 12.4, 6.2, 14.6, 8.3, 4.0, 7.7, 3.7];
  var rawScores213 = [6.3, 11.7, 10.8, 9.4, 9.1, 5.7, 4.0, 7.2, 4.3, 4.0];

  var heatData = [];
  rawScores208.forEach(function(v, si) { heatData.push([si, 0, v]); });
  rawScores204.forEach(function(v, si) { heatData.push([si, 1, v]); });
  rawScores213.forEach(function(v, si) { heatData.push([si, 2, v]); });

  var heatY = ['🥇 #208', '🥈 #204', '🥉 #213'];

  chart2.setOption({
    animation: false,
    tooltip: {
      appendToBody: true,
      formatter: function(p) {
        return heatY[p.value[1]] + ' ' + scores[p.value[0]] + ': ' + p.value[2].toFixed(1) + '%';
      }
    },
    grid: { left: 80, right: 30, top: 10, bottom: 80 },
    xAxis: {
      type: 'category',
      data: scores,
      axisLabel: { color: ink, fontSize: 11, rotate: 45 },
      axisLine: { lineStyle: { color: rule } }
    },
    yAxis: {
      type: 'category',
      data: heatY,
      axisLabel: { color: ink, fontSize: 12 },
      axisLine: { lineStyle: { color: rule } }
    },
    visualMap: {
      min: 2,
      max: 17,
      calculable: true,
      orient: 'horizontal',
      bottom: 0,
      left: 'center',
      textStyle: { color: muted },
      inRange: { color: [bg2, accent2, accent] },
      itemWidth: 16,
      itemHeight: 120
    },
    series: [{
      type: 'heatmap',
      data: heatData,
      label: {
        show: true,
        color: ink,
        fontSize: 11,
        fontWeight: 600,
        formatter: function(p) { return p.value[2].toFixed(1) + '%'; }
      },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowColor: accent }
      }
    }]
  });
  window.addEventListener('resize', function() { chart2.resize(); });

})();
