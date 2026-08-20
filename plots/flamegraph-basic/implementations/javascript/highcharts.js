// anyplot.ai
// flamegraph-basic: Flame Graph for Performance Profiling
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-08-20

const t = window.ANYPLOT_TOKENS;

// --- Data: folded call-stack samples (self-time per stack frame) -----------
// Each row is the *own* (exclusive) sample count captured for that exact
// stack path — the standard "folded stack" input format flame graphs use.
const samples = [
  { stack: "main;acceptConnections", value: 40 },
  { stack: "main;acceptConnections;parseHeaders", value: 220 },
  { stack: "main;acceptConnections;tlsHandshake", value: 150 },
  { stack: "main;garbageCollect", value: 95 },
  { stack: "main;logRequest", value: 45 },
  { stack: "main;routeRequest", value: 30 },
  { stack: "main;routeRequest;authMiddleware", value: 90 },
  { stack: "main;routeRequest;handleApi", value: 20 },
  { stack: "main;routeRequest;handleApi;validateInput", value: 60 },
  { stack: "main;routeRequest;handleApi;queryDatabase", value: 15 },
  { stack: "main;routeRequest;handleApi;queryDatabase;executeQuery", value: 340 },
  { stack: "main;routeRequest;handleApi;queryDatabase;parseResults", value: 180 },
  { stack: "main;routeRequest;handleApi;serializeResponse", value: 110 },
];

// --- Build the call tree: own time per node, then roll up totals -----------
const root = { name: "main", children: {}, own: 0 };
for (const { stack, value } of samples) {
  const parts = stack.split(";");
  let node = root;
  for (let i = 1; i < parts.length; i++) {
    const name = parts[i];
    if (!node.children[name]) node.children[name] = { name, children: {}, own: 0 };
    node = node.children[name];
  }
  node.own += value;
}

let maxDepth = 0;
const rollUp = (node, depth) => {
  maxDepth = Math.max(maxDepth, depth);
  const kids = Object.values(node.children);
  node.total = node.own + kids.reduce((sum, kid) => sum + rollUp(kid, depth + 1), 0);
  return node.total;
};
rollUp(root, 0);
const rootTotal = root.total;

// --- Flatten the tree into left-to-right stacked bars, one series per frame
// A stacked bar chart tiles series strictly by declaration order per row, so
// a depth-first walk reproduces the classic flame-graph layout. Any node that
// doesn't fully cover its own width in the row below it (self time, or a
// leaf ending before the deepest row) needs an invisible spacer series to
// keep every deeper row aligned under the correct parent.
const frames = [];

const padDown = (value, depth) => {
  if (depth > maxDepth) return;
  frames.push({ depth, value, name: null, real: false });
  padDown(value, depth + 1);
};

const walk = (node, depth) => {
  frames.push({ depth, value: node.total, name: node.name, real: true });
  const kids = Object.values(node.children).sort((a, b) => a.name.localeCompare(b.name));
  if (kids.length) {
    for (const kid of kids) walk(kid, depth + 1);
    if (node.own > 0) padDown(node.own, depth + 1);
  } else if (node.total > 0) {
    padDown(node.total, depth + 1);
  }
};
walk(root, 0);

// --- Color: conventional warm flame-graph palette, built from Imprint's ----
// warm-family anchors only (amber -> ochre -> matte-red). The spec calls for
// yellows/oranges/reds by domain convention (Brendan Gregg's original flame
// graph aesthetic), which is the semantic-exception case in the style guide
// — so frames don't follow the usual "first series is brand green" rule.
const warmStops = [t.amber, t.palette[3], t.palette[4]];
const lerp = (hexA, hexB, f) => {
  const a = Highcharts.color(hexA).rgba;
  const b = Highcharts.color(hexB).rgba;
  const mix = [0, 1, 2].map((i) => Math.round(a[i] + (b[i] - a[i]) * f));
  return `rgb(${mix[0]}, ${mix[1]}, ${mix[2]})`;
};
const hash = (str) => {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0;
  return (h % 1000) / 1000;
};
const warmColor = (name) => {
  const f = hash(name);
  return f < 0.5 ? lerp(warmStops[0], warmStops[1], f * 2) : lerp(warmStops[1], warmStops[2], (f - 0.5) * 2);
};

const categories = Array.from({ length: maxDepth + 1 }, (_, i) => (i === 0 ? "Depth 0 · root" : `Depth ${i}`));

const series = frames.map((frame) => {
  const data = new Array(categories.length).fill(null);
  data[frame.depth] = frame.value;
  const widthFraction = frame.value / rootTotal;
  return {
    type: "bar",
    name: frame.real ? frame.name : undefined,
    data,
    stack: "flame",
    color: frame.real ? warmColor(frame.name) : "transparent",
    borderWidth: frame.real ? 1 : 0,
    borderColor: t.pageBg,
    enableMouseTracking: frame.real,
    showInLegend: false,
    // Fixed dark ink, not theme-adaptive: the label sits on the warm data
    // fill (constant across themes), not on the page background. Highcharts
    // hides an inside column/bar label it can't fit in the box by default —
    // exactly the "only when wide enough" behavior the spec asks for, so no
    // manual width estimate is needed beyond skipping obviously-tiny slivers.
    dataLabels: {
      enabled: frame.real && widthFraction > 0.02,
      inside: true,
      align: "center",
      verticalAlign: "middle",
      format: frame.name,
      style: { color: "#1A1A17", fontSize: "13px", fontWeight: "500", textOutline: "none" },
    },
  };
});

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: { type: "bar", backgroundColor: "transparent", animation: false, style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  title: {
    text: "flamegraph-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "CPU profile of a request-handling call stack — bar width is share of total samples",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    categories,
    reversed: false,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: "Call stack depth", style: { color: t.inkSoft, fontSize: "16px" } },
  },
  yAxis: { visible: false, min: 0, max: rootTotal, reversed: true },
  legend: { enabled: false },
  plotOptions: {
    series: { animation: false, stacking: "normal", pointPadding: 0.02, groupPadding: 0, borderRadius: 0 },
  },
  tooltip: {
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    style: { color: t.ink, fontSize: "14px" },
    formatter() {
      const pct = ((this.y / rootTotal) * 100).toFixed(1);
      return `<b>${this.series.name}</b><br/>${this.y.toLocaleString()} samples (${pct}%)`;
    },
  },
  series,
});
