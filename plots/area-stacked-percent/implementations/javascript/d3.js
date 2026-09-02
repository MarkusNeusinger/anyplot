// anyplot.ai
// area-stacked-percent: 100% Stacked Area Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const inkMuted = t.theme === "light" ? "#6B6A63" : "#A8A79F";
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 140, right: 50, bottom: 70, left: 90 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Illustrative global desktop browser market share, 2015-2024 (yearly).
const SERIES = [
  { key: "chrome", label: "Chrome" },
  { key: "safari", label: "Safari" },
  { key: "edge", label: "Edge / IE" },
  { key: "firefox", label: "Firefox" },
  { key: "other", label: "Other" },
];

const data = [
  { year: 2015, chrome: 45, safari: 15, edge: 20, firefox: 15, other: 5 },
  { year: 2016, chrome: 50, safari: 15, edge: 15, firefox: 12, other: 8 },
  { year: 2017, chrome: 55, safari: 15, edge: 12, firefox: 10, other: 8 },
  { year: 2018, chrome: 58, safari: 15, edge: 10, firefox: 9, other: 8 },
  { year: 2019, chrome: 62, safari: 16, edge: 7, firefox: 8, other: 7 },
  { year: 2020, chrome: 64, safari: 17, edge: 6, firefox: 7, other: 6 },
  { year: 2021, chrome: 65, safari: 18, edge: 4, firefox: 6, other: 7 },
  { year: 2022, chrome: 64, safari: 19, edge: 4, firefox: 5, other: 8 },
  { year: 2023, chrome: 63, safari: 20, edge: 5, firefox: 4, other: 8 },
  { year: 2024, chrome: 62, safari: 21, edge: 5, firefox: 3, other: 9 },
];

const years = data.map((d) => d.year);

// "Other" reads as the semantic muted anchor; the named series keep canonical order.
const colorFor = (key) => {
  if (key === "other") return inkMuted;
  const index = SERIES.findIndex((s) => s.key === key);
  return t.palette[index];
};

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales --------------------------------------------------------------
const x = d3.scaleLinear().domain(d3.extent(years)).range([0, iw]);
const y = d3.scaleLinear().domain([0, 1]).range([ih, 0]);

// --- Stack (normalized to 100%) -----------------------------------------
const stack = d3.stack().keys(SERIES.map((s) => s.key)).offset(d3.stackOffsetExpand);
const layers = stack(data);

// --- Gridlines (y-axis only) ----------------------------------------------
g.append("g")
  .selectAll("line")
  .data(y.ticks(4))
  .join("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", (d) => y(d))
  .attr("y2", (d) => y(d))
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- Areas -----------------------------------------------------------------
const area = d3
  .area()
  .x((d) => x(d.data.year))
  .y0((d) => y(d[0]))
  .y1((d) => y(d[1]))
  .curve(d3.curveMonotoneX);

g.selectAll("path.layer")
  .data(layers)
  .join("path")
  .attr("class", "layer")
  .attr("fill", (d) => colorFor(d.key))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5)
  .attr("d", area);

// --- Axes --------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).tickValues(years).tickFormat(d3.format("d")).tickSizeOuter(0));

const yAxis = g.append("g").call(d3.axisLeft(y).ticks(4).tickFormat(d3.format(".0%")).tickSizeOuter(0));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}
xAxis.selectAll("line").remove();
yAxis.selectAll("line").remove();

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -64)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Share of Total");

// --- Legend (measured in-browser, then centered) ----------------------------
const legendG = svg.append("g");
const swatch = 16;
const swatchGap = 8;
const itemGap = 28;
let cursorX = 0;
const items = [];

for (const s of SERIES) {
  const item = legendG.append("g");
  item
    .append("rect")
    .attr("width", swatch)
    .attr("height", swatch)
    .attr("rx", 3)
    .attr("fill", colorFor(s.key));
  const label = item
    .append("text")
    .attr("x", swatch + swatchGap)
    .attr("y", swatch - 3)
    .attr("fill", t.inkSoft)
    .style("font-size", "15px")
    .text(s.label);
  const itemWidth = swatch + swatchGap + label.node().getBBox().width;
  items.push({ item, x: cursorX });
  cursorX += itemWidth + itemGap;
}

const legendWidth = cursorX - itemGap;
const legendStartX = (width - legendWidth) / 2;
for (const { item, x: itemX } of items) {
  item.attr("transform", `translate(${legendStartX + itemX},${92})`);
}

// --- Title -------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("area-stacked-percent · javascript · d3 · anyplot.ai");
