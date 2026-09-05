// anyplot.ai
// histogram-2d: 2D Histogram Heatmap
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data: correlated daily returns for two assets, deterministic LCG -------
function makeLcg(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

function randNormal() {
  const u1 = Math.max(rand(), 1e-12);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const N_POINTS = 6000;
const CORRELATION = 0.65;
const assetAReturns = [];
const assetBReturns = [];
for (let i = 0; i < N_POINTS; i++) {
  const z1 = randNormal();
  const z2 = randNormal();
  assetAReturns.push(z1 * 1.4);
  assetBReturns.push(CORRELATION * z1 * 1.1 + Math.sqrt(1 - CORRELATION * CORRELATION) * z2 * 1.1);
}

// --- Bin the joint distribution into a fixed grid ---------------------------
const N_BINS = 26;
const xMin = Math.min(...assetAReturns);
const xMax = Math.max(...assetAReturns);
const yMin = Math.min(...assetBReturns);
const yMax = Math.max(...assetBReturns);
const binWidthX = (xMax - xMin) / N_BINS;
const binWidthY = (yMax - yMin) / N_BINS;

const counts = new Array(N_BINS * N_BINS).fill(0);
for (let i = 0; i < N_POINTS; i++) {
  let bx = Math.floor((assetAReturns[i] - xMin) / binWidthX);
  let by = Math.floor((assetBReturns[i] - yMin) / binWidthY);
  if (bx === N_BINS) bx -= 1;
  if (by === N_BINS) by -= 1;
  counts[by * N_BINS + bx] += 1;
}
const maxCount = Math.max(...counts);
const logMaxCount = Math.log1p(maxCount);

const bins = [];
for (let by = 0; by < N_BINS; by++) {
  for (let bx = 0; bx < N_BINS; bx++) {
    const count = counts[by * N_BINS + bx];
    if (count === 0) continue;
    const left = xMin + bx * binWidthX;
    const bottom = yMin + by * binWidthY;
    bins.push({ left, right: left + binWidthX, bottom, top: bottom + binWidthY, count });
  }
}

// --- Density color: imprint_seq, log-scaled (density varies widely) --------
function hexToRgb(hex) {
  const value = parseInt(hex.slice(1), 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}
const seqLow = hexToRgb(t.seq[0]);
const seqHigh = hexToRgb(t.seq[1]);
function densityColor(count) {
  const ratio = Math.log1p(count) / logMaxCount;
  const r = Math.round(seqLow[0] + (seqHigh[0] - seqLow[0]) * ratio);
  const g = Math.round(seqLow[1] + (seqHigh[1] - seqLow[1]) * ratio);
  const b = Math.round(seqLow[2] + (seqHigh[2] - seqLow[2]) * ratio);
  return `rgb(${r}, ${g}, ${b})`;
}

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Custom plugin: paints binned density rects + a colorbar legend ---------
// Chart.js has no core heatmap chart type; the plugin hooks below use the
// scatter chart's own linear scales to convert bin edges to pixel rects,
// entirely through Chart.js's public plugin API (no chartjs-chart-matrix).
const COLORBAR_WIDTH = 28;
const COLORBAR_OFFSET = 30;
const COLORBAR_RESERVED = 140;

const heatmapPlugin = {
  id: "histogram2dHeatmap",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    const { x: xScale, y: yScale } = scales;
    ctx.save();
    for (const bin of bins) {
      const xPixelLeft = xScale.getPixelForValue(bin.left);
      const xPixelRight = xScale.getPixelForValue(bin.right);
      const yPixelTop = yScale.getPixelForValue(bin.top);
      const yPixelBottom = yScale.getPixelForValue(bin.bottom);
      ctx.fillStyle = densityColor(bin.count);
      ctx.fillRect(
        Math.min(xPixelLeft, xPixelRight),
        Math.min(yPixelTop, yPixelBottom),
        Math.abs(xPixelRight - xPixelLeft),
        Math.abs(yPixelBottom - yPixelTop)
      );
    }
    ctx.restore();
  },
  afterDraw(chart) {
    const { ctx, chartArea } = chart;
    const barX = chartArea.right + COLORBAR_OFFSET;
    const barTop = chartArea.top;
    const barHeight = chartArea.bottom - chartArea.top;

    const gradient = ctx.createLinearGradient(0, barTop + barHeight, 0, barTop);
    gradient.addColorStop(0, t.seq[0]);
    gradient.addColorStop(1, t.seq[1]);

    ctx.save();
    ctx.fillStyle = gradient;
    ctx.fillRect(barX, barTop, COLORBAR_WIDTH, barHeight);
    ctx.strokeStyle = t.grid;
    ctx.lineWidth = 1;
    ctx.strokeRect(barX, barTop, COLORBAR_WIDTH, barHeight);

    ctx.fillStyle = t.inkSoft;
    ctx.font = "13px sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText("0", barX + COLORBAR_WIDTH + 8, barTop + barHeight);
    ctx.fillText(String(maxCount), barX + COLORBAR_WIDTH + 8, barTop);

    ctx.translate(barX + COLORBAR_WIDTH + 34, barTop + barHeight / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = "center";
    ctx.fillStyle = t.ink;
    ctx.font = "14px sans-serif";
    ctx.fillText("Point count", 0, 0);
    ctx.restore();
  },
};

// --- Chart ---------------------------------------------------------------
// A near-invisible dataset drives the scatter chart's linear scale ranges;
// the plugin above does the actual density painting.
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "Joint density",
        data: [
          { x: xMin, y: yMin },
          { x: xMax, y: yMax },
        ],
        pointRadius: 0,
        showLine: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { right: COLORBAR_RESERVED } },
    plugins: {
      title: {
        display: true,
        text: "histogram-2d · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "linear",
        min: xMin,
        max: xMax,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: { display: true, text: "Asset A Daily Return (%)", color: t.ink, font: { size: 16 } },
      },
      y: {
        type: "linear",
        min: yMin,
        max: yMax,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: { display: true, text: "Asset B Daily Return (%)", color: t.ink, font: { size: 16 } },
      },
    },
  },
  plugins: [heatmapPlugin],
});
