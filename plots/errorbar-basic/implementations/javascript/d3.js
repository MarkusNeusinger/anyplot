// anyplot.ai
// errorbar-basic: Basic Error Bar Plot
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-30

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

const margin = { top: 85, right: 55, bottom: 95, left: 105 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Crop yield (t/ha) by fertilizer treatment — field trial, n=20 plots per group
const data = [
  { treatment: "Control",    mean: 3.2, sd: 0.38 },
  { treatment: "Nitrogen",   mean: 4.8, sd: 0.52 },
  { treatment: "Phosphorus", mean: 4.1, sd: 0.45 },
  { treatment: "Potassium",  mean: 3.9, sd: 0.41 },
  { treatment: "NPK",        mean: 5.7, sd: 0.61 },
  { treatment: "Organic",    mean: 4.4, sd: 0.49 },
];

// SVG mount
const svg = d3.select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Scales
const x = d3.scaleBand()
  .domain(data.map((d) => d.treatment))
  .range([0, iw])
  .padding(0.35);

const y = d3.scaleLinear()
  .domain([0, d3.max(data, (d) => d.mean + d.sd) + 0.35])
  .nice()
  .range([ih, 0]);

// Horizontal gridlines (y-axis only)
const gridG = g.append("g").attr("class", "grid");
gridG.call(d3.axisLeft(y).tickSize(-iw).tickFormat("").ticks(7));
gridG.selectAll("line").attr("stroke", t.grid).attr("stroke-width", 1);
gridG.select(".domain").remove();

// Axes
const xAxis = g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).tickSizeOuter(0));

const yAxis = g.append("g")
  .call(d3.axisLeft(y).ticks(7).tickFormat((d) => d.toFixed(1)).tickSizeOuter(0));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.grid);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// Helper: horizontal center of each band
const cx = (d) => x(d.treatment) + x.bandwidth() / 2;
const capHalf = x.bandwidth() * 0.22;

// Vertical error bar stems
g.selectAll(".errbar").data(data).join("line")
  .attr("class", "errbar")
  .attr("x1", cx).attr("x2", cx)
  .attr("y1", (d) => y(d.mean - d.sd))
  .attr("y2", (d) => y(d.mean + d.sd))
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 2.5);

// Upper caps
g.selectAll(".cap-top").data(data).join("line")
  .attr("class", "cap-top")
  .attr("x1", (d) => cx(d) - capHalf).attr("x2", (d) => cx(d) + capHalf)
  .attr("y1", (d) => y(d.mean + d.sd)).attr("y2", (d) => y(d.mean + d.sd))
  .attr("stroke", t.palette[0]).attr("stroke-width", 2.5);

// Lower caps
g.selectAll(".cap-bot").data(data).join("line")
  .attr("class", "cap-bot")
  .attr("x1", (d) => cx(d) - capHalf).attr("x2", (d) => cx(d) + capHalf)
  .attr("y1", (d) => y(d.mean - d.sd)).attr("y2", (d) => y(d.mean - d.sd))
  .attr("stroke", t.palette[0]).attr("stroke-width", 2.5);

// Mean value circles
g.selectAll("circle").data(data).join("circle")
  .attr("cx", cx)
  .attr("cy", (d) => y(d.mean))
  .attr("r", 9)
  .attr("fill", t.palette[0])
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2.5);

// Axis labels
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 68)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Fertilizer Treatment");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -75)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Crop Yield (t/ha)");

// Title
svg.append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("errorbar-basic · javascript · d3 · anyplot.ai");
