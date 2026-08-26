// anyplot.ai
// map-projections: World Map with Different Projections
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 80/100 | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Simplified landmass outlines (lon, lat degrees) ------------------------
// Low-vertex silhouettes, not survey-accurate coastlines — enough to carry the
// projection-distortion story (esp. Greenland/Antarctica vs. Africa in scale).
const LANDMASSES = [
  [
    [-17, 15], [-16, 21], [-11, 24], [-6, 30], [10, 32], [20, 31], [32, 31],
    [35, 20], [43, 12], [51, 12], [42, -2], [40, -15], [35, -25], [27, -34],
    [18, -34], [12, -18], [9, 4], [0, 4], [-10, 7], [-17, 15],
  ], // Africa
  [
    [-10, 36], [-9, 43], [-5, 48], [2, 51], [5, 58], [10, 60], [20, 60],
    [28, 60], [30, 66], [40, 66], [45, 68], [60, 70], [75, 73], [100, 73],
    [130, 72], [143, 60], [140, 45], [130, 35], [122, 31], [121, 25],
    [110, 18], [103, 10], [95, 5], [80, 8], [68, 7], [60, 25], [50, 25],
    [48, 30], [35, 32], [30, 36], [27, 36], [22, 40], [15, 40], [13, 45],
    [-10, 36],
  ], // Eurasia
  [
    [-165, 65], [-165, 70], [-140, 70], [-120, 75], [-95, 75], [-80, 73],
    [-65, 68], [-60, 60], [-55, 52], [-65, 45], [-75, 35], [-80, 26],
    [-97, 26], [-105, 20], [-115, 30], [-125, 40], [-125, 49], [-135, 58],
    [-165, 65],
  ], // North America
  [
    [-80, 10], [-77, 5], [-70, -5], [-70, -18], [-72, -30], [-70, -40],
    [-68, -52], [-65, -55], [-58, -52], [-53, -35], [-40, -20], [-35, -8],
    [-50, 2], [-60, 10], [-70, 12], [-80, 10],
  ], // South America
  [
    [-55, 60], [-45, 60], [-30, 65], [-25, 70], [-20, 75], [-25, 80],
    [-40, 83], [-55, 75], [-58, 68], [-55, 60],
  ], // Greenland
  [
    [113, -22], [122, -18], [130, -12], [137, -12], [142, -11], [145, -15],
    [153, -27], [150, -35], [140, -38], [131, -32], [115, -34], [113, -22],
  ], // Australia
  [
    [-180, -63], [-150, -66], [-120, -66], [-90, -70], [-60, -66],
    [-30, -66], [0, -66], [30, -66], [60, -66], [90, -66], [120, -66],
    [150, -66], [180, -63], [180, -85], [-180, -85], [-180, -63],
  ], // Antarctica
];

// --- Projections --------------------------------------------------------------
const MERC_CLIP = 85; // clamp latitude — true Mercator diverges at the poles

function toRad(deg) {
  return (deg * Math.PI) / 180;
}

function mercatorXY(lon, lat) {
  const phi = toRad(Math.max(-MERC_CLIP, Math.min(MERC_CLIP, lat)));
  return { x: toRad(lon), y: Math.log(Math.tan(Math.PI / 4 + phi / 2)) };
}

function mollweideXY(lon, lat) {
  const phi = toRad(lat);
  const lam = toRad(lon);
  let theta = phi;
  if (Math.PI / 2 - Math.abs(phi) > 1e-9) {
    for (let i = 0; i < 10; i++) {
      const delta = (2 * theta + Math.sin(2 * theta) - Math.PI * Math.sin(phi)) / (2 + 2 * Math.cos(2 * theta));
      theta -= delta;
    }
  } else {
    theta = Math.sign(phi) * (Math.PI / 2);
  }
  return { x: ((2 * Math.SQRT2) / Math.PI) * lam * Math.cos(theta), y: Math.SQRT2 * Math.sin(theta) };
}

