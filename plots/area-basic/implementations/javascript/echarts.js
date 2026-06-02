// anyplot.ai
// area-basic: Basic Area Chart
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-02

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) -----------------------------------
// Daily website visitors across 30 days: gentle upward trend + weekly cycle
// (weekdays peak, weekends dip) + small noise. Imprint palette position 1 is
// the brand green for the filled trend.
let seed = 42;
const rng = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };

const days = 30;
const start = new Date(2026, 4, 1); // 2026-05-01 (months are 0-indexed)
const dates = [];
const visitors = [];
for (let i = 0; i < days; i++) {
  const d = new Date(start.getTime() + i * 86400000);
  dates.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`);
  const trend = 8200 + i * 180;
  const dow = d.getDay(); // 0 = Sun, 6 = Sat
  const weekly = (dow === 0 || dow === 6) ? -1800 : 600;
  const noise = (rng() - 0.5) * 1400;
  visitors.push(Math.round(trend + weekly + noise));
}

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "area-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 30, fontWeight: "bold" },
  },
  tooltip: {
    trigger: "axis",
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    textStyle: { color: t.ink, fontSize: 14 },
    valueFormatter: (v) => `${v.toLocaleString()} visitors`,
  },
  grid: { left: 130, right: 70, top: 100, bottom: 95, borderWidth: 0 },
  xAxis: {
    type: "category",
    data: dates,
    boundaryGap: false,
    name: "Date (May 2026)",
    nameLocation: "middle",
    nameGap: 58,
    nameTextStyle: { color: t.inkSoft, fontSize: 20, fontWeight: "normal" },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 16,
      formatter: (val) => val.slice(-2), // show day-of-month only
      interval: 2,
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    min: 0,
    name: "Daily Visitors",
    nameLocation: "middle",
    nameRotate: 90,
    nameGap: 90,
    nameTextStyle: { color: t.inkSoft, fontSize: 20, fontWeight: "normal" },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 16,
      formatter: (v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : `${v}`,
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "line",
      data: visitors,
      smooth: true,
      symbol: "circle",
      symbolSize: 8,
      showSymbol: false,
      lineStyle: { color: t.palette[0], width: 3 },
      itemStyle: { color: t.palette[0], borderColor: t.pageBg, borderWidth: 2 },
      // ECharts-distinctive: vertical LinearGradient fill from line down to axis
      areaStyle: {
        opacity: 0.85,
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: t.palette[0] + "B3" }, // ~70% alpha at top
          { offset: 1, color: t.palette[0] + "1A" }, // ~10% alpha at axis
        ]),
      },
      emphasis: { focus: "series" },
    },
  ],
});
