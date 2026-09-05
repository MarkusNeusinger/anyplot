// anyplot.ai
// roc-curve: ROC Curve with AUC
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-05
//# anyplot-orientation: square
// anyplot.ai
// roc-curve: ROC Curve with AUC
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const isDark = window.ANYPLOT_THEME === "dark";
const muted = isDark ? "#A8A79F" : "#6B6A63"; // Imprint semantic anchor: muted
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 90, bottom: 100, left: 120 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: synthetic diagnostic-test scores (deterministic LCG) ------------
function makeLcg(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);
function randNormal() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}
const clamp01 = (v) => Math.min(1, Math.max(0, v));

const nDiseased = 150;
const nHealthy = 150;
const diseasedScores = Array.from({ length: nDiseased }, () => clamp01(0.66 + 0.16 * randNormal()));
const healthyScores = Array.from({ length: nHealthy }, () => clamp01(0.34 + 0.16 * randNormal()));

const labeledScores = [
  ...diseasedScores.map((score) => ({ score, isDiseased: true })),
  ...healthyScores.map((score) => ({ score, isDiseased: false })),
].sort((a, b) => b.score - a.score);

// Sweep the decision threshold from high to low, accumulating hits/misses —
// the same construction sklearn.metrics.roc_curve uses on predicted scores.
let truePositives = 0;
let falsePositives = 0;
const rocPoints = [{ fpr: 0, tpr: 0 }];
for (const { isDiseased } of labeledScores) {
  if (isDiseased) truePositives += 1;
  else falsePositives += 1;
  rocPoints.push({ fpr: falsePositives / nHealthy, tpr: truePositives / nDiseased });
}

let auc = 0;
for (let i = 1; i < rocPoints.length; i++) {
  const a = rocPoints[i - 1];
  const b = rocPoints[i];
  auc += ((b.fpr - a.fpr) * (a.tpr + b.tpr)) / 2;
}

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales — equal-aspect: iw === ih so an FPR unit spans the same pixels
// as a TPR unit, per the spec's "equal aspect ratio preferred" note ---------
const x = d3.scaleLinear().domain([0, 1]).range([0, iw]);
const y = d3.scaleLinear().domain([0, 1]).range([ih, 0]);

// --- Gridlines -----------------------------------------------------------
g.append("g")
  .selectAll("line")
  .data(x.ticks(5))
  .join("line")
  .attr("x1", (d) => x(d))
  .attr("x2", (d) => x(d))
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.grid);
g.append("g")
  .selectAll("line")
  .data(y.ticks(5))
  .join("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", (d) => y(d))
  .attr("y2", (d) => y(d))
  .attr("stroke", t.grid);

// --- Diagonal reference line (random classifier, y = x) ---------------------
g.append("line")
  .attr("x1", x(0))
  .attr("y1", y(0))
  .attr("x2", x(1))
  .attr("y2", y(1))
  .attr("stroke", muted)
  .attr("stroke-width", 2.5)
  .attr("stroke-dasharray", "10,8");

// --- Area fill under the ROC curve, then the curve itself --------------------
const area = d3
  .area()
  .x((d) => x(d.fpr))
  .y0(ih)
  .y1((d) => y(d.tpr));
g.append("path").datum(rocPoints).attr("fill", t.palette[0]).attr("opacity", 0.1).attr("d", area);

const line = d3
  .line()
  .x((d) => x(d.fpr))
  .y((d) => y(d.tpr));
g.append("path")
  .datum(rocPoints)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 4)
  .attr("stroke-linejoin", "round")
  .attr("stroke-linecap", "round")
  .attr("d", line);

// --- Axes -------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(5).tickFormat(d3.format(".1f")));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(5).tickFormat(d3.format(".1f")));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels --------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 65)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("False Positive Rate");
g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -90)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("True Positive Rate");

// --- Legend (bottom-right — the ROC curve bows toward the top-left, so this
// corner stays clear of the data) ---------------------------------------------
const legend = g.append("g").attr("transform", `translate(${iw - 420}, ${ih - 130})`);
legend.append("line").attr("x1", 0).attr("x2", 36).attr("y1", 0).attr("y2", 0).attr("stroke", t.palette[0]).attr("stroke-width", 4);
legend
  .append("text")
  .attr("x", 48)
  .attr("y", 5)
  .attr("fill", t.ink)
  .style("font-size", "15px")
  .text(`Diagnostic test (AUC = ${auc.toFixed(2)})`);
legend
  .append("line")
  .attr("x1", 0)
  .attr("x2", 36)
  .attr("y1", 32)
  .attr("y2", 32)
  .attr("stroke", muted)
  .attr("stroke-width", 2.5)
  .attr("stroke-dasharray", "8,6");
legend
  .append("text")
  .attr("x", 48)
  .attr("y", 37)
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text("Random classifier (AUC = 0.50)");

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 55)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "24px")
  .style("font-weight", "600")
  .text("roc-curve · javascript · d3 · anyplot.ai");
