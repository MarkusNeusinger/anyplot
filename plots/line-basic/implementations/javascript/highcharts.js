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

// Overnight shading — the diurnal formula troughs at h=3 and h=27, so night
// (roughly 9pm-9am) spans these windows within the 0-48h range
const nightBandColor = Highcharts.color(t.inkSoft).setOpacity(0.06).get("rgba");
const nightBands = [
  { from: 0, to: 9, color: nightBandColor },
  { from: 21, to: 33, color: nightBandColor },
  { from: 45, to: 48, color: nightBandColor },
];

// Peak/trough callout for a clear focal point
let peakIdx = 0;
let troughIdx = 0;
temperatures.forEach((v, i) => {
  if (v > temperatures[peakIdx]) peakIdx = i;
  if (v < temperatures[troughIdx]) troughIdx = i;
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
    plotBands: nightBands,
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
    series: { animation: false },
    line: {
      lineWidth: 3,
      marker: { enabled: true, radius: 3, fillColor: t.palette[0], lineWidth: 0 },
    },
  },
  series: [
    {
      name: "Temperature",
      type: "line",
      data: temperatures,
      color: t.palette[0],
    },
    {
      name: "Peak / Trough",
      type: "scatter",
      data: [
        {
          x: peakIdx,
          y: temperatures[peakIdx],
          name: `Peak ${temperatures[peakIdx]}°C`,
          dataLabels: { verticalAlign: "bottom", y: -14 },
        },
        {
          x: troughIdx,
          y: temperatures[troughIdx],
          name: `Trough ${temperatures[troughIdx]}°C`,
          dataLabels: { verticalAlign: "top", y: 14 },
        },
      ],
      color: t.amber,
      marker: { radius: 6, lineColor: t.pageBg, lineWidth: 2 },
      dataLabels: {
        enabled: true,
        format: "{point.name}",
        style: { color: t.ink, fontSize: "13px", fontWeight: "600", textOutline: "none" },
      },
      enableMouseTracking: false,
      showInLegend: false,
      zIndex: 5,
    },
  ],
});
