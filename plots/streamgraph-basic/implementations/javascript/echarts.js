// anyplot.ai
// streamgraph-basic: Basic Stream Graph
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 91/100 | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Monthly streaming hours (thousands) by music genre, Jan 2024 - Dec 2025.
const genres = ["Pop", "Hip-Hop", "Rock", "Electronic", "Jazz"];
const monthCount = 24;

// Per-genre wave parameters: base level, seasonal amplitude/period/phase, linear trend.
const params = [
  { base: 42, amp: 8, period: 12, phase: 0, trend: -0.3 },
  { base: 28, amp: 10, period: 8, phase: 3, trend: 0.5 },
  { base: 35, amp: 6, period: 12, phase: 6, trend: -0.05 },
  { base: 18, amp: 9, period: 6, phase: 1, trend: 0.6 },
  { base: 12, amp: 4, period: 12, phase: 9, trend: 0.05 },
];

const monthLabel = (i) => {
  const year = 2024 + Math.floor(i / 12);
  const month = String((i % 12) + 1).padStart(2, "0");
  return `${year}-${month}-01`;
};

const streamData = [];
for (let i = 0; i < monthCount; i += 1) {
  const date = monthLabel(i);
  genres.forEach((genre, gi) => {
    const p = params[gi];
    const seasonal = p.amp * Math.sin((2 * Math.PI * (i + p.phase)) / p.period);
    const value = Math.max(2, Math.round(p.base + seasonal + p.trend * i));
    streamData.push([date, value, genre]);
  });
}

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "streamgraph-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 30,
    textStyle: { color: t.ink, fontSize: 22 },
  },
  legend: {
    data: genres,
    top: 90,
    textStyle: { color: t.ink, fontSize: 16 },
    itemWidth: 22,
    itemHeight: 14,
  },
  singleAxis: {
    type: "time",
    top: 170,
    bottom: 110,
    left: 90,
    right: 90,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: true, lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "themeRiver",
      emphasis: { disabled: true },
      label: { show: false },
      data: streamData,
    },
  ],
});
