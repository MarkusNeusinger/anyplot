// anyplot.ai
// scatter-annotated: Annotated Scatter Plot with Text Labels
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 90, bottom: 100, left: 120 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Deterministic PRNG (tiny LCG — Math.random() is not reproducible) -----
let seed = 42;
function rand() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

// --- Data: R&D spend vs. annual revenue for fictional tech companies -------
const companies = [
  "Nimbus Labs", "Cascade Systems", "Vertex Dynamics", "Solstice Tech",
  "Ironwood Analytics", "Beacon Robotics", "Quartz Networks", "Halcyon AI",
  "Meridian Software", "Driftwood Data", "Lumen Photonics", "Argent Cloud",
  "Tidewater Semiconductors", "Cobalt Interactive", "Palisade Security",
  "Everline Biotech", "Fernwood Materials", "Aurora Aerospace",
];

const data = companies.map((label) => {
  const rdSpend = 18 + rand() * 380;
  const revenue = Math.max(35, rdSpend * (2.6 + rand() * 4.4) + (rand() - 0.5) * 300);
  return { label, x: rdSpend, y: revenue };
});

// --- Scales -------------------------------------------------------------
const x = d3.scaleLinear().domain(d3.extent(data, (d) => d.x)).nice().range([0, iw]);
const y = d3.scaleLinear().domain([0, d3.max(data, (d) => d.y)]).nice().range([ih, 0]);

// --- SVG mount ------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Gridlines (both axes, per scatter convention) -------------------------
g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(8).tickSize(-ih).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

g.append("g")
  .call(d3.axisLeft(y).ticks(7).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Axes -------------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(8));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(7));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px").style("font-family", "sans-serif");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").remove();
}

// --- Axis labels --------------------------------------------------------
svg.append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", height - 30)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .style("font-family", "sans-serif")
  .text("R&D Spending ($M)");

