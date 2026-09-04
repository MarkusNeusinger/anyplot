// anyplot.ai
// confusion-matrix: Confusion Matrix Heatmap
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-04

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (quality-control defect classifier, in-memory & deterministic) ---
const classNames = ["OK", "Scratch", "Dent", "Crack", "Stain"];
const confusionMatrix = [
  [180, 5, 3, 1, 2],
  [8, 92, 4, 2, 1],
  [6, 3, 78, 5, 2],
  [2, 1, 4, 65, 1],
  [3, 2, 1, 2, 70],
];
const n = classNames.length;
const maxCount = d3.max(confusionMatrix.flat());

// --- Layout ------------------------------------------------------------
const margin = { top: 130, right: 190, bottom: 150, left: 190 };
const availW = width - margin.left - margin.right;
const availH = height - margin.top - margin.bottom;
const gridSize = Math.min(availW, availH);
const gridLeft = margin.left + (availW - gridSize) / 2;
const gridTop = margin.top + (availH - gridSize) / 2;
const cell = gridSize / n;

// --- Scales --------------------------------------------------------------
const color = d3.scaleSequential(d3.interpolateRgbBasis(t.seq)).domain([0, maxCount]);

// --- SVG mount -------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${gridLeft},${gridTop})`);

// --- Cells + value annotations ---------------------------------------------
for (let row = 0; row < n; row++) {
  for (let col = 0; col < n; col++) {
    const value = confusionMatrix[row][col];
    const isDiagonal = row === col;
    g.append("rect")
      .attr("x", col * cell)
      .attr("y", row * cell)
      .attr("width", cell)
      .attr("height", cell)
      .attr("fill", color(value))
      .attr("stroke", isDiagonal ? t.ink : t.pageBg)
      .attr("stroke-width", isDiagonal ? 4 : 2);

    g.append("text")
      .attr("x", col * cell + cell / 2)
      .attr("y", row * cell + cell / 2)
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "central")
      .attr("fill", value / maxCount > 0.45 ? t.pageBg : t.ink)
      .style("font-size", "24px")
      .style("font-weight", isDiagonal ? "700" : "500")
      .text(value);
  }
}

// --- Axis ticks (categorical class names, no numeric axis) -----------------
classNames.forEach((name, i) => {
  g.append("text")
    .attr("x", i * cell + cell / 2)
    .attr("y", gridSize + 34)
    .attr("text-anchor", "middle")
    .attr("fill", t.inkSoft)
    .style("font-size", "16px")
    .text(name);

  g.append("text")
    .attr("x", -16)
    .attr("y", i * cell + cell / 2)
    .attr("text-anchor", "end")
    .attr("dominant-baseline", "central")
    .attr("fill", t.inkSoft)
    .style("font-size", "16px")
    .text(name);
});

// --- Axis titles -------------------------------------------------------
svg
  .append("text")
  .attr("x", gridLeft + gridSize / 2)
  .attr("y", gridTop + gridSize + 100)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .style("font-weight", "600")
  .text("Predicted Label");

svg
  .append("text")
  .attr("transform", `translate(${gridLeft - 130}, ${gridTop + gridSize / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .style("font-weight", "600")
  .text("True Label");

// --- Colorbar (sequential Imprint scale, sample count) ----------------------
const barWidth = 34;
const barX = gridLeft + gridSize + 60;
const barY = gridTop;

const gradient = svg
  .append("defs")
  .append("linearGradient")
  .attr("id", "confusion-seq-gradient")
  .attr("x1", "0%")
  .attr("x2", "0%")
  .attr("y1", "100%")
  .attr("y2", "0%");
d3.range(0, 1.0001, 0.1).forEach((stop) => {
  gradient
    .append("stop")
    .attr("offset", `${stop * 100}%`)
    .attr("stop-color", color(stop * maxCount));
});

svg
  .append("rect")
  .attr("x", barX)
  .attr("y", barY)
  .attr("width", barWidth)
  .attr("height", gridSize)
  .attr("fill", "url(#confusion-seq-gradient)")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1.5);

const barScale = d3.scaleLinear().domain([0, maxCount]).range([barY + gridSize, barY]);
const barAxisG = svg
  .append("g")
  .attr("transform", `translate(${barX + barWidth},0)`)
  .call(d3.axisRight(barScale).ticks(5));
barAxisG.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
barAxisG.selectAll("line").attr("stroke", t.grid);
barAxisG.select(".domain").attr("stroke", t.inkSoft);

svg
  .append("text")
  .attr("transform", `translate(${barX + barWidth + 62}, ${barY + gridSize / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Sample Count");

// --- Title -------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("confusion-matrix · javascript · d3 · anyplot.ai");
