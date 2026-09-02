// anyplot.ai
// network-weighted: Weighted Network Graph with Edge Thickness
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-02

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data: annual bilateral trade volume between major economies ($B) ------
const nodes = [
  { id: "USA", label: "United States" },
  { id: "CHN", label: "China" },
  { id: "DEU", label: "Germany" },
  { id: "JPN", label: "Japan" },
  { id: "GBR", label: "United Kingdom" },
  { id: "FRA", label: "France" },
  { id: "IND", label: "India" },
  { id: "BRA", label: "Brazil" },
  { id: "CAN", label: "Canada" },
  { id: "KOR", label: "South Korea" },
  { id: "MEX", label: "Mexico" },
  { id: "ITA", label: "Italy" },
  { id: "NLD", label: "Netherlands" },
  { id: "SGP", label: "Singapore" },
];

const rawEdges = [
  ["USA", "CAN", 780],
  ["USA", "MEX", 740],
  ["USA", "CHN", 690],
  ["USA", "JPN", 220],
  ["USA", "DEU", 210],
  ["USA", "KOR", 170],
  ["USA", "GBR", 150],
  ["CHN", "JPN", 340],
  ["CHN", "KOR", 300],
  ["CHN", "DEU", 260],
  ["CHN", "BRA", 150],
  ["CHN", "SGP", 130],
  ["CHN", "IND", 115],
  ["DEU", "NLD", 210],
  ["DEU", "FRA", 190],
  ["DEU", "ITA", 160],
  ["DEU", "GBR", 140],
  ["FRA", "GBR", 95],
  ["FRA", "ITA", 90],
  ["GBR", "NLD", 75],
  ["JPN", "KOR", 85],
  ["GBR", "IND", 40],
  ["NLD", "SGP", 45],
  ["MEX", "BRA", 12],
];

// --- Weighted-degree (node "importance") and index lookup ------------------
const idIndex = new Map(nodes.map((n, i) => [n.id, i]));
const links = rawEdges.map(([s, d, w]) => ({ s: idIndex.get(s), d: idIndex.get(d), w }));

const degree = new Array(nodes.length).fill(0);
links.forEach(({ s, d, w }) => {
  degree[s] += w;
  degree[d] += w;
});

// --- Force-directed layout (deterministic: circular seed, no RNG) ----------
// Fruchterman-Reingold style simulation. Edge weight biases the attractive
// force so heavily-traded pairs are pulled closer together, per spec notes.
const n = nodes.length;
const pos = nodes.map((_, i) => {
  const angle = (2 * Math.PI * i) / n;
  return { x: Math.cos(angle), y: Math.sin(angle) };
});

const k = Math.sqrt(6 / n);
const maxW = Math.max(...links.map((l) => l.w));
const minW = Math.min(...links.map((l) => l.w));
let temperature = 0.12;

for (let iter = 0; iter < 300; iter++) {
  const disp = pos.map(() => ({ x: 0, y: 0 }));

  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const dx = pos[i].x - pos[j].x;
      const dy = pos[i].y - pos[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1e-4;
      const force = (k * k) / dist;
      const ux = dx / dist;
      const uy = dy / dist;
      disp[i].x += ux * force;
      disp[i].y += uy * force;
      disp[j].x -= ux * force;
      disp[j].y -= uy * force;
    }
  }

  links.forEach(({ s, d, w }) => {
    const dx = pos[s].x - pos[d].x;
    const dy = pos[s].y - pos[d].y;
    const dist = Math.sqrt(dx * dx + dy * dy) || 1e-4;
    const strength = 0.5 + 0.9 * ((w - minW) / (maxW - minW || 1));
    const force = ((dist * dist) / k) * strength;
    const ux = dx / dist;
    const uy = dy / dist;
    disp[s].x -= ux * force;
    disp[s].y -= uy * force;
    disp[d].x += ux * force;
    disp[d].y += uy * force;
  });

  for (let i = 0; i < n; i++) {
    const len = Math.sqrt(disp[i].x ** 2 + disp[i].y ** 2) || 1e-4;
    pos[i].x += (disp[i].x / len) * Math.min(len, temperature);
    pos[i].y += (disp[i].y / len) * Math.min(len, temperature);
  }
  temperature *= 0.98;
}

