// anyplot.ai
// network-force-directed: Force-Directed Graph
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-07-01
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data: CS Research Domain Network -------------------------------------
const communities = [
  { name: "Core CS",      color: t.palette[0] },
  { name: "AI / ML",      color: t.palette[1] },
  { name: "Systems",      color: t.palette[2] },
  { name: "Theory",       color: t.palette[3] },
  { name: "Applications", color: t.palette[4] },
];

const nodes = [
  // Core CS (0–7)
  { id: 0,  label: "Algorithms",      community: 0 },
  { id: 1,  label: "Data Structures", community: 0 },
  { id: 2,  label: "OS",              community: 0 },
  { id: 3,  label: "Networking",      community: 0 },
  { id: 4,  label: "Databases",       community: 0 },
  { id: 5,  label: "Security",        community: 0 },
  { id: 6,  label: "Compilers",       community: 0 },
  { id: 7,  label: "Prog. Languages", community: 0 },
  // AI / ML (8–13)
  { id: 8,  label: "Machine Learning",community: 1 },
  { id: 9,  label: "Deep Learning",   community: 1 },
  { id: 10, label: "NLP",             community: 1 },
  { id: 11, label: "Comp. Vision",    community: 1 },
  { id: 12, label: "Reinforcement L.",community: 1 },
  { id: 13, label: "Robotics",        community: 1 },
  // Systems (14–19)
  { id: 14, label: "Cloud Computing", community: 2 },
  { id: 15, label: "Distrib. Systems",community: 2 },
  { id: 16, label: "Microservices",   community: 2 },
  { id: 17, label: "Containers",      community: 2 },
  { id: 18, label: "CI/CD",           community: 2 },
  { id: 19, label: "Edge Computing",  community: 2 },
  // Theory (20–24)
  { id: 20, label: "Complexity",      community: 3 },
  { id: 21, label: "Graph Theory",    community: 3 },
  { id: 22, label: "Info. Theory",    community: 3 },
  { id: 23, label: "Logic",           community: 3 },
  { id: 24, label: "Formal Methods",  community: 3 },
  // Applications (25–29)
  { id: 25, label: "Healthcare IT",   community: 4 },
  { id: 26, label: "FinTech",         community: 4 },
  { id: 27, label: "Game Dev",        community: 4 },
  { id: 28, label: "Web Dev",         community: 4 },
  { id: 29, label: "Mobile Dev",      community: 4 },
];

const rawEdges = [
  // Core CS internal
  [0,1],[0,6],[1,6],[6,7],[7,0],[2,3],[2,5],[3,4],[4,5],[0,4],
  // AI/ML internal
  [8,9],[8,10],[8,11],[8,12],[9,10],[9,11],[9,12],[10,13],[11,13],[12,13],
  // Systems internal
  [14,15],[14,16],[14,17],[15,16],[16,17],[17,18],[14,18],[15,19],[18,19],
  // Theory internal
  [20,21],[20,22],[21,22],[21,23],[22,23],[23,24],[20,24],
  // Applications internal
  [25,26],[25,28],[26,28],[27,28],[28,29],[25,29],[27,29],
  // Cross-community bridges
  [0,8],[1,8],[0,20],[0,21],[7,10],[6,23],[6,24],
  [4,14],[4,15],[3,15],[2,14],[5,16],[19,13],
  [9,25],[11,25],[8,26],[9,27],[11,27],[14,28],[16,28],[19,29],[22,8],
];

// Deduplicate edges (canonical min-max key)
const edgeSet = new Set();
const edges = rawEdges.filter(([a, b]) => {
  const key = `${Math.min(a, b)}-${Math.max(a, b)}`;
  if (edgeSet.has(key)) return false;
  edgeSet.add(key);
  return true;
});

// --- Fruchterman-Reingold Force-Directed Layout ---------------------------
// Deterministic LCG for seeded random positions
const lcg = (seed) => {
  let s = seed >>> 0;
  return () => { s = (Math.imul(1664525, s) + 1013904223) >>> 0; return s / 4294967296; };
};
const rand = lcg(42);

const N = nodes.length;
const k = Math.sqrt(4.0 / N); // optimal vertex-vertex distance in 2x2 area

const pos = nodes.map(() => ({ x: (rand() - 0.5) * 2, y: (rand() - 0.5) * 2 }));
const disp = nodes.map(() => ({ x: 0, y: 0 }));
let temp = 1.0;

