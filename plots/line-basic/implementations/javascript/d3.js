// anyplot.ai
// line-basic: Basic Line Plot
// Library: d3 7.9.0 | JavaScript 22.22.3
// Quality: 89/100 | Created: 2026-06-02
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 80, right: 50, bottom: 70, left: 90 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Data — daily high temperature (°C) for a spring month, deterministic LCG noise
const start = new Date(2026, 2, 1);
let seed = 42;
const rand = () => ((seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);
const data = d3.range(31).map((i) => {
  const day = new Date(start);
  day.setDate(start.getDate() + i);
  const trend = 9 + (i / 30) * 11;
  const wobble = Math.sin(i / 3.2) * 2.6 + (rand() - 0.5) * 2.4;
  return { date: day, temp: +(trend + wobble).toFixed(1) };
});

// SVG mount
const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Scales
const x = d3.scaleTime()
  .domain(d3.extent(data, (d) => d.date))
  .range([0, iw]);
const yMin = d3.min(data, (d) => d.temp);
const yMax = d3.max(data, (d) => d.temp);
const y = d3.scaleLinear()
  .domain([Math.floor(yMin - 2), Math.ceil(yMax + 2)])
  .nice()
  .range([ih, 0]);

// Gridlines (y-axis only, behind the data)
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => {
    sel.select(".domain").remove();
    sel.selectAll("line").attr("stroke", t.grid).attr("stroke-width", 1);
  });

// Axes
const xAxis = g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(
    d3.axisBottom(x)
      .ticks(d3.timeWeek.every(1))
      .tickFormat(d3.timeFormat("%b %d"))
      .tickSizeOuter(0),
  );
const yAxis = g.append("g")
  .call(d3.axisLeft(y).ticks(7).tickFormat((d) => `${d}°`).tickSizeOuter(0));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "18px");
  ax.selectAll(".tick line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft).attr("stroke-width", 1.2);
}

// Axis labels
g.append("text")
  .attr("x", iw / 2).attr("y", ih + 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "22px")
  .text("Date (March 2026)");
g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2).attr("y", -60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "22px")
  .text("Daily high temperature (°C)");

// Line + markers — first categorical series is Imprint palette[0]
const line = d3.line()
  .x((d) => x(d.date))
  .y((d) => y(d.temp))
  .curve(d3.curveMonotoneX);

g.append("path")
  .datum(data)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 3.5)
  .attr("stroke-linecap", "round")
  .attr("stroke-linejoin", "round")
  .attr("d", line);

g.selectAll("circle.point")
  .data(data).join("circle")
  .attr("class", "point")
  .attr("cx", (d) => x(d.date))
  .attr("cy", (d) => y(d.temp))
  .attr("r", 4)
  .attr("fill", t.palette[0])
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

// Title
svg.append("text")
  .attr("x", width / 2).attr("y", 46)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "32px")
  .style("font-weight", "600")
  .text("Spring Warming Trend · line-basic · javascript · d3 · anyplot.ai");
