// anyplot.ai
// mosaic-categorical: Mosaic Plot for Categorical Association Analysis
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 130, right: 60, bottom: 60, left: 70 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Web-traffic acquisition: visits by source, cross-tabulated against outcome.
const sources = ["Organic Search", "Paid Ads", "Social Media", "Referral"];
const outcomes = ["Converted", "Bounced"];
const counts = {
  "Organic Search": { Converted: 180, Bounced: 620 },
  "Paid Ads": { Converted: 150, Bounced: 350 },
  "Social Media": { Converted: 40, Bounced: 460 },
  Referral: { Converted: 90, Bounced: 110 },
};

const sourceTotals = sources.map((s) => counts[s].Converted + counts[s].Bounced);
const grandTotal = sourceTotals.reduce((a, b) => a + b, 0);
const color = d3.scaleOrdinal().domain(outcomes).range([t.palette[0], "#AE3030"]);
const LABEL_ON_FILL = "#FFFDF6"; // fixed light label ink for text on saturated data fills, both themes

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Column layout (widths = marginal share of category_1) -------------------
const gapX = 10;
const usableW = iw - gapX * (sources.length - 1);
let xCursor = 0;
const columns = sources.map((source, i) => {
  const colWidth = usableW * (sourceTotals[i] / grandTotal);
  const col = { source, x: xCursor, width: colWidth, total: sourceTotals[i] };
  xCursor += colWidth + gapX;
  return col;
});

// --- Reference y-axis (conditional proportion, shared across columns) --------
const y = d3.scaleLinear().domain([0, 1]).range([ih, 0]);
const yAxis = g.append("g").call(
  d3.axisLeft(y)
    .tickValues([0, 0.25, 0.5, 0.75, 1])
    .tickFormat(d3.format(".0%"))
    .tickSize(-iw)
);
yAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
yAxis.selectAll("line").attr("stroke", t.grid);
yAxis.select(".domain").remove();

// --- Rectangles (heights = conditional proportion within column) -------------
const gapY = 6;
const usableH = ih - gapY;

for (const col of columns) {
  const convertedFrac = counts[col.source].Converted / col.total;
  const bouncedFrac = 1 - convertedFrac;
  const convertedH = usableH * convertedFrac;
  const bouncedH = usableH * bouncedFrac;

  const cell = g.append("g").attr("transform", `translate(${col.x},0)`);

  // Converted — anchored at the bottom
  cell
    .append("rect")
    .attr("x", 0)
    .attr("y", ih - convertedH)
    .attr("width", col.width)
    .attr("height", convertedH)
    .attr("fill", color("Converted"));

  // Bounced — stacked above, separated by a gap
  cell
    .append("rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", col.width)
    .attr("height", bouncedH - gapY / 2)
    .attr("fill", color("Bounced"));

  // Percentage labels — only where the segment is tall enough to hold text
  if (convertedH > 32) {
    cell
      .append("text")
      .attr("x", col.width / 2)
      .attr("y", ih - convertedH / 2)
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "middle")
      .attr("fill", LABEL_ON_FILL)
      .style("font-size", "15px")
      .style("font-weight", "600")
      .text(d3.format(".0%")(convertedFrac));
  }
  if (bouncedH - gapY / 2 > 32) {
    cell
      .append("text")
      .attr("x", col.width / 2)
      .attr("y", (bouncedH - gapY / 2) / 2)
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "middle")
      .attr("fill", LABEL_ON_FILL)
      .style("font-size", "15px")
      .style("font-weight", "600")
      .text(d3.format(".0%")(bouncedFrac));
  }

  // Column header — source name + sample size, wrapped over two lines
  const header = g
    .append("text")
    .attr("x", col.x + col.width / 2)
    .attr("y", -38)
    .attr("text-anchor", "middle")
    .attr("fill", t.ink)
    .style("font-size", "16px")
    .style("font-weight", "600");
  header.append("tspan").attr("x", col.x + col.width / 2).attr("dy", 0).text(col.source);
  header
    .append("tspan")
    .attr("x", col.x + col.width / 2)
    .attr("dy", "1.3em")
    .attr("fill", t.inkSoft)
    .style("font-size", "13px")
    .style("font-weight", "400")
    .text(`n = ${col.total.toLocaleString()}`);
}

// --- Legend --------------------------------------------------------------------
const legend = svg.append("g").attr("transform", `translate(${width - margin.right - 220},44)`);
outcomes.forEach((outcome, i) => {
  const row = legend.append("g").attr("transform", `translate(${i * 115},0)`);
  row.append("rect").attr("width", 16).attr("height", 16).attr("rx", 3).attr("fill", color(outcome));
  row
    .append("text")
    .attr("x", 22)
    .attr("y", 13)
    .attr("fill", t.inkSoft)
    .style("font-size", "14px")
    .text(outcome);
});

// --- Title -----------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("mosaic-categorical · javascript · d3 · anyplot.ai");

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 72)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text("Traffic source vs. conversion outcome — column width = share of visits, height = conversion rate");
