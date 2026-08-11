// anyplot.ai
// count-basic: Basic Count Plot
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: 95/100 | Created: 2026-08-11

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 170, right: 60, bottom: 120, left: 130 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: raw per-respondent observations, counted (not pre-aggregated) ---
// Small LCG so results are deterministic without a browser RNG.
const lcg = (seed) => {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
};
const random = lcg(42);

const languageWeights = [
  { language: "Python", weight: 28 },
  { language: "JavaScript", weight: 24 },
  { language: "TypeScript", weight: 16 },
  { language: "Java", weight: 12 },
  { language: "Go", weight: 9 },
  { language: "Rust", weight: 7 },
  { language: "C++", weight: 4 },
];
let cumulative = 0;
const cumulativeWeights = languageWeights.map((d) => {
  cumulative += d.weight;
  return { language: d.language, upTo: cumulative };
});
const totalWeight = cumulative;

const RESPONDENTS = 640;
const surveyResponses = Array.from({ length: RESPONDENTS }, () => {
  const r = random() * totalWeight;
  return cumulativeWeights.find((d) => r <= d.upTo).language;
});

const counts = Array.from(
  d3.rollup(
    surveyResponses,
    (v) => v.length,
    (d) => d,
  ),
  ([language, count]) => ({ language, count }),
).sort((a, b) => d3.descending(a.count, b.count));
const meanCount = d3.mean(counts, (d) => d.count);

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales --------------------------------------------------------------------
const x = d3
  .scaleBand()
  .domain(counts.map((d) => d.language))
  .range([0, iw])
  .padding(0.35);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(counts, (d) => d.count)])
  .nice()
  .range([ih, 0]);

// --- Gridlines (y-axis only, subtle) --------------------------------------------
g.append("g")
  .selectAll("line")
  .data(y.ticks(6))
  .join("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", (d) => y(d))
  .attr("y2", (d) => y(d))
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- Axes ------------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).tickSize(0).tickPadding(14));
const yAxis = g
  .append("g")
  .call(d3.axisLeft(y).ticks(6).tickFormat(d3.format(",d")).tickSize(0).tickPadding(12));
for (const axis of [xAxis, yAxis]) {
  axis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  axis.select(".domain").remove();
}
yAxis.selectAll(".tick line").attr("stroke", t.grid);

// --- Bars ---------------------------------------------------------------------
// Opacity fades from the leading language (full strength) down through the
// long tail, giving the top result a visual focal point beyond sort order.
const emphasis = d3
  .scaleLinear()
  .domain([d3.min(counts, (d) => d.count), d3.max(counts, (d) => d.count)])
  .range([0.6, 1]);

g.selectAll("rect")
  .data(counts)
  .join("rect")
  .attr("x", (d) => x(d.language))
  .attr("y", (d) => y(d.count))
  .attr("width", x.bandwidth())
  .attr("height", (d) => ih - y(d.count))
  .attr("fill", t.palette[0])
  .attr("fill-opacity", (d) => emphasis(d.count))
  .attr("stroke", t.ink)
  .attr("stroke-opacity", 0.15)
  .attr("stroke-width", 1);

// --- Mean reference line (secondary encoding beyond sort/opacity) --------------
// A dashed amber rule at the across-category mean lets the eye split the long
// tail into above-/below-average languages at a glance. Drawn before the count
// labels so their page-bg halo (below) can mask the line where they land close
// to it, instead of the line cutting through the digits.
g.append("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", y(meanCount))
  .attr("y2", y(meanCount))
  .attr("stroke", t.amber)
  .attr("stroke-width", 2)
  .attr("stroke-dasharray", "6,5");

g.append("text")
  .attr("x", iw)
  .attr("y", y(meanCount) - 10)
  .attr("text-anchor", "end")
  .attr("fill", t.amber)
  .style("font-size", "14px")
  .style("font-weight", "600")
  .text(`Mean = ${d3.format(",.0f")(meanCount)}`);

// --- Count labels above bars ---------------------------------------------------
// A page-bg halo (paint-order: stroke) keeps the mean line above from visually
// clashing with labels that land close to it (e.g. Java at 87 vs. mean 91).
g.selectAll(".count-label")
  .data(counts)
  .join("text")
  .attr("class", "count-label")
  .attr("x", (d) => x(d.language) + x.bandwidth() / 2)
  .attr("y", (d) => y(d.count) - 14)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 6)
  .attr("stroke-linejoin", "round")
  .style("paint-order", "stroke")
  .style("font-size", "16px")
  .style("font-weight", "600")
  .text((d) => d.count);

// --- Leading-category annotation (d3-shape symbol generator) -------------------
// A small amber diamond over the top bar calls out the mode without adding a
// second data color, exercising d3.symbol alongside the rollup/scale/axis idiom.
const leader = counts[0];
const leaderX = x(leader.language) + x.bandwidth() / 2;
const leaderY = y(leader.count) - 40;
g.append("path")
  .attr("d", d3.symbol().type(d3.symbolDiamond).size(140)())
  .attr("transform", `translate(${leaderX},${leaderY})`)
  .attr("fill", t.amber);
g.append("text")
  .attr("x", leaderX)
  .attr("y", leaderY - 14)
  .attr("text-anchor", "middle")
  .attr("fill", t.amber)
  .style("font-size", "14px")
  .style("font-weight", "600")
  .text("Most common");

// --- Axis titles -----------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 76)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Primary Programming Language");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -92)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Number of Respondents");

// --- Title -------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 54)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("count-basic · javascript · d3 · anyplot.ai");

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 88)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "17px")
  .text(`Developer survey · n = ${RESPONDENTS} respondents · sorted by frequency`);
