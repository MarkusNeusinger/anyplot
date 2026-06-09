// anyplot.ai
// scatter-connected-temporal: Connected Scatter Plot with Temporal Path
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-09

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 140, bottom: 90, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// GDP per capita (thousands USD, 2015 prices) vs. Life Expectancy (years), 1992–2021
const data = [
  { year: 1992, gdp: 23.0, le: 75.3 }, { year: 1993, gdp: 23.8, le: 75.5 },
  { year: 1994, gdp: 25.2, le: 75.7 }, { year: 1995, gdp: 26.1, le: 75.9 },
  { year: 1996, gdp: 27.3, le: 76.1 }, { year: 1997, gdp: 28.8, le: 76.4 },
  { year: 1998, gdp: 29.7, le: 76.7 }, { year: 1999, gdp: 31.0, le: 77.0 },
  { year: 2000, gdp: 32.8, le: 77.2 }, { year: 2001, gdp: 32.1, le: 77.3 },
  { year: 2002, gdp: 31.6, le: 77.5 }, { year: 2003, gdp: 32.7, le: 77.5 },
  { year: 2004, gdp: 34.5, le: 77.7 }, { year: 2005, gdp: 36.1, le: 77.9 },
  { year: 2006, gdp: 38.0, le: 78.1 }, { year: 2007, gdp: 39.8, le: 78.2 },
  { year: 2008, gdp: 40.2, le: 78.4 }, { year: 2009, gdp: 37.1, le: 78.6 },
  { year: 2010, gdp: 38.6, le: 78.8 }, { year: 2011, gdp: 40.0, le: 79.0 },
  { year: 2012, gdp: 40.8, le: 79.1 }, { year: 2013, gdp: 42.0, le: 79.3 },
  { year: 2014, gdp: 43.7, le: 79.4 }, { year: 2015, gdp: 44.7, le: 79.6 },
  { year: 2016, gdp: 45.3, le: 79.6 }, { year: 2017, gdp: 47.1, le: 79.7 },
  { year: 2018, gdp: 49.4, le: 79.8 }, { year: 2019, gdp: 51.1, le: 80.0 },
  { year: 2020, gdp: 48.2, le: 79.2 }, { year: 2021, gdp: 52.4, le: 79.5 },
];

// SVG scaffold
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const defs = svg.append("defs");

// Gradient for temporal legend bar (Imprint sequential: green → blue)
const legendGrad = defs.append("linearGradient")
  .attr("id", "temporal-grad")
  .attr("x1", "0%").attr("x2", "100%");
legendGrad.append("stop").attr("offset", "0%").attr("stop-color", t.seq[0]);
legendGrad.append("stop").attr("offset", "100%").attr("stop-color", t.seq[1]);

const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Scales
const xScale = d3.scaleLinear().domain(d3.extent(data, d => d.gdp)).nice().range([0, iw]);
const yScale = d3.scaleLinear().domain(d3.extent(data, d => d.le)).nice().range([ih, 0]);

// Temporal color interpolator: Imprint sequential (green → blue)
const tempColor = frac => d3.interpolateRgb(t.seq[0], t.seq[1])(frac);

// Gridlines (both axes — subtle)
xScale.ticks(6).forEach(v => {
  g.append("line")
    .attr("x1", xScale(v)).attr("x2", xScale(v))
    .attr("y1", 0).attr("y2", ih)
    .attr("stroke", t.grid).attr("stroke-width", 1);
});
yScale.ticks(6).forEach(v => {
  g.append("line")
    .attr("x1", 0).attr("x2", iw)
    .attr("y1", yScale(v)).attr("y2", yScale(v))
    .attr("stroke", t.grid).attr("stroke-width", 1);
});

// Connecting segments, each colored by its midpoint temporal fraction
for (let i = 0; i < data.length - 1; i++) {
  const midFrac = (i + 0.5) / (data.length - 1);
  g.append("line")
    .attr("x1", xScale(data[i].gdp)).attr("y1", yScale(data[i].le))
    .attr("x2", xScale(data[i + 1].gdp)).attr("y2", yScale(data[i + 1].le))
    .attr("stroke", tempColor(midFrac))
    .attr("stroke-width", 2.5)
    .attr("stroke-opacity", 0.85);
}

// Data point markers (larger circles for start and end)
g.selectAll("circle").data(data).join("circle")
  .attr("cx", d => xScale(d.gdp))
  .attr("cy", d => yScale(d.le))
  .attr("r", (d, i) => (i === 0 || i === data.length - 1) ? 9 : 5)
  .attr("fill", (d, i) => tempColor(i / (data.length - 1)))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2);

// Year labels at selected notable points
const labelConfig = [
  { year: 1992, dx: -46, dy: 6 },
  { year: 2000, dx: 10, dy: -13 },
  { year: 2007, dx: 10, dy: -13 },
  { year: 2009, dx: -46, dy: 19 },
  { year: 2015, dx: 10, dy: -13 },
  { year: 2020, dx: 6, dy: 22 },
  { year: 2021, dx: 12, dy: -13 },
];
data.forEach((d, i) => {
  const cfg = labelConfig.find(c => c.year === d.year);
  if (!cfg) return;
  const isEndpoint = d.year === 1992 || d.year === 2021;
  g.append("text")
    .attr("x", xScale(d.gdp) + cfg.dx)
    .attr("y", yScale(d.le) + cfg.dy)
    .attr("fill", isEndpoint ? t.ink : t.inkSoft)
    .style("font-size", isEndpoint ? "13px" : "12px")
    .style("font-weight", isEndpoint ? "700" : "400")
    .text(d.year);
});

// Axes
const xAxis = g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(xScale).ticks(6).tickFormat(d => `$${d3.format(".0f")(d)}k`));
const yAxis = g.append("g")
  .call(d3.axisLeft(yScale).ticks(6).tickFormat(d => `${d3.format(".0f")(d)} yrs`));

[xAxis, yAxis].forEach(ax => {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.grid);
  ax.select(".domain").attr("stroke", t.inkSoft);
});

// Axis labels
g.append("text")
  .attr("x", iw / 2).attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "16px")
  .text("GDP per Capita (USD thousands, 2015 prices)");
g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -(ih / 2)).attr("y", -78)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "16px")
  .text("Life Expectancy (years)");

// Temporal legend (gradient bar)
const lgW = 160, lgH = 10, lgX = iw - lgW - 8, lgY = 18;
g.append("text")
  .attr("x", lgX + lgW / 2).attr("y", lgY - 12)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft).style("font-size", "12px")
  .text("Temporal direction  →");
g.append("rect")
  .attr("x", lgX).attr("y", lgY)
  .attr("width", lgW).attr("height", lgH)
  .attr("rx", 4)
  .attr("fill", "url(#temporal-grad)");
g.append("text")
  .attr("x", lgX).attr("y", lgY + lgH + 14)
  .attr("fill", t.inkSoft).style("font-size", "11px")
  .text("1992");
g.append("text")
  .attr("x", lgX + lgW).attr("y", lgY + lgH + 14)
  .attr("text-anchor", "end")
  .attr("fill", t.inkSoft).style("font-size", "11px")
  .text("2021");

// Title
const title = "GDP & Life Expectancy · scatter-connected-temporal · javascript · d3 · anyplot.ai";
const titleFontSize = Math.max(13, Math.round(22 * 67 / title.length));
svg.append("text")
  .attr("x", width / 2).attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(title);
