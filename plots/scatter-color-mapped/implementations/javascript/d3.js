// anyplot.ai
// scatter-color-mapped: Color-Mapped Scatter Plot
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 100, right: 190, bottom: 90, left: 100 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic LCG) ------------------------------------
// Urban heat island study: surface temperature recorded at monitoring
// stations scattered around a city center.
let seed = 42;
function nextRandom() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const stationCount = 180;
const stations = [];
for (let i = 0; i < stationCount; i++) {
  const distanceEast = (nextRandom() - 0.5) * 24;
  const distanceNorth = (nextRandom() - 0.5) * 24;
  const distanceFromCenter = Math.sqrt(distanceEast ** 2 + distanceNorth ** 2);
  const surfaceTemp = 34 - distanceFromCenter * 0.55 + (nextRandom() - 0.5) * 3;
  stations.push({ distanceEast, distanceNorth, surfaceTemp });
}

// --- Scales -------------------------------------------------------------
const x = d3.scaleLinear().domain(d3.extent(stations, (d) => d.distanceEast)).nice().range([0, iw]);
const y = d3.scaleLinear().domain(d3.extent(stations, (d) => d.distanceNorth)).nice().range([ih, 0]);
const [tempMin, tempMax] = d3.extent(stations, (d) => d.surfaceTemp);
const color = d3.scaleSequential(d3.interpolateRgbBasis(t.seq)).domain([tempMin, tempMax]);

// --- SVG mount ------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Gridlines (both axes, scatter convention) -------------------------
g.append("g")
  .selectAll("line")
  .data(x.ticks(8))
  .join("line")
  .attr("x1", (d) => x(d))
  .attr("x2", (d) => x(d))
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.grid);

g.append("g")
  .selectAll("line")
  .data(y.ticks(8))
  .join("line")
  .attr("y1", (d) => y(d))
  .attr("y2", (d) => y(d))
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("stroke", t.grid);

// --- Axes -------------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(8));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(8));
for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels --------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Distance East of City Center (km)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -70)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Distance North of City Center (km)");

// --- Points ---------------------------------------------------------------
g.selectAll("circle")
  .data(stations)
  .join("circle")
  .attr("cx", (d) => x(d.distanceEast))
  .attr("cy", (d) => y(d.distanceNorth))
  .attr("r", 9)
  .attr("fill", (d) => color(d.surfaceTemp))
  .attr("fill-opacity", 0.85)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1);

// --- Colorbar (Imprint sequential scale) -----------------------------------
const barWidth = 22;
const barX = iw + 55;

const gradient = svg
  .append("defs")
  .append("linearGradient")
  .attr("id", "temperature-gradient")
  .attr("x1", "0%")
  .attr("x2", "0%")
  .attr("y1", "100%")
  .attr("y2", "0%");
d3.range(0, 1.0001, 0.1).forEach((stop) => {
  gradient
    .append("stop")
    .attr("offset", `${stop * 100}%`)
    .attr("stop-color", color(tempMin + stop * (tempMax - tempMin)));
});

g.append("rect")
  .attr("x", barX)
  .attr("y", 0)
  .attr("width", barWidth)
  .attr("height", ih)
  .attr("fill", "url(#temperature-gradient)");

const barScale = d3.scaleLinear().domain([tempMin, tempMax]).range([ih, 0]);
const barAxis = g
  .append("g")
  .attr("transform", `translate(${barX + barWidth},0)`)
  .call(
    d3
      .axisRight(barScale)
      .ticks(6)
      .tickFormat((d) => `${d.toFixed(0)}°`),
  );
barAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "13px");
barAxis.selectAll("line").attr("stroke", t.inkSoft);
barAxis.select(".domain").attr("stroke", t.inkSoft);

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", barX + barWidth + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "15px")
  .text("Surface Temperature (°C)");

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("scatter-color-mapped · javascript · d3 · anyplot.ai");
