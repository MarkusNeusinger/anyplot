// anyplot.ai
// step-basic: Basic Step Plot
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: 84/100 | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 70, bottom: 110, left: 130 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: hourly warehouse inventory (units), restocked at hour 8 and 16 ---
const inventory = [
  { hour: 0, units: 480 },
  { hour: 1, units: 460 },
  { hour: 2, units: 460 },
  { hour: 3, units: 435 },
  { hour: 4, units: 435 },
  { hour: 5, units: 410 },
  { hour: 6, units: 390 },
  { hour: 7, units: 365 },
  { hour: 8, units: 600 },
  { hour: 9, units: 575 },
  { hour: 10, units: 550 },
  { hour: 11, units: 550 },
  { hour: 12, units: 515 },
  { hour: 13, units: 490 },
  { hour: 14, units: 460 },
  { hour: 15, units: 425 },
  { hour: 16, units: 620 },
  { hour: 17, units: 600 },
  { hour: 18, units: 580 },
  { hour: 19, units: 555 },
  { hour: 20, units: 530 },
  { hour: 21, units: 510 },
  { hour: 22, units: 490 },
  { hour: 23, units: 470 },
];

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales -------------------------------------------------------------------
const x = d3.scaleLinear().domain(d3.extent(inventory, (d) => d.hour)).range([0, iw]);
const y = d3
  .scaleLinear()
  .domain([300, d3.max(inventory, (d) => d.units)])
  .nice()
  .range([ih, 0]);

// --- Gridlines (y-axis only, per style guide) ---------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .call((sel) => sel.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid);

// --- Step line (post style: value holds until the next reading) --------------
const stepLine = d3
  .line()
  .x((d) => x(d.hour))
  .y((d) => y(d.units))
  .curve(d3.curveStepAfter);

g.append("path")
  .datum(inventory)
  .attr("fill", "none")
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 4)
  .attr("stroke-linejoin", "round")
  .attr("d", stepLine);

// --- Markers at each recorded reading ------------------------------------------
g.selectAll("circle")
  .data(inventory)
  .join("circle")
  .attr("cx", (d) => x(d.hour))
  .attr("cy", (d) => y(d.units))
  .attr("r", 7)
  .attr("fill", t.pageBg)
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 3);

// --- Axes -----------------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(
    d3
      .axisBottom(x)
      .tickValues(d3.range(0, 24, 4))
      .tickFormat((d) => `${d}:00`),
  );
const yAxis = g.append("g").call(d3.axisLeft(y));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels --------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 70)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .text("Hour of Day");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -95)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .text("Warehouse Inventory (units)");

// --- Title ----------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("step-basic · javascript · d3 · anyplot.ai");
