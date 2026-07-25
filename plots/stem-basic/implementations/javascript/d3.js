// anyplot.ai
// stem-basic: Basic Stem Plot
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-07-25
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 60, bottom: 90, left: 100 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Discrete-time impulse response of a damped oscillator: h[n] = e^(-0.15n) * cos(0.5n)
const sampleCount = 40;
const envelope = (n) => Math.exp(-0.15 * n);
const data = Array.from({ length: sampleCount }, (_, n) => ({
  n,
  amplitude: envelope(n) * Math.cos(0.5 * n),
}));

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const x = d3
  .scaleLinear()
  .domain([d3.min(data, (d) => d.n) - 1, d3.max(data, (d) => d.n) + 1])
  .range([0, iw]);
const y = d3
  .scaleLinear()
  .domain(d3.extent(data, (d) => d.amplitude))
  .nice()
  .range([ih, 0]);
// Marker radius tied to |amplitude|: the decaying envelope reads directly
// through marker prominence, not just vertical position.
const r = d3.scaleLinear().domain([0, 1]).range([5.5, 11]).clamp(true);

// --- Decay-envelope guide (d3-shape line generator) -----------------------------
// A thin dashed guide along +/- e^(-0.15n) gives the reader an immediate read
// on the envelope the stems are riding, rather than leaving it implicit.
const envelopeLine = d3
  .line()
  .curve(d3.curveMonotoneX)
  .x((d) => x(d.n))
  .y((d) => y(d.value));
const upperEnvelope = data.map((d) => ({ n: d.n, value: envelope(d.n) }));
const lowerEnvelope = data.map((d) => ({ n: d.n, value: -envelope(d.n) }));
for (const env of [upperEnvelope, lowerEnvelope]) {
  g.append("path")
    .datum(env)
    .attr("fill", "none")
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1.25)
    .attr("stroke-dasharray", "5,4")
    .attr("stroke-opacity", 0.35)
    .attr("d", envelopeLine);
}

// --- Baseline (y = 0) ----------------------------------------------------------
g.append("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", y(0))
  .attr("y2", y(0))
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1.5);

// --- Stems ----------------------------------------------------------------------
// Positive samples render at full opacity; negative samples are slightly
// dimmed, so the sign transition of the oscillation is visible at a glance.
g.selectAll(".stem")
  .data(data)
  .join("line")
  .attr("class", "stem")
  .attr("x1", (d) => x(d.n))
  .attr("x2", (d) => x(d.n))
  .attr("y1", y(0))
  .attr("y2", (d) => y(d.amplitude))
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 2.5)
  .attr("stroke-opacity", (d) => (d.amplitude >= 0 ? 1 : 0.55));

// --- Markers ----------------------------------------------------------------------
g.selectAll(".marker")
  .data(data)
  .join("circle")
  .attr("class", "marker")
  .attr("cx", (d) => x(d.n))
  .attr("cy", (d) => y(d.amplitude))
  .attr("r", (d) => r(Math.abs(d.amplitude)))
  .attr("fill", t.palette[0])
  .attr("fill-opacity", (d) => (d.amplitude >= 0 ? 1 : 0.55))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

// --- Axes -------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(10).tickFormat(d3.format("d")));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(8));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.grid);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels --------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Sample Index (n)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -70)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Amplitude");

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("stem-basic · javascript · d3 · anyplot.ai");
