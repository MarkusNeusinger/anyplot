// anyplot.ai
// confusion-matrix: Confusion Matrix Heatmap
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-04

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Wildlife camera-trap classifier: true vs. predicted species over 400 test images.
const classNames = ["Deer", "Fox", "Rabbit", "Owl"];
const matrix = [
  [96, 3, 1, 0], // true: Deer
  [4, 89, 5, 2], // true: Fox
  [2, 6, 88, 4], // true: Rabbit
  [0, 3, 7, 90], // true: Owl
];
const maxCount = Math.max(...matrix.flat());

const cells = [];
matrix.forEach((rowCounts, row) => {
  rowCounts.forEach((count, col) => {
    cells.push({ x: classNames[col], y: classNames[row], row, col, count });
  });
});

// --- Color scale: imprint_seq (brand green -> blue), low -> high count -----
function hexToRgb(hex) {
  const num = parseInt(hex.slice(1), 16);
  return { r: (num >> 16) & 255, g: (num >> 8) & 255, b: num & 255 };
}
const seqLow = hexToRgb(t.seq[0]);
const seqHigh = hexToRgb(t.seq[1]);
function cellFill(count) {
  const ratio = count / maxCount;
  const r = Math.round(seqLow.r + (seqHigh.r - seqLow.r) * ratio);
  const g = Math.round(seqLow.g + (seqHigh.g - seqLow.g) * ratio);
  const b = Math.round(seqLow.b + (seqHigh.b - seqLow.b) * ratio);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return { rgb: `rgb(${r}, ${g}, ${b})`, luminance };
}

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Custom plugin: draws the heatmap cells + a color-scale legend ----------
// Chart.js core has no matrix/heatmap chart type (that lives in the unpinned
// chartjs-chart-matrix plugin, out of scope here). A category-scale scatter
// with invisible points supplies the axes, tick labels, and tooltips; this
// inline plugin — plain Chart.js plugin-hook API, no external package — owns
// the cell fills, the diagonal highlight, and the count labels.
const heatmapPlugin = {
  id: "confusionCells",
  beforeDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    const cellW = scales.x.getPixelForTick(1) - scales.x.getPixelForTick(0);
    const cellH = scales.y.getPixelForTick(1) - scales.y.getPixelForTick(0);
    const gap = 3;

    cells.forEach(({ row, col, count }) => {
      const cx = scales.x.getPixelForTick(col);
      const cy = scales.y.getPixelForTick(row);
      const { rgb, luminance } = cellFill(count);

      ctx.fillStyle = rgb;
      ctx.fillRect(cx - cellW / 2 + gap, cy - cellH / 2 + gap, cellW - gap * 2, cellH - gap * 2);

      if (row === col) {
        ctx.strokeStyle = t.ink;
        ctx.lineWidth = 4;
        ctx.strokeRect(cx - cellW / 2 + gap, cy - cellH / 2 + gap, cellW - gap * 2, cellH - gap * 2);
      }

      ctx.fillStyle = luminance > 0.55 ? "#1A1A17" : "#F0EFE8";
      ctx.font = "600 32px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(count), cx, cy);
    });
  },
  afterDraw(chart) {
    const { ctx, chartArea } = chart;
    const barX = chartArea.right + 50;
    const barWidth = 26;
    const { top, bottom } = chartArea;

    const gradient = ctx.createLinearGradient(0, bottom, 0, top);
    gradient.addColorStop(0, t.seq[0]);
    gradient.addColorStop(1, t.seq[1]);
    ctx.fillStyle = gradient;
    ctx.fillRect(barX, top, barWidth, bottom - top);
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1;
    ctx.strokeRect(barX, top, barWidth, bottom - top);

    ctx.fillStyle = t.inkSoft;
    ctx.font = "14px sans-serif";
    ctx.textBaseline = "middle";
    ctx.textAlign = "left";
    ctx.fillText("0", barX + barWidth + 8, bottom);
    ctx.fillText(String(maxCount), barX + barWidth + 8, top);

    ctx.save();
    ctx.translate(barX + barWidth + 34, (top + bottom) / 2);
    ctx.rotate(Math.PI / 2);
    ctx.textAlign = "center";
    ctx.fillStyle = t.ink;
    ctx.fillText("Samples", 0, 0);
    ctx.restore();
  },
};

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "Samples",
        data: cells,
        pointRadius: 0,
        pointHitRadius: 140,
      },
    ],
  },
  plugins: [heatmapPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 10, right: 150, bottom: 10, left: 10 } },
    plugins: {
      title: {
        display: true,
        text: "confusion-matrix · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
      },
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) => {
            const { x, y, count } = context.raw;
            return `True: ${y}  Predicted: ${x}  Count: ${count}`;
          },
        },
      },
    },
    scales: {
      x: {
        type: "category",
        labels: classNames,
        offset: true,
        title: { display: true, text: "Predicted Label", color: t.ink, font: { size: 18 } },
        ticks: { color: t.inkSoft, font: { size: 16 } },
        grid: { display: false },
        border: { display: false },
      },
      y: {
        type: "category",
        labels: classNames,
        offset: true,
        title: { display: true, text: "True Label", color: t.ink, font: { size: 18 } },
        ticks: { color: t.inkSoft, font: { size: 16 } },
        grid: { display: false },
        border: { display: false },
      },
    },
  },
});
