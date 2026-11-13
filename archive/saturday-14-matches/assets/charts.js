// assets/charts.js — ECharts visualizations
(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var accent3 = style.getPropertyValue('--accent3').trim();
  var accent4 = style.getPropertyValue('--accent4').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var bg3 = style.getPropertyValue('--bg3').trim();

  // Data (same as render.js)
  var DATA = [
    {id:201,home:"大田市民",away:"蔚山现代",fused:{win:0.225,draw:0.295,lose:0.482},shin:{win:0.387,draw:0.289,lose:0.324}},
    {id:202,home:"江原FC",away:"金泉尚武",fused:{win:0.528,draw:0.290,lose:0.182},shin:{win:0.473,draw:0.279,lose:0.248}},
    {id:203,home:"济州SK",away:"浦项制铁",fused:{win:0.247,draw:0.287,lose:0.466},shin:{win:0.278,draw:0.292,lose:0.430}},
    {id:204,home:"仁川联",away:"全北现代",fused:{win:0.259,draw:0.332,lose:0.409},shin:{win:0.282,draw:0.296,lose:0.422}},
    {id:205,home:"汉坎",away:"特罗姆瑟",fused:{win:0.479,draw:0.267,lose:0.254},shin:{win:0.368,draw:0.276,lose:0.356}},
    {id:206,home:"赫尔辛基",away:"瓦萨",fused:{win:0.449,draw:0.288,lose:0.263},shin:{win:0.491,draw:0.262,lose:0.247}},
    {id:207,home:"AIK索尔纳",away:"哥德堡盖斯",fused:{win:0.379,draw:0.315,lose:0.306},shin:{win:0.369,draw:0.274,lose:0.357}},
    {id:208,home:"利勒斯特罗姆",away:"奥斯陆KFUM",fused:{win:0.637,draw:0.220,lose:0.143},shin:{win:0.632,draw:0.220,lose:0.148}},
    {id:209,home:"斯达",away:"罗森博格",fused:{win:0.283,draw:0.342,lose:0.375},shin:{win:0.279,draw:0.278,lose:0.443}},
    {id:210,home:"克里斯蒂安松",away:"萨尔普斯堡",fused:{win:0.316,draw:0.282,lose:0.402},shin:{win:0.330,draw:0.274,lose:0.396}},
    {id:211,home:"AC奥卢",away:"赫尔辛基火花",fused:{win:0.491,draw:0.281,lose:0.228},shin:{win:0.413,draw:0.271,lose:0.316}},
    {id:212,home:"塞伊奈约基",away:"库奥皮奥",fused:{win:0.322,draw:0.273,lose:0.407},shin:{win:0.337,draw:0.278,lose:0.386}},
    {id:213,home:"莫尔德",away:"布兰",fused:{win:0.608,draw:0.223,lose:0.171},shin:{win:0.561,draw:0.241,lose:0.198}},
    {id:214,home:"维京",away:"桑纳菲尤尔",fused:{win:0.704,draw:0.183,lose:0.114},shin:{win:0.623,draw:0.210,lose:0.167}}
  ];

  // Sort by best probability descending
  var sorted = DATA.slice().sort(function(a, b) {
    var ba = Math.max(a.fused.win, a.fused.draw, a.fused.lose);
    var bb = Math.max(b.fused.win, b.fused.draw, b.fused.lose);
    return bb - ba;
  });

  var labels = sorted.map(function(m) { return '#' + m.id + ' ' + m.home + '\nvs ' + m.away; });

  // ===== CHART 1: Stacked probability bar =====
  var chart1 = echarts.init(document.getElementById('chart-prob'), null, { renderer: 'svg' });
  chart1.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      appendToBody: true,
      backgroundColor: bg2,
      borderColor: rule,
      textStyle: { color: ink, fontSize: 12 },
      formatter: function(params) {
        var s = '<b>' + params[0].name.replace('\n', ' ') + '</b><br/>';
        params.forEach(function(p) {
          s += p.marker + ' ' + p.seriesName + ': <b>' + (p.value * 100).toFixed(1) + '%</b><br/>';
        });
        return s;
      }
    },
    legend: { data: ['主胜', '平局', '客胜'], textStyle: { color: muted, fontSize: 12 }, top: 0, itemWidth: 14, itemHeight: 10 },
    grid: { left: 50, right: 30, top: 40, bottom: 60 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: muted, fontSize: 10, interval: 0, rotate: 25, formatter: function(v) { return v.split('\n')[0]; } },
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      max: 1,
      axisLabel: { color: muted, fontSize: 11, formatter: '{value}%' },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    series: [
      { name: '主胜', type: 'bar', stack: 'prob', data: sorted.map(function(m){return m.fused.win;}), itemStyle: { color: accent }, barWidth: '55%' },
      { name: '平局', type: 'bar', stack: 'prob', data: sorted.map(function(m){return m.fused.draw;}), itemStyle: { color: accent2 } },
      { name: '客胜', type: 'bar', stack: 'prob', data: sorted.map(function(m){return m.fused.lose;}), itemStyle: { color: accent4 } }
    ]
  });
  window.addEventListener('resize', function() { chart1.resize(); });

  // ===== CHART 2: Divergence =====
  var chart2 = echarts.init(document.getElementById('chart-divergence'), null, { renderer: 'svg' });
  var divLabels = DATA.map(function(m) { return '#' + m.id; });
  var divW = DATA.map(function(m) { return +((m.fused.win - m.shin.win) * 100).toFixed(1); });
  var divD = DATA.map(function(m) { return +((m.fused.draw - m.shin.draw) * 100).toFixed(1); });
  var divA = DATA.map(function(m) { return +((m.fused.lose - m.shin.lose) * 100).toFixed(1); });

  chart2.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis',
      appendToBody: true,
      backgroundColor: bg2,
      borderColor: rule,
      textStyle: { color: ink, fontSize: 12 },
      formatter: function(params) {
        var m = DATA[params[0].dataIndex];
        var s = '<b>#' + m.id + ' ' + m.home + ' vs ' + m.away + '</b><br/>';
        params.forEach(function(p) {
          var v = p.value;
          var c = v > 5 ? accent : v < -5 ? accent3 : muted;
          s += '<span style="color:' + c + '">' + p.marker + ' ' + p.seriesName + ': ' + (v >= 0 ? '+' : '') + v + '%</span><br/>';
        });
        return s;
      }
    },
    legend: { data: ['主胜偏差', '平局偏差', '客胜偏差'], textStyle: { color: muted, fontSize: 12 }, top: 0, itemWidth: 14, itemHeight: 10 },
    grid: { left: 50, right: 30, top: 40, bottom: 40 },
    xAxis: {
      type: 'category',
      data: divLabels,
      axisLabel: { color: muted, fontSize: 11 },
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: muted, fontSize: 11, formatter: '{value}%' },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    series: [
      { name: '主胜偏差', type: 'bar', data: divW, itemStyle: { color: function(p) { return p.value >= 0 ? accent : accent3 + '99'; } }, barGap: '-100%', barCategoryGap: '35%' },
      { name: '平局偏差', type: 'bar', data: divD, itemStyle: { color: function(p) { return p.value >= 0 ? accent2 : accent3 + '99'; } }, barGap: '-100%', barCategoryGap: '35%' },
      { name: '客胜偏差', type: 'bar', data: divA, itemStyle: { color: function(p) { return p.value >= 0 ? accent4 : accent3 + '99'; } }, barGap: '-100%', barCategoryGap: '35%' }
    ]
  });
  window.addEventListener('resize', function() { chart2.resize(); });

})();