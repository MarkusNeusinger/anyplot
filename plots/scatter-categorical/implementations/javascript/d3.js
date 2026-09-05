// anyplot.ai
// scatter-categorical: Categorical Scatter Plot
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 260, bottom: 90, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic fixed-seed LCG) -------------------------
let seed = 42;
function rand() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function randNormal(mean, sd) {
  const u1 = rand() || 1e-9;
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * sd;
}

const species = [
  { name: "Adelie", flipperMean: 190, flipperSd: 6.5, massMean: 3700, massSd: 450, n: 45 },
  { name: "Chinstrap", flipperMean: 196, flipperSd: 7, massMean: 3730, massSd: 380, n: 40 },
  { name: "Gentoo", flipperMean: 217, flipperSd: 6, massMean: 5100, massSd: 500, n: 42 },
];

const points = [];
for (const s of species) {
  for (let i = 0; i < s.n; i++) {
    points.push({
      flipperLength: randNormal(s.flipperMean, s.flipperSd),
      bodyMass: randNormal(s.massMean, s.massSd),
      species: s.name,
    });
  }
}

const categories = species.map((s) => s.name);
const color = d3.scaleOrdinal().domain(categories).range(t.palette);

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales ---------------------------------------------------------------
const x = d3
  .scaleLinear()
  .domain(d3.extent(points, (d) => d.flipperLength)).nice()
  .range([0, iw]);
const y = d3
  .scaleLinear()
  .domain(d3.extent(points, (d) => d.bodyMass)).nice()
  .range([ih, 0]);

// --- Gridlines --------------------------------------------------------------
g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(8).tickSize(-ih).tickFormat(""))
  .selectAll("line")
  .attr("stroke", t.grid);
g.append("g")
  .call(d3.axisLeft(y).ticks(7).tickSize(-iw).tickFormat(""))
  .selectAll("line")
  .attr("stroke", t.grid);
g.selectAll(".domain").remove();

// --- Axes ---------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(8));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(7));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels --------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Flipper Length (mm)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -80)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Body Mass (g)");

// --- Points ---------------------------------------------------------------
g.selectAll("circle")
  .data(points)
  .join("circle")
  .attr("cx", (d) => x(d.flipperLength))
  .attr("cy", (d) => y(d.bodyMass))
  .attr("r", 6.5)
  .attr("fill", (d) => color(d.species))
  .attr("fill-opacity", 0.65)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1);

// --- Centroid markers (data storytelling: per-species mean) -----------------
// d3-shape symbol generator, not just circles — highlights each species'
// average flipper length / body mass as a focal point above the raw cloud.
const diamond = d3.symbol().type(d3.symbolDiamond).size(450);
const centroids = species.map((s) => {
  const speciesPoints = points.filter((d) => d.species === s.name);
  return {
    name: s.name,
    flipperLength: d3.mean(speciesPoints, (d) => d.flipperLength),
    bodyMass: d3.mean(speciesPoints, (d) => d.bodyMass),
  };
});

g.selectAll(".centroid")
  .data(centroids)
  .join("path")
  .attr("class", "centroid")
  .attr("d", diamond)
  .attr("transform", (d) => `translate(${x(d.flipperLength)},${y(d.bodyMass)})`)
  .attr("fill", (d) => color(d.name))
  .attr("stroke", t.ink)
  .attr("stroke-width", 2.5);

// --- Legend -----------------------------------------------------------------
const legend = svg
  .append("g")
  .attr("transform", `translate(${margin.left + iw + 50},${margin.top + 20})`);

categories.forEach((name, i) => {
  const row = legend.append("g").attr("transform", `translate(0,${i * 36})`);
  row.append("circle").attr("r", 9).attr("fill", color(name)).attr("fill-opacity", 0.75);
  row
    .append("text")
    .attr("x", 20)
    .attr("y", 5)
    .attr("fill", t.ink)
    .style("font-size", "16px")
    .text(name);
});

const legendNote = legend
  .append("g")
  .attr("transform", `translate(0,${categories.length * 36 + 14})`);
legendNote
  .append("path")
  .attr("d", d3.symbol().type(d3.symbolDiamond).size(220))
  .attr("fill", t.inkSoft)
  .attr("stroke", t.ink)
  .attr("stroke-width", 1.5);
legendNote
  .append("text")
  .attr("x", 20)
  .attr("y", 5)
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Species mean");

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("scatter-categorical · javascript · d3 · anyplot.ai");
