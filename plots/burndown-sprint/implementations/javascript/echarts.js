// anyplot.ai
// burndown-sprint: Agile Sprint Burndown Chart
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 86/100 | Created: 2026-06-14
//# anyplot-orientation: landscape
// anyplot.ai
// burndown-sprint: Agile Sprint Burndown Chart
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-14

const t = window.ANYPLOT_TOKENS;

// Sprint: June 2–13 2025, 10 working days, initial scope 40 story points
// Scope change: +8 points added on Thu Jun 5 (Day 4)
const ms = (s) => new Date(s).getTime();

const actual = [
  [ms('2025-06-01'), 40], // Sprint kick-off (committed scope)
  [ms('2025-06-02'), 37], // Mon Day 1: burned 3
  [ms('2025-06-03'), 33], // Tue Day 2: burned 4
  [ms('2025-06-04'), 30], // Wed Day 3: burned 3
  [ms('2025-06-05'), 34], // Thu Day 4: burned 4, +8 scope change added
  [ms('2025-06-06'), 30], // Fri Day 5: burned 4
  [ms('2025-06-09'), 25], // Mon Day 6: burned 5 (weekend flat at 30)
  [ms('2025-06-10'), 20], // Tue Day 7: burned 5
  [ms('2025-06-11'), 14], // Wed Day 8: burned 6
  [ms('2025-06-12'),  8], // Thu Day 9: burned 6
  [ms('2025-06-13'),  3], // Fri Day 10: burned 5 — sprint ends, 3 pts remain
];

// Ideal burndown: straight line from committed scope (40) to zero, one point per day
const ideal = Array.from({ length: 13 }, (_, i) => {
  const day = new Date('2025-06-01');
  day.setDate(day.getDate() + i);
  return [day.getTime(), Math.round(40 * (12 - i) / 12)];
});

const chart = echarts.init(document.getElementById('container'));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: 'transparent',

  title: {
    text: 'burndown-sprint · javascript · echarts · anyplot.ai',
    left: 'center',
    top: 20,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 'bold' },
  },

  legend: {
    top: 60,
    textStyle: { color: t.inkSoft, fontSize: 14 },
    icon: 'roundRect',
  },

  tooltip: {
    trigger: 'axis',
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    textStyle: { color: t.ink, fontSize: 13 },
    axisPointer: { lineStyle: { color: t.inkSoft } },
    formatter: (params) => {
      const day = new Date(params[0].data[0]);
      const label = day.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
      const rows = params
        .filter((p) => p.data && p.data.length > 1 && p.data[1] != null)
        .map((p) => `${p.marker} ${p.seriesName}: <b>${p.data[1]} pts</b>`);
      return `${label}<br/>${rows.join('<br/>')}`;
    },
  },

  grid: { left: 120, right: 60, top: 120, bottom: 80 },

  xAxis: {
    type: 'time',
    min: ms('2025-06-01'),
    max: ms('2025-06-13'),
    axisLabel: {
      color: t.inkSoft,
      fontSize: 13,
      formatter: (val) =>
        new Date(val).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },

  yAxis: {
    type: 'value',
    name: 'Story Points Remaining',
    nameLocation: 'middle',
    nameRotate: 90,
    nameGap: 60,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    min: 0,
    max: 50,
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },

  series: [
    {
      name: 'Actual Remaining',
      type: 'line',
      step: 'end',
      data: actual,
      itemStyle: { color: t.palette[0] },
      lineStyle: { color: t.palette[0], width: 3 },
      symbol: 'circle',
      symbolSize: 8,
      markArea: {
        silent: true,
        itemStyle: { color: t.inkSoft, opacity: 0.10 },
        label: {
          show: true,
          position: 'insideTop',
          color: t.inkSoft,
          fontSize: 12,
          formatter: 'Weekend',
        },
        data: [[{ xAxis: ms('2025-06-07') }, { xAxis: ms('2025-06-09') }]],
      },
      markLine: {
        silent: true,
        symbol: ['none', 'none'],
        lineStyle: { color: t.amber, width: 2, type: 'dashed' },
        label: {
          show: true,
          formatter: '+8 pts  Scope Change',
          color: t.amber,
          fontSize: 12,
          position: 'end',
        },
        data: [{ xAxis: ms('2025-06-05'), name: 'Scope Change' }],
      },
    },
    {
      name: 'Ideal Burndown',
      type: 'line',
      data: ideal,
      itemStyle: { color: t.inkSoft },
      lineStyle: { color: t.inkSoft, width: 2, type: 'dashed' },
      symbol: 'none',
    },
  ],
});
