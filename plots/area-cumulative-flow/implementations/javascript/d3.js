// anyplot.ai
// area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-08-18

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 100, right: 260, bottom: 90, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Support-ticket lifecycle over a 90-day window. Each stage's value is the
// CUMULATIVE count of tickets that have entered or passed through that stage
// by the given day — earliest stage (Opened) is always >= every later stage.
let seed = 20260818;
function lcg() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const stages = ["Opened", "Triaged", "In Progress", "Waiting on Customer", "Resolved"];
const advanceRate = [0.42, 0.38, 0.3, 0.24]; // fraction of the gap to the prior stage that advances per day
const days = 90;
const startDate = new Date(2026, 4, 1);

const dates = Array.from({ length: days }, (_, i) => {
  const d = new Date(startDate);
  d.setDate(d.getDate() + i);
  return d;
});

// Daily new-ticket arrivals: a base rate with a weekly dip (weekends) plus noise.
const cumulative = stages.map(() => new Array(days).fill(0));
for (let i = 0; i < days; i += 1) {
  const dow = dates[i].getDay();
  const weekendDamp = dow === 0 || dow === 6 ? 0.4 : 1;
  const arrivals = Math.round((7 + 4 * Math.sin(i / 9)) * weekendDamp + lcg() * 4);
  cumulative[0][i] = (i === 0 ? 0 : cumulative[0][i - 1]) + Math.max(0, arrivals);

  for (let s = 1; s < stages.length; s += 1) {
    const prevDayOwn = i === 0 ? 0 : cumulative[s][i - 1];
    const gap = cumulative[s - 1][i] - prevDayOwn;
    const advance = Math.floor(gap * advanceRate[s - 1] + lcg() * 1.5);
    cumulative[s][i] = prevDayOwn + Math.max(0, Math.min(gap, advance));
  }
}

// Band boundaries bottom-to-top: 0, Resolved, Waiting, In Progress, Triaged, Opened.
// Earliest stage (Opened) renders as the topmost band, latest (Resolved) at the bottom.
const boundaries = [
  new Array(days).fill(0),
  cumulative[4],
  cumulative[3],
  cumulative[2],
  cumulative[1],
  cumulative[0],
];

const bands = stages.map((stage, i) => ({
  stage,
  color: t.palette[i],
  points: dates.map((date, di) => ({
    date,
    y0: boundaries[stages.length - i - 1][di],
    y1: boundaries[stages.length - i][di],
  })),
}));

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales --------------------------------------------------------------------
const x = d3.scaleTime().domain(d3.extent(dates)).range([0, iw]);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(cumulative[0])])
  .nice()
  .range([ih, 0]);

// --- Gridlines -----------------------------------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Bands ---------------------------------------------------------------------
const area = d3
  .area()
  .x((d) => x(d.date))
  .y0((d) => y(d.y0))
  .y1((d) => y(d.y1));

g.selectAll("path.band")
  .data(bands)
  .join("path")
  .attr("class", "band")
  .attr("fill", (d) => d.color)
  .attr("d", (d) => area(d.points));

// --- Axes ------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(d3.timeWeek.every(2)).tickFormat(d3.timeFormat("%b %d")));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.grid);
  ax.select(".domain").attr("stroke", t.inkSoft);
}
xAxis.selectAll("text").attr("dy", "1.4em");

// --- Axis labels -------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 68)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text("Date");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -80)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text("Cumulative Ticket Count");

// --- Legend (workflow order, top stage first) ---------------------------------
const legend = svg
  .append("g")
  .attr("transform", `translate(${margin.left + iw + 40}, ${margin.top + 20})`);

const legendRows = legend
  .selectAll("g")
  .data(stages)
  .join("g")
  .attr("transform", (_, i) => `translate(0, ${i * 34})`);

legendRows
  .append("rect")
  .attr("width", 18)
  .attr("height", 18)
  .attr("rx", 3)
  .attr("fill", (_, i) => t.palette[i]);

legendRows
  .append("text")
  .attr("x", 26)
  .attr("y", 14)
  .attr("fill", t.ink)
  .style("font-size", "15px")
  .text((d) => d);

// --- Title ---------------------------------------------------------------------
const title = "Support Ticket Pipeline · area-cumulative-flow · javascript · d3 · anyplot.ai";
const titleFontSize = Math.max(16, Math.round(22 * Math.min(1, 67 / title.length)));
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(title);
