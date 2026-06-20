// anyplot.ai
// lightcurve-transit: Astronomical Light Curve
// Library: d3 7.9.0 | JavaScript 22.22.3
// Quality: 84/100 | Created: 2026-06-20

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 80, right: 80, bottom: 100, left: 120 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Deterministic LCG (seed 42) — browser has no seeded RNG
let _seed = 42;
function lcg() {
  _seed = ((_seed * 1664525) + 1013904223) >>> 0;
  return _seed / 0x100000000;
}
function randn() {
  return Math.sqrt(-2 * Math.log(lcg() + 1e-10)) * Math.cos(2 * Math.PI * lcg());
}

// Transit model: trapezoidal shape with limb-darkening curvature
function transitFlux(phase) {
  const tc = 0.5, halfDur = 0.065, depth = 0.011;
  const phi = Math.abs(phase - tc);
  if (phi > halfDur) return 1.0;
  const u = phi / halfDur;
  const depthHere = depth * (1 - 0.15 * u * u);
  const ingressZone = 0.25;
  if (u > 1 - ingressZone) {
    const s = (1 - u) / ingressZone;
    return 1.0 - depthHere * s * s * (3 - 2 * s);
  }
  return 1.0 - depthHere;
}

// Phase-folded observations: 450 points with Gaussian photometric noise
const N = 450;
const obs = Array.from({ length: N }, (_, i) => {
  const phase = i / N;
  const model = transitFlux(phase);
  const fluxErr = 0.0025 + lcg() * 0.0010;
  const flux = model + randn() * 0.0030;
  return { phase, flux, fluxErr };
});

// Smooth model curve (1001 points for clean line rendering)
const modelCurve = Array.from({ length: 1001 }, (_, i) => ({
  phase: i / 1000,
  flux: transitFlux(i / 1000),
}));

// SVG
const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Scales
const xScale = d3.scaleLinear().domain([0, 1]).range([0, iw]);
const yMin = d3.min(obs, (d) => d.flux - d.fluxErr) - 0.002;
const yScale = d3.scaleLinear().domain([yMin, 1.009]).nice().range([ih, 0]);

// Horizontal grid lines (y-axis only, subtle)
yScale.ticks(6).forEach((tick) => {
  g.append("line")
    .attr("x1", 0)
    .attr("x2", iw)
    .attr("y1", yScale(tick))
    .attr("y2", yScale(tick))
    .attr("stroke", t.grid)
    .attr("stroke-width", 1);
});

// Error bars (drawn before points so points sit on top)
g.append("g")
  .selectAll("line")
  .data(obs)
  .join("line")
  .attr("x1", (d) => xScale(d.phase))
  .attr("x2", (d) => xScale(d.phase))
  .attr("y1", (d) => yScale(d.flux - d.fluxErr))
  .attr("y2", (d) => yScale(d.flux + d.fluxErr))
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 0.9)
  .attr("opacity", 0.45);

// Data points — Imprint palette[0] (#009E73) as first series
g.append("g")
  .selectAll("circle")
  .data(obs)
  .join("circle")
  .attr("cx", (d) => xScale(d.phase))
  .attr("cy", (d) => yScale(d.flux))
  .attr("r", 2.5)
  .attr("fill", t.palette[0])
  .attr("opacity", 0.80);

// Transit model curve — Imprint palette[1] (#C475FD)
const lineGen = d3
  .line()
  .x((d) => xScale(d.phase))
  .y((d) => yScale(d.flux));
g.append("path")
  .datum(modelCurve)
  .attr("fill", "none")
  .attr("stroke", t.palette[1])
  .attr("stroke-width", 2.5)
  .attr("d", lineGen);

// Axes
const xAxis = d3.axisBottom(xScale).ticks(5).tickFormat(d3.format(".1f"));
const yAxis = d3.axisLeft(yScale).ticks(6).tickFormat(d3.format(".3f"));

const gx = g.append("g").attr("transform", `translate(0,${ih})`).call(xAxis);
const gy = g.append("g").call(yAxis);

for (const ax of [gx, gy]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.grid);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// Axis labels
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 68)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Orbital Phase");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -(ih / 2))
  .attr("y", -88)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Relative Flux");

// Legend
const lx = iw - 200, ly = 30;
g.append("circle")
  .attr("cx", lx)
  .attr("cy", ly)
  .attr("r", 5)
  .attr("fill", t.palette[0])
  .attr("opacity", 0.80);
g.append("text")
  .attr("x", lx + 14)
  .attr("y", ly + 5)
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Observations");

g.append("line")
  .attr("x1", lx - 8)
  .attr("x2", lx + 8)
  .attr("y1", ly + 30)
  .attr("y2", ly + 30)
  .attr("stroke", t.palette[1])
  .attr("stroke-width", 2.5);
g.append("text")
  .attr("x", lx + 14)
  .attr("y", ly + 35)
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Transit Model");

// Title
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("lightcurve-transit · javascript · d3 · anyplot.ai");
