// anyplot.ai
// feynman-basic: Feynman Diagram for Particle Interactions
// Library: d3 7.9.0 | JavaScript 22.22.3
// Quality: 92/100 | Created: 2026-06-03

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Imprint palette — data colors identical across themes
const FERMION = t.palette[0];  // #009E73 green    — all fermion/quark lines
const PHOTON  = t.palette[1];  // #C475FD lavender — photon propagator
const GLUON   = t.palette[2];  // #4467A3 blue     — gluon propagator
const BOSON   = t.palette[3];  // #BD8233 ochre    — scalar boson (Higgs)

// Wavy line for photon propagator — sine wave perpendicular to path
function wavyPath(x1, y1, x2, y2, waves, amp) {
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.sqrt(dx * dx + dy * dy);
  const cx = dx / len, cy = dy / len;
  const n = waves * 24;
  return d3.line()(Array.from({ length: n + 1 }, (_, i) => {
    const u = i / n;
    const p = amp * Math.sin(u * waves * 2 * Math.PI);
    return [x1 + u * len * cx - p * cy, y1 + u * len * cy + p * cx];
  }));
}

// Looped curly path for gluon — cycloidal arches perpendicular to path
function gluonPath(x1, y1, x2, y2, nLoops, radius) {
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.sqrt(dx * dx + dy * dy);
  const cx = dx / len, cy = dy / len;
  const n = nLoops * 72;
  return d3.line()(Array.from({ length: n + 1 }, (_, i) => {
    const theta = (i / n) * nLoops * 2 * Math.PI;
    const along = (i / n) * len + radius * Math.sin(theta);
    const perp  = radius * (1 - Math.cos(theta)); // 0..2r, arches above the path
    return [x1 + along * cx + perp * cy, y1 + along * cy - perp * cx];
  }));
}

const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);
const defs = svg.append("defs");

// Arrow marker for fermion direction
defs.append("marker").attr("id", "arrow-f")
  .attr("markerWidth", 14).attr("markerHeight", 10)
  .attr("refX", 14).attr("refY", 5)
  .attr("orient", "auto").attr("markerUnits", "userSpaceOnUse")
  .append("polygon").attr("points", "0 0, 14 5, 0 10").attr("fill", FERMION);

// Arrow marker for time axis
defs.append("marker").attr("id", "arrow-t")
  .attr("markerWidth", 10).attr("markerHeight", 7)
  .attr("refX", 10).attr("refY", 3.5)
  .attr("orient", "auto").attr("markerUnits", "userSpaceOnUse")
  .append("polygon").attr("points", "0 0, 10 3.5, 0 7").attr("fill", t.inkSoft);

const SW = 3.5;

// Fermion line with directional arrow at midpoint.
// Particle flows a→b (forward in time); antiparticle: pass (vertex, leg) so arrow points away.
function fermionLine(ax, ay, bx, by) {
  const mx = (ax + bx) / 2, my = (ay + by) / 2;
  svg.append("line")
    .attr("x1", ax).attr("y1", ay).attr("x2", mx).attr("y2", my)
    .attr("stroke", FERMION).attr("stroke-width", SW)
    .attr("marker-end", "url(#arrow-f)");
  svg.append("line")
    .attr("x1", mx).attr("y1", my).attr("x2", bx).attr("y2", by)
    .attr("stroke", FERMION).attr("stroke-width", SW);
}

// ── LEFT PANEL: QED  e⁻ e⁺ → γ* → μ⁻ μ⁺ ──────────────────────────────

const v1x = width * 0.22, v1y = height * 0.50;
const v2x = width * 0.44, v2y = height * 0.50;

fermionLine(width * 0.05, height * 0.33, v1x, v1y);       // e⁻ → vertex
fermionLine(v1x, v1y, width * 0.05, height * 0.67);       // vertex → e⁺ (antiparticle)
fermionLine(v2x, v2y, width * 0.59, height * 0.33);       // vertex → μ⁻
fermionLine(width * 0.59, height * 0.67, v2x, v2y);       // μ⁺ → vertex (antiparticle)

