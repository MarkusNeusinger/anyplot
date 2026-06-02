// anyplot.ai
// pie-basic: Basic Pie Chart
// Library: d3 7.9.0 | JavaScript 22.22.3
// Quality: 85/100 | Created: 2026-06-02
//# anyplot-orientation: square
// anyplot.ai
// pie-basic: Basic Pie Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-02

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data — Streaming subscriber share (illustrative, 2024) ------------------
const data = [
  { category: "Netflix", value: 30 },
  { category: "Disney+", value: 22 },
  { category: "Amazon Prime", value: 18 },
  { category: "HBO Max", value: 16 },
  { category: "Hulu", value: 14 },
];
const total = d3.sum(data, (d) => d.value);

// --- SVG mount ---------------------------------------------------------------
const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);

// --- Layout — title on top, pie centered-left, legend on the right -----------
const titleY = 70;
const legendW = 280;
const pieAreaX0 = 40;
const pieAreaY0 = titleY + 60;
const pieAreaX1 = width - legendW;
const pieAreaY1 = height - 60;
const radius =
  (Math.min(pieAreaX1 - pieAreaX0, pieAreaY1 - pieAreaY0) / 2) * 0.82;
const cx = (pieAreaX0 + pieAreaX1) / 2;
const cy = (pieAreaY0 + pieAreaY1) / 2;

// --- Colors — Imprint palette positions 1..N in canonical order --------------
const color = d3
  .scaleOrdinal()
  .domain(data.map((d) => d.category))
  .range(t.palette);

// --- Pie + arc generators ----------------------------------------------------
const pieGen = d3
  .pie()
  .value((d) => d.value)
  .sort(null);
const arcs = pieGen(data);
const arc = d3.arc().innerRadius(0).outerRadius(radius);
const labelArc = d3
  .arc()
  .innerRadius(radius * 0.62)
  .outerRadius(radius * 0.62);

// Slightly explode the largest slice for emphasis (per spec)
const maxIdx = d3.maxIndex(data, (d) => d.value);
const explodeR = 36;
function offset(a) {
  if (a.index !== maxIdx) return [0, 0];
  const mid = (a.startAngle + a.endAngle) / 2 - Math.PI / 2;
  return [Math.cos(mid) * explodeR, Math.sin(mid) * explodeR];
}

const g = svg.append("g").attr("transform", `translate(${cx},${cy})`);

// --- Slices ------------------------------------------------------------------
g.selectAll("path.slice")
  .data(arcs)
  .join("path")
  .attr("class", "slice")
  .attr("transform", (a) => {
    const [ox, oy] = offset(a);
    return `translate(${ox},${oy})`;
  })
  .attr("d", arc)
  .attr("fill", (a) => color(a.data.category))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 3);

// --- Percentage labels inside slices -----------------------------------------
g.selectAll("text.pct")
  .data(arcs)
  .join("text")
  .attr("class", "pct")
  .attr("transform", (a) => {
    const [ox, oy] = offset(a);
    const [lx, ly] = labelArc.centroid(a);
    return `translate(${lx + ox},${ly + oy})`;
  })
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "central")
  // Always-light label on saturated slices: dark theme's near-black `pageBg`
  // tanks contrast on the matte-red and blue slots. The Imprint cream reads
  // cleanly against every palette member in either theme.
  .attr("fill", "#FAF8F1")
  .style("font-size", "30px")
  .style("font-weight", "600")
  .text((a) => `${Math.round((a.data.value / total) * 100)}%`);

// --- Title -------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", titleY)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "34px")
  .style("font-weight", "600")
  .text("pie-basic · javascript · d3 · anyplot.ai");

// --- Legend ------------------------------------------------------------------
const legendX = width - legendW + 20;
const rowH = 56;
const legendH = data.length * rowH;
const legendY0 = (height - legendH) / 2;
const legend = svg
  .append("g")
  .attr("transform", `translate(${legendX},${legendY0})`);
const item = legend
  .selectAll("g.item")
  .data(data)
  .join("g")
  .attr("class", "item")
  .attr("transform", (_d, i) => `translate(0,${i * rowH})`);
item
  .append("rect")
  .attr("width", 28)
  .attr("height", 28)
  .attr("rx", 6)
  .attr("fill", (d) => color(d.category));
item
  .append("text")
  .attr("x", 46)
  .attr("y", 14)
  .attr("dominant-baseline", "central")
  .attr("fill", t.ink)
  .style("font-size", "24px")
  .text((d) => d.category);
