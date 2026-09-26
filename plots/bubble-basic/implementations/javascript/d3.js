// anyplot.ai
// bubble-basic: Basic Bubble Chart
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 94/100 | Updated: 2026-09-26

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 100, right: 60, bottom: 90, left: 100 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Startup funding rounds: funding raised vs. revenue growth rate, bubble size
// encodes team size — funding drives hiring, while growth slows as rounds grow.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = lcg(42);

const n = 120;
const data = [];
for (let i = 0; i < n; i++) {
  const funding = 2 + rand() * 148;
  const growth = 55 - funding * 0.25 + (rand() - 0.5) * 45;
  const team = 10 + funding * 0.55 + (rand() - 0.5) * 20;
  data.push({
    funding: Math.round(funding * 10) / 10,
    growth: Math.round(growth * 10) / 10,
    team: Math.round(Math.min(100, Math.max(10, team))),
  });
}

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales ---------------------------------------------------------------
const x = d3.scaleLinear().domain([0, d3.max(data, (d) => d.funding)]).nice().range([0, iw]);
const y = d3.scaleLinear().domain(d3.extent(data, (d) => d.growth)).nice().range([ih, 0]);
const teamExtent = d3.extent(data, (d) => d.team);
const r = d3.scaleSqrt().domain(teamExtent).range([8, 28]);

// --- Gridlines --------------------------------------------------------------
const gridX = g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).tickSize(-ih).tickFormat(""));
const gridY = g.append("g").call(d3.axisLeft(y).tickSize(-iw).tickFormat(""));
for (const grid of [gridX, gridY]) {
  grid.select(".domain").remove();
  grid.selectAll("line").attr("stroke", t.grid).attr("stroke-opacity", 0.5);
}

// --- Axes ---------------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x));
const yAxis = g.append("g").call(d3.axisLeft(y));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels --------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Funding Raised ($M)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -70)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Revenue Growth Rate (%)");

// --- Force-directed decluttering (d3-specific) -------------------------------
// A collision force gently nudges overlapping bubbles apart from their true
// (funding, growth) position so the densest funding cluster (100-150) stays
// individually legible instead of stacking 3-4 deep. The x/y forces pull each
// node back toward its real data coordinate; the anchor strength is loosened
// (0.85 -> 0.7) and the collision padding widened (1.5 -> 4px) so the
// densest cluster gets enough room to actually separate instead of just
// nudging against its neighbors.
data.forEach((d) => {
  d.x = x(d.funding);
  d.y = y(d.growth);
});
const declutter = d3.forceSimulation(data)
  .force("x", d3.forceX((d) => x(d.funding)).strength(0.7))
  .force("y", d3.forceY((d) => y(d.growth)).strength(0.7))
  .force("collide", d3.forceCollide((d) => r(d.team) + 4))
  .stop();
for (let i = 0; i < 220; i++) declutter.tick();

// --- Bubbles --------------------------------------------------------------
g.selectAll("circle.bubble").data(data).join("circle")
  .attr("class", "bubble")
  .attr("cx", (d) => d.x)
  .attr("cy", (d) => d.y)
  .attr("r", (d) => r(d.team))
  .attr("fill", t.palette[0])
  .attr("fill-opacity", 0.48)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

// --- Trend annotation -------------------------------------------------------
// Least-squares fit of growth vs. funding, drawn as a dashed guide so the
// negative correlation is called out explicitly rather than left implicit.
const sumX = d3.sum(data, (d) => d.funding);
const sumY = d3.sum(data, (d) => d.growth);
const sumXY = d3.sum(data, (d) => d.funding * d.growth);
const sumXX = d3.sum(data, (d) => d.funding * d.funding);
const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
const intercept = (sumY - slope * sumX) / n;
const [fundingMin, fundingMax] = d3.extent(data, (d) => d.funding);

g.append("line")
  .attr("x1", x(fundingMin))
  .attr("y1", y(slope * fundingMin + intercept))
  .attr("x2", x(fundingMax))
  .attr("y2", y(slope * fundingMax + intercept))
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 2.5)
  .attr("stroke-dasharray", "8,6")
  .attr("stroke-opacity", 0.75);

const trendLabelX = x(fundingMin) + (x(fundingMax) - x(fundingMin)) * 0.62;
const trendLabelY = y(slope * (fundingMin + (fundingMax - fundingMin) * 0.62) + intercept) - 22;
const trendLabel = g.append("text")
  .attr("x", trendLabelX)
  .attr("y", trendLabelY)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .style("font-weight", "500")
  .text("Growth slows as funding scales up");

// A background card anchors the trend annotation against the busy bubble
// field behind it, with a brand-green accent bar tying the callout to the
// trend line it explains, so the story reads at a glance.
const trendPad = 10;
const trendBBox = trendLabel.node().getBBox();
const cardX = trendBBox.x - trendPad;
const cardY = trendBBox.y - trendPad * 0.6;
const cardW = trendBBox.width + trendPad * 2;
const cardH = trendBBox.height + trendPad * 1.2;
g.insert("rect", () => trendLabel.node())
  .attr("x", cardX)
  .attr("y", cardY)
  .attr("width", cardW)
  .attr("height", cardH)
  .attr("fill", t.elevatedBg)
  .attr("stroke", t.grid)
  .attr("stroke-width", 1.5)
  .attr("rx", 8);
g.insert("rect", () => trendLabel.node())
  .attr("x", cardX)
  .attr("y", cardY)
  .attr("width", 4)
  .attr("height", cardH)
  .attr("fill", t.palette[0])
  .attr("rx", 2);

// --- Size legend ------------------------------------------------------------
const teamMedian = d3.median(data, (d) => d.team);
const legendValues = [
  Math.round(teamExtent[0] / 5) * 5,
  Math.round(teamMedian / 5) * 5,
  Math.round(teamExtent[1] / 5) * 5,
];
const legendR = legendValues.map((v) => r(v));
const legendBoxW = 260;
const legendBoxH = 140;
const legend = svg.append("g")
  .attr("transform", `translate(${margin.left + iw - legendBoxW + 10},${margin.top - 20})`);

legend.append("rect")
  .attr("width", legendBoxW)
  .attr("height", legendBoxH)
  .attr("fill", t.elevatedBg)
  .attr("stroke", t.grid)
  .attr("rx", 8);

legend.append("text")
  .attr("x", legendBoxW / 2)
  .attr("y", 28)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Team Size (employees)");

// Legend circles echo the real bubble treatment (brand-green tint, not a
// generic gray outline) and step up in stroke weight/opacity from small to
// large, giving the reference set a touch of visual hierarchy of its own.
const baselineY = 110;
const legendX = [60, 140, 210];
legendValues.forEach((v, i) => {
  const emphasis = 0.4 + i * 0.3;
  legend.append("circle")
    .attr("cx", legendX[i])
    .attr("cy", baselineY - legendR[i])
    .attr("r", legendR[i])
    .attr("fill", t.palette[0])
    .attr("fill-opacity", 0.12 + i * 0.06)
    .attr("stroke", t.palette[0])
    .attr("stroke-opacity", emphasis)
    .attr("stroke-width", 1 + i * 0.5);
  legend.append("text")
    .attr("x", legendX[i])
    .attr("y", baselineY + 22)
    .attr("text-anchor", "middle")
    .attr("fill", t.inkSoft)
    .style("font-size", "13px")
    .text(v);
});

// --- Title ------------------------------------------------------------------
svg.append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("bubble-basic · javascript · d3 · anyplot.ai");
