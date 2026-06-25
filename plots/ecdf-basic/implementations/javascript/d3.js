// anyplot.ai
// ecdf-basic: Basic ECDF Plot
// Library: d3 7.9.0 | JavaScript 22.22.3
// Quality: 90/100 | Created: 2026-06-25

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 80, right: 130, bottom: 80, left: 90 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Deterministic LCG + Box-Muller for reproducible normal samples
function makeLCG(seed) {
  let s = seed >>> 0;
  return () => { s = (Math.imul(1664525, s) + 1013904223) >>> 0; return s / 0x100000000; };
}

function normalSamples(n, mean, std, rng) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const u1 = Math.max(1e-12, rng());
    const u2 = rng();
    out.push(mean + std * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2));
  }
  return out.sort((a, b) => a - b);
}

const expressDelivery = normalSamples(160, 3.2, 0.6, makeLCG(42));
const standardDelivery = normalSamples(160, 4.8, 1.3, makeLCG(137));

// Build ECDF step points: prepend (xStart, 0) so the line starts from 0 at left
function ecdfPoints(sorted, xStart, xEnd) {
  const n = sorted.length;
  return [
    { x: xStart, y: 0 },
    ...sorted.map((v, i) => ({ x: v, y: (i + 1) / n })),
    { x: xEnd, y: 1 },
  ];
}

const allValues = [...expressDelivery, ...standardDelivery];
const pad = (d3.max(allValues) - d3.min(allValues)) * 0.04;
const xDomMin = d3.min(allValues) - pad;
const xDomMax = d3.max(allValues) + pad;

const expressECDF = ecdfPoints(expressDelivery, xDomMin, xDomMax);
const standardECDF = ecdfPoints(standardDelivery, xDomMin, xDomMax);

// SVG mount
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Scales
const x = d3.scaleLinear().domain([xDomMin, xDomMax]).range([0, iw]);
const y = d3.scaleLinear().domain([0, 1]).range([ih, 0]);

// Horizontal grid lines at quartile proportions
g.selectAll(".hgrid").data([0.25, 0.5, 0.75]).join("line")
  .attr("x1", 0).attr("x2", iw)
  .attr("y1", d => y(d)).attr("y2", d => y(d))
  .attr("stroke", t.grid).attr("stroke-width", 1);

// Axes
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(8).tickSize(5));
const yAxis = g.append("g")
  .call(d3.axisLeft(y).tickValues([0, 0.25, 0.5, 0.75, 1]).tickFormat(d3.format(".0%")).tickSize(5));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll(".tick line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// ECDF step lines — curveStepAfter matches ECDF semantics: step up AT each observation
const line = d3.line().x(d => x(d.x)).y(d => y(d.y)).curve(d3.curveStepAfter);

g.append("path").datum(expressECDF)
  .attr("fill", "none").attr("stroke", t.palette[0]).attr("stroke-width", 3).attr("d", line);

g.append("path").datum(standardECDF)
  .attr("fill", "none").attr("stroke", t.palette[1]).attr("stroke-width", 3).attr("d", line);

// Axis labels
svg.append("text")
  .attr("x", margin.left + iw / 2).attr("y", height - 18)
  .attr("text-anchor", "middle").attr("fill", t.inkSoft).style("font-size", "16px")
  .text("Delivery Time (days)");

svg.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -(margin.top + ih / 2)).attr("y", 22)
  .attr("text-anchor", "middle").attr("fill", t.inkSoft).style("font-size", "16px")
  .text("Cumulative Proportion");

// Legend (top-left inside plot area — region near (xMin, y=1) is empty for ECDF)
[
  { label: "Express Shipping (n=160)", color: t.palette[0] },
  { label: "Standard Shipping (n=160)", color: t.palette[1] },
].forEach(({ label, color }, i) => {
  const ly = 24 + i * 32;
  g.append("line").attr("x1", 20).attr("x2", 58).attr("y1", ly).attr("y2", ly)
    .attr("stroke", color).attr("stroke-width", 3);
  g.append("text").attr("x", 68).attr("y", ly + 5)
    .attr("fill", t.inkSoft).style("font-size", "14px").text(label);
});

// Title
svg.append("text")
  .attr("x", width / 2).attr("y", 44).attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "22px").style("font-weight", "600")
  .text("ecdf-basic · javascript · d3 · anyplot.ai");
