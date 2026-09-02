// anyplot.ai
// frequency-polygon-basic: Frequency Polygon for Distribution Comparison
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 70, bottom: 90, left: 100 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Fixed-seed LCG — the browser has no seeded RNG.
const lcg = (seed) => {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
};
const rng = lcg(42);
const randNormal = (mean, sd) => {
  const u1 = Math.max(rng(), 1e-9);
  const u2 = rng();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * sd;
};

const groups = [
  { name: "Control", mean: 450, sd: 55, n: 500, dash: "0" },
  { name: "Low Load", mean: 520, sd: 65, n: 500, dash: "9,5" },
  { name: "High Load", mean: 610, sd: 85, n: 500, dash: "2,4" },
];

const binMin = 250;
const binMax = 900;
const binWidth = 25;
const thresholds = d3.range(binMin, binMax + binWidth, binWidth);
const bin = d3.bin().domain([binMin, binMax]).thresholds(thresholds);

const series = groups.map((g, i) => {
  const values = Array.from({ length: g.n }, () => randNormal(g.mean, g.sd)).filter(
    (v) => v > binMin && v < binMax,
  );
  const bins = bin(values);
  const midpoints = bins.map((b) => ({ x: (b.x0 + b.x1) / 2, y: b.length }));
  // Extend to zero at both ends to close the polygon shape.
  const points = [{ x: binMin - binWidth / 2, y: 0 }, ...midpoints, { x: binMax + binWidth / 2, y: 0 }];
  return { ...g, points, midpoints, color: t.palette[i] };
});

// --- Scales -------------------------------------------------------------------
const allPoints = series.flatMap((s) => s.points);
const x = d3
  .scaleLinear()
  .domain(d3.extent(allPoints, (d) => d.x))
  .range([0, iw]);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(allPoints, (d) => d.y)])
  .nice()
  .range([ih, 0]);

// --- SVG mount ------------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Y gridlines (subtle, behind data) -------------------------------------------
g.append("g")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid)
  .attr("stroke-opacity", 0.5);

// --- Area fills + polygon lines + markers ----------------------------------------
const area = d3
  .area()
  .x((d) => x(d.x))
  .y0(y(0))
  .y1((d) => y(d.y))
  .curve(d3.curveLinear);

const line = d3
  .line()
  .x((d) => x(d.x))
  .y((d) => y(d.y))
  .curve(d3.curveLinear);

for (const s of series) {
  g.append("path").datum(s.points).attr("d", area).attr("fill", s.color).attr("fill-opacity", 0.12);
}
for (const s of series) {
  g.append("path")
    .datum(s.points)
    .attr("d", line)
    .attr("fill", "none")
    .attr("stroke", s.color)
    .attr("stroke-width", 3.5)
    .attr("stroke-dasharray", s.dash)
    .attr("stroke-linejoin", "round");
  g.selectAll(`.marker-${s.name.replace(/\s+/g, "")}`)
    .data(s.midpoints.filter((d) => d.y > 0))
    .join("circle")
    .attr("cx", (d) => x(d.x))
    .attr("cy", (d) => y(d.y))
    .attr("r", 4.5)
    .attr("fill", s.color)
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 1.2);
}

// --- Axes -----------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(9));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "15px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels ------------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .text("Response Time (ms)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -70)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .text("Frequency (count)");

// --- Legend (top-right, above the empty tail region) -------------------------------
const legend = g.append("g").attr("transform", `translate(${iw - 210},${18})`);
series.forEach((s, i) => {
  const row = legend.append("g").attr("transform", `translate(0,${i * 30})`);
  row
    .append("line")
    .attr("x1", 0)
    .attr("x2", 32)
    .attr("y1", 0)
    .attr("y2", 0)
    .attr("stroke", s.color)
    .attr("stroke-width", 3.5)
    .attr("stroke-dasharray", s.dash);
  row
    .append("text")
    .attr("x", 42)
    .attr("y", 5)
    .attr("fill", t.inkSoft)
    .style("font-size", "15px")
    .text(s.name);
});

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("frequency-polygon-basic · javascript · d3 · anyplot.ai");
