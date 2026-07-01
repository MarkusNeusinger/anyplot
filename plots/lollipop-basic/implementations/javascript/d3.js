// anyplot.ai
// lollipop-basic: Basic Lollipop Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-07-01
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 80, right: 130, bottom: 70, left: 215 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Data: World's most-visited museums (annual visitors, millions, 2019)
// sorted ascending — scaleBand range([ih,0]) maps first→bottom, last→top
const museums = [
  { name: "Musée d'Orsay",          visitors: 4.0 },
  { name: "Smithsonian Air & Space", visitors: 4.5 },
  { name: "Tokyo National Museum",   visitors: 4.8 },
  { name: "National Gallery",        visitors: 5.7 },
  { name: "Tate Modern",             visitors: 5.9 },
  { name: "British Museum",          visitors: 6.2 },
  { name: "Metropolitan Museum",     visitors: 6.5 },
  { name: "Vatican Museums",         visitors: 6.8 },
  { name: "Nat'l Museum of China",   visitors: 8.6 },
  { name: "Louvre",                  visitors: 9.6 },
];

// SVG
const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Scales
const x = d3.scaleLinear().domain([0, 11]).range([0, iw]);
const y = d3.scaleBand()
  .domain(museums.map(d => d.name))
  .range([ih, 0])
  .padding(0.45);

// Vertical gridlines
x.ticks(6).forEach(tick => {
  g.append("line")
    .attr("x1", x(tick)).attr("x2", x(tick))
    .attr("y1", 0).attr("y2", ih)
    .attr("stroke", t.grid)
    .attr("stroke-width", 1);
});

// Axes
const xAxisG = g.append("g").attr("transform", `translate(0,${ih})`).call(
  d3.axisBottom(x).ticks(6).tickFormat(d => `${d}M`)
);
const yAxisG = g.append("g").call(d3.axisLeft(y).tickSize(0).tickPadding(10));

xAxisG.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
xAxisG.selectAll("line").attr("stroke", t.grid);
xAxisG.select(".domain").attr("stroke", t.inkSoft);

yAxisG.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
yAxisG.select(".domain").attr("stroke", t.inkSoft);

// Stems
g.selectAll(".stem")
  .data(museums)
  .join("line")
  .attr("class", "stem")
  .attr("x1", 0)
  .attr("x2", d => x(d.visitors))
  .attr("y1", d => y(d.name) + y.bandwidth() / 2)
  .attr("y2", d => y(d.name) + y.bandwidth() / 2)
  .attr("stroke", t.palette[0])
  .attr("stroke-width", 2.5)
  .attr("stroke-opacity", 0.65);

// Dots
g.selectAll(".dot")
  .data(museums)
  .join("circle")
  .attr("class", "dot")
  .attr("cx", d => x(d.visitors))
  .attr("cy", d => y(d.name) + y.bandwidth() / 2)
  .attr("r", 10)
  .attr("fill", t.palette[0])
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2.5);

// Value labels
g.selectAll(".val")
  .data(museums)
  .join("text")
  .attr("class", "val")
  .attr("x", d => x(d.visitors) + 16)
  .attr("y", d => y(d.name) + y.bandwidth() / 2)
  .attr("dy", "0.35em")
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .text(d => `${d.visitors}M`);

// X-axis label
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 55)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Annual Visitors (millions, 2019)");

// Title
svg.append("text")
  .attr("x", width / 2)
  .attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("lollipop-basic · javascript · d3 · anyplot.ai");
