// anyplot.ai
// contour-3d: 3D Contour Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 69/100 | Created: 2026-09-10

const t = window.ANYPLOT_TOKENS;

// --- Data: "peaks" response surface z = f(x, y) on a 33x33 grid, read as ---
// terrain elevation relative to sea level (z = 0) ---------------------------
const GRID_N = 33;
const RANGE = 3;
const grid = Array.from({ length: GRID_N }, (_, i) => -RANGE + (2 * RANGE * i) / (GRID_N - 1));
const peaks = (x, y) =>
  3 * (1 - x) ** 2 * Math.exp(-(x ** 2) - (y + 1) ** 2) -
  10 * (x / 5 - x ** 3 - y ** 5) * Math.exp(-(x ** 2) - y ** 2) -
  (1 / 3) * Math.exp(-((x + 1) ** 2) - y ** 2);
const zGrid = grid.map((y) => grid.map((x) => peaks(x, y)));
let zMin = Infinity;
let zMax = -Infinity;
zGrid.forEach((row) =>
  row.forEach((z) => {
    if (z < zMin) zMin = z;
    if (z > zMax) zMax = z;
  })
);
const M = Math.max(Math.abs(zMin), Math.abs(zMax));
const fmt = (v) => {
  const s = v.toFixed(1);
  return s === "-0.0" ? "0.0" : s;
};

// --- 3D -> 2D orthographic projection (elevation 30°, azimuth -50°) --------
// Highcharts core has no chart3d/highcharts-3d module (and no polygon/
// colorAxis — those live in highcharts-more, also unloaded), so the surface,
// its isolines, and the legend are all projected/drawn by hand as ordinary
// `line`/`scatter` series — the same math a native 3D engine applies before
// rasterizing, just computed here instead of in an unavailable add-on.
const ELEV = (30 * Math.PI) / 180;
const AZIM = (-50 * Math.PI) / 180;
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

// --- Color: diverging imprint_div gradient, centered on sea level (z = 0) --
const hexToRgb = (hex) => {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};
const divLo = hexToRgb(t.div[0]);
const divHi = hexToRgb(t.div[2]);
// The canonical imprint_div midpoint equals the page background (by design,
// for area fills that should "fade to neutral" at zero). For thin isoline
// strokes that would make every near-sea-level contour invisible, so lines
// blend through the theme ink token instead — still the two Imprint
// diverging anchors, just a legible midpoint for stroked geometry.
const lineMid = hexToRgb(t.ink);
const lerpRgb = (a, b, f) => [0, 1, 2].map((i) => Math.round(a[i] + (b[i] - a[i]) * f));
const rgbaStr = ([r, g, b], a) => `rgba(${r}, ${g}, ${b}, ${a})`;
const colorAt = (z, alpha = 1) => {
  const raw = Math.min(1, Math.max(-1, z / M)); // -1..1 around sea level
  const f = Math.sign(raw) * Math.sqrt(Math.abs(raw)); // sqrt eases weak levels toward a legible tint
  return f < 0 ? rgbaStr(lerpRgb(lineMid, divLo, -f), alpha) : rgbaStr(lerpRgb(lineMid, divHi, f), alpha);
};

// --- Contour levels: 6 isolines spanning the elevation range, centered on 0
const N_LEVELS = 6;
const levels = Array.from({ length: N_LEVELS }, (_, i) => -M + ((i + 1) * (2 * M)) / (N_LEVELS + 1));

// --- Isolines via marching-triangles: split each grid cell into 2 -----------
// triangles, then for every triangle + level, linearly interpolate along the
// crossing edges to get a 2-point segment lying exactly on that contour.
const lerpPt = (a, b, level) => {
  const f = (level - a[2]) / (b[2] - a[2]);
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, level];
};
const triangleSegment = (v0, v1, v2, level) => {
  const pts = [];
  [
    [v0, v1],
    [v1, v2],
    [v2, v0],
  ].forEach(([a, b]) => {
    if ((a[2] - level) * (b[2] - level) < 0) pts.push(lerpPt(a, b, level));
  });
  return pts.length === 2 ? pts : null;
};

const floorZ = zMin - (zMax - zMin) * 0.3;
const surfaceLevelData = levels.map(() => []);
const baseLevelData = levels.map(() => []);
for (let j = 0; j < GRID_N - 1; j++) {
  for (let i = 0; i < GRID_N - 1; i++) {
    const c00 = [grid[i], grid[j], zGrid[j][i]];
    const c10 = [grid[i + 1], grid[j], zGrid[j][i + 1]];
    const c01 = [grid[i], grid[j + 1], zGrid[j + 1][i]];
    const c11 = [grid[i + 1], grid[j + 1], zGrid[j + 1][i + 1]];
    [
      [c00, c10, c01],
      [c10, c11, c01],
    ].forEach((tri) => {
      levels.forEach((level, li) => {
        const seg = triangleSegment(tri[0], tri[1], tri[2], level);
        if (!seg) return;
        const [p1, p2] = seg;
        surfaceLevelData[li].push(project(...p1), project(...p2), [null, null]);
        baseLevelData[li].push(project(p1[0], p1[1], floorZ), project(p2[0], p2[1], floorZ), [null, null]);
      });
    });
  }
}

