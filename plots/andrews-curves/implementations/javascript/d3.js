// anyplot.ai
// andrews-curves: Andrews Curves for Multivariate Data
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 210, bottom: 90, left: 100 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: synthetic iris-like measurements (4 variables, 3 species) -------
// Deterministic LCG (the browser has no seeded Math.random) drives a
// Box-Muller transform so each species clusters around realistic means.
let seed = 42;
function lcg() {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
}
function gaussian(mean, std) {
  const u1 = lcg() || 1e-9;
  const u2 = lcg();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

const species = [
  { name: "setosa", n: 30, means: [5.0, 3.4, 1.5, 0.2], stds: [0.35, 0.38, 0.17, 0.11] },
  { name: "versicolor", n: 30, means: [5.9, 2.8, 4.3, 1.3], stds: [0.52, 0.31, 0.47, 0.2] },
  { name: "virginica", n: 30, means: [6.6, 3.0, 5.6, 2.0], stds: [0.64, 0.32, 0.55, 0.27] },
];

const observations = [];
for (const sp of species) {
  for (let i = 0; i < sp.n; i++) {
    observations.push({
      species: sp.name,
      values: sp.means.map((m, j) => gaussian(m, sp.stds[j])),
    });
  }
}

// Standardize each variable (z-score) so no single measurement dominates
const dims = observations[0].values.length;
for (let j = 0; j < dims; j++) {
  const col = observations.map((o) => o.values[j]);
  const mean = d3.mean(col);
  const std = d3.deviation(col);
  observations.forEach((o) => (o.values[j] = (o.values[j] - mean) / std));
}

// --- Andrews curve: x1/sqrt(2) + x2 sin(t) + x3 cos(t) + x4 sin(2t) --------
function andrews(tt, v) {
  return v[0] / Math.SQRT2 + v[1] * Math.sin(tt) + v[2] * Math.cos(tt) + v[3] * Math.sin(2 * tt);
}

const N_SAMPLES = 120;
const tSamples = d3.range(N_SAMPLES + 1).map((i) => -Math.PI + (2 * Math.PI * i) / N_SAMPLES);

const curves = observations.map((o) => ({
  species: o.species,
  points: tSamples.map((tt) => ({ t: tt, value: andrews(tt, o.values) })),
}));

const yExtent = d3.extent(curves.flatMap((c) => c.points.map((p) => p.value)));
const yPad = (yExtent[1] - yExtent[0]) * 0.08;

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const x = d3.scaleLinear().domain([-Math.PI, Math.PI]).range([0, iw]);
const y = d3
  .scaleLinear()
  .domain([yExtent[0] - yPad, yExtent[1] + yPad])
  .nice()
  .range([ih, 0]);
const color = d3
  .scaleOrdinal()
  .domain(species.map((s) => s.name))
  .range(t.palette);

// --- Gridlines (y-axis only) -------------------------------------------------
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

// --- Axes -----------------------------------------------------------------
const piTicks = [-Math.PI, -Math.PI / 2, 0, Math.PI / 2, Math.PI];
const piLabels = ["-π", "-π/2", "0", "π/2", "π"];
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(
    d3
      .axisBottom(x)
      .tickValues(piTicks)
      .tickFormat((d, i) => piLabels[i])
      .tickSizeOuter(0)
  );
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6).tickSizeOuter(0));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.select(".domain").attr("stroke", t.inkSoft);
}
xAxis.selectAll(".tick line").remove();
yAxis.selectAll(".tick line").remove();

// --- Axis labels -------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 58)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("t (Fourier parameter)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -72)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("f(t)");

// --- Curves --------------------------------------------------------------
const line = d3
  .line()
  .x((d) => x(d.t))
  .y((d) => y(d.value));

g.selectAll("path.curve")
  .data(curves)
  .join("path")
  .attr("class", "curve")
  .attr("d", (d) => line(d.points))
  .attr("fill", "none")
  .attr("stroke", (d) => color(d.species))
  .attr("stroke-width", 1.4)
  .attr("stroke-opacity", 0.45);

// --- Legend ------------------------------------------------------------------
const legend = svg
  .append("g")
  .attr("transform", `translate(${margin.left + iw + 40},${margin.top + 20})`);
species.forEach((sp, i) => {
  const row = legend.append("g").attr("transform", `translate(0,${i * 34})`);
  row
    .append("rect")
    .attr("width", 18)
    .attr("height", 18)
    .attr("rx", 3)
    .attr("fill", color(sp.name));
  row
    .append("text")
    .attr("x", 26)
    .attr("y", 14)
    .attr("fill", t.inkSoft)
    .style("font-size", "14px")
    .text(sp.name[0].toUpperCase() + sp.name.slice(1));
});

// --- Title ---------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("andrews-curves · javascript · d3 · anyplot.ai");
