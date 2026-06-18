// anyplot.ai
// eye-diagram-basic: Signal Integrity Eye Diagram
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-18

const tok = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 80, right: 70, bottom: 90, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Deterministic LCG RNG
let _rng = 42;
function rand() { _rng = (_rng * 1664525 + 1013904223) >>> 0; return _rng / 4294967296; }
function randn() {
  return Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
}

// Bandwidth-limited NRZ signal parameters
const N_TRACES = 400;
const SAMPLES = 160;
const NOISE_SIGMA = 0.05;
const JITTER_SIGMA = 0.03;
const BW = 0.15;

const sigmoid = x => 1 / (1 + Math.exp(-x / BW));

// Build all trace points: each trace is a 2-UI window with 3 random bits
const allPoints = [];
for (let i = 0; i < N_TRACES; i++) {
  const b0 = rand() > 0.5 ? 1 : 0;
  const b1 = rand() > 0.5 ? 1 : 0;
  const b2 = rand() > 0.5 ? 1 : 0;
  const j0 = randn() * JITTER_SIGMA;
  const j1 = randn() * JITTER_SIGMA;
  for (let s = 0; s < SAMPLES; s++) {
    const tm = (s / (SAMPLES - 1)) * 2;
    const v = b0
      + (b1 - b0) * sigmoid(tm - j0)
      + (b2 - b1) * sigmoid(tm - 1 - j1)
      + randn() * NOISE_SIGMA;
    allPoints.push([tm, v]);
  }
}

// 2D histogram: bin trace points for density heatmap
const BINS_X = 200;
const BINS_Y = 120;
const V_MIN = -0.25;
const V_MAX = 1.25;
const T_MIN = 0;
const T_MAX = 2;

const hist = new Int32Array(BINS_X * BINS_Y);
for (const [tm, v] of allPoints) {
  const bx = Math.floor(((tm - T_MIN) / (T_MAX - T_MIN)) * BINS_X);
  const by = Math.floor(((V_MAX - v) / (V_MAX - V_MIN)) * BINS_Y);
  if (bx >= 0 && bx < BINS_X && by >= 0 && by < BINS_Y) {
    hist[by * BINS_X + bx]++;
  }
}
const maxCount = Math.max(...hist);

// Color scale: page background → Imprint green → Imprint blue (sequential)
const colorScale = d3.scaleSequential()
  .domain([0, maxCount])
  .interpolator(d3.interpolateRgbBasis([tok.pageBg, tok.seq[0], tok.seq[1]]));

// SVG mount
const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);

// Clip path for plot area
svg.append("defs").append("clipPath").attr("id", "plotarea")
  .append("rect").attr("width", iw).attr("height", ih);

const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Density heatmap cells
const cellW = iw / BINS_X;
const cellH = ih / BINS_Y;
g.append("g").attr("clip-path", "url(#plotarea)")
  .selectAll("rect")
  .data(hist)
  .join("rect")
  .attr("x", (_, i) => (i % BINS_X) * cellW)
  .attr("y", (_, i) => Math.floor(i / BINS_X) * cellH)
  .attr("width", cellW + 0.6)
  .attr("height", cellH + 0.6)
  .attr("fill", d => colorScale(d));

// Linear scales for overlay elements
const xScale = d3.scaleLinear().domain([T_MIN, T_MAX]).range([0, iw]);
const yScale = d3.scaleLinear().domain([V_MIN, V_MAX]).range([ih, 0]);

// Dashed reference lines at nominal NRZ voltage levels (0 V and 1 V)
for (const level of [0, 1]) {
  g.append("line")
    .attr("x1", 0).attr("x2", iw)
    .attr("y1", yScale(level)).attr("y2", yScale(level))
    .attr("stroke", tok.inkSoft)
    .attr("stroke-dasharray", "8,5")
    .attr("stroke-opacity", 0.55)
    .attr("stroke-width", 1.5);
}

// Dashed vertical line at t = 1 UI (sampling instant / eye center)
g.append("line")
  .attr("x1", xScale(1)).attr("x2", xScale(1))
  .attr("y1", 0).attr("y2", ih)
  .attr("stroke", tok.inkSoft)
  .attr("stroke-dasharray", "8,5")
  .attr("stroke-opacity", 0.55)
  .attr("stroke-width", 1.5);

// Axes
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(xScale).ticks(5).tickFormat(d => `${d} UI`));
const yAxis = g.append("g")
  .call(d3.axisLeft(yScale).ticks(6).tickFormat(d => d.toFixed(1) + " V"));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", tok.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", tok.inkSoft).attr("stroke-opacity", 0.35);
  ax.select(".domain").attr("stroke", tok.inkSoft).attr("stroke-opacity", 0.5);
}

// Axis labels
g.append("text")
  .attr("x", iw / 2).attr("y", ih + 65)
  .attr("text-anchor", "middle")
  .attr("fill", tok.ink)
  .style("font-size", "16px")
  .text("Time (UI)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2).attr("y", -80)
  .attr("text-anchor", "middle")
  .attr("fill", tok.ink)
  .style("font-size", "16px")
  .text("Voltage (V)");

// Chart title
svg.append("text")
  .attr("x", width / 2).attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", tok.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("eye-diagram-basic · javascript · d3 · anyplot.ai");
