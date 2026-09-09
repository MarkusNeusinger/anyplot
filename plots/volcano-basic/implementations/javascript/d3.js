// anyplot.ai
// volcano-basic: Volcano Plot for Statistical Significance
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 80/100 | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 60, bottom: 90, left: 100 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic RNA-seq differential expression) -------
// Small fixed-seed LCG — the browser has no seeded RNG.
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function randn() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const N_GENES = 2200;
const FC_SIG = 1.6;
const P_THRESHOLD = 1.3; // -log10(0.05)
const FC_THRESHOLD = 1;

const genes = [];
for (let i = 0; i < N_GENES; i += 1) {
  const logFc = randn() * FC_SIG;
  // stronger fold changes tend to carry lower p-values (more significant)
  const base = Math.abs(logFc) * 1.55 + Math.abs(randn()) * 0.9;
  const negLogP = Math.max(0.02, base + (rand() - 0.5) * 1.3);
  genes.push({ logFc, negLogP });
}

const topHits = [
  { label: "TP53", logFc: 3.4, negLogP: 6.3 },
  { label: "MYC", logFc: -3.1, negLogP: 5.6 },
  { label: "BRCA1", logFc: 2.6, negLogP: 4.8 },
  { label: "EGFR", logFc: -2.4, negLogP: 4.2 },
];
for (const hit of topHits) genes.push({ ...hit });

function status(d) {
  if (d.negLogP < P_THRESHOLD || Math.abs(d.logFc) < FC_THRESHOLD) return "ns";
  return d.logFc > 0 ? "up" : "down";
}

const colorFor = { ns: t.muted, up: t.palette[4], down: t.palette[2] };

// --- SVG mount ---------------------------------------------------------------
const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);
const g = svg
  .append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const fcExtent = d3.max(genes, (d) => Math.abs(d.logFc)) * 1.15;
const x = d3.scaleLinear().domain([-fcExtent, fcExtent]).nice().range([0, iw]);
const yMax = d3.max(genes, (d) => d.negLogP) * 1.1;
const y = d3.scaleLinear().domain([0, yMax]).nice().range([ih, 0]);

// --- Gridlines (both axes — scatter plot) --------------------------------------
g.append("g")
  .selectAll("line")
  .data(y.ticks(6))
  .join("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", (d) => y(d))
  .attr("y2", (d) => y(d))
  .attr("stroke", t.grid);

g.append("g")
  .selectAll("line")
  .data(x.ticks(8))
  .join("line")
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("x1", (d) => x(d))
  .attr("x2", (d) => x(d))
  .attr("stroke", t.grid);

// --- Threshold lines ------------------------------------------------------------
g.append("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", y(P_THRESHOLD))
  .attr("y2", y(P_THRESHOLD))
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1.5)
  .attr("stroke-dasharray", "6,5");

for (const fc of [-FC_THRESHOLD, FC_THRESHOLD]) {
  g.append("line")
    .attr("x1", x(fc))
    .attr("x2", x(fc))
    .attr("y1", 0)
    .attr("y2", ih)
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1.5)
    .attr("stroke-dasharray", "6,5");
}

// --- Points -----------------------------------------------------------------
g.selectAll("circle")
  .data(genes)
  .join("circle")
  .attr("cx", (d) => x(d.logFc))
  .attr("cy", (d) => y(d.negLogP))
  .attr("r", 6)
  .attr("fill", (d) => colorFor[status(d)])
  .attr("fill-opacity", (d) => (status(d) === "ns" ? 0.35 : 0.75))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 0.6);

// --- Top-hit labels ----------------------------------------------------------
g.selectAll(".hit-label")
  .data(topHits)
  .join("text")
  .attr("class", "hit-label")
  .attr("x", (d) => x(d.logFc) + (d.logFc > 0 ? 14 : -14))
  .attr("y", (d) => y(d.negLogP) - 10)
  .attr("text-anchor", (d) => (d.logFc > 0 ? "start" : "end"))
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .style("font-weight", "600")
  .text((d) => d.label);

// --- Axes ----------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(8));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.grid);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels -----------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("log2 Fold Change");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -70)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("-log10(p-value)");

// --- Legend -----------------------------------------------------------------
const legendItems = [
  { key: "up", label: "Up-regulated" },
  { key: "down", label: "Down-regulated" },
  { key: "ns", label: "Not significant" },
];
const legend = svg
  .append("g")
  .attr(
    "transform",
    `translate(${width - margin.right - 220},${margin.top + 10})`,
  );
legend
  .append("rect")
  .attr("x", -16)
  .attr("y", -22)
  .attr("width", 210)
  .attr("height", legendItems.length * 30 + 12)
  .attr("fill", t.elevatedBg);
legendItems.forEach((item, i) => {
  const row = legend.append("g").attr("transform", `translate(0,${i * 30})`);
  row
    .append("circle")
    .attr("r", 7)
    .attr("cx", 7)
    .attr("cy", 0)
    .attr("fill", colorFor[item.key]);
  row
    .append("text")
    .attr("x", 22)
    .attr("y", 5)
    .attr("fill", t.inkSoft)
    .style("font-size", "15px")
    .text(item.label);
});

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 46)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("volcano-basic · javascript · d3 · anyplot.ai");
