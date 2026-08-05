//# anyplot-orientation: square
// anyplot.ai
// heatmap-annotated: Annotated Heatmap
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data: deterministic pseudo-random correlation matrix (LCG) ------------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

const variables = [
  "Temperature",
  "Humidity",
  "Wind Speed",
  "Pressure",
  "Rainfall",
  "Cloud Cover",
  "UV Index",
  "Visibility",
];
const n = variables.length;

const corr = Array.from({ length: n }, () => new Array(n).fill(0));
for (let i = 0; i < n; i++) {
  corr[i][i] = 1;
  for (let j = i + 1; j < n; j++) {
    let value = Math.round((rand() * 2 - 1) * 100) / 100;
    if (value === 0) value = 0; // normalize -0 to 0 for clean formatting
    corr[i][j] = value;
    corr[j][i] = value;
  }
}

const cells = [];
for (let i = 0; i < n; i++) {
  for (let j = 0; j < n; j++) {
    cells.push({ row: variables[i], col: variables[j], value: corr[i][j] });
  }
}

// --- Layout ------------------------------------------------------------------
const margin = { top: 150, right: 230, bottom: 130, left: 190 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales --------------------------------------------------------------------
const x = d3.scaleBand().domain(variables).range([0, iw]).padding(0.04);
const y = d3.scaleBand().domain(variables).range([0, ih]).padding(0.04);
const color = d3.scaleSequential(d3.interpolateRgbBasis(t.div)).domain([-1, 1]);

// --- Contrast text color -------------------------------------------------------
function luminance(hex) {
  const c = d3.color(hex).rgb();
  const lin = (v) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
}
const DARK_TEXT = "#1A1A17";
const LIGHT_TEXT = "#F0EFE8";
function textColor(hex) {
  return luminance(hex) > 0.45 ? DARK_TEXT : LIGHT_TEXT;
}

// --- Cells -----------------------------------------------------------------
g.selectAll("rect.cell")
  .data(cells)
  .join("rect")
  .attr("class", "cell")
  .attr("x", (d) => x(d.col))
  .attr("y", (d) => y(d.row))
  .attr("width", x.bandwidth())
  .attr("height", y.bandwidth())
  .attr("fill", (d) => color(d.value))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2);

// --- Cell value annotations --------------------------------------------------
const cellFontSize = Math.max(13, Math.min(22, x.bandwidth() / 3.6));
g.selectAll("text.cell-label")
  .data(cells)
  .join("text")
  .attr("class", "cell-label")
  .attr("x", (d) => x(d.col) + x.bandwidth() / 2)
  .attr("y", (d) => y(d.row) + y.bandwidth() / 2)
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "central")
  .style("font-size", `${cellFontSize}px`)
  .style("font-weight", (d) => (d.row === d.col || Math.abs(d.value) > 0.6 ? 600 : 400))
  .attr("fill", (d) => textColor(color(d.value)))
  .text((d) => d.value.toFixed(2));

// --- Axes ------------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).tickSize(0));
xAxis
  .selectAll("text")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .attr("transform", "rotate(-35)")
  .attr("text-anchor", "end")
  .attr("dx", "-0.4em")
  .attr("dy", "0.4em");
xAxis.select(".domain").remove();

const yAxis = g.append("g").call(d3.axisLeft(y).tickSize(0));
yAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
yAxis.select(".domain").remove();

// --- Colorbar legend -----------------------------------------------------------
const legendW = 34;
const legendH = ih * 0.62;
const legendX = margin.left + iw + 70;
const legendY = margin.top + (ih - legendH) / 2;

const defs = svg.append("defs");
const gradient = defs
  .append("linearGradient")
  .attr("id", "corr-gradient")
  .attr("x1", "0")
  .attr("x2", "0")
  .attr("y1", "1")
  .attr("y2", "0");
gradient
  .selectAll("stop")
  .data(d3.range(0, 1.0001, 0.1))
  .join("stop")
  .attr("offset", (d) => `${d * 100}%`)
  .attr("stop-color", (d) => color(-1 + d * 2));

svg
  .append("rect")
  .attr("x", legendX)
  .attr("y", legendY)
  .attr("width", legendW)
  .attr("height", legendH)
  .attr("fill", "url(#corr-gradient)")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1);

const legendScale = d3.scaleLinear().domain([-1, 1]).range([legendY + legendH, legendY]);
const legendAxis = d3.axisRight(legendScale).ticks(5).tickSize(6);
const legendAxisG = svg.append("g").attr("transform", `translate(${legendX + legendW},0)`).call(legendAxis);
legendAxisG.selectAll("text").attr("fill", t.inkSoft).style("font-size", "15px");
legendAxisG.selectAll("line").attr("stroke", t.grid);
legendAxisG.select(".domain").attr("stroke", t.inkSoft);

svg
  .append("text")
  .attr("x", legendX + legendW / 2)
  .attr("y", legendY - 22)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .style("font-weight", "600")
  .text("r");

// --- Title -------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 64)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("heatmap-annotated · javascript · d3 · anyplot.ai");

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 100)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "17px")
  .text("Pearson correlation between weather variables");
