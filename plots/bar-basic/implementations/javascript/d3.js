// anyplot.ai
// bar-basic: Basic Bar Chart
// Library: d3 7.9.0 | JavaScript 22.22.3
// Quality: 90/100 | Created: 2026-06-02

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 60, bottom: 100, left: 130 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Data — quarterly revenue (USD millions) for a fictional consumer-products company
const data = [
  { category: "Beverages", value: 184.2 },
  { category: "Snacks", value: 152.7 },
  { category: "Dairy", value: 138.4 },
  { category: "Bakery", value: 121.9 },
  { category: "Frozen", value: 97.3 },
  { category: "Produce", value: 86.1 },
  { category: "Pantry", value: 74.5 },
  { category: "Household", value: 58.8 },
];

// SVG mount
const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);
const g = svg
  .append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// Scales
const x = d3
  .scaleBand()
  .domain(data.map((d) => d.category))
  .range([0, iw])
  .padding(0.28);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(data, (d) => d.value) * 1.1])
  .nice()
  .range([ih, 0]);

// Y-axis gridlines (drawn behind the bars, no domain line)
g.append("g")
  .attr("class", "y-grid")
  .call(d3.axisLeft(y).ticks(6).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .call((sel) =>
    sel.selectAll("line").attr("stroke", t.ink).attr("stroke-opacity", 0.15),
  );

// Bars — Imprint palette position 1 (brand green) for the single series
g.selectAll("rect.bar")
  .data(data)
  .join("rect")
  .attr("class", "bar")
  .attr("x", (d) => x(d.category))
  .attr("y", (d) => y(d.value))
  .attr("width", x.bandwidth())
  .attr("height", (d) => ih - y(d.value))
  .attr("fill", t.palette[0]);

// Value labels above each bar
g.selectAll("text.value-label")
  .data(data)
  .join("text")
  .attr("class", "value-label")
  .attr("x", (d) => x(d.category) + x.bandwidth() / 2)
  .attr("y", (d) => y(d.value) - 12)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "20px")
  .style("font-weight", "500")
  .text((d) => `$${d.value.toFixed(0)}M`);

// X-axis (floating — domain line kept as a subtle baseline)
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).tickSize(0).tickPadding(12));
xAxis.select(".domain").attr("stroke", t.inkSoft);
xAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "22px");

// Y-axis (floating — no domain line; values formatted as $N M)
const yAxis = g
  .append("g")
  .call(
    d3
      .axisLeft(y)
      .ticks(6)
      .tickSize(0)
      .tickPadding(14)
      .tickFormat((d) => `$${d}M`),
  );
yAxis.select(".domain").remove();
yAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "20px");

// Axis labels
svg
  .append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", height - 24)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "24px")
  .text("Product Category");

svg
  .append("text")
  .attr("transform", `translate(36, ${margin.top + ih / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "24px")
  .text("Quarterly Revenue (USD millions)");

// Title — descriptive prefix included; ~72 chars at 28px fits comfortably
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "28px")
  .style("font-weight", "600")
  .text("Quarterly Revenue by Category · bar-basic · javascript · d3 · anyplot.ai");
