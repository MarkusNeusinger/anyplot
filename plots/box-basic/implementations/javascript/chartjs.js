// anyplot.ai
// box-basic: Basic Box Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-24

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Deterministic PRNG (LCG) + Box-Muller normal sampling ------------------
let seed = 42;
function lcg() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function randNormal(mean, sd) {
  const u1 = Math.max(lcg(), 1e-9);
  const u2 = lcg();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * sd;
}
function quantile(sorted, q) {
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  return sorted[base + 1] !== undefined
    ? sorted[base] + rest * (sorted[base + 1] - sorted[base])
    : sorted[base];
}

// --- Data: exam scores across 5 classes -------------------------------------
const classSpecs = [
  { label: "Class A", mean: 78, sd: 8, n: 60 },
  { label: "Class B", mean: 82, sd: 6, n: 75 },
  { label: "Class C", mean: 70, sd: 10, n: 50 },
  { label: "Class D", mean: 88, sd: 5, n: 90 },
  { label: "Class E", mean: 75, sd: 12, n: 65 },
];

const categories = classSpecs.map((spec) => {
  const scores = Array.from({ length: spec.n }, () =>
    Math.min(100, Math.max(0, randNormal(spec.mean, spec.sd)))
  ).sort((a, b) => a - b);

  const q1 = quantile(scores, 0.25);
  const median = quantile(scores, 0.5);
  const q3 = quantile(scores, 0.75);
  const iqr = q3 - q1;
  const lowerFence = q1 - 1.5 * iqr;
  const upperFence = q3 + 1.5 * iqr;

  const inRange = scores.filter((v) => v >= lowerFence && v <= upperFence);
  const outliers = scores.filter((v) => v < lowerFence || v > upperFence);

  return {
    label: spec.label,
    q1,
    median,
    q3,
    whiskerMin: inRange[0],
    whiskerMax: inRange[inRange.length - 1],
    outliers,
  };
});

const allRangeValues = categories.flatMap((c) => [
  c.whiskerMin,
  c.whiskerMax,
  ...c.outliers,
]);
const dataMin = Math.min(...allRangeValues);
const dataMax = Math.max(...allRangeValues);
const pad = (dataMax - dataMin) * 0.1;
const yMin = Math.floor((dataMin - pad) / 5) * 5;
const yMax = Math.ceil((dataMax + pad) / 5) * 5;

// --- Custom plugin: whiskers, caps, median line, outlier points ------------
const boxPlotExtras = {
  id: "boxPlotExtras",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    const meta = chart.getDatasetMeta(0);
    const yScale = chart.scales.y;
    ctx.save();

    categories.forEach((cat, i) => {
      const bar = meta.data[i];
      if (!bar) return;
      const centerX = bar.x;
      const capHalf = bar.width * 0.3;
      const yWhiskerMin = yScale.getPixelForValue(cat.whiskerMin);
      const yWhiskerMax = yScale.getPixelForValue(cat.whiskerMax);
      const yQ1 = yScale.getPixelForValue(cat.q1);
      const yQ3 = yScale.getPixelForValue(cat.q3);
      const yMedian = yScale.getPixelForValue(cat.median);

      // Whiskers
      ctx.strokeStyle = t.ink;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(centerX, yWhiskerMin);
      ctx.lineTo(centerX, yQ1);
      ctx.moveTo(centerX, yQ3);
      ctx.lineTo(centerX, yWhiskerMax);
      ctx.stroke();

      // Whisker caps
      ctx.beginPath();
      ctx.moveTo(centerX - capHalf, yWhiskerMin);
      ctx.lineTo(centerX + capHalf, yWhiskerMin);
      ctx.moveTo(centerX - capHalf, yWhiskerMax);
      ctx.lineTo(centerX + capHalf, yWhiskerMax);
      ctx.stroke();

      // Median line — page-bg stroke for contrast against the saturated fill
      ctx.strokeStyle = t.pageBg;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(centerX - bar.width / 2, yMedian);
      ctx.lineTo(centerX + bar.width / 2, yMedian);
      ctx.stroke();

      // Outliers
      const color = t.palette[i % t.palette.length];
      cat.outliers.forEach((value) => {
        const y = yScale.getPixelForValue(value);
        ctx.beginPath();
        ctx.arc(centerX, y, 6, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = t.pageBg;
        ctx.stroke();
      });
    });

    ctx.restore();
  },
};

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart: floating bars for Q1-Q3, custom plugin for the rest ------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: categories.map((c) => c.label),
    datasets: [
      {
        label: "Interquartile range",
        data: categories.map((c) => [c.q1, c.q3]),
        backgroundColor: categories.map((_, i) => t.palette[i % t.palette.length]),
        borderColor: t.ink,
        borderWidth: 2,
        barPercentage: 0.45,
        categoryPercentage: 0.75,
      },
    ],
  },
  plugins: [boxPlotExtras],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "box-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        title: { display: true, text: "Class", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
      },
      y: {
        min: yMin,
        max: yMax,
        title: { display: true, text: "Exam Score", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
    },
  },
});
