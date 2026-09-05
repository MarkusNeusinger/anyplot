// anyplot.ai
// heatmap-adjacency: Network Adjacency Matrix Heatmap
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Deterministic PRNG (LCG, no seeded Math.random in the browser) --------
let seed = 42;
function rand() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

// --- Data: workplace collaboration network, grouped by department ----------
// Nodes are ordered by department so the block-diagonal structure (dense
// within-team collaboration, sparse cross-team ties) is visible without any
// reordering step.
const departments = [
  { name: "Product", size: 8 },
  { name: "Engineering", size: 14 },
  { name: "Marketing", size: 9 },
  { name: "Sales", size: 9 },
];
const nodes = [];
departments.forEach((dept) => {
  for (let i = 0; i < dept.size; i++) nodes.push({ department: dept.name });
});
const n = nodes.length;

// Symmetric weighted adjacency matrix; null = no collaboration recorded.
// Diagonal stays null (self-loops carry no information here).
const matrix = Array.from({ length: n }, () => new Array(n).fill(null));
for (let i = 0; i < n; i++) {
  for (let j = i + 1; j < n; j++) {
    const sameDept = nodes[i].department === nodes[j].department;
    let weight = null;
    if (sameDept) {
      if (rand() < 0.72) weight = 0.35 + rand() * 0.6;
    } else if (rand() < 0.05) {
      weight = 0.1 + rand() * 0.3;
    }
    matrix[i][j] = weight;
    matrix[j][i] = weight;
  }
}
const maxWeight = d3.max(matrix.flat().filter((v) => v !== null));

// Department block boundaries (node index ranges) for separators + labels.
let cursor = 0;
const blocks = departments.map((dept) => {
  const start = cursor;
  cursor += dept.size;
  return { name: dept.name, start, end: cursor, mid: start + dept.size / 2 };
});

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Layout -------------------------------------------------------------------
const margin = { top: 150, right: 220, bottom: 40, left: 110 };
const availW = width - margin.left - margin.right;
const availH = height - margin.top - margin.bottom;
const gridSize = Math.min(availW, availH);
const cell = gridSize / n;
const gridX = margin.left;
const gridY = margin.top;

// --- Color scale (Imprint sequential: brand green -> blue) ------------------
const color = d3.scaleSequential(d3.interpolateRgbBasis(t.seq)).domain([0, maxWeight]);

// --- Cells --------------------------------------------------------------------
const cellData = [];
for (let i = 0; i < n; i++) {
  for (let j = 0; j < n; j++) {
    cellData.push({ i, j, value: matrix[i][j] });
  }
}

svg
  .append("g")
  .selectAll("rect")
  .data(cellData)
  .join("rect")
  .attr("x", (d) => gridX + d.j * cell)
  .attr("y", (d) => gridY + d.i * cell)
  .attr("width", cell)
  .attr("height", cell)
  .attr("fill", (d) => (d.value === null ? t.elevatedBg : color(d.value)));

// --- Block separators (mark cluster / department boundaries) ----------------
const separators = svg.append("g");
blocks.forEach((b) => {
  if (b.start === 0) return;
  const pos = gridX + b.start * cell;
  separators
    .append("line")
    .attr("x1", pos)
    .attr("x2", pos)
    .attr("y1", gridY)
    .attr("y2", gridY + gridSize)
    .attr("stroke", t.ink)
    .attr("stroke-width", 2);
  separators
    .append("line")
    .attr("x1", gridX)
    .attr("x2", gridX + gridSize)
    .attr("y1", gridY + b.start * cell)
    .attr("y2", gridY + b.start * cell)
    .attr("stroke", t.ink)
    .attr("stroke-width", 2);
});
// Outer frame around the full matrix.
separators
  .append("rect")
  .attr("x", gridX)
  .attr("y", gridY)
  .attr("width", gridSize)
  .attr("height", gridSize)
  .attr("fill", "none")
  .attr("stroke", t.ink)
  .attr("stroke-width", 2);

// --- Group boundary labels (node count too large for per-node ticks) -------
svg
  .append("g")
  .selectAll("text")
  .data(blocks)
  .join("text")
  .attr("x", (d) => gridX + d.mid * cell)
  .attr("y", gridY - 16)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text((d) => d.name);

svg
  .append("g")
  .selectAll("text")
  .data(blocks)
  .join("text")
  .attr("transform", (d) => `translate(${gridX - 16},${gridY + d.mid * cell}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text((d) => d.name);

// --- Colorbar legend (weight scale) ------------------------------------------
const legendX = gridX + gridSize + 60;
const legendW = 26;
const legendH = gridSize * 0.6;
const legendY = gridY + (gridSize - legendH) / 2;

const defs = svg.append("defs");
const gradient = defs
  .append("linearGradient")
  .attr("id", "weight-gradient")
  .attr("x1", "0%")
  .attr("x2", "0%")
  .attr("y1", "100%")
  .attr("y2", "0%");
gradient
  .selectAll("stop")
  .data(d3.range(0, 1.001, 0.1))
  .join("stop")
  .attr("offset", (d) => `${d * 100}%`)
  .attr("stop-color", (d) => color(d * maxWeight));

svg
  .append("rect")
  .attr("x", legendX)
  .attr("y", legendY)
  .attr("width", legendW)
  .attr("height", legendH)
  .attr("fill", "url(#weight-gradient)")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1);

const legendScale = d3.scaleLinear().domain([0, maxWeight]).range([legendY + legendH, legendY]);
const legendAxis = d3.axisRight(legendScale).ticks(5).tickFormat(d3.format(".1f"));
const legendAxisG = svg
  .append("g")
  .attr("transform", `translate(${legendX + legendW},0)`)
  .call(legendAxis);
legendAxisG.selectAll("text").attr("fill", t.inkSoft).style("font-size", "13px");
legendAxisG.selectAll("line").attr("stroke", t.inkSoft);
legendAxisG.select(".domain").attr("stroke", t.inkSoft);

svg
  .append("text")
  .attr("transform", `translate(${legendX - 24},${legendY + legendH / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Collaboration strength");

// No-data swatch, to disambiguate the near-background fill from a low weight.
const swatchY = legendY + legendH + 40;
svg
  .append("rect")
  .attr("x", legendX)
  .attr("y", swatchY)
  .attr("width", legendW)
  .attr("height", legendW)
  .attr("fill", t.elevatedBg)
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1);
svg
  .append("text")
  .attr("x", legendX + legendW + 10)
  .attr("y", swatchY + legendW / 2 + 5)
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .text("No link");

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 54)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("heatmap-adjacency · javascript · d3 · anyplot.ai");

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 84)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text(`${n}-person collaboration network across 4 departments, reordered to reveal team clusters`);
