// anyplot.ai
// wireframe-3d-basic: Basic 3D Wireframe Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.1
// Quality: 83/100 | Created: 2026-08-04

const t = window.ANYPLOT_TOKENS;

// --- Data: ripple surface z = sin(sqrt(x^2 + y^2)) on a 27x27 grid ---------
const GRID_N = 27;
const RANGE = 6;
const grid = Array.from({ length: GRID_N }, (_, i) => -RANGE + (2 * RANGE * i) / (GRID_N - 1));
const zAt = (x, y) => Math.sin(Math.sqrt(x * x + y * y));
const zGrid = grid.map((y) => grid.map((x) => zAt(x, y)));
let zMin = Infinity;
let zMax = -Infinity;
zGrid.forEach((row) =>
  row.forEach((z) => {
    if (z < zMin) zMin = z;
    if (z > zMax) zMax = z;
  })
);

// --- 3D -> 2D orthographic projection (elevation 28°, azimuth 40°) ---------
// Highcharts core has no chart3d/highcharts-3d module, so the mesh is
// projected by hand into plain (x, y) screen coordinates and drawn as
// ordinary `line` series — the same math a native 3D engine applies before
// rasterizing, just computed here instead of in an unavailable add-on.
const ELEV = (28 * Math.PI) / 180;
const AZIM = (40 * Math.PI) / 180;
const cosAz = Math.cos(AZIM);
const sinAz = Math.sin(AZIM);
const cosEl = Math.cos(ELEV);
const sinEl = Math.sin(ELEV);

const project = (x, y, z) => {
  const xr = x * cosAz + y * sinAz;
  const yr = -x * sinAz + y * cosAz;
  const zScreen = yr * sinEl + z * cosEl;
  return [xr, zScreen];
};

// --- Color: height-based gradient along the imprint_seq colormap -----------
const hexToRgb = (hex) => {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};
const seqLo = hexToRgb(t.seq[0]);
const seqHi = hexToRgb(t.seq[1]);
const heightColor = (z) => {
  const f = (z - zMin) / (zMax - zMin);
  const r = Math.round(seqLo[0] + (seqHi[0] - seqLo[0]) * f);
  const g = Math.round(seqLo[1] + (seqHi[1] - seqLo[1]) * f);
  const b = Math.round(seqLo[2] + (seqHi[2] - seqLo[2]) * f);
  return `rgb(${r}, ${g}, ${b})`;
};

// --- Mesh: one line series per grid row and per grid column ----------------
const projected = grid.map((y, iy) => grid.map((x, ix) => project(x, y, zGrid[iy][ix])));

const meshSeries = [];
grid.forEach((_, iy) => {
  const avgZ = zGrid[iy].reduce((a, b) => a + b, 0) / GRID_N;
  meshSeries.push({
    type: "line",
    data: projected[iy],
    color: heightColor(avgZ),
    lineWidth: 1.3,
    marker: { enabled: false },
    enableMouseTracking: false,
    showInLegend: false,
  });
});
grid.forEach((_, ix) => {
  const colZs = grid.map((_, iy) => zGrid[iy][ix]);
  const avgZ = colZs.reduce((a, b) => a + b, 0) / GRID_N;
  const colPoints = grid.map((_, iy) => projected[iy][ix]);
  meshSeries.push({
    type: "line",
    data: colPoints,
    color: heightColor(avgZ),
    lineWidth: 1.3,
    marker: { enabled: false },
    enableMouseTracking: false,
    showInLegend: false,
  });
});

// --- Axis frame: an L-shaped X/Y/Z reference resting below the surface -----
const floorZ = zMin - (zMax - zMin) * 0.35;
const topZ = zMax + (zMax - zMin) * 0.2;
const corner = project(-RANGE, -RANGE, floorZ);
const xEnd = project(RANGE, -RANGE, floorZ);
const yEnd = project(-RANGE, RANGE, floorZ);
const zEnd = project(-RANGE, -RANGE, topZ);

