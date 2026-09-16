// anyplot.ai
// silhouette-basic: Silhouette Plot
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-09

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 230, bottom: 100, left: 70 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: silhouette scores for a k-means clustering of the iris dataset --
// (fixed-seed LCG in place of a seeded RNG, which the browser lacks)
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
function clip(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

const clusterSpecs = [
  { label: "Cluster 0 · setosa", count: 50, mean: 0.8, std: 0.07 },
  { label: "Cluster 1 · versicolor", count: 47, mean: 0.42, std: 0.2 },
  { label: "Cluster 2 · virginica", count: 53, mean: 0.33, std: 0.22 },
];

const clusters = clusterSpecs.map((spec, i) => {
  const values = Array.from({ length: spec.count }, () =>
    clip(randNormal(spec.mean, spec.std), -1, 1),
  );
  values.sort((a, b) => b - a);
  return { ...spec, index: i, values, avg: d3.mean(values) };
});

const allValues = clusters.flatMap((c) => c.values);
const overallAvg = d3.mean(allValues);

// --- Sample-space row layout (one thin bar per sample, gap between clusters)
const GAP = 10;
let cursor = 0;
const rows = [];
for (const cluster of clusters) {
  const start = cursor;
  cluster.values.forEach((val, i) =>
    rows.push({ y0: cursor + i, y1: cursor + i + 1, val, cluster }),
  );
  cursor += cluster.values.length;
  cluster.mid = (start + cursor) / 2;
  cursor += GAP;
}
const ySpaceMax = cursor - GAP;

// --- Scales -------------------------------------------------------------
const xMin = Math.min(-0.1, d3.min(allValues) - 0.02);
const x = d3.scaleLinear().domain([xMin, 1]).nice().range([0, iw]);
const y = d3.scaleLinear().domain([0, ySpaceMax]).range([0, ih]);

// --- SVG mount ------------------------------------------------------------
const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);
const g = svg
  .append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// --- Gridlines (value axis) -------------------------------------------------
g.selectAll(".grid-line")
  .data(x.ticks(6))
  .join("line")
  .attr("class", "grid-line")
  .attr("x1", (d) => x(d))
  .attr("x2", (d) => x(d))
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.grid);

// --- Zero-reference line -----------------------------------------------------
g.append("line")
  .attr("x1", x(0))
  .attr("x2", x(0))
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1);

// --- Per-sample silhouette bars ---------------------------------------------
g.selectAll("rect")
  .data(rows)
  .join("rect")
  .attr("x", (d) => x(Math.min(0, d.val)))
  .attr("width", (d) => Math.abs(x(d.val) - x(0)))
  .attr("y", (d) => y(d.y0))
  .attr("height", (d) => y(d.y1) - y(d.y0) + 0.5)
  .attr("shape-rendering", "crispEdges")
  .attr("fill", (d) => t.palette[d.cluster.index]);

// --- Overall average reference line -----------------------------------------
g.append("line")
  .attr("x1", x(overallAvg))
  .attr("x2", x(overallAvg))
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.ink)
  .attr("stroke-width", 2)
  .attr("stroke-dasharray", "6,5");

g.append("text")
  .attr("x", x(overallAvg) + 10)
  .attr("y", -18)
  .attr("fill", t.ink)
  .style("font-size", "15px")
  .style("font-weight", "600")
  .text(`Overall avg = ${overallAvg.toFixed(2)}`);

// --- X axis -------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(6));
xAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
xAxis.selectAll("line").attr("stroke", t.grid);
xAxis.select(".domain").attr("stroke", t.inkSoft);

svg
  .append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", height - 28)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Silhouette Coefficient");

// --- Cluster legend + per-cluster average annotation ------------------------
const clusterLabel = g
  .selectAll(".cluster-label")
  .data(clusters)
  .join("g")
  .attr("class", "cluster-label")
  .attr("transform", (d) => `translate(${iw + 24},${y(d.mid)})`);

clusterLabel
  .append("rect")
  .attr("x", 0)
  .attr("y", -9)
  .attr("width", 16)
  .attr("height", 16)
  .attr("rx", 3)
  .attr("fill", (d) => t.palette[d.index]);

clusterLabel
  .append("text")
  .attr("x", 24)
  .attr("y", -1)
  .attr("dy", "0.35em")
  .attr("fill", t.ink)
  .style("font-size", "15px")
  .style("font-weight", "600")
  .text((d) => d.label);

clusterLabel
  .append("text")
  .attr("x", 24)
  .attr("y", 20)
  .attr("dy", "0.35em")
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .text((d) => `avg = ${d.avg.toFixed(2)}`);

// --- Title --------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("silhouette-basic · javascript · d3 · anyplot.ai");
