// anyplot.ai
// histogram-stepwise: Step Histogram
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Small LCG PRNG + Box-Muller transform — the browser has no seeded RNG.
let seed = 42;
function lcgRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function randomNormal(mean, stdDev) {
  const u1 = 1 - lcgRandom();
  const u2 = lcgRandom();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * stdDev;
}

const endpoints = [
  { name: "API v1 (legacy)", mean: 220, stdDev: 55, n: 700 },
  { name: "API v2 (rewrite)", mean: 140, stdDev: 30, n: 700 },
];
endpoints.forEach((endpoint) => {
  endpoint.latencies = Array.from({ length: endpoint.n }, () =>
    Math.max(5, randomNormal(endpoint.mean, endpoint.stdDev)),
  );
});

// --- Shared bins across both endpoints (aligned edges for direct overlay) ---
const allLatencies = endpoints.flatMap((endpoint) => endpoint.latencies);
const binWidth = 12;
const minEdge = Math.floor(Math.min(...allLatencies) / binWidth) * binWidth;
const maxEdge = Math.ceil(Math.max(...allLatencies) / binWidth) * binWidth;
const binCount = (maxEdge - minEdge) / binWidth;
const edges = Array.from({ length: binCount + 1 }, (_, i) => minEdge + i * binWidth);

// One point per bin's left edge (plus a trailing point at the final right
// edge, zero-padded at both ends) — Chart.js's native `stepped: "after"` line
// option draws the horizontal-then-vertical step outline between them, so no
// point-doubling is needed to fake the shape.
function stepOutline(latencies) {
  const counts = new Array(binCount).fill(0);
  latencies.forEach((value) => {
    const idx = Math.min(binCount - 1, Math.max(0, Math.floor((value - minEdge) / binWidth)));
    counts[idx] += 1;
  });

  const points = [{ x: edges[0], y: 0 }];
  for (let i = 0; i < binCount; i++) {
    points.push({ x: edges[i], y: counts[i] });
  }
  points.push({ x: edges[binCount], y: counts[binCount - 1] });
  points.push({ x: edges[binCount], y: 0 });
  return points;
}

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    datasets: endpoints.map((endpoint, i) => ({
      label: endpoint.name,
      data: stepOutline(endpoint.latencies),
      stepped: "after",
      borderColor: t.palette[i],
      backgroundColor: "transparent",
      // Rewrite's tighter, faster distribution is the story — give it the
      // heavier line weight so it reads as the visual focal point.
      borderWidth: i === 1 ? 4.5 : 2.75,
      pointRadius: 0,
      fill: false,
    })),
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: {
      padding: { right: 24, top: 8 },
    },
    plugins: {
      title: {
        display: true,
        text: "API Latency · histogram-stepwise · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 20, weight: "600" },
        padding: { bottom: 20 },
      },
      legend: {
        labels: {
          color: t.inkSoft,
          font: { size: 14 },
          boxWidth: 14,
          usePointStyle: true,
          pointStyle: "line",
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { display: false },
        title: {
          display: true,
          text: "Response Time (ms)",
          color: t.ink,
          font: { size: 16 },
        },
      },
      y: {
        beginAtZero: true,
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Number of Requests",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
});
