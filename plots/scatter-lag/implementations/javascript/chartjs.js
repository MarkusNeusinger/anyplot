// anyplot.ai
// scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
// Library: chartjs 4.4.7 | JavaScript 22.23.0
// Quality: 85/100 | Created: 2026-06-24

const t = window.ANYPLOT_TOKENS;

// Deterministic LCG pseudo-random (seed 42)
let _s = 42;
function rand() {
  _s = (Math.imul(1664525, _s) + 1013904223) >>> 0;
  return _s / 0x100000000;
}

// AR(1) time series: y(t) = 0.85 * y(t-1) + noise
const N = 300;
const PHI = 0.85;
const series = new Array(N);
series[0] = 0.0;
for (let i = 1; i < N; i++) {
  series[i] = PHI * series[i - 1] + (rand() - 0.5) * 2.0;
}

// Lag-1 scatter pairs: x = y(t), y = y(t+1)
const lagData = [];
for (let i = 0; i < N - 1; i++) {
  lagData.push({ x: series[i], y: series[i + 1] });
}

// Interpolate color along imprint_seq by time index (early: green → late: blue)
function hexRgb(h) {
  return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
}
function lerpColor(c1, c2, frac) {
  const [r1, g1, b1] = hexRgb(c1);
  const [r2, g2, b2] = hexRgb(c2);
  return `rgba(${Math.round(r1 + (r2 - r1) * frac)},${Math.round(g1 + (g2 - g1) * frac)},${Math.round(b1 + (b2 - b1) * frac)},0.82)`;
}
const pointColors = lagData.map((_, i) => lerpColor(t.seq[0], t.seq[1], i / (lagData.length - 1)));

// Axis range: equal scale on both axes so y=x is truly at 45°
const allVals = series;
const vMin = Math.min(...allVals);
const vMax = Math.max(...allVals);
const pad = (vMax - vMin) * 0.06;
const axisMin = Math.floor((vMin - pad) * 10) / 10;
const axisMax = Math.ceil((vMax + pad) * 10) / 10;

// Diagonal reference line (y = x)
const diagData = [
  { x: axisMin, y: axisMin },
  { x: axisMax, y: axisMax },
];

// Pearson r at lag-1
const xs = lagData.map(d => d.x);
const ys = lagData.map(d => d.y);
const n = lagData.length;
const mX = xs.reduce((a, b) => a + b, 0) / n;
const mY = ys.reduce((a, b) => a + b, 0) / n;
let num = 0, ssX = 0, ssY = 0;
for (let i = 0; i < n; i++) {
  const dx = xs[i] - mX;
  const dy = ys[i] - mY;
  num += dx * dy;
  ssX += dx * dx;
  ssY += dy * dy;
}
const rVal = (num / Math.sqrt(ssX * ssY)).toFixed(3);

// Background fill plugin
const bgPlugin = {
  id: "bg",
  beforeDraw(chart) {
    chart.ctx.fillStyle = t.pageBg;
    chart.ctx.fillRect(0, 0, chart.width, chart.height);
  },
};

// Correlation coefficient annotation drawn in the upper-left of the plot area
const rAnnotation = {
  id: "rAnnotation",
  afterDatasetsDraw(chart) {
    const { ctx, chartArea: { left, top } } = chart;
    ctx.save();
    ctx.font = "600 15px sans-serif";
    ctx.fillStyle = t.ink;
    ctx.fillText(`r = ${rVal}`, left + 14, top + 22);
    ctx.restore();
  },
};

// Mount canvas
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Chart
new Chart(canvas, {
  type: "scatter",
  plugins: [bgPlugin, rAnnotation],
  data: {
    datasets: [
      {
        label: "y(t) vs y(t+1)",
        data: lagData,
        backgroundColor: pointColors,
        borderColor: "transparent",
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: "y = x  (no autocorrelation)",
        type: "line",
        data: diagData,
        borderColor: t.inkSoft,
        borderWidth: 2,
        borderDash: [8, 5],
        pointRadius: 0,
        fill: false,
        tension: 0,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "AR(1) Process · scatter-lag · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 20, weight: "600" },
        padding: { top: 8, bottom: 4 },
      },
      subtitle: {
        display: true,
        text: "Points colored by time index (early: green → late: blue)",
        color: t.inkSoft,
        font: { size: 13 },
        padding: { bottom: 12 },
      },
      legend: {
        position: "bottom",
        labels: {
          color: t.ink,
          font: { size: 14 },
          padding: 20,
          filter(item) {
            return item.datasetIndex === 1;
          },
        },
      },
      tooltip: {
        callbacks: {
          label(ctx) {
            return `y(t) = ${ctx.parsed.x.toFixed(3)},  y(t+1) = ${ctx.parsed.y.toFixed(3)}`;
          },
        },
      },
    },
    scales: {
      x: {
        min: axisMin,
        max: axisMax,
        title: {
          display: true,
          text: "y(t)",
          color: t.ink,
          font: { size: 16 },
          padding: { top: 6 },
        },
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { color: t.grid },
      },
      y: {
        min: axisMin,
        max: axisMax,
        title: {
          display: true,
          text: "y(t + 1)",
          color: t.ink,
          font: { size: 16 },
          padding: { bottom: 6 },
        },
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { color: t.grid },
      },
    },
  },
});
