(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();

  // Color palette
  var colors = [accent, accent2, '#e8b339', '#6bbd7b', '#d46a6a'];

  // --- Summary Overview Chart ---
  var chartSummary = echarts.init(document.getElementById('chart-summary'), null, { renderer: 'svg' });
  chartSummary.setOption({
    animation: false,
    tooltip: { appendToBody: true, trigger: 'axis' },
    legend: { data: ['主胜', '平局', '客胜'], top: 5, textStyle: { color: muted, fontSize: 12 } },
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
    xAxis: { 
      type: 'category', 
      data: ['201 TPS图尔库\nvs 坦山猫', '202 玛丽港\nvs 拉赫蒂', '203 厄尔格里特\nvs 佐加顿斯', '204 卡尔马\nvs 马尔默'],
      axisLabel: { color: muted, fontSize: 11 }, axisLine: { lineStyle: { color: rule } }
    },
    yAxis: { 
      type: 'value', max: 65, name: '%',
      nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } }
    },
    series: [
      { name: '主胜', type: 'bar', data: [50.1, 28.5, 22.2, 35.1], itemStyle: { color: colors[0] } },
      { name: '平局', type: 'bar', data: [26.7, 29.8, 24.6, 28.7], itemStyle: { color: colors[1] } },
      { name: '客胜', type: 'bar', data: [23.2, 41.7, 53.2, 36.2], itemStyle: { color: colors[2] } }
    ]
  });
  window.addEventListener('resize', function() { chartSummary.resize(); });

  // --- Model Comparison for each match ---
  var matches = [
    { id: 'chart-m1', dc: [55.1,23.1,21.8], nb: [52.1,25.8,22.1], sk: [54.3,24.9,20.8], mc: [53.8,25.1,21.1], fused: [50.1,26.7,23.2], shin: [37.4,25.8,36.8], labels: ['DC','NB','Skellam','MC','融合','Shin'] },
    { id: 'chart-m2', dc: [27.7,29.1,43.3], nb: [27.0,32.6,40.5], sk: [27.0,30.4,42.6], mc: [27.3,30.0,42.7], fused: [28.5,29.8,41.7], shin: [18.1,21.9,60.0], labels: ['DC','NB','Skellam','MC','融合','Shin'] },
    { id: 'chart-m3', dc: [22.3,21.0,56.7], nb: [23.2,25.3,51.5], sk: [21.2,23.1,55.7], mc: [21.0,23.1,55.9], fused: [22.2,24.6,53.2], shin: [16.1,19.5,64.4], labels: ['DC','NB','Skellam','MC','融合','Shin'] },
    { id: 'chart-m4', dc: [40.1,25.0,34.9], nb: [36.7,30.7,32.6], sk: [39.1,27.0,33.8], mc: [39.0,26.9,34.0], fused: [35.1,28.7,36.2], shin: [21.4,23.0,55.5], labels: ['DC','NB','Skellam','MC','融合','Shin'] },
  ];

  matches.forEach(function(m) {
    var el = document.getElementById(m.id);
    if (!el) return;
    var c = echarts.init(el, null, { renderer: 'svg' });
    c.setOption({
      animation: false,
      tooltip: { appendToBody: true, trigger: 'axis' },
      legend: { data: ['主胜','平局','客胜'], top: 0, textStyle: { color: muted, fontSize: 11 } },
      grid: { left: 45, right: 15, top: 35, bottom: 28 },
      xAxis: { type: 'category', data: m.labels, axisLabel: { color: muted, fontSize: 10 }, axisLine: { lineStyle: { color: rule } } },
      yAxis: { type: 'value', name: '%', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
      series: [
        { name: '主胜', type: 'bar', data: [m.dc[0],m.nb[0],m.sk[0],m.mc[0],m.fused[0],m.shin[0]], itemStyle: { color: colors[0] } },
        { name: '平局', type: 'bar', data: [m.dc[1],m.nb[1],m.sk[1],m.mc[1],m.fused[1],m.shin[1]], itemStyle: { color: colors[1] } },
        { name: '客胜', type: 'bar', data: [m.dc[2],m.nb[2],m.sk[2],m.mc[2],m.fused[2],m.shin[2]], itemStyle: { color: colors[2] } }
      ]
    });
    window.addEventListener('resize', function() { c.resize(); });
  });

  // --- Total Goals Charts ---
  var goalData = [
    { id: 'chart-goals-1', data: {'0':8.3,'1':20.3,'2':25.4,'3':21.4,'4+':24.1}, line: 2.75 },
    { id: 'chart-goals-2', data: {'0':13.5,'1':27.1,'2':26.7,'3':18.3,'4+':14.3}, line: 2.5 },
    { id: 'chart-goals-3', data: {'0':6.1,'1':17.1,'2':23.5,'3':22.5,'4+':29.9}, line: 3.0 },
    { id: 'chart-goals-4', data: {'0':8.2,'1':20.3,'2':25.6,'3':21.5,'4+':23.9}, line: 2.5 },
  ];

  goalData.forEach(function(g) {
    var el = document.getElementById(g.id);
    if (!el) return;
    var cats = Object.keys(g.data);
    var vals = Object.values(g.data);
    var c = echarts.init(el, null, { renderer: 'svg' });
    c.setOption({
      animation: false,
      tooltip: { appendToBody: true, trigger: 'axis', formatter: function(p) { return p[0].name + '球: ' + p[0].value + '%'; } },
      grid: { left: 40, right: 15, top: 15, bottom: 28 },
      xAxis: { type: 'category', data: cats, axisLabel: { color: muted, fontSize: 11 }, axisLine: { lineStyle: { color: rule } } },
      yAxis: { type: 'value', name: '%', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
      series: [{
        type: 'bar', data: vals,
        itemStyle: { color: function(p) { return p.dataIndex <= 1 ? accent + '99' : accent; } },
        label: { show: true, position: 'top', formatter: '{c}%', fontSize: 10, color: muted }
      }]
    });
    window.addEventListener('resize', function() { c.resize(); });
  });
})();