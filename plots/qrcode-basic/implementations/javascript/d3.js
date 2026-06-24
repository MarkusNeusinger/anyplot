// anyplot.ai
// qrcode-basic: Basic QR Code Generator
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-24

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

const ENCODED_URL = "https://anyplot.ai";

// QR code matrix for https://anyplot.ai (Version 2, Error Correction M)
const QR_MATRIX = [
  [1,1,1,1,1,1,1,0,1,0,0,1,1,0,1,0,0,0,1,1,1,1,1,1,1],
  [1,0,0,0,0,0,1,0,1,0,1,1,1,1,1,0,1,0,1,0,0,0,0,0,1],
  [1,0,1,1,1,0,1,0,1,0,1,0,0,1,1,1,1,0,1,0,1,1,1,0,1],
  [1,0,1,1,1,0,1,0,0,1,0,0,1,0,1,0,1,0,1,0,1,1,1,0,1],
  [1,0,1,1,1,0,1,0,1,0,1,0,1,1,1,0,1,0,1,0,1,1,1,0,1],
  [1,0,0,0,0,0,1,0,0,1,1,1,0,1,1,0,1,0,1,0,0,0,0,0,1],
  [1,1,1,1,1,1,1,0,1,0,1,0,1,0,1,0,1,0,1,1,1,1,1,1,1],
  [0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,1,1,0,0,0,0,0,0,0,0],
  [1,0,0,1,1,1,1,1,1,1,0,1,1,1,1,0,1,1,0,0,1,0,1,1,1],
  [0,0,1,0,1,0,0,1,0,0,1,0,0,0,1,1,1,0,0,1,1,1,1,1,0],
  [1,0,0,0,0,1,1,1,1,0,1,1,0,0,1,1,0,0,0,1,1,1,0,0,1],
  [0,1,1,1,1,1,0,1,0,1,0,1,0,0,1,0,0,1,0,0,0,1,1,1,1],
  [1,0,1,1,1,0,1,0,1,1,1,1,0,1,1,1,0,0,1,1,0,0,0,0,1],
  [1,0,0,0,1,0,0,0,0,0,1,0,1,0,0,1,1,1,0,0,1,0,0,1,0],
  [1,1,0,0,0,0,1,1,1,1,0,0,0,0,1,1,0,0,0,0,1,1,1,1,1],
  [1,0,0,1,0,1,0,0,1,0,0,0,1,1,1,1,0,1,1,1,0,1,1,0,1],
  [1,0,1,1,1,0,1,0,1,0,1,1,1,0,0,0,1,1,1,1,1,0,1,1,0],
  [0,0,0,0,0,0,0,0,1,1,0,1,0,0,0,0,1,0,0,0,1,0,1,1,0],
  [1,1,1,1,1,1,1,0,1,0,1,0,1,1,1,0,1,0,1,0,1,0,0,0,1],
  [1,0,0,0,0,0,1,0,1,0,1,1,0,1,0,1,1,0,0,0,1,0,0,0,0],
  [1,0,1,1,1,0,1,0,1,0,1,1,0,1,0,1,1,1,1,1,1,0,0,0,1],
  [1,0,1,1,1,0,1,0,1,1,1,0,1,1,0,0,1,1,1,0,0,0,0,1,1],
  [1,0,1,1,1,0,1,0,0,0,0,1,0,1,0,0,1,0,0,0,1,1,1,1,1],
  [1,0,0,0,0,0,1,0,0,1,0,1,1,1,0,0,0,1,1,1,1,0,1,1,1],
  [1,1,1,1,1,1,1,0,1,1,0,1,1,1,0,0,1,1,1,0,0,1,0,0,1],
];

const QR_SIZE = QR_MATRIX.length;
const QUIET_ZONE = 4;
const TOTAL_MODULES = QR_SIZE + QUIET_ZONE * 2;

// Layout
const TITLE_Y = 52;
const QR_TOP = TITLE_Y + 36;
const LABEL_RESERVE = 80;
const CELL = Math.floor(
  Math.min((width - 80) / TOTAL_MODULES, (height - QR_TOP - LABEL_RESERVE) / TOTAL_MODULES)
);
const QR_PX = CELL * TOTAL_MODULES;
const QR_X = Math.floor((width - QR_PX) / 2);
const QR_Y = QR_TOP;

// QR module colors — high contrast for scanner readability
const MODULE_ON = "#1A1A17";
const MODULE_OFF = "#FAF8F1";

// SVG
const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);

// QR card — warm white background covers full area including quiet zone
svg.append("rect")
  .attr("x", QR_X)
  .attr("y", QR_Y)
  .attr("width", QR_PX)
  .attr("height", QR_PX)
  .attr("fill", MODULE_OFF)
  .attr("rx", 10)
  .attr("ry", 10);

// Subtle card border in dark theme for visual separation
if (window.ANYPLOT_THEME === "dark") {
  svg.append("rect")
    .attr("x", QR_X)
    .attr("y", QR_Y)
    .attr("width", QR_PX)
    .attr("height", QR_PX)
    .attr("fill", "none")
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1.5)
    .attr("stroke-opacity", 0.25)
    .attr("rx", 10)
    .attr("ry", 10);
}

// Draw dark modules only (light modules are the card background)
QR_MATRIX.forEach((row, ri) => {
  row.forEach((cell, ci) => {
    if (!cell) return;
    svg.append("rect")
      .attr("x", QR_X + (QUIET_ZONE + ci) * CELL)
      .attr("y", QR_Y + (QUIET_ZONE + ri) * CELL)
      .attr("width", CELL)
      .attr("height", CELL)
      .attr("fill", MODULE_ON);
  });
});

// Title
svg.append("text")
  .attr("x", width / 2)
  .attr("y", TITLE_Y)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("qrcode-basic · javascript · d3 · anyplot.ai");

// URL label below QR code
svg.append("text")
  .attr("x", width / 2)
  .attr("y", QR_Y + QR_PX + 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "18px")
  .text(ENCODED_URL);
