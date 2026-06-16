//# anyplot-orientation: square
// anyplot.ai
// stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-16

const t = window.ANYPLOT_TOKENS;
const DEG = Math.PI / 180;
const R = 1.0; // primitive (perimeter) radius in axis units

// --- Deterministic RNG (fixed-seed LCG + Box–Muller) -----------------------
let _seed = 20260616;
function rand() {
  _seed = (_seed * 1103515245 + 12345) & 0x7fffffff;
  return _seed / 0x7fffffff;
}
function gauss(mean, sd) {
  let u = 0,
    v = 0;
  while (u === 0) u = rand();
  while (v === 0) v = rand();
  return mean + sd * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// --- Equal-area (Schmidt, lower-hemisphere) projection ----------------------
// A line of given trend/plunge maps to a planar point. North = +y (top),
// East = +x (right); azimuth measured clockwise from North.
function projLine(trendDeg, plungeDeg) {
  const tr = trendDeg * DEG;
  const rho = (90 - plungeDeg) * DEG; // angular distance from net centre
  const r = R * Math.SQRT2 * Math.sin(rho / 2);
  return [r * Math.sin(tr), r * Math.cos(tr)];
}
// Project a downward direction vector (E, N, U) with U <= 0.
function projVec(e, n, u) {
  const h = Math.hypot(e, n);
  const rho = Math.acos(Math.max(-1, Math.min(1, -u))); // angle from nadir
  const r = R * Math.SQRT2 * Math.sin(rho / 2);
  if (h < 1e-9) return [0, 0];
  return [(r * e) / h, (r * n) / h];
}
// Pole to a plane: normal plunges (90 - dip), trend = dipDir + 180.
function poleXY(dipDir, dip) {
  return projLine(dipDir + 180, 90 - dip);
}
// Great circle of a plane: sweep in-plane lines from one strike end to the other.
function greatCircle(dipDir, dip, steps) {
  const a = dipDir * DEG,
    d = dip * DEG;
  const sx = Math.sin(a - Math.PI / 2),
    sy = Math.cos(a - Math.PI / 2); // strike line (horizontal)
  const tx = Math.cos(d) * Math.sin(a),
    ty = Math.cos(d) * Math.cos(a),
    tz = -Math.sin(d); // dip vector
  const pts = [];
  for (let i = 0; i <= steps; i++) {
    const b = (Math.PI * i) / steps;
    const cb = Math.cos(b),
      sb = Math.sin(b);
    pts.push(projVec(cb * sx + sb * tx, cb * sy + sb * ty, sb * tz));
  }
  return pts;
}

// --- Field data: bedding, joint set, fault (deterministic) ------------------
const features = [
  { name: "Bedding", color: t.palette[0], symbol: "circle", count: 46, ddMean: 118, ddSd: 11, dipMean: 24, dipSd: 6, nGreat: 7 },
  { name: "Joint set", color: t.palette[1], symbol: "triangle", count: 34, ddMean: 212, ddSd: 14, dipMean: 74, dipSd: 8, nGreat: 8 },
  { name: "Fault", color: t.palette[2], symbol: "diamond", count: 17, ddMean: 47, ddSd: 12, dipMean: 60, dipSd: 11, nGreat: 8 },
];

const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));

// --- Subtle equal-area net graticule (10° spacing about the N–S axis) -------
const netData = [];
function pushPath(pts) {
  for (const p of pts) netData.push(p);
  netData.push([null, null]);
}
// Meridians: planes striking N–S, dipping E/W — they pass through N and S.
for (let dip = 10; dip <= 80; dip += 10) {
  pushPath(greatCircle(90, dip, 90));
  pushPath(greatCircle(270, dip, 90));
}
pushPath(greatCircle(90, 90, 90)); // straight N–S diameter
pushPath(greatCircle(0, 90, 90)); // straight E–W diameter
// Small circles: cones about the horizontal N–S axis (latitude lines).
for (let colat = 10; colat <= 170; colat += 10) {
  if (colat === 90) continue; // coincides with the E–W diameter
  const k = colat * DEG;
  const arc = [];
  for (let j = 0; j <= 90; j++) {
    const phi = Math.PI + (Math.PI * j) / 90; // lower hemisphere (U <= 0)
    arc.push(projVec(Math.sin(k) * Math.cos(phi), Math.cos(k), Math.sin(k) * Math.sin(phi)));
  }
  pushPath(arc);
}

