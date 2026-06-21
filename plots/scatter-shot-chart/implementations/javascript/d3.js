// anyplot.ai
// scatter-shot-chart: Basketball Shot Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-21
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const THEME = window.ANYPLOT_THEME;
const { width, height } = window.ANYPLOT_SIZE;

// Imprint palette: made = brand green (pos 1), missed = matte red (semantic anchor for loss/error)
const COLOR_MADE   = t.palette[0];  // #009E73
const COLOR_MISSED = t.palette[4];  // #AE3030

// Deterministic LCG — browser has no seeded Math.random
function makeLcg(seed) {
  let s = seed >>> 0;
  return () => { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; };
}
const rng = makeLcg(42);

function bm() {
  const u1 = Math.max(rng(), 1e-9), u2 = rng();
  const r = Math.sqrt(-2 * Math.log(u1));
  return [r * Math.cos(2 * Math.PI * u2), r * Math.sin(2 * Math.PI * u2)];
}

// Shot clusters [cx, cy, spreadX, spreadY, madeRate, weight]
// Coordinates: x = horizontal from court center, y = distance from baseline (ft)
// Basket at (0, 5.25)
const CLUSTERS = [
  [0,    5.5,  1.8, 1.5, 0.62, 0.12],  // at-rim
  [0,   16.0,  2.0, 1.5, 0.38, 0.07],  // mid-range top
  [-7,  13.0,  2.5, 2.0, 0.37, 0.07],  // left mid
  [7,   13.0,  2.5, 2.0, 0.37, 0.07],  // right mid
  [-21,  6.5,  1.5, 2.5, 0.38, 0.09],  // left corner 3
  [21,   6.5,  1.5, 2.5, 0.38, 0.09],  // right corner 3
  [-18, 18.0,  2.5, 2.5, 0.34, 0.10],  // left wing 3
  [18,  18.0,  2.5, 2.5, 0.34, 0.10],  // right wing 3
  [0,   28.0,  2.5, 1.5, 0.35, 0.10],  // top of 3-point arc
  [-12, 23.0,  2.5, 2.0, 0.33, 0.10],  // left 3
  [12,  23.0,  2.5, 2.0, 0.33, 0.10],  // right 3
  [0,    9.5,  3.5, 2.5, 0.40, 0.09],  // paint
];
const W_SUM = CLUSTERS.reduce((a, c) => a + c[5], 0);

const shots = [];
for (let i = 0; i < 420; i++) {
  let pick = rng() * W_SUM, ci = 0, acc = 0;
  for (let j = 0; j < CLUSTERS.length; j++) {
    acc += CLUSTERS[j][5];
    if (pick <= acc) { ci = j; break; }
  }
  const [cx, cy, spx, spy, madeRate] = CLUSTERS[ci];
  const [z0, z1] = bm();
  const sx = cx + spx * z0;
  const sy = cy + spy * z1;
  if (sx < -25 || sx > 25 || sy < 0 || sy > 47) continue;
  shots.push({ x: sx, y: sy, made: rng() < madeRate });
}

// Layout
const margin = { top: 80, right: 50, bottom: 30, left: 50 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

const BKST_X = 0, BKST_Y = 5.25;  // basket center in ft from baseline

const xSc = d3.scaleLinear().domain([-25, 25]).range([0, iw]);
const ySc = d3.scaleLinear().domain([0, 47]).range([ih, 0]);

const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);

const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// Subtle court floor color
const floorColor = THEME === "dark" ? "#3A2B12" : "#D4B483";
g.append("rect")
  .attr("x", 0).attr("y", 0)
  .attr("width", iw).attr("height", ih)
  .attr("fill", floorColor).attr("fill-opacity", 0.18);

// Arc helper: math-coord angles; ySc handles the y-axis flip
function aPath(cx, cy, r, a0, a1, steps = 80) {
  return Array.from({ length: steps + 1 }, (_, i) => {
    const a = a0 + (a1 - a0) * i / steps;
    return `${i ? "L" : "M"}${xSc(cx + r * Math.cos(a)).toFixed(1)},${ySc(cy + r * Math.sin(a)).toFixed(1)}`;
  }).join("");
}

const LC = t.inkSoft;  // court line color
const LW = 2;

function cLine(x1, y1, x2, y2) {
  g.append("line")
    .attr("x1", xSc(x1)).attr("y1", ySc(y1))
    .attr("x2", xSc(x2)).attr("y2", ySc(y2))
    .attr("stroke", LC).attr("stroke-width", LW);
}

