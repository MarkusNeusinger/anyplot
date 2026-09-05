// anyplot.ai
// network-bipartite: Bipartite Network Graph
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Author-paper affiliation network: which researchers contributed to which papers.
const authors = [
  "Chen", "Diaz", "Kumar", "Novak", "Osei", "Petrov",
  "Silva", "Tanaka", "Ahmed", "Brooks", "Costa", "Duran",
];
const papers = Array.from({ length: 16 }, (_, i) => `Paper ${i + 1}`);

// Fixed-seed LCG — the browser has no seeded RNG, so pseudo-randomness must be
// hand-rolled for reproducible output.
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

// Each paper draws 1-3 co-authors; weight is that author's credited
// contribution share (0.3-1.0), encoded later as edge width/opacity.
const edges = [];
papers.forEach((_, paperIdx) => {
  const numAuthors = 1 + Math.floor(rand() * 3);
  const chosen = new Set();
  while (chosen.size < numAuthors) {
    chosen.add(Math.floor(rand() * authors.length));
  }
  chosen.forEach((authorIdx) => {
    edges.push({ authorIdx, paperIdx, weight: 0.3 + rand() * 0.7 });
  });
});

const authorDegree = authors.map((_, i) => edges.filter((e) => e.authorIdx === i).length);
const paperDegree = papers.map((_, j) => edges.filter((e) => e.paperIdx === j).length);

const authorY = (i) => 1 - (i + 0.5) / authors.length;
const paperY = (j) => 1 - (j + 0.5) / papers.length;
const radiusFor = (degree) => 9 + Math.min(degree, 8) * 2.3;

function withAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Native Chart.js plugin: draws the bipartite edges behind the node
// datasets, then the source/target labels on top — no external package.
const bipartiteLayout = {
  id: "bipartiteLayout",
  beforeDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    ctx.save();
    edges.forEach(({ authorIdx, paperIdx, weight }) => {
      ctx.beginPath();
      ctx.moveTo(scales.x.getPixelForValue(0), scales.y.getPixelForValue(authorY(authorIdx)));
      ctx.lineTo(scales.x.getPixelForValue(1), scales.y.getPixelForValue(paperY(paperIdx)));
      ctx.lineWidth = 1 + weight * 2.5;
      ctx.strokeStyle = withAlpha(t.inkSoft, 0.15 + weight * 0.45);
      ctx.stroke();
    });
    ctx.restore();
  },
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    ctx.save();
    ctx.font = "14px sans-serif";
    ctx.fillStyle = t.inkSoft;
    ctx.textBaseline = "middle";
    ctx.textAlign = "right";
    authors.forEach((name, i) => {
      const gap = radiusFor(authorDegree[i]) + 8;
      ctx.fillText(name, scales.x.getPixelForValue(0) - gap, scales.y.getPixelForValue(authorY(i)));
    });
    ctx.textAlign = "left";
    papers.forEach((name, j) => {
      const gap = radiusFor(paperDegree[j]) + 8;
      ctx.fillText(name, scales.x.getPixelForValue(1) + gap, scales.y.getPixelForValue(paperY(j)));
    });
    ctx.restore();
  },
};

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "Authors",
        data: authors.map((name, i) => ({ x: 0, y: authorY(i), name, degree: authorDegree[i] })),
        backgroundColor: t.palette[0],
        borderColor: t.pageBg,
        borderWidth: 2,
        pointRadius: (ctx) => radiusFor(ctx.raw.degree),
        pointHoverRadius: (ctx) => radiusFor(ctx.raw.degree) + 3,
      },
      {
        label: "Papers",
        data: papers.map((name, j) => ({ x: 1, y: paperY(j), name, degree: paperDegree[j] })),
        backgroundColor: t.palette[1],
        borderColor: t.pageBg,
        borderWidth: 2,
        pointRadius: (ctx) => radiusFor(ctx.raw.degree),
        pointHoverRadius: (ctx) => radiusFor(ctx.raw.degree) + 3,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 10, bottom: 10, left: 10, right: 10 } },
    plugins: {
      title: {
        display: true,
        text: "network-bipartite · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        position: "top",
        labels: { color: t.ink, font: { size: 16 }, usePointStyle: true },
      },
      tooltip: {
        callbacks: {
          label: (ctx) => `${ctx.raw.name} (degree ${ctx.raw.degree})`,
        },
      },
    },
    scales: {
      x: { display: false, min: -0.45, max: 1.45 },
      y: { display: false, min: -0.05, max: 1.05 },
    },
  },
  plugins: [bipartiteLayout],
});
