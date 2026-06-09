// anyplot.ai
// pp-basic: Probability-Probability (P-P) Plot
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-09

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (deterministic LCG, no browser RNG) ---
let seed = 42;
function rand() {
  seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
  return seed / 4294967296;
}
function randn() {
  const u = rand() || 1e-10;
  const v = rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// 200 samples from a slightly right-skewed distribution (normal + quadratic term)
// Context: manufacturing process measurements — testing normality assumption
const N = 200;
const raw = Array.from({ length: N }, () => {
  const z = randn();
  return z + 0.45 * z * z - 0.45; // right-skewed, bias-corrected
});

// Fit normal parameters to the sample
const sampleMean = raw.reduce((a, b) => a + b, 0) / N;
const sampleStd = Math.sqrt(raw.reduce((s, x) => s + (x - sampleMean) ** 2, 0) / (N - 1));

// Sort and compute empirical CDF (Hazen plotting position: (i + 0.5) / N)
const sorted = [...raw].sort((a, b) => a - b);
const empirical = sorted.map((_, i) => (i + 0.5) / N);

// Normal CDF via error function approximation (Abramowitz & Stegun 7.1.26)
function erf(z) {
  const a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741;
  const a4 = -1.453152027, a5 = 1.061405429, q = 0.3275911;
  const sign = z < 0 ? -1 : 1;
  const ta = 1 / (1 + q * Math.abs(z));
  const y = 1 - (((((a5 * ta + a4) * ta + a3) * ta + a2) * ta + a1) * ta) * Math.exp(-z * z);
  return sign * y;
}
function normCDF(x, mu, sigma) {
  return 0.5 * (1 + erf((x - mu) / (sigma * Math.SQRT2)));
}

const theoretical = sorted.map((val) => normCDF(val, sampleMean, sampleStd));
const points = theoretical.map((th, i) => ({ th, em: empirical[i] }));

// --- Layout ---
const margin = { top: 95, right: 70, bottom: 110, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);

const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales ---
const x = d3.scaleLinear().domain([0, 1]).range([0, iw]);
const y = d3.scaleLinear().domain([0, 1]).range([ih, 0]);

// --- Gridlines (both axes for scatter) ---
g.append("g")
  .selectAll("line")
  .data(x.ticks(5))
  .join("line")
  .attr("x1", (d) => x(d))
  .attr("x2", (d) => x(d))
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

g.append("g")
  .selectAll("line")
  .data(y.ticks(5))
  .join("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", (d) => y(d))
  .attr("y2", (d) => y(d))
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- 45-degree reference line (perfect fit) ---
g.append("line")
  .attr("x1", x(0))
  .attr("y1", y(0))
  .attr("x2", x(1))
  .attr("y2", y(1))
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 2.5)
  .attr("stroke-dasharray", "10,7")
  .attr("opacity", 0.75);

// --- Data points ---
g.selectAll("circle")
  .data(points)
  .join("circle")
  .attr("cx", (d) => x(d.th))
  .attr("cy", (d) => y(d.em))
  .attr("r", 5.5)
  .attr("fill", t.palette[0])
  .attr("opacity", 0.72)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1);

// --- Axes ---
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(5).tickFormat(d3.format(".1f")));

const yAxis = g.append("g").call(d3.axisLeft(y).ticks(5).tickFormat(d3.format(".1f")));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  ax.select(".domain").attr("stroke", t.inkSoft);
  ax.selectAll(".tick line").remove();
}

// --- Axis labels ---
svg
  .append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", height - 22)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Theoretical Normal Probability");

svg
  .append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -(margin.top + ih / 2))
  .attr("y", 28)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Empirical Probability");

// --- Title ---
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("pp-basic · javascript · d3 · anyplot.ai");
