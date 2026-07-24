// anyplot.ai
// qq-basic: Basic Q-Q Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 84/100 | Created: 2026-07-24
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Deterministic PRNG (Park-Miller LCG) + Box-Muller normal sampler ------
let seed = 42;
function nextUniform() {
  seed = (seed * 16807) % 2147483647;
  return seed / 2147483647;
}
function nextStandardNormal() {
  const u1 = Math.max(nextUniform(), 1e-12);
  const u2 = nextUniform();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// --- Inverse standard-normal CDF (Acklam's rational approximation) --------
function normInv(p) {
  const a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2,
    1.383577518672690e2, -3.066479806614716e1, 2.506628277459239e0];
  const b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2,
    6.680131188771972e1, -1.328068155288572e1];
  const c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838e0,
    -2.549732539343734e0, 4.374664141464968e0, 2.938163982698783e0];
  const d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996e0,
    3.754408661907416e0];
  const pLow = 0.02425;
  const pHigh = 1 - pLow;
  if (p < pLow) {
    const q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
      ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  if (p <= pHigh) {
    const q = p - 0.5;
    const r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
      (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  const q = Math.sqrt(-2 * Math.log(1 - p));
  return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
    ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
}

// --- Data: standardized residuals from a precision gauge calibration run ---
// (z-scores; a Q-Q plot against the standard normal tests whether the
// instrument's error distribution supports the normality assumption behind
// its control-chart limits)
const n = 100;
const residuals = [];
for (let i = 0; i < n; i++) residuals.push(nextStandardNormal());
residuals.sort((x, y) => x - y);

const qqPoints = residuals.map((sampleQuantile, i) => ({
  x: normInv((i + 0.5) / n),
  y: sampleQuantile,
}));

// 45-degree reference line spanning the data range, with a little padding
const allCoords = qqPoints.flatMap((p) => [p.x, p.y]);
const lo = Math.min(...allCoords);
const hi = Math.max(...allCoords);
const pad = (hi - lo) * 0.08;
const referenceLine = [
  { x: lo - pad, y: lo - pad },
  { x: hi + pad, y: hi + pad },
];

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement('canvas');
document.getElementById('container').appendChild(canvas);

// --- Title — scale font size for length (baseline: 22px at 67 chars) -------
const titleText = 'Calibration Residuals · qq-basic · javascript · chartjs · anyplot.ai';
const titleSize = Math.max(14, Math.round(22 * 67 / titleText.length));

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: 'scatter',
  data: {
    datasets: [
      {
        type: 'line',
        label: 'Reference Line (y = x)',
        data: referenceLine,
        borderColor: t.ink,
        borderDash: [10, 6],
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
        order: 2,
      },
      {
        type: 'scatter',
        label: 'Sample vs. Theoretical',
        data: qqPoints,
        backgroundColor: `${t.palette[0]}CC`,
        borderColor: t.pageBg,
        borderWidth: 1,
        pointRadius: 6,
        pointHoverRadius: 8,
        order: 1,
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
        text: titleText,
        color: t.ink,
        font: { size: titleSize, weight: '500' },
        padding: { top: 8, bottom: 16 },
      },
      legend: {
        labels: { color: t.ink, font: { size: 15 }, boxWidth: 22, padding: 14 },
      },
    },
    scales: {
      x: {
        title: { display: true, text: 'Theoretical Quantiles', color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
      },
      y: {
        title: { display: true, text: 'Sample Quantiles', color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
      },
    },
  },
});
