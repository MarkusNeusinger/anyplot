// anyplot.ai
// bar-grouped: Grouped Bar Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 130, right: 260, bottom: 100, left: 130 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly revenue (in $M) for three product lines across four fiscal quarters.
const categories = ["Q1", "Q2", "Q3", "Q4"];
const groups = ["Hardware", "Software", "Services"];
const data = [
  { category: "Q1", group: "Hardware", value: 4.2 },
  { category: "Q1", group: "Software", value: 6.1 },
  { category: "Q1", group: "Services", value: 3.0 },
  { category: "Q2", group: "Hardware", value: 4.6 },
  { category: "Q2", group: "Software", value: 6.8 },
  { category: "Q2", group: "Services", value: 3.4 },
  { category: "Q3", group: "Hardware", value: 4.1 },
  { category: "Q3", group: "Software", value: 7.9 },
  { category: "Q3", group: "Services", value: 3.9 },
  { category: "Q4", group: "Hardware", value: 5.3 },
  { category: "Q4", group: "Software", value: 9.2 },
  { category: "Q4", group: "Services", value: 4.5 },
];

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales ---------------------------------------------------------------
const x0 = d3.scaleBand().domain(categories).range([0, iw]).paddingInner(0.3);
const x1 = d3.scaleBand().domain(groups).range([0, x0.bandwidth()]).padding(0.12);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(data, (d) => d.value)])
  .nice()
  .range([ih, 0]);
const color = d3.scaleOrdinal().domain(groups).range(t.palette);

// --- Gridlines (y-axis only) ------------------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .selectAll("line")
  .attr("stroke", t.grid);
g.select(".grid .domain").remove();

// --- Bars -------------------------------------------------------------------
const categoryGroups = g
  .selectAll(".category-group")
  .data(categories)
  .join("g")
  .attr("class", "category-group")
  .attr("transform", (d) => `translate(${x0(d)},0)`);

categoryGroups
  .selectAll("rect")
  .data((cat) => data.filter((d) => d.category === cat))
  .join("rect")
  .attr("x", (d) => x1(d.group))
  .attr("y", (d) => y(d.value))
  .attr("width", x1.bandwidth())
  .attr("height", (d) => ih - y(d.value))
  .attr("fill", (d) => color(d.group));

// --- Value labels -------------------------------------------------------------
categoryGroups
  .selectAll("text")
  .data((cat) => data.filter((d) => d.category === cat))
  .join("text")
  .attr("x", (d) => x1(d.group) + x1.bandwidth() / 2)
  .attr("y", (d) => y(d.value) - 12)
  .attr("text-anchor", "middle")
  .style("font-size", "13px")
  .attr("fill", t.inkSoft)
  .text((d) => d.value.toFixed(1));

// --- Axes -----------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x0));
const yAxis = g
  .append("g")
  .call(d3.axisLeft(y).tickFormat((d) => `$${d}M`));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}
xAxis.selectAll("line").remove();

// --- Axis labels ------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 66)
  .attr("text-anchor", "middle")
  .style("font-size", "18px")
  .attr("fill", t.ink)
  .text("Fiscal Quarter (2025)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -96)
  .attr("text-anchor", "middle")
  .style("font-size", "18px")
  .attr("fill", t.ink)
  .text("Revenue ($M)");

// --- Legend -------------------------------------------------------------------
const legend = svg
  .append("g")
  .attr("transform", `translate(${width - margin.right + 60},${margin.top + 20})`);

groups.forEach((group, i) => {
  const row = legend.append("g").attr("transform", `translate(0,${i * 40})`);
  row.append("rect").attr("width", 24).attr("height", 24).attr("fill", color(group));
  row
    .append("text")
    .attr("x", 36)
    .attr("y", 18)
    .style("font-size", "16px")
    .attr("fill", t.ink)
    .text(group);
});

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "19px")
  .style("font-weight", "600")
  .text("Product Line Revenue by Quarter · bar-grouped · javascript · d3 · anyplot.ai");
