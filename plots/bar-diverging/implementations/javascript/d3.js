// anyplot.ai
// bar-diverging: Diverging Bar Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-08-18

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 90, bottom: 90, left: 260 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: year-over-year revenue growth by product line (%) ---------------
const productLines = [
  { category: "Cloud Services", value: 24 },
  { category: "Data Analytics", value: 19 },
  { category: "Cybersecurity", value: 15 },
  { category: "IoT Sensors", value: 11 },
  { category: "Streaming Media", value: 8 },
  { category: "Mobile Devices", value: 4 },
  { category: "Enterprise Software", value: -3 },
  { category: "Consumer Electronics", value: -7 },
  { category: "Retail POS Systems", value: -10 },
  { category: "Desktop Software", value: -13 },
  { category: "Legacy Hardware", value: -16 },
  { category: "Print Media", value: -21 },
];

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const maxAbs = d3.max(productLines, (d) => Math.abs(d.value));
const x = d3.scaleLinear().domain([-maxAbs, maxAbs]).nice().range([0, iw]);
const y = d3
  .scaleBand()
  .domain(productLines.map((d) => d.category))
  .range([0, ih])
  .padding(0.28);

// --- Gridlines (value axis only) ----------------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisBottom(x).tickSize(-ih).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Zero baseline --------------------------------------------------------------
g.append("line")
  .attr("x1", x(0))
  .attr("x2", x(0))
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1.5);

// --- Bars -----------------------------------------------------------------------
g.selectAll("rect")
  .data(productLines)
  .join("rect")
  .attr("x", (d) => Math.min(x(0), x(d.value)))
  .attr("y", (d) => y(d.category))
  .attr("width", (d) => Math.abs(x(d.value) - x(0)))
  .attr("height", y.bandwidth())
  .attr("fill", (d) => (d.value >= 0 ? t.palette[0] : t.palette[4]));

// --- Value labels at bar tips ----------------------------------------------------
g.selectAll(".value-label")
  .data(productLines)
  .join("text")
  .attr("class", "value-label")
  .attr("x", (d) => x(d.value) + (d.value >= 0 ? 10 : -10))
  .attr("y", (d) => y(d.category) + y.bandwidth() / 2)
  .attr("dy", "0.35em")
  .attr("text-anchor", (d) => (d.value >= 0 ? "start" : "end"))
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text((d) => `${d.value > 0 ? "+" : ""}${d.value}%`);

// --- Axes -----------------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).tickFormat((d) => `${d}%`));
xAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
xAxis.selectAll("line").attr("stroke", t.inkSoft);
xAxis.select(".domain").attr("stroke", t.inkSoft);

const yAxis = g.append("g").call(d3.axisLeft(y).tickSize(0));
yAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "15px");
yAxis.select(".domain").remove();

// --- Axis label ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", height - 30)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text("Year-over-Year Revenue Growth (%)");

// --- Legend (growth / decline) ----------------------------------------------------
const legend = svg.append("g").attr("transform", `translate(${width - margin.right - 210},${margin.top - 56})`);
const legendItems = [
  { label: "Growth", color: t.palette[0] },
  { label: "Decline", color: t.palette[4] },
];
legendItems.forEach((item, i) => {
  const row = legend.append("g").attr("transform", `translate(${i * 110},0)`);
  row.append("rect").attr("width", 16).attr("height", 16).attr("fill", item.color);
  row
    .append("text")
    .attr("x", 24)
    .attr("y", 13)
    .attr("fill", t.inkSoft)
    .style("font-size", "14px")
    .text(item.label);
});

// --- Title -------------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 54)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("bar-diverging · javascript · d3 · anyplot.ai");