// Court boundary
cLine(-25, 0, 25, 0);        // baseline
cLine(-25, 0, -25, 47);      // left sideline
cLine(25, 0, 25, 47);        // right sideline
cLine(-25, 47, 25, 47);      // half-court line

// Half-court circle (6 ft radius — bottom semicircle visible from this end)
g.append("path").attr("d", aPath(0, 47, 6, 0, -Math.PI))
  .attr("fill", "none").attr("stroke", LC).attr("stroke-width", LW);

// Paint / key (16 ft wide, free-throw line at y=19)
cLine(-8, 0, -8, 19);
cLine(8, 0, 8, 19);
cLine(-8, 19, 8, 19);

// Free-throw circle (6 ft radius, center at basket_x=0, y=19)
// Upper arc solid (toward half court), lower arc dashed (inside paint)
g.append("path").attr("d", aPath(0, 19, 6, Math.PI, 0))
  .attr("fill", "none").attr("stroke", LC).attr("stroke-width", LW);
g.append("path").attr("d", aPath(0, 19, 6, 0, -Math.PI))
  .attr("fill", "none").attr("stroke", LC).attr("stroke-width", LW)
  .attr("stroke-dasharray", "7,5");

// Backboard and basket
cLine(-3, 4, 3, 4);
g.append("circle")
  .attr("cx", xSc(BKST_X)).attr("cy", ySc(BKST_Y))
  .attr("r", xSc(BKST_X + 0.75) - xSc(BKST_X))
  .attr("fill", "none").attr("stroke", LC).attr("stroke-width", 2.5);

// Restricted area (4 ft radius, upper semicircle)
g.append("path").attr("d", aPath(BKST_X, BKST_Y, 4, Math.PI, 0))
  .attr("fill", "none").attr("stroke", LC).attr("stroke-width", LW);

// Three-point line: straight segments + arc (23.75 ft from basket)
cLine(-22, 0, -22, 14);
cLine(22, 0, 22, 14);
g.append("path")
  .attr("d", aPath(
    BKST_X, BKST_Y, 23.75,
    Math.atan2(14 - BKST_Y, -22 - BKST_X),  // left endpoint angle
    Math.atan2(14 - BKST_Y,  22 - BKST_X),  // right endpoint angle (arc goes through top)
  ))
  .attr("fill", "none").attr("stroke", LC).attr("stroke-width", LW);

// Shot markers — missed first so made renders on top
const madeArr   = shots.filter(d =>  d.made);
const missedArr = shots.filter(d => !d.made);

g.selectAll(".miss").data(missedArr).join("circle")
  .attr("cx", d => xSc(d.x)).attr("cy", d => ySc(d.y))
  .attr("r", 5)
  .attr("fill", COLOR_MISSED).attr("fill-opacity", 0.65)
  .attr("stroke", t.pageBg).attr("stroke-width", 0.8);

g.selectAll(".make").data(madeArr).join("circle")
  .attr("cx", d => xSc(d.x)).attr("cy", d => ySc(d.y))
  .attr("r", 5)
  .attr("fill", COLOR_MADE).attr("fill-opacity", 0.85)
  .attr("stroke", t.pageBg).attr("stroke-width", 0.8);

// Legend
const lgData = [
  { label: `Made (${madeArr.length})`,     color: COLOR_MADE },
  { label: `Missed (${missedArr.length})`, color: COLOR_MISSED },
];
const lgX = 16, lgY = 14;
g.append("rect")
  .attr("x", lgX - 10).attr("y", lgY - 12)
  .attr("width", 182).attr("height", 76)
  .attr("fill", t.elevatedBg).attr("rx", 6).attr("fill-opacity", 0.90)
  .attr("stroke", t.grid).attr("stroke-width", 1);
lgData.forEach((d, i) => {
  g.append("circle")
    .attr("cx", lgX + 6).attr("cy", lgY + 8 + i * 30)
    .attr("r", 7).attr("fill", d.color)
    .attr("stroke", t.pageBg).attr("stroke-width", 1);
  g.append("text")
    .attr("x", lgX + 22).attr("y", lgY + 13 + i * 30)
    .attr("fill", t.inkSoft).style("font-size", "16px")
    .text(d.label);
});

// Title
svg.append("text")
  .attr("x", width / 2).attr("y", 48)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px").style("font-weight", "600")
  .text("scatter-shot-chart · javascript · d3 · anyplot.ai");
