// anyplot.ai
// line-reaction-coordinate: Reaction Coordinate Energy Diagram
// Library: d3 7.9.0 | JavaScript 22.22.3
// Quality: 91/100 | Created: 2026-06-24

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

const margin = { top: 90, right: 160, bottom: 90, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Data: single-step exothermic reaction
// Reactants: 50 kJ/mol, Transition State: 120 kJ/mol, Products: 20 kJ/mol
const E_r = 50, E_ts = 120, E_p = 20;
const sigma = 0.15;
const A = E_ts - (E_r + (E_p - E_r) * 0.5); // Gaussian amplitude = 85

const N = 300;
const curveData = Array.from({ length: N }, (_, i) => {
  const x = i / (N - 1);
  const energy = E_r + A * Math.exp(-Math.pow(x - 0.5, 2) / (2 * sigma * sigma)) + (E_p - E_r) * x;
  return { x, energy };
});

// --- SVG mount
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales
const xScale = d3.scaleLinear().domain([0, 1]).range([0, iw]);
const yScale = d3.scaleLinear().domain([0, 140]).range([ih, 0]);

// --- Defs: arrowhead markers for double-headed arrows
const defs = svg.append("defs");

defs.append("marker")
  .attr("id", "arrow-end")
  .attr("viewBox", "0 -5 10 10")
  .attr("refX", 8).attr("refY", 0)
  .attr("markerWidth", 5).attr("markerHeight", 5)
  .attr("orient", "auto")
  .append("path").attr("d", "M0,-5L10,0L0,5").attr("fill", t.inkSoft);

defs.append("marker")
  .attr("id", "arrow-start")
  .attr("viewBox", "0 -5 10 10")
  .attr("refX", 2).attr("refY", 0)
  .attr("markerWidth", 5).attr("markerHeight", 5)
  .attr("orient", "auto-start-reverse")
  .append("path").attr("d", "M0,-5L10,0L0,5").attr("fill", t.inkSoft);

// --- Y-axis gridlines
g.append("g")
  .selectAll("line.grid")
  .data(yScale.ticks(7))
  .join("line")
  .attr("class", "grid")
  .attr("x1", 0).attr("x2", iw)
  .attr("y1", d => yScale(d)).attr("y2", d => yScale(d))
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- Subtle shaded ΔH region between reactant and product energy levels
g.append("rect")
  .attr("x", 0)
  .attr("y", yScale(E_r))
  .attr("width", iw)
  .attr("height", yScale(E_p) - yScale(E_r))
  .attr("fill", t.palette[0])
  .attr("opacity", 0.08);

// --- Horizontal dashed reference lines at reactant and product energy levels
g.append("line")
  .attr("x1", 0).attr("x2", xScale(0.38))
  .attr("y1", yScale(E_r)).attr("y2", yScale(E_r))
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1.5)
  .attr("stroke-dasharray", "8,5")
  .attr("opacity", 0.6);

g.append("line")
  .attr("x1", xScale(0.62)).attr("x2", iw)
  .attr("y1", yScale(E_p)).attr("y2", yScale(E_p))
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1.5)
  .attr("stroke-dasharray", "8,5")
  .attr("opacity", 0.6);

// --- Ea double-headed arrow (reactant level → transition state peak)
const eaX = xScale(0.22);
g.append("line")
  .attr("x1", eaX).attr("y1", yScale(E_r) - 2)
  .attr("x2", eaX).attr("y2", yScale(E_ts) + 2)
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 2)
  .attr("marker-start", "url(#arrow-start)")
  .attr("marker-end", "url(#arrow-end)");

g.append("text")
  .attr("x", eaX + 10)
  .attr("y", yScale((E_r + E_ts) / 2))
  .attr("fill", t.ink)
  .attr("dominant-baseline", "middle")
  .style("font-size", "15px")
  .text(`Eₐ = ${E_ts - E_r} kJ/mol`);

// --- ΔH double-headed arrow (reactant level → product level)
const dhX = xScale(0.78);
g.append("line")
  .attr("x1", dhX).attr("y1", yScale(E_r) + 2)
  .attr("x2", dhX).attr("y2", yScale(E_p) - 2)
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 2)
  .attr("marker-start", "url(#arrow-start)")
  .attr("marker-end", "url(#arrow-end)");

g.append("text")
  .attr("x", dhX + 16)
  .attr("y", yScale((E_r + E_p) / 2))
  .attr("fill", t.ink)
  .attr("dominant-baseline", "middle")
  .style("font-size", "15px")
  .text(`ΔH = ${E_p - E_r} kJ/mol`);

// --- Main reaction coordinate curve
const line = d3.line()
  .x(d => xScale(d.x))
  .y(d => yScale(d.energy))
  .curve(d3.curveCatmullRom.alpha(0.5));

g.append("path")
  .datum(curveData)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 4)
  .attr("d", line);

// --- Direct labels for Reactants, Transition State, Products
// Reactants
g.append("text")
  .attr("x", xScale(0.07))
  .attr("y", yScale(E_r) - 20)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .style("font-weight", "600")
  .text("Reactants");

g.append("text")
  .attr("x", xScale(0.07))
  .attr("y", yScale(E_r) - 4)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text(`${E_r} kJ/mol`);

// Transition State
g.append("text")
  .attr("x", xScale(0.5))
  .attr("y", yScale(E_ts) - 20)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .style("font-weight", "600")
  .text("Transition State ‡");

g.append("text")
  .attr("x", xScale(0.5))
  .attr("y", yScale(E_ts) - 4)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text(`${E_ts} kJ/mol`);

// Products
g.append("text")
  .attr("x", xScale(0.93))
  .attr("y", yScale(E_p) - 20)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .style("font-weight", "600")
  .text("Products");

g.append("text")
  .attr("x", xScale(0.93))
  .attr("y", yScale(E_p) - 4)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text(`${E_p} kJ/mol`);

// --- Axes
const xAxis = g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(xScale).ticks(0).tickSize(0));

xAxis.select(".domain").attr("stroke", t.inkSoft).attr("stroke-width", 1.5);
xAxis.selectAll("text").remove();

const yAxis = g.append("g")
  .call(d3.axisLeft(yScale).ticks(7).tickSize(5));

yAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
yAxis.selectAll(".tick line").attr("stroke", t.grid);
yAxis.select(".domain").attr("stroke", "none");

// --- Axis labels
svg.append("text")
  .attr("transform", `translate(${margin.left - 72},${margin.top + ih / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Potential Energy (kJ/mol)");

svg.append("text")
  .attr("x", margin.left + iw / 2)
  .attr("y", margin.top + ih + 62)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text("Reaction Coordinate →");

// --- Title
svg.append("text")
  .attr("x", width / 2).attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("line-reaction-coordinate · javascript · d3 · anyplot.ai");
