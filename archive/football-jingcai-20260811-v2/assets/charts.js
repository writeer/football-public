/* charts.js — v2 基本面驱动版图表 */
(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var danger = style.getPropertyValue('--danger').trim();

  var matches = [
    '001 江原FC', '002 凯拉特', '003 博德闪耀', '004 萨巴赫', '005 奈梅亨',
    '006 采列', '007 布拉迪', '008 格拉茨', '009 里昂', '010 弗鲁米嫩塞'
  ];
  var modelP = [49.7, 37.3, 56.3, 54.4, 39.9, 63.6, 57.2, 27.2, 71.6, 59.7];
  var marketP = [34.8, 34.1, 60.6, 49.6, 34.2, 69.2, 51.6, 21.7, 70.3, 61.1];

  // ---- Chart 1: 模型 vs 市场主胜概率 ----
  var c1 = echarts.init(document.getElementById('chart-div'), null, { renderer: 'svg' });
  c1.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis', appendToBody: true,
      axisPointer: { type: 'shadow' },
      backgroundColor: bg2, borderColor: rule, textStyle: { color: ink },
      formatter: function(params) {
        var idx = params[0].dataIndex;
        var d = (modelP[idx] - marketP[idx]).toFixed(1);
        var sign = d >= 0 ? '+' : '';
        return params[0].name + '<br/>' +
          params[0].marker + ' 模型: <b>' + modelP[idx] + '%</b><br/>' +
          params[1].marker + ' 市场Shin: <b>' + marketP[idx] + '%</b><br/>' +
          '差异: <b style="color:' + (d >= 0 ? accent : danger) + '">' + sign + d + 'pp</b>';
      }
    },
    legend: { data: ['模型(基本面驱动)', '市场Shin(赔率去水)'], top: 0, textStyle: { color: muted } },
    grid: { left: 40, right: 20, top: 40, bottom: 40 },
    xAxis: { type: 'category', data: matches, axisLabel: { color: muted, fontSize: 11, interval: 0, rotate: 32 }, axisLine: { lineStyle: { color: rule } } },
    yAxis: { type: 'value', min: 0, max: 80, axisLabel: { color: muted, formatter: '{value}%' }, splitLine: { lineStyle: { color: rule } } },
    series: [
      { name: '模型(基本面驱动)', type: 'bar', data: modelP, itemStyle: { color: accent }, barMaxWidth: 20,
        label: { show: true, position: 'top', color: ink, fontSize: 10, formatter: '{c}%' } },
      { name: '市场Shin(赔率去水)', type: 'bar', data: marketP, itemStyle: { color: muted + '88' }, barMaxWidth: 20 }
    ]
  });
  window.addEventListener('resize', function() { c1.resize(); });

  // ---- Chart 2: 置信度分布 ----
  var c2 = echarts.init(document.getElementById('chart-conf'), null, { renderer: 'svg' });
  c2.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true, axisPointer: { type: 'shadow' }, backgroundColor: bg2, borderColor: rule, textStyle: { color: ink } },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: ['★★★ 高置信度', '★★ 中置信度', '★ 低置信度（含降级）'], axisLabel: { color: muted, fontSize: 12 }, axisLine: { lineStyle: { color: rule } } },
    yAxis: { type: 'value', min: 0, max: 6, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
    series: [{
      name: '场次', type: 'bar',
      data: [
        { value: 3, itemStyle: { color: accent } },
        { value: 3, itemStyle: { color: accent2 } },
        { value: 4, itemStyle: { color: danger } }
      ],
      label: { show: true, position: 'top', color: ink, formatter: '{c} 场' },
      barMaxWidth: 70
    }]
  });
  window.addEventListener('resize', function() { c2.resize(); });
})();
