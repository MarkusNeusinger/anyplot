// anyplot.ai
// lollipop-grouped: Grouped Lollipop Chart
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 150, right: 90, bottom: 80, left: 210 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Model benchmark: three metrics per algorithm, sorted ascending by mean score
// so scaleBand's range([ih,0]) puts the strongest model at the top.
const metrics = ["Accuracy", "Precision", "Recall"];
const models = [
  { name: "SVM (RBF)", Accuracy: 85.1, Precision: 84.0, Recall: 82.3 },
  { name: "Logistic Regression", Accuracy: 87.9, Precision: 86.4, Recall: 85.1 },
  { name: "Random Forest", Accuracy: 92.3, Precision: 91.5, Recall: 90.2 },
  { name: "Gradient Boosting", Accuracy: 94.7, Precision: 93.9, Recall: 93.1 },
  { name: "Neural Network", Accuracy: 96.2, Precision: 95.4, Recall: 94.8 },
];
const cells = models.flatMap((m) =>
  metrics.map((metric) => ({ model: m.name, metric, value: m[metric] })),
);

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const y0 = d3
  .scaleBand()
  .domain(models.map((m) => m.name))
  .range([ih, 0])
  .paddingInner(0.4)
  .paddingOuter(0.25);
const y1 = d3.scaleBand().domain(metrics).range([0, y0.bandwidth()]).padding(0.25);
const x = d3.scaleLinear().domain([0, 100]).range([0, iw]);
const color = d3.scaleOrdinal().domain(metrics).range(t.palette);

// --- Gridlines ------------------------------------------------------------------
g.selectAll(".grid")
  .data(x.ticks(5))
  .join("line")
  .attr("class", "grid")
  .attr("x1", (d) => x(d))
  .attr("x2", (d) => x(d))
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- Axes -----------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(5).tickFormat((d) => `${d}%`));
const yAxis = g.append("g").call(d3.axisLeft(y0).tickSize(0).tickPadding(14));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "15px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- X-axis label -----------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Score (%)");

// --- Grouped lollipops --------------------------------------------------------
const cellY = (d) => y0(d.model) + y1(d.metric) + y1.bandwidth() / 2;

g.selectAll(".stem")
  .data(cells)
  .join("line")
  .attr("class", "stem")
  .attr("x1", 0)
  .attr("x2", (d) => x(d.value))
  .attr("y1", cellY)
  .attr("y2", cellY)
  .attr("stroke", (d) => color(d.metric))
  .attr("stroke-width", 2.5)
  .attr("stroke-opacity", 0.7);

g.selectAll(".dot")
  .data(cells)
  .join("circle")
  .attr("class", "dot")
  .attr("cx", (d) => x(d.value))
  .attr("cy", cellY)
  .attr("r", 8)
  .attr("fill", (d) => color(d.metric))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2);

g.selectAll(".val")
  .data(cells)
  .join("text")
  .attr("class", "val")
  .attr("x", (d) => x(d.value) + 14)
  .attr("y", cellY)
  .attr("dy", "0.35em")
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .text((d) => d.value.toFixed(1));

// --- Legend ---------------------------------------------------------------------
const legend = svg.append("g").attr("transform", "translate(0, 96)");
let xOffset = 0;
for (const metric of metrics) {
  const item = legend.append("g").attr("transform", `translate(${xOffset},0)`);
  item.append("circle").attr("r", 9).attr("cy", -5).attr("fill", color(metric));
  const label = item
    .append("text")
    .attr("x", 20)
    .attr("y", 0)
    .attr("dominant-baseline", "middle")
    .attr("fill", t.ink)
    .style("font-size", "15px")
    .text(metric);
  xOffset += 20 + label.node().getBBox().width + 40;
}
const legendWidth = xOffset - 40;
legend.attr("transform", `translate(${(width - legendWidth) / 2}, 96)`);

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("lollipop-grouped · javascript · d3 · anyplot.ai");
