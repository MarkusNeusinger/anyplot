// anyplot.ai
// pyramid-basic: Basic Pyramid Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Data — streaming-service subscriber counts by age bracket (thousands).
// Two competing services, symmetric axis scale, revealing an age-driven
// crossover in preference.
const ageGroups = [
  { category: "18–24", auroraStream: 18, novaPlay: 42 },
  { category: "25–34", auroraStream: 28, novaPlay: 38 },
  { category: "35–44", auroraStream: 35, novaPlay: 30 },
  { category: "45–54", auroraStream: 44, novaPlay: 24 },
  { category: "55–64", auroraStream: 52, novaPlay: 16 },
  { category: "65+", auroraStream: 46, novaPlay: 10 },
];
const maxValue = 60;

// Layout — two mirrored bar areas separated by a gap for center category labels.
const margin = { top: 130, right: 70, bottom: 90, left: 70 };
const innerWidth = width - margin.left - margin.right;
const innerHeight = height - margin.top - margin.bottom;
const centerGap = 140;
const sideWidth = (innerWidth - centerGap) / 2;
const leftX0 = margin.left;
const rightX0 = margin.left + sideWidth + centerGap;
const centerX = margin.left + sideWidth + centerGap / 2;

// Scales
const xLeft = d3.scaleLinear().domain([0, maxValue]).range([sideWidth, 0]);
const xRight = d3.scaleLinear().domain([0, maxValue]).range([0, sideWidth]);
const y = d3
  .scaleBand()
  .domain(ageGroups.map((d) => d.category))
  .range([0, innerHeight])
  .padding(0.28);

// SVG mount
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// Center divider
svg
  .append("line")
  .attr("x1", centerX)
  .attr("x2", centerX)
  .attr("y1", margin.top)
  .attr("y2", margin.top + innerHeight)
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// Left bars (AuroraStream)
svg
  .selectAll(".bar-left")
  .data(ageGroups)
  .join("rect")
  .attr("x", (d) => leftX0 + xLeft(d.auroraStream))
  .attr("y", (d) => margin.top + y(d.category))
  .attr("width", (d) => sideWidth - xLeft(d.auroraStream))
  .attr("height", y.bandwidth())
  .attr("fill", t.palette[0]);

// Right bars (NovaPlay)
svg
  .selectAll(".bar-right")
  .data(ageGroups)
  .join("rect")
  .attr("x", rightX0)
  .attr("y", (d) => margin.top + y(d.category))
  .attr("width", (d) => xRight(d.novaPlay))
  .attr("height", y.bandwidth())
  .attr("fill", t.palette[1]);

// Center category labels
svg
  .selectAll(".category-label")
  .data(ageGroups)
  .join("text")
  .attr("x", centerX)
  .attr("y", (d) => margin.top + y(d.category) + y.bandwidth() / 2)
  .attr("dy", "0.35em")
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text((d) => d.category);

// Value axes (bottom, mirrored)
const leftAxis = svg
  .append("g")
  .attr("transform", `translate(${leftX0},${margin.top + innerHeight})`)
  .call(d3.axisBottom(xLeft).ticks(5));
const rightAxis = svg
  .append("g")
  .attr("transform", `translate(${rightX0},${margin.top + innerHeight})`)
  .call(d3.axisBottom(xRight).ticks(5));
for (const axis of [leftAxis, rightAxis]) {
  axis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  axis.selectAll("line").attr("stroke", t.grid);
  axis.select(".domain").attr("stroke", t.inkSoft);
}

// Axis title
svg
  .append("text")
  .attr("x", margin.left + innerWidth / 2)
  .attr("y", height - 20)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text("Subscribers (thousands)");

// Legend
const legend = svg.append("g").attr("transform", `translate(${margin.left + innerWidth / 2}, 78)`);
const legendItems = [
  { label: "AuroraStream", color: t.palette[0], dx: -170 },
  { label: "NovaPlay", color: t.palette[1], dx: 20 },
];
for (const item of legendItems) {
  legend
    .append("rect")
    .attr("x", item.dx)
    .attr("y", -12)
    .attr("width", 16)
    .attr("height", 16)
    .attr("fill", item.color);
  legend
    .append("text")
    .attr("x", item.dx + 22)
    .attr("y", 0)
    .attr("fill", t.inkSoft)
    .style("font-size", "15px")
    .text(item.label);
}

// Title
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("pyramid-basic · javascript · d3 · anyplot.ai");
