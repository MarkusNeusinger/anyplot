// anyplot.ai
// choropleth-basic: Choropleth Map with Regional Coloring
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
// `muted` isn't part of ANYPLOT_TOKENS — derive it from the theme, matching
// the Imprint semantic anchor in prompts/default-style-guide.md.
const MUTED = t.theme === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic) ----------------------------------------
// Illustrative renewable-electricity share (%) of generation, one synthetic
// value per U.S. state. Laid out as an equal-area tile grid ("state grid
// map" cartogram) rather than literal shapefile boundaries — the renderer
// runs offline with no network/topojson access, and every state keeps the
// same visual weight regardless of its true land area, a well-established
// choropleth variant for all-state comparisons (e.g. NPR's state grid maps).
let seed = 42;
function nextRandom() {
  seed = (1103515245 * seed + 12345) % 2147483648;
  return seed / 2147483648;
}

const regions = [
  { abbr: "AK", col: -1, row: 0 }, { abbr: "HI", col: -1, row: 1 },
  { abbr: "WA", col: 0, row: 0 }, { abbr: "OR", col: 0, row: 1 }, { abbr: "CA", col: 0, row: 2 },
  { abbr: "NV", col: 0, row: 3 }, { abbr: "AZ", col: 0, row: 4 },
  { abbr: "ID", col: 1, row: 0 }, { abbr: "UT", col: 1, row: 1 }, { abbr: "NM", col: 1, row: 2 },
  { abbr: "MT", col: 2, row: 0 }, { abbr: "WY", col: 2, row: 1 }, { abbr: "CO", col: 2, row: 2 },
  { abbr: "ND", col: 3, row: 0 }, { abbr: "SD", col: 3, row: 1 }, { abbr: "NE", col: 3, row: 2 },
  { abbr: "KS", col: 3, row: 3 }, { abbr: "OK", col: 3, row: 4 }, { abbr: "TX", col: 3, row: 5 },
  { abbr: "MN", col: 4, row: 0 }, { abbr: "IA", col: 4, row: 1 }, { abbr: "MO", col: 4, row: 2 },
  { abbr: "AR", col: 4, row: 3 }, { abbr: "LA", col: 4, row: 4 },
  { abbr: "WI", col: 5, row: 0 }, { abbr: "IL", col: 5, row: 1 }, { abbr: "KY", col: 5, row: 2 },
  { abbr: "TN", col: 5, row: 3 }, { abbr: "MS", col: 5, row: 4 }, { abbr: "AL", col: 5, row: 5 },
  { abbr: "MI", col: 6, row: 0 }, { abbr: "IN", col: 6, row: 1 }, { abbr: "OH", col: 6, row: 2 },
  { abbr: "WV", col: 6, row: 3 }, { abbr: "VA", col: 6, row: 4 }, { abbr: "NC", col: 6, row: 5 },
  { abbr: "SC", col: 6, row: 6 }, { abbr: "GA", col: 6, row: 7 }, { abbr: "FL", col: 6, row: 8 },
  { abbr: "NY", col: 7, row: 0 }, { abbr: "PA", col: 7, row: 1 }, { abbr: "NJ", col: 7, row: 2 },
  { abbr: "DE", col: 7, row: 3 }, { abbr: "MD", col: 7, row: 4 },
  { abbr: "VT", col: 8, row: 0 }, { abbr: "MA", col: 8, row: 1 }, { abbr: "CT", col: 8, row: 2 },
  { abbr: "RI", col: 8, row: 3 },
  { abbr: "ME", col: 9, row: 0 }, { abbr: "NH", col: 9, row: 1 },
].map((d) => ({ ...d, value: Math.round(5 + nextRandom() * 90) }));

// Two states illustrate graceful handling of missing data (spec requirement).
const noDataStates = new Set(["WY", "SC"]);
for (const region of regions) {
  if (noDataStates.has(region.abbr)) region.value = null;
}