// --- Fit layout to the canvas — each axis scaled to its own extent, since a
// network diagram encodes topology, not metric distance, so isotropy isn't
// required and independent-axis fitting uses the square canvas fully.
const xs = pos.map((p) => p.x);
const ys = pos.map((p) => p.y);
const cx = (Math.min(...xs) + Math.max(...xs)) / 2;
const cy = (Math.min(...ys) + Math.max(...ys)) / 2;
const halfX = (Math.max(...xs) - Math.min(...xs)) / 2 * 1.16 + 0.11;
const halfY = (Math.max(...ys) - Math.min(...ys)) / 2 * 1.16 + 0.11;

// --- Visual scales: node radius from weighted degree, edge width from weight
const minDeg = Math.min(...degree);
const maxDeg = Math.max(...degree);
const nodeRadius = degree.map((deg) => {
  const norm = (deg - minDeg) / (maxDeg - minDeg || 1);
  return 13 + Math.sqrt(norm) * 17; // 13 .. 30 CSS px
});

function edgeWidth(w) {
  const norm = (w - minW) / (maxW - minW || 1);
  return 2 + norm * 12; // 2 .. 14 CSS px — distinguishable, never extreme
}

// --- Custom plugin: draws edges beneath nodes, labels + legend above -------
const networkLayer = {
  id: "networkLayer",
  beforeDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    ctx.save();
    links.forEach(({ s, d, w }) => {
      const x1 = scales.x.getPixelForValue(pos[s].x);
      const y1 = scales.y.getPixelForValue(pos[s].y);
      const x2 = scales.x.getPixelForValue(pos[d].x);
      const y2 = scales.y.getPixelForValue(pos[d].y);
      const norm = (w - minW) / (maxW - minW || 1);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.lineWidth = edgeWidth(w);
      ctx.lineCap = "round";
      ctx.strokeStyle = t.ink;
      ctx.globalAlpha = 0.2 + norm * 0.55;
      ctx.stroke();
    });
    ctx.restore();
  },
  afterDatasetsDraw(chart) {
    const { ctx, scales, chartArea } = chart;
    ctx.save();

    // node id labels
    ctx.font = "600 15px sans-serif";
    ctx.fillStyle = t.inkSoft;
    ctx.textAlign = "center";
    nodes.forEach((node, i) => {
      const px = scales.x.getPixelForValue(pos[i].x);
      const py = scales.y.getPixelForValue(pos[i].y) + nodeRadius[i] + 20;
      ctx.fillText(node.id, px, py);
    });

    // edge-weight legend
    const legendW = 300;
    const legendH = 132;
    const lx = chartArea.left + 8;
    const ly = chartArea.top + 8;

    ctx.fillStyle = t.elevatedBg;
    ctx.fillRect(lx, ly, legendW, legendH);
    ctx.strokeStyle = t.grid;
    ctx.lineWidth = 1;
    ctx.strokeRect(lx, ly, legendW, legendH);

    ctx.textAlign = "left";
    ctx.fillStyle = t.ink;
    ctx.font = "600 15px sans-serif";
    ctx.fillText("Trade volume ($B)", lx + 16, ly + 28);

    const samples = [minW, (minW + maxW) / 2, maxW];
    samples.forEach((w, i) => {
      const rowY = ly + 56 + i * 26;
      const norm = (w - minW) / (maxW - minW || 1);

      ctx.globalAlpha = 0.2 + norm * 0.55;
      ctx.strokeStyle = t.ink;
      ctx.lineWidth = edgeWidth(w);
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(lx + 16, rowY);
      ctx.lineTo(lx + 58, rowY);
      ctx.stroke();
      ctx.globalAlpha = 1;

      ctx.fillStyle = t.inkSoft;
      ctx.font = "13px sans-serif";
      ctx.fillText(`$${Math.round(w)}B`, lx + 70, rowY + 4);
    });

    ctx.restore();
  },
};

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "Countries",
        data: pos,
        pointRadius: nodeRadius,
        pointHoverRadius: nodeRadius,
        backgroundColor: t.palette[0],
        borderColor: t.pageBg,
        borderWidth: 2,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: 8 },
    plugins: {
      title: {
        display: true,
        text: "network-weighted · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 4 },
      },
      subtitle: {
        display: true,
        text: "Edge thickness = trade volume · node size = total trade across all partners",
        color: t.inkSoft,
        font: { size: 14, weight: "normal" },
        padding: { bottom: 12 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: { type: "linear", min: cx - halfX, max: cx + halfX, display: false },
      y: { type: "linear", min: cy - halfY, max: cy + halfY, display: false },
    },
  },
  plugins: [networkLayer],
});
