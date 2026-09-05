// anyplot.ai
// parallel-categories-basic: Basic Parallel Categories Plot
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 81/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 150, right: 190, bottom: 40, left: 190 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;
const barWidth = 20;
const nodePadding = 22;

// --- Data: customer journey from acquisition channel through product
// category and device type to purchase outcome (in-memory, deterministic).
// Device counts are a fixed per-channel desktop/mobile split of each
// channel-category-outcome total (Organic Search skews desktop-heavy research
// behavior 65/35, Paid Ads skews mobile 40/60, Referral is closer to even
// 55/45) — no RNG, every count traces back to an explicit ratio. ------------
const dims = [
  { key: "channel", label: "Acquisition Channel", values: ["Organic Search", "Paid Ads", "Referral"] },
  { key: "category", label: "Product Category", values: ["Electronics", "Apparel", "Home Goods"] },
  { key: "device", label: "Device Type", values: ["Desktop", "Mobile"] },
  { key: "outcome", label: "Purchase Outcome", values: ["Purchased", "Abandoned"] },
];

const flows = [
  { channel: "Organic Search", category: "Electronics", device: "Desktop", outcome: "Purchased", count: 273 },
  { channel: "Organic Search", category: "Electronics", device: "Desktop", outcome: "Abandoned", count: 117 },
  { channel: "Organic Search", category: "Electronics", device: "Mobile", outcome: "Purchased", count: 147 },
  { channel: "Organic Search", category: "Electronics", device: "Mobile", outcome: "Abandoned", count: 63 },
  { channel: "Organic Search", category: "Apparel", device: "Desktop", outcome: "Purchased", count: 169 },
  { channel: "Organic Search", category: "Apparel", device: "Desktop", outcome: "Abandoned", count: 91 },
  { channel: "Organic Search", category: "Apparel", device: "Mobile", outcome: "Purchased", count: 91 },
  { channel: "Organic Search", category: "Apparel", device: "Mobile", outcome: "Abandoned", count: 49 },
  { channel: "Organic Search", category: "Home Goods", device: "Desktop", outcome: "Purchased", count: 124 },
  { channel: "Organic Search", category: "Home Goods", device: "Desktop", outcome: "Abandoned", count: 72 },
  { channel: "Organic Search", category: "Home Goods", device: "Mobile", outcome: "Purchased", count: 66 },
  { channel: "Organic Search", category: "Home Goods", device: "Mobile", outcome: "Abandoned", count: 38 },
  { channel: "Paid Ads", category: "Electronics", device: "Desktop", outcome: "Purchased", count: 60 },
  { channel: "Paid Ads", category: "Electronics", device: "Desktop", outcome: "Abandoned", count: 84 },
  { channel: "Paid Ads", category: "Electronics", device: "Mobile", outcome: "Purchased", count: 90 },
  { channel: "Paid Ads", category: "Electronics", device: "Mobile", outcome: "Abandoned", count: 126 },
  { channel: "Paid Ads", category: "Apparel", device: "Desktop", outcome: "Purchased", count: 48 },
  { channel: "Paid Ads", category: "Apparel", device: "Desktop", outcome: "Abandoned", count: 76 },
  { channel: "Paid Ads", category: "Apparel", device: "Mobile", outcome: "Purchased", count: 72 },
  { channel: "Paid Ads", category: "Apparel", device: "Mobile", outcome: "Abandoned", count: 114 },
  { channel: "Paid Ads", category: "Home Goods", device: "Desktop", outcome: "Purchased", count: 36 },
  { channel: "Paid Ads", category: "Home Goods", device: "Desktop", outcome: "Abandoned", count: 64 },
  { channel: "Paid Ads", category: "Home Goods", device: "Mobile", outcome: "Purchased", count: 54 },
  { channel: "Paid Ads", category: "Home Goods", device: "Mobile", outcome: "Abandoned", count: 96 },
  { channel: "Referral", category: "Electronics", device: "Desktop", outcome: "Purchased", count: 110 },
  { channel: "Referral", category: "Electronics", device: "Desktop", outcome: "Abandoned", count: 50 },
  { channel: "Referral", category: "Electronics", device: "Mobile", outcome: "Purchased", count: 90 },
  { channel: "Referral", category: "Electronics", device: "Mobile", outcome: "Abandoned", count: 40 },
  { channel: "Referral", category: "Apparel", device: "Desktop", outcome: "Purchased", count: 72 },
  { channel: "Referral", category: "Apparel", device: "Desktop", outcome: "Abandoned", count: 39 },
  { channel: "Referral", category: "Apparel", device: "Mobile", outcome: "Purchased", count: 58 },
  { channel: "Referral", category: "Apparel", device: "Mobile", outcome: "Abandoned", count: 31 },
  { channel: "Referral", category: "Home Goods", device: "Desktop", outcome: "Purchased", count: 55 },
  { channel: "Referral", category: "Home Goods", device: "Desktop", outcome: "Abandoned", count: 33 },
  { channel: "Referral", category: "Home Goods", device: "Mobile", outcome: "Purchased", count: 45 },
  { channel: "Referral", category: "Home Goods", device: "Mobile", outcome: "Abandoned", count: 27 },
];

