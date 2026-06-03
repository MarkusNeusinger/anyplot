// anyplot.ai
// feynman-basic: Feynman Diagram for Particle Interactions
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-03

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// CSS mount: 1600 × 900 px at 2× DPR → 3200 × 1800 PNG
const W = 1600, H = 900;

// Imprint palette: fermions in brand green, photon in blue
const C_FERMION = t.palette[0];  // #009E73
const C_PHOTON  = t.palette[2];  // #4467A3

const LW = 5.5;  // line width (CSS px → ~11 source px)
const VR = 11;   // vertex dot radius

// Diagram: e⁻e⁺ annihilation → γ* → μ⁻μ⁺ pair production
const V1 = [530, 440];
const V2 = [1070, 440];
const E_IN   = [100, 185];
const P_IN   = [100, 695];
const MU_OUT = [1500, 185];
const AP_OUT = [1500, 695];

// Returns array of bezierCurve elements for a wavy photon line
function wavyBeziers(x1, y1, x2, y2, nWaves, amp, strokeColor, lineWidth) {
  var dx = x2 - x1, dy = y2 - y1;
  var len = Math.sqrt(dx * dx + dy * dy);
  var nx = -dy / len, ny = dx / len;
  var n = nWaves * 2;
  var elems = [];
  for (var i = 0; i < n; i++) {
    var t0 = i / n, t1 = (i + 1) / n, tm = (t0 + t1) / 2;
    var sign = (i % 2 === 0) ? 1 : -1;
    elems.push({
      type: "bezierCurve",
      shape: {
        x1: x1 + dx * t0, y1: y1 + dy * t0,
        cpx1: x1 + dx * tm + nx * amp * sign,
        cpy1: y1 + dy * tm + ny * amp * sign,
        x2: x1 + dx * t1, y2: y1 + dy * t1
      },
      style: { stroke: strokeColor, lineWidth: lineWidth, fill: "rgba(0,0,0,0)" }
    });
  }
  return elems;
}

// Triangle polygon points for arrowhead at (x2,y2) pointing from (x1,y1)→(x2,y2)
function arrowPoints(x1, y1, x2, y2, size) {
  var dx = x2 - x1, dy = y2 - y1;
  var len = Math.sqrt(dx * dx + dy * dy);
  var ux = dx / len, uy = dy / len;
  var px = -uy, py = ux;
  var bx = x2 - ux * size, by = y2 - uy * size;
  var w = size * 0.42;
  return [[x2, y2], [bx + px * w, by + py * w], [bx - px * w, by - py * w]];
}

// Interpolate between two points
function lerp(p, q, f) {
  return [p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f];
}

// Precompute arrowhead polygon points
// Particles flow forward in time; antiparticles have reversed arrows
var eA1 = lerp(E_IN, V1, 0.45), eA2 = lerp(E_IN, V1, 0.52);
var epA1 = lerp(P_IN, V1, 0.55), epA2 = lerp(P_IN, V1, 0.48);
var muA1 = lerp(V2, MU_OUT, 0.45), muA2 = lerp(V2, MU_OUT, 0.52);
var apA1 = lerp(V2, AP_OUT, 0.55), apA2 = lerp(V2, AP_OUT, 0.48);

var photonWaves = wavyBeziers(V1[0], V1[1], V2[0], V2[1], 7, 32, C_PHOTON, LW);
var legendWaves = wavyBeziers(350, H - 90, 425, H - 90, 3, 16, C_PHOTON, LW);

const chart = echarts.init(document.getElementById("container"));

