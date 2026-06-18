// anyplot.ai
// root-locus-basic: Root Locus Plot for Control Systems
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-18

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// Horner evaluation of monic cubic s³ + p·s² + q·s + r at complex z = (zr + j·zi)
function evalCubic(p, q, r, zr, zi) {
  let re = 1, im = 0;
  for (const c of [p, q, r]) {
    const nr = re * zr - im * zi + c;
    const ni = re * zi + im * zr;
    re = nr; im = ni;
  }
  return { re, im };
}

// Durand–Kerner method: three roots of s³ + p·s² + q·s + r = 0
function cubicRoots(p, q, r) {
  let z = [{ re: 0.5, im: 0.6 }, { re: -0.7, im: 0.3 }, { re: 0.2, im: -0.8 }];
  for (let it = 0; it < 150; it++) {
    for (let i = 0; i < 3; i++) {
      const f = evalCubic(p, q, r, z[i].re, z[i].im);
      let dr = 1, di = 0;
      for (let j = 0; j < 3; j++) {
        if (j === i) continue;
        const nr = dr * (z[i].re - z[j].re) - di * (z[i].im - z[j].im);
        const ni = dr * (z[i].im - z[j].im) + di * (z[i].re - z[j].re);
        dr = nr; di = ni;
      }
      const d2 = dr * dr + di * di;
      if (d2 < 1e-28) continue;
      z[i].re -= (f.re * dr + f.im * di) / d2;
      z[i].im -= (f.im * dr - f.re * di) / d2;
    }
  }
  // Consistent branch ordering: descending real, break ties by descending imaginary
  return z.sort((a, b) =>
    Math.abs(a.re - b.re) > 0.01 ? b.re - a.re : b.im - a.im
  );
}

// System: G(s) = K / [s(s+2)(s+4)]
// Characteristic polynomial: s³ + 6s² + 8s + K = 0
// Open-loop poles:   s = 0, −2, −4      (K = 0)
// Breakaway point:   s ≈ −0.845          (K ≈ 3.08)
// Im-axis crossings: s = ±j√8 ≈ ±j2.83  (K = 48, stability boundary)
// Centroid of asymptotes: (0 − 2 − 4) / 3 = −2

const N = 600;
const K_MAX = 70;
const branches = [[], [], []];

for (let i = 0; i <= N; i++) {
  const K = (i / N) * K_MAX;
  const roots = cubicRoots(6, 8, K);
  for (let b = 0; b < 3; b++) {
    branches[b].push({ x: roots[b].re, y: roots[b].im });
  }
}

// Landmarks
const openLoopPoles = [{ x: 0, y: 0 }, { x: -2, y: 0 }, { x: -4, y: 0 }];
const stabMarkers = [{ x: 0, y: Math.sqrt(8) }, { x: 0, y: -Math.sqrt(8) }];

// Mount canvas
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

const title = "root-locus-basic · javascript · chartjs · anyplot.ai";
const titleSize = title.length > 67 ? Math.round(22 * 67 / title.length) : 22;

new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "Branch 1 (pole at 0)",
        data: branches[0],
        borderColor: t.palette[0],
        backgroundColor: "transparent",
        showLine: true,
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0,
      },
      {
        label: "Branch 2 (pole at −2)",
        data: branches[1],
        borderColor: t.palette[1],
        backgroundColor: "transparent",
        showLine: true,
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0,
      },
      {
        label: "Branch 3 (pole at −4)",
        data: branches[2],
        borderColor: t.palette[2],
        backgroundColor: "transparent",
        showLine: true,
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0,
      },
      {
        label: "Open-loop poles",
        data: openLoopPoles,
        borderColor: t.ink,
        backgroundColor: "transparent",
        pointStyle: "crossRot",
        pointRadius: 12,
        pointBorderWidth: 3,
        showLine: false,
      },
      {
        label: "Stability boundary (K = 48)",
        data: stabMarkers,
        borderColor: t.amber,
        backgroundColor: t.amber,
        pointStyle: "triangle",
        pointRadius: 10,
        pointBorderWidth: 2,
        showLine: false,
      },
    ],
  },
  plugins: [
    {
      id: "bg",
      beforeDraw: (chart) => {
        const ctx = chart.ctx;
        ctx.save();
        ctx.fillStyle = t.pageBg;
        ctx.fillRect(0, 0, chart.width, chart.height);
        ctx.restore();
      },
    },
  ],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 4, right: 20, bottom: 10, left: 10 } },
    plugins: {
      title: {
        display: true,
        text: title,
        color: t.ink,
        font: { size: titleSize, weight: "500" },
        padding: { top: 8, bottom: 16 },
      },
      legend: {
        labels: {
          color: t.inkSoft,
          font: { size: 14 },
          usePointStyle: true,
          padding: 18,
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: -8,
        max: 2,
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Real Axis",
          color: t.ink,
          font: { size: 15, weight: "500" },
        },
        border: { color: t.inkSoft },
      },
      y: {
        type: "linear",
        min: -5,
        max: 5,
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Imaginary Axis",
          color: t.ink,
          font: { size: 15, weight: "500" },
        },
        border: { color: t.inkSoft },
      },
    },
  },
});
