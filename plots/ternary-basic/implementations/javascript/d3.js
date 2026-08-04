// anyplot.ai
// ternary-basic: Basic Ternary Plot
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: 80/100 | Created: 2026-08-04

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 210, right: 110, bottom: 110, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Soil samples: clay / sand / silt proportions (%), each triplet sums to 100.
function lcg(seed) {
  let s = seed;
  return () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    return s / 0x7fffffff;
  };
}
const rand = lcg(42123);
const samples = [];
for (let i = 0; i < 28; i++) {
  const wClay = 0.15 + rand() * 0.85;
  const wSand = 0.15 + rand() * 0.85;
  const wSilt = 0.15 + rand() * 0.85;
  const total = wClay + wSand + wSilt;
  samples.push({
    clay: (wClay / total) * 100,
    sand: (wSand / total) * 100,
    silt: (wSilt / total) * 100,
  });
}

// --- Triangle geometry --------------------------------------------------------
// Apex = clay, bottom-left = sand, bottom-right = silt (classic soil-texture layout).
const side = iw;
const triHeight = (side * Math.sqrt(3)) / 2;
const apex = { x: margin.left + side / 2, y: margin.top };
const left = { x: margin.left, y: margin.top + triHeight };
const right = { x: margin.left + side, y: margin.top + triHeight };
const centroid = {
  x: (apex.x + left.x + right.x) / 3,
  y: (apex.y + left.y + right.y) / 3,
};

// Barycentric (a=clay, b=sand, c=silt, each 0-1, a+b+c=1) -> pixel coordinates.
function toXY(a, b, c) {
  return {
    x: a * apex.x + b * left.x + c * right.x,
    y: a * apex.y + b * left.y + c * right.y,
  };
}
function outward(p, dist) {
  const dx = p.x - centroid.x;
  const dy = p.y - centroid.y;
  const len = Math.hypot(dx, dy) || 1;
  return { x: p.x + (dx / len) * dist, y: p.y + (dy / len) * dist };
}

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Grid lines (20% intervals, three families parallel to each edge) --------
const levels = [0.2, 0.4, 0.6, 0.8];
const gridSegments = [];
for (const lv of levels) {
  gridSegments.push([toXY(lv, 1 - lv, 0), toXY(lv, 0, 1 - lv)]); // parallel to base
  gridSegments.push([toXY(1 - lv, lv, 0), toXY(0, lv, 1 - lv)]); // parallel to apex-right
  gridSegments.push([toXY(1 - lv, 0, lv), toXY(0, 1 - lv, lv)]); // parallel to apex-left
}
svg
  .selectAll(".grid-line")
  .data(gridSegments)
  .join("line")
  .attr("class", "grid-line")
  .attr("x1", (d) => d[0].x)
  .attr("y1", (d) => d[0].y)
  .attr("x2", (d) => d[1].x)
  .attr("y2", (d) => d[1].y)
  .attr("stroke", t.grid)
  .attr("stroke-width", 1.5);

// --- Triangle border ------------------------------------------------------------
svg
  .append("path")
  .attr("d", `M${apex.x},${apex.y} L${left.x},${left.y} L${right.x},${right.y} Z`)
  .attr("fill", "none")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 2.5);

// --- Tick marks + labels (one axis per edge, 0-100 by 20%) -------------------
const tickLevels = [0, 0.2, 0.4, 0.6, 0.8, 1];
const ticks = [];
for (const lv of tickLevels) {
  ticks.push(toXY(lv, 1 - lv, 0)); // clay axis, edge apex-left
  ticks.push(toXY(1 - lv, 0, lv)); // silt axis, edge apex-right
  ticks.push(toXY(0, lv, 1 - lv)); // sand axis, edge base
}
for (const p of ticks) {
  const tickEnd = outward(p, 14);
  const labelPos = outward(p, 34);
  svg
    .append("line")
    .attr("x1", p.x)
    .attr("y1", p.y)
    .attr("x2", tickEnd.x)
    .attr("y2", tickEnd.y)
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1.5);
}
const tickLabels = [];
for (const lv of tickLevels) {
  tickLabels.push({ p: outward(toXY(lv, 1 - lv, 0), 34), text: Math.round(lv * 100) });
  tickLabels.push({ p: outward(toXY(1 - lv, 0, lv), 34), text: Math.round(lv * 100) });
  tickLabels.push({ p: outward(toXY(0, lv, 1 - lv), 34), text: Math.round(lv * 100) });
}
svg
  .selectAll(".tick-label")
  .data(tickLabels)
  .join("text")
  .attr("class", "tick-label")
  .attr("x", (d) => d.p.x)
  .attr("y", (d) => d.p.y)
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .style("font-family", "sans-serif")
  .text((d) => d.text);

// --- Vertex labels --------------------------------------------------------------
const vertexLabels = [
  { p: outward(apex, 78), text: "Clay" },
  { p: outward(left, 78), text: "Sand" },
  { p: outward(right, 78), text: "Silt" },
];
svg
  .selectAll(".vertex-label")
  .data(vertexLabels)
  .join("text")
  .attr("class", "vertex-label")
  .attr("x", (d) => d.p.x)
  .attr("y", (d) => d.p.y)
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "middle")
  .attr("fill", t.ink)
  .style("font-size", "20px")
  .style("font-weight", "600")
  .style("font-family", "sans-serif")
  .text((d) => d.text);

// --- Data points ------------------------------------------------------------
const points = samples.map((s) => toXY(s.clay / 100, s.sand / 100, s.silt / 100));
svg
  .selectAll(".sample")
  .data(points)
  .join("circle")
  .attr("class", "sample")
  .attr("cx", (d) => d.x)
  .attr("cy", (d) => d.y)
  .attr("r", 9)
  .attr("fill", t.palette[0])
  .attr("fill-opacity", 0.85)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .style("font-family", "sans-serif")
  .text("ternary-basic · javascript · d3 · anyplot.ai");
