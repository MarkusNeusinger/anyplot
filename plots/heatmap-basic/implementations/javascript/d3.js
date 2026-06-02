// anyplot.ai
// heatmap-basic: Basic Heatmap
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-02
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 150, right: 180, bottom: 60, left: 220 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Data — asset-class correlation matrix (symmetric, diagonal = 1), the canonical
// diverging-heatmap scenario from the spec's applications. Values are hand-tuned
// to reflect typical post-2020 regime correlations: equities cluster positive,
// long-duration bonds anti-correlate with risk assets, gold sits near-zero.
const assets = [
  "US Equities",
  "EU Equities",
  "EM Equities",
  "REITs",
  "High Yield",
  "IG Credit",
  "Treasuries",
  "Gold",
  "Oil",
  "USD Cash",
];

const corr = [
  [1.00,  0.84,  0.72,  0.68,  0.71,  0.42, -0.34,  0.08,  0.38, -0.28],
  [0.84,  1.00,  0.78,  0.62,  0.66,  0.45, -0.30,  0.12,  0.35, -0.31],
  [0.72,  0.78,  1.00,  0.55,  0.61,  0.38, -0.38,  0.18,  0.44, -0.42],
  [0.68,  0.62,  0.55,  1.00,  0.58,  0.48, -0.12,  0.10,  0.28, -0.18],
  [0.71,  0.66,  0.61,  0.58,  1.00,  0.66, -0.22,  0.05,  0.32, -0.20],
  [0.42,  0.45,  0.38,  0.48,  0.66,  1.00,  0.52,  0.14,  0.08,  0.06],
  [-0.34, -0.30, -0.38, -0.12, -0.22,  0.52,  1.00,  0.22, -0.18,  0.38],
  [0.08,  0.12,  0.18,  0.10,  0.05,  0.14,  0.22,  1.00,  0.26,  0.15],
  [0.38,  0.35,  0.44,  0.28,  0.32,  0.08, -0.18,  0.26,  1.00, -0.22],
  [-0.28, -0.31, -0.42, -0.18, -0.20,  0.06,  0.38,  0.15, -0.22,  1.00],
];

// SVG mount
const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Scales
const x = d3.scaleBand().domain(assets).range([0, iw]).padding(0.04);
const y = d3.scaleBand().domain(assets).range([0, ih]).padding(0.04);

// Imprint diverging colormap — three stops, midpoint already theme-adaptive
const color = d3.scaleSequential(d3.interpolateRgbBasis(t.div)).domain([-1, 1]);

// Cells (flattened)
const cells = [];
for (let i = 0; i < assets.length; i++) {
  for (let j = 0; j < assets.length; j++) {
    cells.push({ row: assets[i], col: assets[j], value: corr[i][j] });
  }
}

// Cell rectangles
g.selectAll("rect.cell").data(cells).join("rect")
  .attr("class", "cell")
  .attr("x", (d) => x(d.col))
  .attr("y", (d) => y(d.row))
  .attr("width", x.bandwidth())
  .attr("height", y.bandwidth())
  .attr("fill", (d) => color(d.value));

// Value annotations — switch to page-bg text on saturated cells for legibility
g.selectAll("text.value").data(cells).join("text")
  .attr("class", "value")
  .attr("x", (d) => x(d.col) + x.bandwidth() / 2)
  .attr("y", (d) => y(d.row) + y.bandwidth() / 2)
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "central")
  .style("font-size", "22px")
  .style("font-weight", "500")
  .attr("fill", (d) => (Math.abs(d.value) > 0.55 ? t.pageBg : t.ink))
  .text((d) => d.value.toFixed(2));

// Column labels — rotated above the matrix
const xAxis = g.append("g")
  .attr("transform", "translate(0,0)")
  .call(d3.axisTop(x).tickSize(0).tickPadding(14));
xAxis.select(".domain").remove();
xAxis.selectAll("text")
  .attr("fill", t.inkSoft)
  .style("font-size", "24px")
  .style("font-weight", "500")
  .attr("transform", "rotate(-38)")
  .style("text-anchor", "start");

// Row labels — left of the matrix
const yAxis = g.append("g").call(d3.axisLeft(y).tickSize(0).tickPadding(14));
yAxis.select(".domain").remove();
yAxis.selectAll("text")
  .attr("fill", t.inkSoft)
  .style("font-size", "24px")
  .style("font-weight", "500");

// Title
svg.append("text")
  .attr("x", width / 2).attr("y", 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "38px")
  .style("font-weight", "600")
  .text("heatmap-basic · javascript · d3 · anyplot.ai");

// Colorbar — vertical gradient strip + axis
const cbWidth = 38;
const cbHeight = ih;
const cbX = iw + 70;

const defs = svg.append("defs");
const grad = defs.append("linearGradient")
  .attr("id", "cbgrad")
  .attr("x1", "0%").attr("y1", "0%")
  .attr("x2", "0%").attr("y2", "100%");
const nStops = 32;
for (let i = 0; i <= nStops; i++) {
  const u = i / nStops;
  grad.append("stop")
    .attr("offset", `${u * 100}%`)
    .attr("stop-color", color(1 - 2 * u));
}

g.append("rect")
  .attr("x", cbX).attr("y", 0)
  .attr("width", cbWidth).attr("height", cbHeight)
  .attr("fill", "url(#cbgrad)")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 0.6);

const cbScale = d3.scaleLinear().domain([1, -1]).range([0, cbHeight]);
const cbAxis = g.append("g")
  .attr("transform", `translate(${cbX + cbWidth}, 0)`)
  .call(
    d3.axisRight(cbScale)
      .tickValues([-1, -0.5, 0, 0.5, 1])
      .tickFormat(d3.format("+.1f"))
      .tickSize(8),
  );
cbAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "22px");
cbAxis.selectAll("line").attr("stroke", t.inkSoft);
cbAxis.select(".domain").attr("stroke", t.inkSoft);

// Colorbar caption
g.append("text")
  .attr("x", cbX + cbWidth / 2).attr("y", -22)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "22px")
  .style("font-weight", "500")
  .text("Pearson r");
