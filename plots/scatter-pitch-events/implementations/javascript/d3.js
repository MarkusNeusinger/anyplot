// anyplot.ai
// scatter-pitch-events: Soccer Pitch Event Map
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-21

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Deterministic LCG for reproducible data
let _s = 12345;
function rand() { _s = (_s * 1664525 + 1013904223) >>> 0; return _s / 4294967295; }
function rr(lo, hi) { return lo + rand() * (hi - lo); }

// Theme
const isDark = window.ANYPLOT_THEME === "dark";
const PITCH_BG       = isDark ? "#1e3a28" : "#3a7d44";
const PITCH_LINE_CLR = isDark ? "rgba(255,255,255,0.82)" : "rgba(255,255,255,0.92)";
const GOAL_BG        = isDark ? "#152b1e" : "#2d5e34";

// Event colors — Imprint palette positions 1–4
const EC = {
  pass:         t.palette[0], // #009E73
  shot:         t.palette[1], // #C475FD
  tackle:       t.palette[2], // #4467A3
  interception: t.palette[3], // #BD8233
};

// Data: 120 events (deterministic)
const events = [];

// 60 passes with end positions (arrows show direction)
for (let i = 0; i < 60; i++) {
  const x = rr(5, 95), y = rr(3, 65);
  const ang = rr(-0.65, 0.65);
  const dist = rr(8, 26);
  events.push({
    type: "pass", x, y,
    ex: Math.min(103, Math.max(2, x + Math.cos(ang) * dist)),
    ey: Math.min(66, Math.max(2, y + Math.sin(ang) * dist)),
    ok: rand() > 0.22,
  });
}

// 25 shots toward right goal (arrows point to goal mouth)
for (let i = 0; i < 25; i++) {
  const x = rr(60, 103), y = rr(14, 54);
  events.push({ type: "shot", x, y, ex: 105, ey: rr(29.5, 38.5), ok: rand() > 0.72 });
}

// 20 tackles (no arrows)
for (let i = 0; i < 20; i++) {
  events.push({ type: "tackle", x: rr(5, 100), y: rr(3, 65), ok: rand() > 0.4 });
}

// 15 interceptions (no arrows)
for (let i = 0; i < 15; i++) {
  events.push({ type: "interception", x: rr(5, 100), y: rr(3, 65), ok: rand() > 0.35 });
}

// Layout — maintain 105:68 pitch aspect ratio within the drawing area
const margin = { top: 70, right: 50, bottom: 100, left: 50 };
const drawW = width - margin.left - margin.right;
const drawH = height - margin.top - margin.bottom;

const PITCH_RATIO = 105 / 68;
let pitchW, pitchH;
if (drawW / drawH > PITCH_RATIO) {
  pitchH = drawH;
  pitchW = pitchH * PITCH_RATIO;
} else {
  pitchW = drawW;
  pitchH = pitchW / PITCH_RATIO;
}
const offX = (drawW - pitchW) / 2;
const offY = (drawH - pitchH) / 2;
const mPx  = pitchW / 105; // pixels per metre (same in x and y due to aspect ratio lock)

// Scales (pitch metres → SVG px within g)
const px = d3.scaleLinear().domain([0, 105]).range([0, pitchW]);
const py = d3.scaleLinear().domain([0, 68]).range([0, pitchH]);

// SVG root
const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);

const g = svg.append("g")
  .attr("transform", `translate(${margin.left + offX},${margin.top + offY})`);

// Pitch drawing helpers
function pline(x1, y1, x2, y2) {
  g.append("line")
    .attr("x1", px(x1)).attr("y1", py(y1)).attr("x2", px(x2)).attr("y2", py(y2))
    .attr("stroke", PITCH_LINE_CLR).attr("stroke-width", 1.5);
}
function prect(x, y, w, h, fill) {
  g.append("rect")
    .attr("x", px(x)).attr("y", py(y))
    .attr("width", px(x + w) - px(x)).attr("height", py(y + h) - py(y))
    .attr("fill", fill || "none").attr("stroke", PITCH_LINE_CLR).attr("stroke-width", 1.5);
}
function parc(x1, y1, x2, y2, r, sweep) {
  const rp = r * mPx;
  g.append("path")
    .attr("d", `M${px(x1)},${py(y1)} A${rp},${rp} 0 0,${sweep} ${px(x2)},${py(y2)}`)
    .attr("fill", "none").attr("stroke", PITCH_LINE_CLR).attr("stroke-width", 1.5);
}

