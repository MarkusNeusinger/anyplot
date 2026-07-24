// anyplot.ai
// radar-basic: Basic Radar Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-07-24

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
const categories = [
  "Communication", "Technical Skills", "Teamwork",
  "Leadership", "Problem Solving", "Adaptability",
];
const series = [
  { name: "Software Engineer", values: [85, 92, 78, 65, 88, 74], color: t.palette[0] },
  { name: "Team Average", values: [70, 75, 72, 68, 70, 71], color: t.palette[1] },
];
const maxValue = 100;
const gridLevels = [20, 40, 60, 80, 100];

// --- Layout ------------------------------------------------------------------
const titleSpace = 90;
const legendSpace = 70;
const cx = width / 2;
const cy = titleSpace + (height - titleSpace - legendSpace) / 2;
const radius = Math.min(width, height - titleSpace - legendSpace) / 2 - 90;
const angleSlice = (2 * Math.PI) / categories.length;
const rScale = d3.scaleLinear().domain([0, maxValue]).range([0, radius]);

const angleFor = (i) => i * angleSlice - Math.PI / 2;
const point = (i, value) => {
  const a = angleFor(i);
  return [cx + rScale(value) * Math.cos(a), cy + rScale(value) * Math.sin(a)];
};

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Grid: concentric webs + spokes -------------------------------------------
gridLevels.forEach((level) => {
  const gridPoints = categories.map((_, i) => point(i, level));
  svg.append("polygon")
    .attr("points", gridPoints.map((p) => p.join(",")).join(" "))
    .attr("fill", "none")
    .attr("stroke", t.grid)
    .attr("stroke-width", 1);
});

gridLevels.forEach((level) => {
  const [, y] = point(0, level);
  svg.append("text")
    .attr("x", cx + 6).attr("y", y)
    .attr("fill", t.inkSoft)
    .attr("dominant-baseline", "middle")
    .style("font-size", "12px")
    .text(level);
});

categories.forEach((cat, i) => {
  const [x, y] = point(i, maxValue);
  svg.append("line")
    .attr("x1", cx).attr("y1", cy).attr("x2", x).attr("y2", y)
    .attr("stroke", t.grid).attr("stroke-width", 1);

  const [lx, ly] = point(i, maxValue * 1.14);
  const cos = Math.cos(angleFor(i));
  const anchor = cos > 0.15 ? "start" : cos < -0.15 ? "end" : "middle";
  svg.append("text")
    .attr("x", lx).attr("y", ly)
    .attr("text-anchor", anchor)
    .attr("dominant-baseline", "middle")
    .attr("fill", t.ink)
    .style("font-size", "16px")
    .text(cat);
});

// --- Data polygons --------------------------------------------------------------
const radarLine = d3.line().x((d) => d[0]).y((d) => d[1]).curve(d3.curveLinearClosed);

series.forEach((s) => {
  const pts = s.values.map((v, i) => point(i, v));
  svg.append("path")
    .attr("d", radarLine(pts))
    .attr("fill", s.color)
    .attr("fill-opacity", 0.25)
    .attr("stroke", s.color)
    .attr("stroke-width", 3);

  pts.forEach(([x, y]) => {
    svg.append("circle")
      .attr("cx", x).attr("cy", y).attr("r", 5)
      .attr("fill", s.color)
      .attr("stroke", t.pageBg)
      .attr("stroke-width", 1.5);
  });
});

// --- Title ------------------------------------------------------------------
svg.append("text")
  .attr("x", width / 2).attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("radar-basic · javascript · d3 · anyplot.ai");

// --- Legend -------------------------------------------------------------------
const legendY = height - 36;
const legendItemWidth = 260;
const legendStartX = width / 2 - (series.length * legendItemWidth) / 2;
series.forEach((s, i) => {
  const gx = legendStartX + i * legendItemWidth;
  svg.append("rect")
    .attr("x", gx).attr("y", legendY - 12)
    .attr("width", 16).attr("height", 16)
    .attr("fill", s.color);
  svg.append("text")
    .attr("x", gx + 24).attr("y", legendY)
    .attr("fill", t.inkSoft)
    .attr("dominant-baseline", "middle")
    .style("font-size", "16px")
    .text(s.name);
});