for (let iter = 0; iter < 350; iter++) {
  for (let v = 0; v < N; v++) { disp[v].x = 0; disp[v].y = 0; }

  // Repulsive forces between all pairs
  for (let v = 0; v < N; v++) {
    for (let u = 0; u < N; u++) {
      if (u === v) continue;
      const dx = pos[v].x - pos[u].x;
      const dy = pos[v].y - pos[u].y;
      const d = Math.sqrt(dx * dx + dy * dy) + 1e-4;
      const f = k * k / d;
      disp[v].x += (dx / d) * f;
      disp[v].y += (dy / d) * f;
    }
  }

  // Attractive forces along edges only
  for (const [u, v] of edges) {
    const dx = pos[v].x - pos[u].x;
    const dy = pos[v].y - pos[u].y;
    const d = Math.sqrt(dx * dx + dy * dy) + 1e-4;
    const f = d * d / k;
    disp[u].x += (dx / d) * f;
    disp[u].y += (dy / d) * f;
    disp[v].x -= (dx / d) * f;
    disp[v].y -= (dy / d) * f;
  }

  // Weak gravity toward center
  for (let v = 0; v < N; v++) {
    disp[v].x -= pos[v].x * 0.015;
    disp[v].y -= pos[v].y * 0.015;
  }

  // Apply displacement capped by temperature
  for (let v = 0; v < N; v++) {
    const dm = Math.sqrt(disp[v].x * disp[v].x + disp[v].y * disp[v].y) || 1e-10;
    const scale = Math.min(dm, temp) / dm;
    pos[v].x += disp[v].x * scale;
    pos[v].y += disp[v].y * scale;
  }

  temp = Math.max(temp * 0.975, 0.001);
}

// Normalize final positions to fit in [-1, 1]
const allX = pos.map(p => p.x), allY = pos.map(p => p.y);
const minX = Math.min(...allX), maxX = Math.max(...allX);
const minY = Math.min(...allY), maxY = Math.max(...allY);
const span = Math.max(maxX - minX, maxY - minY) / 1.8 || 1;
const cxc = (minX + maxX) / 2, cyc = (minY + maxY) / 2;
for (const p of pos) { p.x = (p.x - cxc) / span; p.y = (p.y - cyc) / span; }

// Node degree (for size scaling)
const degree = new Array(N).fill(0);
for (const [a, b] of edges) { degree[a]++; degree[b]++; }

// Top-8 nodes by degree receive visible labels
const topNodes = [...nodes].sort((a, b) => degree[b.id] - degree[a.id]).slice(0, 8);

// --- Mount ----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Plugin: draw edges before bubbles ------------------------------------
const edgePlugin = {
  id: "edgePlugin",
  beforeDatasetsDraw(chart) {
    const { ctx, scales: { x: xsc, y: ysc } } = chart;
    if (!xsc || !ysc) return;
    ctx.save();
    ctx.globalAlpha = 0.22;
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1.5;
    ctx.lineCap = "round";
    for (const [a, b] of edges) {
      ctx.beginPath();
      ctx.moveTo(xsc.getPixelForValue(pos[a].x), ysc.getPixelForValue(pos[a].y));
      ctx.lineTo(xsc.getPixelForValue(pos[b].x), ysc.getPixelForValue(pos[b].y));
      ctx.stroke();
    }
    ctx.restore();
  },
};

// --- Plugin: label high-degree nodes after bubbles ------------------------
const labelPlugin = {
  id: "labelPlugin",
  afterDatasetsDraw(chart) {
    const { ctx, scales: { x: xsc, y: ysc } } = chart;
    if (!xsc || !ysc) return;
    ctx.save();
    ctx.font = "600 12px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (const node of topNodes) {
      const nx = xsc.getPixelForValue(pos[node.id].x);
      const ny = ysc.getPixelForValue(pos[node.id].y);
      const r = 6 + degree[node.id] * 2;
      const txt = node.label;
      const tw = ctx.measureText(txt).width;
      // Semi-transparent pill background for legibility on any node color
      ctx.globalAlpha = 0.82;
      ctx.fillStyle = t.elevatedBg;
      ctx.fillRect(nx - tw / 2 - 4, ny + r + 3, tw + 8, 20);
      ctx.globalAlpha = 1.0;
      ctx.fillStyle = t.ink;
      ctx.fillText(txt, nx, ny + r + 5);
    }
    ctx.restore();
  },
};

// --- Chart ----------------------------------------------------------------
const TITLE = "network-force-directed · javascript · chartjs · anyplot.ai";
const titleSz = Math.round(22 * Math.min(1, 67 / TITLE.length));

const datasets = communities.map((comm, ci) => ({
  label: comm.name,
  data: nodes
    .filter(nd => nd.community === ci)
    .map(nd => ({ x: pos[nd.id].x, y: pos[nd.id].y, r: 6 + degree[nd.id] * 2 })),
  backgroundColor: comm.color + "bb",
  borderColor: comm.color,
  borderWidth: 1.5,
}));

new Chart(canvas, {
  type: "bubble",
  data: { datasets },
  plugins: [edgePlugin, labelPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 10, right: 20, bottom: 40, left: 10 } },
    plugins: {
      title: {
        display: true,
        text: TITLE,
        color: t.ink,
        font: { size: titleSz, weight: "500" },
        padding: { top: 14, bottom: 24 },
      },
      legend: {
        display: true,
        position: "right",
        labels: {
          color: t.ink,
          font: { size: 14 },
          padding: 16,
          usePointStyle: true,
          pointStyleWidth: 14,
        },
      },
      tooltip: {
        callbacks: {
          label(ctx) {
            const commNodes = nodes.filter(nd => nd.community === ctx.datasetIndex);
            const nd = commNodes[ctx.dataIndex];
            return `${nd.label}  (degree ${degree[nd.id]})`;
          },
        },
      },
    },
    scales: {
      x: { display: false, min: -1.35, max: 1.35 },
      y: { display: false, min: -1.35, max: 1.35 },
    },
  },
});
