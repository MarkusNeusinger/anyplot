// anyplot.ai
// scatter-3d: 3D Scatter Plot
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-10

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data: customer segments across three RFM behavioral dimensions --------
// (Recency, Frequency, Monetary — a classic feature space for spotting
// customer clusters in retention/marketing analysis.)
function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let x = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}
const random = mulberry32(42);
function gaussian() {
  const u1 = Math.max(random(), 1e-9);
  const u2 = random();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const segments = [
  { name: "Champions", n: 60, recency: [12, 4], frequency: [20, 3], monetary: [190, 25] },
  { name: "At Risk", n: 60, recency: [150, 22], frequency: [4, 1.4], monetary: [85, 15] },
  { name: "New Customers", n: 60, recency: [32, 9], frequency: [3, 1], monetary: [55, 12] },
];

const points = [];
segments.forEach((seg, segIndex) => {
  for (let i = 0; i < seg.n; i++) {
    points.push({
      segment: seg.name,
      segIndex,
      recency: Math.max(1, seg.recency[0] + gaussian() * seg.recency[1]),
      frequency: Math.max(0.5, seg.frequency[0] + gaussian() * seg.frequency[1]),
      monetary: Math.max(10, seg.monetary[0] + gaussian() * seg.monetary[1]),
    });
  }
});

// --- Normalize each axis into a [-1, 1] cube for the 3D projection ---------
const normX = d3.scaleLinear().domain(d3.extent(points, (d) => d.recency)).range([-1, 1]);
const normY = d3.scaleLinear().domain(d3.extent(points, (d) => d.frequency)).range([-1, 1]);
const normZ = d3.scaleLinear().domain(d3.extent(points, (d) => d.monetary)).range([-1, 1]);

// --- Axonometric projection: fixed camera angle, no interactive rotation ---
// (D3 has no native 3D scene graph — this rotates the normalized cube with a
// standard yaw/pitch rotation matrix and keeps the post-rotation z as a depth
// value for painter's-algorithm ordering and near/far size + opacity cueing.)
const yaw = (-32 * Math.PI) / 180;
const pitch = (18 * Math.PI) / 180;

function project(x, y, z) {
  const x1 = x * Math.cos(yaw) + z * Math.sin(yaw);
  const z1 = -x * Math.sin(yaw) + z * Math.cos(yaw);
  const y2 = y * Math.cos(pitch) - z1 * Math.sin(pitch);
  const z2 = y * Math.sin(pitch) + z1 * Math.cos(pitch);
  return { sx: x1, sy: y2, depth: z2 };
}

// Frame the view from the 8 cube corners so the projection is data-independent.
const corners = [];
for (const cx of [-1, 1]) for (const cy of [-1, 1]) for (const cz of [-1, 1]) corners.push(project(cx, cy, cz));

const margin = { top: 110, right: 260, bottom: 90, left: 90 };
const screenX = d3.scaleLinear().domain(d3.extent(corners, (c) => c.sx)).range([margin.left, width - margin.right]);
const screenY = d3.scaleLinear().domain(d3.extent(corners, (c) => c.sy)).range([height - margin.bottom, margin.top]);

const projected = points.map((d) => ({ ...d, ...project(normX(d.recency), normY(d.frequency), normZ(d.monetary)) }));
const depthExtent = d3.extent(projected, (d) => d.depth);
const radiusScale = d3.scaleLinear().domain(depthExtent).range([6, 11]);
const opacityScale = d3.scaleLinear().domain(depthExtent).range([0.55, 0.92]);

const color = d3.scaleOrdinal().domain(segments.map((s) => s.name)).range(t.palette);

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- 3D axes: three edges from the cube's front-bottom-left corner ---------
const axes = [
  { label: "Recency (days)", from: [-1, -1, -1], to: [1, -1, -1], scale: normX, format: d3.format(".0f") },
  { label: "Frequency (orders/yr)", from: [-1, -1, -1], to: [-1, 1, -1], scale: normY, format: d3.format(".0f") },
  { label: "Monetary ($ avg order)", from: [-1, -1, -1], to: [-1, -1, 1], scale: normZ, format: (v) => `$${d3.format(".0f")(v)}` },
];

const axisGroup = svg.append("g");
axes.forEach((axis) => {
  const p0 = project(...axis.from);
  const p1 = project(...axis.to);
  axisGroup
    .append("line")
    .attr("x1", screenX(p0.sx))
    .attr("y1", screenY(p0.sy))
    .attr("x2", screenX(p1.sx))
    .attr("y2", screenY(p1.sy))
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1.5);

  axis.scale.ticks(4).forEach((value) => {
    const tPos = axis.scale(value);
    const point = axis.from.map((v, i) => (axis.to[i] !== v ? tPos : v));
    const pr = project(...point);
    axisGroup
      .append("circle")
      .attr("cx", screenX(pr.sx))
      .attr("cy", screenY(pr.sy))
      .attr("r", 2.5)
      .attr("fill", t.grid);
    axisGroup
      .append("text")
      .attr("x", screenX(pr.sx))
      .attr("y", screenY(pr.sy) + 18)
      .attr("text-anchor", "middle")
      .attr("fill", t.inkSoft)
      .style("font-size", "13px")
      .text(axis.format(value));
  });

  const pEnd = project(...axis.to);
  axisGroup
    .append("text")
    .attr("x", screenX(pEnd.sx))
    .attr("y", screenY(pEnd.sy) - 14)
    .attr("text-anchor", "middle")
    .attr("fill", t.ink)
    .style("font-size", "15px")
    .style("font-weight", "600")
    .text(axis.label);
});

// --- Scatter points, painter's algorithm (far to near) ----------------------
svg
  .append("g")
  .selectAll("circle.point")
  .data([...projected].sort((a, b) => a.depth - b.depth))
  .join("circle")
  .attr("class", "point")
  .attr("cx", (d) => screenX(d.sx))
  .attr("cy", (d) => screenY(d.sy))
  .attr("r", (d) => radiusScale(d.depth))
  .attr("fill", (d) => color(d.segment))
  .attr("fill-opacity", (d) => opacityScale(d.depth))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 0.75);

// --- Legend -------------------------------------------------------------------
const legend = svg.append("g").attr("transform", `translate(${width - margin.right + 40}, ${margin.top + 30})`);
segments.forEach((seg, i) => {
  const row = legend.append("g").attr("transform", `translate(0, ${i * 34})`);
  row.append("circle").attr("r", 8).attr("cx", 8).attr("cy", 0).attr("fill", color(seg.name));
  row.append("text").attr("x", 24).attr("y", 5).attr("fill", t.ink).style("font-size", "15px").text(seg.name);
});

// --- Title --------------------------------------------------------------------
const titleText = "Customer Segments in 3D Feature Space · scatter-3d · javascript · d3 · anyplot.ai";
const titleFontSize = Math.max(15, Math.round(22 * Math.min(1, 67 / titleText.length)));
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 46)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(titleText);