const MERC_Y_LIMIT = mercatorXY(0, MERC_CLIP).y;
const PROJECTIONS = {
  mercator: {
    fn: mercatorXY,
    range: { xMin: -Math.PI, xMax: Math.PI, yMin: -MERC_Y_LIMIT, yMax: MERC_Y_LIMIT },
    latMin: -MERC_CLIP,
    latMax: MERC_CLIP,
  },
  mollweide: {
    fn: mollweideXY,
    range: { xMin: -2 * Math.SQRT2, xMax: 2 * Math.SQRT2, yMin: -Math.SQRT2, yMax: Math.SQRT2 },
    latMin: -90,
    latMax: 90,
  },
};

function toPanel(pt, range, rect) {
  const nx = (pt.x - range.xMin) / (range.xMax - range.xMin);
  const ny = (pt.y - range.yMin) / (range.yMax - range.yMin);
  return [rect.x + nx * rect.w, rect.y + (1 - ny) * rect.h];
}

function projectPoints(lonlats, kind, rect) {
  const proj = PROJECTIONS[kind];
  return lonlats.map(([lon, lat]) => toPanel(proj.fn(lon, lat), proj.range, rect));
}

function meridian(lon, kind) {
  const proj = PROJECTIONS[kind];
  const pts = [];
  for (let lat = proj.latMin; lat <= proj.latMax + 1e-6; lat += 2) pts.push([lon, lat]);
  return pts;
}

function parallel(lat) {
  return [[-180, lat], [180, lat]];
}

// --- Panel layout (CSS px, within the 1600×900 landscape mount) -------------
const PANEL_H = 480;
const PANEL_GAP = 60;
const MERC_RECT = { x: 50, y: 263, w: PANEL_H, h: PANEL_H };
const MOLL_RECT = { x: 50 + PANEL_H + PANEL_GAP, y: 263, w: 2 * PANEL_H, h: PANEL_H };

const MERIDIAN_LONS = [-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150];
const PARALLEL_LATS = [-60, -30, 0, 30, 60];
const LAND_STYLE = { fill: t.palette[0], stroke: t.inkSoft, lineWidth: 1, opacity: 0.92 };
const GRID_STYLE = { stroke: t.grid, lineWidth: 1, fill: "none" };
const OCEAN_STYLE = { fill: t.elevatedBg, stroke: t.inkSoft, lineWidth: 2 };

function panelElements(kind, rect, label) {
  const elements = [];

  if (kind === "mercator") {
    elements.push({ type: "rect", shape: { x: rect.x, y: rect.y, width: rect.w, height: rect.h }, style: OCEAN_STYLE, silent: true });
  } else {
    elements.push({
      type: "ellipse",
      shape: { cx: rect.x + rect.w / 2, cy: rect.y + rect.h / 2, rx: rect.w / 2, ry: rect.h / 2 },
      style: OCEAN_STYLE,
      silent: true,
    });
  }

  for (const lon of MERIDIAN_LONS) {
    elements.push({ type: "polyline", shape: { points: projectPoints(meridian(lon, kind), kind, rect) }, style: GRID_STYLE, silent: true });
  }
  for (const lat of PARALLEL_LATS) {
    elements.push({ type: "polyline", shape: { points: projectPoints(parallel(lat), kind, rect) }, style: GRID_STYLE, silent: true });
  }

  for (const landmass of LANDMASSES) {
    elements.push({ type: "polygon", shape: { points: projectPoints(landmass, kind, rect) }, style: LAND_STYLE, silent: true });
  }

  elements.push({
    type: "text",
    left: rect.x + rect.w / 2,
    top: rect.y - 34,
    style: { text: label, fill: t.ink, font: "600 16px sans-serif", textAlign: "center" },
  });

  return elements;
}

const graphicElements = [
  ...panelElements("mercator", MERC_RECT, "Mercator — conformal (shape-true, area-distorted)"),
  ...panelElements("mollweide", MOLL_RECT, "Mollweide — equal-area (area-true, shape-distorted)"),
];

// --- Chart --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "map-projections · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  graphic: { elements: graphicElements },
});
