// anyplot.ai
// line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// 13 standardized chemical-composition features (alcohol, acidity, phenols,
// color intensity, etc.) from a wine-cultivar dataset — a classic PCA example.
// Individual variance ratios decay geometrically with a small deterministic
// wobble (fixed-seed LCG), then are normalized so they sum to 1.0.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1103515245 + 12345) & 0x7fffffff;
    return state / 0x7fffffff;
  };
}
const rand = lcg(42);

const nComponents = 13;
const rawRatios = Array.from({ length: nComponents }, (_, i) => {
  const decay = Math.exp(-0.34 * i);
  const wobble = 1 + (rand() - 0.5) * 0.12;
  return decay * wobble;
});
const rawTotal = rawRatios.reduce((a, b) => a + b, 0);
const individualRatio = rawRatios.map((v) => v / rawTotal);

const componentLabels = individualRatio.map((_, i) => String(i + 1));
const cumulativePct = [];
individualRatio.reduce((acc, v, i) => {
  const next = acc + v;
  cumulativePct[i] = next * 100;
  return next;
}, 0);
const individualPct = individualRatio.map((v) => v * 100);

// Elbow detection (kneedle-style): the point on the cumulative curve with the
// largest perpendicular distance from the line connecting the first and last
// points — the classic scree-plot "knee".
function findElbowIndex(xs, ys) {
  const x1 = xs[0], y1 = ys[0];
  const xN = xs[xs.length - 1], yN = ys[ys.length - 1];
  const denom = Math.hypot(xN - x1, yN - y1);
  let bestIdx = 0;
  let bestDist = -1;
  xs.forEach((x, i) => {
    const dist = Math.abs((yN - y1) * x - (xN - x1) * ys[i] + xN * y1 - yN * x1) / denom;
    if (dist > bestDist) {
      bestDist = dist;
      bestIdx = i;
    }
  });
  return bestIdx;
}
const elbowIdx = findElbowIndex(
  componentLabels.map(Number),
  cumulativePct
);

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: componentLabels,
    datasets: [
      {
        type: "bar",
        label: "Individual variance",
        data: individualPct,
        backgroundColor: `${t.palette[1]}8c`,
        borderWidth: 0,
        yAxisID: "y1",
        order: 3,
      },
      {
        type: "line",
        label: "Cumulative variance",
        data: cumulativePct,
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        pointBackgroundColor: t.palette[0],
        pointBorderColor: t.pageBg,
        pointRadius: 7,
        pointBorderWidth: 2,
        borderWidth: 4,
        tension: 0,
        yAxisID: "y",
        order: 1,
      },
      {
        type: "line",
        label: "90% threshold",
        data: componentLabels.map(() => 90),
        borderColor: t.ink,
        borderDash: [10, 6],
        borderWidth: 2,
        pointRadius: 0,
        yAxisID: "y",
        order: 2,
      },
      {
        type: "line",
        label: "95% threshold",
        data: componentLabels.map(() => 95),
        borderColor: t.ink,
        borderDash: [3, 5],
        borderWidth: 2,
        pointRadius: 0,
        yAxisID: "y",
        order: 2,
      },
      {
        type: "line",
        label: "Elbow point",
        data: componentLabels.map((_, i) => (i === elbowIdx ? cumulativePct[i] : null)),
        showLine: false,
        backgroundColor: t.ink,
        borderColor: t.ink,
        pointRadius: 11,
        pointBackgroundColor: t.ink,
        pointBorderColor: t.pageBg,
        pointBorderWidth: 3,
        yAxisID: "y",
        order: 0,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 10, right: 10, bottom: 4, left: 4 } },
    plugins: {
      title: {
        display: true,
        text: "line-pca-variance-cumulative · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        position: "bottom",
        labels: { color: t.ink, font: { size: 14 }, boxWidth: 22, padding: 18 },
      },
    },
    scales: {
      x: {
        title: { display: true, text: "Number of Principal Components", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { display: false },
      },
      y: {
        position: "left",
        min: 0,
        max: 105,
        title: { display: true, text: "Cumulative Explained Variance (%)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 13 }, stepSize: 20 },
        grid: { color: t.grid },
      },
      y1: {
        position: "right",
        min: 0,
        max: 45,
        title: { display: true, text: "Individual Component Variance (%)", color: t.inkSoft, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { display: false },
      },
    },
  },
});
