// anyplot.ai
// curve-oc: Operating Characteristic (OC) Curve
// Library: d3 7.9.0 | JavaScript 22.22.3
// Quality: 91/100 | Created: 2026-06-20
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 190, bottom: 88, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Helpers ------------------------------------------------------------------
function logFact(k) {
  let s = 0;
  for (let i = 2; i <= k; i++) s += Math.log(i);
  return s;
}

function binomialCDF(n, c, p) {
  if (p <= 0) return 1;
  if (p >= 1) return c >= n ? 1 : 0;
  const lp = Math.log(p);
  const l1p = Math.log(1 - p);
  const lfn = logFact(n);
  let sum = 0;
  for (let k = 0; k <= c; k++) {
    sum += Math.exp(lfn - logFact(k) - logFact(n - k) + k * lp + (n - k) * l1p);
  }
  return Math.min(1, sum);
}

// --- Data ---------------------------------------------------------------------
const plans = [
  { label: "n=50,  c=1", n: 50,  c: 1, color: t.palette[0] },
  { label: "n=50,  c=2", n: 50,  c: 2, color: t.palette[1] },
  { label: "n=100, c=2", n: 100, c: 2, color: t.palette[2] },
  { label: "n=100, c=3", n: 100, c: 3, color: t.palette[3] },
];

const X_MAX = 0.15;
const fracs = d3.range(201).map(i => (i * X_MAX) / 200);
for (const plan of plans) {
  plan.pts = fracs.map(p => ({ p, pa: binomialCDF(plan.n, plan.c, p) }));
}

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);

const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const x = d3.scaleLinear().domain([0, X_MAX]).range([0, iw]);
const y = d3.scaleLinear().domain([0, 1]).range([ih, 0]);

// --- Gridlines ----------------------------------------------------------------
g.append("g")
  .selectAll("line")
  .data(y.ticks(5))
  .join("line")
  .attr("x1", 0).attr("x2", iw)
  .attr("y1", d => y(d)).attr("y2", d => y(d))
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- Vertical reference lines: AQL and LTPD -----------------------------------
const vRefs = [
  { px: 0.02, label: "AQL = 2%" },
  { px: 0.08, label: "LTPD = 8%" },
];
for (const { px, label } of vRefs) {
  g.append("line")
    .attr("x1", x(px)).attr("x2", x(px))
    .attr("y1", 0).attr("y2", ih)
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1.5)
    .attr("stroke-dasharray", "8,5");
  g.append("text")
    .attr("x", x(px)).attr("y", -18)
    .attr("text-anchor", "middle")
    .attr("fill", t.inkSoft)
    .style("font-size", "13px")
    .text(label);
}

// --- Horizontal reference lines: producer / consumer risk ---------------------
const hRefs = [
  { pa: 0.95, label: "1−α = 95%" },
  { pa: 0.10, label: "β = 10%" },
];
for (const { pa, label } of hRefs) {
  g.append("line")
    .attr("x1", 0).attr("x2", iw)
    .attr("y1", y(pa)).attr("y2", y(pa))
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "5,4");
  g.append("text")
    .attr("x", iw - 8).attr("y", y(pa) - 7)
    .attr("text-anchor", "end")
    .attr("fill", t.inkSoft)
    .style("font-size", "13px")
    .text(label);
}

// --- OC curves ----------------------------------------------------------------
const lineGen = d3.line()
  .x(d => x(d.p))
  .y(d => y(d.pa))
  .curve(d3.curveMonotoneX);

for (const plan of plans) {
  g.append("path")
    .datum(plan.pts)
    .attr("fill", "none")
    .attr("stroke", plan.color)
    .attr("stroke-width", 3)
    .attr("d", lineGen);
}

// --- Axes ---------------------------------------------------------------------
const xAxis = g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(5).tickFormat(d3.format(".0%")));

const yAxis = g.append("g")
  .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format(".0%")));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels --------------------------------------------------------------
svg.append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", height - 24)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text("Fraction Defective (p)");

svg.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -(margin.top + ih / 2))
  .attr("y", 24)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text("Probability of Acceptance Pa(p)");

// --- Legend (right margin) ---------------------------------------------------
const lgX = iw + 18;
const lgSpacing = 32;
const lgTotal = plans.length * lgSpacing + 20;
const lgY = (ih - lgTotal) / 2;

g.append("rect")
  .attr("x", lgX - 8).attr("y", lgY - 12)
  .attr("width", 155).attr("height", lgTotal + 12)
  .attr("fill", t.elevatedBg)
  .attr("rx", 5)
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

for (let i = 0; i < plans.length; i++) {
  const ly = lgY + i * lgSpacing;
  g.append("line")
    .attr("x1", lgX).attr("x2", lgX + 28)
    .attr("y1", ly + 7).attr("y2", ly + 7)
    .attr("stroke", plans[i].color)
    .attr("stroke-width", 3);
  g.append("text")
    .attr("x", lgX + 36).attr("y", ly + 12)
    .attr("fill", t.ink)
    .style("font-size", "14px")
    .style("font-family", "monospace")
    .text(plans[i].label);
}

// --- Title --------------------------------------------------------------------
svg.append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("curve-oc · javascript · d3 · anyplot.ai");
