// anyplot.ai
// histogram-cumulative: Cumulative Histogram
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const theme = window.ANYPLOT_THEME;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 100, right: 70, bottom: 100, left: 120 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// The "muted / other / rest" semantic anchor from the style guide isn't part
// of window.ANYPLOT_TOKENS for JS, so it's reproduced here directly.
const muted = theme === "dark" ? "#A8A79F" : "#6B6A63";
const mutedOpacity = theme === "dark" ? 0.6 : 0.45;

// --- Data (in-memory, deterministic) ----------------------------------------
// Deterministic LCG so the sample is reproducible without a seeded Math.random.
const lcg = (seed) => {
  let s = seed % 2147483647;
  return () => (s = (s * 48271) % 2147483647) / 2147483647;
};
const rand = lcg(42);

// Call-center wait times (seconds) — right-skewed, as most calls answer quickly
// and a long tail waits far longer. Exponential draws model that shape well.
const MEAN_WAIT = 32;
const waitTimes = Array.from({ length: 650 }, () => -MEAN_WAIT * Math.log(1 - rand()));

// Cap the visible domain at the 99th percentile rather than the raw sample
// max: a single slow outlier call would otherwise stretch the x-axis with a
// long, information-free flat tail. Values beyond the cap are clamped into
// the final bin so the cumulative curve still reaches exactly 100%.
const sortedWait = waitTimes.slice().sort(d3.ascending);
const p99Wait = d3.quantile(sortedWait, 0.99);
const maxWait = Math.ceil(p99Wait / 10) * 10;
const clampedWaitTimes = waitTimes.map((w) => Math.min(w, maxWait));
const binCount = 20;
const bins = d3.bin().domain([0, maxWait]).thresholds(binCount)(clampedWaitTimes);

let running = 0;
const total = waitTimes.length;
const steps = [{ x: bins[0].x0, y: 0 }];
for (const bin of bins) {
  running += bin.length;
  steps.push({ x: bin.x1, y: (running / total) * 100 });
}
const maxBinCount = d3.max(bins, (b) => b.length);

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales --------------------------------------------------------------
const x = d3.scaleLinear().domain([0, maxWait]).range([0, iw]);
const y = d3.scaleLinear().domain([0, 100]).range([ih, 0]);
const barHeight = d3.scaleLinear().domain([0, maxBinCount]).range([0, ih * 0.4]);

// --- Gridlines (y-axis only, subtle) -----------------------------------------
g.append("g")
  .selectAll("line")
  .data(y.ticks(5))
  .join("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", (d) => y(d))
  .attr("y2", (d) => y(d))
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- Underlying histogram (secondary encoding, muted) ------------------------
g.selectAll("rect.freq")
  .data(bins)
  .join("rect")
  .attr("class", "freq")
  .attr("x", (d) => x(d.x0) + 1)
  .attr("width", (d) => Math.max(0, x(d.x1) - x(d.x0) - 2))
  .attr("y", (d) => ih - barHeight(d.length))
  .attr("height", (d) => barHeight(d.length))
  .attr("fill", muted)
  .attr("opacity", mutedOpacity);

// --- Cumulative step curve (primary series) -----------------------------------
const areaGen = d3
  .area()
  .x((d) => x(d.x))
  .y0(ih)
  .y1((d) => y(d.y))
  .curve(d3.curveStepAfter);

const lineGen = d3
  .line()
  .x((d) => x(d.x))
  .y((d) => y(d.y))
  .curve(d3.curveStepAfter);

g.append("path").datum(steps).attr("d", areaGen).attr("fill", t.palette[0]).attr("opacity", 0.16);
g.append("path")
  .datum(steps)
  .attr("d", lineGen)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 3.5)
  .attr("stroke-linejoin", "round");

// --- Axes ----------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(8).tickFormat((d) => `${d}s`));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(5).tickFormat((d) => `${d}%`));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}
g.selectAll(".tick line").attr("stroke", t.inkSoft);

// --- Axis labels -----------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 64)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Call Wait Time (seconds)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -88)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Cumulative Share of Calls");

// --- Legend ------------------------------------------------------------------
const legend = svg.append("g").attr("transform", `translate(${width - margin.right - 260}, ${margin.top - 56})`);
const legendItems = [
  { label: "Cumulative %", color: t.palette[0], opacity: 1 },
  { label: "Calls per bin", color: muted, opacity: mutedOpacity },
];
legendItems.forEach((item, i) => {
  const row = legend.append("g").attr("transform", `translate(${i * 150}, 0)`);
  row.append("rect").attr("width", 16).attr("height", 16).attr("fill", item.color).attr("opacity", item.opacity);
  row
    .append("text")
    .attr("x", 24)
    .attr("y", 13)
    .attr("fill", t.inkSoft)
    .style("font-size", "14px")
    .text(item.label);
});

// --- Title -------------------------------------------------------------------
const TITLE = "Call Center Wait Times · histogram-cumulative · javascript · d3 · anyplot.ai";
const titleFontSize = Math.max(15, Math.round(22 * Math.min(1, 67 / TITLE.length)));
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(TITLE);