// Pitch background
g.append("rect").attr("x", 0).attr("y", 0)
  .attr("width", pitchW).attr("height", pitchH).attr("fill", PITCH_BG);

// Goals — 7.32 m wide, 2.44 m deep; extend beyond pitch boundary
const gy1 = (68 - 7.32) / 2, gy2 = gy1 + 7.32;
g.append("path")
  .attr("d", `M${px(0)},${py(gy1)} L${px(-2.44)},${py(gy1)} L${px(-2.44)},${py(gy2)} L${px(0)},${py(gy2)}`)
  .attr("fill", GOAL_BG).attr("stroke", PITCH_LINE_CLR).attr("stroke-width", 2);
g.append("path")
  .attr("d", `M${px(105)},${py(gy1)} L${px(107.44)},${py(gy1)} L${px(107.44)},${py(gy2)} L${px(105)},${py(gy2)}`)
  .attr("fill", GOAL_BG).attr("stroke", PITCH_LINE_CLR).attr("stroke-width", 2);

// Pitch outline and halfway line
prect(0, 0, 105, 68);
pline(52.5, 0, 52.5, 68);

// Centre circle and spot
g.append("circle").attr("cx", px(52.5)).attr("cy", py(34)).attr("r", 9.15 * mPx)
  .attr("fill", "none").attr("stroke", PITCH_LINE_CLR).attr("stroke-width", 1.5);
g.append("circle").attr("cx", px(52.5)).attr("cy", py(34)).attr("r", 3.5)
  .attr("fill", PITCH_LINE_CLR);

// Penalty areas (FIFA: 16.5 m deep, 40.3 m wide; goal area: 5.5 m deep, 18.3 m wide)
prect(0, 13.85, 16.5, 40.3);
prect(0, 24.85, 5.5, 18.3);
prect(88.5, 13.85, 16.5, 40.3);
prect(99.5, 24.85, 5.5, 18.3);

// Penalty spots
g.append("circle").attr("cx", px(11)).attr("cy", py(34)).attr("r", 3).attr("fill", PITCH_LINE_CLR);
g.append("circle").attr("cx", px(94)).attr("cy", py(34)).attr("r", 3).attr("fill", PITCH_LINE_CLR);

// Penalty arcs (radius 9.15 m from spot, only the portion outside the penalty area)
const ady = Math.sqrt(9.15 * 9.15 - 5.5 * 5.5) * mPx;
const arR = 9.15 * mPx;
g.append("path")
  .attr("d", `M${px(16.5)},${py(34) - ady} A${arR},${arR} 0 0,1 ${px(16.5)},${py(34) + ady}`)
  .attr("fill", "none").attr("stroke", PITCH_LINE_CLR).attr("stroke-width", 1.5);
g.append("path")
  .attr("d", `M${px(88.5)},${py(34) - ady} A${arR},${arR} 0 0,0 ${px(88.5)},${py(34) + ady}`)
  .attr("fill", "none").attr("stroke", PITCH_LINE_CLR).attr("stroke-width", 1.5);

// Corner arcs (radius 1 m); sweep directions keep the arc inside the pitch
parc(1, 0, 0, 1, 1, 1);
parc(104, 0, 105, 1, 1, 0);
parc(0, 67, 1, 68, 1, 1);
parc(105, 67, 104, 68, 1, 0);

// Arrow marker definitions for passes and shots
const defs = svg.append("defs");
for (const tp of ["pass", "shot"]) {
  defs.append("marker").attr("id", `arr-${tp}`)
    .attr("viewBox", "0 -4 8 8").attr("refX", 7).attr("refY", 0)
    .attr("markerWidth", 5).attr("markerHeight", 5).attr("orient", "auto")
    .append("path").attr("d", "M0,-4L8,0L0,4Z")
    .attr("fill", EC[tp]).attr("opacity", 0.9);
}

// Arrow lines for passes and shots
g.selectAll(".ev-arr")
  .data(events.filter(e => e.type === "pass" || e.type === "shot"))
  .join("line").attr("class", "ev-arr")
  .attr("x1", d => px(d.x)).attr("y1", d => py(d.y))
  .attr("x2", d => px(d.ex)).attr("y2", d => py(d.ey))
  .attr("stroke", d => EC[d.type])
  .attr("stroke-width", d => d.type === "shot" ? 1.8 : 1.2)
  .attr("opacity", d => d.ok ? 0.6 : 0.25)
  .attr("marker-end", d => `url(#arr-${d.type})`);

