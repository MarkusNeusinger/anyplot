// anyplot.ai
// shap-waterfall: SHAP Waterfall Plot for Feature Attribution
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 94/100 | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Data — SHAP contributions for a single loan-default-risk prediction,
// ordered by absolute magnitude (largest contribution first / at top).
const baseValue = 0.32;
const contributions = [
  { feature: "Credit score (620)", shapValue: -0.18 },
  { feature: "Debt-to-income ratio (48%)", shapValue: 0.14 },
  { feature: "Recent credit inquiries (5)", shapValue: 0.09 },
  { feature: "Employment length (1.5 yrs)", shapValue: 0.07 },
  { feature: "Credit history length (3 yrs)", shapValue: 0.05 },
  { feature: "Late payments, 12mo (2)", shapValue: 0.04 },
  { feature: "Annual income ($42k)", shapValue: -0.03 },
  { feature: "Loan amount ($15k)", shapValue: 0.02 },
  { feature: "Age (29)", shapValue: -0.015 },
  { feature: "Existing debt ($8k)", shapValue: 0.01 },
];

let cursor = baseValue;
const rows = contributions.map((d) => {
  const start = cursor;
  const end = cursor + d.shapValue;
  cursor = end;
  return { ...d, start, end };
});
const finalValue = cursor;

// Plot
const margin = { top: 185, right: 90, bottom: 100, left: 320 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

const allValues = [baseValue, finalValue, ...rows.flatMap((r) => [r.start, r.end])];
const domainMin = d3.min(allValues);
const domainMax = d3.max(allValues);
const domainPad = (domainMax - domainMin) * 0.18;
const x = d3.scaleLinear()
  .domain([domainMin - domainPad, domainMax + domainPad])
  .nice()
  .range([0, iw]);

const y = d3.scaleBand()
  .domain(rows.map((d) => d.feature))
  .range([0, ih])
  .padding(0.38);

const POSITIVE = t.palette[4]; // matte red — increases predicted risk
const NEGATIVE = t.palette[2]; // blue — decreases predicted risk

// Style — vertical gridlines aligned to the x-axis ticks
g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(6).tickSize(-ih).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// Connector lines linking each bar's end to the next bar's start
for (let i = 0; i < rows.length - 1; i++) {
  g.append("line")
    .attr("x1", x(rows[i].end))
    .attr("x2", x(rows[i].end))
    .attr("y1", y(rows[i].feature) + y.bandwidth())
    .attr("y2", y(rows[i + 1].feature))
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1.5)
    .attr("stroke-dasharray", "4,4");
}

// Base-value and final-prediction reference lines
g.append("line")
  .attr("x1", x(baseValue)).attr("x2", x(baseValue))
  .attr("y1", 0).attr("y2", ih)
  .attr("stroke", t.inkSoft).attr("stroke-width", 2).attr("stroke-dasharray", "6,5");

g.append("line")
  .attr("x1", x(finalValue)).attr("x2", x(finalValue))
  .attr("y1", 0).attr("y2", ih)
  .attr("stroke", t.ink).attr("stroke-width", 2.5);

svg.append("text")
  .attr("x", margin.left + x(baseValue)).attr("y", 145)
  .attr("text-anchor", "middle").attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text(`Base value  E[f(x)] = ${baseValue.toFixed(3)}`);

svg.append("text")
  .attr("x", margin.left + x(finalValue)).attr("y", 168)
  .attr("text-anchor", "middle").attr("fill", t.ink).style("font-weight", "600")
  .style("font-size", "15px")
  .text(`Predicted risk  f(x) = ${finalValue.toFixed(3)}`);

// Waterfall bars
g.selectAll("rect.bar").data(rows).join("rect").attr("class", "bar")
  .attr("x", (d) => x(Math.min(d.start, d.end)))
  .attr("y", (d) => y(d.feature))
  .attr("width", (d) => Math.abs(x(d.end) - x(d.start)))
  .attr("height", y.bandwidth())
  .attr("fill", (d) => (d.shapValue >= 0 ? POSITIVE : NEGATIVE));

// Numeric SHAP value beside each bar segment
g.selectAll("text.value").data(rows).join("text").attr("class", "value")
  .attr("x", (d) => x(d.end) + (d.shapValue >= 0 ? 10 : -10))
  .attr("y", (d) => y(d.feature) + y.bandwidth() / 2)
  .attr("dy", "0.35em")
  .attr("text-anchor", (d) => (d.shapValue >= 0 ? "start" : "end"))
  .attr("fill", t.ink)
  .style("font-size", "14px")
  .text((d) => `${d.shapValue >= 0 ? "+" : ""}${d.shapValue.toFixed(3)}`);

// Axes
const xAxis = g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(6).tickFormat(d3.format(".2f")));
xAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
xAxis.selectAll("line").attr("stroke", t.inkSoft);
xAxis.select(".domain").attr("stroke", t.inkSoft);

const yAxis = g.append("g").call(d3.axisLeft(y).tickSize(0));
yAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "15px");
yAxis.select(".domain").remove();

svg.append("text")
  .attr("x", margin.left + iw / 2).attr("y", height - 34)
  .attr("text-anchor", "middle").attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Predicted probability of loan default");

// Legend
const legendItems = [
  { label: "Increases risk", color: POSITIVE },
  { label: "Decreases risk", color: NEGATIVE },
];
const legend = svg.append("g")
  .attr("transform", `translate(${width - margin.right - 260},${100})`);
legendItems.forEach((item, i) => {
  const row = legend.append("g").attr("transform", `translate(${i * 150},0)`);
  row.append("rect").attr("width", 20).attr("height", 20).attr("rx", 3).attr("fill", item.color);
  row.append("text").attr("x", 28).attr("y", 15).attr("fill", t.inkSoft)
    .style("font-size", "14px").text(item.label);
});

// Title
svg.append("text")
  .attr("x", width / 2).attr("y", 50)
  .attr("text-anchor", "middle").attr("fill", t.ink)
  .style("font-size", "22px").style("font-weight", "600")
  .text("Loan Default Risk · shap-waterfall · javascript · d3 · anyplot.ai");

svg.append("text")
  .attr("x", width / 2).attr("y", 85)
  .attr("text-anchor", "middle").attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text("Feature attribution for loan application #4821");
