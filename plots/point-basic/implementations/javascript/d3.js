// anyplot.ai
// point-basic: Point Estimate Plot
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 90, bottom: 80, left: 220 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: customer satisfaction survey, mean score (1-10) with 95% CI -----
const data = [
  { category: "Checkout Flow", estimate: 8.4, lower: 8.0, upper: 8.8 },
  { category: "Search Relevance", estimate: 7.6, lower: 7.1, upper: 8.1 },
  { category: "Delivery Speed", estimate: 6.9, lower: 6.3, upper: 7.5 },
  { category: "Mobile App", estimate: 7.2, lower: 6.8, upper: 7.6 },
  { category: "Customer Support", estimate: 8.1, lower: 7.6, upper: 8.6 },
  { category: "Product Packaging", estimate: 6.3, lower: 5.6, upper: 7.0 },
  { category: "Return Process", estimate: 5.8, lower: 5.1, upper: 6.5 },
];

// sort descending by estimate so the eye reads a clean ranking top to bottom
data.sort((a, b) => b.estimate - a.estimate);

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales --------------------------------------------------------------
const x = d3.scaleLinear().domain([0, 10]).nice().range([0, iw]);
const y = d3
  .scaleBand()
  .domain(data.map((d) => d.category))
  .range([0, ih])
  .padding(0.4);

// --- Gridlines (x-axis only, subtle) ---------------------------------------
g.append("g")
  .attr("class", "grid")
  .selectAll("line")
  .data(x.ticks(6))
  .join("line")
  .attr("x1", (d) => x(d))
  .attr("x2", (d) => x(d))
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- Axes ------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(6).tickSize(0).tickPadding(14));
const yAxis = g.append("g").call(d3.axisLeft(y).tickSize(0).tickPadding(16));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  ax.select(".domain").attr("stroke", t.inkSoft);
}
yAxis.select(".domain").remove();

// --- Axis labels -------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Mean Satisfaction Score (1–10 scale)");

// --- Confidence interval whiskers + caps ------------------------------------
const rows = g
  .selectAll(".row")
  .data(data)
  .join("g")
  .attr("class", "row")
  .attr("transform", (d) => `translate(0,${y(d.category) + y.bandwidth() / 2})`);

const capHalf = 9;

rows
  .append("line")
  .attr("x1", (d) => x(d.lower))
  .attr("x2", (d) => x(d.upper))
  .attr("y1", 0)
  .attr("y2", 0)
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 2.5);

rows
  .append("line")
  .attr("x1", (d) => x(d.lower))
  .attr("x2", (d) => x(d.lower))
  .attr("y1", -capHalf)
  .attr("y2", capHalf)
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 2.5);

rows
  .append("line")
  .attr("x1", (d) => x(d.upper))
  .attr("x2", (d) => x(d.upper))
  .attr("y1", -capHalf)
  .attr("y2", capHalf)
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 2.5);

// --- Point estimates ---------------------------------------------------------
rows
  .append("circle")
  .attr("cx", (d) => x(d.estimate))
  .attr("cy", 0)
  .attr("r", 10)
  .attr("fill", t.palette[0])
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2);

// --- Title -------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("point-basic · javascript · d3 · anyplot.ai");
