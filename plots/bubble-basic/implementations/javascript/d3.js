// anyplot.ai
// bubble-basic: Basic Bubble Chart
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-08-24

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
const r = d3.scaleSqrt().domain(teamExtent).range([8, 34]);

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

// --- Bubbles --------------------------------------------------------------
g.selectAll("circle.bubble").data(data).join("circle")
  .attr("class", "bubble")
  .attr("cx", (d) => x(d.funding))
  .attr("cy", (d) => y(d.growth))
  .attr("r", (d) => r(d.team))
  .attr("fill", t.palette[0])
  .attr("fill-opacity", 0.48)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1);

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
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 2)
  .attr("stroke-dasharray", "8,6")
  .attr("stroke-opacity", 0.6);

const trendLabelX = x(fundingMin) + (x(fundingMax) - x(fundingMin)) * 0.62;
const trendLabelY = y(slope * (fundingMin + (fundingMax - fundingMin) * 0.62) + intercept) - 16;
g.append("text")
  .attr("x", trendLabelX)
  .attr("y", trendLabelY)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .style("font-style", "italic")
  .text("Growth slows as funding scales up");

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

const baselineY = 110;
const legendX = [60, 140, 210];
legendValues.forEach((v, i) => {
  legend.append("circle")
    .attr("cx", legendX[i])
    .attr("cy", baselineY - legendR[i])
    .attr("r", legendR[i])
    .attr("fill", "none")
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1.5);
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
