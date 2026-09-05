// anyplot.ai
// line-timeseries-rolling: Time Series with Rolling Average Overlay
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 82/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 60, bottom: 70, left: 90 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily website engagement score over ~120 days with a 14-day rolling average.
function lcg(seed) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };
}
const rand = lcg(42);

const numDays = 120;
const windowSize = 14;
const startDate = new Date(2025, 3, 1);

const rawSeries = [];
let level = 62;
for (let i = 0; i < numDays; i++) {
  const seasonal = 8 * Math.sin((i / numDays) * Math.PI * 2.4);
  const noise = (rand() - 0.5) * 14;
  level += (rand() - 0.5) * 1.2;
  const value = Math.max(5, level + seasonal + noise);
  const date = new Date(startDate);
  date.setDate(date.getDate() + i);
  rawSeries.push({ date, value });
}

const rollingSeries = [];
for (let i = windowSize - 1; i < rawSeries.length; i++) {
  let sum = 0;
  for (let j = i - windowSize + 1; j <= i; j++) sum += rawSeries[j].value;
  rollingSeries.push({ date: rawSeries[i].date, value: sum / windowSize });
}

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales ---------------------------------------------------------------
const x = d3
  .scaleTime()
  .domain(d3.extent(rawSeries, (d) => d.date))
  .range([0, iw]);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(rawSeries, (d) => d.value) * 1.08])
  .nice()
  .range([ih, 0]);

// --- Gridlines (both axes) ---------------------------------------------------
g.append("g")
  .attr("class", "grid grid-y")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .selectAll("line")
  .attr("stroke", t.grid);
g.select(".grid-y .domain").remove();

g.append("g")
  .attr("class", "grid grid-x")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).tickSize(-ih).tickFormat(""))
  .selectAll("line")
  .attr("stroke", t.grid);
g.select(".grid-x .domain").remove();

// --- Axes -------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(8).tickFormat(d3.timeFormat("%b %d")));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.grid);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Raw data: thin, semi-transparent line -----------------------------------
const rawLine = d3
  .line()
  .x((d) => x(d.date))
  .y((d) => y(d.value))
  .curve(d3.curveMonotoneX);

g.append("path")
  .datum(rawSeries)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 1.5)
  .attr("stroke-opacity", 0.35)
  .attr("d", rawLine);

// --- Rolling average: prominent, smooth, contrasting color -------------------
const rollingLine = d3
  .line()
  .x((d) => x(d.date))
  .y((d) => y(d.value))
  .curve(d3.curveMonotoneX);

// Subtle halo behind the rolling-average line to lift it further above the noisy raw data.
g.append("path")
  .datum(rollingSeries)
  .attr("fill", "none")
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 7)
  .attr("stroke-opacity", 0.6)
  .attr("d", rollingLine);

g.append("path")
  .datum(rollingSeries)
  .attr("fill", "none")
  .attr("stroke", t.palette[1])
  .attr("stroke-width", 4)
  .attr("d", rollingLine);

// --- Legend -------------------------------------------------------------------
const legendData = [
  { label: "Raw Data", color: t.palette[0], opacity: 0.35, width: 3 },
  { label: `Rolling Average (${windowSize}-Day)`, color: t.palette[1], opacity: 1, width: 5 },
];
const legendBoxWidth = 300;
const legendBoxHeight = 66;
const legend = g.append("g").attr("transform", `translate(${iw - legendBoxWidth - 14}, 14)`);
legend
  .append("rect")
  .attr("width", legendBoxWidth)
  .attr("height", legendBoxHeight)
  .attr("rx", 8)
  .attr("fill", t.elevatedBg)
  .attr("stroke", t.grid);
legendData.forEach((d, i) => {
  const row = legend.append("g").attr("transform", `translate(18, ${20 + i * 28})`);
  row
    .append("line")
    .attr("x1", 0)
    .attr("x2", 32)
    .attr("y1", 0)
    .attr("y2", 0)
    .attr("stroke", d.color)
    .attr("stroke-opacity", d.opacity)
    .attr("stroke-width", d.width);
  row
    .append("text")
    .attr("x", 42)
    .attr("y", 5)
    .attr("fill", t.inkSoft)
    .style("font-size", "15px")
    .text(d.label);
});

// --- Labels -------------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 55)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Date");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -65)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Engagement Score");

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("line-timeseries-rolling · javascript · d3 · anyplot.ai");
