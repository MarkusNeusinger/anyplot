// anyplot.ai
// dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-05

//# anyplot-orientation: square

// --- Data (in-memory, deterministic) ----------------------------------------
// 12-week clinical trial follow-up outcomes for 400 enrolled patients.
const t = window.ANYPLOT_TOKENS;
const categories = [
  { label: "Improved", count: 220, color: t.palette[0] },
  { label: "No change", count: 110, color: t.palette[1] },
  { label: "Worsened", count: 45, color: t.palette[4] },
  { label: "Discontinued", count: 25, color: t.palette[2] },
];
const total = categories.reduce((sum, c) => sum + c.count, 0);

// Flatten into one entry per dot, filled left-to-right, top-to-bottom in
// category order.
const dots = categories.flatMap((c) => Array.from({ length: c.count }, () => c));

const nCols = 20;
const nRows = Math.ceil(total / nCols);

// --- SVG mount ---------------------------------------------------------------
const { width, height } = window.ANYPLOT_SIZE;
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

const margin = { top: 170, right: 90, bottom: 210, left: 90 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

const cell = Math.min(iw / nCols, ih / nRows);
const gridW = nCols * cell;
const gridH = nRows * cell;
const offsetX = (iw - gridW) / 2;
const offsetY = (ih - gridH) / 2;

const g = svg
  .append("g")
  .attr("transform", `translate(${margin.left + offsetX},${margin.top + offsetY})`);

// --- Dots ----------------------------------------------------------------
const dotRadius = cell * 0.36;
g.selectAll("circle")
  .data(dots)
  .join("circle")
  .attr("cx", (d, i) => (i % nCols) * cell + cell / 2)
  .attr("cy", (d, i) => Math.floor(i / nCols) * cell + cell / 2)
  .attr("r", dotRadius)
  .attr("fill", (d) => d.color);

// --- Title ---------------------------------------------------------------
const title = "Clinical Trial Outcomes at 12 Weeks · dot-matrix-proportional · javascript · d3 · anyplot.ai";
const titleFontSize = Math.max(14, Math.round(22 * Math.min(1, 67 / title.length)));
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 64)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(title);

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 64 + titleFontSize + 20)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text(`${total} patients, one dot per patient`);

// --- Legend ----------------------------------------------------------------
const legendY = margin.top + offsetY + gridH + 60;
const slotWidth = width / categories.length;

const legend = svg
  .selectAll("g.legend-item")
  .data(categories)
  .join("g")
  .attr("class", "legend-item")
  .attr("transform", (d, i) => `translate(${slotWidth * (i + 0.5)},${legendY})`);

legend
  .append("circle")
  .attr("r", 11)
  .attr("cy", -34)
  .attr("fill", (d) => d.color);

legend
  .append("text")
  .attr("text-anchor", "middle")
  .attr("y", -6)
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .style("font-weight", "600")
  .text((d) => d.label);

legend
  .append("text")
  .attr("text-anchor", "middle")
  .attr("y", 18)
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text((d) => `${d.count} (${Math.round((d.count / total) * 100)}%)`);
