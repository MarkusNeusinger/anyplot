// anyplot.ai
// line-styled: Styled Line Plot
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 80, right: 220, bottom: 80, left: 90 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Fixed-seed LCG — the browser has no seeded RNG.
let seed = 42;
function rand() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const months = 36;
const series = [
  { name: "North America", start: 82, drift: 0.55, noise: 2.2, dash: null },
  { name: "Europe", start: 68, drift: 0.35, noise: 2.0, dash: "8,6" },
  { name: "Asia-Pacific", start: 45, drift: 0.9, noise: 2.6, dash: "2,4" },
  { name: "Latin America", start: 30, drift: 0.4, noise: 1.6, dash: "10,4,2,4" },
];

const data = series.map((s) => {
  let value = s.start;
  const points = [];
  for (let i = 0; i < months; i += 1) {
    value += s.drift + (rand() - 0.5) * s.noise;
    value = Math.max(5, value);
    points.push({ month: i, value });
  }
  return { name: s.name, dash: s.dash, points };
});

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales --------------------------------------------------------------------
const x = d3.scaleLinear().domain([0, months - 1]).range([0, iw]);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(data, (s) => d3.max(s.points, (p) => p.value))])
  .nice()
  .range([ih, 0]);

// --- Gridlines (y-axis only, subtle) --------------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Axes ------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(
    d3
      .axisBottom(x)
      .ticks(9)
      .tickFormat((d) => `M${d}`),
  );
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6).tickFormat((d) => `${d}`));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.grid);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels -------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Month");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -62)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Shipment Volume (thousand units)");

// --- Lines — distinguished by style, not just color -----------------------------
const color = d3.scaleOrdinal().domain(series.map((s) => s.name)).range(t.palette);
const line = d3
  .line()
  .x((d) => x(d.month))
  .y((d) => y(d.value))
  .curve(d3.curveMonotoneX);

g.selectAll(".series-line")
  .data(data)
  .join("path")
  .attr("class", "series-line")
  .attr("fill", "none")
  .attr("stroke", (d) => color(d.name))
  .attr("stroke-width", 3.5)
  .attr("stroke-dasharray", (d) => d.dash)
  .attr("stroke-linecap", "round")
  .attr("d", (d) => line(d.points));

// --- Legend (style + color mapping) --------------------------------------------
const legend = svg
  .append("g")
  .attr("transform", `translate(${margin.left + iw + 40},${margin.top + 20})`);

const legendRows = legend
  .selectAll(".legend-row")
  .data(data)
  .join("g")
  .attr("class", "legend-row")
  .attr("transform", (d, i) => `translate(0,${i * 44})`);

legendRows
  .append("line")
  .attr("x1", 0)
  .attr("x2", 40)
  .attr("y1", 0)
  .attr("y2", 0)
  .attr("stroke", (d) => color(d.name))
  .attr("stroke-width", 3.5)
  .attr("stroke-dasharray", (d) => d.dash)
  .attr("stroke-linecap", "round");

legendRows
  .append("text")
  .attr("x", 52)
  .attr("y", 5)
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text((d) => d.name);

// --- Title -------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("line-styled · javascript · d3 · anyplot.ai");
