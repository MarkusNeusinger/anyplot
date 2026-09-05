// anyplot.ai
// elbow-curve: Elbow Curve for K-Means Clustering
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 80, bottom: 100, left: 140 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// K-means inertia (within-cluster sum of squares) for customer segmentation
// on annual spend + purchase frequency, k = 1..10. The rate of decrease flattens
// sharply after k = 4 — the elbow point.
const kValues = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const inertia = [8450, 5120, 3210, 2050, 1780, 1590, 1440, 1330, 1240, 1170];
const elbowK = 4;

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales --------------------------------------------------------------------
const x = d3.scaleLinear().domain([1, 10]).range([0, iw]);
const y = d3.scaleLinear().domain([0, d3.max(inertia)]).nice().range([ih, 0]);

// --- Y-axis gridlines (subtle, no x-axis grid for a single-line chart) --------
g.append("g")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Axes ------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(10).tickFormat(d3.format("d")));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6).tickFormat(d3.format(",")));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Elbow guide line -----------------------------------------------------
g.append("line")
  .attr("x1", x(elbowK))
  .attr("x2", x(elbowK))
  .attr("y1", y(0))
  .attr("y2", y(inertia[elbowK - 1]))
  .attr("stroke", t.inkSoft)
  .attr("stroke-dasharray", "5,5")
  .attr("stroke-width", 1.5);

// --- Connecting line ---------------------------------------------------------
const line = d3
  .line()
  .x((d, i) => x(kValues[i]))
  .y((d) => y(d));
g.append("path").datum(inertia).attr("fill", "none").attr("stroke", t.palette[0]).attr("stroke-width", 3.5).attr("d", line);

// --- Markers, with the elbow point picked out in amber -----------------------
g.selectAll("circle")
  .data(inertia)
  .join("circle")
  .attr("cx", (d, i) => x(kValues[i]))
  .attr("cy", (d) => y(d))
  .attr("r", (d, i) => (kValues[i] === elbowK ? 11 : 7))
  .attr("fill", (d, i) => (kValues[i] === elbowK ? t.amber : t.palette[0]))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2);

// --- Elbow annotation (spec explicitly calls for highlighting the optimal k) --
g.append("text")
  .attr("x", x(elbowK) + 16)
  .attr("y", y(inertia[elbowK - 1]) - 16)
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .style("font-weight", "600")
  .text(`Optimal k = ${elbowK}`);

// --- Axis labels -------------------------------------------------------------
svg
  .append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", height - 28)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Number of Clusters (k)");

svg
  .append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -(margin.top + ih / 2))
  .attr("y", 40)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Inertia (Within-Cluster Sum of Squares)");

// --- Title -------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("elbow-curve · javascript · d3 · anyplot.ai");
