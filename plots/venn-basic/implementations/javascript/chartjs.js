// anyplot.ai
// venn-basic: Venn Diagram
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-09

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Reading-habit survey of 500 adults: which genres they read regularly.
const totalReaders = 500;
const fictionTotal = 280;
const nonfictionTotal = 210;
const bothGenres = 95;
const fictionOnly = fictionTotal - bothGenres;
const nonfictionOnly = nonfictionTotal - bothGenres;

const sets = [
  { name: "Fiction readers", total: fictionTotal, color: t.palette[0] },
  { name: "Nonfiction readers", total: nonfictionTotal, color: t.palette[1] },
];

function withAlpha(hex, alpha) {
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Venn diagram plugin -------------------------------------------------------
// Chart.js has no native Venn geometry. A "bubble" dataset sized to the real
// circle radius would work in principle, but Chart.js auto-reserves layout
// padding equal to the largest point radius on every side (so large bubbles
// never clip) — at this scale that padding eats almost the whole chart area.
// Instead the dataset stays a near-invisible placeholder (keeps `new Chart`
// idiomatic) and this plugin draws the two circles and their region labels
// directly onto the canvas, sized from `chart.chartArea` (native Chart.js
// plugin API — not an external library).
const vennDiagram = {
  id: "vennDiagram",
  afterDatasetsDraw(chart) {
    const { ctx, chartArea: area } = chart;
    const width = area.right - area.left;
    const height = area.bottom - area.top;
    const cy = area.top + height / 2;

    const rA = height * 0.4;
    const rB = rA * Math.sqrt(sets[1].total / sets[0].total);
    const centerDist = (rA + rB) * 0.42;
    const cxMid = area.left + width / 2;
    const centers = [
      { x: cxMid - centerDist / 2, y: cy, r: rA },
      { x: cxMid + centerDist / 2, y: cy, r: rB },
    ];

    ctx.save();

    // Circles — drawn with translucent fill so the overlap blends visibly.
    centers.forEach((c, i) => {
      ctx.beginPath();
      ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2);
      ctx.fillStyle = withAlpha(sets[i].color, 0.55);
      ctx.fill();
      ctx.lineWidth = 3;
      ctx.strokeStyle = sets[i].color;
      ctx.stroke();
    });

    // Set names, above each circle.
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    sets.forEach((s, i) => {
      ctx.fillStyle = t.ink;
      ctx.font = "bold 30px -apple-system, sans-serif";
      ctx.fillText(s.name, centers[i].x, centers[i].y - centers[i].r - 28);
    });

    // Region counts.
    const regions = [
      { count: fictionOnly, label: "Fiction only", x: centers[0].x - centers[0].r * 0.42, y: cy },
      { count: nonfictionOnly, label: "Nonfiction only", x: centers[1].x + centers[1].r * 0.42, y: cy },
      { count: bothGenres, label: "Both", x: (centers[0].x + centers[1].x) / 2, y: cy },
    ];
    regions.forEach((r) => {
      ctx.fillStyle = t.ink;
      ctx.font = "bold 38px -apple-system, sans-serif";
      ctx.fillText(String(r.count), r.x, r.y - 16);
      ctx.fillStyle = t.inkSoft;
      ctx.font = "18px -apple-system, sans-serif";
      ctx.fillText(r.label, r.x, r.y + 22);
    });

    ctx.restore();
  },
};

// --- Chart ---------------------------------------------------------------------
new Chart(canvas, {
  type: "bubble",
  data: {
    // Invisible placeholder points — the visible circles are hand-drawn by
    // vennDiagram above, sized to the actual chart area instead of Chart.js's
    // radius-based auto-padding.
    datasets: sets.map((s) => ({
      label: s.name,
      data: [{ x: 0, y: 0, r: 1 }],
      backgroundColor: "transparent",
      borderWidth: 0,
    })),
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 20, bottom: 40, left: 40, right: 40 } },
    plugins: {
      title: {
        display: true,
        text: "venn-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 4 },
      },
      subtitle: {
        display: true,
        text: `Reading habits of ${totalReaders} surveyed adults`,
        color: t.inkSoft,
        font: { size: 16 },
        padding: { bottom: 20 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: { display: false, min: -1, max: 1 },
      y: { display: false, min: -1, max: 1 },
    },
  },
  plugins: [vennDiagram],
});
