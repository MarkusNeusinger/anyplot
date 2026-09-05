// anyplot.ai
// lift-curve: Model Lift Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fraud-detection scenario) --------------
// Tiny fixed-seed LCG — the browser has no seeded Math.random().
function makeLcg(seed) {
  let state = seed >>> 0;
  return function lcg() {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rng = makeLcg(42);

const SAMPLE_COUNT = 3000;
const transactions = [];
for (let i = 0; i < SAMPLE_COUNT; i++) {
  // Latent risk, skewed toward zero — most transactions are low risk.
  const risk = Math.pow(rng(), 3);
  const fraudProbability = Math.min(0.95, risk * 0.9 + 0.02);
  const isFraud = rng() < fraudProbability ? 1 : 0;
  // Model score correlates with risk but includes noise (imperfect model).
  const noise = (rng() - 0.5) * 0.3;
  const score = Math.max(0, Math.min(1, risk + noise));
  transactions.push({ isFraud, score });
}

const rankedByScore = transactions.slice().sort((a, b) => b.score - a.score);
const cumulativeFraud = new Array(SAMPLE_COUNT + 1).fill(0);
for (let i = 0; i < SAMPLE_COUNT; i++) {
  cumulativeFraud[i + 1] = cumulativeFraud[i] + rankedByScore[i].isFraud;
}
const totalFraud = cumulativeFraud[SAMPLE_COUNT];
const baselineRate = totalFraud / SAMPLE_COUNT;

const liftPoints = [];
for (let percent = 1; percent <= 100; percent++) {
  const targeted = Math.max(1, Math.round((percent / 100) * SAMPLE_COUNT));
  const responseRate = cumulativeFraud[targeted] / targeted;
  liftPoints.push({ x: percent, y: responseRate / baselineRate });
}

const DECILE_STEP = 10;
// Deciles called out with an explicit numeric label (spec: "actual values at
// key percentiles"); FOCUS_DECILE also gets a larger marker as the chart's
// single focal point.
const CALLOUT_DECILES = [10, 30];
const FOCUS_DECILE = 10;

// --- Mount -------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Plugins ---------------------------------------------------------------
// Draws "3.1x at 10%" callouts above the CALLOUT_DECILES markers.
const decileCalloutPlugin = {
  id: "decileCallout",
  afterDatasetsDraw(chart) {
    const meta = chart.getDatasetMeta(0);
    const { ctx, chartArea } = chart;
    ctx.save();
    ctx.font = "bold 15px sans-serif";
    ctx.fillStyle = t.ink;
    ctx.textAlign = "left";
    // Offset up-and-right of the marker: the falling curve approaches from
    // the upper-left and departs to the lower-right, so that quadrant stays clear.
    for (const percent of CALLOUT_DECILES) {
      const point = meta.data[percent - 1];
      if (!point) continue;
      const value = liftPoints[percent - 1].y;
      const labelY = Math.max(point.y - 22, chartArea.top + 14);
      ctx.fillText(`${value.toFixed(1)}x at ${percent}%`, point.x + 14, labelY);
    }
    ctx.restore();
  },
};

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  plugins: [decileCalloutPlugin],
  data: {
    datasets: [
      {
        label: "Model lift",
        data: liftPoints,
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        borderWidth: 3,
        pointBackgroundColor: t.palette[0],
        pointBorderColor: t.pageBg,
        pointBorderWidth: 2,
        pointRadius: (ctx) => {
          const percent = ctx.dataIndex + 1;
          if (percent === FOCUS_DECILE) return 8;
          return percent % DECILE_STEP === 0 ? 6 : 0;
        },
        pointHoverRadius: 7,
        tension: 0.15,
        fill: false,
      },
      {
        label: "Random baseline (no lift)",
        data: [
          { x: 0, y: 1 },
          { x: 100, y: 1 },
        ],
        borderColor: t.ink,
        backgroundColor: t.pageBg,
        borderWidth: 2,
        borderDash: [8, 4],
        pointBackgroundColor: t.pageBg,
        pointBorderColor: t.ink,
        pointBorderWidth: 2,
        pointRadius: 0,
        fill: false,
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
        text: "lift-curve · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
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
        min: 0,
        max: 100,
        title: { display: true, text: "Population Targeted (%)", color: t.ink, font: { size: 18 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, callback: (v) => `${v}%` },
        grid: { display: false },
      },
      y: {
        beginAtZero: true,
        title: { display: true, text: "Cumulative Lift Ratio", color: t.ink, font: { size: 18 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, callback: (v) => `${v}x` },
        grid: { color: t.grid },
      },
    },
  },
});
