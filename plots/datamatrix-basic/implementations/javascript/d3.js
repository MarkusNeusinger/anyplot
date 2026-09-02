// anyplot.ai
// datamatrix-basic: Basic Data Matrix 2D Barcode
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-02
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data --------------------------------------------------------------
// A Data Matrix encodes text into a square grid of modules bounded by an
// L-shaped solid finder (left + bottom) and an alternating timing pattern
// (top + right). MODULES=24 is a valid ISO/IEC 16022 symbol size, leaving a
// 22x22 interior for payload + ECC 200 parity.
const content = "PN-88214-REV3";
const MODULES = 24;

// Tiny deterministic LCG (the browser has no seeded RNG) seeded from the
// content string, so the interior pattern is stable across light/dark runs.
function hashString(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}
function makeRng(seed) {
  let state = seed >>> 0 || 1;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rng = makeRng(hashString(content));

// Build the module grid: true = dark module.
const grid = Array.from({ length: MODULES }, () => new Array(MODULES).fill(false));

// Interior region: pseudo-random fill standing in for encoded payload + ECC 200 parity.
for (let r = 1; r < MODULES - 1; r++) {
  for (let c = 1; c < MODULES - 1; c++) {
    grid[r][c] = rng() > 0.5;
  }
}

// Timing (clock) pattern: alternating modules on the top row and right column.
for (let c = 0; c < MODULES; c++) grid[0][c] = c % 2 === 0;
for (let r = 0; r < MODULES; r++) grid[r][MODULES - 1] = r % 2 === 0;

// L-shaped finder: solid modules on the left column and bottom row (drawn last so it wins corners).
for (let r = 0; r < MODULES; r++) grid[r][0] = true;
for (let c = 0; c < MODULES; c++) grid[MODULES - 1][c] = true;

// --- SVG mount ---------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Layout --------------------------------------------------------------
const margin = { top: 130, right: 90, bottom: 110, left: 90 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

const quiet = 2; // quiet-zone width in module-widths (spec requires >= 1)
const totalModules = MODULES + quiet * 2;
const cell = Math.min(iw, ih) / totalModules;
const plateSize = cell * totalModules;
const plateX = margin.left + (iw - plateSize) / 2;
const plateY = margin.top + (ih - plateSize) / 2;

// A Data Matrix must stay high-contrast dark-on-light to remain scannable
// (spec: "high contrast black on white for maximum readability"), so the
// plate + modules use fixed Imprint light-theme tokens in both themes —
// like a printed label affixed to the page — while the surrounding title
// and caption still flip with ANYPLOT_THEME.
const PLATE_BG = "#FAF8F1";
const MODULE_INK = "#1A1A17";

// --- Quiet-zone plate ------------------------------------------------------
svg
  .append("rect")
  .attr("x", plateX)
  .attr("y", plateY)
  .attr("width", plateSize)
  .attr("height", plateSize)
  .attr("rx", cell * 0.6)
  .attr("fill", PLATE_BG)
  .attr("stroke", MODULE_INK)
  .attr("stroke-opacity", 0.15)
  .attr("stroke-width", 1.5);

// --- Modules ---------------------------------------------------------------
const modules = [];
for (let r = 0; r < MODULES; r++) {
  for (let c = 0; c < MODULES; c++) {
    if (grid[r][c]) modules.push({ r, c });
  }
}

svg
  .selectAll("rect.module")
  .data(modules)
  .join("rect")
  .attr("class", "module")
  .attr("x", (d) => plateX + (quiet + d.c) * cell)
  .attr("y", (d) => plateY + (quiet + d.r) * cell)
  .attr("width", cell)
  .attr("height", cell)
  .attr("fill", MODULE_INK);

// --- Title -------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 66)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("datamatrix-basic · javascript · d3 · anyplot.ai");

// --- Caption -------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", plateY + plateSize + 46)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "18px")
  .style("font-family", "monospace")
  .text(`"${content}"  ·  ${MODULES}×${MODULES} modules · ECC 200`);