var graphicElements = [
  // ── e⁻ incoming leg (solid, arrow toward V1) ─────────────────────────
  { type: "polyline",
    shape: { points: [[E_IN[0], E_IN[1]], [V1[0], V1[1]]] },
    style: { stroke: C_FERMION, lineWidth: LW, fill: "rgba(0,0,0,0)" } },
  { type: "polygon",
    shape: { points: arrowPoints(eA1[0], eA1[1], eA2[0], eA2[1], 24) },
    style: { fill: C_FERMION, stroke: "none" } },

  // ── e⁺ incoming leg (solid, arrow reversed — antiparticle) ───────────
  { type: "polyline",
    shape: { points: [[P_IN[0], P_IN[1]], [V1[0], V1[1]]] },
    style: { stroke: C_FERMION, lineWidth: LW, fill: "rgba(0,0,0,0)" } },
  { type: "polygon",
    shape: { points: arrowPoints(epA1[0], epA1[1], epA2[0], epA2[1], 24) },
    style: { fill: C_FERMION, stroke: "none" } },

  // ── μ⁻ outgoing leg (solid, arrow away from V2) ───────────────────────
  { type: "polyline",
    shape: { points: [[V2[0], V2[1]], [MU_OUT[0], MU_OUT[1]]] },
    style: { stroke: C_FERMION, lineWidth: LW, fill: "rgba(0,0,0,0)" } },
  { type: "polygon",
    shape: { points: arrowPoints(muA1[0], muA1[1], muA2[0], muA2[1], 24) },
    style: { fill: C_FERMION, stroke: "none" } },

  // ── μ⁺ outgoing leg (solid, arrow reversed — antiparticle) ───────────
  { type: "polyline",
    shape: { points: [[V2[0], V2[1]], [AP_OUT[0], AP_OUT[1]]] },
    style: { stroke: C_FERMION, lineWidth: LW, fill: "rgba(0,0,0,0)" } },
  { type: "polygon",
    shape: { points: arrowPoints(apA1[0], apA1[1], apA2[0], apA2[1], 24) },
    style: { fill: C_FERMION, stroke: "none" } },

  // ── Interaction vertices ──────────────────────────────────────────────
  { type: "circle", shape: { cx: V1[0], cy: V1[1], r: VR }, style: { fill: t.ink } },
  { type: "circle", shape: { cx: V2[0], cy: V2[1], r: VR }, style: { fill: t.ink } },

  // ── Particle labels ───────────────────────────────────────────────────
  { type: "text", style: { text: "e⁻",  x: E_IN[0]   - 14, y: E_IN[1]   - 44, font: "bold 30px sans-serif", fill: C_FERMION, textAlign: "right"  } },
  { type: "text", style: { text: "e⁺",  x: P_IN[0]   - 14, y: P_IN[1]   + 14, font: "bold 30px sans-serif", fill: C_FERMION, textAlign: "right"  } },
  { type: "text", style: { text: "μ⁻", x: MU_OUT[0] + 14, y: MU_OUT[1] - 44, font: "bold 30px sans-serif", fill: C_FERMION } },
  { type: "text", style: { text: "μ⁺", x: AP_OUT[0] + 14, y: AP_OUT[1] + 14, font: "bold 30px sans-serif", fill: C_FERMION } },
  { type: "text", style: { text: "γ*", x: (V1[0] + V2[0]) / 2 - 18, y: V1[1] - 58, font: "bold 36px sans-serif", fill: C_PHOTON } },

  // ── Legend ────────────────────────────────────────────────────────────
  { type: "polyline", shape: { points: [[80, H - 90], [155, H - 90]] }, style: { stroke: C_FERMION, lineWidth: LW, fill: "rgba(0,0,0,0)" } },
  { type: "polygon",  shape: { points: arrowPoints(102, H - 90, 112, H - 90, 20) }, style: { fill: C_FERMION, stroke: "none" } },
  { type: "text", style: { text: "fermion", x: 165, y: H - 100, font: "22px sans-serif", fill: t.inkSoft } },
  { type: "text", style: { text: "photon (γ*)", x: 435, y: H - 100, font: "22px sans-serif", fill: t.inkSoft } },

  // ── Time axis ─────────────────────────────────────────────────────────
  { type: "polyline", shape: { points: [[W / 2 - 100, H - 38], [W / 2 + 100, H - 38]] }, style: { stroke: t.inkSoft, lineWidth: 2, fill: "rgba(0,0,0,0)" } },
  { type: "polygon",  shape: { points: arrowPoints(W / 2 + 80, H - 38, W / 2 + 100, H - 38, 14) }, style: { fill: t.inkSoft, stroke: "none" } },
  { type: "text", style: { text: "time", x: W / 2 - 122, y: H - 48, font: "20px sans-serif", fill: t.inkSoft } },

  // ── Process description ───────────────────────────────────────────────
  { type: "text", style: { text: "e⁻e⁺ annihilation  →  virtual photon  →  μ⁻μ⁺ pair production", x: W / 2, y: 102, textAlign: "center", font: "24px sans-serif", fill: t.inkSoft } },
];

// Spread in the wavy photon beziers and legend wavy beziers
graphicElements = graphicElements.concat(photonWaves).concat(legendWaves);

chart.setOption({
  animation: false,
  backgroundColor: t.pageBg,
  title: {
    text: "feynman-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 26,
    textStyle: { color: t.ink, fontSize: 34, fontWeight: "normal" }
  },
  graphic: graphicElements,
});
