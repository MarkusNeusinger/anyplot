// anyplot.ai
// rose-basic: Basic Rose Chart
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: 91/100 | Created: 2026-07-25
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Monthly rainfall for a temperate coastal city (mm), Jan at 12 o'clock
const monthlyRainfall = [
  { month: "Jan", mm: 142 },
  { month: "Feb", mm: 118 },
  { month: "Mar", mm: 98 },
  { month: "Apr", mm: 68 },
  { month: "May", mm: 47 },
  { month: "Jun", mm: 38 },
  { month: "Jul", mm: 19 },
  { month: "Aug", mm: 24 },
  { month: "Sep", mm: 52 },
  { month: "Oct", mm: 96 },
  { month: "Nov", mm: 151 },
  { month: "Dec", mm: 158 },
];

// --- Layout -------------------------------------------------------------------
const marginTop = 110;
const cx = width / 2;
const cy = marginTop + (height - marginTop) / 2;
const maxRadius = Math.min(width, height - marginTop) / 2 - 110;

// --- Scales ---------------------------------------------------------------------
const angleStep = (2 * Math.PI) / monthlyRainfall.length;
const wedgeAngle = angleStep * 0.82;
const maxRainfall = d3.max(monthlyRainfall, (d) => d.mm);
const radius = d3.scaleLinear().domain([0, maxRainfall]).nice().range([0, maxRadius]);
// Explicit lightness-scaled hex per value (not `fill-opacity`) so equal rainfall
// values read as the same color in both themes — opacity would otherwise blend
// against the theme-dependent page background and shift hue between renders.
const wedgeColor = d3.scaleLinear().domain([0, maxRainfall]).range(["#BFE9DB", t.palette[0]]);

monthlyRainfall.forEach((d, i) => {
  d.centerAngle = i * angleStep;
  d.startAngle = d.centerAngle - wedgeAngle / 2;
  d.endAngle = d.centerAngle + wedgeAngle / 2;
});

// --- SVG mount --------------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const plot = svg.append("g").attr("transform", `translate(${cx},${cy})`);

// --- Radial gridlines (aid value estimation) ---------------------------------------
const gridTicks = radius.ticks(4).filter((v) => v > 0);

plot
  .selectAll("circle.grid-ring")
  .data(gridTicks)
  .join("circle")
  .attr("class", "grid-ring")
  .attr("r", (d) => radius(d))
  .attr("fill", "none")
  .attr("stroke", t.grid)
  .attr("stroke-width", 1.5);

// Placed along the bottom (Jul) spoke, where the shortest wedges leave the
// rings clear — every other spoke direction is crossed by a tall wedge.
plot
  .selectAll("text.grid-label")
  .data(gridTicks)
  .join("text")
  .attr("class", "grid-label")
  .attr("x", 8)
  .attr("y", (d) => radius(d) + 4)
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text((d) => `${d} mm`);

// --- Wedges (radius proportional to value) --------------------------------------------
const wedge = d3
  .arc()
  .innerRadius(0)
  .outerRadius((d) => radius(d.mm))
  .startAngle((d) => d.startAngle)
  .endAngle((d) => d.endAngle);

plot
  .selectAll("path.wedge")
  .data(monthlyRainfall)
  .join("path")
  .attr("class", "wedge")
  .attr("d", wedge)
  .attr("fill", (d) => wedgeColor(d.mm))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 2);

// --- Month labels -----------------------------------------------------------------
const labelRadius = maxRadius + 46;

plot
  .selectAll("text.month-label")
  .data(monthlyRainfall)
  .join("text")
  .attr("class", "month-label")
  .attr("x", (d) => labelRadius * Math.sin(d.centerAngle))
  .attr("y", (d) => -labelRadius * Math.cos(d.centerAngle) + 5)
  .attr("text-anchor", (d) => {
    const s = Math.sin(d.centerAngle);
    if (s > 0.15) return "start";
    if (s < -0.15) return "end";
    return "middle";
  })
  .attr("fill", t.inkSoft)
  .style("font-size", "16px")
  .text((d) => d.month);

// --- Title --------------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("rose-basic · javascript · d3 · anyplot.ai");
