// anyplot.ai
// waffle-basic: Basic Waffle Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-09

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Marketing budget allocation across spending categories, values sum to 100.
const categories = [
  { label: "Digital Advertising", value: 32 },
  { label: "Content Marketing", value: 24 },
  { label: "Events & Sponsorships", value: 18 },
  { label: "Public Relations", value: 14 },
  { label: "Tools & Software", value: 12 },
];

const color = d3.scaleOrdinal()
  .domain(categories.map((d) => d.label))
  .range(t.palette);

// Expand into 100 grid cells (one square = 1%), in category order.
const cellCategories = categories.flatMap((d) => Array(d.value).fill(d));

const gridCols = 10;
const gridRows = 10;
const cells = cellCategories.map((d, i) => ({
  category: d,
  row: Math.floor(i / gridCols),
  col: i % gridCols,
}));

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Title ----------------------------------------------------------------
svg.append("text").attr("x", width / 2).attr("y", 64).attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "22px").style("font-weight", "600")
  .text("waffle-basic · javascript · d3 · anyplot.ai");

// --- Waffle grid --------------------------------------------------------------
const marginTop = 140;
const legendHeight = 170;
const sideMargin = 100;
const availableWidth = width - 2 * sideMargin;
const availableHeight = height - marginTop - legendHeight;
const gridSize = Math.min(availableWidth, availableHeight);
const cellGap = 4;
const cellSize = (gridSize - (gridCols - 1) * cellGap) / gridCols;
const gridX = (width - gridSize) / 2;
const gridY = marginTop;

const g = svg.append("g").attr("transform", `translate(${gridX},${gridY})`);

g.selectAll("rect").data(cells).join("rect")
  .attr("x", (d) => d.col * (cellSize + cellGap))
  .attr("y", (d) => d.row * (cellSize + cellGap))
  .attr("width", cellSize)
  .attr("height", cellSize)
  .attr("rx", 3)
  .attr("fill", (d) => color(d.category.label));

// --- Legend ---------------------------------------------------------------
const legendY = marginTop + gridSize + 70;
const swatchSize = 22;
const itemGap = 34;

const legend = svg.append("g").attr("transform", `translate(0,${legendY})`);

// Measure each item's text width first so items can be centered as a group.
const measure = legend.append("text").style("font-size", "16px").attr("opacity", 0);
const itemWidths = categories.map((d) => {
  measure.text(`${d.label} (${d.value}%)`);
  return swatchSize + 10 + measure.node().getComputedTextLength();
});
measure.remove();

const totalLegendWidth = itemWidths.reduce((a, b) => a + b, 0) + itemGap * (categories.length - 1);
let cursorX = (width - totalLegendWidth) / 2;

categories.forEach((d, i) => {
  const item = legend.append("g").attr("transform", `translate(${cursorX},0)`);
  item.append("rect")
    .attr("width", swatchSize).attr("height", swatchSize)
    .attr("rx", 3)
    .attr("fill", color(d.label));
  item.append("text")
    .attr("x", swatchSize + 10).attr("y", swatchSize / 2)
    .attr("dominant-baseline", "middle")
    .attr("fill", t.inkSoft).style("font-size", "16px")
    .text(`${d.label} (${d.value}%)`);
  cursorX += itemWidths[i] + itemGap;
});
