// anyplot.ai
// heatmap-calendar: Basic Calendar Heatmap
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: 86/100 | Created: 2026-07-23

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Tiny fixed-seed LCG (no seeded RNG in the browser) --------------------
let seed = 42;
const rand = () => {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
};

// --- Data: daily step count (thousands) for 2025, with a handful of gaps ---
// where the tracker wasn't worn — a realistic "missing data" scenario.
const YEAR = 2025;
const DAY_COUNT = 365;

const isMissing = (date) => {
  const m = date.getMonth();
  const d = date.getDate();
  return (m === 3 && d >= 14 && d <= 20) || (m === 0 && d === 15) || (m === 8 && d === 7) || (m === 10 && d === 11);
};

const days = [];
for (let i = 0; i < DAY_COUNT; i++) {
  const date = new Date(YEAR, 0, 1 + i);
  const dayOfYear = i;
  const dow = date.getDay(); // 0=Sun..6=Sat
  const isWeekend = dow === 0 || dow === 6;

  const seasonal = 1.7 * Math.sin((2 * Math.PI * (dayOfYear - 105)) / 365);
  const weekdayAdj = isWeekend ? -0.6 : 1.1;
  const noiseAmp = isWeekend ? 4.2 : 3.0;
  const noise = (rand() - 0.5) * noiseAmp;
  const value = Math.max(0.6, 7.0 + seasonal + weekdayAdj + noise);

  days.push({
    date,
    row: (dow + 6) % 7, // 0=Mon .. 6=Sun
    value: isMissing(date) ? null : Math.round(value * 10) / 10,
  });
}

const firstRow = days[0].row;
days.forEach((d, i) => {
  d.col = Math.floor((i + firstRow) / 7);
});
const numWeeks = days[days.length - 1].col + 1;

const values = days.map((d) => d.value).filter((v) => v !== null);
const [minVal, maxVal] = d3.extent(values);

// --- Layout -------------------------------------------------------------
const margin = { left: 86, right: 46 };
const iw = width - margin.left - margin.right;
const step = iw / numWeeks;
const cellSize = step * 0.78;

const titleY = 64;
const subtitleY = 104;
const monthLabelY = subtitleY + 76;
const gridTop = monthLabelY + 22;
const gridHeight = 7 * step;
const gridBottom = gridTop + gridHeight;

// --- SVG mount ------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Sequential color scale: Imprint seq (brand green → blue) -------------
const colorScale = d3.scaleSequential(d3.interpolateRgbBasis(t.seq)).domain([minVal, maxVal]);

// --- Calendar grid ----------------------------------------------------------
const g = svg.append("g").attr("transform", `translate(${margin.left},${gridTop})`);

g.selectAll(".cell")
  .data(days)
  .join("rect")
  .attr("class", "cell")
  .attr("x", (d) => d.col * step)
  .attr("y", (d) => d.row * step)
  .attr("width", cellSize)
  .attr("height", cellSize)
  .attr("rx", 3)
  .attr("fill", (d) => (d.value === null ? t.elevatedBg : colorScale(d.value)))
  .attr("stroke", (d) => (d.value === null ? t.grid : "none"))
  .attr("stroke-width", (d) => (d.value === null ? 1.2 : 0))
  .attr("stroke-dasharray", (d) => (d.value === null ? "3,3" : null));

// --- Weekday labels (y-axis, Mon..Sun) ---------------------------------
const weekdayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
g.selectAll(".weekday-label")
  .data(weekdayNames)
  .join("text")
  .attr("class", "weekday-label")
  .attr("x", -14)
  .attr("y", (d, i) => i * step + cellSize / 2)
  .attr("text-anchor", "end")
  .attr("dominant-baseline", "central")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text((d) => d);

// --- Month labels (above the grid) --------------------------------------
const monthNames = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const monthStarts = monthNames.map((name, m) => {
  const first = days.find((d) => d.date.getMonth() === m && d.date.getDate() === 1);
  return { name, col: first.col };
});

svg
  .selectAll(".month-label")
  .data(monthStarts)
  .join("text")
  .attr("class", "month-label")
  .attr("x", (d) => margin.left + d.col * step)
  .attr("y", monthLabelY)
  .attr("text-anchor", "start")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .style("font-weight", "500")
  .text((d) => d.name);

// --- Legend: "no data" swatch + sequential gradient bar --------------------
const legendY = gridBottom + 66;
const swatchSize = 24;

svg
  .append("rect")
  .attr("x", margin.left)
  .attr("y", legendY)
  .attr("width", swatchSize)
  .attr("height", swatchSize)
  .attr("rx", 3)
  .attr("fill", t.elevatedBg)
  .attr("stroke", t.grid)
  .attr("stroke-width", 1.2)
  .attr("stroke-dasharray", "3,3");

svg
  .append("text")
  .attr("x", margin.left + swatchSize + 10)
  .attr("y", legendY + swatchSize / 2)
  .attr("dominant-baseline", "central")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text("No data");

const barW = 280;
const barH = swatchSize;
const barX = margin.left + iw - barW;

const defs = svg.append("defs");
const grad = defs
  .append("linearGradient")
  .attr("id", "calendar-seq")
  .attr("x1", "0%")
  .attr("y1", "0%")
  .attr("x2", "100%")
  .attr("y2", "0%");
[0, 25, 50, 75, 100].forEach((p) => {
  grad.append("stop").attr("offset", `${p}%`).attr("stop-color", colorScale(minVal + (p / 100) * (maxVal - minVal)));
});

svg
  .append("rect")
  .attr("x", barX)
  .attr("y", legendY)
  .attr("width", barW)
  .attr("height", barH)
  .attr("rx", 3)
  .attr("fill", "url(#calendar-seq)");

svg
  .append("text")
  .attr("x", barX - 12)
  .attr("y", legendY + barH / 2)
  .attr("text-anchor", "end")
  .attr("dominant-baseline", "central")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text("Less");

svg
  .append("text")
  .attr("x", barX + barW + 12)
  .attr("y", legendY + barH / 2)
  .attr("text-anchor", "start")
  .attr("dominant-baseline", "central")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text("More");

// --- Title & subtitle -------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", titleY)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "26px")
  .style("font-weight", "600")
  .text("heatmap-calendar · javascript · d3 · anyplot.ai");

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", subtitleY)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "17px")
  .style("font-weight", "500")
  .text("Daily step count (thousands) · 2025");
