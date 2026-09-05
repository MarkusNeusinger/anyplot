// anyplot.ai
// errorbar-asymmetric: Asymmetric Error Bars Plot
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 150, right: 60, bottom: 70, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: ozone readings per station, 10th-90th percentile bounds ---------
// Right-skewed spread (pollution spikes push the upper tail out further
// than the lower tail) — a canonical case for asymmetric error bars.
const stations = [
  { station: "Riverside", median: 28, lower: 6, upper: 13 },
  { station: "Uptown", median: 42, lower: 8, upper: 18 },
  { station: "Harbor", median: 35, lower: 7, upper: 15 },
  { station: "Industrial", median: 51, lower: 10, upper: 22 },
  { station: "Greenfield", median: 22, lower: 4, upper: 9 },
  { station: "Lakeside", median: 31, lower: 6, upper: 12 },
  { station: "Downtown", median: 47, lower: 9, upper: 20 },
  { station: "Hilltop", median: 26, lower: 5, upper: 10 },
];

// --- SVG mount ---------------------------------------------------------------
const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);
const g = svg
  .append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales --------------------------------------------------------------------
const x = d3
  .scaleBand()
  .domain(stations.map((d) => d.station))
  .range([0, iw])
  .padding(0.4);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(stations, (d) => d.median + d.upper)])
  .nice()
  .range([ih, 0]);

// --- Gridlines (y-axis only) ---------------------------------------------------
g.append("g")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Axes ------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).tickSize(0));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "15px");
  ax.select(".domain").attr("stroke", t.inkSoft);
}
xAxis.select(".domain").attr("stroke", t.inkSoft);
g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -80)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Ozone Concentration (ppb)");

// --- Asymmetric error bars ------------------------------------------------
const capWidth = x.bandwidth() * 0.5;
const bar = g
  .selectAll(".errorbar")
  .data(stations)
  .join("g")
  .attr("class", "errorbar")
  .attr("transform", (d) => `translate(${x(d.station) + x.bandwidth() / 2},0)`);

bar
  .append("line")
  .attr("y1", (d) => y(d.median - d.lower))
  .attr("y2", (d) => y(d.median + d.upper))
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 3);

bar
  .append("line")
  .attr("x1", -capWidth / 2)
  .attr("x2", capWidth / 2)
  .attr("y1", (d) => y(d.median - d.lower))
  .attr("y2", (d) => y(d.median - d.lower))
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 3);

bar
  .append("line")
  .attr("x1", -capWidth / 2)
  .attr("x2", capWidth / 2)
  .attr("y1", (d) => y(d.median + d.upper))
  .attr("y2", (d) => y(d.median + d.upper))
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 3);

bar
  .append("circle")
  .attr("cy", (d) => y(d.median))
  .attr("r", 9)
  .attr("fill", t.palette[0])
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

// --- Title + subtitle --------------------------------------------------------
const title =
  "Ozone Levels by Monitoring Station · errorbar-asymmetric · javascript · d3 · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / title.length));
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 55)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(title);

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 92)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text(
    "Points show the median reading; bars span the 10th–90th percentile range",
  );