// Virtual photon γ* (wavy)
svg.append("path")
  .attr("d", wavyPath(v1x, v1y, v2x, v2y, 7, 14))
  .attr("stroke", PHOTON).attr("stroke-width", SW).attr("fill", "none");

// Interaction vertex dots
svg.append("circle").attr("cx", v1x).attr("cy", v1y).attr("r", 7).attr("fill", t.ink);
svg.append("circle").attr("cx", v2x).attr("cy", v2y).attr("r", 7).attr("fill", t.ink);

// Particle labels at external legs
[
  [width * 0.05 - 16, height * 0.33 - 10, "e⁻", "end",    FERMION],
  [width * 0.05 - 16, height * 0.67 + 20, "e⁺", "end",    FERMION],
  [width * 0.59 + 16, height * 0.33 - 10, "μ⁻", "start",  FERMION],
  [width * 0.59 + 16, height * 0.67 + 20, "μ⁺", "start",  FERMION],
  [(v1x + v2x) / 2,   height * 0.50 - 28, "γ*", "middle", PHOTON],
].forEach(([x, y, text, anchor, color]) => {
  svg.append("text").attr("x", x).attr("y", y).attr("text-anchor", anchor)
    .attr("fill", color).style("font-size", "20px").style("font-weight", "700").text(text);
});

// QED section label
svg.append("text").attr("x", (v1x + v2x) / 2).attr("y", height * 0.14)
  .attr("text-anchor", "middle").attr("fill", t.inkSoft)
  .style("font-size", "15px").text("QED  ·  e⁻e⁺ → γ* → μ⁻μ⁺");

// Time axis
const tY = height * 0.87;
svg.append("line")
  .attr("x1", width * 0.05).attr("y1", tY)
  .attr("x2", width * 0.59).attr("y2", tY)
  .attr("stroke", t.inkSoft).attr("stroke-width", 1.5)
  .attr("marker-end", "url(#arrow-t)");
svg.append("text").attr("x", width * 0.59 + 14).attr("y", tY + 5)
  .attr("fill", t.inkSoft).style("font-size", "17px").text("time");

// ── VERTICAL PANEL DIVIDER ──────────────────────────────────────────────
svg.append("line")
  .attr("x1", width * 0.625).attr("y1", height * 0.10)
  .attr("x2", width * 0.625).attr("y2", height * 0.92)
  .attr("stroke", t.grid).attr("stroke-width", 1)
  .attr("stroke-dasharray", "6,4");

// ── RIGHT TOP: QCD  q q̄ → g ────────────────────────────────────────────

const vGx = width * 0.75, vGy = height * 0.30;

fermionLine(width * 0.65, height * 0.18, vGx, vGy);    // q → vertex
fermionLine(vGx, vGy, width * 0.65, height * 0.42);    // vertex → q̄ (antiparticle)

// Gluon propagator (curly)
svg.append("path")
  .attr("d", gluonPath(vGx, vGy, width * 0.95, height * 0.30, 6, 16))
  .attr("stroke", GLUON).attr("stroke-width", SW).attr("fill", "none");

svg.append("circle").attr("cx", vGx).attr("cy", vGy).attr("r", 7).attr("fill", t.ink);

[
  [width * 0.65 - 14, height * 0.18 - 10, "q",   "end",   FERMION],
  [width * 0.65 - 14, height * 0.42 + 20, "q̅", "end",   FERMION],
  [width * 0.95 + 14, height * 0.30 +  4, "g",   "start", GLUON],
].forEach(([x, y, text, anchor, color]) => {
  svg.append("text").attr("x", x).attr("y", y).attr("text-anchor", anchor)
    .attr("fill", color).style("font-size", "20px").style("font-weight", "700").text(text);
});

svg.append("text").attr("x", width * 0.80).attr("y", height * 0.12)
  .attr("text-anchor", "middle").attr("fill", t.inkSoft)
  .style("font-size", "15px").text("QCD  ·  q q̅ → g");

// ── HORIZONTAL DIVIDER (right panel) ────────────────────────────────────
svg.append("line")
  .attr("x1", width * 0.64).attr("y1", height * 0.50)
  .attr("x2", width * 0.97).attr("y2", height * 0.50)
  .attr("stroke", t.grid).attr("stroke-width", 1)
  .attr("stroke-dasharray", "4,4");

