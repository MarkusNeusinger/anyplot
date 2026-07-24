// anyplot.ai
// marimekko-basic: Basic Marimekko Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-07-24

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 100, right: 260, bottom: 130, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Revenue ($M) by region (bar width) and product line (segment height share)
const yCategories = ["Software", "Hardware", "Services", "Support"];
const data = [
  { x: "North America", values: { Software: 420, Hardware: 180, Services: 150, Support: 90 } },
  { x: "Europe", values: { Software: 260, Hardware: 140, Services: 130, Support: 70 } },
  { x: "Asia Pacific", values: { Software: 310, Hardware: 90, Services: 60, Support: 40 } },
  { x: "Latin America", values: { Software: 90, Hardware: 40, Services: 30, Support: 20 } },
];

const rows = data.map((d) => ({
  x: d.x,
  values: yCategories.map((cat) => ({ cat, value: d.values[cat] })),
  total: d3.sum(yCategories, (cat) => d.values[cat]),
}));
const grandTotal = d3.sum(rows, (r) => r.total);

// Column widths proportional to each region's share of grand total
const gap = 10;
const plotWidth = iw - gap * (rows.length - 1);
let cumX = 0;
const columns = rows.map((r) => {
  const colWidth = (r.total / grandTotal) * plotWidth;
  const col = { ...r, x0: cumX, width: colWidth };
  cumX += colWidth + gap;
  return col;
});

// Segment heights proportional to each product line's share within its column
const yScale = d3.scaleLinear().domain([0, 1]).range([ih, 0]);
columns.forEach((col) => {
  let cum = 0;
  col.segments = col.values.map((v) => {
    const share = v.value / col.total;
    const y0 = cum;
    cum += share;
    return { ...v, y0, y1: cum, share };
  });
});

const color = d3.scaleOrdinal().domain(yCategories).range(t.palette);

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Reference gridlines (quartile shares) -------------------------------------
g.selectAll("line.grid")
  .data([0.25, 0.5, 0.75])
  .join("line")
  .attr("class", "grid")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", (d) => yScale(d))
  .attr("y2", (d) => yScale(d))
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- Y axis (share of column revenue) ------------------------------------------
const yAxis = g.append("g").call(d3.axisLeft(yScale).ticks(4).tickFormat(d3.format(".0%")));
yAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
yAxis.selectAll("line").attr("stroke", t.grid);
yAxis.select(".domain").attr("stroke", t.inkSoft);

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -78)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Share of Regional Revenue");

// --- Columns (variable-width stacked bars) -------------------------------------
const columnGroups = g
  .selectAll("g.column")
  .data(columns)
  .join("g")
  .attr("class", "column")
  .attr("transform", (d) => `translate(${d.x0},0)`);

columnGroups.each(function (col) {
  d3.select(this)
    .selectAll("rect")
    .data(col.segments)
    .join("rect")
    .attr("x", 0)
    .attr("y", (s) => yScale(s.y1))
    .attr("width", col.width)
    .attr("height", (s) => yScale(s.y0) - yScale(s.y1))
    .attr("fill", (s) => color(s.cat))
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 2);
});

// Value labels on segments large enough to hold them legibly
columnGroups.each(function (col) {
  const labeled = col.segments.filter(
    (s) => col.width > 140 && yScale(s.y0) - yScale(s.y1) > 90
  );
  d3.select(this)
    .selectAll("text.segment-label")
    .data(labeled)
    .join("text")
    .attr("class", "segment-label")
    .attr("x", col.width / 2)
    .attr("y", (s) => (yScale(s.y1) + yScale(s.y0)) / 2)
    .attr("text-anchor", "middle")
    .attr("dominant-baseline", "middle")
    .attr("fill", t.pageBg)
    .style("font-size", "14px")
    .style("font-weight", "600")
    .text((s) => `$${d3.format(",")(s.value)}M`);
});

// --- X-axis labels (region name + column total, centered under each bar) ------
const xLabels = g
  .selectAll("g.x-label")
  .data(columns)
  .join("g")
  .attr("transform", (d) => `translate(${d.x0 + d.width / 2},${ih})`);

xLabels
  .append("text")
  .attr("y", 30)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .style("font-weight", "600")
  .text((d) => d.x);

xLabels
  .append("text")
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .text((d) => `$${d3.format(",")(d.total)}M total`);

// --- Legend ---------------------------------------------------------------------
const legend = svg
  .append("g")
  .attr("transform", `translate(${margin.left + iw + 50},${margin.top + 30})`);

const legendItems = legend
  .selectAll("g.legend-item")
  .data(yCategories)
  .join("g")
  .attr("class", "legend-item")
  .attr("transform", (d, i) => `translate(0,${i * 34})`);

legendItems
  .append("rect")
  .attr("width", 18)
  .attr("height", 18)
  .attr("rx", 2)
  .attr("fill", (d) => color(d));

legendItems
  .append("text")
  .attr("x", 26)
  .attr("y", 14)
  .attr("fill", t.ink)
  .style("font-size", "14px")
  .text((d) => d);

// --- Title -----------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("marimekko-basic · javascript · d3 · anyplot.ai");
