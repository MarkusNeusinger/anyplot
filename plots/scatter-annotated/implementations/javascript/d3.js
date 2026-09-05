// anyplot.ai
// scatter-annotated: Annotated Scatter Plot with Text Labels
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

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
  ax.select(".domain").attr("stroke", t.inkSoft);
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
const points = data.map((d) => ({ ...d, px: x(d.x), py: y(d.y) }));

// --- Points -------------------------------------------------------------
g.selectAll(".point")
  .data(points)
  .join("circle")
  .attr("class", "point")
  .attr("cx", (d) => d.px)
  .attr("cy", (d) => d.py)
  .attr("r", markerRadius)
  .attr("fill", t.palette[0])
  .attr("fill-opacity", 0.7)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

// --- Greedy label placement (a hand-rolled adjustText equivalent) ---------
// D3 has no adjustText port, but the render harness runs in a real browser,
// so text width is measured with actual SVG layout (getBBox) rather than
// estimated — jsdom can't do this, a headless Chromium can.
const measure = svg.append("text").attr("opacity", 0).style("font-size", "13px").style("font-family", "sans-serif");
const labelWidth = new Map(points.map((d) => {
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
  x0: d.px - markerRadius - pad, y0: d.py - markerRadius - pad,
  x1: d.px + markerRadius + pad, y1: d.py + markerRadius + pad,
}));

const placedBoxes = [];
const placed = points.map((d, i) => {
  const w = labelWidth.get(d.label);
  let chosen = null;
  outer: for (const r of radii) {
    for (const dir of compass) {
      const box = labelBox(d.px, d.py, dir, r, w, labelHeight);
      const hitsMarker = markerBoxes.some((m, j) => j !== i && overlaps(box, m));
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
  .attr("x1", (d) => d.px + d.dir.dx * (markerRadius + 3))
  .attr("y1", (d) => d.py + d.dir.dy * (markerRadius + 3))
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
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
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
