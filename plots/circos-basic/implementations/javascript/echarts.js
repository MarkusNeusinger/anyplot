// anyplot.ai
// circos-basic: Circos Plot
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-04
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width: W, height: H } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Software-module call graph: which service talks to which, and how often
// (calls/sec, thousands). The inner track shows each module's test-coverage %.
const modules = [
  "API Gateway",
  "Auth Service",
  "Database",
  "Cache Layer",
  "Job Queue",
  "Web UI",
  "Analytics",
  "Notifications",
];

const connections = [
  ["API Gateway", "Auth Service", 45],
  ["API Gateway", "Database", 60],
  ["API Gateway", "Cache Layer", 35],
  ["API Gateway", "Job Queue", 20],
  ["Auth Service", "Database", 30],
  ["Auth Service", "Cache Layer", 15],
  ["Web UI", "API Gateway", 55],
  ["Web UI", "Analytics", 25],
  ["Job Queue", "Database", 40],
  ["Job Queue", "Notifications", 22],
  ["Cache Layer", "Database", 18],
  ["Analytics", "Database", 28],
  ["Analytics", "Cache Layer", 12],
  ["Notifications", "Web UI", 10],
  ["Notifications", "Database", 14],
  ["Web UI", "Cache Layer", 9],
];

const coverage = {
  "API Gateway": 82,
  "Auth Service": 90,
  Database: 65,
  "Cache Layer": 78,
  "Job Queue": 55,
  "Web UI": 88,
  Analytics: 70,
  Notifications: 60,
};

// --- Layout geometry ---------------------------------------------------------
const cx = W / 2;
const cy = H / 2 + 30; // nudge down to leave room for the title
const outerLimit = Math.min(W, H) / 2 - 60;
const labelBand = 80;
const segmentOuter = outerLimit - labelBand;
const ringWidth = segmentOuter * 0.09;
const segmentInner = segmentOuter - ringWidth;
const trackOuter = segmentInner - 8;
const trackBandHeight = ringWidth;
const trackBase = trackOuter - trackBandHeight;
const ribbonRadius = trackBase - 10;

const GAP_DEG = 4;
const moduleColor = Object.fromEntries(modules.map((m, i) => [m, t.palette[i]]));

// --- Angle allocation (chord-diagram convention: arc span ∝ total connection
// value touching each module) --------------------------------------------
const segmentTotal = Object.fromEntries(modules.map((m) => [m, 0]));
connections.forEach(([source, target, value]) => {
  segmentTotal[source] += value;
  segmentTotal[target] += value;
});

const totalGap = GAP_DEG * modules.length;
const totalValue = modules.reduce((sum, m) => sum + segmentTotal[m], 0);
const degPerValue = (360 - totalGap) / totalValue;

const segmentAngle = {};
let cursor = 0;
modules.forEach((m) => {
  const span = segmentTotal[m] * degPerValue;
  segmentAngle[m] = { start: cursor, end: cursor + span };
  cursor += span + GAP_DEG;
});

const segmentCursor = Object.fromEntries(modules.map((m) => [m, segmentAngle[m].start]));
const ribbons = connections.map(([source, target, value]) => {
  const width = value * degPerValue;
  const sStart = segmentCursor[source];
  const sEnd = sStart + width;
  segmentCursor[source] = sEnd;
  const tStart = segmentCursor[target];
  const tEnd = tStart + width;
  segmentCursor[target] = tEnd;
  return { source, target, value, sStart, sEnd, tStart, tEnd };
});

// --- Geometry helpers --------------------------------------------------------
function polar(r, deg) {
  const rad = (deg * Math.PI) / 180;
  return [cx + r * Math.sin(rad), cy - r * Math.cos(rad)];
}

// The declarative `graphic` component only ships a handful of registered shape
// types (circle/sector/ring/polygon/polyline/rect/line/bezierCurve/arc/text) —
// no generic SVG-path type. Donut wedges and chord ribbons are built instead as
// sampled-point polygons, dense enough to read as smooth curves.
function arcPoints(r, startDeg, endDeg, steps) {
  const pts = [];
  for (let i = 0; i <= steps; i++) {
    pts.push(polar(r, startDeg + (endDeg - startDeg) * (i / steps)));
  }
  return pts;
}

