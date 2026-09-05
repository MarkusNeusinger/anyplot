// anyplot.ai
// line-timeseries-rolling: Time Series with Rolling Average Overlay
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fixed-seed LCG) ------------------------
// Hourly temperature sensor readings with noise, smoothed by a 24-hour
// rolling mean to reveal the underlying diurnal trend.
let seed = 42;
function lcgRandom() {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
}

const HOURS = 240; // 10 days of hourly readings
const WINDOW = 24; // 24-hour rolling window
const startDate = Date.UTC(2024, 5, 1, 0, 0, 0);
const hourMs = 3600 * 1000;

const rawSeries = [];
for (let i = 0; i < HOURS; i += 1) {
  const timestamp = startDate + i * hourMs;
  const diurnal = 6 * Math.sin((2 * Math.PI * (i % 24)) / 24 - Math.PI / 2);
  const drift = 2 * Math.sin((2 * Math.PI * i) / (24 * 6));
  const noise = (lcgRandom() - 0.5) * 3.5;
  const temperature = 18 + diurnal + drift + noise;
  rawSeries.push([timestamp, Number(temperature.toFixed(2))]);
}

const rollingSeries = [];
for (let i = WINDOW - 1; i < HOURS; i += 1) {
  let sum = 0;
  for (let w = i - WINDOW + 1; w <= i; w += 1) {
    sum += rawSeries[w][1];
  }
  rollingSeries.push([rawSeries[i][0], Number((sum / WINDOW).toFixed(2))]);
}

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "line-timeseries-rolling · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Hourly sensor temperature with 24-hour rolling average",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    type: "datetime",
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: "Date", style: { color: t.inkSoft, fontSize: "16px" } },
  },
  yAxis: {
    title: {
      text: "Temperature (°C)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
  },
  series: [
    {
      name: "Raw Data",
      data: rawSeries,
      color: t.palette[0],
      opacity: 0.35,
      lineWidth: 1.5,
      zIndex: 1,
    },
    {
      name: "Rolling Average (24-Hour)",
      data: rollingSeries,
      color: t.palette[2],
      lineWidth: 3.5,
      zIndex: 2,
    },
  ],
});
