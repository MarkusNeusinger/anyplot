// anyplot.ai
// indicator-sma: Simple Moving Average (SMA) Indicator Chart
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 130, right: 70, bottom: 70, left: 100 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: one year of daily closes (fixed-seed LCG random walk) + SMA overlays
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);
function gaussian() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const PERIODS = 252;
const dates = [];
const cursor = new Date(2024, 0, 2);
while (dates.length < PERIODS) {
  const weekday = cursor.getDay();
  if (weekday !== 0 && weekday !== 6) dates.push(new Date(cursor));
  cursor.setDate(cursor.getDate() + 1);
}

const closes = [];
let price = 148;
for (let i = 0; i < PERIODS; i++) {
  price *= 1 + 0.0006 + 0.014 * gaussian();
  closes.push(price);
}

function movingAverage(values, period) {
  return values.map((_, i) => {
    if (i < period - 1) return null;
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += values[j];
    return sum / period;
  });
}

const series = [
  { key: "close", label: "Close", values: closes, color: t.palette[0], width: 2 },
  { key: "sma20", label: "SMA 20", values: movingAverage(closes, 20), color: t.palette[1], width: 3 },
  { key: "sma50", label: "SMA 50", values: movingAverage(closes, 50), color: t.palette[2], width: 3 },
  { key: "sma200", label: "SMA 200", values: movingAverage(closes, 200), color: t.palette[3], width: 3 },
];

// --- Scales -------------------------------------------------------------
const x = d3.scaleTime().domain(d3.extent(dates)).range([0, iw]);
const allValues = series.flatMap((s) => s.values).filter((v) => v !== null);
const y = d3
  .scaleLinear()
  .domain([d3.min(allValues) * 0.97, d3.max(allValues) * 1.03])
  .nice()
  .range([ih, 0]);

// --- SVG mount ------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Gridlines (y-axis only, per spec) -------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).ticks(6).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Axes -------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(d3.timeMonth.every(1)).tickFormat(d3.timeFormat("%b %Y")));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6).tickFormat(d3.format("$,.0f")));
for (const axis of [xAxis, yAxis]) {
  axis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  axis.selectAll("line").attr("stroke", t.inkSoft);
  axis.select(".domain").attr("stroke", t.inkSoft);
}
xAxis.selectAll("text").attr("transform", "rotate(-30)").style("text-anchor", "end");

g.append("text")
  .attr("x", -margin.left + 24)
  .attr("y", -30)
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Price (USD)");

// --- Lines ------------------------------------------------------------------
const line = d3
  .line()
  .defined((d) => d.value !== null)
  .x((d) => x(d.date))
  .y((d) => y(d.value))
  .curve(d3.curveMonotoneX);

for (const s of series) {
  const points = dates.map((date, i) => ({ date, value: s.values[i] }));
  g.append("path")
    .datum(points)
    .attr("fill", "none")
    .attr("stroke", s.color)
    .attr("stroke-width", s.width)
    .attr("stroke-linejoin", "round")
    .attr("stroke-linecap", "round")
    .attr("opacity", s.key === "close" ? 0.85 : 1)
    .attr("d", line);
}

// --- Title --------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("indicator-sma · javascript · d3 · anyplot.ai");

// --- Legend (horizontal, below title) ---------------------------------------
const legend = svg.append("g").attr("transform", `translate(0, 90)`);
const legendWidth = series.reduce((acc, s) => acc + s.label.length * 11 + 60, 0);
let cursorX = width / 2 - legendWidth / 2;
for (const s of series) {
  const item = legend.append("g").attr("transform", `translate(${cursorX},0)`);
  item
    .append("line")
    .attr("x1", 0)
    .attr("x2", 28)
    .attr("y1", 0)
    .attr("y2", 0)
    .attr("stroke", s.color)
    .attr("stroke-width", s.width)
    .attr("stroke-linecap", "round");
  item
    .append("text")
    .attr("x", 38)
    .attr("y", 5)
    .attr("fill", t.inkSoft)
    .style("font-size", "15px")
    .text(s.label);
  cursorX += s.label.length * 11 + 60;
}
