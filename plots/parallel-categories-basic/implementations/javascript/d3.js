// anyplot.ai
// parallel-categories-basic: Basic Parallel Categories Plot
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 150, right: 190, bottom: 40, left: 190 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;
const barWidth = 20;
const nodePadding = 22;

// --- Data: customer journey from acquisition channel to product category to
// purchase outcome (in-memory, deterministic) --------------------------------
const channels = ["Organic Search", "Paid Ads", "Referral"];
const categories = ["Electronics", "Apparel", "Home Goods"];
const outcomes = ["Purchased", "Abandoned"];

const flows = [
  { channel: "Organic Search", category: "Electronics", outcome: "Purchased", count: 420 },
  { channel: "Organic Search", category: "Electronics", outcome: "Abandoned", count: 180 },
  { channel: "Organic Search", category: "Apparel", outcome: "Purchased", count: 260 },
  { channel: "Organic Search", category: "Apparel", outcome: "Abandoned", count: 140 },
  { channel: "Organic Search", category: "Home Goods", outcome: "Purchased", count: 190 },
  { channel: "Organic Search", category: "Home Goods", outcome: "Abandoned", count: 110 },
  { channel: "Paid Ads", category: "Electronics", outcome: "Purchased", count: 150 },
  { channel: "Paid Ads", category: "Electronics", outcome: "Abandoned", count: 210 },
  { channel: "Paid Ads", category: "Apparel", outcome: "Purchased", count: 120 },
  { channel: "Paid Ads", category: "Apparel", outcome: "Abandoned", count: 190 },
  { channel: "Paid Ads", category: "Home Goods", outcome: "Purchased", count: 90 },
  { channel: "Paid Ads", category: "Home Goods", outcome: "Abandoned", count: 160 },
  { channel: "Referral", category: "Electronics", outcome: "Purchased", count: 200 },
  { channel: "Referral", category: "Electronics", outcome: "Abandoned", count: 90 },
  { channel: "Referral", category: "Apparel", outcome: "Purchased", count: 130 },
  { channel: "Referral", category: "Apparel", outcome: "Abandoned", count: 70 },
  { channel: "Referral", category: "Home Goods", outcome: "Purchased", count: 100 },
  { channel: "Referral", category: "Home Goods", outcome: "Abandoned", count: 60 },
];

const totalCount = flows.reduce((s, f) => s + f.count, 0);

// --- Column layout: a shared pixels-per-unit scale keeps a flow's ribbon the
// same height on both ends it touches, regardless of how many categories
// share that column ----------------------------------------------------------
function columnValue(values, key) {
  return values.map((v) => ({
    value: v,
    total: flows.filter((f) => f[key] === v).reduce((s, f) => s + f.count, 0),
  }));
}
function rawKy(n) {
  return (ih - nodePadding * (n - 1)) / totalCount;
}
const ky = Math.min(rawKy(channels.length), rawKy(categories.length), rawKy(outcomes.length));

function layoutColumn(values, key) {
  const items = columnValue(values, key);
  const contentHeight = items.reduce((s, d) => s + d.total * ky, 0) + nodePadding * (items.length - 1);
  let y = margin.top + (ih - contentHeight) / 2;
  const nodes = new Map();
  for (const d of items) {
    const h = d.total * ky;
    nodes.set(d.value, { y0: y, y1: y + h, total: d.total });
    y += h + nodePadding;
  }
  return nodes;
}

const x0 = margin.left;
const x1 = margin.left + iw / 2;
const x2 = margin.left + iw;

const channelNodes = layoutColumn(channels, "channel");
const categoryNodes = layoutColumn(categories, "category");
const outcomeNodes = layoutColumn(outcomes, "outcome");

// --- Stack each flow's sub-ribbon within its endpoints. Two cursors per node
// (in vs. out) because a category node is a link target on the left and a
// link source on the right --------------------------------------------------
function stack(order, cursorStart, key, tagY0, tagY1) {
  const cursor = new Map(cursorStart);
  for (const f of order) {
    const h = f.count * ky;
    const y0 = cursor.get(f[key]);
    f[tagY0] = y0;
    f[tagY1] = y0 + h;
    cursor.set(f[key], y0 + h);
  }
}

const byIndex = (list) => (v) => list.indexOf(v);
const categoryIx = byIndex(categories);
const outcomeIx = byIndex(outcomes);
const channelIx = byIndex(channels);

