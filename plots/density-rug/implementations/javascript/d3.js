// anyplot.ai
// density-rug: Density Plot with Rug Marks
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 70, bottom: 110, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Reaction times (ms) pooled from two task-difficulty conditions, producing a
// mildly bimodal distribution — the kind of shape a KDE reveals but a
// histogram alone can obscure.
function lcg(seed) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}
function randomNormal(rng, mean, std) {
  let u = 0;
  let v = 0;
  while (u === 0) u = rng();
  while (v === 0) v = rng();
  return mean + std * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

const rng = lcg(42);
const easyTrials = Array.from({ length: 130 }, () => randomNormal(rng, 320, 36));
const hardTrials = Array.from({ length: 75 }, () => randomNormal(rng, 495, 50));
const reactionTimes = easyTrials.concat(hardTrials).filter((v) => v > 150 && v < 700);

// --- Kernel density estimate --------------------------------------------------
function kernelGaussian(bandwidth) {
  return (v) => Math.exp(-0.5 * (v / bandwidth) ** 2) / (bandwidth * Math.sqrt(2 * Math.PI));
}
function kernelDensityEstimator(kernel, sampleX) {
  return (sampleValues) => sampleX.map((xi) => [xi, d3.mean(sampleValues, (v) => kernel(xi - v))]);
}

const [dataMin, dataMax] = d3.extent(reactionTimes);
const domainPad = (dataMax - dataMin) * 0.08;

const x = d3.scaleLinear().domain([dataMin - domainPad, dataMax + domainPad]).nice().range([0, iw]);

// Silverman's rule of thumb for bandwidth selection.
const bandwidth = 1.06 * d3.deviation(reactionTimes) * Math.pow(reactionTimes.length, -0.2);
const density = kernelDensityEstimator(kernelGaussian(bandwidth), x.ticks(300))(reactionTimes);

const y = d3.scaleLinear().domain([0, d3.max(density, (d) => d[1]) * 1.12]).range([ih, 0]);

// The two reaction-time regimes (fast vs. slow trials) each carve out a local
// maximum in the KDE; find them so the chart can call them out directly
// instead of leaving the bimodality as a shape the viewer has to notice alone.
function findTwoPeaks(points, minSeparation) {
  const byDensity = points.slice().sort((a, b) => b[1] - a[1]);
  const first = byDensity[0];
  const second = byDensity.find((d) => Math.abs(d[0] - first[0]) > minSeparation);
  return [first, second].sort((a, b) => a[0] - b[0]);
}
const [fastPeak, slowPeak] = findTwoPeaks(density, (dataMax - dataMin) * 0.15);

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Axes -----------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(8));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(5).tickFormat(d3.format(".3f")));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  ax.selectAll("line").attr("stroke", t.grid);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Y-axis gridlines (subtle) ----------------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).ticks(5).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .call((sel) => sel.selectAll("line").attr("stroke", t.grid));

// --- KDE curve: gradient-filled area + line ----------------------------------
// A vertical fade (denser green at the baseline, airier near the peak) gives
// the fill more depth than a single flat fill-opacity, within the Imprint hue.
const gradientId = "density-fill-gradient";
svg
  .append("defs")
  .append("linearGradient")
  .attr("id", gradientId)
  .attr("x1", "0")
  .attr("x2", "0")
  .attr("y1", "0")
  .attr("y2", "1")
  .call((grad) => grad.append("stop").attr("offset", "0%").attr("stop-color", t.palette[0]).attr("stop-opacity", 0.08))
  .call((grad) => grad.append("stop").attr("offset", "100%").attr("stop-color", t.palette[0]).attr("stop-opacity", 0.4));

const area = d3
  .area()
  .x((d) => x(d[0]))
  .y0(ih)
  .y1((d) => y(d[1]))
  .curve(d3.curveBasis);
const line = d3
  .line()
  .x((d) => x(d[0]))
  .y((d) => y(d[1]))
  .curve(d3.curveBasis);

g.append("path").datum(density).attr("d", area).attr("fill", `url(#${gradientId})`);
g.append("path")
  .datum(density)
  .attr("d", line)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 3.5);

// --- Peak annotations: name the two reaction-time regimes --------------------
const peakLabels = [
  { peak: fastPeak, text: "Fast trials" },
  { peak: slowPeak, text: "Slow trials" },
];
g.selectAll(".peak-marker")
  .data(peakLabels)
  .join("circle")
  .attr("class", "peak-marker")
  .attr("cx", (d) => x(d.peak[0]))
  .attr("cy", (d) => y(d.peak[1]))
  .attr("r", 4.5)
  .attr("fill", t.palette[0]);
g.selectAll(".peak-label")
  .data(peakLabels)
  .join("text")
  .attr("class", "peak-label")
  .attr("x", (d) => x(d.peak[0]))
  .attr("y", (d) => y(d.peak[1]) - 16)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "15px")
  .style("font-style", "italic")
  .text((d) => d.text);

// --- Rug marks: exact observation locations along the x-axis -----------------
// Short ticks placed at a deterministically jittered vertical position within
// the rug band (the spec's own suggestion) instead of one line per point
// spanning the full band — this staggers observations that share nearly the
// same x pixel so they read as distinct marks instead of a solid dark block.
const rugBandHeight = 22;
const tickLength = 6;
const jitterRng = lcg(7);
const rugData = reactionTimes.map((value) => ({ value, jitter: jitterRng() }));
g.append("g")
  .selectAll("line")
  .data(rugData)
  .join("line")
  .attr("x1", (d) => x(d.value))
  .attr("x2", (d) => x(d.value))
  .attr("y1", (d) => ih - d.jitter * (rugBandHeight - tickLength))
  .attr("y2", (d) => ih - d.jitter * (rugBandHeight - tickLength) - tickLength)
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 1.5)
  .attr("stroke-opacity", 0.4);

// --- Axis labels --------------------------------------------------------------
svg
  .append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", height - 30)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "20px")
  .text("Reaction Time (ms)");

svg
  .append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -(margin.top + ih / 2))
  .attr("y", 40)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "20px")
  .text("Density");

// --- Title ----------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "28px")
  .style("font-weight", "600")
  .text("density-rug · javascript · d3 · anyplot.ai");
