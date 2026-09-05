// anyplot.ai
// line-filled: Filled Line Plot
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 70, bottom: 90, left: 120 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic LCG) ------------------------------------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const random = lcg(42);

const startDate = new Date(2026, 5, 1);
const dayCount = 60;
const dailyVisitors = [];
for (let i = 0; i < dayCount; i++) {
  const trend = 820 + i * 7.5;
  const weeklyCycle = 140 * Math.sin((i / 7) * 2 * Math.PI);
  const noise = (random() - 0.5) * 160;
  const date = new Date(startDate);
  date.setDate(date.getDate() + i);
  dailyVisitors.push({ date, visitors: Math.max(0, trend + weeklyCycle + noise) });
}

// --- Scales -------------------------------------------------------------------
const x = d3.scaleTime()
  .domain(d3.extent(dailyVisitors, (d) => d.date))
  .range([0, iw]);
const y = d3.scaleLinear()
  .domain([0, d3.max(dailyVisitors, (d) => d.visitors) * 1.1])
  .nice()
  .range([ih, 0]);

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Gridlines (y-axis only, subtle) -------------------------------------------
const grid = g.append("g").call(d3.axisLeft(y).tickSize(-iw).tickFormat(""));
grid.selectAll("line").attr("stroke", t.grid);
grid.select(".domain").remove();

// --- Area gradient (opaque near the line, fading to the baseline) --------------
const gradientId = "line-filled-area-gradient";
const gradient = svg.append("defs")
  .append("linearGradient")
  .attr("id", gradientId)
  .attr("gradientUnits", "userSpaceOnUse")
  .attr("x1", 0).attr("y1", 0)
  .attr("x2", 0).attr("y2", ih);
gradient.append("stop").attr("offset", "0%").attr("stop-color", t.palette[0]).attr("stop-opacity", 0.45);
gradient.append("stop").attr("offset", "100%").attr("stop-color", t.palette[0]).attr("stop-opacity", 0.04);

// --- Area + line ----------------------------------------------------------------
const area = d3.area()
  .curve(d3.curveMonotoneX)
  .x((d) => x(d.date))
  .y0(ih)
  .y1((d) => y(d.visitors));
const line = d3.line()
  .curve(d3.curveMonotoneX)
  .x((d) => x(d.date))
  .y((d) => y(d.visitors));

g.append("path")
  .datum(dailyVisitors)
  .attr("d", area)
  .attr("fill", `url(#${gradientId})`)
  .attr("stroke", "none");

g.append("path")
  .datum(dailyVisitors)
  .attr("d", line)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 3.5);

// --- End-point focal marker (emphasizes the overall upward trend) --------------
const last = dailyVisitors[dailyVisitors.length - 1];
const first = dailyVisitors[0];
const growthPct = Math.round(((last.visitors - first.visitors) / first.visitors) * 100);
g.append("circle")
  .attr("cx", x(last.date))
  .attr("cy", y(last.visitors))
  .attr("r", 6)
  .attr("fill", t.palette[0])
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2);

g.append("text")
  .attr("x", x(last.date))
  .attr("y", y(last.visitors) - 16)
  .attr("text-anchor", "end")
  .attr("fill", t.ink)
  .style("font-size", "15px")
  .style("font-weight", "600")
  .text(`+${growthPct}% vs. day 1`);

// --- Axes -----------------------------------------------------------------------
const xAxis = g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(d3.timeWeek.every(1)).tickFormat(d3.timeFormat("%b %d")));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.grid);
  ax.select(".domain").attr("stroke", t.inkSoft);
}
xAxis.selectAll("text").attr("dy", "1.2em");

// --- Axis labels ------------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 70)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Date");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -85)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Daily Visitors (count)");

// --- Title ----------------------------------------------------------------------
svg.append("text")
  .attr("x", width / 2)
  .attr("y", 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("line-filled · javascript · d3 · anyplot.ai");