// --- Primitive circle + 10° perimeter tick marks ---------------------------
const frameData = [];
for (let deg = 0; deg <= 360; deg += 2) {
  frameData.push([R * Math.sin(deg * DEG), R * Math.cos(deg * DEG)]);
}
frameData.push([null, null]);
for (let deg = 0; deg < 360; deg += 10) {
  const outer = deg % 90 === 0 ? 1.05 : 1.03;
  frameData.push([R * Math.sin(deg * DEG), R * Math.cos(deg * DEG)]);
  frameData.push([outer * Math.sin(deg * DEG), outer * Math.cos(deg * DEG)]);
  frameData.push([null, null]);
}

// --- Build per-feature pole (scatter) + great-circle (line) series ----------
const series = [];

// Net graticule and frame sit beneath the data.
series.push({
  type: "line",
  name: "Net grid",
  data: netData,
  color: t.grid,
  lineWidth: 1,
  enableMouseTracking: false,
  showInLegend: false,
  marker: { enabled: false },
  zIndex: 0,
});
series.push({
  type: "line",
  name: "Primitive",
  data: frameData,
  color: t.inkSoft,
  lineWidth: 1.6,
  enableMouseTracking: false,
  showInLegend: false,
  marker: { enabled: false },
  zIndex: 1,
});

features.forEach((f, idx) => {
  const planes = [];
  for (let i = 0; i < f.count; i++) {
    const dipDir = (gauss(f.ddMean, f.ddSd) + 360) % 360;
    const dip = clamp(gauss(f.dipMean, f.dipSd), 2, 88);
    planes.push({ dipDir, dip });
  }

  // Poles (scatter) — every measurement; clustering reveals preferred orientation.
  const poleId = "poles-" + idx;
  series.push({
    type: "scatter",
    id: poleId,
    name: f.name,
    data: planes.map((p) => poleXY(p.dipDir, p.dip)),
    color: f.color,
    marker: {
      symbol: f.symbol,
      radius: 5.5,
      lineWidth: 1,
      lineColor: t.pageBg,
    },
    zIndex: 5,
  });

  // Great circles (line) — an evenly sampled subset keeps the net legible.
  const gcData = [];
  const stride = Math.max(1, Math.floor(f.count / f.nGreat));
  for (let i = 0; i < f.count; i += stride) {
    for (const pt of greatCircle(planes[i].dipDir, planes[i].dip, 80)) gcData.push(pt);
    gcData.push([null, null]);
  }
  series.push({
    type: "line",
    linkedTo: poleId,
    name: f.name + " planes",
    data: gcData,
    color: f.color,
    lineWidth: 1.6,
    opacity: 0.55,
    enableMouseTracking: false,
    marker: { enabled: false },
    zIndex: 3,
  });
});

// --- Cardinal labels (N/E/S/W) just outside the primitive ------------------
series.push({
  type: "scatter",
  name: "Cardinals",
  showInLegend: false,
  enableMouseTracking: false,
  color: t.ink,
  marker: { enabled: false },
  dataLabels: {
    enabled: true,
    allowOverlap: true,
    style: { color: t.ink, fontSize: "16px", fontWeight: "600", textOutline: "none" },
  },
  data: [
    { x: 0, y: 1.12, dataLabels: { format: "N" } },
    { x: 1.13, y: 0, dataLabels: { format: "E" } },
    { x: 0, y: -1.13, dataLabels: { format: "S" } },
    { x: -1.13, y: 0, dataLabels: { format: "W" } },
  ],
  zIndex: 6,
});

// --- Chart ------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    // Symmetric margins make the plot box square (1000×1000) so the net is round.
    marginTop: 70,
    marginBottom: 130,
    marginLeft: 100,
    marginRight: 100,
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "stereonet-equal-area · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Lower-hemisphere Schmidt net — poles (points) and great circles (planes)",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    min: -1.18,
    max: 1.18,
    visible: false,
    startOnTick: false,
    endOnTick: false,
  },
  yAxis: {
    min: -1.18,
    max: 1.18,
    visible: false,
    startOnTick: false,
    endOnTick: false,
    gridLineWidth: 0,
  },
  legend: {
    align: "center",
    verticalAlign: "bottom",
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
    symbolRadius: 6,
  },
  plotOptions: {
    series: { animation: false, states: { inactive: { opacity: 1 } } },
    scatter: { stickyTracking: false },
  },
  series,
});
