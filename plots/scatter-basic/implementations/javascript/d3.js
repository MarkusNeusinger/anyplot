// anyplot.ai
// scatter-basic: Basic Scatter Plot
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-02

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 80, right: 60, bottom: 100, left: 120 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (deterministic LCG seed=42, marketing spend vs sales revenue) ----
let seed = 42;
function lcgRand() {
  seed = (1664525 * seed + 1013904223) >>> 0;
  return seed / 4294967296;
}
function lcgRandn() {
  const u1 = lcgRand() + 1e-10;
  const u2 = lcgRand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const data = Array.from({ length: 100 }, () => {
  const spend = 10 + lcgRand() * 140;
  const sales = Math.max(0.3, 0.8 + spend * 0.035 + lcgRandn() * 1.2);
  return { x: spend, y: sales };
});

// --- SVG mount -------------------------------------------------------------
const svg = d3.select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales ----------------------------------------------------------------
const x = d3.scaleLinear()
  .domain([0, d3.max(data, (d) => d.x) * 1.04]).nice().range([0, iw]);
const y = d3.scaleLinear()
  .domain([0, d3.max(data, (d) => d.y) * 1.04]).nice().range([ih, 0]);

// --- Grid lines (both axes for scatter) ------------------------------------
g.append("g").attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(8).tickSize(-ih).tickFormat(""))
  .call((ax) => ax.select(".domain").remove())
  .call((ax) => ax.selectAll("line").attr("stroke", t.grid));

g.append("g")
  .call(d3.axisLeft(y).ticks(6).tickSize(-iw).tickFormat(""))
  .call((ax) => ax.select(".domain").remove())
  .call((ax) => ax.selectAll("line").attr("stroke", t.grid));

// --- X axis ----------------------------------------------------------------
g.append("g").attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(8).tickFormat((d) => `${d}K`))
  .call((ax) => ax.select(".domain").attr("stroke", t.inkSoft))
  .call((ax) => ax.selectAll(".tick text").attr("fill", t.inkSoft).style("font-size", "18px"))
  .call((ax) => ax.selectAll(".tick line").remove());

// --- Y axis ----------------------------------------------------------------
g.append("g")
  .call(d3.axisLeft(y).ticks(6).tickFormat((d) => `$${d.toFixed(1)}M`))
  .call((ax) => ax.select(".domain").attr("stroke", t.inkSoft))
  .call((ax) => ax.selectAll(".tick text").attr("fill", t.inkSoft).style("font-size", "18px"))
  .call((ax) => ax.selectAll(".tick line").remove());

// --- Scatter markers -------------------------------------------------------
g.selectAll("circle").data(data).join("circle")
  .attr("cx", (d) => x(d.x))
  .attr("cy", (d) => y(d.y))
  .attr("r", 8)
  .attr("fill", t.palette[0])
  .attr("fill-opacity", 0.7)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

// --- Axis labels -----------------------------------------------------------
svg.append("text")
  .attr("x", margin.left + iw / 2).attr("y", height - 18)
  .attr("text-anchor", "middle").attr("fill", t.inkSoft)
  .style("font-size", "22px").text("Marketing Spend ($K)");

svg.append("text")
  .attr("transform", `translate(22,${margin.top + ih / 2}) rotate(-90)`)
  .attr("text-anchor", "middle").attr("fill", t.inkSoft)
  .style("font-size", "22px").text("Sales Revenue ($M)");

// --- Title -----------------------------------------------------------------
svg.append("text")
  .attr("x", width / 2).attr("y", 48)
  .attr("text-anchor", "middle").attr("fill", t.ink)
  .style("font-size", "28px").style("font-weight", "600")
  .text("scatter-basic · javascript · d3 · anyplot.ai");
