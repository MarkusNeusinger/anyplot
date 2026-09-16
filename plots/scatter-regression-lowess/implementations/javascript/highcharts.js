// anyplot.ai
// scatter-regression-lowess: Scatter Plot with LOWESS Regression
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Reproducible PRNG (LCG + Box-Muller for gaussian noise) ---------------
let lcgState = 20260909;
function uniform() {
  lcgState = (1664525 * lcgState + 1013904223) >>> 0;
  return lcgState / 4294967296;
}
function gaussian(mean, std) {
  const u1 = Math.max(uniform(), 1e-9);
  const u2 = uniform();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + std * z;
}

// --- Data: ad-spend saturation curve with fatigue dip -----------------------
// Weekly sales response to advertising spend: steep early gains, diminishing
// returns as spend saturates the audience, then a mild ad-fatigue decline —
// a non-monotonic relationship no single parametric curve captures cleanly.
const POINT_COUNT = 200;
const adSpend = [];
const weeklySales = [];
for (let i = 0; i < POINT_COUNT; i++) {
  const spend = uniform() * 100;
  const saturation = 22 + 58 * (1 - Math.exp(-spend / 22));
  const fatigue = spend > 65 ? 0.22 * (spend - 65) : 0;
  const sales = saturation - fatigue + gaussian(0, 5.5);
  adSpend.push(Math.round(spend * 10) / 10);
  weeklySales.push(Math.round(Math.max(sales, 0) * 10) / 10);
}

// --- LOWESS smoothing (local weighted linear regression) -------------------
// Tricube-weighted local linear fit evaluated on a dense grid across the
// x-range; frac controls the neighborhood fraction used at each grid point.
function tricube(u) {
  return u < 1 ? Math.pow(1 - Math.pow(u, 3), 3) : 0;
}

function lowess(xs, ys, frac, gridSize) {
  const n = xs.length;
  const neighbors = Math.max(2, Math.round(frac * n));
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const fitted = [];
  for (let g = 0; g < gridSize; g++) {
    const xg = xMin + ((xMax - xMin) * g) / (gridSize - 1);
    const distances = xs.map((xi) => Math.abs(xi - xg)).sort((a, b) => a - b);
    const bandwidth = Math.max(distances[neighbors - 1], 1e-6);

    let s0 = 0;
    let s1 = 0;
    let s2 = 0;
    let sy = 0;
    let sxy = 0;
    for (let i = 0; i < n; i++) {
      const w = tricube(Math.abs(xs[i] - xg) / bandwidth);
      if (w === 0) continue;
      s0 += w;
      s1 += w * xs[i];
      s2 += w * xs[i] * xs[i];
      sy += w * ys[i];
      sxy += w * xs[i] * ys[i];
    }
    const denom = s0 * s2 - s1 * s1;
    const slope = denom !== 0 ? (s0 * sxy - s1 * sy) / denom : 0;
    const intercept = (sy - slope * s1) / s0;
    fitted.push([xg, intercept + slope * xg]);
  }
  return fitted;
}

const lowessCurve = lowess(adSpend, weeklySales, 0.35, 120);

// --- Story markers: find where the LOWESS curve peaks (saturation point) ---
// then declines (ad fatigue) — drive the zone/band thresholds from the fitted
// curve itself rather than a hard-coded spend value.
const xMax = Math.max(...adSpend);
let peakIndex = 0;
for (let i = 1; i < lowessCurve.length; i++) {
  if (lowessCurve[i][1] > lowessCurve[peakIndex][1]) peakIndex = i;
}
const peakX = lowessCurve[peakIndex][0];

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
    text: "scatter-regression-lowess · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "LOWESS trend, bandwidth frac = 0.35",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: {
      text: "Advertising Spend ($1,000s)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineWidth: 0,
    tickWidth: 0,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotBands: [
      {
        from: peakX,
        to: xMax,
        color: Highcharts.color(t.amber).setOpacity(0.1).get("rgba"),
        label: {
          text: "Ad-fatigue region",
          align: "right",
          x: -8,
          y: 16,
          style: { color: t.inkSoft, fontSize: "12px", fontStyle: "italic" },
        },
      },
    ],
    plotLines: [
      {
        value: peakX,
        color: t.inkSoft,
        width: 1,
        dashStyle: "ShortDash",
        label: {
          text: `Saturation ~$${Math.round(peakX)}k`,
          rotation: 0,
          y: -6,
          style: { color: t.inkSoft, fontSize: "12px" },
        },
      },
    ],
  },
  yAxis: {
    title: {
      text: "Weekly Sales (units)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineWidth: 0,
    tickWidth: 0,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    enabled: true,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      marker: {
        radius: 6,
        fillColor: Highcharts.color(t.palette[0]).setOpacity(0.7).get("rgba"),
        lineWidth: 0,
      },
      states: { hover: { halo: { size: 0 } } },
    },
  },
  tooltip: {
    pointFormat: "Spend: <b>${point.x}k</b><br/>Sales: <b>{point.y}</b> units",
  },
  series: [
    {
      type: "scatter",
      name: "Weekly observations",
      data: adSpend.map((x, i) => [x, weeklySales[i]]),
      color: t.palette[0],
    },
    {
      type: "line",
      name: "LOWESS smoothed trend",
      data: lowessCurve,
      color: t.ink,
      lineWidth: 3,
      marker: { enabled: false },
      enableMouseTracking: false,
      zoneAxis: "x",
      zones: [
        { value: peakX, color: t.ink },
        { color: t.amber, dashStyle: "Dash" },
      ],
    },
  ],
});
