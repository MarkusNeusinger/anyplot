// anyplot.ai
// line-timeseries: Time Series Line Plot
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 60, bottom: 70, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: daily closing price random walk over one trading year -----------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
}
const random = lcg(42);

const startDate = new Date(2024, 0, 1);
let price = 148;
const data = Array.from({ length: 365 }, (_, i) => {
  const date = new Date(startDate);
  date.setDate(date.getDate() + i);
  price = Math.max(price + (random() - 0.485) * 3.4, 20);
  return { date, close: Math.round(price * 100) / 100 };
});

// --- Scales -------------------------------------------------------------
const x = d3.scaleTime().domain(d3.extent(data, (d) => d.date)).range([0, iw]);
const y = d3.scaleLinear().domain(d3.extent(data, (d) => d.close)).nice().range([ih, 0]);

// --- SVG mount ------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Grid (drawn first, behind the line) ------------------------------------
const gridY = g.append("g").call(d3.axisLeft(y).tickSize(-iw).tickFormat(""));
gridY.selectAll("line").attr("stroke", t.grid);
gridY.select(".domain").remove();

const gridX = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(10).tickSize(-ih).tickFormat(""));
gridX.selectAll("line").attr("stroke", t.grid);
gridX.select(".domain").remove();

// --- Line: intelligent date axis handles the temporal formatting -----------
const line = d3
  .line()
  .x((d) => x(d.date))
  .y((d) => y(d.close))
  .curve(d3.curveMonotoneX);

g.append("path")
  .datum(data)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 3)
  .attr("stroke-linejoin", "round")
  .attr("stroke-linecap", "round")
  .attr("d", line);

// --- Axes -------------------------------------------------------------------
// d3's default time-scale tick format is already "smart": it switches
// resolution (year / month / day / hour) to match the ticks it selects for
// the current domain, so no custom multi-format function is needed here.
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(10));
xAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
xAxis.selectAll("line").attr("stroke", t.inkSoft);
xAxis.select(".domain").attr("stroke", t.inkSoft);

const yAxis = g.append("g").call(d3.axisLeft(y).tickFormat((d) => `$${d}`));
yAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
yAxis.selectAll("line").attr("stroke", t.inkSoft);
yAxis.select(".domain").attr("stroke", t.inkSoft);

// --- Y-axis label -------------------------------------------------------
svg
  .append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -(margin.top + ih / 2))
  .attr("y", 30)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Closing Price (USD)");

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("line-timeseries · javascript · d3 · anyplot.ai");
