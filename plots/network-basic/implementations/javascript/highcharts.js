// anyplot.ai
// network-basic: Basic Network Graph
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-07-24
//# anyplot-orientation: square

// Only the core Highcharts bundle is loaded (no `networkgraph` module), so node
// positions are computed here with a Fruchterman-Reingold force-directed layout
// and drawn as a `line` series (edges) plus per-community `scatter` series
// (nodes) — the same approach anyone would take without the add-on module.
const t = window.ANYPLOT_TOKENS;

// --- Data: a small friendship network across three communities -------------
const NODES = [
  { id: "Ava", group: "Work" },
  { id: "Liam", group: "Work" },
  { id: "Mia", group: "Work" },
  { id: "Noah", group: "Work" },
  { id: "Ivy", group: "Work" },
  { id: "Ethan", group: "Work" },
  { id: "Zoe", group: "Work" },
  { id: "Leo", group: "College" },
  { id: "Nora", group: "College" },
  { id: "Kai", group: "College" },
  { id: "Luna", group: "College" },
  { id: "Finn", group: "College" },
  { id: "Maya", group: "College" },
  { id: "Owen", group: "College" },
  { id: "Ruby", group: "Family" },
  { id: "Theo", group: "Family" },
  { id: "Sara", group: "Family" },
  { id: "Milo", group: "Family" },
  { id: "Ella", group: "Family" },
  { id: "Jack", group: "Family" },
];

const EDGES = [
  ["Ava", "Liam"], ["Ava", "Mia"], ["Ava", "Noah"], ["Liam", "Mia"], ["Liam", "Ivy"],
  ["Mia", "Noah"], ["Noah", "Ethan"], ["Ivy", "Zoe"], ["Ethan", "Zoe"], ["Ava", "Ethan"],
  ["Leo", "Nora"], ["Leo", "Kai"], ["Nora", "Luna"], ["Kai", "Luna"], ["Kai", "Finn"],
  ["Luna", "Maya"], ["Finn", "Owen"], ["Maya", "Owen"], ["Leo", "Maya"],
  ["Ruby", "Theo"], ["Ruby", "Sara"], ["Theo", "Milo"], ["Sara", "Ella"], ["Milo", "Jack"],
  ["Ella", "Jack"], ["Ruby", "Jack"],
  ["Ava", "Leo"], ["Mia", "Ruby"], ["Kai", "Theo"],
];

// Degree (connection count) drives node size.
const degree = {};
NODES.forEach((node) => { degree[node.id] = 0; });
EDGES.forEach(([a, b]) => { degree[a] += 1; degree[b] += 1; });

// --- Force-directed layout (Fruchterman-Reingold, fixed-seed LCG) ----------
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const AREA = 100;
const idealDistance = Math.sqrt((AREA * AREA) / NODES.length);
const pos = {};
NODES.forEach((node, i) => {
  const angle = (i / NODES.length) * 2 * Math.PI;
  pos[node.id] = {
    x: 40 * Math.cos(angle) + (rand() - 0.5) * 6,
    y: 40 * Math.sin(angle) + (rand() - 0.5) * 6,
  };
});

let temperature = AREA / 10;
for (let iter = 0; iter < 300; iter += 1) {
  const disp = {};
  NODES.forEach((node) => { disp[node.id] = { x: 0, y: 0 }; });

  for (let i = 0; i < NODES.length; i += 1) {
    for (let j = i + 1; j < NODES.length; j += 1) {
      const a = NODES[i].id;
      const b = NODES[j].id;
      const dx = pos[a].x - pos[b].x;
      const dy = pos[a].y - pos[b].y;
      const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 0.01);
      const force = (idealDistance * idealDistance) / dist;
      disp[a].x += (dx / dist) * force;
      disp[a].y += (dy / dist) * force;
      disp[b].x -= (dx / dist) * force;
      disp[b].y -= (dy / dist) * force;
    }
  }

  EDGES.forEach(([a, b]) => {
    const dx = pos[a].x - pos[b].x;
    const dy = pos[a].y - pos[b].y;
    const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 0.01);
    const force = (dist * dist) / idealDistance;
    disp[a].x -= (dx / dist) * force;
    disp[a].y -= (dy / dist) * force;
    disp[b].x += (dx / dist) * force;
    disp[b].y += (dy / dist) * force;
  });

  NODES.forEach((node) => {
    const dx = disp[node.id].x;
    const dy = disp[node.id].y;
    const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 0.01);
    const capped = Math.min(dist, temperature);
    pos[node.id].x += (dx / dist) * capped;
    pos[node.id].y += (dy / dist) * capped;
  });
  temperature *= 0.97;
}

// Normalize the free-floating layout into a fixed, centered frame — the
// repulsion/attraction forces above have no boundary, so raw coordinates can
// land anywhere; rescale to a known extent before drawing.
let minX = Infinity;
let maxX = -Infinity;
let minY = Infinity;
let maxY = -Infinity;
NODES.forEach((node) => {
  minX = Math.min(minX, pos[node.id].x);
  maxX = Math.max(maxX, pos[node.id].x);
  minY = Math.min(minY, pos[node.id].y);
  maxY = Math.max(maxY, pos[node.id].y);
});
const centerX = (minX + maxX) / 2;
const centerY = (minY + maxY) / 2;
const halfExtent = Math.max(maxX - minX, maxY - minY) / 2;
NODES.forEach((node) => {
  pos[node.id].x = ((pos[node.id].x - centerX) / halfExtent) * 50;
  pos[node.id].y = ((pos[node.id].y - centerY) / halfExtent) * 50;
});

// --- Chart -------------------------------------------------------------------
const GROUPS = ["Work", "College", "Family"];
const GROUP_COLOR = { Work: t.palette[0], College: t.palette[1], Family: t.palette[2] };
const EDGE_COLOR = t.grid.replace(/[\d.]+\)$/, "0.35)");

const edgeData = [];
EDGES.forEach(([a, b]) => {
  edgeData.push([pos[a].x, pos[a].y]);
  edgeData.push([pos[b].x, pos[b].y]);
  edgeData.push(null);
});

const nodeSeries = GROUPS.map((group) => ({
  type: "scatter",
  name: group,
  color: GROUP_COLOR[group],
  data: NODES.filter((node) => node.group === group).map((node) => ({
    x: pos[node.id].x,
    y: pos[node.id].y,
    name: node.id,
    marker: { radius: 6 + degree[node.id] * 1.8 },
  })),
  marker: { lineColor: t.pageBg, lineWidth: 1 },
  dataLabels: {
    enabled: true,
    format: "{point.name}",
    allowOverlap: false,
    y: -14,
    style: { color: t.ink, fontSize: "12px", fontWeight: "normal", textOutline: "none" },
  },
}));

Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "network-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Friendship network across three communities — node size = number of connections",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: { visible: false, min: -58, max: 58 },
  yAxis: { visible: false, min: -58, max: 58, title: { text: null } },
  legend: {
    enabled: true,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false },
    scatter: { states: { hover: { enabled: false } } },
  },
  series: [
    {
      type: "line",
      name: "Connections",
      data: edgeData,
      color: EDGE_COLOR,
      lineWidth: 1.5,
      marker: { enabled: false },
      enableMouseTracking: false,
      showInLegend: false,
      zIndex: 0,
    },
    ...nodeSeries,
  ],
});
