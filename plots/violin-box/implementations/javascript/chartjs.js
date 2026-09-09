// anyplot.ai
// violin-box: Violin Plot with Embedded Box Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Deterministic PRNG (LCG) + samplers ------------------------------------
function makeLcg(seed) {
  let state = seed >>> 0;
  return function next() {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function randNormal(rng, mean, std) {
  const u1 = Math.max(rng(), 1e-9);
  const u2 = rng();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

function randExponential(rng, rate) {
  return -Math.log(1 - rng()) / rate;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

// --- Data: adult height (cm) across 4 sports, each a distinct shape --------
const rng = makeLcg(2026);
const sampleSize = 140;

function sampleGroup(generator) {
  return Array.from({ length: sampleSize }, generator).map((v) => clamp(v, 140, 220));
}

const sportGroups = [
  { name: "Gymnastics", values: sampleGroup(() => randNormal(rng, 159, 5)) },
  {
    name: "Swimming",
    values: sampleGroup(() => (rng() < 0.5 ? randNormal(rng, 173, 4) : randNormal(rng, 188, 4))),
  },
  { name: "Rowing", values: sampleGroup(() => 176 + randExponential(rng, 1 / 9)) },
  { name: "Basketball", values: sampleGroup(() => randNormal(rng, 198, 6)) },
];

// --- Stats helpers -----------------------------------------------------------
function std(values, m) {
  const variance = values.reduce((sum, v) => sum + (v - m) ** 2, 0) / (values.length - 1);
  return Math.sqrt(variance);
}

function mean(values) {
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

function silvermanBandwidth(values) {
  return 1.06 * std(values, mean(values)) * values.length ** (-1 / 5);
}

function gaussianKde(values, evalPoints, bandwidth) {
  const norm = 1 / (values.length * bandwidth * Math.sqrt(2 * Math.PI));
  return evalPoints.map((point) => {
    let sum = 0;
    for (const v of values) {
      const u = (point - v) / bandwidth;
      sum += Math.exp(-0.5 * u * u);
    }
    return sum * norm;
  });
}

function quantile(sortedValues, q) {
  const idx = q * (sortedValues.length - 1);
  const lower = Math.floor(idx);
  const upper = Math.ceil(idx);
  if (lower === upper) return sortedValues[lower];
  return sortedValues[lower] + (sortedValues[upper] - sortedValues[lower]) * (idx - lower);
}

// --- Build the KDE silhouette + embedded box/whisker stats per group -------
const gridSize = 120;
const maxHalfWidth = 0.4; // groups are spaced 1 unit apart on the x-axis
const boxHalfWidth = 0.12; // fixed, narrower than the violin envelope

const violins = sportGroups.map((group, i) => {
  const catX = i + 1;
  const sorted = [...group.values].sort((a, b) => a - b);
  const bandwidth = silvermanBandwidth(sorted);
  const pad = bandwidth * 1.5;
  const yMin = quantile(sorted, 0.01) - pad;
  const yMax = quantile(sorted, 0.99) + pad;
  const step = (yMax - yMin) / (gridSize - 1);
  const evalPoints = Array.from({ length: gridSize }, (_, j) => yMin + j * step);
  const density = gaussianKde(sorted, evalPoints, bandwidth);
  const scale = maxHalfWidth / Math.max(...density);

  const q1 = quantile(sorted, 0.25);
  const median = quantile(sorted, 0.5);
  const q3 = quantile(sorted, 0.75);
  const iqr = q3 - q1;
  const loBound = q1 - 1.5 * iqr;
  const hiBound = q3 + 1.5 * iqr;
  const inRange = sorted.filter((v) => v >= loBound && v <= hiBound);
  const whiskerLo = inRange.length ? inRange[0] : q1;
  const whiskerHi = inRange.length ? inRange[inRange.length - 1] : q3;
  const outliers = sorted.filter((v) => v < whiskerLo || v > whiskerHi);

  return {
    catX,
    left: evalPoints.map((y, j) => ({ x: catX - density[j] * scale, y })),
    right: evalPoints.map((y, j) => ({ x: catX + density[j] * scale, y })),
    stats: { q1, median, q3, whiskerLo, whiskerHi, outliers },
  };
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Datasets: mirrored fill areas (the violin silhouette) -----------------
const datasets = [];

violins.forEach((violin, i) => {
  const color = t.palette[i % t.palette.length];
  const leftIdx = datasets.length;
  datasets.push({
    data: violin.left,
    borderColor: color,
    borderWidth: 2,
    pointRadius: 0,
    fill: false,
    tension: 0,
  });
  datasets.push({
    data: violin.right,
    borderColor: color,
    backgroundColor: hexToRgba(color, 0.3),
    borderWidth: 2,
    pointRadius: 0,
    fill: leftIdx,
    tension: 0,
  });
});

// Round to clean tick bounds based on the raw (clamped) data range so a
// single skewed group's KDE padding can't dictate the shared axis extent.
const rawValues = sportGroups.flatMap((group) => group.values);
const rawMin = Math.min(...rawValues);
const rawMax = Math.max(...rawValues);
const axisPad = (rawMax - rawMin) * 0.08;
const yAxisMin = Math.floor((rawMin - axisPad) / 5) * 5;
const yAxisMax = Math.ceil((rawMax + axisPad) / 5) * 5;

// --- Embedded box plot: hand-drawn on top of the violin silhouettes --------
// Chart.js has no built-in violin or box-plot type; the box/whisker/outlier
// geometry inside each violin is drawn by hand with the canvas API in a
// plugin hook, using the same linear x/y scales the violin datasets sit on —
// no external chart type or plugin package.
const embeddedBoxPlugin = {
  id: "embeddedBox",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;

    violins.forEach((violin) => {
      const s = violin.stats;
      const cx = scales.x.getPixelForValue(violin.catX);
      const halfWidthPx =
        scales.x.getPixelForValue(violin.catX + boxHalfWidth) - scales.x.getPixelForValue(violin.catX);

      const yQ1 = scales.y.getPixelForValue(s.q1);
      const yQ3 = scales.y.getPixelForValue(s.q3);
      const yMed = scales.y.getPixelForValue(s.median);
      const yWhiskerLo = scales.y.getPixelForValue(s.whiskerLo);
      const yWhiskerHi = scales.y.getPixelForValue(s.whiskerHi);

      // Whiskers
      ctx.save();
      ctx.strokeStyle = t.ink;
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.moveTo(cx, yQ3);
      ctx.lineTo(cx, yWhiskerHi);
      ctx.moveTo(cx - halfWidthPx * 0.5, yWhiskerHi);
      ctx.lineTo(cx + halfWidthPx * 0.5, yWhiskerHi);
      ctx.moveTo(cx, yQ1);
      ctx.lineTo(cx, yWhiskerLo);
      ctx.moveTo(cx - halfWidthPx * 0.5, yWhiskerLo);
      ctx.lineTo(cx + halfWidthPx * 0.5, yWhiskerLo);
      ctx.stroke();

      // Quartile box — opaque elevated fill so it reads as a distinct layer
      // sitting inside the translucent violin, per the spec's "box plot
      // centered inside violin" requirement.
      ctx.fillStyle = t.elevatedBg;
      ctx.strokeStyle = t.ink;
      ctx.lineWidth = 2;
      ctx.fillRect(cx - halfWidthPx, yQ3, halfWidthPx * 2, yQ1 - yQ3);
      ctx.strokeRect(cx - halfWidthPx, yQ3, halfWidthPx * 2, yQ1 - yQ3);

      // Median line
      ctx.strokeStyle = t.ink;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(cx - halfWidthPx, yMed);
      ctx.lineTo(cx + halfWidthPx, yMed);
      ctx.stroke();
      ctx.restore();

      // Outliers
      ctx.save();
      ctx.fillStyle = t.inkSoft;
      ctx.strokeStyle = t.pageBg;
      ctx.lineWidth = 1.5;
      s.outliers.forEach((v) => {
        const cy = scales.y.getPixelForValue(v);
        ctx.beginPath();
        ctx.arc(cx, cy, 5, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
      });
      ctx.restore();
    });
  },
};

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: { datasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "violin-box · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      subtitle: {
        display: true,
        text: "Shaded silhouette = density (KDE) · Box = IQR, median & 1.5×IQR whiskers",
        color: t.inkSoft,
        font: { size: 14, style: "italic" },
        padding: { bottom: 12 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "linear",
        min: 0.5,
        max: sportGroups.length + 0.5,
        afterBuildTicks: (axis) => {
          axis.ticks = sportGroups.map((_, i) => ({ value: i + 1 }));
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => sportGroups[Math.round(value) - 1]?.name ?? "",
        },
        grid: { display: false },
        title: { display: true, text: "Sport", color: t.ink, font: { size: 16 } },
      },
      y: {
        min: yAxisMin,
        max: yAxisMax,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Height (cm)", color: t.ink, font: { size: 16 } },
      },
    },
  },
  plugins: [embeddedBoxPlugin],
});
