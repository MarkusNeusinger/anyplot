// anyplot.ai
// bar-3d-categorical: 3D Bar Chart for Categorical Comparison
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-04

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ---------------------------------------
// Customer satisfaction score (0-100) by product line and region.
const regions = ["North", "South", "East", "West"];
const productLines = ["Electronics", "Apparel", "Home Goods", "Grocery"];
const scores = [
  [82, 76, 88, 91],
  [74, 69, 81, 77],
  [90, 85, 93, 88],
  [95, 91, 89, 97],
];

const values = [];
scores.forEach((row) => row.forEach((v) => values.push(v)));
const minValue = Math.min(...values);
const maxValue = Math.max(...values);

// --- Isometric projection (elevation ~30deg, azimuth ~45deg) ---------------
// The depth factor is pushed slightly beyond a literal sin(30deg) so that
// consecutive rows/columns stay clear of each other even at max bar height —
// a purely 30deg depth step would let a tall back bar visually collide with
// a short bar one row closer (their screen-space heights overlap).
const ISO_ANGLE = (30 * Math.PI) / 180;
const COS_A = Math.cos(ISO_ANGLE);
const DEPTH_A = 0.574; // ~elevation 35deg equivalent, for readable depth spacing
const CELL = 140; // grid spacing along each categorical axis
const PAD = 0.32; // half bar footprint (cell units) — leaves a visible gap
const MAX_BAR_H = 140; // px for the tallest bar
const LABEL_MARGIN = 40; // px beyond the grid's silhouette for axis labels

function projectRaw(col, row, z) {
  const x = (col - row) * COS_A * CELL;
  const y = (col + row) * DEPTH_A * CELL - z;
  return [x, y];
}

function barHeight(value) {
  return (value / 100) * MAX_BAR_H;
}

// --- Color: value magnitude -> Imprint sequential gradient ------------------
function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function rgbToHex(rgb) {
  return (
    "#" +
    rgb
      .map((c) => Math.max(0, Math.min(255, Math.round(c))).toString(16).padStart(2, "0"))
      .join("")
  );
}
function lerpColor(hexA, hexB, frac) {
  const a = hexToRgb(hexA);
  const b = hexToRgb(hexB);
  return rgbToHex(a.map((c, i) => c + (b[i] - c) * frac));
}
function shade(hex, factor) {
  return rgbToHex(hexToRgb(hex).map((c) => c * factor));
}
function colorForValue(value) {
  const frac = (value - minValue) / (maxValue - minValue);
  return lerpColor(t.seq[0], t.seq[1], frac);
}

// --- Bars, back-to-front (painter's algorithm) ------------------------------
const bars = [];
productLines.forEach((yLabel, row) => {
  regions.forEach((xLabel, col) => {
    bars.push({ col, row, xLabel, yLabel, value: scores[row][col] });
  });
});
bars.sort((a, b) => a.col + a.row - (b.col + b.row));

// --- Center the isometric grid inside the mount -----------------------------
const TOP_MARGIN = 110;
const BOTTOM_MARGIN = 70;
const LEFT_MARGIN = 210;
const RIGHT_MARGIN = 190;
const midRow = (productLines.length - 1) / 2;
const midCol = (regions.length - 1) / 2;

const rawPoints = [];
for (const rowEdge of [-PAD, productLines.length - 1 + PAD]) {
  for (const colEdge of [-PAD, regions.length - 1 + PAD]) {
    rawPoints.push(projectRaw(colEdge, rowEdge, 0));
  }
}
bars.forEach(({ col, row, value }) => {
  rawPoints.push(projectRaw(col - PAD, row - PAD, barHeight(value)));
});
// Axis label lanes: a straight line below (x-axis) and to the left (y-axis)
// of the grid's silhouette, not the skewed isometric edge.
const frontTipYRaw = projectRaw(regions.length - 1 + PAD, productLines.length - 1 + PAD, 0)[1];
const leftTipXRaw = projectRaw(-PAD, productLines.length - 1 + PAD, 0)[0];
const xLabelYRaw = frontTipYRaw + LABEL_MARGIN;
const yLabelXRaw = leftTipXRaw - LABEL_MARGIN - 70;
regions.forEach((_, col) => rawPoints.push([projectRaw(col, midRow, 0)[0], xLabelYRaw]));
productLines.forEach((_, row) => rawPoints.push([yLabelXRaw, projectRaw(midCol, row, 0)[1]]));

const rawXs = rawPoints.map((p) => p[0]);
const rawYs = rawPoints.map((p) => p[1]);
const rawMinX = Math.min(...rawXs);
const rawMaxX = Math.max(...rawXs);
const rawMinY = Math.min(...rawYs);
const rawMaxY = Math.max(...rawYs);

