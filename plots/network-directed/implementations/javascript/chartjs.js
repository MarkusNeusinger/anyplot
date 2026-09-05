// anyplot.ai
// network-directed: Directed Network Graph
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-05
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data: software module import graph -------------------------------------
// Layered left-to-right by build order; an edge (a, b) means "a is imported
// by b", so the arrow flows from the dependency toward the dependent module.
const nodes = [
  { id: "utils", x: 0, y: 1.0 },
  { id: "config", x: 0, y: 3.6 },
  { id: "logger", x: 1, y: 0.4 },
  { id: "validator", x: 1, y: 2.6 },
  { id: "db", x: 2, y: 1.6 },
  { id: "cache", x: 2, y: 3.9 },
  { id: "auth", x: 3, y: 1.0 },
  { id: "middleware", x: 3, y: 3.2 },
  { id: "api", x: 4, y: 2.1 },
  { id: "router", x: 5, y: 0.9 },
  { id: "ui", x: 5, y: 3.3 },
];

const edges = [
  ["utils", "logger"],
  ["utils", "validator"],
  ["config", "db"],
  ["config", "cache"],
  ["logger", "db"],
  ["logger", "middleware"],
  ["validator", "auth"],
  ["db", "auth"],
  ["cache", "middleware"],
  ["auth", "api"],
  ["middleware", "api"],
  ["api", "router"],
  ["api", "ui"],
];

const nodeById = Object.fromEntries(nodes.map((n) => [n.id, n]));
const NODE_RADIUS = 30;

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Directed-edge plugin: arrows + node labels around the scatter dataset ---
const directedEdgesPlugin = {
  id: "directedEdges",
  beforeDatasetsDraw(chart) {
    const {
      ctx,
      scales: { x: xScale, y: yScale },
    } = chart;
    ctx.save();
    ctx.strokeStyle = t.inkSoft;
    ctx.fillStyle = t.inkSoft;
    ctx.lineWidth = 2.5;
    ctx.globalAlpha = 0.65;

    edges.forEach(([sourceId, targetId]) => {
      const s = nodeById[sourceId];
      const d = nodeById[targetId];
      const x1 = xScale.getPixelForValue(s.x);
      const y1 = yScale.getPixelForValue(s.y);
      const x2 = xScale.getPixelForValue(d.x);
      const y2 = yScale.getPixelForValue(d.y);

      const angle = Math.atan2(y2 - y1, x2 - x1);
      const startX = x1 + Math.cos(angle) * NODE_RADIUS;
      const startY = y1 + Math.sin(angle) * NODE_RADIUS;
      const endX = x2 - Math.cos(angle) * (NODE_RADIUS + 10);
      const endY = y2 - Math.sin(angle) * (NODE_RADIUS + 10);

      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.lineTo(endX, endY);
      ctx.stroke();

      const arrowLength = 16;
      const arrowSpread = Math.PI / 7;
      const tipX = endX + Math.cos(angle) * 10;
      const tipY = endY + Math.sin(angle) * 10;
      ctx.beginPath();
      ctx.moveTo(tipX, tipY);
      ctx.lineTo(
        tipX - arrowLength * Math.cos(angle - arrowSpread),
        tipY - arrowLength * Math.sin(angle - arrowSpread),
      );
      ctx.lineTo(
        tipX - arrowLength * Math.cos(angle + arrowSpread),
        tipY - arrowLength * Math.sin(angle + arrowSpread),
      );
      ctx.closePath();
      ctx.fill();
    });
    ctx.restore();
  },
  afterDatasetsDraw(chart) {
    const {
      ctx,
      scales: { x: xScale, y: yScale },
    } = chart;
    ctx.save();
    ctx.font = "600 16px sans-serif";
    ctx.fillStyle = t.ink;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    nodes.forEach((n) => {
      const px = xScale.getPixelForValue(n.x);
      const py = yScale.getPixelForValue(n.y);
      ctx.fillText(n.id, px, py + NODE_RADIUS + 8);
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
        label: "Module",
        data: nodes.map((n) => ({ x: n.x, y: n.y })),
        backgroundColor: t.palette[0],
        borderColor: t.pageBg,
        borderWidth: 3,
        pointRadius: NODE_RADIUS,
        pointHoverRadius: NODE_RADIUS,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: 40 },
    plugins: {
      title: {
        display: true,
        text: "network-directed · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: { display: false, min: -0.6, max: 5.6 },
      y: { display: false, min: -0.6, max: 4.5 },
    },
  },
  plugins: [directedEdgesPlugin],
});
