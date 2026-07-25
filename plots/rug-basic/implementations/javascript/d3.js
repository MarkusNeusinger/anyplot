// anyplot.ai
// rug-basic: Basic Rug Plot
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 60, bottom: 110, left: 100 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// API endpoint response times (ms) for 180 requests: a lognormal-ish cluster
// of fast responses plus a small cluster of slow/timed-out retries.
let seed = 42;
const lcg = () => {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
};
const gaussian = () => {
  const u1 = lcg() || 1e-9;
  const u2 = lcg();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
};

const responseTimes = [];
for (let i = 0; i < 170; i++) {
  responseTimes.push(Math.exp(Math.log(140) + 0.35 * gaussian()));
}
for (let i = 0; i < 10; i++) {
  responseTimes.push(500 + gaussian() * 18);
}

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Layout: histogram on top, rug strip below, sharing the x scale ----------
const rugHeight = 34;
const rugGap = 16;
const histHeight = ih - rugHeight - rugGap;
const rugTop = histHeight + rugGap;

// --- Scale ----------------------------------------------------------------
const x = d3
  .scaleLinear()
  .domain([0, d3.max(responseTimes) * 1.04])
  .range([0, iw]);

const bins = d3.bin().domain(x.domain()).thresholds(24)(responseTimes);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(bins, (b) => b.length)])
  .nice()
  .range([histHeight, 0]);

// --- Y gridlines (histogram area only) --------------------------------------
g.append("g")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((axis) => axis.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Histogram bars -----------------------------------------------------------
g.selectAll("rect.bar")
  .data(bins)
  .join("rect")
  .attr("class", "bar")
  .attr("x", (b) => x(b.x0) + 1)
  .attr("y", (b) => y(b.length))
  .attr("width", (b) => Math.max(0, x(b.x1) - x(b.x0) - 2))
  .attr("height", (b) => histHeight - y(b.length))
  .attr("fill", t.palette[0])
  .attr("fill-opacity", 0.85)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1);

// --- Rug strip: one tick per observation, semi-transparent for overlap -------
g.selectAll("line.rug")
  .data(responseTimes)
  .join("line")
  .attr("class", "rug")
  .attr("x1", (d) => x(d))
  .attr("x2", (d) => x(d))
  .attr("y1", rugTop)
  .attr("y2", rugTop + rugHeight)
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 1.5)
  .attr("stroke-opacity", 0.35);

// --- Axes ------------------------------------------------------------------
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6));
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${rugTop + rugHeight})`)
  .call(d3.axisBottom(x));

for (const axis of [xAxis, yAxis]) {
  axis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  axis.selectAll("line").attr("stroke", t.inkSoft);
  axis.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels -------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", rugTop + rugHeight + 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Response Time (ms)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -histHeight / 2)
  .attr("y", -70)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Number of Requests");

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 46)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("rug-basic · javascript · d3 · anyplot.ai");