const totalCount = flows.reduce((s, f) => s + f.count, 0);
const byIndex = (list) => (v) => list.indexOf(v);
const ixOf = dims.map((d) => byIndex(d.values));

// A single global dimension-order sort (channel -> category -> device ->
// outcome) drives every node's internal stacking below, so a flow keeps the
// same relative vertical slot on both faces of every interior node instead
// of twisting inside the node bar — the source of most avoidable crossings.
const flowOrder = [...flows].sort((a, b) => {
  for (let i = 0; i < dims.length; i++) {
    const diff = ixOf[i](a[dims[i].key]) - ixOf[i](b[dims[i].key]);
    if (diff !== 0) return diff;
  }
  return 0;
});

// --- Column layout: a shared pixels-per-unit scale keeps a flow's ribbon the
// same height on both ends it touches, regardless of how many values share
// that column ----------------------------------------------------------------
function columnTotals(values, key) {
  return values.map((v) => ({
    value: v,
    total: flows.filter((f) => f[key] === v).reduce((s, f) => s + f.count, 0),
  }));
}
function rawKy(n) {
  return (ih - nodePadding * (n - 1)) / totalCount;
}
const ky = Math.min(...dims.map((d) => rawKy(d.values.length)));

function layoutColumn(values, key) {
  const items = columnTotals(values, key);
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

const xs = dims.map((_, i) => margin.left + (iw * i) / (dims.length - 1));
const dimNodes = dims.map((d) => layoutColumn(d.values, d.key));

// Stack every flow within each dimension's nodes, in the shared global order,
// recording the y-band it occupies at that dimension — reused as the link
// target on its left and the link source on its right.
for (let i = 0; i < dims.length; i++) {
  const key = dims[i].key;
  const cursor = new Map(dims[i].values.map((v) => [v, dimNodes[i].get(v).y0]));
  for (const f of flowOrder) {
    const v = f[key];
    const y0 = cursor.get(v);
    const y1 = y0 + f.count * ky;
    f.bandY0 = f.bandY0 || [];
    f.bandY1 = f.bandY1 || [];
    f.bandY0[i] = y0;
    f.bandY1[i] = y1;
    cursor.set(v, y1);
  }
}

// --- Ribbon shape: two cubic-bezier edges between a source band and a target
// band, filled as a single closed path ---------------------------------------
function ribbonPath(xa, xb, sy0, sy1, ty0, ty1) {
  const xm = (xa + xb) / 2;
  return `M${xa},${sy0}C${xm},${sy0} ${xm},${ty0} ${xb},${ty0}L${xb},${ty1}C${xm},${ty1} ${xm},${sy1} ${xa},${sy1}Z`;
}

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

const color = d3.scaleOrdinal().domain(dims[0].values).range(t.palette.slice(0, dims[0].values.length));

// Ribbons (drawn first, nodes sit on top of their edges). Largest flows first
// so the smaller, easier-to-lose ribbons draw on top at crossing points —
// combined with the higher opacity below this keeps multi-channel overlaps
// readable instead of blending into a muddy composite color.
const drawOrder = [...flows].sort((a, b) => b.count - a.count);
for (let i = 0; i < dims.length - 1; i++) {
  const xa = xs[i] + barWidth;
  const xb = xs[i + 1];
  svg
    .selectAll(`.ribbon-${i}`)
    .data(drawOrder)
    .join("path")
    .attr("d", (f) => ribbonPath(xa, xb, f.bandY0[i], f.bandY1[i], f.bandY0[i + 1], f.bandY1[i + 1]))
    .attr("fill", (f) => color(f.channel))
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 1)
    .attr("opacity", 0.82);
}

// Node bars: theme-adaptive neutral anchor — these represent structural
// totals, not a categorical series, so they stay ink-colored rather than
// pulling another Imprint hue.
for (let i = 0; i < dims.length; i++) {
  const dim = dims[i];
  const nodes = dimNodes[i];
  const isFirst = i === 0;
  const x = xs[i];

  svg
    .append("g")
    .selectAll("rect")
    .data(dim.values)
    .join("rect")
    .attr("x", x)
    .attr("y", (v) => nodes.get(v).y0)
    .attr("width", barWidth)
    .attr("height", (v) => nodes.get(v).y1 - nodes.get(v).y0)
    .attr("fill", t.ink);

  svg
    .append("g")
    .selectAll("text")
    .data(dim.values)
    .join("text")
    .attr("x", isFirst ? x - 14 : x + barWidth + 14)
    .attr("y", (v) => (nodes.get(v).y0 + nodes.get(v).y1) / 2)
    .attr("dy", "0.35em")
    .attr("text-anchor", isFirst ? "end" : "start")
    .style("font-size", "17px")
    .style("font-weight", isFirst ? "600" : "400")
    .style("paint-order", "stroke")
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 6)
    .attr("stroke-linejoin", "round")
    .attr("fill", isFirst ? (v) => color(v) : t.inkSoft)
    .text((v) => v);

  svg
    .append("text")
    .attr("x", x + barWidth / 2)
    .attr("y", margin.top - 34)
    .attr("text-anchor", "middle")
    .style("font-size", "15px")
    .style("font-weight", "600")
    .style("letter-spacing", "0.02em")
    .attr("fill", t.inkSoft)
    .text(dim.label.toUpperCase());
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
