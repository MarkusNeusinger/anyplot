// anyplot.ai
// scatter-regression-lowess: Scatter Plot with LOWESS Regression
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Weekly ad-spend campaigns and their conversion rate: response rises with
// spend, plateaus, then dips slightly at very high spend (ad fatigue) — a
// non-linear pattern with no obvious closed-form model, well suited to LOWESS.
function makeRng(seed) {
  let state = seed >>> 0;
  return () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rng = makeRng(42);
function gaussian() {
  const u1 = Math.max(rng(), 1e-9);
  const u2 = rng();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const n = 150;
const adSpend = [];
for (let i = 0; i < n; i++) {
  adSpend.push(1 + (99 * i) / (n - 1) + (rng() - 0.5) * 0.6);
}
adSpend.sort((a, b) => a - b);

const conversionRate = adSpend.map((x) => {
  const rise = 8 * (1 - Math.exp(-x / 20));
  const fatigue = x > 70 ? 0.015 * Math.pow(x - 70, 1.5) : 0;
  return 2 + rise - fatigue + gaussian() * 0.9;
});

// --- LOWESS (locally weighted regression with tricube weights + two
//     bisquare robustness iterations, following Cleveland 1979) -------------
function lowess(xs, ys, frac, iterations) {
  const count = xs.length;
  const windowSize = Math.max(2, Math.round(frac * count));
  let robustWeights = new Array(count).fill(1);
  let fitted = new Array(count).fill(0);

  for (let iter = 0; iter <= iterations; iter++) {
    for (let i = 0; i < count; i++) {
      const xi = xs[i];
      const distances = xs.map((x) => Math.abs(x - xi));
      const bandwidth = [...distances].sort((a, b) => a - b)[windowSize - 1] || 1e-9;

      let sumW = 0;
      let sumWX = 0;
      let sumWY = 0;
      let sumWXX = 0;
      let sumWXY = 0;
      for (let j = 0; j < count; j++) {
        const d = distances[j] / bandwidth;
        if (d >= 1) continue;
        const w = Math.pow(1 - Math.pow(d, 3), 3) * robustWeights[j];
        sumW += w;
        sumWX += w * xs[j];
        sumWY += w * ys[j];
        sumWXX += w * xs[j] * xs[j];
        sumWXY += w * xs[j] * ys[j];
      }

      const denom = sumW * sumWXX - sumWX * sumWX;
      let slope = 0;
      let intercept = sumWY / sumW;
      if (Math.abs(denom) > 1e-9) {
        slope = (sumW * sumWXY - sumWX * sumWY) / denom;
        intercept = (sumWY - slope * sumWX) / sumW;
      }
      fitted[i] = intercept + slope * xi;
    }

    if (iter < iterations) {
      const absResiduals = ys.map((y, i) => Math.abs(y - fitted[i]));
      const sortedAbs = [...absResiduals].sort((a, b) => a - b);
      const mid = Math.floor(count / 2);
      const mad = count % 2 !== 0 ? sortedAbs[mid] : (sortedAbs[mid - 1] + sortedAbs[mid]) / 2;
      const scale = 6 * mad || 1e-9;
      robustWeights = ys.map((y, i) => {
        const u = (y - fitted[i]) / scale;
        return Math.abs(u) < 1 ? Math.pow(1 - u * u, 2) : 0;
      });
    }
  }

  return fitted;
}

const lowessFit = lowess(adSpend, conversionRate, 0.35, 2);
const curvePoints = adSpend.map((x, i) => ({ x, y: lowessFit[i] }));

// --- Helpers -----------------------------------------------------------------
function withAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const TITLE_TEXT =
  "Ad Spend vs. Conversion Rate · scatter-regression-lowess · javascript · chartjs · anyplot.ai";
const TITLE_FONT_SIZE = Math.max(15, Math.round(22 * Math.min(1, 67 / TITLE_TEXT.length)));

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        type: "scatter",
        label: "Weekly campaigns",
        data: adSpend.map((x, i) => ({ x, y: conversionRate[i] })),
        backgroundColor: withAlpha(t.palette[0], 0.6),
        borderColor: t.pageBg,
        borderWidth: 1,
        pointRadius: 5,
        pointHoverRadius: 6,
      },
      {
        type: "line",
        label: "LOWESS fit (frac = 0.35)",
        data: curvePoints,
        borderColor: t.palette[1],
        backgroundColor: t.palette[1],
        borderWidth: 3.5,
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
        text: TITLE_TEXT,
        color: t.ink,
        font: { size: TITLE_FONT_SIZE, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        position: "top",
        align: "end",
        labels: { color: t.ink, font: { size: 16 }, boxWidth: 24, usePointStyle: true },
      },
    },
    scales: {
      x: {
        type: "linear",
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Weekly Ad Spend ($1,000s)", color: t.ink, font: { size: 18 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Conversion Rate (%)", color: t.ink, font: { size: 18 } },
      },
    },
  },
});
