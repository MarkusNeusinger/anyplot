// anyplot.ai
// renko-basic: Basic Renko Chart
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 130, right: 70, bottom: 90, left: 130 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: deterministic daily-close random walk (in-memory, LCG PRNG) ------
function lcg(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = lcg(42);

// Four phases (uptrend, consolidation, downtrend, recovery) so the resulting
// bricks trace a clear trend story, matching the spec's "identify trend
// directions" application.
const N_OBSERVATIONS = 220;
const BRICK_SIZE = 3; // $ price move required to draw a new brick
const phases = [
  { end: 60, drift: 0.18 },
  { end: 100, drift: 0.0 },
  { end: 165, drift: -0.16 },
  { end: N_OBSERVATIONS, drift: 0.22 },
];
const closes = [148];
for (let i = 1; i < N_OBSERVATIONS; i++) {
  const drift = phases.find((p) => i < p.end).drift;
  const noise = (rand() - 0.5) * 4.5;
  closes.push(Math.max(60, closes[i - 1] + drift + noise));
}

// --- Renko brick construction ------------------------------------------------
// A new brick is emitted every time the close crosses a full BRICK_SIZE step
// away from the last brick boundary, in either direction — this is what lets
// a run of up bricks reverse into a run of down bricks (trend reversal).
const bricks = [];
let base = Math.round(closes[0] / BRICK_SIZE) * BRICK_SIZE;
for (let i = 1; i < closes.length; i++) {
  let diff = closes[i] - base;
  while (diff >= BRICK_SIZE) {
    const open = base;
    base += BRICK_SIZE;
    diff -= BRICK_SIZE;
    bricks.push({ open, close: base, up: true });
  }
  while (diff <= -BRICK_SIZE) {
    const open = base;
    base -= BRICK_SIZE;
    diff += BRICK_SIZE;
    bricks.push({ open, close: base, up: false });
  }
}

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const x = d3
  .scaleBand()
  .domain(d3.range(bricks.length))
  .range([0, iw])
  .paddingInner(0.22)
  .paddingOuter(0.05);
const levels = bricks.flatMap((b) => [b.open, b.close]);
const y = d3
  .scaleLinear()
  .domain([d3.min(levels) - BRICK_SIZE, d3.max(levels) + BRICK_SIZE])
  .nice()
  .range([ih, 0]);

// --- Gridlines (y-axis only, subtle) -------------------------------------------
g.append("g")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- Bricks ---------------------------------------------------------------
// Bullish (up) -> Imprint brand green; Bearish (down) -> Imprint matte red —
// the semantic finance exception (profit/up -> green, loss/down -> red),
// labeled explicitly in the legend below.
g.selectAll("rect.brick")
  .data(bricks)
  .join("rect")
  .attr("class", "brick")
  .attr("x", (d, i) => x(i))
  .attr("width", x.bandwidth())
  .attr("y", (d) => y(Math.max(d.open, d.close)))
  .attr("height", (d) => Math.abs(y(d.close) - y(d.open)))
  .attr("fill", (d) => (d.up ? t.palette[0] : t.palette[4]))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

// --- Axes -----------------------------------------------------------------
const tickEvery = Math.max(1, Math.ceil(bricks.length / 12));
const xTickValues = d3.range(bricks.length).filter((i) => i % tickEvery === 0);
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).tickValues(xTickValues).tickFormat((i) => i + 1));
const yAxis = g.append("g").call(d3.axisLeft(y).tickFormat(d3.format("$,.0f")));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels ------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 64)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Brick Index");
g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -96)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Price ($)");

// --- Legend (semantic color mapping must be explicit) ------------------------
const legend = svg.append("g").attr("transform", `translate(${margin.left},${margin.top - 56})`);
const legendItems = [
  { label: "Bullish (Up)", color: t.palette[0] },
  { label: "Bearish (Down)", color: t.palette[4] },
];
legendItems.forEach((item, i) => {
  const item_g = legend.append("g").attr("transform", `translate(${i * 190},0)`);
  item_g.append("rect").attr("width", 22).attr("height", 22).attr("fill", item.color);
  item_g
    .append("text")
    .attr("x", 32)
    .attr("y", 17)
    .attr("fill", t.inkSoft)
    .style("font-size", "16px")
    .text(item.label);
});

// --- Title --------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("renko-basic · javascript · d3 · anyplot.ai");