const axisFrameSeries = [
  { type: "line", data: [corner, xEnd], color: t.inkSoft, lineWidth: 2, marker: { enabled: false }, enableMouseTracking: false, showInLegend: false },
  { type: "line", data: [corner, yEnd], color: t.inkSoft, lineWidth: 2, marker: { enabled: false }, enableMouseTracking: false, showInLegend: false },
  { type: "line", data: [corner, zEnd], color: t.inkSoft, lineWidth: 2, marker: { enabled: false }, enableMouseTracking: false, showInLegend: false },
];

// --- Axis ticks + titles as labeled points (core dataLabels, no modules) ---
// The three axes share one corner, so ticks placed there are offset in
// different directions per axis (down / left / left) to keep the labels from
// stacking on top of each other. The two "-RANGE" ticks (one per axis) sit
// exactly on top of that shared corner point, so they get an extra push
// beyond the normal offset to stay independently legible.
const tickVals = [-RANGE, 0, RANGE];
const tickPoints = [];
tickVals.forEach((v) => {
  const [sx, sy] = project(v, -RANGE, floorZ);
  const cornerBoost = v === -RANGE ? 16 : 0;
  tickPoints.push({ x: sx, y: sy, name: String(v), dataLabels: { x: 0, y: 18 + cornerBoost } });
});
tickVals.forEach((v) => {
  const [sx, sy] = project(-RANGE, v, floorZ);
  const cornerBoost = v === -RANGE ? 16 : 0;
  tickPoints.push({ x: sx, y: sy, name: String(v), dataLabels: { x: -22 - cornerBoost, y: 0 } });
});
[zMin, 0, zMax].forEach((v) => {
  const [sx, sy] = project(-RANGE, -RANGE, v);
  tickPoints.push({ x: sx, y: sy, name: v.toFixed(1), dataLabels: { x: -26, y: 0 } });
});

const [xTitleX, xTitleY] = project(RANGE * 1.18, -RANGE, floorZ);
const [yTitleX, yTitleY] = project(-RANGE, RANGE * 1.18, floorZ);
const [zTitleX, zTitleY] = project(-RANGE, -RANGE, topZ * 1.12);
const titlePoints = [
  { x: xTitleX, y: xTitleY, name: "X" },
  { x: yTitleX, y: yTitleY, name: "Y" },
  { x: zTitleX, y: zTitleY, name: "Z" },
];

const labelSeries = [
  {
    type: "scatter",
    data: tickPoints,
    marker: { enabled: false },
    enableMouseTracking: false,
    showInLegend: false,
    dataLabels: {
      enabled: true,
      format: "{point.name}",
      allowOverlap: true,
      style: { color: t.inkSoft, fontSize: "13px", textOutline: "none" },
    },
  },
  {
    type: "scatter",
    data: titlePoints,
    marker: { enabled: false },
    enableMouseTracking: false,
    showInLegend: false,
    dataLabels: {
      enabled: true,
      format: "{point.name}",
      allowOverlap: true,
      style: { color: t.ink, fontSize: "16px", fontWeight: "600", textOutline: "none" },
    },
  },
];

// --- Axis bounds: fit every projected coordinate with padding --------------
const allX = [];
const allY = [];
[...projected.flat(), corner, xEnd, yEnd, zEnd, ...tickPoints, ...titlePoints].forEach((p) => {
  const px = Array.isArray(p) ? p[0] : p.x;
  const py = Array.isArray(p) ? p[1] : p.y;
  allX.push(px);
  allY.push(py);
});
const padX = (Math.max(...allX) - Math.min(...allX)) * 0.08;
const padY = (Math.max(...allY) - Math.min(...allY)) * 0.08;

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "wireframe-3d-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "z = sin(&#8730;(x&sup2; + y&sup2;)) ripple surface",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    visible: false,
    min: Math.min(...allX) - padX,
    max: Math.max(...allX) + padX,
    startOnTick: false,
    endOnTick: false,
  },
  yAxis: {
    visible: false,
    min: Math.min(...allY) - padY,
    max: Math.max(...allY) + padY,
    startOnTick: false,
    endOnTick: false,
    title: { text: null },
  },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: { series: { animation: false } },
  series: [...meshSeries, ...axisFrameSeries, ...labelSeries],
});