svg.append("text")
  .attr("transform", `translate(${36},${margin.top + ih / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .style("font-family", "sans-serif")
  .text("Annual Revenue ($M)");

// --- Marker + label layout --------------------------------------------------
const markerRadius = 10;

// --- Trend-relative highlight: which company earns the most revenue per
// R&D dollar (the story's focal point), and which points are worth naming --
const n = data.length;
const sumX = d3.sum(data, (d) => d.x);
const sumY = d3.sum(data, (d) => d.y);
const sumXY = d3.sum(data, (d) => d.x * d.y);
const sumXX = d3.sum(data, (d) => d.x * d.x);
const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
const intercept = (sumY - slope * sumX) / n;
const withResidual = data.map((d) => ({ ...d, residual: d.y - (slope * d.x + intercept) }));
const standout = withResidual.reduce((a, b) => (b.residual > a.residual ? b : a));

// Label only the notable subset — biggest over/under-performers relative to
// the trend, plus the R&D and revenue extremes — per the spec's guidance to
// annotate a subset rather than every point once the dataset gets dense.
const maxX = d3.max(data, (d) => d.x);
const maxY = d3.max(data, (d) => d.y);
const keyLabels = new Set(
  [...withResidual]
    .sort((a, b) => Math.abs(b.residual) - Math.abs(a.residual))
    .slice(0, 8)
    .map((d) => d.label)
);
keyLabels.add(standout.label);
for (const d of data) if (d.x === maxX || d.y === maxY) keyLabels.add(d.label);

// The trend-beating standout renders larger and at full opacity to act as a
// focal point; the rest stay uniform to keep the density-driven alpha~0.7.
const points = data.map((d) => ({
  ...d,
  px: x(d.x),
  py: y(d.y),
  r: d.label === standout.label ? markerRadius + 5 : markerRadius,
}));

// --- Points ---------------------------------------------------------------
g.selectAll(".point")
  .data(points)
  .join("circle")
  .attr("class", "point")
  .attr("cx", (d) => d.px)
  .attr("cy", (d) => d.py)
  .attr("r", (d) => d.r)
  .attr("fill", t.palette[0])
  .attr("fill-opacity", (d) => (d.label === standout.label ? 1 : 0.7))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", (d) => (d.label === standout.label ? 2.5 : 1.5));

// --- Greedy label placement (a hand-rolled adjustText equivalent) ---------
// D3 has no adjustText port, but the render harness runs in a real browser,
// so text width is measured with actual SVG layout (getBBox) rather than
// estimated — jsdom can't do this, a headless Chromium can.
const labeledPoints = points.filter((d) => keyLabels.has(d.label));
const measure = svg.append("text").attr("opacity", 0).style("font-size", "13px").style("font-family", "sans-serif");
const labelWidth = new Map(labeledPoints.map((d) => {
  measure.text(d.label);
  return [d.label, measure.node().getBBox().width];
}));
measure.remove();
const labelHeight = 15;

const compass = [
  { dx: 1, dy: -1 }, { dx: 0, dy: -1 }, { dx: 1, dy: 0 }, { dx: -1, dy: -1 },
  { dx: 1, dy: 1 }, { dx: -1, dy: 0 }, { dx: 0, dy: 1 }, { dx: -1, dy: 1 },
];
const radii = [28, 42, 58, 76, 96];
const pad = 5;

function labelBox(px, py, dir, r, w, h) {
  const anchorX = px + dir.dx * r;
  const anchorY = py + dir.dy * r;
  const x0 = dir.dx > 0 ? anchorX : dir.dx < 0 ? anchorX - w : anchorX - w / 2;
  const y0 = dir.dy > 0 ? anchorY - h * 0.2 : dir.dy < 0 ? anchorY - h * 0.9 : anchorY - h / 2;
  return { x0, y0, x1: x0 + w, y1: y0 + h, anchorX, anchorY };
}

function overlaps(a, b) {
  return a.x0 < b.x1 + pad && a.x1 + pad > b.x0 && a.y0 < b.y1 + pad && a.y1 + pad > b.y0;
}

const markerBoxes = points.map((d) => ({
  label: d.label,
  x0: d.px - d.r - pad, y0: d.py - d.r - pad,
  x1: d.px + d.r + pad, y1: d.py + d.r + pad,
}));

const placedBoxes = [];
const placed = labeledPoints.map((d) => {
  const w = labelWidth.get(d.label);
  let chosen = null;
  outer: for (const r of radii) {
    for (const dir of compass) {
      const box = labelBox(d.px, d.py, dir, r, w, labelHeight);
      const hitsMarker = markerBoxes.some((m) => m.label !== d.label && overlaps(box, m));
      const hitsLabel = placedBoxes.some((p) => overlaps(box, p));
      if (!hitsMarker && !hitsLabel) {
        chosen = { box, dir, r };
        break outer;
      }
    }
  }
  if (!chosen) chosen = { box: labelBox(d.px, d.py, compass[0], radii[radii.length - 1], w, labelHeight), dir: compass[0], r: radii[radii.length - 1] };
  placedBoxes.push(chosen.box);
  return {
    ...d,
    dir: chosen.dir,
    anchorX: chosen.box.anchorX,
    anchorY: chosen.box.anchorY,
    textAnchor: chosen.dir.dx > 0 ? "start" : chosen.dir.dx < 0 ? "end" : "middle",
    baseline: chosen.dir.dy > 0 ? "hanging" : chosen.dir.dy < 0 ? "auto" : "middle",
  };
});

// --- Leader lines (subtle, connecting offset labels back to their point) ---
g.selectAll(".leader")
  .data(placed)
  .join("line")
  .attr("class", "leader")
  .attr("x1", (d) => d.px + d.dir.dx * (d.r + 3))
  .attr("y1", (d) => d.py + d.dir.dy * (d.r + 3))
  .attr("x2", (d) => d.anchorX - d.dir.dx * 5)
  .attr("y2", (d) => d.anchorY - d.dir.dy * 5)
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1)
  .attr("opacity", 0.5);

// --- Labels -------------------------------------------------------------
g.selectAll(".label")
  .data(placed)
  .join("text")
  .attr("class", "label")
  .attr("x", (d) => d.anchorX)
  .attr("y", (d) => d.anchorY)
  .attr("text-anchor", (d) => d.textAnchor)
  .attr("dominant-baseline", (d) => d.baseline)
  .attr("fill", (d) => (d.label === standout.label ? t.ink : t.inkSoft))
  .style("font-size", "13px")
  .style("font-weight", (d) => (d.label === standout.label ? "600" : "400"))
  .style("font-family", "sans-serif")
  .text((d) => d.label);

// --- Title ------------------------------------------------------------------
svg.append("text")
  .attr("x", width / 2)
  .attr("y", 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .style("font-family", "sans-serif")
  .text("scatter-annotated · javascript · d3 · anyplot.ai");
