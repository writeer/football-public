/* charts.js — 周二竞彩10场分析报告 图表 */
(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();

  var matches = [
    '001 江原FC', '002 凯拉特', '003 博德闪耀', '004 萨巴赫', '005 奈梅亨',
    '006 采列', '007 布拉迪', '008 格拉茨', '009 里昂', '010 弗鲁米嫩塞'
  ];

  // ---- Chart 1: 主胜概率对比 ----
  var c1 = echarts.init(document.getElementById('chart-odds'), null, { renderer: 'svg' });
  c1.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis', appendToBody: true,
      axisPointer: { type: 'shadow' },
      valueFormatter: function(v) { return (v * 100).toFixed(1) + '%'; },
      backgroundColor: bg2, borderColor: rule, textStyle: { color: ink }
    },
    legend: {
      data: ['Shin去水', 'DC修正', '蒙特卡洛'],
      top: 0, textStyle: { color: muted }
    },
    grid: { left: 40, right: 20, top: 40, bottom: 40 },
    xAxis: {
      type: 'category', data: matches,
      axisLabel: { color: muted, fontSize: 11, interval: 0, rotate: 32 },
      axisLine: { lineStyle: { color: rule } }
    },
    yAxis: {
      type: 'value', min: 0, max: 0.8,
      axisLabel: { color: muted, formatter: function(v) { return (v * 100) + '%'; } },
      splitLine: { lineStyle: { color: rule } }
    },
    series: [
      {
        name: 'Shin去水', type: 'bar', data: [0.348, 0.341, 0.606, 0.496, 0.342, 0.692, 0.516, 0.217, 0.703, 0.611],
        itemStyle: { color: accent2 }, barMaxWidth: 20
      },
      {
        name: 'DC修正', type: 'bar', data: [0.325, 0.307, 0.600, 0.520, 0.309, 0.678, 0.519, 0.158, 0.756, 0.535],
        itemStyle: { color: accent }, barMaxWidth: 20
      },
      {
        name: '蒙特卡洛', type: 'bar', data: [0.322, 0.310, 0.597, 0.518, 0.311, 0.677, 0.516, 0.161, 0.754, 0.534],
        itemStyle: { color: accent + '66' }, barMaxWidth: 20
      }
    ]
  });
  window.addEventListener('resize', function() { c1.resize(); });

  // ---- Chart 2: 大2.5球概率 ----
  var overData = [30.2, 32.8, 49.4, 44.8, 34.0, 42.8, 45.5, 41.4, 51.2, 28.0];
  var c2 = echarts.init(document.getElementById('chart-over'), null, { renderer: 'svg' });
  c2.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis', appendToBody: true,
      axisPointer: { type: 'shadow' },
      valueFormatter: function(v) { return v + '%'; },
      backgroundColor: bg2, borderColor: rule, textStyle: { color: ink }
    },
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category', data: matches,
      axisLabel: { color: muted, fontSize: 11, interval: 0, rotate: 32 },
      axisLine: { lineStyle: { color: rule } }
    },
    yAxis: {
      type: 'value', min: 0, max: 60,
      axisLabel: { color: muted, formatter: function(v) { return v + '%'; } },
      splitLine: { lineStyle: { color: rule } }
    },
    series: [{
      name: '大2.5球概率', type: 'bar',
      data: overData.map(function(v) {
        return {
          value: v,
          itemStyle: { color: v >= 45 ? accent : (v >= 38 ? accent + '99' : muted + '66') }
        };
      }),
      label: { show: true, position: 'top', color: ink, formatter: function(p) { return p.value + '%'; } },
      barMaxWidth: 34,
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: accent2, type: 'dashed' },
        label: { color: accent2, formatter: '45% 分界' },
        data: [{ yAxis: 45 }]
      }
    }]
  });
  window.addEventListener('resize', function() { c2.resize(); });
})();
