// anyplot.ai
// pp-basic: Probability-Probability (P-P) Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-09
//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data: 200 samples from a right-skewed distribution vs normal reference ---
// Deterministic LCG for reproducibility (no seeded Math.random in browser)
let seed = 987654321;
function lcg() {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 0x100000000;
}

function randn() {
  const u1 = Math.max(lcg(), 1e-10);
  const u2 = lcg();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// 200 samples with slight right skew: z + 0.3*z^2 shifts mass rightward
const n = 200;
const rawData = Array.from({ length: n }, () => {
  const z = randn();
  return z + 0.3 * z * z;
});

// Sort ascending for empirical CDF
const sorted = [...rawData].sort((a, b) => a - b);

// Fit normal: sample mean and standard deviation
const mean = sorted.reduce((s, v) => s + v, 0) / n;
const std = Math.sqrt(sorted.reduce((s, v) => s + (v - mean) ** 2, 0) / n);

// Error function (Abramowitz & Stegun, max error ~1.5e-7)
function erf(x) {
  const sign = x >= 0 ? 1 : -1;
  const a = Math.abs(x);
  const t1 = 1 / (1 + 0.3275911 * a);
  const poly =
    (((1.061405429 * t1 - 1.453152027) * t1 + 1.421413741) * t1 - 0.284496736) * t1 + 0.254829592;
  return sign * (1 - poly * t1 * Math.exp(-a * a));
}

function normCDF(x, mu, sigma) {
  return 0.5 * (1 + erf((x - mu) / (sigma * Math.SQRT2)));
}

// P-P coordinates: (theoretical CDF, empirical CDF) for each sorted observation
const ppPoints = sorted.map((val, i) => ({
  x: normCDF(val, mean, std),
  y: (i + 1) / (n + 1), // Hazen plotting position
}));

// 45-degree reference line: perfect distributional fit
const refLine = [
  { x: 0, y: 0 },
  { x: 1, y: 1 },
];

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "Empirical vs Theoretical CDF",
        data: ppPoints,
        backgroundColor: t.palette[0] + "bb",
        borderColor: t.pageBg,
        borderWidth: 1,
        pointRadius: 5,
        pointHoverRadius: 7,
      },
      {
        label: "Reference (perfect fit)",
        data: refLine,
        type: "line",
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
        text: "pp-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { top: 10, bottom: 20 },
      },
      legend: {
        labels: {
          color: t.inkSoft,
          font: { size: 14 },
          boxWidth: 14,
          padding: 16,
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: 1,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          maxTicksLimit: 6,
        },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Theoretical CDF (Normal)",
          color: t.ink,
          font: { size: 16 },
          padding: { top: 12 },
        },
      },
      y: {
        type: "linear",
        min: 0,
        max: 1,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          maxTicksLimit: 6,
        },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Empirical CDF",
          color: t.ink,
          font: { size: 16 },
          padding: { bottom: 12 },
        },
      },
    },
  },
});
