// anyplot.ai
// line-confidence: Line Plot with Confidence Interval
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
}
const rand = lcg(42);

const days = 60;
const startDate = new Date(2026, 0, 1);
const dates = [];
for (let i = 0; i < days; i++) {
  const d = new Date(startDate);
  d.setDate(d.getDate() + i);
  dates.push(d.toLocaleDateString("en-US", { month: "short", day: "numeric" }));
}

// Forecast model: trend + weekly seasonality + noise. Uncertainty is tight
// over the observed window (days 0-29) and widens across the forecast
// horizon (days 30-59), matching how prediction intervals grow with lead time.
const predicted = [];
const lower = [];
const upper = [];
const baseUsers = 4200;
for (let i = 0; i < days; i++) {
  const trend = i * 18;
  const weekly = Math.sin((i / 7) * Math.PI * 2) * 220;
  const noise = (rand() - 0.5) * 150;
  const value = baseUsers + trend + weekly + noise;
  const horizonFactor = i < 30 ? 1 : 1 + (i - 30) * 0.06;
  const margin = 180 * horizonFactor;
  predicted.push(Math.round(value));
  lower.push(Math.round(value - margin));
  upper.push(Math.round(value + margin));
}
const band = upper.map((u, i) => u - lower[i]);

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
const title = "Daily Active Users Forecast · line-confidence · javascript · echarts · anyplot.ai";

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  color: t.palette,
  title: {
    text: title,
    left: "center",
    textStyle: { color: t.ink, fontSize: 18, fontWeight: 500 },
  },
  legend: {
    data: [
      { name: "Predicted Active Users", icon: "roundRect" },
      { name: "Prediction Interval", icon: "roundRect" },
    ],
    top: 56,
    textStyle: { color: t.ink, fontSize: 16 },
  },
  grid: { left: 100, right: 60, top: 130, bottom: 90 },
  tooltip: {
    trigger: "axis",
    formatter: (params) => {
      const shown = params.filter((p) => p.seriesName !== "Lower Bound");
      const lines = shown.map((p) => `${p.marker} ${p.seriesName}: ${p.value.toLocaleString()}`);
      return `${params[0].axisValueLabel}<br/>${lines.join("<br/>")}`;
    },
  },
  xAxis: {
    type: "category",
    data: dates,
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: 4 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Daily Active Users",
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Lower Bound",
      type: "line",
      data: lower,
      stack: "confidence-band",
      symbol: "none",
      lineStyle: { opacity: 0 },
      silent: true,
      tooltip: { show: false },
    },
    {
      name: "Prediction Interval",
      type: "line",
      data: band,
      stack: "confidence-band",
      symbol: "none",
      lineStyle: { opacity: 0 },
      itemStyle: { color: t.palette[0], opacity: 0.25 },
      areaStyle: { color: t.palette[0], opacity: 0.25 },
    },
    {
      name: "Predicted Active Users",
      type: "line",
      data: predicted,
      symbol: "none",
      lineStyle: { width: 3.5, color: t.palette[0] },
      itemStyle: { color: t.palette[0] },
      z: 3,
    },
  ],
});
