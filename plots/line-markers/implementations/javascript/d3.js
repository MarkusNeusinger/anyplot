// anyplot.ai
// line-markers: Line Plot with Markers
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 284, bottom: 110, left: 120 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: enzyme activity across a pH gradient, three variants -----------
// Sparse discrete measurements (13 pH readings per enzyme) where each point
// is a meaningful lab observation, not a dense sampled curve.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

const phLevels = [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0];

function bellActivity(ph, optimum, sigma, peak) {
  const gaussian = peak * Math.exp(-((ph - optimum) ** 2) / (2 * sigma ** 2));
  const noise = (rand() - 0.5) * 4;
  return Math.max(0, gaussian + noise);
}

const enzymes = [
  {
    name: "Pepsin",
    optimum: 5.0,
    sigma: 1.3,
    peak: 92,
    color: t.palette[0],
    symbol: d3.symbolCircle,
  },
  {
    name: "Trypsin",
    optimum: 7.5,
    sigma: 1.1,
    peak: 88,
    color: t.palette[1],
    symbol: d3.symbolSquare,
  },
  {
    name: "Alkaline phosphatase",
    optimum: 9.5,
    sigma: 1.4,
    peak: 96,
    color: t.palette[2],
    symbol: d3.symbolTriangle,
  },
];

const series = enzymes.map((e) => ({
  ...e,
  values: phLevels.map((ph) => ({ ph, activity: bellActivity(ph, e.optimum, e.sigma, e.peak) })),
}));

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const x = d3.scaleLinear().domain([4.0, 10.0]).range([0, iw]);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(series, (s) => d3.max(s.values, (v) => v.activity)) * 1.1])
  .nice()
  .range([ih, 0]);

// --- Gridlines (y-axis only, subtle) -------------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid)
  .attr("stroke-opacity", 0.15);

// --- Axes -----------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).tickValues([4, 5, 6, 7, 8, 9, 10]).tickFormat((d) => d.toFixed(0)));
const yAxis = g.append("g").call(d3.axisLeft(y));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Lines + markers per series -----------------------------------------------
const line = d3
  .line()
  .x((d) => x(d.ph))
  .y((d) => y(d.activity));

for (const s of series) {
  const peak = s.values.reduce((a, b) => (b.activity > a.activity ? b : a));

  // Soft halo behind the optimum point gives each curve a clear focal point.
  g.append("circle")
    .attr("cx", x(peak.ph))
    .attr("cy", y(peak.activity))
    .attr("r", 26)
    .attr("fill", s.color)
    .attr("opacity", 0.16);

  g.append("path")
    .datum(s.values)
    .attr("fill", "none")
    .attr("stroke", s.color)
    .attr("stroke-width", 3)
    .attr("d", line);

  g.selectAll(`.marker-${s.name.replace(/\s/g, "")}`)
    .data(s.values)
    .join("path")
    .attr("d", (d) => d3.symbol().type(s.symbol).size(d === peak ? 460 : 260)())
    .attr("transform", (d) => `translate(${x(d.ph)},${y(d.activity)})`)
    .attr("fill", s.color)
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 2);
}

// --- Axis labels ------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 64)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("pH Level");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -84)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Enzyme Activity (%)");

// --- Legend (symbol + color + line swatch per series) -------------------------
const legend = svg
  .append("g")
  .attr("transform", `translate(${margin.left + iw + 40},${margin.top + 20})`);

series.forEach((s, i) => {
  const row = legend.append("g").attr("transform", `translate(0,${i * 56})`);
  row
    .append("line")
    .attr("x1", 0)
    .attr("x2", 60)
    .attr("y1", 0)
    .attr("y2", 0)
    .attr("stroke", s.color)
    .attr("stroke-width", 3);
  row
    .append("path")
    .attr("d", d3.symbol().type(s.symbol).size(260)())
    .attr("transform", "translate(30,0)")
    .attr("fill", s.color)
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 2);
  row
    .append("text")
    .attr("x", 76)
    .attr("y", 0)
    .attr("dominant-baseline", "middle")
    .attr("fill", t.inkSoft)
    .style("font-size", "16px")
    .text(s.name);
});

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("line-markers · javascript · d3 · anyplot.ai");
