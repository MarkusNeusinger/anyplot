// anyplot.ai
// dumbbell-basic: Basic Dumbbell Chart
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: 87/100 | Created: 2026-06-30

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

const margin = { top: 95, right: 80, bottom: 90, left: 175 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Employee satisfaction scores (0–100) before and after flexible work policy
const rawData = [
  { dept: "Research",         before: 57, after: 79 },
  { dept: "Engineering",      before: 72, after: 91 },
  { dept: "Product",          before: 63, after: 81 },
  { dept: "IT Support",       before: 65, after: 82 },
  { dept: "Design",           before: 68, after: 84 },
  { dept: "Operations",       before: 71, after: 83 },
  { dept: "Marketing",        before: 60, after: 71 },
  { dept: "Customer Success", before: 66, after: 76 },
  { dept: "HR",               before: 75, after: 83 },
  { dept: "Finance",          before: 62, after: 69 },
];

// Sort by improvement (largest gap at top)
const data = rawData.slice().sort((a, b) => (b.after - b.before) - (a.after - a.before));

const svg = d3.select("#container").append("svg")
  .attr("width", width)
  .attr("height", height);

const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Scales
const x = d3.scaleLinear().domain([50, 100]).range([0, iw]);
const y = d3.scaleBand()
  .domain(data.map(d => d.dept))
  .range([0, ih])
  .padding(0.4);

// Vertical gridlines
g.selectAll(".vgrid")
  .data(x.ticks(6))
  .join("line")
  .attr("x1", d => x(d))
  .attr("x2", d => x(d))
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// X-axis
const xAxisG = g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(6).tickSize(0));

xAxisG.select(".domain").attr("stroke", t.inkSoft);
xAxisG.selectAll(".tick text")
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .attr("dy", "1.3em");
xAxisG.selectAll(".tick line").remove();

// Y-axis (no domain line — categories are self-labelling)
const yAxisG = g.append("g")
  .call(d3.axisLeft(y).tickSize(0));

yAxisG.select(".domain").remove();
yAxisG.selectAll(".tick text")
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .attr("dx", "-0.6em");

// Connecting lines
g.selectAll(".dumbbell-line")
  .data(data)
  .join("line")
  .attr("x1", d => x(d.before))
  .attr("x2", d => x(d.after))
  .attr("y1", d => y(d.dept) + y.bandwidth() / 2)
  .attr("y2", d => y(d.dept) + y.bandwidth() / 2)
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 2.5)
  .attr("opacity", 0.4);

// Before dots (Imprint palette[0] — brand green)
g.selectAll(".dot-before")
  .data(data)
  .join("circle")
  .attr("cx", d => x(d.before))
  .attr("cy", d => y(d.dept) + y.bandwidth() / 2)
  .attr("r", 10)
  .attr("fill", t.palette[0])
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2);

// After dots (Imprint palette[1] — lavender)
g.selectAll(".dot-after")
  .data(data)
  .join("circle")
  .attr("cx", d => x(d.after))
  .attr("cy", d => y(d.dept) + y.bandwidth() / 2)
  .attr("r", 10)
  .attr("fill", t.palette[1])
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2);

// X-axis label
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 62)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Satisfaction Score (0–100)");

// Legend (horizontal, centered below title in top margin)
const legendItems = [
  { label: "Before Policy", color: t.palette[0] },
  { label: "After Policy",  color: t.palette[1] },
];
const legendSpacing = 170;
const legendStartX = (width - legendItems.length * legendSpacing) / 2;
const legendY = 72;

legendItems.forEach((item, i) => {
  const lx = legendStartX + i * legendSpacing;
  svg.append("circle")
    .attr("cx", lx + 10).attr("cy", legendY)
    .attr("r", 10)
    .attr("fill", item.color)
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 1.5);
  svg.append("text")
    .attr("x", lx + 26).attr("y", legendY + 5)
    .attr("fill", t.inkSoft)
    .style("font-size", "13px")
    .text(item.label);
});

// Title — font-size scaled for title length
const title = "Employee Satisfaction · dumbbell-basic · javascript · d3 · anyplot.ai";
const titleFontSize = title.length > 67 ? Math.round(22 * 67 / title.length) : 22;

svg.append("text")
  .attr("x", width / 2)
  .attr("y", 42)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(title);
