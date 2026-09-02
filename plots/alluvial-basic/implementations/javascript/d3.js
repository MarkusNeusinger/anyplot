// anyplot.ai
// alluvial-basic: Basic Alluvial Diagram
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Cohort of 240 students tracked across four semesters, transitioning between
// declared academic tracks. Categories persist across time points, so each
// keeps the same Imprint color throughout.
const categories = ["STEM", "Business", "Humanities", "Undeclared"];
const stages = ["Semester 1", "Semester 2", "Semester 3", "Semester 4"];

const initialCounts = { STEM: 70, Business: 60, Humanities: 50, Undeclared: 60 };

// transitions[s] = flows from stages[s] to stages[s + 1]
const transitions = [
  [
    ["STEM", "STEM", 55], ["STEM", "Business", 10], ["STEM", "Undeclared", 5],
    ["Business", "STEM", 5], ["Business", "Business", 45], ["Business", "Humanities", 5], ["Business", "Undeclared", 5],
    ["Humanities", "Business", 5], ["Humanities", "Humanities", 40], ["Humanities", "Undeclared", 5],
    ["Undeclared", "STEM", 10], ["Undeclared", "Business", 15], ["Undeclared", "Humanities", 10], ["Undeclared", "Undeclared", 25],
  ],
  [
    ["STEM", "STEM", 50], ["STEM", "Business", 12], ["STEM", "Humanities", 3], ["STEM", "Undeclared", 5],
    ["Business", "STEM", 8], ["Business", "Business", 55], ["Business", "Humanities", 7], ["Business", "Undeclared", 5],
    ["Humanities", "STEM", 2], ["Humanities", "Business", 8], ["Humanities", "Humanities", 40], ["Humanities", "Undeclared", 5],
    ["Undeclared", "STEM", 5], ["Undeclared", "Business", 10], ["Undeclared", "Humanities", 5], ["Undeclared", "Undeclared", 20],
  ],
  [
    ["STEM", "STEM", 48], ["STEM", "Business", 10], ["STEM", "Humanities", 2], ["STEM", "Undeclared", 5],
    ["Business", "STEM", 10], ["Business", "Business", 62], ["Business", "Humanities", 8], ["Business", "Undeclared", 5],
    ["Humanities", "STEM", 3], ["Humanities", "Business", 7], ["Humanities", "Humanities", 40], ["Humanities", "Undeclared", 5],
    ["Undeclared", "STEM", 4], ["Undeclared", "Business", 8], ["Undeclared", "Humanities", 3], ["Undeclared", "Undeclared", 20],
  ],
];

// Node totals per stage, derived from the transition matrices (column sums).
const counts = [initialCounts];
for (const stageTransitions of transitions) {
  const next = Object.fromEntries(categories.map((c) => [c, 0]));
  for (const [, target, value] of stageTransitions) next[target] += value;
  counts.push(next);
}

// --- Layout -------------------------------------------------------------
const margin = { top: 130, right: 190, bottom: 40, left: 190 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;
const nodePadding = 14;
const nodeWidth = 22;
const colX = stages.map((_, s) => margin.left + (s * iw) / (stages.length - 1));

const color = d3.scaleOrdinal().domain(categories).range(t.palette);

// nodes[s][category] = { y0, y1, unit }
const nodes = counts.map((stageCounts) => {
  const total = d3.sum(categories, (c) => stageCounts[c]);
  const unit = (ih - nodePadding * (categories.length - 1)) / total;
  let y = margin.top;
  const stageNodes = {};
  for (const c of categories) {
    const h = stageCounts[c] * unit;
    stageNodes[c] = { y0: y, y1: y + h, unit };
    y += h + nodePadding;
  }
  return stageNodes;
});

// Sub-stack each node's outgoing/incoming flows in fixed category order so
// ribbons never cross within the same node.
const links = transitions.map((stageTransitions, s) => {
  const sourceOffset = Object.fromEntries(categories.map((c) => [c, nodes[s][c].y0]));
  const targetOffset = Object.fromEntries(categories.map((c) => [c, nodes[s + 1][c].y0]));
  const sorted = [...stageTransitions].sort(
    (a, b) => categories.indexOf(a[1]) - categories.indexOf(b[1]) || categories.indexOf(a[0]) - categories.indexOf(b[0])
  );
  return sorted.map(([source, target, value]) => {
    const h0 = value * nodes[s][source].unit;
    const h1 = value * nodes[s + 1][target].unit;
    const y0a = sourceOffset[source];
    const y1a = targetOffset[target];
    sourceOffset[source] += h0;
    targetOffset[target] += h1;
    return { source, target, value, x0: colX[s] + nodeWidth / 2, x1: colX[s + 1] - nodeWidth / 2, y0a, y0b: y0a + h0, y1a, y1b: y1a + h1 };
  });
});

const ribbonPath = (x0, y0a, y0b, x1, y1a, y1b) => {
  const xm = (x0 + x1) / 2;
  return `M${x0},${y0a}C${xm},${y0a} ${xm},${y1a} ${x1},${y1a}L${x1},${y1b}C${xm},${y1b} ${xm},${y0b} ${x0},${y0b}Z`;
};

// --- SVG mount ----------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Ribbons --------------------------------------------------------------
for (const stageLinks of links) {
  svg
    .append("g")
    .selectAll("path")
    .data(stageLinks)
    .join("path")
    .attr("d", (d) => ribbonPath(d.x0, d.y0a, d.y0b, d.x1, d.y1a, d.y1b))
    .attr("fill", (d) => color(d.source))
    .attr("fill-opacity", 0.45)
    .attr("stroke", "none");
}

// --- Nodes ------------------------------------------------------------------
nodes.forEach((stageNodes, s) => {
  svg
    .append("g")
    .selectAll("rect")
    .data(categories.map((c) => ({ category: c, ...stageNodes[c] })))
    .join("rect")
    .attr("x", colX[s] - nodeWidth / 2)
    .attr("y", (d) => d.y0)
    .attr("width", nodeWidth)
    .attr("height", (d) => d.y1 - d.y0)
    .attr("fill", (d) => color(d.category));
});

// --- Category labels (first and last stage only) -----------------------
const labelStage = (s, anchor, dx) => {
  const g = svg.append("g");
  for (const c of categories) {
    const { y0, y1 } = nodes[s][c];
    const cy = (y0 + y1) / 2;
    const text = g
      .append("text")
      .attr("x", colX[s] + dx)
      .attr("y", cy)
      .attr("text-anchor", anchor)
      .attr("fill", t.ink)
      .style("font-size", "15px")
      .style("font-weight", "600");
    text.append("tspan").text(c);
    text
      .append("tspan")
      .attr("x", colX[s] + dx)
      .attr("dy", "1.3em")
      .attr("fill", t.inkSoft)
      .style("font-size", "13px")
      .style("font-weight", "400")
      .text(`${counts[s][c]} students`);
  }
};
labelStage(0, "end", -nodeWidth / 2 - 12);
labelStage(stages.length - 1, "start", nodeWidth / 2 + 12);

// --- Stage headers ------------------------------------------------------
svg
  .append("g")
  .selectAll("text")
  .data(stages)
  .join("text")
  .attr("x", (_, s) => colX[s])
  .attr("y", margin.top - 32)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .style("font-weight", "600")
  .text((d) => d);

// --- Title --------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("alluvial-basic · javascript · d3 · anyplot.ai");