// ── RIGHT BOTTOM: Higgs  q q̄ → H ────────────────────────────────────────

const vHx = width * 0.75, vHy = height * 0.70;

fermionLine(width * 0.65, height * 0.58, vHx, vHy);    // q → vertex
fermionLine(vHx, vHy, width * 0.65, height * 0.82);    // vertex → q̄ (antiparticle)

// Scalar Higgs propagator (dashed straight line)
svg.append("line")
  .attr("x1", vHx).attr("y1", vHy)
  .attr("x2", width * 0.95).attr("y2", height * 0.70)
  .attr("stroke", BOSON).attr("stroke-width", SW)
  .attr("stroke-dasharray", "14,8");

svg.append("circle").attr("cx", vHx).attr("cy", vHy).attr("r", 7).attr("fill", t.ink);

[
  [width * 0.65 - 14, height * 0.58 - 10, "q",   "end",   FERMION],
  [width * 0.65 - 14, height * 0.82 + 20, "q̅", "end",   FERMION],
  [width * 0.95 + 14, height * 0.70 +  4, "H",   "start", BOSON],
].forEach(([x, y, text, anchor, color]) => {
  svg.append("text").attr("x", x).attr("y", y).attr("text-anchor", anchor)
    .attr("fill", color).style("font-size", "20px").style("font-weight", "700").text(text);
});

svg.append("text").attr("x", width * 0.80).attr("y", height * 0.54)
  .attr("text-anchor", "middle").attr("fill", t.inkSoft)
  .style("font-size", "15px").text("Higgs  ·  q q̅ → H");

// ── LEGEND — all four line types ────────────────────────────────────────
const lY = height * 0.93;
[
  { x: width * 0.07,  color: FERMION, type: "fermion", text: "Fermion" },
  { x: width * 0.27,  color: PHOTON,  type: "wavy",    text: "Photon (γ)" },
  { x: width * 0.47,  color: GLUON,   type: "gluon",   text: "Gluon (g)" },
  { x: width * 0.67,  color: BOSON,   type: "dashed",  text: "Scalar Boson (H)" },
].forEach(({ x, color, type, text }) => {
  const x2 = x + 60;
  if (type === "fermion") {
    const mx = (x + x2) / 2;
    svg.append("line").attr("x1", x).attr("y1", lY).attr("x2", mx).attr("y2", lY)
      .attr("stroke", color).attr("stroke-width", 3).attr("marker-end", "url(#arrow-f)");
    svg.append("line").attr("x1", mx).attr("y1", lY).attr("x2", x2).attr("y2", lY)
      .attr("stroke", color).attr("stroke-width", 3);
  } else if (type === "wavy") {
    svg.append("path").attr("d", wavyPath(x, lY, x2, lY, 3, 7))
      .attr("stroke", color).attr("stroke-width", 3).attr("fill", "none");
  } else if (type === "gluon") {
    svg.append("path").attr("d", gluonPath(x, lY, x2, lY, 3, 9))
      .attr("stroke", color).attr("stroke-width", 3).attr("fill", "none");
  } else {
    svg.append("line").attr("x1", x).attr("y1", lY).attr("x2", x2).attr("y2", lY)
      .attr("stroke", color).attr("stroke-width", 3).attr("stroke-dasharray", "10,6");
  }
  svg.append("text").attr("x", x2 + 12).attr("y", lY + 5)
    .attr("fill", t.inkSoft).style("font-size", "17px").text(text);
});

// ── TITLE & SUBTITLE ────────────────────────────────────────────────────
svg.append("text").attr("x", width / 2).attr("y", 44)
  .attr("text-anchor", "middle").attr("fill", t.ink)
  .style("font-size", "22px").style("font-weight", "600")
  .text("feynman-basic · javascript · d3 · anyplot.ai");

svg.append("text").attr("x", width / 2).attr("y", 74)
  .attr("text-anchor", "middle").attr("fill", t.inkSoft).style("font-size", "16px")
  .text("QED & QCD Feynman Diagrams  ·  All Four Particle Types");
