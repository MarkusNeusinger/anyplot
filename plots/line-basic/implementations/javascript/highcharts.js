// anyplot.ai
// line-basic: Basic Line Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 80/100 | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Hourly outdoor temperature over a 48-hour window (two-day trend)
let seed = 42;
function lcg() {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
}

const hours = Array.from({ length: 49 }, (_, i) => i);
const temperatures = hours.map((h) => {
  const diurnal = 14 + 9 * Math.sin(((h - 9) / 24) * 2 * Math.PI);
  const drift = 1.5 * Math.sin((h / 48) * Math.PI);
  const noise = (lcg() - 0.5) * 1.2;
  return Math.round((diurnal + drift + noise) * 10) / 10;
});

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
    text: "line-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: {
      text: "Hour of Observation",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    tickInterval: 6,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Temperature (°C)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineWidth: 1,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false, marker: { enabled: false } },
    line: { lineWidth: 3 },
  },
  series: [
    {
      name: "Temperature",
      data: temperatures,
      color: t.palette[0],
    },
  ],
});
