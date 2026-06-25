// anyplot.ai
// contour-basic: Basic Contour Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.0
// Quality: 82/100 | Created: 2026-06-25

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data ---
// Peaks function: z = f(x,y) on [-3, 3]² — a classic surface with two peaks and a valley
const N = 70;
const RANGE = 3;

const allPoints = [];
for (let i = 0; i < N; i++) {
  for (let j = 0; j < N; j++) {
    const x = -RANGE + (2 * RANGE * i) / (N - 1);
    const y = -RANGE + (2 * RANGE * j) / (N - 1);
    const z =
      3 * (1 - x) ** 2 * Math.exp(-(x ** 2) - (y + 1) ** 2) -
      10 * (x / 5 - x ** 3 - y ** 5) * Math.exp(-(x ** 2) - y ** 2) -
      (1 / 3) * Math.exp(-((x + 1) ** 2) - y ** 2);
    allPoints.push({ x, y, z });
  }
}

// Compute z range from data
let Z_MIN = Infinity,
  Z_MAX = -Infinity;
for (const p of allPoints) {
  if (p.z < Z_MIN) Z_MIN = p.z;
  if (p.z > Z_MAX) Z_MAX = p.z;
}

// Fraction along colormap where z=0 sits (boundary between valleys and peaks)
const Z_ZERO_FRAC = (0 - Z_MIN) / (Z_MAX - Z_MIN);

// --- Imprint diverging colormap ---
// t.div = ["#AE3030" (matte red), neutral midpoint (theme-adaptive), "#4467A3" (blue)]
function hexToRgb(hex) {
  return [
    parseInt(hex.slice(1, 3), 16),
    parseInt(hex.slice(3, 5), 16),
    parseInt(hex.slice(5, 7), 16),
  ];
}

function lerpColor(h1, h2, frac) {
  const [r1, g1, b1] = hexToRgb(h1);
  const [r2, g2, b2] = hexToRgb(h2);
  return `rgb(${Math.round(r1 + (r2 - r1) * frac)},${Math.round(g1 + (g2 - g1) * frac)},${Math.round(b1 + (b2 - b1) * frac)})`;
}

function divColor(z) {
  const frac = Math.max(0, Math.min(1, (z - Z_MIN) / (Z_MAX - Z_MIN)));
  if (frac <= Z_ZERO_FRAC) {
    return lerpColor(t.div[0], t.div[1], frac / Z_ZERO_FRAC);
  }
  return lerpColor(t.div[1], t.div[2], (frac - Z_ZERO_FRAC) / (1 - Z_ZERO_FRAC));
}

// --- Contour band datasets ---
// Points are sorted into NUM_LEVELS z-bands; each band is a scatter dataset
const NUM_LEVELS = 16;
const step = (Z_MAX - Z_MIN) / NUM_LEVELS;
const datasets = [];

for (let lvl = 0; lvl < NUM_LEVELS; lvl++) {
  const zLow = Z_MIN + lvl * step;
  const zHigh = zLow + step;
  const zMid = (zLow + zHigh) / 2;
  const color = divColor(zMid);
  const isLastBand = lvl === NUM_LEVELS - 1;
  const points = allPoints
    .filter((p) => p.z >= zLow && (isLastBand ? p.z <= zHigh : p.z < zHigh))
    .map((p) => ({ x: p.x, y: p.y }));
  if (points.length > 0) {
    datasets.push({
      data: points,
      backgroundColor: color,
      borderColor: color,
      borderWidth: 0,
      pointRadius: 10,
      pointHoverRadius: 10,
      showLine: false,
    });
  }
}

// --- Colorbar plugin ---
// Draws a gradient color scale bar to the right of the chart area
const colorbarPlugin = {
  id: "colorbar",
  afterDraw(chart) {
    const ctx = chart.ctx;
    const ca = chart.chartArea;
    if (!ca) return;

    const barX = ca.right + 22;
    const barW = 22;
    const barH = ca.bottom - ca.top;

    // Gradient: bottom=Z_MIN (red) → Z_ZERO (neutral) → top=Z_MAX (blue)
    const grad = ctx.createLinearGradient(0, ca.bottom, 0, ca.top);
    grad.addColorStop(0, t.div[0]);
    grad.addColorStop(Z_ZERO_FRAC, t.div[1]);
    grad.addColorStop(1, t.div[2]);
    ctx.fillStyle = grad;
    ctx.fillRect(barX, ca.top, barW, barH);

    // Border
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1;
    ctx.strokeRect(barX, ca.top, barW, barH);

    // Zero-line inside the colorbar marks the valley/peak boundary
    const zeroBarY = ca.bottom - Z_ZERO_FRAC * barH;
    ctx.strokeStyle = t.ink;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(barX, zeroBarY);
    ctx.lineTo(barX + barW, zeroBarY);
    ctx.stroke();

    // "z" label above bar
    ctx.fillStyle = t.ink;
    ctx.font = "bold 15px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("z", barX + barW / 2, ca.top - 6);

    // Tick marks and labels at max, 0, min
    const ticks = [
      { frac: 1, label: `+${Z_MAX.toFixed(1)}` },
      { frac: Z_ZERO_FRAC, label: "0" },
      { frac: 0, label: Z_MIN.toFixed(1) },
    ];
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1;
    ctx.fillStyle = t.inkSoft;
    ctx.font = "13px sans-serif";
    ctx.textAlign = "left";
    for (const tk of ticks) {
      const ty = ca.bottom - tk.frac * barH;
      ctx.beginPath();
      ctx.moveTo(barX + barW, ty);
      ctx.lineTo(barX + barW + 5, ty);
      ctx.stroke();
      ctx.fillText(tk.label, barX + barW + 8, ty + 5);
    }
  },
};

// --- Mount ---
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---
new Chart(canvas, {
  type: "scatter",
  data: { datasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { right: 100, bottom: 10 } },
    plugins: {
      title: {
        display: true,
        text: "contour-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { top: 12, bottom: 12 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        type: "linear",
        min: -RANGE,
        max: RANGE,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "X",
          color: t.ink,
          font: { size: 16 },
        },
      },
      y: {
        type: "linear",
        min: -RANGE,
        max: RANGE,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Y",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
  plugins: [colorbarPlugin],
});
