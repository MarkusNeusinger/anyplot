// anyplot.ai
// feynman-basic: Feynman Diagram for Particle Interactions
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-03

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Imprint palette — data colors identical across themes
const FERMION = t.palette[0];  // #009E73 — brand green, fermion lines
const PHOTON  = t.palette[1];  // #C475FD — lavender, virtual photon

// Process: e⁻ e⁺ → γ* → μ⁻ μ⁺  (QED tree-level annihilation)
const v1 = { x: width * 0.35, y: height * 0.50 };  // left vertex (annihilation)
const v2 = { x: width * 0.65, y: height * 0.50 };  // right vertex (production)

const legs = {
  eMinus:  { x: width * 0.125, y: height * 0.30 },
  ePlus:   { x: width * 0.125, y: height * 0.70 },
  muMinus: { x: width * 0.875, y: height * 0.30 },
  muPlus:  { x: width * 0.875, y: height * 0.70 },
};

// Wavy path for photon propagator — parametric sine wave along a line
function wavyPath(x1, y1, x2, y2, waves, amp) {
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.sqrt(dx * dx + dy * dy);
  const cx = dx / len, cy = dy / len;
  const n = waves * 24;
  const pts = Array.from({ length: n + 1 }, (_, i) => {
    const u = i / n;
    const a = u * len;
    const p = amp * Math.sin(u * waves * 2 * Math.PI);
    return [x1 + a * cx - p * cy, y1 + a * cy + p * cx];
  });
  return d3.line()(pts);
}

const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);

const defs = svg.append("defs");

// Arrow marker for fermion direction (userSpaceOnUse keeps size fixed)
defs.append("marker")
  .attr("id", "fermion-arrow")
  .attr("markerWidth", 14).attr("markerHeight", 10)
  .attr("refX", 14).attr("refY", 5)
  .attr("orient", "auto")
  .attr("markerUnits", "userSpaceOnUse")
  .append("polygon")
  .attr("points", "0 0, 14 5, 0 10")
  .attr("fill", FERMION);

// Arrow for time axis
defs.append("marker")
  .attr("id", "time-arrow")
  .attr("markerWidth", 10).attr("markerHeight", 7)
  .attr("refX", 10).attr("refY", 3.5)
  .attr("orient", "auto")
  .attr("markerUnits", "userSpaceOnUse")
  .append("polygon")
  .attr("points", "0 0, 10 3.5, 0 7")
  .attr("fill", t.inkSoft);

const SW = 3.5;

// Fermion line with directional arrow at midpoint.
// Path direction encodes physics convention:
//   particles: endpoint→vertex (forward in time)
//   antiparticles: vertex→endpoint (backward in time)
function fermionLine(ax, ay, bx, by) {
  const mx = (ax + bx) / 2, my = (ay + by) / 2;
  svg.append("line")
    .attr("x1", ax).attr("y1", ay).attr("x2", mx).attr("y2", my)
    .attr("stroke", FERMION).attr("stroke-width", SW)
    .attr("marker-end", "url(#fermion-arrow)");
  svg.append("line")
    .attr("x1", mx).attr("y1", my).attr("x2", bx).attr("y2", by)
    .attr("stroke", FERMION).attr("stroke-width", SW);
}

// e⁻: particle — arrow points toward vertex (left → right)
fermionLine(legs.eMinus.x, legs.eMinus.y, v1.x, v1.y);
// e⁺: antiparticle — arrow points away from vertex (right → left)
fermionLine(v1.x, v1.y, legs.ePlus.x, legs.ePlus.y);
// μ⁻: particle — arrow points away from vertex (left → right)
fermionLine(v2.x, v2.y, legs.muMinus.x, legs.muMinus.y);
// μ⁺: antiparticle — arrow points toward vertex (right → left)
fermionLine(legs.muPlus.x, legs.muPlus.y, v2.x, v2.y);

// Virtual photon propagator (wavy line, v1 → v2)
svg.append("path")
  .attr("d", wavyPath(v1.x, v1.y, v2.x, v2.y, 7, 15))
  .attr("stroke", PHOTON).attr("stroke-width", SW).attr("fill", "none");

// Interaction vertex dots
[v1, v2].forEach(v => {
  svg.append("circle")
    .attr("cx", v.x).attr("cy", v.y).attr("r", 7)
    .attr("fill", t.ink);
});

// Particle labels at external legs
[
  { pt: legs.eMinus,  text: "e⁻", anchor: "end",   dx: -20, dy: -10 },
  { pt: legs.ePlus,   text: "e⁺", anchor: "end",   dx: -20, dy:  18 },
  { pt: legs.muMinus, text: "μ⁻", anchor: "start", dx: 20, dy: -10 },
  { pt: legs.muPlus,  text: "μ⁺", anchor: "start", dx: 20, dy:  18 },
].forEach(({ pt, text, anchor, dx, dy }) => {
  svg.append("text")
    .attr("x", pt.x + dx).attr("y", pt.y + dy)
    .attr("text-anchor", anchor)
    .attr("fill", FERMION)
    .style("font-size", "22px").style("font-weight", "700")
    .text(text);
});

// Virtual photon label above the propagator
svg.append("text")
  .attr("x", (v1.x + v2.x) / 2).attr("y", height * 0.50 - 30)
  .attr("text-anchor", "middle")
  .attr("fill", PHOTON)
  .style("font-size", "22px").style("font-weight", "700")
  .text("γ*");

// Time axis arrow at bottom
const timeY = height * 0.88;
svg.append("line")
  .attr("x1", width * 0.18).attr("y1", timeY)
  .attr("x2", width * 0.82).attr("y2", timeY)
  .attr("stroke", t.inkSoft).attr("stroke-width", 1.5)
  .attr("marker-end", "url(#time-arrow)");

svg.append("text")
  .attr("x", width * 0.82 + 14).attr("y", timeY + 5)
  .attr("fill", t.inkSoft).style("font-size", "15px")
  .text("time");

// Legend (top-right)
const legX = width * 0.77, legY = height * 0.14;

svg.append("line")
  .attr("x1", legX).attr("y1", legY)
  .attr("x2", legX + 30).attr("y2", legY)
  .attr("stroke", FERMION).attr("stroke-width", 3)
  .attr("marker-end", "url(#fermion-arrow)");
svg.append("line")
  .attr("x1", legX + 30).attr("y1", legY)
  .attr("x2", legX + 60).attr("y2", legY)
  .attr("stroke", FERMION).attr("stroke-width", 3);
svg.append("text")
  .attr("x", legX + 70).attr("y", legY + 5)
  .attr("fill", t.inkSoft).style("font-size", "15px")
  .text("Fermion");

svg.append("path")
  .attr("d", wavyPath(legX, legY + 36, legX + 60, legY + 36, 3, 8))
  .attr("stroke", PHOTON).attr("stroke-width", 3).attr("fill", "none");
svg.append("text")
  .attr("x", legX + 70).attr("y", legY + 36 + 5)
  .attr("fill", t.inkSoft).style("font-size", "15px")
  .text("Photon (γ)");

// Title
svg.append("text")
  .attr("x", width / 2).attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px").style("font-weight", "600")
  .text("feynman-basic · javascript · d3 · anyplot.ai");

// Process subtitle
svg.append("text")
  .attr("x", width / 2).attr("y", 72)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft).style("font-size", "16px")
  .text("Electron-Positron Annihilation  ·  e⁻ e⁺ → γ* → μ⁻ μ⁺");
