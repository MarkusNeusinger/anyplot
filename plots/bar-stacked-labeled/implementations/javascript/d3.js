// anyplot.ai
// bar-stacked-labeled: Stacked Bar Chart with Total Labels
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 150, right: 50, bottom: 90, left: 120 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: quarterly revenue by product line, in $M ------------------------
const components = ["Hardware", "Software", "Services"];
const data = [
  { quarter: "Q1", Hardware: 42, Software: 28, Services: 15 },
  { quarter: "Q2", Hardware: 38, Software: 34, Services: 19 },
  { quarter: "Q3", Hardware: 45, Software: 39, Services: 22 },
  { quarter: "Q4", Hardware: 51, Software: 46, Services: 27 },
];
const totals = data.map((d) =>
  components.reduce((sum, key) => sum + d[key], 0),
);

// --- SVG mount ---------------------------------------------------------------
const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);
const g = svg
  .append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const x = d3
  .scaleBand()
  .domain(data.map((d) => d.quarter))
  .range([0, iw])
  .padding(0.35);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(totals) * 1.15])
  .nice()
  .range([ih, 0]);
const color = d3
  .scaleOrdinal()
  .domain(components)
  .range(t.palette.slice(0, components.length));

// --- Y grid (subtle, y-axis only) --------------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Stacked bars ---------------------------------------------------------
const series = d3.stack().keys(components)(data);

const segments = g
  .append("g")
  .selectAll("g")
  .data(series)
  .join("g")
  .attr("fill", (d) => color(d.key));

segments
  .selectAll("rect")
  .data((d) => d)
  .join("rect")
  .attr("x", (d) => x(d.data.quarter))
  .attr("y", (d) => y(d[1]))
  .attr("width", x.bandwidth())
  .attr("height", (d) => y(d[0]) - y(d[1]));

// --- In-segment value labels (distinct from the total labels above) ----------
const MIN_LABEL_SEGMENT_HEIGHT = 46;
segments
  .selectAll(".segment-label")
  .data((d) => d.filter((v) => y(v[0]) - y(v[1]) >= MIN_LABEL_SEGMENT_HEIGHT))
  .join("text")
  .attr("class", "segment-label")
  .attr("x", (d) => x(d.data.quarter) + x.bandwidth() / 2)
  .attr("y", (d) => (y(d[0]) + y(d[1])) / 2)
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "central")
  .style("font-size", "15px")
  .style("font-weight", "600")
  .style("paint-order", "stroke")
  .attr("stroke", "rgba(0,0,0,0.35)")
  .attr("stroke-width", 3)
  .attr("fill", "#FFFFFF")
  .text((d) => `$${d[1] - d[0]}M`);

// --- Total labels above each stack -------------------------------------------
g.selectAll(".total-label")
  .data(data)
  .join("text")
  .attr("class", "total-label")
  .attr("x", (d) => x(d.quarter) + x.bandwidth() / 2)
  .attr("y", (d, i) => y(totals[i]) - 16)
  .attr("text-anchor", "middle")
  .style("font-size", "20px")
  .style("font-weight", "700")
  .attr("fill", t.ink)
  .text((d, i) => `$${totals[i]}M`);

// --- Axes ---------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x));
const yAxis = g.append("g").call(
  d3
    .axisLeft(y)
    .ticks(5)
    .tickFormat((d) => `$${d}M`),
);
for (const axis of [xAxis, yAxis]) {
  axis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  axis.selectAll("line").attr("stroke", t.inkSoft);
  axis.select(".domain").attr("stroke", t.inkSoft);
}

g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 64)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Quarter");

g.append("text")
  .attr("transform", `translate(${-88},${ih / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Revenue ($M)");

// --- Legend --------------------------------------------------------------
const legendItemWidth = 170;
const legend = svg
  .append("g")
  .attr(
    "transform",
    `translate(${width - margin.right - components.length * legendItemWidth}, 78)`,
  );

const legendItem = legend
  .selectAll("g")
  .data(components)
  .join("g")
  .attr("transform", (d, i) => `translate(${i * legendItemWidth},0)`);

legendItem
  .append("rect")
  .attr("width", 20)
  .attr("height", 20)
  .attr("y", -15)
  .attr("fill", (d) => color(d));

legendItem
  .append("text")
  .attr("x", 28)
  .attr("y", 0)
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text((d) => d);

// --- Title ---------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("bar-stacked-labeled · javascript · d3 · anyplot.ai");
