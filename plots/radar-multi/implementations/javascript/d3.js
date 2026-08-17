// anyplot.ai
// radar-multi: Multi-Series Radar Chart
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-08-17

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data: Quarterly Performance Review — Competency Scores (0-100) --------
const categories = [
  "Communication",
  "Technical Skill",
  "Leadership",
  "Creativity",
  "Problem Solving",
  "Teamwork",
];
const series = [
  { name: "Alicia Chen", values: [85, 70, 90, 60, 75, 80] },
  { name: "Marcus Reyes", values: [60, 95, 55, 70, 88, 65] },
  { name: "Priya Nair", values: [75, 65, 70, 92, 68, 85] },
];

const maxValue = 100;
const ringCount = 5; // gridlines at 20, 40, 60, 80, 100
const angleSlice = (Math.PI * 2) / categories.length;

// --- Layout ------------------------------------------------------------------
const titleH = 90;
const legendH = 90;
const margin = 170;
const radius = Math.min(width, height - titleH - legendH) / 2 - margin;
const centerX = width / 2;
const centerY = titleH + (height - titleH - legendH) / 2;

const rScale = d3.scaleLinear().domain([0, maxValue]).range([0, radius]);

function angleFor(i) {
  return angleSlice * i - Math.PI / 2;
}
function pointFor(i, value) {
  const a = angleFor(i);
  const r = rScale(value);
  return [centerX + r * Math.cos(a), centerY + r * Math.sin(a)];
}

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Grid rings -----------------------------------------------------------------
const gridGroup = svg.append("g");
for (let lvl = 1; lvl <= ringCount; lvl++) {
  const value = (maxValue / ringCount) * lvl;
  const points = categories.map((_, i) => pointFor(i, value));
  gridGroup
    .append("polygon")
    .attr("points", points.map((p) => p.join(",")).join(" "))
    .attr("fill", "none")
    .attr("stroke", t.grid)
    .attr("stroke-width", 1);
}

// --- Axis spokes + category labels --------------------------------------------
const axisGroup = svg.append("g");
categories.forEach((cat, i) => {
  const [x, y] = pointFor(i, maxValue);
  axisGroup
    .append("line")
    .attr("x1", centerX)
    .attr("y1", centerY)
    .attr("x2", x)
    .attr("y2", y)
    .attr("stroke", t.grid)
    .attr("stroke-width", 1);

  const a = angleFor(i);
  const labelR = radius + 36;
  const lx = centerX + labelR * Math.cos(a);
  const ly = centerY + labelR * Math.sin(a);
  let anchor = "middle";
  if (Math.cos(a) > 0.15) anchor = "start";
  else if (Math.cos(a) < -0.15) anchor = "end";
  axisGroup
    .append("text")
    .attr("x", lx)
    .attr("y", ly)
    .attr("text-anchor", anchor)
    .attr("dominant-baseline", "middle")
    .attr("fill", t.ink)
    .style("font-size", "18px")
    .text(cat);
});

// --- Series polygons ------------------------------------------------------------
const radarLine = d3
  .lineRadial()
  .radius((d) => rScale(d))
  .angle((d, i) => angleSlice * i)
  .curve(d3.curveLinearClosed);

const seriesGroup = svg.append("g").attr("transform", `translate(${centerX},${centerY})`);

series.forEach((s, si) => {
  const color = t.palette[si];
  seriesGroup
    .append("path")
    .attr("d", radarLine(s.values))
    .attr("fill", color)
    .attr("fill-opacity", 0.22)
    .attr("stroke", color)
    .attr("stroke-width", 3.5)
    .attr("stroke-linejoin", "round");

  s.values.forEach((value, i) => {
    const a = angleSlice * i - Math.PI / 2;
    const r = rScale(value);
    seriesGroup
      .append("circle")
      .attr("cx", r * Math.cos(a))
      .attr("cy", r * Math.sin(a))
      .attr("r", 6)
      .attr("fill", color)
      .attr("stroke", t.pageBg)
      .attr("stroke-width", 1.5);
  });
});

// --- Ring value labels (drawn on top of series, haloed for legibility) --------
const ringLabelGroup = svg.append("g");
for (let lvl = 1; lvl <= ringCount; lvl++) {
  const value = (maxValue / ringCount) * lvl;
  const label = ringLabelGroup
    .append("text")
    .attr("x", centerX + 8)
    .attr("y", centerY - rScale(value) - 4)
    .attr("fill", t.inkSoft)
    .style("font-size", "13px")
    .text(value.toFixed(0));
  const bbox = label.node().getBBox();
  ringLabelGroup
    .insert("rect", () => label.node())
    .attr("x", bbox.x - 3)
    .attr("y", bbox.y - 2)
    .attr("width", bbox.width + 6)
    .attr("height", bbox.height + 4)
    .attr("fill", t.pageBg)
    .attr("opacity", 0.85);
}

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 54)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("radar-multi · javascript · d3 · anyplot.ai");

// --- Legend (centered, measured after render) --------------------------------
const legendY = height - 44;
const swatchSize = 20;
const itemGap = 44;

const legendItems = svg
  .selectAll("g.legend-item")
  .data(series)
  .join("g")
  .attr("class", "legend-item");

legendItems
  .append("rect")
  .attr("width", swatchSize)
  .attr("height", swatchSize)
  .attr("rx", 4)
  .attr("fill", (d, i) => t.palette[i]);

legendItems
  .append("text")
  .attr("x", swatchSize + 10)
  .attr("y", swatchSize / 2)
  .attr("dominant-baseline", "middle")
  .attr("fill", t.ink)
  .style("font-size", "18px")
  .text((d) => d.name);

const itemWidths = [];
legendItems.each(function () {
  itemWidths.push(this.getBBox().width);
});
const totalWidth = itemWidths.reduce((a, b) => a + b, 0) + itemGap * (itemWidths.length - 1);
let cursorX = centerX - totalWidth / 2;
legendItems.each(function (d, i) {
  d3.select(this).attr("transform", `translate(${cursorX},${legendY})`);
  cursorX += itemWidths[i] + itemGap;
});
