// anyplot.ai
// line-timeseries: Time Series Line Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-05
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily average temperature readings (°C) across 2024 (leap year), with a
// seasonal cycle plus noise from a tiny fixed-seed LCG (no seeded RNG in-browser).
let seed = 42;
function nextRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const startDate = Date.UTC(2024, 0, 1);
const dayMs = 24 * 3600 * 1000;
const daysInYear = 366;
const temperatures = [];
for (let day = 0; day < daysInYear; day++) {
  const seasonal = 12 + 10 * Math.sin(((day - 100) / 365) * 2 * Math.PI);
  const noise = (nextRandom() - 0.5) * 4;
  const value = Math.round((seasonal + noise) * 10) / 10;
  temperatures.push([startDate + day * dayMs, value]);
}

// --- Chart -------------------------------------------------------------------
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
    text: "line-timeseries · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    type: "datetime",
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: "Date", style: { color: t.inkSoft, fontSize: "16px" } },
  },
  yAxis: {
    title: {
      text: "Avg. Temperature (°C)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
    line: { lineWidth: 2.5 },
  },
  series: [
    {
      name: "Avg. Temperature",
      data: temperatures,
    },
  ],
});