stack(
  [...flows].sort((a, b) => categoryIx(a.category) - categoryIx(b.category) || outcomeIx(a.outcome) - outcomeIx(b.outcome)),
  channels.map((c) => [c, channelNodes.get(c).y0]),
  "channel",
  "aSourceY0",
  "aSourceY1"
);
stack(
  [...flows].sort((a, b) => channelIx(a.channel) - channelIx(b.channel) || outcomeIx(a.outcome) - outcomeIx(b.outcome)),
  categories.map((c) => [c, categoryNodes.get(c).y0]),
  "category",
  "aTargetY0",
  "aTargetY1"
);
stack(
  [...flows].sort((a, b) => outcomeIx(a.outcome) - outcomeIx(b.outcome) || channelIx(a.channel) - channelIx(b.channel)),
  categories.map((c) => [c, categoryNodes.get(c).y0]),
  "category",
  "bSourceY0",
  "bSourceY1"
);
stack(
  [...flows].sort((a, b) => categoryIx(a.category) - categoryIx(b.category) || channelIx(a.channel) - channelIx(b.channel)),
  outcomes.map((o) => [o, outcomeNodes.get(o).y0]),
  "outcome",
  "bTargetY0",
  "bTargetY1"
);

// --- Ribbon shape: two cubic-bezier edges between a source band and a target
// band, filled as a single closed path ---------------------------------------
function ribbonPath(xa, xb, sy0, sy1, ty0, ty1) {
  const xm = (xa + xb) / 2;
  return `M${xa},${sy0}C${xm},${sy0} ${xm},${ty0} ${xb},${ty0}L${xb},${ty1}C${xm},${ty1} ${xm},${sy1} ${xa},${sy1}Z`;
}

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

const color = d3.scaleOrdinal().domain(channels).range(t.palette.slice(0, channels.length));

// Ribbons (drawn first, nodes sit on top of their edges)
svg
  .selectAll(".ribbon-a")
  .data(flows)
  .join("path")
  .attr("d", (f) => ribbonPath(x0 + barWidth, x1, f.aSourceY0, f.aSourceY1, f.aTargetY0, f.aTargetY1))
  .attr("fill", (f) => color(f.channel))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1)
  .attr("opacity", 0.65);

svg
  .selectAll(".ribbon-b")
  .data(flows)
  .join("path")
  .attr("d", (f) => ribbonPath(x1 + barWidth, x2, f.bSourceY0, f.bSourceY1, f.bTargetY0, f.bTargetY1))
  .attr("fill", (f) => color(f.channel))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1)
  .attr("opacity", 0.65);

// Node bars: theme-adaptive neutral anchor — these represent structural
// totals, not a categorical series, so they stay ink-colored rather than
// pulling another Imprint hue.
const columns = [
  { x: x0, nodes: channelNodes, values: channels, label: "Acquisition Channel", labelSide: "left", colorByChannel: true },
  { x: x1, nodes: categoryNodes, values: categories, label: "Product Category", labelSide: "right", colorByChannel: false },
  { x: x2, nodes: outcomeNodes, values: outcomes, label: "Purchase Outcome", labelSide: "right", colorByChannel: false },
];

for (const col of columns) {
  svg
    .append("g")
    .selectAll("rect")
    .data(col.values)
    .join("rect")
    .attr("x", col.x)
    .attr("y", (v) => col.nodes.get(v).y0)
    .attr("width", barWidth)
    .attr("height", (v) => col.nodes.get(v).y1 - col.nodes.get(v).y0)
    .attr("fill", t.ink);

  svg
    .append("g")
    .selectAll("text")
    .data(col.values)
    .join("text")
    .attr("x", col.labelSide === "left" ? col.x - 14 : col.x + barWidth + 14)
    .attr("y", (v) => (col.nodes.get(v).y0 + col.nodes.get(v).y1) / 2)
    .attr("dy", "0.35em")
    .attr("text-anchor", col.labelSide === "left" ? "end" : "start")
    .style("font-size", "17px")
    .style("font-weight", col.colorByChannel ? "600" : "400")
    .style("paint-order", "stroke")
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 6)
    .attr("stroke-linejoin", "round")
    .attr("fill", col.colorByChannel ? (v) => color(v) : t.inkSoft)
    .text((v) => v);

  svg
    .append("text")
    .attr("x", col.x + barWidth / 2)
    .attr("y", margin.top - 34)
    .attr("text-anchor", "middle")
    .style("font-size", "15px")
    .style("font-weight", "600")
    .style("letter-spacing", "0.02em")
    .attr("fill", t.inkSoft)
    .text(col.label.toUpperCase());
}

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 54)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "24px")
  .style("font-weight", "600")
  .text("parallel-categories-basic · javascript · d3 · anyplot.ai");
