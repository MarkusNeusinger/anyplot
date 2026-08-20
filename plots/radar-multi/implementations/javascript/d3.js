// anyplot.ai
// radar-multi: Multi-Series Radar Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-08-20

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Wireless headphone models scored 0-100 across shared review criteria.
const axes = [
  "Sound Quality",
  "Battery Life",
  "Comfort",
  "Noise Cancel.",
  "Build Quality",
  "Value",
];

const series = [
  { name: "Aria Pro", values: [88, 76, 82, 91, 79, 62] },
  { name: "Sonic Wave", values: [72, 94, 68, 58, 71, 85] },
  { name: "Bass Nova", values: [65, 60, 90, 74, 88, 70] },
];

const n = axes.length;
const angleSlice = (2 * Math.PI) / n;
const maxValue = 100;
const levels = [20, 40, 60, 80, 100];

// --- Layout -------------------------------------------------------------
const cx = width / 2;
const cy = height / 2;
const radius = Math.min(width, height) / 2 - 180;

const radiusScale = d3.scaleLinear().domain([0, maxValue]).range([0, radius]);
const color = d3.scaleOrdinal().domain(series.map((s) => s.name)).range(t.palette);

// --- SVG mount ------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${cx},${cy})`);

// --- Grid: concentric level circles + radial spokes ------------------------
const gridGroup = g.append("g");
gridGroup
  .selectAll("circle")
  .data(levels)
  .join("circle")
  .attr("r", (d) => radiusScale(d))
  .attr("fill", "none")
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

gridGroup
  .selectAll(".level-label")
  .data(levels)
  .join("text")
  .attr("class", "level-label")
  .attr("x", 4)
  .attr("y", (d) => -radiusScale(d) - 4)
  .attr("fill", t.inkSoft)
  .style("font-size", "12px")
  .text((d) => d);

const axisAngle = (i) => i * angleSlice - Math.PI / 2;

g.append("g")
  .selectAll("line")
  .data(axes)
  .join("line")
  .attr("x1", 0)
  .attr("y1", 0)
  .attr("x2", (d, i) => radiusScale(maxValue) * Math.cos(axisAngle(i)))
  .attr("y2", (d, i) => radiusScale(maxValue) * Math.sin(axisAngle(i)))
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- Axis labels --------------------------------------------------------
const labelRadius = radius + 34;
g.append("g")
  .selectAll("text")
  .data(axes)
  .join("text")
  .attr("x", (d, i) => labelRadius * Math.cos(axisAngle(i)))
  .attr("y", (d, i) => labelRadius * Math.sin(axisAngle(i)))
  .attr("text-anchor", (d, i) => {
    const c = Math.cos(axisAngle(i));
    if (c > 0.15) return "start";
    if (c < -0.15) return "end";
    return "middle";
  })
  .attr("dominant-baseline", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .style("font-weight", "500")
  .text((d) => d);

// --- Data polygons --------------------------------------------------------
const radarLine = d3
  .lineRadial()
  .angle((d, i) => i * angleSlice)
  .radius((d) => radiusScale(d))
  .curve(d3.curveLinearClosed);

const seriesGroup = g.append("g");

seriesGroup
  .selectAll(".radar-area")
  .data(series)
  .join("path")
  .attr("class", "radar-area")
  .attr("d", (d) => radarLine(d.values))
  .attr("fill", (d) => color(d.name))
  .attr("fill-opacity", 0.22)
  .attr("stroke", (d) => color(d.name))
  .attr("stroke-width", 3)
  .attr("stroke-linejoin", "round");

seriesGroup
  .selectAll(".radar-dots")
  .data(series)
  .join("g")
  .attr("class", "radar-dots")
  .attr("fill", (d) => color(d.name))
  .each(function (d) {
    d3.select(this)
      .selectAll("circle")
      .data(d.values)
      .join("circle")
      .attr("cx", (v, i) => radiusScale(v) * Math.cos(axisAngle(i)))
      .attr("cy", (v, i) => radiusScale(v) * Math.sin(axisAngle(i)))
      .attr("r", 6)
      .attr("stroke", t.pageBg)
      .attr("stroke-width", 1.5);
  });

// --- Legend -----------------------------------------------------------------
const legendItemWidth = 190;
const legendWidth = series.length * legendItemWidth;
const legend = svg
  .append("g")
  .attr("transform", `translate(${cx - legendWidth / 2},${height - 56})`);

const legendItems = legend
  .selectAll(".legend-item")
  .data(series)
  .join("g")
  .attr("class", "legend-item")
  .attr("transform", (d, i) => `translate(${i * legendItemWidth},0)`);

legendItems
  .append("rect")
  .attr("width", 18)
  .attr("height", 18)
  .attr("y", -14)
  .attr("rx", 3)
  .attr("fill", (d) => color(d.name));

legendItems
  .append("text")
  .attr("x", 26)
  .attr("y", 0)
  .attr("fill", t.ink)
  .style("font-size", "15px")
  .text((d) => d.name);

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("radar-multi · javascript · d3 · anyplot.ai");
