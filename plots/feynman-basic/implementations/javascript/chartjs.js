// anyplot.ai
// feynman-basic: Feynman Diagram for Particle Interactions
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 85/100 | Created: 2026-06-03

const t = window.ANYPLOT_TOKENS;

// Imprint palette: fermion lines = green (pos 0), virtual photon = lavender (pos 1)
const FERMION_COLOR = t.palette[0];
const PHOTON_COLOR  = t.palette[1];

// e⁺e⁻ → γ* → μ⁺μ⁻  (QED tree-level annihilation)
const vertices = [
  { x: 3.5, y: 3.5 },  // V1: annihilation vertex
  { x: 6.5, y: 3.5 },  // V2: pair-creation vertex
];

// arrowDir: "forward" = particle flows from→to, "backward" = antiparticle (arrow reversed), "none" = boson
const lines = [
  { from: [1.0, 5.3], to: [3.5, 3.5], color: FERMION_COLOR, arrowDir: "forward",  label: "e⁻", labelAt: [0.55, 5.75] },
  { from: [1.0, 1.7], to: [3.5, 3.5], color: FERMION_COLOR, arrowDir: "backward", label: "e⁺", labelAt: [0.55, 1.25] },
  { from: [3.5, 3.5], to: [6.5, 3.5], color: PHOTON_COLOR,  arrowDir: "none",     label: "γ*", labelAt: [5.0,  4.25] },
  { from: [6.5, 3.5], to: [9.0, 5.3], color: FERMION_COLOR, arrowDir: "forward",  label: "μ⁻", labelAt: [9.45, 5.75] },
  { from: [6.5, 3.5], to: [9.0, 1.7], color: FERMION_COLOR, arrowDir: "backward", label: "μ⁺", labelAt: [9.45, 1.25] },
];

function toPx(chart, dx, dy) {
  return [chart.scales.x.getPixelForValue(dx), chart.scales.y.getPixelForValue(dy)];
}

function arrowHead(ctx, mx, my, ax, ay, bx, by, color, sz) {
  const angle = Math.atan2(by - ay, bx - ax);
  ctx.save();
  ctx.translate(mx, my);
  ctx.rotate(angle);
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(-sz, -sz * 0.38);
  ctx.lineTo(-sz,  sz * 0.38);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
  ctx.restore();
}

function fermionLine(ctx, x1, y1, x2, y2, color, lw, arrowDir) {
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.strokeStyle = color;
  ctx.lineWidth = lw;
  ctx.setLineDash([]);
  ctx.stroke();
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const sz = 13;
  if (arrowDir === "forward")  arrowHead(ctx, mx, my, x1, y1, x2, y2, color, sz);
  if (arrowDir === "backward") arrowHead(ctx, mx, my, x2, y2, x1, y1, color, sz);
  ctx.restore();
}

function photonLine(ctx, x1, y1, x2, y2, color, lw) {
  const dx = x2 - x1, dy = y2 - y1;
  const length = Math.sqrt(dx * dx + dy * dy);
  const angle  = Math.atan2(dy, dx);
  const amp = 10, wl = 24;
  const steps = Math.ceil(length * 1.2);
  ctx.save();
  ctx.translate(x1, y1);
  ctx.rotate(angle);
  ctx.beginPath();
  ctx.moveTo(0, 0);
  for (let i = 1; i <= steps; i++) {
    const xp = (i / steps) * length;
    ctx.lineTo(xp, amp * Math.sin(2 * Math.PI * xp / wl));
  }
  ctx.strokeStyle = color;
  ctx.lineWidth = lw;
  ctx.setLineDash([]);
  ctx.stroke();
  ctx.restore();
}

const feynmanPlugin = {
  id: "feynman",
  beforeDraw(chart) {
    const { ctx } = chart;
    ctx.fillStyle = t.pageBg;
    ctx.fillRect(0, 0, chart.width, chart.height);
  },
  afterDraw(chart) {
    const { ctx } = chart;
    ctx.save();

    const lw = 3.5;

    // Draw propagators
    lines.forEach(line => {
      const [x1, y1] = toPx(chart, line.from[0], line.from[1]);
      const [x2, y2] = toPx(chart, line.to[0], line.to[1]);
      if (line.arrowDir === "none") {
        photonLine(ctx, x1, y1, x2, y2, line.color, lw);
      } else {
        fermionLine(ctx, x1, y1, x2, y2, line.color, lw, line.arrowDir);
      }
    });

    // Draw vertex dots
    vertices.forEach(v => {
      const [px, py] = toPx(chart, v.x, v.y);
      ctx.beginPath();
      ctx.arc(px, py, 6, 0, 2 * Math.PI);
      ctx.fillStyle = t.ink;
      ctx.fill();
    });

    // Particle labels
    ctx.font = "bold 20px 'Helvetica Neue', Helvetica, Arial, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    lines.forEach(line => {
      const [lx, ly] = toPx(chart, line.labelAt[0], line.labelAt[1]);
      ctx.fillStyle = line.color;
      ctx.fillText(line.label, lx, ly);
    });

    // Time direction indicator (dashed arrow at bottom)
    const [tx1, ty] = toPx(chart, 2.0, 0.72);
    const [tx2   ] = toPx(chart, 8.0, 0.72);
    ctx.beginPath();
    ctx.moveTo(tx1, ty);
    ctx.lineTo(tx2 - 6, ty);
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1.5;
    ctx.setLineDash([5, 5]);
    ctx.stroke();
    ctx.setLineDash([]);
    arrowHead(ctx, tx2, ty, tx1, ty, tx2, ty, t.inkSoft, 8);
    ctx.font = "italic 15px 'Helvetica Neue', Helvetica, Arial, sans-serif";
    ctx.fillStyle = t.inkSoft;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillText("time", (tx1 + tx2) / 2, ty + 8);

    ctx.restore();
  },
};

// Mount
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

const titleText = "feynman-basic · javascript · chartjs · anyplot.ai";

new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [{
      data: [{ x: 0, y: 0 }, { x: 10, y: 7 }],
      pointRadius: 0,
      borderWidth: 0,
      backgroundColor: "transparent",
    }],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: titleText,
        color: t.ink,
        font: { size: 22, weight: "600" },
        padding: { top: 20, bottom: 14 },
      },
      legend: { display: false },
    },
    scales: {
      x: { min: 0, max: 10, display: false },
      y: { min: 0, max: 7,  display: false },
    },
    layout: {
      padding: { left: 60, right: 60, top: 10, bottom: 30 },
    },
  },
  plugins: [feynmanPlugin],
});
