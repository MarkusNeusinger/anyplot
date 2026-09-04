// anyplot.ai
// contour-density: Density Contour Plot
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-04

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data ---------------------------------------------------------------
// Geyser eruption duration vs. waiting time to the next eruption — a classic
// bimodal bivariate pattern (short/quick eruptions vs. long/slow ones) that
// makes multi-level density contours meaningful. Deterministic LCG + Box-Muller
// stand in for a seeded RNG (the browser has none).
let seed = 42;
function lcg() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function gaussian() {
  const u1 = Math.max(lcg(), 1e-9);
  const u2 = lcg();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const points = [];
const n = 320;
for (let i = 0; i < n; i++) {
  const isShortBurst = lcg() < 0.62;
  const duration = isShortBurst ? 1.9 + gaussian() * 0.28 : 4.35 + gaussian() * 0.38;
  const wait = isShortBurst
    ? 54 + duration * 3.2 + gaussian() * 4.5
    : 76 + duration * 2.4 + gaussian() * 5;
  points.push({ duration, wait });
}

// --- SVG mount ------------------------------------------------------------
const margin = { top: 100, right: 220, bottom: 90, left: 100 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -----------------------------------------------------------------
const durationExtent = d3.extent(points, (d) => d.duration);
const waitExtent = d3.extent(points, (d) => d.wait);
const durationPad = (durationExtent[1] - durationExtent[0]) * 0.12;
const waitPad = (waitExtent[1] - waitExtent[0]) * 0.12;

const x = d3
  .scaleLinear()
  .domain([durationExtent[0] - durationPad, durationExtent[1] + durationPad])
  .range([0, iw])
  .nice();
const y = d3
  .scaleLinear()
  .domain([waitExtent[0] - waitPad, waitExtent[1] + waitPad])
  .range([ih, 0])
  .nice();

// --- Background grid (subtle, sits behind the contour fill) ---------------
g.append("g")
  .attr("class", "grid")
  .selectAll("line.x-grid")
  .data(x.ticks(7))
  .join("line")
  .attr("x1", (d) => x(d))
  .attr("x2", (d) => x(d))
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.grid)
  .attr("stroke-opacity", 0.4);

g.append("g")
  .attr("class", "grid")
  .selectAll("line.y-grid")
  .data(y.ticks(7))
  .join("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", (d) => y(d))
  .attr("y2", (d) => y(d))
  .attr("stroke", t.grid)
  .attr("stroke-opacity", 0.4);

// --- Density contours ---------------------------------------------------
const densityData = d3
  .contourDensity()
  .x((d) => x(d.duration))
  .y((d) => y(d.wait))
  .size([iw, ih])
  .bandwidth(32)
  .thresholds(16)(points);

const densityExtent = d3.extent(densityData, (d) => d.value);
const color = d3.scaleSequential(d3.interpolateRgbBasis(t.seq)).domain(densityExtent);

g.append("g")
  .selectAll("path")
  .data(densityData)
  .join("path")
  .attr("d", d3.geoPath())
  .attr("fill", (d) => color(d.value))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 0.5)
  .attr("stroke-opacity", 0.6);

// --- Scatter overlay (context for the underlying point cloud) --------------
g.append("g")
  .selectAll("circle")
  .data(points)
  .join("circle")
  .attr("cx", (d) => x(d.duration))
  .attr("cy", (d) => y(d.wait))
  .attr("r", 2.75)
  .attr("fill", t.ink)
  .attr("fill-opacity", 0.35)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 0.6)
  .attr("stroke-opacity", 0.5);

// --- Axes ---------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(7));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(7));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Eruption Duration (minutes)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -72)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Waiting Time to Next Eruption (minutes)");

// --- Title ----------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("contour-density · javascript · d3 · anyplot.ai");

// --- Density legend (vertical gradient) ------------------------------------
const legendWidth = 22;
const legendHeight = ih * 0.6;
const legendX = margin.left + iw + 60;
const legendY = margin.top + (ih - legendHeight) / 2;

const gradient = svg
  .append("defs")
  .append("linearGradient")
  .attr("id", "density-gradient")
  .attr("x1", "0%")
  .attr("x2", "0%")
  .attr("y1", "100%")
  .attr("y2", "0%");

const gradientStops = 10;
for (let i = 0; i <= gradientStops; i++) {
  const fraction = i / gradientStops;
  gradient
    .append("stop")
    .attr("offset", `${fraction * 100}%`)
    .attr("stop-color", color(densityExtent[0] + (densityExtent[1] - densityExtent[0]) * fraction));
}

svg
  .append("rect")
  .attr("x", legendX)
  .attr("y", legendY)
  .attr("width", legendWidth)
  .attr("height", legendHeight)
  .attr("fill", "url(#density-gradient)")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1);

svg
  .append("text")
  .attr("x", legendX + legendWidth / 2)
  .attr("y", legendY - 16)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("High");

svg
  .append("text")
  .attr("x", legendX + legendWidth / 2)
  .attr("y", legendY + legendHeight + 26)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Low");

svg
  .append("text")
  .attr(
    "transform",
    `translate(${legendX + legendWidth + 26}, ${legendY + legendHeight / 2}) rotate(90)`
  )
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text("Point density");
