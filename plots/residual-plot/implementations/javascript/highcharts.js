// anyplot.ai
// residual-plot: Residual Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
// Simulated house-price regression: fitted values (predicted price, $k) vs.
// residuals (observed - predicted), with mild heteroscedasticity so the
// diagnostic value of the plot is visible (funnel-shaped spread).
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
function gaussian(rand) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const rand = lcg(42);
const n = 220;
const fitted = [];
const residuals = [];
for (let i = 0; i < n; i++) {
  const price = 150 + rand() * 500; // fitted house price, $k
  const noiseScale = 8 + price * 0.08; // variance grows with fitted value
  const residual = gaussian(rand) * noiseScale;
  fitted.push(Number(price.toFixed(1)));
  residuals.push(Number(residual.toFixed(1)));
}

const mean = residuals.reduce((a, b) => a + b, 0) / n;
const variance = residuals.reduce((a, b) => a + (b - mean) ** 2, 0) / n;
const sd = Math.sqrt(variance);
const threshold = 2 * sd;

const inlierPoints = [];
const outlierPoints = [];
for (let i = 0; i < n; i++) {
  const point = { x: fitted[i], y: residuals[i] };
  if (Math.abs(residuals[i]) > threshold) {
    outlierPoints.push(point);
  } else {
    inlierPoints.push(point);
  }
}

const xMin = Math.min(...fitted);
const xMax = Math.max(...fitted);

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "residual-plot · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: { text: "Fitted Value ($k)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    min: xMin - 20,
    max: xMax + 20,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: "Residual ($k)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      {
        value: 0,
        color: t.ink,
        width: 2,
        zIndex: 3,
      },
    ],
    plotBands: [
      {
        from: -threshold,
        to: threshold,
        color: Highcharts.color(t.inkSoft).setOpacity(0.08).get("rgba"),
        zIndex: 0,
      },
    ],
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      marker: { radius: 5, symbol: "circle" },
    },
  },
  series: [
    {
      name: "Residuals (within ±2 SD)",
      data: inlierPoints,
      color: t.palette[0],
      marker: { fillColor: Highcharts.color(t.palette[0]).setOpacity(0.65).get("rgba"), lineWidth: 0 },
    },
    {
      name: "Outliers (beyond ±2 SD)",
      data: outlierPoints,
      color: t.palette[4],
      marker: { radius: 6, lineColor: t.ink, lineWidth: 1 },
    },
  ],
});
