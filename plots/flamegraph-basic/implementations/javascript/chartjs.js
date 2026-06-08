// anyplot.ai
// flamegraph-basic: Flame Graph for Performance Profiling
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 85/100 | Created: 2026-06-08
//# anyplot-orientation: landscape
// anyplot.ai
// flamegraph-basic: Flame Graph for Performance Profiling
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-08

const t = window.ANYPLOT_TOKENS;

// --- Data: simulated CPU profile of a web API request handler --------------
// Tree of call stacks. `self` = samples spent in the function itself (not in
// its children). A node's *total* = self + sum(children.total) and becomes the
// width of its flame-graph bar. Children sit above the parent and fill it
// left-to-right; any leftover width at depth+1 is the parent's `self` time.
const profile = {
  name: "main", self: 2, children: [
    { name: "runServer", self: 6, children: [
      { name: "handleRequest", self: 8, children: [
        { name: "parseHeaders", self: 32, children: [] },
        { name: "routeRequest", self: 4, children: [
          { name: "authMiddleware", self: 18, children: [
            { name: "verifyToken", self: 14, children: [] },
            { name: "loadUser", self: 22, children: [] },
          ] },
          { name: "dispatchHandler", self: 6, children: [
            { name: "queryDB", self: 8, children: [
              { name: "openConn", self: 12, children: [] },
              { name: "executeQuery", self: 78, children: [] },
              { name: "parseRows", self: 22, children: [] },
            ] },
            { name: "renderTemplate", self: 14, children: [
              { name: "loadTemplate", self: 10, children: [] },
              { name: "compileTemplate", self: 32, children: [] },
              { name: "renderHTML", self: 24, children: [] },
            ] },
            { name: "serialize", self: 28, children: [] },
          ] },
        ] },
        { name: "writeResponse", self: 18, children: [] },
      ] },
      { name: "gcMinor", self: 20, children: [] },
    ] },
  ],
};

// Flatten the tree into (depth, start, end, total) frames via DFS.
const frames = [];
let maxDepth = 0;
function visit(node, depth, x) {
  if (depth > maxDepth) maxDepth = depth;
  let childX = x;
  let kidsTotal = 0;
  for (const child of node.children) {
    const ct = visit(child, depth + 1, childX);
    childX += ct;
    kidsTotal += ct;
  }
  const total = node.self + kidsTotal;
  frames.push({ name: node.name, depth, start: x, end: x + total, total });
  return total;
}
const totalSamples = visit(profile, 0, 0);

// --- Warm palette (Imprint semantic exception for flame graphs) ------------
// The spec explicitly calls for the conventional yellows-oranges-reds aesthetic
// invented by Brendan Gregg. Pick from Imprint's three warm anchors (amber,
// ochre, matte red) by hashing the function name + depth, so the same call
// site always reads the same hue across renders.
const warmAnchors = ["#DDCC77", "#BD8233", "#AE3030"];
function warmFor(seed) {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return warmAnchors[(h >>> 0) % warmAnchors.length];
}
function textOn(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return lum > 0.5 ? "#1A1A17" : "#FFFDF6";
}

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Custom flame-graph renderer ------------------------------------------
// Chart.js core has no flame-graph type, so we run a `type: 'bar'` chart for
// its axes / title chrome and draw the per-frame rectangles ourselves in an
// `afterDatasetsDraw` plugin. y-pixel positions are computed from chartArea
// rather than the category scale so reverse / band alignment stay exact.
const flamePlugin = {
  id: "flamegraph",
  afterDatasetsDraw(chart) {
    const { ctx, chartArea, scales: { x } } = chart;
    const rows = maxDepth + 1;
    const bandPx = (chartArea.bottom - chartArea.top) / rows;
    const gap = 2;
    const barH = Math.max(2, bandPx - gap);

    ctx.save();
    ctx.font = "600 14px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    ctx.textBaseline = "middle";

    for (const f of frames) {
      const xLeft = x.getPixelForValue(f.start);
      const xRight = x.getPixelForValue(f.end);
      // depth 0 at the bottom band; depth N at the top.
      const yCenter = chartArea.bottom - (f.depth + 0.5) * bandPx;
      const top = yCenter - barH / 2;
      const w = Math.max(1, xRight - xLeft - 1);

      const fill = warmFor(f.name + "·" + f.depth);
      ctx.fillStyle = fill;
      ctx.fillRect(xLeft, top, w, barH);
      // pageBg-coloured hairline separates adjacent siblings on both themes.
      ctx.strokeStyle = t.pageBg;
      ctx.lineWidth = 1;
      ctx.strokeRect(xLeft + 0.5, top + 0.5, w - 1, barH - 1);

      if (w >= 60) {
        ctx.fillStyle = textOn(fill);
        let text = f.name;
        const maxText = w - 12;
        if (ctx.measureText(text).width > maxText) {
          while (text.length > 2 && ctx.measureText(text + "…").width > maxText) {
            text = text.slice(0, -1);
          }
          text = text + "…";
        }
        ctx.fillText(text, xLeft + 6, yCenter);
      }
    }
    ctx.restore();
  },
};

// --- Chart -----------------------------------------------------------------
const depthLabels = Array.from({ length: maxDepth + 1 }, (_, i) => String(i));

new Chart(canvas, {
  type: "bar",
  data: {
    labels: depthLabels,
    datasets: [{
      label: "Stack frames",
      data: depthLabels.map(() => 0), // placeholder; real bars are drawn by the plugin
      backgroundColor: "rgba(0,0,0,0)",
      borderColor: "rgba(0,0,0,0)",
    }],
  },
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { left: 8, right: 18, top: 4, bottom: 8 } },
    plugins: {
      title: {
        display: true,
        text: "flamegraph-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "600" },
        padding: { top: 4, bottom: 6 },
      },
      subtitle: {
        display: true,
        text: "Simulated CPU profile · bar width = samples · horizontal order is arbitrary, not temporal",
        color: t.inkSoft,
        font: { size: 14, style: "italic" },
        padding: { bottom: 16 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: totalSamples,
        title: {
          display: true,
          text: "Samples",
          color: t.ink,
          font: { size: 14 },
          padding: { top: 8 },
        },
        ticks: { color: t.inkSoft, font: { size: 12 } },
        grid: { color: t.grid, drawTicks: false },
        border: { color: t.grid },
      },
      y: {
        type: "category",
        labels: depthLabels,
        reverse: true, // depth 0 (root) at the bottom
        title: {
          display: true,
          text: "Call stack depth  (root → leaf)",
          color: t.ink,
          font: { size: 14 },
        },
        ticks: { color: t.inkSoft, font: { size: 12 } },
        grid: { display: false, drawTicks: false },
        border: { color: t.grid },
      },
    },
  },
  plugins: [flamePlugin],
});
