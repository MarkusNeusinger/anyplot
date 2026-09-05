// anyplot.ai
// line-confidence: Line Plot with Confidence Interval
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 94/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 60, bottom: 90, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: monthly demand forecast with a 90% prediction interval ----------
// Small fixed-seed LCG so the "noise" around the forecast is reproducible.
let seed = 42;
function lcg() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const months = 24;
const data = [];
for (let i = 0; i < months; i += 1) {
  const trend = 480 + 9.5 * i;
  const seasonal = 40 * Math.sin((2 * Math.PI * i) / 12);
  const forecast = trend + seasonal;
  const spread = 25 + 2.2 * i + 30 * (lcg() - 0.5);
  data.push({
    month: i,
    forecast,
    lower: forecast - Math.abs(spread),
    upper: forecast + Math.abs(spread),
  });
}

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const x = d3
  .scaleLinear()
  .domain([0, months - 1])
  .range([0, iw]);
const y = d3
  .scaleLinear()
  .domain([d3.min(data, (d) => d.lower) - 20, d3.max(data, (d) => d.upper) + 20])
  .nice()
  .range([ih, 0]);

// --- Gridlines (y-axis only) --------------------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).ticks(6).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Confidence band -----------------------------------------------------------
// Gradient fill (subtle → stronger opacity left-to-right) makes the growing
// forecast uncertainty a first-class visual cue, not just an implicit shape.
const bandGradient = svg
  .append("defs")
  .append("linearGradient")
  .attr("id", "band-gradient")
  .attr("gradientUnits", "userSpaceOnUse")
  .attr("x1", x(0))
  .attr("x2", x(months - 1))
  .attr("y1", 0)
  .attr("y2", 0);
bandGradient.append("stop").attr("offset", "0%").attr("stop-color", t.palette[0]).attr("stop-opacity", 0.12);
bandGradient.append("stop").attr("offset", "100%").attr("stop-color", t.palette[0]).attr("stop-opacity", 0.38);

const band = d3
  .area()
  .x((d) => x(d.month))
  .y0((d) => y(d.lower))
  .y1((d) => y(d.upper))
  .curve(d3.curveMonotoneX);

g.append("path").datum(data).attr("d", band).attr("fill", "url(#band-gradient)").attr("stroke", "none");

// --- Central forecast line -----------------------------------------------------
const line = d3
  .line()
  .x((d) => x(d.month))
  .y((d) => y(d.forecast))
  .curve(d3.curveMonotoneX);

g.append("path")
  .datum(data)
  .attr("d", line)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 4)
  .attr("stroke-linejoin", "round")
  .attr("stroke-linecap", "round");

// --- Axes ------------------------------------------------------------------
const monthLabels = ["Jan", "Apr", "Jul", "Oct"];
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(
    d3
      .axisBottom(x)
      .tickValues(d3.range(0, months, 3))
      .tickFormat((d) => `${monthLabels[(d / 3) % 4]} ${d < 12 ? "'25" : "'26"}`),
  );
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6).tickFormat((d) => d3.format(",")(d)));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels -----------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 66)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Month");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -80)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Units Sold (forecast)");

// --- Annotation: call out the widening uncertainty ----------------------------
const annotationPoint = data[months - 5];
const annoX = x(annotationPoint.month);
const annoTopY = y(annotationPoint.upper);
const labelY = annoTopY - 46;

g.append("line")
  .attr("x1", annoX)
  .attr("y1", labelY + 14)
  .attr("x2", annoX)
  .attr("y2", annoTopY - 6)
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1.5)
  .attr("stroke-dasharray", "3,3");

g.append("text")
  .attr("x", annoX)
  .attr("y", labelY)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .style("font-style", "italic")
  .text("Interval widens as the forecast horizon grows");

// --- Legend ------------------------------------------------------------------
const legend = svg.append("g").attr("transform", `translate(${margin.left + 10},${margin.top - 22})`);

legend.append("line").attr("x1", 0).attr("x2", 36).attr("y1", 0).attr("y2", 0).attr("stroke", t.palette[0]).attr("stroke-width", 4);
legend
  .append("text")
  .attr("x", 46)
  .attr("y", 5)
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text("Forecast");

legend
  .append("rect")
  .attr("x", 180)
  .attr("y", -9)
  .attr("width", 36)
  .attr("height", 18)
  .attr("fill", t.palette[0])
  .attr("fill-opacity", 0.25)
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 1);
legend
  .append("text")
  .attr("x", 226)
  .attr("y", 5)
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text("90% Prediction Interval");

// --- Title -------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 54)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "40px")
  .style("font-weight", "600")
  .text("line-confidence · javascript · d3 · anyplot.ai");
