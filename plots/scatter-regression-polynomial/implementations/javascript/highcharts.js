// anyplot.ai
// scatter-regression-polynomial: Scatter Plot with Polynomial Regression
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-11

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Small fixed-seed LCG — Math.random() is not reproducible in the browser.
let seed = 42;
function rand() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function gaussian() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// Crop yield response to fertilizer dose — a textbook diminishing-returns
// curve: yield climbs steeply at first, then flattens and tips over past the
// agronomic optimum, so a quadratic captures the pattern a line cannot.
const pointCount = 80;
const fertilizer = [];
const cropYield = [];
for (let i = 0; i < pointCount; i++) {
  const dose = 5 + rand() * 195; // kg/hectare, 5-200
  const trueYield = 2.1 + 0.085 * dose - 0.00021 * dose * dose;
  fertilizer.push(dose);
  cropYield.push(Math.max(0, trueYield + gaussian() * 0.9));
}

// --- Quadratic least-squares fit (normal equations + Gaussian elimination) -
function polyfit(xs, ys, degree) {
  const m = degree + 1;
  const xtx = Array.from({ length: m }, () => new Array(m).fill(0));
  const xty = new Array(m).fill(0);
  for (let i = 0; i < xs.length; i++) {
    const powers = new Array(2 * m - 1);
    let p = 1;
    for (let k = 0; k < powers.length; k++) {
      powers[k] = p;
      p *= xs[i];
    }
    for (let r = 0; r < m; r++) {
      xty[r] += powers[r] * ys[i];
      for (let c = 0; c < m; c++) xtx[r][c] += powers[r + c];
    }
  }
  for (let col = 0; col < m; col++) {
    let pivot = col;
    for (let r = col + 1; r < m; r++) {
      if (Math.abs(xtx[r][col]) > Math.abs(xtx[pivot][col])) pivot = r;
    }
    [xtx[col], xtx[pivot]] = [xtx[pivot], xtx[col]];
    [xty[col], xty[pivot]] = [xty[pivot], xty[col]];
    for (let r = col + 1; r < m; r++) {
      const factor = xtx[r][col] / xtx[col][col];
      for (let c = col; c < m; c++) xtx[r][c] -= factor * xtx[col][c];
      xty[r] -= factor * xty[col];
    }
  }
  const coeffs = new Array(m).fill(0);
  for (let r = m - 1; r >= 0; r--) {
    let sum = xty[r];
    for (let c = r + 1; c < m; c++) sum -= xtx[r][c] * coeffs[c];
    coeffs[r] = sum / xtx[r][r];
  }
  return coeffs; // [c0, c1, c2] for y = c0 + c1*x + c2*x^2
}

const [c0, c1, c2] = polyfit(fertilizer, cropYield, 2);
const predict = (x) => c0 + c1 * x + c2 * x * x;

const meanYield = cropYield.reduce((a, b) => a + b, 0) / pointCount;
let ssRes = 0;
let ssTot = 0;
for (let i = 0; i < pointCount; i++) {
  ssRes += (cropYield[i] - predict(fertilizer[i])) ** 2;
  ssTot += (cropYield[i] - meanYield) ** 2;
}
const rSquared = 1 - ssRes / ssTot;

const xMin = Math.min(...fertilizer);
const xMax = Math.max(...fertilizer);
const curveSteps = 100;
const curvePoints = [];
for (let i = 0; i <= curveSteps; i++) {
  const x = xMin + ((xMax - xMin) * i) / curveSteps;
  curvePoints.push([x, predict(x)]);
}

const equation = `y = ${c2.toFixed(4)}x² ${c1 >= 0 ? "+" : "−"} ${Math.abs(c1).toFixed(3)}x ${c0 >= 0 ? "+" : "−"} ${Math.abs(c0).toFixed(2)}`;
const fitSummary = `${equation}    |    R² = ${rSquared.toFixed(3)}`;

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

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
    text: "scatter-regression-polynomial · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: fitSummary,
    style: { color: t.inkSoft, fontSize: "16px" },
  },
  xAxis: {
    title: {
      text: "Fertilizer Applied (kg/hectare)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Crop Yield (tons/hectare)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
  },
  series: [
    {
      type: "scatter",
      name: "Field Trials",
      data: fertilizer.map((x, i) => [x, cropYield[i]]),
      color: hexToRgba(t.palette[0], 0.65),
      marker: { radius: 5.5, lineWidth: 0 },
    },
    {
      type: "spline",
      name: "Quadratic Fit",
      data: curvePoints,
      color: t.palette[1],
      lineWidth: 3,
      marker: { enabled: false },
      enableMouseTracking: false,
    },
  ],
});