// Marker shape path builders
function starP(cx, cy, r) {
  let d = "";
  for (let i = 0; i < 10; i++) {
    const a = i * Math.PI / 5 - Math.PI / 2;
    const rad = i % 2 === 0 ? r : r * 0.42;
    d += (i === 0 ? "M" : "L") + (cx + rad * Math.cos(a)) + "," + (cy + rad * Math.sin(a));
  }
  return d + "Z";
}
function triP(cx, cy, r) {
  return `M${cx},${cy - r}L${cx + r * 0.866},${cy + r * 0.5}L${cx - r * 0.866},${cy + r * 0.5}Z`;
}
function diaP(cx, cy, r) {
  return `M${cx},${cy - r}L${cx + r * 0.65},${cy}L${cx},${cy + r}L${cx - r * 0.65},${cy}Z`;
}

// Draw event markers — filled = successful, hollow = unsuccessful
const MR = mPx * 0.9;
for (const ev of events) {
  const cx = px(ev.x), cy = py(ev.y), col = EC[ev.type];
  let el;
  if (ev.type === "pass") {
    el = g.append("circle").attr("cx", cx).attr("cy", cy).attr("r", MR * 0.85);
  } else if (ev.type === "shot") {
    el = g.append("path").attr("d", starP(cx, cy, MR * 1.1));
  } else if (ev.type === "tackle") {
    el = g.append("path").attr("d", triP(cx, cy, MR * 1.05));
  } else {
    el = g.append("path").attr("d", diaP(cx, cy, MR * 1.1));
  }
  el.attr("fill", ev.ok ? col : "none")
    .attr("stroke", col).attr("stroke-width", 1.8)
    .attr("opacity", ev.ok ? 0.9 : 0.55);
}

// Legend — two rows centred under the pitch
const pitchLeft = margin.left + offX;
const pitchBot  = margin.top + offY + pitchH;
const pcX       = pitchLeft + pitchW / 2;
const lgY1      = pitchBot + 24;
const lgY2      = lgY1 + 30;
const LR        = 9;

const typeItems = [
  { label: "Pass",         tp: "pass",         shape: "circle" },
  { label: "Shot",         tp: "shot",          shape: "star" },
  { label: "Tackle",       tp: "tackle",        shape: "tri" },
  { label: "Interception", tp: "interception",  shape: "diam" },
];
const tSp = 185;
const tX0 = pcX - tSp * 1.5;

for (let i = 0; i < typeItems.length; i++) {
  const { label, tp, shape } = typeItems[i];
  const lx = tX0 + i * tSp, col = EC[tp];
  const lg = svg.append("g");
  if (shape === "circle") {
    lg.append("circle").attr("cx", lx).attr("cy", lgY1).attr("r", LR).attr("fill", col).attr("opacity", 0.9);
  } else if (shape === "star") {
    lg.append("path").attr("d", starP(lx, lgY1, LR)).attr("fill", col).attr("opacity", 0.9);
  } else if (shape === "tri") {
    lg.append("path").attr("d", triP(lx, lgY1, LR)).attr("fill", col).attr("opacity", 0.9);
  } else {
    lg.append("path").attr("d", diaP(lx, lgY1, LR)).attr("fill", col).attr("opacity", 0.9);
  }
  lg.append("text").attr("x", lx + LR + 7).attr("y", lgY1 + 5)
    .attr("fill", t.ink).style("font-size", "13px").text(label);
}

// Outcome row
const oSp = 220;
const oX0 = pcX - oSp / 2;
svg.append("circle").attr("cx", oX0).attr("cy", lgY2).attr("r", LR)
  .attr("fill", t.inkSoft).attr("opacity", 0.9);
svg.append("text").attr("x", oX0 + LR + 7).attr("y", lgY2 + 5)
  .attr("fill", t.ink).style("font-size", "13px").text("Successful (filled)");
svg.append("circle").attr("cx", oX0 + oSp).attr("cy", lgY2).attr("r", LR)
  .attr("fill", "none").attr("stroke", t.inkSoft).attr("stroke-width", 1.8).attr("opacity", 0.9);
svg.append("text").attr("x", oX0 + oSp + LR + 7).attr("y", lgY2 + 5)
  .attr("fill", t.ink).style("font-size", "13px").text("Unsuccessful (hollow)");

// Title
svg.append("text").attr("x", width / 2).attr("y", 46)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "22px").style("font-weight", "600")
  .text("scatter-pitch-events · javascript · d3 · anyplot.ai");
