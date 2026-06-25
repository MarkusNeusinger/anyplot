// anyplot.ai
// contour-basic: Basic Contour Plot
// Library: d3 7.9.0 | JavaScript 22.23.0
// Quality: 89/100 | Created: 2026-06-25

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 70, right: 130, bottom: 72, left: 80 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: "peaks" function on [-3, 3] × [-3, 3], produces both positive and negative values ---
const nx = 80, ny = 80;
const values = new Float64Array(nx * ny);
for (let j = 0; j < ny; j++) {
  for (let i = 0; i < nx; i++) {
    const x = -3 + 6 * i / (nx - 1);
    const y = 3 - 6 * j / (ny - 1); // j=0 → y=3 (top), j=ny-1 → y=-3 (bottom)
    const x2 = x * x, y2 = y * y;
    values[j * nx + i] =
      3 * (1 - x) * (1 - x) * Math.exp(-x2 - (y + 1) * (y + 1)) -
      10 * (x / 5 - x * x2 - y * y2 * y2) * Math.exp(-x2 - y2) -
      (1 / 3) * Math.exp(-(x + 1) * (x + 1) - y2);
  }
}
const vmin = d3.min(values);
const vmax = d3.max(values);
const absMax = Math.max(Math.abs(vmin), Math.abs(vmax));

// --- SVG mount ---
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const defs = svg.append("defs");

defs.append("clipPath").attr("id", "pc")
  .append("rect").attr("width", iw).attr("height", ih);

const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Contour generation ---
const numLevels = 18;
const thresholds = d3.range(numLevels + 1).map(i => -absMax + 2 * absMax * i / numLevels);
const contoursData = d3.contours().size([nx, ny]).thresholds(thresholds)(values);

// Projection: grid space [0..nx] × [0..ny] → plot area [0..iw] × [0..ih]
const geoProj = d3.geoTransform({
  point: function(px, py) { this.stream.point(px * iw / nx, py * ih / ny); }
});
const pathGen = d3.geoPath(geoProj);

// Diverging Imprint colormap: red (negative) → near-bg → blue (positive)
const colorScale = d3.scaleSequential(d3.interpolateRgbBasis(t.div)).domain([-absMax, absMax]);

// --- Filled contour bands (clipped to plot area) ---
const cg = g.append("g").attr("clip-path", "url(#pc)");

cg.selectAll(".cf").data(contoursData).join("path")
  .attr("class", "cf").attr("d", pathGen)
  .attr("fill", d => colorScale(d.value)).attr("stroke", "none");

// --- Contour isolines (thin, semi-transparent) ---
cg.selectAll(".cl").data(contoursData).join("path")
  .attr("class", "cl").attr("d", pathGen)
  .attr("fill", "none")
  .attr("stroke", t.ink).attr("stroke-width", 0.7).attr("stroke-opacity", 0.2);

// --- Plot border (all four sides — standard for contour plots) ---
g.append("rect").attr("width", iw).attr("height", ih)
  .attr("fill", "none").attr("stroke", t.inkSoft).attr("stroke-width", 1);

// --- Axes ---
const xScale = d3.scaleLinear().domain([-3, 3]).range([0, iw]);
const yScale = d3.scaleLinear().domain([3, -3]).range([0, ih]);

const xAx = g.append("g").attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(xScale).ticks(7).tickSize(5).tickPadding(6));
xAx.select(".domain").remove();
xAx.selectAll(".tick line").attr("stroke", t.inkSoft);
xAx.selectAll(".tick text").attr("fill", t.inkSoft).style("font-size", "14px");

const yAx = g.append("g")
  .call(d3.axisLeft(yScale).ticks(7).tickSize(5).tickPadding(6));
yAx.select(".domain").remove();
yAx.selectAll(".tick line").attr("stroke", t.inkSoft);
yAx.selectAll(".tick text").attr("fill", t.inkSoft).style("font-size", "14px");

// --- Axis labels ---
g.append("text")
  .attr("x", iw / 2).attr("y", ih + 58)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "16px")
  .text("x");

g.append("text")
  .attr("transform", `translate(-56,${ih / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "16px")
  .text("y");

// --- Colorbar ---
const cbW = 18, cbX = iw + 32;
const cbGrad = defs.append("linearGradient").attr("id", "cbg")
  .attr("x1", "0%").attr("y1", "100%").attr("x2", "0%").attr("y2", "0%");
for (let s = 0; s <= 30; s++) {
  const f = s / 30;
  cbGrad.append("stop")
    .attr("offset", `${(f * 100).toFixed(1)}%`)
    .attr("stop-color", colorScale(-absMax + 2 * absMax * f));
}

g.append("rect")
  .attr("x", cbX).attr("y", 0).attr("width", cbW).attr("height", ih)
  .style("fill", "url(#cbg)").attr("stroke", t.inkSoft).attr("stroke-width", 0.5);

const cbScale = d3.scaleLinear().domain([-absMax, absMax]).range([ih, 0]);
const cbAx = g.append("g").attr("transform", `translate(${cbX + cbW},0)`)
  .call(d3.axisRight(cbScale).ticks(6).tickFormat(d3.format(".1f")));
cbAx.selectAll(".tick text").attr("fill", t.inkSoft).style("font-size", "12px");
cbAx.selectAll(".tick line").attr("stroke", t.inkSoft);
cbAx.select(".domain").attr("stroke", t.inkSoft);

g.append("text")
  .attr("transform", `translate(${cbX + cbW + 60},${ih / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft).style("font-size", "13px")
  .text("z (field value)");

// --- Title ---
svg.append("text")
  .attr("x", width / 2).attr("y", 46)
  .attr("text-anchor", "middle").attr("fill", t.ink)
  .style("font-size", "22px").style("font-weight", "600")
  .text("contour-basic · javascript · d3 · anyplot.ai");