// --- Layout -------------------------------------------------------------
const margin = { top: 150, right: 70, bottom: 40, left: 70 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

const x = d3.scaleBand().domain(d3.range(-1, 10)).range([0, iw]).padding(0.1);
const y = d3.scaleBand().domain(d3.range(0, 9)).range([0, ih]).padding(0.1);

const valueExtent = d3.extent(regions.filter((d) => d.value != null), (d) => d.value);
const color = d3.scaleSequential(d3.interpolateRgbBasis(t.seq)).domain(valueExtent);

// Pick dark or light label ink from the tile's own fill luminance, independent
// of page theme — a pale tile needs dark text even on the dark surface.
function labelInk(hex) {
  const c = d3.rgb(hex);
  const luminance = 0.299 * c.r + 0.587 * c.g + 0.114 * c.b;
  return luminance > 150 ? "#1A1A17" : "#F0EFE8";
}

// --- SVG mount ----------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Tiles ----------------------------------------------------------------
const tile = g
  .selectAll("g.tile")
  .data(regions)
  .join("g")
  .attr("class", "tile")
  .attr("transform", (d) => `translate(${x(d.col)},${y(d.row)})`);

tile
  .append("rect")
  .attr("width", x.bandwidth())
  .attr("height", y.bandwidth())
  .attr("rx", 4)
  .attr("fill", (d) => (d.value == null ? MUTED : color(d.value)))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 3);

tile
  .append("text")
  .attr("x", x.bandwidth() / 2)
  .attr("y", y.bandwidth() / 2)
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "central")
  .style("font-size", "16px")
  .style("font-weight", "600")
  .attr("fill", (d) => labelInk(d.value == null ? MUTED : color(d.value)))
  .text((d) => d.abbr);

// --- Title ------------------------------------------------------------------
const title = "Renewable Electricity Share · choropleth-basic · javascript · d3 · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / title.length));
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(title);

// --- Legend (sequential gradient + no-data swatch) --------------------------
const legendWidth = 260;
const legendHeight = 18;
const noDataSwatchGap = 20;
const noDataLabelWidth = 60;
const legendTotalWidth = legendWidth + noDataSwatchGap + legendHeight + 8 + noDataLabelWidth;
const legendX = width - 20 - legendTotalWidth;
const legendY = 95;

const gradientId = "choropleth-legend-gradient";
const gradient = svg
  .append("defs")
  .append("linearGradient")
  .attr("id", gradientId)
  .attr("x1", "0%")
  .attr("x2", "100%")
  .attr("y1", "0%")
  .attr("y2", "0%");
d3.range(0, 1.001, 0.1).forEach((stop) => {
  gradient
    .append("stop")
    .attr("offset", `${stop * 100}%`)
    .attr("stop-color", color(valueExtent[0] + stop * (valueExtent[1] - valueExtent[0])));
});

svg
  .append("text")
  .attr("x", legendX)
  .attr("y", legendY - 12)
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Renewable electricity share (%)");

svg
  .append("rect")
  .attr("x", legendX)
  .attr("y", legendY)
  .attr("width", legendWidth)
  .attr("height", legendHeight)
  .attr("fill", `url(#${gradientId})`);

svg
  .append("text")
  .attr("x", legendX)
  .attr("y", legendY + legendHeight + 20)
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .text(`${valueExtent[0]}%`);

svg
  .append("text")
  .attr("x", legendX + legendWidth)
  .attr("y", legendY + legendHeight + 20)
  .attr("text-anchor", "end")
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .text(`${valueExtent[1]}%`);

svg
  .append("rect")
  .attr("x", legendX + legendWidth + noDataSwatchGap)
  .attr("y", legendY)
  .attr("width", legendHeight)
  .attr("height", legendHeight)
  .attr("rx", 3)
  .attr("fill", MUTED);

svg
  .append("text")
  .attr("x", legendX + legendWidth + noDataSwatchGap + legendHeight + 8)
  .attr("y", legendY + legendHeight - 4)
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .text("No data");
