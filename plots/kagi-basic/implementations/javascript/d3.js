// anyplot.ai
// kagi-basic: Basic Kagi Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 100, right: 80, bottom: 90, left: 110 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: deterministic daily closes (mulberry32 PRNG, fixed seed) --------
function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let x = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(20260108);

const numDays = 260;
const regimeDrift = [0.0012, -0.001, 0.002, -0.0016, 0.0008]; // rotating trend legs
const closes = [84];
for (let i = 1; i < numDays; i++) {
  const regime = regimeDrift[Math.floor(i / 44) % regimeDrift.length];
  const shock = (rand() - 0.5) * 0.05;
  closes.push(Math.max(20, closes[i - 1] * (1 + regime + shock)));
}

// --- Kagi construction: reversal-threshold zigzag over the close series ----
const REVERSAL_PCT = 0.04;

function buildKagiPivots(prices, reversalPct) {
  const pivots = [prices[0]];
  let direction = 0; // 0 = undecided, 1 = up-tracking, -1 = down-tracking
  let extreme = prices[0];

  for (let i = 1; i < prices.length; i++) {
    const p = prices[i];
    if (direction === 0) {
      // Undecided: wait for the first breakout from the starting anchor.
      if (p >= prices[0] * (1 + reversalPct)) {
        direction = 1;
        extreme = p;
      } else if (p <= prices[0] * (1 - reversalPct)) {
        direction = -1;
        extreme = p;
      }
      continue;
    }
    if (direction === 1) {
      if (p > extreme) {
        extreme = p;
      } else if (p <= extreme * (1 - reversalPct)) {
        pivots.push(extreme);
        direction = -1;
        extreme = p;
      }
    } else {
      if (p < extreme) {
        extreme = p;
      } else if (p >= extreme * (1 + reversalPct)) {
        pivots.push(extreme);
        direction = 1;
        extreme = p;
      }
    }
  }
  pivots.push(extreme);
  return pivots;
}

const pivots = buildKagiPivots(closes, REVERSAL_PCT);

const verticals = [];
for (let i = 0; i < pivots.length - 1; i++) {
  verticals.push({
    x: i,
    y0: pivots[i],
    y1: pivots[i + 1],
    dir: pivots[i + 1] >= pivots[i] ? "up" : "down",
  });
}
const horizontals = [];
for (let i = 0; i < verticals.length - 1; i++) {
  horizontals.push({
    x0: i,
    x1: i + 1,
    y: verticals[i].y1,
    dir: verticals[i + 1].dir,
  });
}

// --- Scales -------------------------------------------------------------
const x = d3
  .scaleLinear()
  .domain([0, verticals.length - 1])
  .range([0, iw]);
const yExtent = d3.extent(pivots);
const y = d3
  .scaleLinear()
  .domain([yExtent[0] * 0.97, yExtent[1] * 1.03])
  .nice()
  .range([ih, 0]);

// --- SVG mount -------------------------------------------------------------
const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height);
const g = svg
  .append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// --- Kagi lines: thick/green for yang (up), thin/red for yin (down) --------
// Semantic exception (default-style-guide.md): profit/up -> green, loss/down -> red.
const THICK = 6;
const THIN = 2.5;
const upColor = t.palette[0]; // brand green
const downColor = t.palette[4]; // matte red

g.selectAll(".kagi-vertical")
  .data(verticals)
  .join("line")
  .attr("class", "kagi-vertical")
  .attr("x1", (d) => x(d.x))
  .attr("x2", (d) => x(d.x))
  .attr("y1", (d) => y(d.y0))
  .attr("y2", (d) => y(d.y1))
  .attr("stroke", (d) => (d.dir === "up" ? upColor : downColor))
  .attr("stroke-width", (d) => (d.dir === "up" ? THICK : THIN))
  .attr("stroke-linecap", "round");

g.selectAll(".kagi-horizontal")
  .data(horizontals)
  .join("line")
  .attr("class", "kagi-horizontal")
  .attr("x1", (d) => x(d.x0))
  .attr("x2", (d) => x(d.x1))
  .attr("y1", (d) => y(d.y))
  .attr("y2", (d) => y(d.y))
  .attr("stroke", (d) => (d.dir === "up" ? upColor : downColor))
  .attr("stroke-width", (d) => (d.dir === "up" ? THICK : THIN))
  .attr("stroke-linecap", "round");

// --- Axes --------------------------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(10).tickFormat(d3.format("d")));
const yAxis = g
  .append("g")
  .call(d3.axisLeft(y).tickFormat((d) => `$${d3.format(",.0f")(d)}`));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  ax.selectAll("line").attr("stroke", t.grid);
  ax.select(".domain").attr("stroke", t.inkSoft);
}

// --- Axis labels -------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Kagi Line Index (4% Reversal Threshold)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -78)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Closing Price ($)");

// --- Legend --------------------------------------------------------------
const legendItems = [
  { label: "Yang (Up)", color: upColor, width: THICK },
  { label: "Yin (Down)", color: downColor, width: THIN },
];
const legend = svg
  .append("g")
  .attr("transform", `translate(${width - margin.right - 190}, 24)`);
legendItems.forEach((item, i) => {
  const row = legend.append("g").attr("transform", `translate(0, ${i * 28})`);
  row
    .append("line")
    .attr("x1", 0)
    .attr("x2", 32)
    .attr("y1", 0)
    .attr("y2", 0)
    .attr("stroke", item.color)
    .attr("stroke-width", item.width)
    .attr("stroke-linecap", "round");
  row
    .append("text")
    .attr("x", 42)
    .attr("y", 5)
    .attr("fill", t.inkSoft)
    .style("font-size", "14px")
    .text(item.label);
});

// --- Title -------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("kagi-basic · javascript · d3 · anyplot.ai");
