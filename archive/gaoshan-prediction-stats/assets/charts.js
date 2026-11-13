(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var red = style.getPropertyValue('--red').trim();
  var yellow = style.getPropertyValue('--yellow').trim();

  var baseText = { color: muted, fontSize: 11 };
  var baseLine = { lineStyle: { color: rule } };

  // Chart 1: Direction Accuracy by Prediction Type
  var chart1 = echarts.init(document.getElementById('chart-dir-accuracy'), null, { renderer: 'svg' });
  chart1.setOption({
    tooltip: { trigger: 'axis', appendToBody: true, axisPointer: { type: 'shadow' } },
    legend: { data: ['Sport', '全场高山'], top: 0, textStyle: { color: muted, fontSize: 12 } },
    grid: { left: 60, right: 30, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: ['主胜', '平局', '客胜'], axisLabel: baseText, axisLine: baseLine, axisTick: { show: false } },
    yAxis: { type: 'value', max: 70, axisLabel: { ...baseText, formatter: '{value}%' }, splitLine: { lineStyle: { color: rule, type: 'dashed' } }, axisLine: { show: false } },
    series: [
      {
        name: 'Sport', type: 'bar', barWidth: '28%',
        data: [
          { value: 55.8, itemStyle: { color: accent } },
          { value: 26.5, itemStyle: { color: red } },
          { value: 50.1, itemStyle: { color: accent2 } }
        ],
        label: { show: true, position: 'top', formatter: '{c}%', color: ink, fontSize: 12, fontWeight: 600 }
      },
      {
        name: '全场高山', type: 'bar', barWidth: '28%',
        data: [
          { value: 56.1, itemStyle: { color: accent + 'cc' } },
          { value: 24.4, itemStyle: { color: red + 'cc' } },
          { value: 47.7, itemStyle: { color: accent2 + 'cc' } }
        ],
        label: { show: true, position: 'top', formatter: '{c}%', color: ink, fontSize: 12, fontWeight: 600 }
      }
    ],
    animation: false
  });
  window.addEventListener('resize', function() { chart1.resize(); });

  // Chart 2: Agreement Analysis
  var chart2 = echarts.init(document.getElementById('chart-agreement'), null, { renderer: 'svg' });
  chart2.setOption({
    tooltip: { trigger: 'axis', appendToBody: true, axisPointer: { type: 'shadow' } },
    grid: { left: 60, right: 40, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: ['方向一致 (744场)', '方向不一致 (413场)'], axisLabel: { ...baseText, fontSize: 12 }, axisLine: baseLine, axisTick: { show: false } },
    yAxis: { type: 'value', max: 70, axisLabel: { ...baseText, formatter: '{value}%' }, splitLine: { lineStyle: { color: rule, type: 'dashed' } }, axisLine: { show: false } },
    series: [
      {
        type: 'bar', barWidth: '40%',
        data: [
          { value: 52.2, itemStyle: { color: accent } },
          { value: 35.8, itemStyle: { color: red } }
        ],
        label: { show: true, position: 'top', formatter: '{c}%', color: ink, fontSize: 13, fontWeight: 700 }
      }
    ],
    animation: false
  });
  window.addEventListener('resize', function() { chart2.resize(); });

  // Chart 3: Sport by League (horizontal bar, sorted)
  var sportLeagues = [
    ['世预赛', 78, 67.9], ['欧冠', 126, 50.8], ['意甲', 151, 46.4],
    ['西甲', 116, 49.1], ['英超', 131, 45.0], ['英冠', 103, 45.6],
    ['德甲', 96, 47.9], ['法甲', 89, 41.6], ['荷甲', 72, 48.6],
    ['欧罗巴', 55, 45.5], ['葡超', 47, 51.1], ['澳超', 45, 24.4],
    ['沙职', 43, 48.8], ['德乙', 41, 36.6], ['瑞超', 29, 34.5]
  ].sort(function(a, b) { return b[2] - a[2]; });

  var chart3 = echarts.init(document.getElementById('chart-league-sport'), null, { renderer: 'svg' });
  chart3.setOption({
    tooltip: { trigger: 'axis', appendToBody: true, axisPointer: { type: 'shadow' },
      formatter: function(p) { return p[0].name + '<br/>场次: ' + sportLeagues[p[0].dataIndex][1] + '<br/>准确率: ' + p[0].value + '%'; }
    },
    grid: { left: 70, right: 50, top: 10, bottom: 20 },
    xAxis: { type: 'value', max: 80, axisLabel: { ...baseText, formatter: '{value}%' }, splitLine: { lineStyle: { color: rule, type: 'dashed' } }, axisLine: { show: false } },
    yAxis: { type: 'category', data: sportLeagues.map(function(d) { return d[0]; }), axisLabel: { color: ink, fontSize: 11 }, axisLine: baseLine, axisTick: { show: false }, inverse: true },
    series: [{
      type: 'bar', barWidth: '55%',
      data: sportLeagues.map(function(d) {
        var c = d[2] >= 50 ? accent : (d[2] >= 40 ? yellow : red);
        return { value: d[2], itemStyle: { color: c } };
      }),
      label: { show: true, position: 'right', formatter: '{c}%', color: ink, fontSize: 11, fontWeight: 600 }
    }],
    animation: false
  });
  window.addEventListener('resize', function() { chart3.resize(); });

  // Chart 4: Gaoshan by League (horizontal bar, sorted)
  var gsLeagues = [
    ['英超', 121, 36.4], ['意甲', 135, 44.4], ['西甲', 113, 50.4],
    ['德甲', 95, 45.3], ['欧冠', 112, 48.2], ['英冠', 98, 43.9],
    ['法甲', 80, 41.2], ['荷甲', 67, 55.2], ['瑞超', 46, 43.5],
    ['韩职', 49, 30.6], ['澳超', 49, 32.7], ['日职', 34, 52.9],
    ['世预赛', 36, 58.3], ['挪超', 33, 57.6], ['葡超', 41, 51.2]
  ].sort(function(a, b) { return b[2] - a[2]; });

  var chart4 = echarts.init(document.getElementById('chart-league-gaoshan'), null, { renderer: 'svg' });
  chart4.setOption({
    tooltip: { trigger: 'axis', appendToBody: true, axisPointer: { type: 'shadow' },
      formatter: function(p) { return p[0].name + '<br/>场次: ' + gsLeagues[p[0].dataIndex][1] + '<br/>准确率: ' + p[0].value + '%'; }
    },
    grid: { left: 70, right: 50, top: 10, bottom: 20 },
    xAxis: { type: 'value', max: 80, axisLabel: { ...baseText, formatter: '{value}%' }, splitLine: { lineStyle: { color: rule, type: 'dashed' } }, axisLine: { show: false } },
    yAxis: { type: 'category', data: gsLeagues.map(function(d) { return d[0]; }), axisLabel: { color: ink, fontSize: 11 }, axisLine: baseLine, axisTick: { show: false }, inverse: true },
    series: [{
      type: 'bar', barWidth: '55%',
      data: gsLeagues.map(function(d) {
        var c = d[2] >= 50 ? accent : (d[2] >= 40 ? yellow : red);
        return { value: d[2], itemStyle: { color: c } };
      }),
      label: { show: true, position: 'right', formatter: '{c}%', color: ink, fontSize: 11, fontWeight: 600 }
    }],
    animation: false
  });
  window.addEventListener('resize', function() { chart4.resize(); });
})();