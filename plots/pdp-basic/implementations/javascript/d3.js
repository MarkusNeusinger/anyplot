// anyplot.ai
// pdp-basic: Partial Dependence Plot
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 70, bottom: 130, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Deterministic PRNG (mulberry32, fixed seed) ----------------------------
function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let x = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}
function randNormal(rand) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// --- Data: PDP of house price on living area, from a gradient boosting model
const rand = mulberry32(42);
const xMin = 800;
const xMax = 4000;
const gridSize = 70;
const featureValues = d3.range(gridSize).map((i) => xMin + (i / (gridSize - 1)) * (xMax - xMin));

// Saturating price response with a mild boosting-style wiggle, then centered at zero.
const centerX = (xMin + xMax) / 2;
const halfRange = (xMax - xMin) / 2;
const rawDependence = featureValues.map(
  (x) => 165 * Math.log(x / xMin) + 4 * Math.sin((x - xMin) / 240)
);
const baseline = d3.mean(rawDependence);
const partialDependence = rawDependence.map((v) => v - baseline);

// Confidence band widens toward the sparser edges of the feature range.
const ciHalfWidth = featureValues.map(
  (x) => 3 + 22 * Math.pow(Math.abs(x - centerX) / halfRange, 1.8)
);
const ciLower = partialDependence.map((v, i) => v - ciHalfWidth[i]);
const ciUpper = partialDependence.map((v, i) => v + ciHalfWidth[i]);

// Rug: training sample of feature values (approx. normal, clipped to range).
const rugValues = d3.range(140).map(() => {
  const v = 1900 + 480 * randNormal(rand);
  return Math.max(xMin, Math.min(xMax, v));
});

// --- Scales -------------------------------------------------------------
const x = d3.scaleLinear().domain([xMin, xMax]).range([0, iw]);
const y = d3
  .scaleLinear()
  .domain([d3.min(ciLower), d3.max(ciUpper)])
  .nice()
  .range([ih, 0]);

// --- SVG mount ------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Zero reference line — the PDP is centered, so this marks "no effect vs. average".
g.append("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", y(0))
  .attr("y2", y(0))
  .attr("stroke", t.grid)
  .attr("stroke-width", 1.5)
  .attr("stroke-dasharray", "6,5");

// Confidence band
const area = d3
  .area()
  .x((d, i) => x(featureValues[i]))
  .y0((d, i) => y(ciLower[i]))
  .y1((d, i) => y(ciUpper[i]))
  .curve(d3.curveMonotoneX);
g.append("path").datum(featureValues).attr("d", area).attr("fill", t.palette[0]).attr("fill-opacity", 0.16);

// Partial dependence curve
const line = d3
  .line()
  .x((d, i) => x(featureValues[i]))
  .y((d, i) => y(partialDependence[i]))
  .curve(d3.curveMonotoneX);
g.append("path")
  .datum(featureValues)
  .attr("d", line)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 4);

// Rug plot — distribution of observed feature values along the x-axis
g.selectAll(".rug")
  .data(rugValues)
  .join("line")
  .attr("class", "rug")
  .attr("x1", (d) => x(d))
  .attr("x2", (d) => x(d))
  .attr("y1", ih + 34)
  .attr("y2", ih + 48)
  .attr("stroke", t.inkSoft)
  .attr("stroke-opacity", 0.5)
  .attr("stroke-width", 1.5);

// Direct label for the shaded band (single series → no legend needed)
g.append("text")
  .attr("x", iw)
  .attr("y", y(ciUpper[ciUpper.length - 1]) - 12)
  .attr("text-anchor", "end")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("90% prediction interval");

// --- Axes -----------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(6).tickFormat(d3.format(",")));
const yAxis = g.append("g").call(
  d3
    .axisLeft(y)
    .ticks(6)
    .tickFormat((d) => (d > 0 ? "+" : "") + d3.format(",")(d))
);
for (const axis of [xAxis, yAxis]) {
  axis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  axis.selectAll("line").attr("stroke", t.grid);
  axis.select(".domain").attr("stroke", t.inkSoft);
}
xAxis.selectAll(".tick line").attr("y2", 0);
yAxis.selectAll(".tick line").attr("x2", 0);

// --- Axis labels ------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 70)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .text("Living Area (sq ft)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -80)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .text("Partial Dependence (Δ Predicted Price, $k)");

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 46)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("pdp-basic · javascript · d3 · anyplot.ai");
