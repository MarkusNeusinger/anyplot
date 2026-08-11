// anyplot.ai
// bland-altman-basic: Bland-Altman Agreement Plot
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: 85/100 | Created: 2026-08-11

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 190, bottom: 90, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic LCG + Box-Muller) -----------------------
function lcg(seed) {
  let state = seed;
  return function () {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = lcg(42);
function randNormal() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// Systolic blood pressure (mmHg) from a reference sphygmomanometer vs. a
// test cuff, with a small proportional bias plus measurement noise.
const nPairs = 100;
const reference = [];
const testCuff = [];
for (let i = 0; i < nPairs; i++) {
  const systolic = 120 + 15 * randNormal();
  const bias = 3;
  const proportionalError = 0.02 * (systolic - 120);
  const noise = 6 * randNormal();
  reference.push(systolic);
  testCuff.push(systolic + bias + proportionalError + noise);
}

const pairs = reference.map((v, i) => ({
  mean: (v + testCuff[i]) / 2,
  diff: v - testCuff[i],
}));
const diffs = pairs.map((d) => d.diff);
const meanDiff = d3.mean(diffs);
const sdDiff = d3.deviation(diffs);
const upperLoA = meanDiff + 1.96 * sdDiff;
const lowerLoA = meanDiff - 1.96 * sdDiff;

// --- SVG mount ----------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales ---------------------------------------------------------------
const x = d3.scaleLinear().domain(d3.extent(pairs, (d) => d.mean)).nice().range([0, iw]);
const yMin = Math.min(d3.min(diffs), lowerLoA);
const yMax = Math.max(d3.max(diffs), upperLoA);
const yPad = (yMax - yMin) * 0.12;
const y = d3.scaleLinear().domain([yMin - yPad, yMax + yPad]).nice().range([ih, 0]);

// --- Agreement-zone band (behind gridlines/points, frames ±1.96 SD) --------
g.append("rect")
  .attr("x", 0)
  .attr("y", y(upperLoA))
  .attr("width", iw)
  .attr("height", y(lowerLoA) - y(upperLoA))
  .attr("fill", t.ink)
  .attr("fill-opacity", 0.05);

// --- Gridlines (both axes, subtle) -----------------------------------------
g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).tickSize(-ih).tickFormat(""))
  .selectAll("line")
  .attr("stroke", t.grid);
g.append("g")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .selectAll("line")
  .attr("stroke", t.grid);
g.selectAll(".domain").remove();

// --- Axes -------------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x));
const yAxis = g.append("g").call(d3.axisLeft(y));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "15px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Limits-of-agreement reference lines ------------------------------------
g.append("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", y(meanDiff))
  .attr("y2", y(meanDiff))
  .attr("stroke", t.ink)
  .attr("stroke-width", 2.5);

for (const loa of [upperLoA, lowerLoA]) {
  g.append("line")
    .attr("x1", 0)
    .attr("x2", iw)
    .attr("y1", y(loa))
    .attr("y2", y(loa))
    .attr("stroke", t.ink)
    .attr("stroke-width", 2)
    .attr("stroke-dasharray", "9,6")
    .attr("opacity", 0.7);
}

// --- Annotations (mean bias + limits of agreement) --------------------------
const annotations = [
  { y: meanDiff, label: `Bias: ${meanDiff.toFixed(1)} mmHg` },
  { y: upperLoA, label: `+1.96 SD: ${upperLoA.toFixed(1)}` },
  { y: lowerLoA, label: `−1.96 SD: ${lowerLoA.toFixed(1)}` },
];
g.selectAll(".loa-label")
  .data(annotations)
  .join("text")
  .attr("x", iw + 12)
  .attr("y", (d) => y(d.y))
  .attr("dy", "0.35em")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text((d) => d.label);

// --- Points (out-of-limit observations flagged in amber) -------------------
const outOfLimits = (d) => d.diff > upperLoA || d.diff < lowerLoA;
g.selectAll("circle")
  .data(pairs)
  .join("circle")
  .attr("cx", (d) => x(d.mean))
  .attr("cy", (d) => y(d.diff))
  .attr("r", (d) => (outOfLimits(d) ? 9 : 7))
  .attr("fill", (d) => (outOfLimits(d) ? t.amber : t.palette[0]))
  .attr("fill-opacity", (d) => (outOfLimits(d) ? 0.85 : 0.55))
  .attr("stroke", (d) => (outOfLimits(d) ? t.ink : t.pageBg))
  .attr("stroke-width", (d) => (outOfLimits(d) ? 1.5 : 1));

// --- Axis labels --------------------------------------------------------
svg
  .append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", height - 28)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .text("Mean of Two Methods (mmHg)");

svg
  .append("text")
  .attr("transform", `translate(${34},${margin.top + ih / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .text("Difference: Reference − Test Cuff (mmHg)");

// --- Title ----------------------------------------------------------------
const title = "Blood Pressure Cuff Comparison · bland-altman-basic · javascript · d3 · anyplot.ai";
const titleFontSize = title.length > 67 ? Math.round(22 * (67 / title.length)) : 22;
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 46)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(title);
