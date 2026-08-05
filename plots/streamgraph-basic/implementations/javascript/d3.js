// anyplot.ai
// streamgraph-basic: Basic Stream Graph
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 190, bottom: 60, left: 30 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: monthly streaming hours by music genre, 2024-2025 (deterministic) --
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const months = d3.range(24).map((i) => new Date(2024, i, 1));

const genreConfig = [
  { name: "Pop", base: 55, amp: 18, phase: 0.3, trend: 0 },
  { name: "Hip-Hop", base: 42, amp: 14, phase: 1.8, trend: 0.6 },
  { name: "Electronic", base: 30, amp: 16, phase: 2.6, trend: 0.5 },
  { name: "Rock", base: 34, amp: 9, phase: 0.9, trend: -0.35 },
  { name: "Jazz", base: 16, amp: 5, phase: 4.0, trend: 0.05 },
  { name: "Classical", base: 11, amp: 3, phase: 5.2, trend: -0.05 },
];
const genres = genreConfig.map((g) => g.name);
const freq = (2 * Math.PI) / 12;

const data = months.map((date, i) => {
  const row = { date };
  for (const g of genreConfig) {
    const seasonal = Math.sin(i * freq + g.phase) * g.amp;
    const noise = (rand() - 0.5) * 4;
    row[g.name] = Math.max(2, g.base + seasonal + g.trend * i + noise);
  }
  return row;
});

// --- Stack (wiggle offset = symmetric streamgraph baseline) ------------------
const stack = d3
  .stack()
  .keys(genres)
  .order(d3.stackOrderInsideOut)
  .offset(d3.stackOffsetWiggle);
const series = stack(data);

const x = d3.scaleTime().domain(d3.extent(months)).range([0, iw]);
const yExtent = d3.extent(series.flatMap((s) => s.flatMap((d) => [d[0], d[1]])));
const y = d3.scaleLinear().domain(yExtent).range([ih, 0]);
const color = d3.scaleOrdinal().domain(genres).range(t.palette.slice(0, genres.length));

const area = d3
  .area()
  .curve(d3.curveBasis)
  .x((d) => x(d.data.date))
  .y0((d) => y(d[0]))
  .y1((d) => y(d[1]));

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Streams --------------------------------------------------------------
g.selectAll("path.layer")
  .data(series)
  .join("path")
  .attr("class", "layer")
  .attr("fill", (d) => color(d.key))
  .attr("d", area);

// --- Time axis (no value axis — the wiggle baseline has no meaningful zero) --
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih + 16})`)
  .call(d3.axisBottom(x).ticks(d3.timeMonth.every(3)).tickFormat(d3.timeFormat("%b %Y")).tickSizeOuter(0));
xAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
xAxis.selectAll("line").attr("stroke", t.grid);
xAxis.select(".domain").attr("stroke", t.inkSoft);

// --- Legend -----------------------------------------------------------------
const legend = svg
  .append("g")
  .attr("transform", `translate(${width - margin.right + 34}, ${margin.top + 20})`);
genres.forEach((name, i) => {
  const row = legend.append("g").attr("transform", `translate(0, ${i * 34})`);
  row.append("rect").attr("width", 18).attr("height", 18).attr("rx", 3).attr("fill", color(name));
  row
    .append("text")
    .attr("x", 26)
    .attr("y", 14)
    .attr("fill", t.ink)
    .style("font-size", "15px")
    .text(name);
});

// --- Title --------------------------------------------------------------------
const title = "Music Genre Streaming · streamgraph-basic · javascript · d3 · anyplot.ai";
const ratio = title.length > 67 ? 67 / title.length : 1.0;
const titleFontSize = Math.max(14, Math.round(22 * ratio));
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 50)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(title);
