// anyplot.ai
// bar-3d-categorical: 3D Bar Chart for Categorical Comparison
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-04

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly sales ($k) across product category (x) and sales region (y).
const xCategories = ["Electronics", "Apparel", "Home Goods", "Sporting", "Toys"];
const yCategories = ["North", "South", "East", "West"];
const values = [
  [82, 45, 38, 29, 51],
  [64, 58, 42, 33, 47],
  [91, 39, 55, 61, 28],
  [73, 66, 49, 44, 36],
];
const bars = [];
for (let iy = 0; iy < yCategories.length; iy++) {
  for (let ix = 0; ix < xCategories.length; ix++) {
    bars.push({ ix, iy, value: values[iy][ix] });
  }
}
const minValue = d3.min(bars, (d) => d.value);
const maxValue = d3.max(bars, (d) => d.value);

// --- Isometric projection ----------------------------------------------------
const nCols = xCategories.length;
const nRows = yCategories.length;
const cellSize = 110;
const angle = Math.PI / 6; // 30 degrees elevation of the base grid
const cosA = Math.cos(angle);
const sinA = Math.sin(angle);
const heightScale = 2.2; // px per $k, ~30deg/45deg-style isometric read
const originX = 700;
const originY = 300;

function iso(px, py) {
  return {
    x: originX + (px - py) * cellSize * cosA,
    y: originY + (px + py) * cellSize * sinA,
  };
}
function pts(corners) {
  return corners.map((p) => `${p.x},${p.y}`).join(" ");
}

// --- Color: sequential Imprint scale encodes value magnitude ----------------
const colorScale = d3.scaleSequential(d3.interpolateRgbBasis(t.seq)).domain([minValue, maxValue]);

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

const defs = svg.append("defs");
const gradient = defs
  .append("linearGradient")
  .attr("id", "seqGradient")
  .attr("x1", "0%")
  .attr("y1", "100%")
  .attr("x2", "0%")
  .attr("y2", "0%");
d3.range(0, 1.0001, 0.1).forEach((f) => {
  gradient
    .append("stop")
    .attr("offset", `${f * 100}%`)
    .attr("stop-color", colorScale(minValue + f * (maxValue - minValue)));
});

// --- Base-plane grid ----------------------------------------------------------
const gridGroup = svg.append("g");
for (let i = 0; i <= nCols; i++) {
  const a = iso(i, 0);
  const b = iso(i, nRows);
  gridGroup.append("line").attr("x1", a.x).attr("y1", a.y).attr("x2", b.x).attr("y2", b.y);
}
for (let j = 0; j <= nRows; j++) {
  const a = iso(0, j);
  const b = iso(nCols, j);
  gridGroup.append("line").attr("x1", a.x).attr("y1", a.y).attr("x2", b.x).attr("y2", b.y);
}
gridGroup.selectAll("line").attr("stroke", t.grid).attr("stroke-width", 1.5);

// --- Bars (painter's algorithm: back-to-front by grid depth) ----------------
const barGroup = svg.append("g");
const hw = 0.38; // half-width of footprint, leaves spacing between bars
const sorted = [...bars].sort((a, b) => a.ix + a.iy - (b.ix + b.iy));

for (const d of sorted) {
  const cx = d.ix + 0.5;
  const cy = d.iy + 0.5;
  const baseTL = iso(cx - hw, cy - hw);
  const baseTR = iso(cx + hw, cy - hw);
  const baseBR = iso(cx + hw, cy + hw);
  const baseBL = iso(cx - hw, cy + hw);
  const barH = d.value * heightScale;
  const raise = (p) => ({ x: p.x, y: p.y - barH });
  const topTL = raise(baseTL);
  const topTR = raise(baseTR);
  const topBR = raise(baseBR);
  const topBL = raise(baseBL);

  const base = d3.color(colorScale(d.value));
  const g = barGroup.append("g");
  g.append("polygon")
    .attr("points", pts([baseBL, baseBR, topBR, topBL]))
    .attr("fill", base.darker(0.9))
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 1.5);
  g.append("polygon")
    .attr("points", pts([baseTR, baseBR, topBR, topTR]))
    .attr("fill", base.darker(0.45))
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 1.5);
  g.append("polygon")
    .attr("points", pts([topTL, topTR, topBR, topBL]))
    .attr("fill", base)
    .attr("stroke", t.pageBg)
    .attr("stroke-width", 1.5);

  const labelY = (topTL.y + topBR.y) / 2 - 6;
  const labelX = (topTL.x + topBR.x) / 2;
  g.append("text")
    .attr("x", labelX)
    .attr("y", labelY)
    .attr("text-anchor", "middle")
    .style("font-size", "14px")
    .style("font-weight", "600")
    .style("paint-order", "stroke")
    .style("stroke", t.pageBg)
    .style("stroke-width", "3px")
    .attr("fill", t.ink)
    .text(d.value);
}

// --- Category axis labels (along the two front grid edges) ------------------
const labelGroup = svg.append("g");
xCategories.forEach((name, ix) => {
  const p = iso(ix + 0.5, nRows + 0.5);
  labelGroup
    .append("text")
    .attr("transform", `translate(${p.x},${p.y}) rotate(30)`)
    .attr("text-anchor", "middle")
    .style("font-size", "15px")
    .attr("fill", t.inkSoft)
    .text(name);
});
yCategories.forEach((name, iy) => {
  const p = iso(nCols + 0.5, iy + 0.5);
  labelGroup
    .append("text")
    .attr("transform", `translate(${p.x},${p.y}) rotate(-30)`)
    .attr("text-anchor", "middle")
    .style("font-size", "15px")
    .attr("fill", t.inkSoft)
    .text(name);
});

// --- Color legend (value magnitude -> Imprint sequential scale) ------------
const legendX = width - 130;
const legendY = 260;
const legendH = 260;
const legendW = 26;
svg
  .append("rect")
  .attr("x", legendX)
  .attr("y", legendY)
  .attr("width", legendW)
  .attr("height", legendH)
  .attr("fill", "url(#seqGradient)")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1);
svg
  .append("text")
  .attr("x", legendX + legendW / 2)
  .attr("y", legendY - 16)
  .attr("text-anchor", "middle")
  .style("font-size", "14px")
  .attr("fill", t.inkSoft)
  .text("Sales ($k)");
svg
  .append("text")
  .attr("x", legendX + legendW + 8)
  .attr("y", legendY + 5)
  .style("font-size", "13px")
  .attr("fill", t.inkSoft)
  .text(maxValue);
svg
  .append("text")
  .attr("x", legendX + legendW + 8)
  .attr("y", legendY + legendH)
  .style("font-size", "13px")
  .attr("fill", t.inkSoft)
  .text(minValue);

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("bar-3d-categorical · javascript · d3 · anyplot.ai");
