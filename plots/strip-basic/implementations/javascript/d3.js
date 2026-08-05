// anyplot.ai
// strip-basic: Basic Strip Plot
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: 82/100 | Created: 2026-08-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic LCG) ------------------------------------
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function randNormal(mean, std) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

const batches = [
  { name: "Batch 1", mean: 12.0, std: 0.04 },
  { name: "Batch 2", mean: 12.02, std: 0.05 },
  { name: "Batch 3", mean: 11.97, std: 0.09 },
  { name: "Batch 4", mean: 12.01, std: 0.03 },
];
const pointsPerBatch = 60;
const data = [];
for (const b of batches) {
  for (let i = 0; i < pointsPerBatch; i++) {
    data.push({ category: b.name, value: randNormal(b.mean, b.std) });
  }
}

// --- Layout -------------------------------------------------------------
const margin = { top: 120, right: 60, bottom: 110, left: 130 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- SVG mount ------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -----------------------------------------------------------------
const x = d3
  .scaleBand()
  .domain(batches.map((b) => b.name))
  .range([0, iw])
  .padding(0.4);
const y = d3
  .scaleLinear()
  .domain(d3.extent(data, (d) => d.value))
  .nice()
  .range([ih, 0]);
const color = d3
  .scaleOrdinal()
  .domain(batches.map((b) => b.name))
  .range(t.palette);

// --- Gridlines (y-axis only, scatter-style plot) -----------------------------
const grid = g.append("g").attr("class", "grid").call(d3.axisLeft(y).tickSize(-iw).tickFormat(""));
grid.select(".domain").remove();
grid.selectAll("line").attr("stroke", t.grid);

// --- Axes -------------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).tickSizeOuter(0));
const yAxis = g.append("g").call(d3.axisLeft(y).tickFormat(d3.format(".2f")).tickSizeOuter(0));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}
g.selectAll(".tick line").attr("stroke", t.inkSoft);
grid.selectAll(".tick line").attr("stroke", t.grid);

// --- Jittered strip points (D3 force-simulation beeswarm) --------------------
// True values stay pinned on y (fy); a collision + centering force resolves x
// so points spread just enough to avoid overlap, instead of plain uniform jitter.
const xCenter = (name) => x(name) + x.bandwidth() / 2;
const jitterWidth = x.bandwidth() * 0.6;
const pointRadius = 4;

const nodes = data.map((d) => ({
  ...d,
  x: xCenter(d.category) + (rand() - 0.5) * jitterWidth,
  y: y(d.value),
  fy: y(d.value),
}));

d3.forceSimulation(nodes)
  .force("x", d3.forceX((d) => xCenter(d.category)).strength(0.08))
  .force("collide", d3.forceCollide(pointRadius + 0.6))
  .stop()
  .tick(150);

for (const n of nodes) {
  const lo = xCenter(n.category) - jitterWidth / 2;
  const hi = xCenter(n.category) + jitterWidth / 2;
  n.x = Math.min(hi, Math.max(lo, n.x));
}

g.selectAll("circle")
  .data(nodes)
  .join("circle")
  .attr("cx", (d) => d.x)
  .attr("cy", (d) => d.y)
  .attr("r", pointRadius)
  .attr("fill", (d) => color(d.category))
  .attr("fill-opacity", 0.55)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 0.5);

// --- Mean reference lines (data storytelling: highlights Batch 3's shift) ----
for (const b of batches) {
  const mean = d3.mean(data, (d) => (d.category === b.name ? d.value : undefined));
  g.append("line")
    .attr("x1", x(b.name) + x.bandwidth() * 0.08)
    .attr("x2", x(b.name) + x.bandwidth() * 0.92)
    .attr("y1", y(mean))
    .attr("y2", y(mean))
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 2)
    .attr("stroke-dasharray", "6,4")
    .attr("opacity", 0.85);
}

g.append("text")
  .attr("x", 0)
  .attr("y", -14)
  .attr("text-anchor", "start")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .style("font-style", "italic")
  .text("Dashed line = batch mean");

// --- Axis labels --------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 70)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Production Batch");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -90)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Shaft Diameter (mm)");

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("strip-basic · javascript · d3 · anyplot.ai");
