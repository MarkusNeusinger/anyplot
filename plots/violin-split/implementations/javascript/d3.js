// anyplot.ai
// violin-split: Split Violin Plot
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-09
//# anyplot-orientation: landscape
// anyplot.ai
// violin-split: Split Violin Plot
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 100, right: 220, bottom: 90, left: 90 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Deterministic PRNG (LCG) + Box-Muller normal sampler -------------------
function makeRng(seed) {
  let state = seed >>> 0;
  return function () {
    state = (1103515245 * state + 12345) >>> 0;
    return state / 4294967296;
  };
}
const rng = makeRng(42);
function randNormal(mean, std) {
  const u1 = Math.max(rng(), 1e-9);
  const u2 = rng();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}
function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

// --- Data: midterm vs final exam scores across five courses -----------------
const COURSES = [
  { name: "Algebra", midterm: [68, 12], final: [76, 10] },
  { name: "Biology", midterm: [74, 9], final: [79, 8] },
  { name: "Chemistry", midterm: [63, 14], final: [70, 13] },
  { name: "Physics", midterm: [58, 15], final: [67, 14] },
  { name: "Statistics", midterm: [71, 10], final: [75, 9] },
];
const N = 220;
const courses = COURSES.map((c) => ({
  name: c.name,
  midterm: Array.from({ length: N }, () => clamp(randNormal(c.midterm[0], c.midterm[1]), 0, 100)),
  final: Array.from({ length: N }, () => clamp(randNormal(c.final[0], c.final[1]), 0, 100)),
}));

// --- Kernel density estimate (Gaussian kernel, Silverman bandwidth) ---------
const GRID = d3.range(0, 100.001, 100 / 140);
function kde(sample) {
  const std = d3.deviation(sample);
  const bw = 1.06 * std * Math.pow(sample.length, -0.2);
  return GRID.map((x) => ({
    x,
    density: d3.mean(sample, (v) => {
      const u = (x - v) / bw;
      return Math.exp(-0.5 * u * u) / (bw * Math.sqrt(2 * Math.PI));
    }),
  }));
}
for (const c of courses) {
  c.midtermKde = kde(c.midterm);
  c.finalKde = kde(c.final);
}
const maxDensity = d3.max(courses, (c) =>
  Math.max(d3.max(c.midtermKde, (d) => d.density), d3.max(c.finalKde, (d) => d.density))
);

function quartiles(sample) {
  const sorted = [...sample].sort(d3.ascending);
  return {
    q1: d3.quantileSorted(sorted, 0.25),
    median: d3.quantileSorted(sorted, 0.5),
    q3: d3.quantileSorted(sorted, 0.75),
  };
}

// --- Scales -------------------------------------------------------------
const x = d3.scaleBand().domain(courses.map((c) => c.name)).range([0, iw]).padding(0.38);
const y = d3.scaleLinear().domain([0, 100]).nice().range([ih, 0]);
const halfWidth = (x.bandwidth() / 2) * 0.88;
const widthScale = d3.scaleLinear().domain([0, maxDensity]).range([0, halfWidth]);

// --- SVG mount --------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Y gridlines (drawn first, below the violins) ---------------------------
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

// --- Axes -------------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll(".tick line").remove();
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Split violin halves ------------------------------------------------
const areaLeft = d3.area().curve(d3.curveBasis).y((d) => y(d.x)).x0(0).x1((d) => -widthScale(d.density));
const areaRight = d3.area().curve(d3.curveBasis).y((d) => y(d.x)).x0(0).x1((d) => widthScale(d.density));

const violin = g
  .selectAll(".violin")
  .data(courses)
  .join("g")
  .attr("class", "violin")
  .attr("transform", (d) => `translate(${x(d.name) + x.bandwidth() / 2},0)`);

violin
  .append("path")
  .attr("d", (d) => areaLeft(d.midtermKde))
  .attr("fill", t.palette[0])
  .attr("fill-opacity", 0.85)
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 1.5);

violin
  .append("path")
  .attr("d", (d) => areaRight(d.finalKde))
  .attr("fill", t.palette[1])
  .attr("fill-opacity", 0.85)
  .attr("stroke", t.palette[1])
  .attr("stroke-width", 1.5);

// center seam where the two halves meet
violin
  .append("line")
  .attr("x1", 0)
  .attr("x2", 0)
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2);

// --- Inner quartile markers (median tick + IQR ticks) per half --------------
function drawQuartiles(sel, sample, sign) {
  const { q1, median, q3 } = quartiles(sample);
  sel
    .append("line")
    .attr("x1", 0)
    .attr("x2", sign * halfWidth * 0.42)
    .attr("y1", y(q1))
    .attr("y2", y(q1))
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 1.5);
  sel
    .append("line")
    .attr("x1", 0)
    .attr("x2", sign * halfWidth * 0.42)
    .attr("y1", y(q3))
    .attr("y2", y(q3))
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 1.5);
  sel
    .append("line")
    .attr("x1", 0)
    .attr("x2", sign * halfWidth * 0.6)
    .attr("y1", y(median))
    .attr("y2", y(median))
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 2.5);
}
violin.each(function (d) {
  const sel = d3.select(this);
  drawQuartiles(sel, d.midterm, -1);
  drawQuartiles(sel, d.final, 1);
});

// --- Legend -------------------------------------------------------------
const legendData = [
  { label: "Midterm", color: t.palette[0] },
  { label: "Final", color: t.palette[1] },
];
const legend = svg.append("g").attr("transform", `translate(${margin.left + iw + 40}, ${margin.top + 10})`);
const legendRows = legend
  .selectAll("g")
  .data(legendData)
  .join("g")
  .attr("transform", (d, i) => `translate(0, ${i * 34})`);
legendRows.append("rect").attr("width", 20).attr("height", 20).attr("rx", 3).attr("fill", (d) => d.color);
legendRows
  .append("text")
  .attr("x", 28)
  .attr("y", 15)
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text((d) => d.label);

// --- Axis labels --------------------------------------------------------
svg
  .append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", height - 24)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Course");

svg
  .append("text")
  .attr("transform", `translate(28, ${margin.top + ih / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Exam Score (%)");

// --- Title --------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("violin-split · javascript · d3 · anyplot.ai");
