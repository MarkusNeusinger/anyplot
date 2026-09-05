// anyplot.ai
// network-directed: Directed Network Graph
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data: a software module import graph, laid out in dependency tiers ----
// Arrows point from an importing module to the module it imports. Node radius
// encodes in-degree (how many other modules import it), so the shared
// foundation modules read as visual hubs.
const TIERS = [
  {
    name: "Entry points",
    color: t.palette[0],
    nodes: [
      { id: "cli", name: "cli", y: 1, indeg: 0 },
      { id: "server", name: "server", y: 2, indeg: 0 },
      { id: "worker", name: "worker", y: 3, indeg: 0 },
    ],
  },
  {
    name: "Orchestration",
    color: t.palette[1],
    nodes: [
      { id: "router", name: "router", y: 1, indeg: 2 },
      { id: "scheduler", name: "scheduler", y: 2, indeg: 1 },
      { id: "api_gateway", name: "api_gateway", y: 3, indeg: 1 },
    ],
  },
  {
    name: "Services",
    color: t.palette[2],
    nodes: [
      { id: "auth", name: "auth", y: 0.8, indeg: 3 },
      { id: "database", name: "database", y: 1.6, indeg: 3 },
      { id: "cache", name: "cache", y: 2.4, indeg: 2 },
      { id: "queue", name: "queue", y: 3.2, indeg: 2 },
    ],
  },
  {
    name: "Foundation",
    color: t.palette[3],
    nodes: [
      { id: "logger", name: "logger", y: 1, indeg: 7 },
      { id: "config", name: "config", y: 2, indeg: 3 },
      { id: "utils", name: "utils", y: 3, indeg: 3 },
    ],
  },
];

const EDGES = [
  ["cli", "router"],
  ["cli", "config"],
  ["server", "router"],
  ["server", "auth"],
  ["server", "api_gateway"],
  ["worker", "scheduler"],
  ["worker", "queue"],
  ["worker", "config"],
  ["router", "auth"],
  ["router", "database"],
  ["router", "logger"],
  ["scheduler", "queue"],
  ["scheduler", "database"],
  ["scheduler", "logger"],
  ["api_gateway", "auth"],
  ["api_gateway", "cache"],
  ["api_gateway", "logger"],
  ["auth", "database"],
  ["auth", "cache"],
  ["auth", "logger"],
  ["database", "logger"],
  ["database", "config"],
  ["cache", "logger"],
  ["queue", "logger"],
  ["queue", "utils"],
  ["logger", "utils"],
  ["config", "utils"],
];

const nodeRadius = (indeg) => 14 + indeg * 3;

// --- Chart -------------------------------------------------------------
const series = TIERS.map((tier, i) => ({
  name: tier.name,
  color: tier.color,
  data: tier.nodes.map((n) => ({
    id: n.id,
    x: i * 3,
    y: n.y,
    name: n.name,
    marker: { radius: nodeRadius(n.indeg), lineColor: t.pageBg, lineWidth: 2 },
    dataLabels: { format: n.name, y: -(nodeRadius(n.indeg) + 10) },
  })),
}));

Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    events: {
      load() {
        drawEdges(this);
      },
    },
  },
  credits: { enabled: false },
  title: {
    text: "network-directed · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Module import graph — arrows point from importer to dependency",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    min: -1.5,
    max: 10.5,
    lineWidth: 0,
    tickLength: 0,
    gridLineWidth: 0,
    labels: { enabled: false },
    title: { text: null },
  },
  yAxis: {
    min: 0.3,
    max: 3.7,
    lineWidth: 0,
    tickLength: 0,
    gridLineWidth: 0,
    labels: { enabled: false },
    title: { text: null },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { enabled: false },
  plotOptions: {
    series: {
      animation: false,
      dataLabels: {
        enabled: true,
        style: {
          color: t.ink,
          fontSize: "14px",
          fontWeight: "normal",
          textOutline: "none",
        },
      },
    },
  },
  series,
});

// Edges are drawn once with the core SVGRenderer, behind the node markers —
// the core `highcharts` bundle has no networkgraph module (add-on only), so
// node-link edges with arrowheads are composed by hand from point coordinates.
function drawEdges(c) {
  const group = c.renderer.g("edges").attr({ zIndex: 1 }).add();
  const strokeColor = t.inkSoft;

  EDGES.forEach(([fromId, toId]) => {
    const from = c.get(fromId);
    const to = c.get(toId);
    if (!from || !to) return;

    const sx = c.plotLeft + from.plotX;
    const sy = c.plotTop + from.plotY;
    const tx = c.plotLeft + to.plotX;
    const ty = c.plotTop + to.plotY;

    const dx = tx - sx;
    const dy = ty - sy;
    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
    const ux = dx / dist;
    const uy = dy / dist;

    const rFrom = from.marker.radius + 2;
    const rTo = to.marker.radius + 4;
    const x1 = sx + ux * rFrom;
    const y1 = sy + uy * rFrom;
    const x2 = tx - ux * rTo;
    const y2 = ty - uy * rTo;

    drawArrow(c.renderer, group, x1, y1, x2, y2, strokeColor);
  });

  c.series.forEach((s) => s.group.toFront());
  c.series.forEach((s) => s.dataLabelsGroup && s.dataLabelsGroup.toFront());
}

function drawArrow(renderer, group, x1, y1, x2, y2, color) {
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const headLen = 12;
  const headAngle = Math.PI / 7;

  const shaftEndX = x2 - Math.cos(angle) * headLen * 0.6;
  const shaftEndY = y2 - Math.sin(angle) * headLen * 0.6;

  renderer
    .path(["M", x1, y1, "L", shaftEndX, shaftEndY])
    .attr({
      stroke: color,
      "stroke-width": 2,
      "stroke-linecap": "round",
      fill: "none",
      opacity: 0.65,
    })
    .add(group);

  const p1x = x2 - Math.cos(angle - headAngle) * headLen;
  const p1y = y2 - Math.sin(angle - headAngle) * headLen;
  const p2x = x2 - Math.cos(angle + headAngle) * headLen;
  const p2y = y2 - Math.sin(angle + headAngle) * headLen;

  renderer
    .path(["M", x2, y2, "L", p1x, p1y, "L", p2x, p2y, "Z"])
    .attr({ fill: color, stroke: "none", opacity: 0.8 })
    .add(group);
}