// --- Sparse wireframe mesh: carries the surface geometry between isolines --
// Drawn in a fixed neutral (not value-coded) so it reads as structure —
// the diverging colormap is reserved for the isolines, the actual data encoding.
const MESH_STRIDE = 2;
const meshColor = rgbaStr(hexToRgb(t.inkSoft), 0.5);
const meshSeries = [];
for (let j = 0; j < GRID_N; j += MESH_STRIDE) {
  meshSeries.push({
    type: "line",
    data: grid.map((x, i) => project(x, grid[j], zGrid[j][i])),
    color: meshColor,
    lineWidth: 1,
    marker: { enabled: false },
    enableMouseTracking: false,
    showInLegend: false,
  });
}
for (let i = 0; i < GRID_N; i += MESH_STRIDE) {
  meshSeries.push({
    type: "line",
    data: grid.map((y, j) => project(grid[i], y, zGrid[j][i])),
    color: meshColor,
    lineWidth: 1,
    marker: { enabled: false },
    enableMouseTracking: false,
    showInLegend: false,
  });
}

// --- Isoline series: bold on the surface, faint projected onto the floor ---
const isolineSurfaceSeries = levels.map((level, li) => ({
  type: "line",
  data: surfaceLevelData[li],
  color: colorAt(level),
  lineWidth: 2.4,
  marker: { enabled: false },
  enableMouseTracking: false,
  showInLegend: false,
}));
const isolineBaseSeries = levels.map((level, li) => ({
  type: "line",
  data: baseLevelData[li],
  color: colorAt(level, 0.55),
  lineWidth: 1.4,
  dashStyle: "ShortDot",
  marker: { enabled: false },
  enableMouseTracking: false,
  showInLegend: false,
}));

// --- Axis frame: an L-shaped X/Y/Z reference resting below the surface -----
const topZ = zMax + (zMax - zMin) * 0.15;
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
  tickPoints.push({ x: sx, y: sy, name: fmt(v), dataLabels: { x: -26, y: 0 } });
});

const [xTitleX, xTitleY] = project(RANGE * 1.22, -RANGE, floorZ);
const [yTitleX, yTitleY] = project(-RANGE, RANGE * 1.22, floorZ);
const [zTitleX, zTitleY] = project(-RANGE, -RANGE, topZ * 1.12);
const titlePoints = [
  { x: xTitleX, y: xTitleY, name: "X" },
  { x: yTitleX, y: yTitleY, name: "Y" },
  { x: zTitleX, y: zTitleY, name: "Elevation" },
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

// --- Preliminary bounds (everything except the manual colorbar legend) -----
const prelimPts = [];
meshSeries.forEach((s) => s.data.forEach((p) => prelimPts.push(p)));
isolineSurfaceSeries.forEach((s) => s.data.forEach((p) => p[1] !== null && prelimPts.push(p)));
[corner, xEnd, yEnd, zEnd].forEach((p) => prelimPts.push(p));
[...tickPoints, ...titlePoints].forEach((p) => prelimPts.push([p.x, p.y]));
const prelimX = prelimPts.map((p) => p[0]);
const prelimY = prelimPts.map((p) => p[1]);
const pMinX = Math.min(...prelimX);
const pMaxX = Math.max(...prelimX);
const pMinY = Math.min(...prelimY);
const pMaxY = Math.max(...prelimY);

// --- Manual colorbar: one swatch + value label per isoline level -----------
// Highcharts core has no ColorAxis (map/heatmap-only), so the level legend
// is built from ordinary labeled scatter points — the same technique used
// for the axis ticks above.
const legendX = pMaxX + (pMaxX - pMinX) * 0.12;
const legendTop = pMaxY - (pMaxY - pMinY) * 0.08;
const legendStep = (pMaxY - pMinY) * 0.12;
const swatchLevels = [...levels].sort((a, b) => b - a);
const legendSwatches = swatchLevels.map((level, k) => ({
  x: legendX,
  y: legendTop - (k + 1) * legendStep,
  name: fmt(level),
  color: colorAt(level),
}));
const legendHeader = [{ x: legendX, y: legendTop, name: "Elevation levels" }];

const legendSeries = [
  {
    type: "scatter",
    data: legendSwatches,
    marker: { symbol: "square", radius: 9, lineWidth: 0 },
    enableMouseTracking: false,
    showInLegend: false,
    dataLabels: {
      enabled: true,
      format: "{point.name}",
      align: "left",
      x: 18,
      allowOverlap: true,
      style: { color: t.inkSoft, fontSize: "13px", textOutline: "none" },
    },
  },
  {
    type: "scatter",
    data: legendHeader,
    marker: { enabled: false },
    enableMouseTracking: false,
    showInLegend: false,
    dataLabels: {
      enabled: true,
      format: "{point.name}",
      align: "left",
      x: -9,
      allowOverlap: true,
      style: { color: t.ink, fontSize: "14px", fontWeight: "600", textOutline: "none" },
    },
  },
];

// --- Final bounds: everything, with extra right-side room for the legend ---
const allX = [...prelimX, ...legendSwatches.map((p) => p.x + (pMaxX - pMinX) * 0.12)];
const allY = [...prelimY, legendTop + legendStep, ...legendSwatches.map((p) => p.y)];
const padX = (Math.max(...allX) - Math.min(...allX)) * 0.06;
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
  colors: t.palette,
  title: {
    text: "contour-3d · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Terrain elevation relative to sea level, with isolines on the surface and projected onto the base plane",
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
  series: [...meshSeries, ...isolineBaseSeries, ...isolineSurfaceSeries, ...axisFrameSeries, ...labelSeries, ...legendSeries],
});
