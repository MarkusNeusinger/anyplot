// anyplot.ai
// bar-horizontal: Horizontal Bar Chart
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: 81/100 | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 140, bottom: 90, left: 260 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Most-starred open-source frameworks on GitHub, sorted ascending so the
// largest bar lands at the top when rendered with a reversed band scale.
// Raw star counts (not pre-scaled) — the SI-prefix formatter below derives
// the "k" display units directly from the real magnitude.
const data = [
  { language: "Vue", stars: 46900 },
  { language: "Bootstrap", stars: 59100 },
  { language: "TensorFlow", stars: 68300 },
  { language: "React", stars: 79400 },
  { language: "Flutter", stars: 89900 },
  { language: "VS Code", stars: 98700 },
  { language: "Node.js", stars: 108200 },
  { language: "freeCodeCamp", stars: 118500 },
].sort((a, b) => a.stars - b.stars);

// SI-prefix formatter (d3-format) — auto-derives "k" units from magnitude
// instead of a hardcoded `${d}M` multiplier.
const siFormat = d3.format("~s");
const valueFormat = d3.format(".3~s");

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const x = d3.scaleLinear().domain([0, d3.max(data, (d) => d.stars)]).nice().range([0, iw]);
const y = d3.scaleBand().domain(data.map((d) => d.language)).range([ih, 0]).padding(0.28);

// --- Gridlines (x-axis only, per horizontal-bar convention) -------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisBottom(x).tickSize(ih).tickFormat(""))
  .attr("transform", `translate(0,0)`)
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Axes -----------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(6).tickFormat(siFormat).tickSizeOuter(0));
const yAxis = g.append("g").call(d3.axisLeft(y).tickSizeOuter(0));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}
yAxis.selectAll("line").remove();

// --- Bars -----------------------------------------------------------------
g.selectAll("rect.bar")
  .data(data)
  .join("rect")
  .attr("class", "bar")
  .attr("x", 0)
  .attr("y", (d) => y(d.language))
  .attr("width", (d) => x(d.stars))
  .attr("height", y.bandwidth())
  .attr("rx", 3)
  .attr("ry", 3)
  .attr("fill", t.palette[0]);

// --- Value labels at bar ends ------------------------------------------------
g.selectAll("text.value")
  .data(data)
  .join("text")
  .attr("class", "value")
  .attr("x", (d) => x(d.stars) + 14)
  .attr("y", (d) => y(d.language) + y.bandwidth() / 2)
  .attr("dy", "0.35em")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .style("font-weight", "500")
  .text((d) => `${valueFormat(d.stars)}`);

// --- Axis label ---------------------------------------------------------------
svg
  .append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", height - 26)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "18px")
  .text("GitHub Stars");

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "30px")
  .style("font-weight", "600")
  .text("bar-horizontal · javascript · d3 · anyplot.ai");
