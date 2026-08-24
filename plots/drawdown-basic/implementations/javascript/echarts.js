// anyplot.ai
// drawdown-basic: Drawdown Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-24

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Fixed-seed LCG + Box-Muller for reproducible pseudo-normal daily returns.
function lcg(seed) {
  let state = seed >>> 0;
  return function () {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = lcg(20260111);
function gaussian() {
  const u1 = rand() || 1e-9;
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// Trading dates: ~3 years of weekdays starting 2021-01-04.
const dates = [];
const cursor = new Date(Date.UTC(2021, 0, 4));
while (dates.length < 756) {
  const weekday = cursor.getUTCDay();
  if (weekday !== 0 && weekday !== 6) dates.push(new Date(cursor.getTime()));
  cursor.setUTCDate(cursor.getUTCDate() + 1);
}

// Simulated NAV: uptrend, then a bear-market decline, then a recovery leg.
const nav = [100];
for (let i = 1; i < dates.length; i++) {
  let mu, sigma;
  if (i < 350) {
    mu = 0.0009;
    sigma = 0.0085;
  } else if (i < 500) {
    mu = -0.0022;
    sigma = 0.016;
  } else {
    mu = 0.0012;
    sigma = 0.01;
  }
  nav.push(nav[i - 1] * (1 + mu + sigma * gaussian()));
}

// Drawdown = decline from the running maximum NAV, as a percentage.
const runningMax = [];
let peak = -Infinity;
for (let i = 0; i < nav.length; i++) {
  peak = Math.max(peak, nav[i]);
  runningMax.push(peak);
}
const drawdown = nav.map((v, i) => ((v - runningMax[i]) / runningMax[i]) * 100);

let maxDdIdx = 0;
for (let i = 1; i < drawdown.length; i++) {
  if (drawdown[i] < drawdown[maxDdIdx]) maxDdIdx = i;
}
let peakIdx = maxDdIdx;
for (let i = maxDdIdx; i >= 0; i--) {
  if (drawdown[i] === 0) {
    peakIdx = i;
    break;
  }
}
let recoveryIdx = null;
for (let i = maxDdIdx + 1; i < drawdown.length; i++) {
  if (drawdown[i] >= -0.001) {
    recoveryIdx = i;
    break;
  }
}

const navSeriesData = dates.map((d, i) => [d.getTime(), Number(nav[i].toFixed(2))]);
const drawdownSeriesData = dates.map((d, i) => [d.getTime(), Number(drawdown[i].toFixed(2))]);

const maxDdPct = drawdown[maxDdIdx].toFixed(1);
const declineDays = maxDdIdx - peakIdx;
const statsText =
  recoveryIdx !== null
    ? `Max Drawdown: ${maxDdPct}% · Decline: ${declineDays}d · Recovery: ${recoveryIdx - maxDdIdx}d`
    : `Max Drawdown: ${maxDdPct}% · Decline: ${declineDays}d · Recovery: ongoing`;

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
const markPointData = [
  {
    name: "Max Drawdown",
    coord: [dates[maxDdIdx].getTime(), drawdown[maxDdIdx]],
    symbol: "pin",
    symbolSize: 52,
    itemStyle: { color: t.palette[4] },
    label: { color: "#FFFFFF", fontSize: 13, fontWeight: 600, formatter: () => `${maxDdPct}%` },
  },
];
if (recoveryIdx !== null) {
  markPointData.push({
    name: "Recovery",
    coord: [dates[recoveryIdx].getTime(), drawdown[recoveryIdx]],
    symbol: "circle",
    symbolSize: 14,
    itemStyle: { color: t.ink },
    label: { show: true, position: "top", distance: 10, color: t.ink, fontSize: 13, formatter: "Recovery" },
  });
}

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "Tech Growth Fund · drawdown-basic · javascript · echarts · anyplot.ai",
    subtext: statsText,
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 21, fontWeight: 600 },
    subtextStyle: { color: t.inkSoft, fontSize: 15 },
  },
  legend: {
    data: ["Portfolio NAV", "Drawdown"],
    top: 108,
    left: "center",
    textStyle: { color: t.ink, fontSize: 16 },
    itemWidth: 22,
    itemHeight: 12,
  },
  grid: { left: 110, right: 110, top: 172, bottom: 90 },
  xAxis: {
    type: "time",
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: [
    {
      type: "value",
      name: "Drawdown (%)",
      nameTextStyle: { color: t.inkSoft, fontSize: 14 },
      max: 0,
      position: "left",
      axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "{value}%" },
      axisLine: { show: true, lineStyle: { color: t.inkSoft } },
      splitLine: { lineStyle: { color: t.grid } },
    },
    {
      type: "value",
      name: "NAV ($)",
      nameTextStyle: { color: t.inkSoft, fontSize: 14 },
      position: "right",
      scale: true,
      axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "${value}" },
      axisLine: { show: true, lineStyle: { color: t.inkSoft } },
      splitLine: { show: false },
    },
  ],
  series: [
    {
      name: "Portfolio NAV",
      type: "line",
      yAxisIndex: 1,
      data: navSeriesData,
      symbol: "none",
      lineStyle: { color: t.palette[0], width: 2.5 },
      itemStyle: { color: t.palette[0] },
    },
    {
      name: "Drawdown",
      type: "line",
      yAxisIndex: 0,
      data: drawdownSeriesData,
      symbol: "none",
      lineStyle: { color: t.palette[4], width: 2 },
      itemStyle: { color: t.palette[4] },
      areaStyle: { color: t.palette[4], opacity: 0.32 },
      markPoint: { data: markPointData },
    },
  ],
});
