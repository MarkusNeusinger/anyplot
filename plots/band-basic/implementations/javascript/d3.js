// anyplot.ai
// band-basic: Basic Band Plot
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 70, bottom: 90, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: 60-day streamflow forecast with a widening 90% prediction band --
// Deterministic LCG so the "uncertainty" wiggle is reproducible without Math.random().
let seed = 42;
function lcg() {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
}

const days = 60;
const data = Array.from({ length: days }, (_, i) => {
  const day = i + 1;
  const seasonal = 8 * Math.sin((2 * Math.PI * day) / 45);
  const trend = 0.15 * day;
  const wiggle = (lcg() - 0.5) * 3;
  const yCenter = 42 + trend + seasonal + wiggle;
  // Forecast uncertainty grows the further out the prediction reaches.
  const spread = 3 + 0.35 * day;
  return { day, yCenter, yLower: yCenter - spread, yUpper: yCenter + spread };
});

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales --------------------------------------------------------------------
const x = d3
  .scaleLinear()
  .domain(d3.extent(data, (d) => d.day))
  .range([0, iw]);
const y = d3
  .scaleLinear()
  .domain([d3.min(data, (d) => d.yLower) - 3, d3.max(data, (d) => d.yUpper) + 3])
  .nice()
  .range([ih, 0]);

// --- Gridlines (y-axis only) ---------------------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Band (semi-transparent prediction interval) -------------------------------
const area = d3
  .area()
  .x((d) => x(d.day))
  .y0((d) => y(d.yLower))
  .y1((d) => y(d.yUpper))
  .curve(d3.curveMonotoneX);

g.append("path").datum(data).attr("d", area).attr("fill", t.palette[0]).attr("fill-opacity", 0.28).attr("stroke", "none");

// --- Center trend line -----------------------------------------------------------
const line = d3
  .line()
  .x((d) => x(d.day))
  .y((d) => y(d.yCenter))
  .curve(d3.curveMonotoneX);

g.append("path")
  .datum(data)
  .attr("d", line)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 3.5)
  .attr("stroke-linejoin", "round")
  .attr("stroke-linecap", "round");

// --- Axes -------------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(10).tickFormat((d) => `Day ${d}`));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(8).tickFormat((d) => `${d.toFixed(0)} m³/s`));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.grid);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels --------------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 62)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Forecast Day");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -80)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("River Streamflow (m³/s)");

// --- Title ------------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("Streamflow Forecast · band-basic · javascript · d3 · anyplot.ai");

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 78)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text("Shaded band shows the 90% prediction interval around the forecast mean");
