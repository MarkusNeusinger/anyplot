// anyplot.ai
// polar-scatter: Polar Scatter Plot
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic LCG — wind observations) ---------------
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function noise() {
  // roughly bell-shaped in [-1, 1]
  return (rand() + rand() + rand() - 1.5) / 1.5;
}

const CATEGORY_CONFIG = [
  { category: "morning", angle: 65, angleSpread: 35, speedBase: 6, speedSpread: 3 },
  { category: "afternoon", angle: 205, angleSpread: 30, speedBase: 14, speedSpread: 4 },
  { category: "evening", angle: 245, angleSpread: 25, speedBase: 9, speedSpread: 3 },
  { category: "night", angle: 350, angleSpread: 40, speedBase: 4, speedSpread: 2 },
];
const POINTS_PER_CATEGORY = 30;

const data = [];
for (const cfg of CATEGORY_CONFIG) {
  for (let i = 0; i < POINTS_PER_CATEGORY; i++) {
    const theta = (cfg.angle + noise() * cfg.angleSpread + 360) % 360;
    const speed = Math.max(0.5, cfg.speedBase + noise() * cfg.speedSpread);
    data.push({ theta, speed, category: cfg.category });
  }
}

const categories = CATEGORY_CONFIG.map((c) => c.category);
const color = d3.scaleOrdinal().domain(categories).range(t.palette);

// --- Layout -------------------------------------------------------------
const margin = { top: 130, bottom: 110, left: 100, right: 100 };
const availableWidth = width - margin.left - margin.right;
const availableHeight = height - margin.top - margin.bottom;
const plotRadius = Math.min(availableWidth, availableHeight) / 2 - 40;
const cx = margin.left + availableWidth / 2;
const cy = margin.top + availableHeight / 2;

const maxSpeed = d3.max(data, (d) => d.speed);
const domainMax = Math.ceil(maxSpeed / 5) * 5;
const radialScale = d3.scaleLinear().domain([0, domainMax]).range([0, plotRadius]);
const radialTicks = d3.range(1, 5).map((i) => (domainMax * i) / 4);

function toXY(thetaDeg, r) {
  const rad = (thetaDeg * Math.PI) / 180;
  return [cx + r * Math.sin(rad), cy - r * Math.cos(rad)];
}

// --- SVG mount ------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Radial gridlines + tick labels ----------------------------------------
const gridGroup = svg.append("g");
for (const tick of radialTicks) {
  gridGroup
    .append("circle")
    .attr("cx", cx)
    .attr("cy", cy)
    .attr("r", radialScale(tick))
    .attr("fill", "none")
    .attr("stroke", t.grid)
    .attr("stroke-width", 1);

  gridGroup
    .append("text")
    .attr("x", cx + 8)
    .attr("y", cy - radialScale(tick) - 6)
    .attr("fill", t.inkSoft)
    .style("font-size", "14px")
    .text(`${d3.format(".0f")(tick)} m/s`);
}

// Outer domain circle
svg
  .append("circle")
  .attr("cx", cx)
  .attr("cy", cy)
  .attr("r", plotRadius)
  .attr("fill", "none")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1.5);

// --- Angular spokes + compass labels -----------------------------------
const COMPASS = [
  { deg: 0, label: "N" },
  { deg: 45, label: "NE" },
  { deg: 90, label: "E" },
  { deg: 135, label: "SE" },
  { deg: 180, label: "S" },
  { deg: 225, label: "SW" },
  { deg: 270, label: "W" },
  { deg: 315, label: "NW" },
];

const spokeGroup = svg.append("g");
for (const { deg, label } of COMPASS) {
  const [x2, y2] = toXY(deg, plotRadius);
  spokeGroup
    .append("line")
    .attr("x1", cx)
    .attr("y1", cy)
    .attr("x2", x2)
    .attr("y2", y2)
    .attr("stroke", t.grid)
    .attr("stroke-width", 1);

  const [lx, ly] = toXY(deg, plotRadius + 34);
  spokeGroup
    .append("text")
    .attr("x", lx)
    .attr("y", ly)
    .attr("text-anchor", "middle")
    .attr("dominant-baseline", "middle")
    .attr("fill", t.ink)
    .style("font-size", "16px")
    .style("font-weight", "600")
    .text(label);
}

// --- Data points -------------------------------------------------------
svg
  .selectAll("circle.observation")
  .data(data)
  .join("circle")
  .attr("class", "observation")
  .attr("cx", (d) => toXY(d.theta, radialScale(d.speed))[0])
  .attr("cy", (d) => toXY(d.theta, radialScale(d.speed))[1])
  .attr("r", 8)
  .attr("fill", (d) => color(d.category))
  .attr("fill-opacity", 0.75)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1);

// --- Title + subtitle ----------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("polar-scatter · javascript · d3 · anyplot.ai");

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 84)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text("Wind observations — radius = speed (m/s), angle = compass bearing");

// --- Legend ----------------------------------------------------------------
const legendGroup = svg.append("g");
const swatch = 16;
const legendGap = 26;
const legendWidths = categories.map((c) => c.length * 9 + swatch + legendGap);
const legendTotalWidth = legendWidths.reduce((a, b) => a + b, 0);
let legendX = width / 2 - legendTotalWidth / 2;
const legendY = height - 48;

categories.forEach((cat, i) => {
  legendGroup
    .append("rect")
    .attr("x", legendX)
    .attr("y", legendY - swatch / 2)
    .attr("width", swatch)
    .attr("height", swatch)
    .attr("fill", color(cat));

  legendGroup
    .append("text")
    .attr("x", legendX + swatch + 8)
    .attr("y", legendY + swatch / 2 - 2)
    .attr("fill", t.inkSoft)
    .style("font-size", "15px")
    .text(cat.charAt(0).toUpperCase() + cat.slice(1));

  legendX += legendWidths[i];
});
