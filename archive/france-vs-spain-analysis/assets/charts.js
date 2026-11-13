(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var bg3 = style.getPropertyValue('--bg3').trim();
  var green = style.getPropertyValue('--green').trim();
  var yellow = style.getPropertyValue('--yellow').trim();
  var red = style.getPropertyValue('--red').trim();

  var franceColor = '#60a5fa';
  var spainColor = '#f87171';
  var drawColor = yellow;

  // --- Chart 1: Model Comparison ---
  var chart1 = echarts.init(document.getElementById('chart-models'), null, { renderer: 'svg' });
  chart1.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      appendToBody: true,
      formatter: function(params) {
        var str = params[0].name + '<br/>';
        params.forEach(function(p) {
          str += p.marker + p.seriesName + ': ' + p.value + '%<br/>';
        });
        return str;
      }
    },
    legend: {
      data: ['法国胜', '平局', '西班牙胜'],
      top: 0,
      textStyle: { color: ink, fontSize: 12 },
      itemWidth: 14,
      itemHeight: 10
    },
    grid: { top: 40, bottom: 60, left: 50, right: 20 },
    xAxis: {
      type: 'category',
      data: ['DC模型', '负二项', 'ZIP', '双变量泊松', 'Skellam', '蒙特卡洛', '加权融合', 'Shin隐含'],
      axisLabel: { color: muted, fontSize: 10, rotate: 25 },
      axisLine: { lineStyle: { color: rule } }
    },
    yAxis: {
      type: 'value',
      max: 50,
      axisLabel: { color: muted, fontSize: 11, formatter: '{value}%' },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } },
      axisLine: { lineStyle: { color: rule } }
    },
    series: [
      {
        name: '法国胜',
        type: 'bar',
        data: [38.1, 38.9, 38.8, 38.0, 38.8, 37.4, 41.3, 39.2],
        itemStyle: { color: franceColor, borderRadius: [3, 3, 0, 0] }
      },
      {
        name: '平局',
        type: 'bar',
        data: [28.1, 26.5, 26.6, 28.6, 26.5, 28.4, 26.8, 27.0],
        itemStyle: { color: drawColor, borderRadius: [3, 3, 0, 0] }
      },
      {
        name: '西班牙胜',
        type: 'bar',
        data: [33.9, 34.7, 34.6, 33.5, 34.6, 34.1, 31.9, 33.8],
        itemStyle: { color: spainColor, borderRadius: [3, 3, 0, 0] }
      }
    ]
  });
  window.addEventListener('resize', function() { chart1.resize(); });

  // --- Chart 2: Score Distribution ---
  var chart2 = echarts.init(document.getElementById('chart-scores'), null, { renderer: 'svg' });
  var scoreData = [
    { name: '1-1', prob: 11.5, winner: 'draw' },
    { name: '0-0', prob: 10.7, winner: 'draw' },
    { name: '1-0', prob: 9.3, winner: 'france' },
    { name: '0-1', prob: 8.7, winner: 'spain' },
    { name: '2-1', prob: 8.4, winner: 'france' },
    { name: '1-2', prob: 8.1, winner: 'spain' },
    { name: '2-0', prob: 6.2, winner: 'france' },
    { name: '0-2', prob: 5.8, winner: 'spain' },
    { name: '2-2', prob: 4.7, winner: 'draw' },
    { name: '3-1', prob: 3.3, winner: 'france' }
  ];

  chart2.setOption({
    animation: false,
    tooltip: {
      trigger: 'item',
      appendToBody: true,
      formatter: function(p) {
        return p.name + '<br/>概率: ' + p.value + '%';
      }
    },
    grid: { top: 20, bottom: 30, left: 50, right: 20 },
    xAxis: {
      type: 'category',
      data: scoreData.map(function(d) { return d.name; }),
      axisLabel: { color: muted, fontSize: 11 },
      axisLine: { lineStyle: { color: rule } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: muted, fontSize: 11, formatter: '{value}%' },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } },
      axisLine: { lineStyle: { color: rule } }
    },
    series: [{
      type: 'bar',
      data: scoreData.map(function(d) {
        var color = d.winner === 'france' ? franceColor :
                    d.winner === 'spain' ? spainColor : drawColor;
        return { value: d.prob, itemStyle: { color: color, borderRadius: [4, 4, 0, 0] } };
      }),
      label: {
        show: true,
        position: 'top',
        formatter: '{c}%',
        fontSize: 10,
        color: ink
      }
    }]
  });
  window.addEventListener('resize', function() { chart2.resize(); });

  // --- Chart 3: Goal Distribution ---
  var chart3 = echarts.init(document.getElementById('chart-goals'), null, { renderer: 'svg' });
  chart3.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      appendToBody: true,
      formatter: function(params) {
        var str = params[0].name + '球<br/>';
        params.forEach(function(p) {
          str += p.marker + p.seriesName + ': ' + p.value + '%<br/>';
        });
        return str;
      }
    },
    legend: {
      data: ['泊松', '负二项(NB)', 'ZIP', '蒙特卡洛'],
      top: 0,
      textStyle: { color: ink, fontSize: 11 },
      itemWidth: 14,
      itemHeight: 10
    },
    grid: { top: 40, bottom: 30, left: 50, right: 20 },
    xAxis: {
      type: 'category',
      data: ['0球', '1球', '2球', '3球', '4+球'],
      axisLabel: { color: muted, fontSize: 12 },
      axisLine: { lineStyle: { color: rule } }
    },
    yAxis: {
      type: 'value',
      max: 30,
      axisLabel: { color: muted, fontSize: 11, formatter: '{value}%' },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } },
      axisLine: { lineStyle: { color: rule } }
    },
    series: [
      {
        name: '泊松',
        type: 'line',
        data: [7.7, 19.8, 25.5, 21.8, 25.2],
        smooth: true,
        itemStyle: { color: muted },
        lineStyle: { color: muted, type: 'dashed', width: 2 },
        symbol: 'circle',
        symbolSize: 6
      },
      {
        name: '负二项(NB)',
        type: 'line',
        data: [8.5, 18.5, 24.2, 22.5, 26.3],
        smooth: true,
        itemStyle: { color: accent2 },
        lineStyle: { color: accent2, width: 2 },
        symbol: 'diamond',
        symbolSize: 6
      },
      {
        name: 'ZIP',
        type: 'line',
        data: [10.8, 18.3, 24.1, 22.1, 24.7],
        smooth: true,
        itemStyle: { color: green },
        lineStyle: { color: green, width: 2 },
        symbol: 'triangle',
        symbolSize: 6
      },
      {
        name: '蒙特卡洛',
        type: 'bar',
        data: [10.8, 18.3, 24.1, 22.1, 24.7],
        itemStyle: { color: accent, opacity: 0.5, borderRadius: [4, 4, 0, 0] }
      }
    ]
  });
  window.addEventListener('resize', function() { chart3.resize(); });

})();
