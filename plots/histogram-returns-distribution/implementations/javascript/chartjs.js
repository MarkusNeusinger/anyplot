// anyplot.ai
// histogram-returns-distribution: Returns Distribution Histogram
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily returns (%) for a single equity over one trading year, generated with a
// fixed-seed LCG. A small mixture of wide-vol days is blended in so the
// empirical distribution shows the fat tails real markets exhibit versus a
// pure Gaussian.
function makeLcg(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rng = makeLcg(42);
function randNormal() {
  const u1 = Math.max(rng(), 1e-9);
  const u2 = rng();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const N_OBS = 252;
const DRIFT = 0.04; // mean daily return, %
const VOL = 1.05; // baseline daily volatility, %
const returns = [];
for (let i = 0; i < N_OBS; i++) {
  const fatTailDay = rng() < 0.07;
  const vol = fatTailDay ? VOL * 3.2 : VOL;
  returns.push(DRIFT + vol * randNormal());
}

// --- Stats -------------------------------------------------------------------
const n = returns.length;
const mean = returns.reduce((a, b) => a + b, 0) / n;
const variance = returns.reduce((a, b) => a + (b - mean) ** 2, 0) / n;
const std = Math.sqrt(variance);
const skewness = returns.reduce((a, b) => a + ((b - mean) / std) ** 3, 0) / n;
const kurtosis = returns.reduce((a, b) => a + ((b - mean) / std) ** 4, 0) / n - 3;

// --- Histogram (density-normalized) -------------------------------------------
const BIN_COUNT = 30;
const lo = Math.min(...returns);
const hi = Math.max(...returns);
const binWidth = (hi - lo) / BIN_COUNT;
const counts = new Array(BIN_COUNT).fill(0);
returns.forEach((r) => {
  const idx = Math.min(BIN_COUNT - 1, Math.max(0, Math.floor((r - lo) / binWidth)));
  counts[idx]++;
});
const density = counts.map((c) => c / (n * binWidth));
const binCenters = Array.from({ length: BIN_COUNT }, (_, i) => lo + (i + 0.5) * binWidth);
const labels = binCenters.map((c) => `${c.toFixed(1)}%`);

// Fitted normal curve sampled at each bin center, so it overlays the category axis exactly.
function normalPdf(x, mu, sigma) {
  return Math.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * Math.sqrt(2 * Math.PI));
}
const normalCurve = binCenters.map((c) => normalPdf(c, mean, std));

// Tail bins beyond +/-2 std get the semantic loss/extreme-event color.
const tailLow = mean - 2 * std;
const tailHigh = mean + 2 * std;
const barColors = binCenters.map((c) => (c < tailLow || c > tailHigh ? t.palette[4] : t.palette[0]));

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Stats box plugin ---------------------------------------------------------
const statsBoxPlugin = {
  id: "statsBox",
  afterDraw(chart) {
    const { ctx, chartArea } = chart;
    const lines = [
      `Mean:  ${mean.toFixed(2)}%`,
      `Std Dev:  ${std.toFixed(2)}%`,
      `Skewness:  ${skewness.toFixed(2)}`,
      `Kurtosis:  ${kurtosis.toFixed(2)}`,
    ];
    const fontSize = 15;
    ctx.save();
    ctx.font = `${fontSize}px sans-serif`;
    const padding = 16;
    const lineHeight = fontSize * 1.6;
    const boxWidth = Math.max(...lines.map((l) => ctx.measureText(l).width)) + padding * 2;
    const boxHeight = lines.length * lineHeight + padding * 1.2;
    const boxX = chartArea.right - boxWidth - 24;
    const boxY = chartArea.top + 16;

    ctx.fillStyle = t.elevatedBg;
    ctx.strokeStyle = t.grid;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(boxX, boxY, boxWidth, boxHeight, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = t.ink;
    ctx.textBaseline = "top";
    lines.forEach((line, i) => {
      ctx.fillText(line, boxX + padding, boxY + padding * 0.6 + i * lineHeight);
    });
    ctx.restore();
  },
};

// --- Chart ---------------------------------------------------------------------
new Chart(canvas, {
  data: {
    labels,
    datasets: [
      {
        type: "bar",
        label: "Daily Returns",
        data: density,
        backgroundColor: barColors,
        borderWidth: 0,
        categoryPercentage: 1.0,
        barPercentage: 0.98,
        order: 2,
      },
      {
        type: "line",
        label: "Normal (Fitted)",
        data: normalCurve,
        borderColor: t.palette[2],
        backgroundColor: "transparent",
        borderWidth: 3.5,
        pointRadius: 0,
        tension: 0.35,
        order: 1,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 8 } },
    plugins: {
      title: {
        display: true,
        text: "histogram-returns-distribution · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 21, weight: "500" },
        padding: { bottom: 8 },
      },
      subtitle: {
        display: true,
        text: "Matte-red bars mark returns beyond ±2σ (tail risk)",
        color: t.inkSoft,
        font: { size: 15, style: "italic" },
        padding: { bottom: 20 },
      },
      legend: {
        labels: { color: t.ink, font: { size: 16 }, boxWidth: 24 },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 }, maxTicksLimit: 12, maxRotation: 0 },
        grid: { display: false },
        title: { display: true, text: "Daily Return (%)", color: t.ink, font: { size: 18 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Density", color: t.ink, font: { size: 18 } },
        beginAtZero: true,
      },
    },
  },
  plugins: [statsBoxPlugin],
});
