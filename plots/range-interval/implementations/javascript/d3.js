// anyplot.ai
// range-interval: Range Interval Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 70, bottom: 90, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: monthly temperature range for a temperate city (deg C) ----------
const months = [
  { label: "Jan", min: 0, max: 4, mean: 2.1 },
  { label: "Feb", min: 1, max: 6, mean: 3.3 },
  { label: "Mar", min: 4, max: 11, mean: 7.2 },
  { label: "Apr", min: 8, max: 16, mean: 11.9 },
  { label: "May", min: 12, max: 20, mean: 15.8 },
  { label: "Jun", min: 15, max: 23, mean: 18.7 },
  { label: "Jul", min: 17, max: 25, mean: 20.9 },
  { label: "Aug", min: 17, max: 25, mean: 20.6 },
  { label: "Sep", min: 13, max: 20, mean: 16.1 },
  { label: "Oct", min: 8, max: 14, mean: 10.8 },
  { label: "Nov", min: 4, max: 8, mean: 5.9 },
  { label: "Dec", min: 1, max: 5, mean: 2.7 },
];

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const x = d3.scaleBand().domain(months.map((d) => d.label)).range([0, iw]).padding(0.35);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(months, (d) => d.max)])
  .nice()
  .range([ih, 0]);

// --- Gridlines (y only) --------------------------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Range bars -----------------------------------------------------------------
g.selectAll("rect.range")
  .data(months)
  .join("rect")
  .attr("class", "range")
  .attr("x", (d) => x(d.label))
  .attr("width", x.bandwidth())
  .attr("y", (d) => y(d.max))
  .attr("height", (d) => y(d.min) - y(d.max))
  .attr("rx", 4)
  .attr("fill", t.palette[0])
  .attr("fill-opacity", 0.55)
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 1.5);

// --- Endpoint markers (min / max emphasis) --------------------------------------
for (const key of ["min", "max"]) {
  g.selectAll(`circle.${key}`)
    .data(months)
    .join("circle")
    .attr("class", key)
    .attr("cx", (d) => x(d.label) + x.bandwidth() / 2)
    .attr("cy", (d) => y(d[key]))
    .attr("r", 7)
    .attr("fill", t.palette[0])
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 2.5);
}

// --- Midpoint reference tick -----------------------------------------------------
g.selectAll("line.mean")
  .data(months)
  .join("line")
  .attr("class", "mean")
  .attr("x1", (d) => x(d.label) + x.bandwidth() * 0.18)
  .attr("x2", (d) => x(d.label) + x.bandwidth() * 0.82)
  .attr("y1", (d) => y(d.mean))
  .attr("y2", (d) => y(d.mean))
  .attr("stroke", t.ink)
  .attr("stroke-opacity", 0.55)
  .attr("stroke-width", 2);

// --- Axes ------------------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x));
const yAxis = g.append("g").call(d3.axisLeft(y).tickFormat((d) => `${d}°`));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels -------------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Month");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -80)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Temperature (°C)");

// --- Title -------------------------------------------------------------------------
const title = "Monthly Temperature Range · range-interval · javascript · d3 · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / title.length));
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(title);