function quadBezierPoints(p0, pControl, p1, steps) {
  const pts = [];
  for (let i = 1; i <= steps; i++) {
    const u = i / steps;
    const x = (1 - u) * (1 - u) * p0[0] + 2 * (1 - u) * u * pControl[0] + u * u * p1[0];
    const y = (1 - u) * (1 - u) * p0[1] + 2 * (1 - u) * u * pControl[1] + u * u * p1[1];
    pts.push([x, y]);
  }
  return pts;
}

function sectorPoints(rOuter, rInner, startDeg, endDeg) {
  const steps = Math.max(4, Math.round((endDeg - startDeg) / 3));
  return arcPoints(rOuter, startDeg, endDeg, steps).concat(arcPoints(rInner, endDeg, startDeg, steps));
}

function ribbonPoints(r, sStart, sEnd, tStart, tEnd) {
  const curveSteps = 20;
  const arcS = arcPoints(r, sStart, sEnd, Math.max(4, Math.round((sEnd - sStart) / 3)));
  const arcT = arcPoints(r, tStart, tEnd, Math.max(4, Math.round((tEnd - tStart) / 3)));
  const curve1 = quadBezierPoints(arcS[arcS.length - 1], [cx, cy], arcT[0], curveSteps);
  const curve2 = quadBezierPoints(arcT[arcT.length - 1], [cx, cy], arcS[0], curveSteps);
  return arcS.concat(curve1, arcT, curve2);
}

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function lerpColor(a, b, frac) {
  const [r1, g1, b1] = hexToRgb(a);
  const [r2, g2, b2] = hexToRgb(b);
  const r = Math.round(r1 + (r2 - r1) * frac);
  const g = Math.round(g1 + (g2 - g1) * frac);
  const bl = Math.round(b1 + (b2 - b1) * frac);
  return `rgb(${r}, ${g}, ${bl})`;
}

// --- Graphic elements: ribbons (bottom) → track → segment ring → labels -----
const covValues = Object.values(coverage);
const covMin = Math.min(...covValues);
const covMax = Math.max(...covValues);

const ribbonElements = ribbons.map((rb) => ({
  type: "polygon",
  shape: { points: ribbonPoints(ribbonRadius, rb.sStart, rb.sEnd, rb.tStart, rb.tEnd) },
  style: { fill: moduleColor[rb.source], opacity: 0.5, stroke: t.pageBg, lineWidth: 1 },
  silent: true,
}));

const trackBaseline = {
  type: "ring",
  shape: { cx, cy, r: trackBase + 1.5, r0: trackBase - 1.5 },
  style: { fill: t.grid },
  silent: true,
};

const trackElements = modules.map((m) => {
  const { start, end } = segmentAngle[m];
  const frac = (coverage[m] - covMin) / (covMax - covMin);
  const barOuter = trackBase + trackBandHeight * Math.max(frac, 0.3);
  return {
    type: "polygon",
    shape: { points: sectorPoints(barOuter, trackBase, start, end) },
    style: { fill: lerpColor(t.seq[0], t.seq[1], frac), stroke: t.pageBg, lineWidth: 1 },
    silent: true,
  };
});

const segmentElements = modules.map((m) => {
  const { start, end } = segmentAngle[m];
  return {
    type: "polygon",
    shape: { points: sectorPoints(segmentOuter, segmentInner, start, end) },
    style: { fill: moduleColor[m], stroke: t.pageBg, lineWidth: 2 },
    silent: true,
  };
});

const labelElements = modules.map((m) => {
  const { start, end } = segmentAngle[m];
  const mid = (start + end) / 2;
  const [lx, ly] = polar(segmentOuter + 18, mid);
  const rightHalf = mid < 180;
  return {
    type: "text",
    style: {
      text: m,
      x: lx,
      y: ly,
      fill: t.ink,
      fontSize: 18,
      fontWeight: 500,
      align: rightHalf ? "left" : "right",
      verticalAlign: "middle",
    },
    silent: true,
  };
});

// --- Init & option ------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "circos-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 30,
    textStyle: { color: t.ink, fontSize: 22 },
  },
  graphic: [...ribbonElements, trackBaseline, ...trackElements, ...segmentElements, ...labelElements],
});

chart.on("finished", () => {
  window.__anyplotReady = true;
});
