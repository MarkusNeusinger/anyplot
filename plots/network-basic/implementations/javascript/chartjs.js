// anyplot.ai
// network-basic: Basic Network Graph
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 87/100 | Created: 2026-07-24
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data: a small company collaboration network, grouped by department ---
const GROUP_NAMES = ["Engineering", "Design", "Product", "Marketing"];

const nodes = [
  { id: 0, name: "Ava", group: 0 },
  { id: 1, name: "Noah", group: 0 },
  { id: 2, name: "Mia", group: 0 },
  { id: 3, name: "Ethan", group: 0 },
  { id: 4, name: "Zoe", group: 0 },
  { id: 5, name: "Liam", group: 1 },
  { id: 6, name: "Grace", group: 1 },
  { id: 7, name: "Kai", group: 1 },
  { id: 8, name: "Nora", group: 1 },
  { id: 9, name: "Owen", group: 1 },
  { id: 10, name: "Maya", group: 2 },
  { id: 11, name: "Leo", group: 2 },
  { id: 12, name: "Ivy", group: 2 },
  { id: 13, name: "Finn", group: 2 },
  { id: 14, name: "Ruby", group: 2 },
  { id: 15, name: "Jack", group: 3 },
  { id: 16, name: "Elena", group: 3 },
  { id: 17, name: "Theo", group: 3 },
  { id: 18, name: "Luna", group: 3 },
  { id: 19, name: "Max", group: 3 },
];

const edges = [
  [0, 1], [0, 2], [1, 2], [1, 3], [2, 3], [3, 4], [2, 4], [0, 4],
  [5, 6], [5, 7], [6, 7], [6, 8], [7, 8], [8, 9], [7, 9],
  [10, 11], [10, 12], [11, 12], [11, 13], [12, 13], [13, 14], [12, 14],
  [15, 16], [15, 17], [16, 17], [16, 18], [17, 18], [18, 19], [17, 19],
  [0, 5], [2, 10], [6, 11], [8, 15], [12, 16], [4, 17],
];

// Degree (connection count) per node — drives marker size
const degree = new Array(nodes.length).fill(0);
edges.forEach(([a, b]) => {
  degree[a] += 1;
  degree[b] += 1;
});

// --- Force-directed layout (Fruchterman-Reingold), deterministic via a fixed-seed LCG ---
function lcg(seed) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };
}
const rand = lcg(42);

const nodeCount = nodes.length;
const area = 4; // layout unfolds inside a [-1, 1] x [-1, 1] square
const k = Math.sqrt(area / nodeCount);
const pos = nodes.map(() => ({ x: rand() * 2 - 1, y: rand() * 2 - 1 }));

let temperature = 0.15;
const iterations = 400;
for (let iter = 0; iter < iterations; iter++) {
  const disp = pos.map(() => ({ x: 0, y: 0 }));

  // Repulsion between every pair of nodes keeps clusters from collapsing
  for (let i = 0; i < nodeCount; i++) {
    for (let j = i + 1; j < nodeCount; j++) {
      let dx = pos[i].x - pos[j].x;
      let dy = pos[i].y - pos[j].y;
      const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 0.01);
      const force = (k * k) / dist;
      dx = (dx / dist) * force;
      dy = (dy / dist) * force;
      disp[i].x += dx;
      disp[i].y += dy;
      disp[j].x -= dx;
      disp[j].y -= dy;
    }
  }

  // Attraction along edges pulls connected nodes together
  edges.forEach(([a, b]) => {
    let dx = pos[a].x - pos[b].x;
    let dy = pos[a].y - pos[b].y;
    const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 0.01);
    const force = (dist * dist) / k;
    dx = (dx / dist) * force;
    dy = (dy / dist) * force;
    disp[a].x -= dx;
    disp[a].y -= dy;
    disp[b].x += dx;
    disp[b].y += dy;
  });

  // Apply displacement, capped by the cooling temperature
  for (let i = 0; i < nodeCount; i++) {
    const d = Math.max(Math.sqrt(disp[i].x ** 2 + disp[i].y ** 2), 0.0001);
    pos[i].x += (disp[i].x / d) * Math.min(d, temperature);
    pos[i].y += (disp[i].y / d) * Math.min(d, temperature);
  }
  temperature *= 0.99;
}

// Symmetric bound (with padding) so the square canvas isn't stretched
const bound =
  Math.max(...pos.map((p) => Math.max(Math.abs(p.x), Math.abs(p.y)))) * 1.08;
nodes.forEach((node, i) => {
  node.x = pos[i].x;
  node.y = pos[i].y;
});

// --- Mount ---
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Edges: drawn under the node markers via a lightweight inline plugin ---
const edgePlugin = {
  id: "networkEdges",
  beforeDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    ctx.save();
    ctx.strokeStyle = t.inkSoft;
    ctx.globalAlpha = 0.35;
    ctx.lineWidth = 2;
    edges.forEach(([a, b]) => {
      ctx.beginPath();
      ctx.moveTo(scales.x.getPixelForValue(nodes[a].x), scales.y.getPixelForValue(nodes[a].y));
      ctx.lineTo(scales.x.getPixelForValue(nodes[b].x), scales.y.getPixelForValue(nodes[b].y));
      ctx.stroke();
    });
    ctx.restore();
  },
};

// --- Nodes: one dataset per department so the legend reads as group color ---
const groupNodes = GROUP_NAMES.map((_, g) => nodes.filter((node) => node.group === g));
const datasets = groupNodes.map((group, g) => ({
  label: GROUP_NAMES[g],
  data: group.map((node) => ({ x: node.x, y: node.y })),
  backgroundColor: t.palette[g],
  borderColor: t.pageBg,
  borderWidth: 2,
  pointRadius: group.map((node) => 9 + degree[node.id] * 2),
  pointHoverRadius: group.map((node) => 13 + degree[node.id] * 2),
  showLine: false,
}));

// --- Chart ---
new Chart(canvas, {
  type: "scatter",
  data: { datasets },
  plugins: [edgePlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: {
      padding: { top: 10, right: 30, bottom: 20, left: 30 },
    },
    plugins: {
      title: {
        display: true,
        text: "network-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 24, weight: "normal" },
        padding: { top: 12, bottom: 16 },
      },
      legend: {
        display: true,
        position: "bottom",
        labels: { color: t.ink, font: { size: 16 }, usePointStyle: true, boxWidth: 10 },
      },
      tooltip: {
        callbacks: {
          title: (items) => (items.length ? GROUP_NAMES[items[0].datasetIndex] : ""),
          label: (item) => {
            const node = groupNodes[item.datasetIndex][item.dataIndex];
            return `${node.name} — ${degree[node.id]} connections`;
          },
        },
      },
    },
    scales: {
      x: { display: false, min: -bound, max: bound },
      y: { display: false, min: -bound, max: bound },
    },
  },
});
