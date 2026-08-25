// anyplot.ai
// heatmap-stripes-climate: Climate Warming Stripes
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-25

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const titleArea = 64;

// --- Data: global mean temperature anomaly, 1850-2024, °C vs 1961-1990 baseline
// Deterministic LCG (browser has no seeded Math.random) -----------------------
let seed = 42;
function lcgNoise() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296 - 0.5;
}

const startYear = 1850;
const endYear = 2024;
const years = d3.range(startYear, endYear + 1);
const anomalies = years.map((year) => {
  const progress = (year - startYear) / (endYear - startYear);
  // Long-term warming trend: slow pre-industrial drift, sharp post-1980 rise.
  const trend = -0.35 + 1.55 * Math.pow(progress, 1.7);
  const noise = lcgNoise() * 0.24;
  return trend + noise;
});

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Color scale: symmetric diverging, cold->blue, warm->red (Imprint stops) --
// Semantic exception (temperature hot->red / cold->blue) — reorder the Imprint
// diverging stops so negative anomalies read blue and positive anomalies read red.
const extent = d3.max(anomalies, (d) => Math.abs(d));
const stripeColor = d3
  .scaleSequential(d3.interpolateRgbBasis([t.div[2], t.div[1], t.div[0]]))
  .domain([-extent, extent]);

// --- Stripes: equal-width bars, no gaps, edge-to-edge ---------------------------
const x = d3.scaleBand().domain(years).range([0, width]).padding(0);
const stripeTop = titleArea;
const stripeHeight = height - titleArea;

svg
  .selectAll("rect")
  .data(years)
  .join("rect")
  .attr("x", (d) => x(d))
  .attr("y", stripeTop)
  .attr("width", x.bandwidth() + 0.5) // 0.5px overlap avoids antialiasing seams between bars
  .attr("height", stripeHeight)
  .attr("fill", (d, i) => stripeColor(anomalies[i]));

// --- Title ----------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 40)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "20px")
  .style("font-weight", "600")
  .text("heatmap-stripes-climate · javascript · d3 · anyplot.ai");
