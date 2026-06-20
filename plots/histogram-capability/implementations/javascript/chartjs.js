// anyplot.ai
// histogram-capability: Process Capability Plot with Specification Limits
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-20

const t = window.ANYPLOT_TOKENS;

// ── Deterministic data generation (LCG + Box-Muller) ────────────────────────
let seed = 42;
function lcg() {
  seed = (seed * 1664525 + 1013904223) & 0xffffffff;
  return (seed >>> 0) / 0x100000000;
}
function randn() {
  return Math.sqrt(-2 * Math.log(lcg() || 1e-10)) * Math.cos(2 * Math.PI * lcg());
}

// Process parameters (shaft diameter, mm)
const LSL = 9.95, USL = 10.05, TARGET = 10.00;
const POP_MEAN = 10.005, POP_STD = 0.0125;
const N = 200;

const measurements = Array.from({ length: N }, () => POP_MEAN + POP_STD * randn());

// Sample statistics — computed from data
const sampleMean = measurements.reduce((s, v) => s + v, 0) / N;
const sampleStd = Math.sqrt(measurements.reduce((s, v) => s + (v - sampleMean) ** 2, 0) / (N - 1));

// Capability indices
const Cp  = (USL - LSL) / (6 * sampleStd);
const Cpk = Math.min((USL - sampleMean) / (3 * sampleStd), (sampleMean - LSL) / (3 * sampleStd));

// ── Histogram bins ───────────────────────────────────────────────────────────
const BIN_COUNT = 20;
const X_MIN = 9.93, X_MAX = 10.08;
const binWidth = (X_MAX - X_MIN) / BIN_COUNT;
const binCenters = Array.from({ length: BIN_COUNT }, (_, i) => X_MIN + (i + 0.5) * binWidth);
const freqs = new Array(BIN_COUNT).fill(0);
measurements.forEach(m => {
  const idx = Math.min(Math.floor((m - X_MIN) / binWidth), BIN_COUNT - 1);
  if (idx >= 0 && idx < BIN_COUNT) freqs[idx]++;
});

// ── Fitted normal distribution curve (scaled to histogram counts) ────────────
const CURVE_PTS = 150;
const normalData = Array.from({ length: CURVE_PTS }, (_, i) => {
  const x = X_MIN + (i / (CURVE_PTS - 1)) * (X_MAX - X_MIN);
  const z = (x - sampleMean) / sampleStd;
  const y = (1 / (sampleStd * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * z * z) * N * binWidth;
  return { x, y };
});

const maxFreq = Math.max(...freqs, ...normalData.map(d => d.y));
const yMax = Math.ceil(maxFreq * 1.2 / 5) * 5;

// ── Spec-lines + capability annotation plugin ────────────────────────────────
const specPlugin = {
  id: 'specLines',
  afterDatasetsDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const xScale = scales.x;

    ctx.save();

    // Vertical spec-limit and target lines
    const lines = [
      { value: LSL,    color: '#AE3030', dash: [10, 5], label: 'LSL',    labelSide: 'left'  },
      { value: USL,    color: '#AE3030', dash: [10, 5], label: 'USL',    labelSide: 'right' },
      { value: TARGET, color: t.inkSoft, dash: [6,  4], label: 'Target', labelSide: 'right' },
    ];

    lines.forEach(({ value, color, dash, label, labelSide }) => {
      const px = xScale.getPixelForValue(value);

      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.setLineDash(dash);
      ctx.beginPath();
      ctx.moveTo(px, chartArea.top);
      ctx.lineTo(px, chartArea.bottom);
      ctx.stroke();

      ctx.setLineDash([]);
      ctx.fillStyle = color;
      ctx.font = 'bold 15px system-ui, sans-serif';
      ctx.textAlign = labelSide === 'right' ? 'left' : 'right';
      ctx.fillText(label, px + (labelSide === 'right' ? 7 : -7), chartArea.top + 26);
    });

    // Cp / Cpk annotation box (upper-right corner)
    const bW = 200, bH = 96;
    const bX = chartArea.right - bW - 12;
    const bY = chartArea.top + 12;

    ctx.fillStyle = t.elevatedBg;
    ctx.strokeStyle = t.grid;
    ctx.lineWidth = 1;
    ctx.fillRect(bX, bY, bW, bH);
    ctx.strokeRect(bX, bY, bW, bH);

    ctx.fillStyle = t.ink;
    ctx.font = 'bold 18px system-ui, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`Cp  = ${Cp.toFixed(2)}`,  bX + 20, bY + 36);
    ctx.fillText(`Cpk = ${Cpk.toFixed(2)}`, bX + 20, bY + 70);

    ctx.restore();
  },
};

// ── Mount ────────────────────────────────────────────────────────────────────
const canvas = document.createElement('canvas');
document.getElementById('container').appendChild(canvas);

// ── Chart ────────────────────────────────────────────────────────────────────
new Chart(canvas, {
  type: 'bar',
  data: {
    datasets: [
      {
        type: 'bar',
        label: 'Frequency',
        data: binCenters.map((c, i) => ({ x: c, y: freqs[i] })),
        backgroundColor: t.palette[0] + 'bb',
        borderColor: t.palette[0],
        borderWidth: 1,
        barPercentage: 1,
        categoryPercentage: 1,
        order: 2,
      },
      {
        type: 'line',
        label: 'Normal fit',
        data: normalData,
        borderColor: t.palette[2],
        borderWidth: 3.5,
        pointRadius: 0,
        tension: 0.4,
        fill: false,
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
        text: 'histogram-capability · javascript · chartjs · anyplot.ai',
        color: t.ink,
        font: { size: 22, weight: '600' },
        padding: { top: 10, bottom: 20 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          boxWidth: 22,
          padding: 20,
        },
      },
    },
    scales: {
      x: {
        type: 'linear',
        min: X_MIN,
        max: X_MAX,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          maxTicksLimit: 11,
          callback: v => v.toFixed(3),
        },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
        title: {
          display: true,
          text: 'Shaft Diameter (mm)',
          color: t.ink,
          font: { size: 16 },
          padding: { top: 10 },
        },
      },
      y: {
        type: 'linear',
        beginAtZero: true,
        max: yMax,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          stepSize: 10,
        },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
        title: {
          display: true,
          text: 'Frequency',
          color: t.ink,
          font: { size: 16 },
          padding: { bottom: 10 },
        },
      },
    },
  },
  plugins: [specPlugin],
});
