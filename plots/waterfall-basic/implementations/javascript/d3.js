// anyplot.ai
// waterfall-basic: Basic Waterfall Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-08-04

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 140, right: 60, bottom: 160, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic): quarterly revenue bridge, $K --------
const changes = [
  { label: "Starting Revenue", value: 850, type: "total" },
  { label: "Cost of Goods Sold", value: -320, type: "change" },
  { label: "Operating Expenses", value: -180, type: "change" },
  { label: "R&D Investment", value: -95, type: "change" },
  { label: "Marketing Spend", value: -60, type: "change" },
  { label: "Tax Adjustment", value: -45, type: "change" },
  { label: "Other Income", value: 25, type: "change" },
  { label: "Net Profit", value: null, type: "total" },
];

let cumulative = 0;
const steps = changes.map((d) => {
  if (d.type === "total" && d.value !== null) {
    cumulative = d.value;
    return { ...d, start: 0, end: d.value };
  }
  if (d.type === "change") {
    const start = cumulative;
    cumulative += d.value;
    return { ...d, start, end: cumulative };
  }
  // final total: value derived from the running cumulative
  return { ...d, value: cumulative, start: 0, end: cumulative };
});

const fmtTotal = (v) => `$${d3.format(",")(Math.round(v))}K`;
const fmtChange = (v) => `${v >= 0 ? "+" : ""}${d3.format(",")(Math.round(v))}K`;

// --- Scales ------------------------------------------------------------------
const x = d3
  .scaleBand()
  .domain(steps.map((d) => d.label))
  .range([0, iw])
  .padding(0.35);

const maxLevel = d3.max(steps, (d) => Math.max(d.start, d.end));
const y = d3
  .scaleLinear()
  .domain([0, maxLevel * 1.12])
  .nice()
  .range([ih, 0]);

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Y grid (horizontal only) --------------------------------------------------
g.append("g")
  .call(d3.axisLeft(y).ticks(6).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Connecting lines (running-total flow) -------------------------------------
for (let i = 0; i < steps.length - 1; i++) {
  const level = steps[i].end;
  g.append("line")
    .attr("x1", x(steps[i].label) + x.bandwidth())
    .attr("x2", x(steps[i + 1].label))
    .attr("y1", y(level))
    .attr("y2", y(level))
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1.5)
    .attr("stroke-dasharray", "4,4")
    .attr("opacity", 0.6);
}

// --- Bars -----------------------------------------------------------------------
const barColor = (d) => {
  if (d.type === "total") return t.ink;
  return d.value >= 0 ? t.palette[0] : t.palette[4];
};

g.selectAll("rect.bar")
  .data(steps)
  .join("rect")
  .attr("class", "bar")
  .attr("x", (d) => x(d.label))
  .attr("y", (d) => y(Math.max(d.start, d.end)))
  .attr("width", x.bandwidth())
  .attr("height", (d) => Math.max(1, y(Math.min(d.start, d.end)) - y(Math.max(d.start, d.end))))
  .attr("fill", barColor)
  .attr("rx", 3);

// --- Value labels -----------------------------------------------------------------
g.selectAll("text.value")
  .data(steps)
  .join("text")
  .attr("class", "value")
  .attr("x", (d) => x(d.label) + x.bandwidth() / 2)
  .attr("y", (d) => y(Math.max(d.start, d.end)) - 14)
  .attr("text-anchor", "middle")
  .attr("fill", (d) => (d.type === "total" ? t.ink : barColor(d)))
  .style("font-size", "16px")
  .style("font-weight", "600")
  .text((d) => (d.type === "total" ? fmtTotal(d.value) : fmtChange(d.value)));

// --- X axis -----------------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x));
xAxis.select(".domain").attr("stroke", t.inkSoft);
xAxis.selectAll("line").attr("stroke", t.inkSoft);
xAxis
  .selectAll("text")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .attr("transform", "rotate(-30)")
  .attr("text-anchor", "end")
  .attr("dx", "-0.6em")
  .attr("dy", "0.3em");

// --- Y axis -----------------------------------------------------------------------
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6).tickFormat((v) => `$${d3.format(",")(v)}K`));
yAxis.select(".domain").attr("stroke", t.inkSoft);
yAxis.selectAll("line").attr("stroke", t.inkSoft);
yAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -80)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Amount ($K)");

// --- Legend ------------------------------------------------------------------------
const legendItems = [
  { label: "Increase", color: t.palette[0] },
  { label: "Decrease", color: t.palette[4] },
  { label: "Total", color: t.ink },
];
const legend = svg.append("g").attr("transform", `translate(${width - margin.right - 340},70)`);
legendItems.forEach((item, i) => {
  const lg = legend.append("g").attr("transform", `translate(${i * 115},0)`);
  lg.append("rect").attr("width", 16).attr("height", 16).attr("rx", 3).attr("fill", item.color);
  lg.append("text")
    .attr("x", 24)
    .attr("y", 13)
    .attr("fill", t.inkSoft)
    .style("font-size", "14px")
    .text(item.label);
});

// --- Title ---------------------------------------------------------------------------
const title = "Quarterly Revenue Bridge · waterfall-basic · javascript · d3 · anyplot.ai";
const titleFontSize = Math.max(15, Math.round(22 * Math.min(1, 67 / title.length)));
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(title);
