// anyplot.ai
// line-impurity-comparison: Gini Impurity vs Entropy Comparison
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-08-26

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 130, right: 60, bottom: 90, left: 90 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Gini impurity: 2p(1-p). Entropy (log2, normalized): -p*log2(p) - (1-p)*log2(1-p).
const gini = (p) => 2 * p * (1 - p);
const entropy = (p) => (p === 0 || p === 1 ? 0 : -p * Math.log2(p) - (1 - p) * Math.log2(1 - p));

const probabilities = d3.range(0, 101).map((i) => i / 100);
const giniCurve = probabilities.map((p) => ({ p, value: gini(p) }));
const entropyCurve = probabilities.map((p) => ({ p, value: entropy(p) }));

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales ---------------------------------------------------------------
const x = d3.scaleLinear().domain([0, 1]).range([0, iw]);
const y = d3.scaleLinear().domain([0, 1]).nice().range([ih, 0]);

// --- Grid (light, y-axis only) ---------------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Axes -------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(6));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels --------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Probability p");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -62)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Impurity Measure");

// --- Lines --------------------------------------------------------------------
const line = d3
  .line()
  .x((d) => x(d.p))
  .y((d) => y(d.value));

g.append("path")
  .datum(giniCurve)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 4)
  .attr("d", line);

g.append("path")
  .datum(entropyCurve)
  .attr("fill", "none")
  .attr("stroke", t.palette[1])
  .attr("stroke-width", 4)
  .attr("stroke-dasharray", "10,6")
  .attr("d", line);

// --- Annotation: shared maximum at p=0.5 (spec-requested) ---------------------
const guideX = x(0.5);
g.append("line")
  .attr("x1", guideX)
  .attr("x2", guideX)
  .attr("y1", y(0))
  .attr("y2", y(1))
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1.5)
  .attr("stroke-dasharray", "4,4")
  .attr("opacity", 0.6);

g.append("circle").attr("cx", guideX).attr("cy", y(gini(0.5))).attr("r", 7).attr("fill", t.palette[0]);
g.append("circle").attr("cx", guideX).attr("cy", y(entropy(0.5))).attr("r", 7).attr("fill", t.palette[1]);

// Label sits in the open gap between the two curves, clear of both lines.
g.append("text")
  .attr("x", guideX + 18)
  .attr("y", y((gini(0.5) + entropy(0.5)) / 2))
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("p = 0.5")
  .append("tspan")
  .attr("x", guideX + 18)
  .attr("dy", 20)
  .text("shared maximum");

// --- Legend (with formulas) ----------------------------------------------------
const legend = svg
  .append("g")
  .attr("transform", `translate(${margin.left + 20},${margin.top - 66})`);

const legendRows = [
  { label: "Gini impurity:  2p(1 − p)", color: t.palette[0], dash: null },
  { label: "Entropy:  −p·log₂p − (1 − p)·log₂(1 − p)", color: t.palette[1], dash: "10,6" },
];

legendRows.forEach((d, i) => {
  const row = legend.append("g").attr("transform", `translate(0,${i * 26})`);
  row
    .append("line")
    .attr("x1", 0)
    .attr("x2", 32)
    .attr("y1", 0)
    .attr("y2", 0)
    .attr("stroke", d.color)
    .attr("stroke-width", 4)
    .attr("stroke-dasharray", d.dash);
  row
    .append("text")
    .attr("x", 42)
    .attr("y", 5)
    .attr("fill", t.ink)
    .style("font-size", "15px")
    .text(d.label);
});

// --- Title ----------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("line-impurity-comparison · javascript · d3 · anyplot.ai");
