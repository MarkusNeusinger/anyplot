// anyplot.ai
// line-loss-training: Training Loss Curve
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 120, right: 70, bottom: 90, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: deterministic training run (fixed-seed LCG, no Math.random) ------
let seed = 42;
const rand = () => {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
};

const epochs = d3.range(1, 61);
const overfitStart = 30;
const history = epochs.map((epoch) => {
  const smooth = 2.7 * Math.exp(-epoch / 17) + 0.06;
  const trainLoss = Math.max(0.02, smooth + (rand() - 0.5) * 0.03);
  const overfitTerm =
    epoch > overfitStart ? 0.0011 * (epoch - overfitStart) ** 2 : 0;
  const valLoss = Math.max(
    0.02,
    smooth + 0.1 + overfitTerm + (rand() - 0.5) * 0.05,
  );
  return { epoch, trainLoss, valLoss };
});

const minValPoint = history.reduce((best, d) =>
  d.valLoss < best.valLoss ? d : best,
);

// --- Scales -------------------------------------------------------------------
const x = d3.scaleLinear().domain(d3.extent(epochs)).range([0, iw]);
const maxLoss = d3.max(history, (d) => Math.max(d.trainLoss, d.valLoss));
const y = d3
  .scaleLinear()
  .domain([0, maxLoss * 1.08])
  .nice()
  .range([ih, 0]);

// --- SVG mount ------------------------------------------------------------------
const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);
const g = svg
  .append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// --- Gridlines (y-axis only) -----------------------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Axes -------------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(10).tickFormat(d3.format("d")));
const yAxis = g
  .append("g")
  .call(d3.axisLeft(y).ticks(6).tickFormat(d3.format(".1f")));
for (const axis of [xAxis, yAxis]) {
  axis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  axis.selectAll("line").attr("stroke", t.inkSoft);
  axis.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels --------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Epoch");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -80)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Cross-Entropy Loss");

// --- Reference marker: epoch of minimum validation loss ------------------------
g.append("line")
  .attr("x1", x(minValPoint.epoch))
  .attr("x2", x(minValPoint.epoch))
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.ink)
  .attr("stroke-width", 1.5)
  .attr("stroke-dasharray", "6,5")
  .attr("opacity", 0.5);

g.append("text")
  .attr("x", x(minValPoint.epoch))
  .attr("y", -16)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text(`min val loss · epoch ${minValPoint.epoch}`);

// --- Loss curves ----------------------------------------------------------------
const line = (accessor) =>
  d3
    .line()
    .x((d) => x(d.epoch))
    .y((d) => y(accessor(d)))
    .curve(d3.curveLinear);

g.append("path")
  .datum(history)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 3.5)
  .attr(
    "d",
    line((d) => d.trainLoss),
  );

g.append("path")
  .datum(history)
  .attr("fill", "none")
  .attr("stroke", t.palette[1])
  .attr("stroke-width", 3.5)
  .attr(
    "d",
    line((d) => d.valLoss),
  );

g.append("circle")
  .attr("cx", x(minValPoint.epoch))
  .attr("cy", y(minValPoint.valLoss))
  .attr("r", 8)
  .attr("fill", t.pageBg)
  .attr("stroke", t.palette[1])
  .attr("stroke-width", 3);

// --- Legend -----------------------------------------------------------------------
const legend = g.append("g").attr("transform", `translate(${iw - 210}, 10)`);
const legendItems = [
  { label: "Training loss", color: t.palette[0] },
  { label: "Validation loss", color: t.palette[1] },
];
legendItems.forEach((item, i) => {
  const row = legend.append("g").attr("transform", `translate(0, ${i * 30})`);
  row
    .append("line")
    .attr("x1", 0)
    .attr("x2", 26)
    .attr("y1", 0)
    .attr("y2", 0)
    .attr("stroke", item.color)
    .attr("stroke-width", 3.5);
  row
    .append("text")
    .attr("x", 36)
    .attr("y", 5)
    .attr("fill", t.inkSoft)
    .style("font-size", "14px")
    .text(item.label);
});

// --- Title ------------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("line-loss-training · javascript · d3 · anyplot.ai");
