// anyplot.ai
// span-basic: Basic Span Plot (Highlighted Region)
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 60, bottom: 90, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly stock index level, 2006–2011, with two recession periods marked.
function lcg(seed) {
  let s = seed;
  return () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    return s / 0x7fffffff;
  };
}
const rand = lcg(42);

const quarters = [];
for (let year = 2006; year <= 2011; year++) {
  for (let q = 0; q < 4; q++) quarters.push(new Date(year, q * 3, 1));
}

let level = 100;
const series = quarters.map((date, i) => {
  const inRecession =
    (date >= new Date(2007, 9, 1) && date < new Date(2009, 3, 1)) ||
    (date >= new Date(2011, 6, 1) && date < new Date(2011, 12, 1));
  const drift = inRecession ? -3.2 : 1.8;
  level += drift + (rand() - 0.5) * 4;
  level = Math.max(level, 55);
  return { date, index: level };
});

const spans = [
  { start: new Date(2007, 9, 1), end: new Date(2009, 3, 1), label: "2007–09 recession" },
  { start: new Date(2011, 6, 1), end: new Date(2011, 12, 1), label: "2011 slowdown" },
];

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales --------------------------------------------------------------------
const x = d3.scaleTime().domain(d3.extent(series, (d) => d.date)).range([0, iw]);
const y = d3
  .scaleLinear()
  .domain([d3.min(series, (d) => d.index) * 0.95, d3.max(series, (d) => d.index) * 1.05])
  .nice()
  .range([ih, 0]);

// --- Gridlines (y-axis only) ---------------------------------------------------
g.append("g")
  .selectAll("line")
  .data(y.ticks(6))
  .join("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", (d) => y(d))
  .attr("y2", (d) => y(d))
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- Vertical spans (drawn beneath the line) ------------------------------------
const spanColor = t.palette[4]; // matte red — semantic anchor for downturn periods
g.selectAll(".span")
  .data(spans)
  .join("rect")
  .attr("class", "span")
  .attr("x", (d) => x(d.start))
  .attr("y", 0)
  .attr("width", (d) => x(d.end) - x(d.start))
  .attr("height", ih)
  .attr("fill", spanColor)
  .attr("opacity", 0.22);

g.selectAll(".span-label")
  .data(spans)
  .join("text")
  .attr("class", "span-label")
  .attr("x", (d) => x(d.start) + (x(d.end) - x(d.start)) / 2)
  .attr("y", 22)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .style("font-weight", "500")
  .text((d) => d.label);

// --- Line (drawn above the spans) -----------------------------------------------
const line = d3
  .line()
  .x((d) => x(d.date))
  .y((d) => y(d.index));

g.append("path")
  .datum(series)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 3)
  .attr("stroke-linejoin", "round")
  .attr("stroke-linecap", "round")
  .attr("d", line);

// --- Axes -------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(d3.timeYear.every(1)).tickFormat(d3.timeFormat("%Y")).tickSizeOuter(0));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6).tickSizeOuter(0));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "15px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}
xAxis.selectAll("line").remove();
yAxis.selectAll("line").remove();

// --- Axis titles --------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .text("Year");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -80)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .text("Market Index");

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("span-basic · javascript · d3 · anyplot.ai");