const drawWidth = size.width - LEFT_MARGIN - RIGHT_MARGIN;
const drawHeight = size.height - TOP_MARGIN - BOTTOM_MARGIN;
const originX = LEFT_MARGIN + (drawWidth - (rawMaxX - rawMinX)) / 2 - rawMinX;
const originY = TOP_MARGIN + (drawHeight - (rawMaxY - rawMinY)) / 2 - rawMinY;

function project(col, row, z) {
  const [x, y] = projectRaw(col, row, z);
  return [x + originX, y + originY];
}

// --- Graphic elements --------------------------------------------------------
function gridLine(p1, p2) {
  return {
    type: "line",
    shape: { x1: p1[0], y1: p1[1], x2: p2[0], y2: p2[1] },
    style: { stroke: t.grid, lineWidth: 1.5 },
    silent: true,
  };
}
function polygon(points, fill) {
  return {
    type: "polygon",
    shape: { points },
    style: { fill, stroke: t.pageBg, lineWidth: 1.5 },
    silent: true,
  };
}

const graphicElements = [];

// Floor grid — relates bars to their categorical position
for (let row = 0; row <= productLines.length; row++) {
  graphicElements.push(gridLine(project(-PAD, row - PAD, 0), project(regions.length - 1 + PAD, row - PAD, 0)));
}
for (let col = 0; col <= regions.length; col++) {
  graphicElements.push(gridLine(project(col - PAD, -PAD, 0), project(col - PAD, productLines.length - 1 + PAD, 0)));
}

// Bars — each drawn as three shaded faces (top, left, right) for a 3D look
bars.forEach(({ col, row, value }) => {
  const h = barHeight(value);
  const topColor = colorForValue(value);
  const rightColor = shade(topColor, 0.82);
  const leftColor = shade(topColor, 0.62);

  const baseFront = project(col + PAD, row + PAD, 0);
  const baseLeft = project(col - PAD, row + PAD, 0);
  const baseRight = project(col + PAD, row - PAD, 0);
  const topFront = project(col + PAD, row + PAD, h);
  const topLeft = project(col - PAD, row + PAD, h);
  const topRight = project(col + PAD, row - PAD, h);
  const topBack = project(col - PAD, row - PAD, h);
  const topCenter = project(col, row, h);

  graphicElements.push(polygon([baseLeft, baseFront, topFront, topLeft], leftColor));
  graphicElements.push(polygon([baseFront, baseRight, topRight, topFront], rightColor));
  graphicElements.push(polygon([topBack, topLeft, topFront, topRight], topColor));

  graphicElements.push({
    type: "text",
    style: {
      text: String(value),
      x: topCenter[0],
      y: topBack[1] - 12,
      fill: t.ink,
      fontSize: 15,
      fontWeight: 600,
      align: "center",
      verticalAlign: "bottom",
    },
    silent: true,
  });
});

// Axis category labels — straight lanes outside the grid silhouette
regions.forEach((label, col) => {
  const x = project(col, midRow, 0)[0];
  graphicElements.push({
    type: "text",
    style: { text: label, x, y: frontTipYRaw + originY + LABEL_MARGIN, fill: t.inkSoft, fontSize: 15, align: "center", verticalAlign: "top" },
    silent: true,
  });
});
productLines.forEach((label, row) => {
  const y = project(midCol, row, 0)[1];
  graphicElements.push({
    type: "text",
    style: { text: label, x: leftTipXRaw + originX - LABEL_MARGIN, y, fill: t.inkSoft, fontSize: 15, align: "right", verticalAlign: "middle" },
    silent: true,
  });
});

// Color legend — value magnitude -> Imprint sequential gradient
const legendX = size.width - 110;
const legendTop = TOP_MARGIN + 40;
const legendHeight = 340;
const legendWidth = 26;

graphicElements.push({
  type: "text",
  style: {
    text: "Satisfaction\nscore",
    x: legendX + legendWidth / 2,
    y: legendTop - 20,
    fill: t.inkSoft,
    fontSize: 14,
    align: "center",
    verticalAlign: "bottom",
  },
});
graphicElements.push({
  type: "rect",
  shape: { x: legendX, y: legendTop, width: legendWidth, height: legendHeight },
  style: {
    fill: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: t.seq[1] },
      { offset: 1, color: t.seq[0] },
    ]),
    stroke: t.inkSoft,
    lineWidth: 1,
  },
});
graphicElements.push({
  type: "text",
  style: { text: String(maxValue), x: legendX + legendWidth + 10, y: legendTop, fill: t.inkSoft, fontSize: 14, verticalAlign: "middle" },
});
graphicElements.push({
  type: "text",
  style: { text: String(minValue), x: legendX + legendWidth + 10, y: legendTop + legendHeight, fill: t.inkSoft, fontSize: 14, verticalAlign: "middle" },
});

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "bar-3d-categorical · javascript · echarts · anyplot.ai",
    left: "center",
    top: 30,
    textStyle: { color: t.ink, fontSize: 22 },
  },
  graphic: graphicElements,
});
