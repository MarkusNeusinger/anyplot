// anyplot.ai
// line-3d-trajectory: 3D Line Plot for Trajectory Visualization
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-10

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// --- Data: Lorenz attractor, integrated with RK4 ----------------------------
// Classic chaotic system (sigma, rho, beta) — a canonical example of a 3D
// trajectory whose spatial structure (the two "wings") only reads correctly
// with real depth cues, which is exactly what interactive rotation gives a
// viewer and a flat projection has to approximate.
const SIGMA = 10;
const RHO = 28;
const BETA = 8 / 3;
const DT = 0.008;
const STEPS = 6000;

function lorenzDerivative(x, y, z) {
  return [SIGMA * (y - x), x * (RHO - z) - y, x * y - BETA * z];
}

function rk4Step(x, y, z) {
  const [k1x, k1y, k1z] = lorenzDerivative(x, y, z);
  const [k2x, k2y, k2z] = lorenzDerivative(
    x + (DT / 2) * k1x,
    y + (DT / 2) * k1y,
    z + (DT / 2) * k1z
  );
  const [k3x, k3y, k3z] = lorenzDerivative(
    x + (DT / 2) * k2x,
    y + (DT / 2) * k2y,
    z + (DT / 2) * k2z
  );
  const [k4x, k4y, k4z] = lorenzDerivative(x + DT * k3x, y + DT * k3y, z + DT * k3z);
  return [
    x + (DT / 6) * (k1x + 2 * k2x + 2 * k3x + k4x),
    y + (DT / 6) * (k1y + 2 * k2y + 2 * k3y + k4y),
    z + (DT / 6) * (k1z + 2 * k2z + 2 * k3z + k4z),
  ];
}

const rawPoints = [[0.1, 0, 0]];
for (let i = 1; i < STEPS; i += 1) {
  const [px, py, pz] = rawPoints[i - 1];
  rawPoints.push(rk4Step(px, py, pz));
}
// Downsample to a smooth-but-lighter point count (spec calls for 100-2000).
const DOWNSAMPLE = 4;
const points = rawPoints.filter((_, i) => i % DOWNSAMPLE === 0);
const N = points.length;

// --- Camera: orthographic axonometric projection (elevation + azimuth) -----
const ELEVATION = (22 * Math.PI) / 180;
const AZIMUTH = (-52 * Math.PI) / 180;
const sinAz = Math.sin(AZIMUTH);
const cosAz = Math.cos(AZIMUTH);
const sinEl = Math.sin(ELEVATION);
const cosEl = Math.cos(ELEVATION);

// True proportions matter for a trajectory (unlike a bounded surface), so all
// three axes share one normalizing scale instead of being stretched
// independently — the butterfly shape stays undistorted.
const xs = points.map((p) => p[0]);
const ys = points.map((p) => p[1]);
const zs = points.map((p) => p[2]);
const xMin = Math.min(...xs);
const xMax = Math.max(...xs);
const yMin = Math.min(...ys);
const yMax = Math.max(...ys);
const zMin = Math.min(...zs);
const zMax = Math.max(...zs);
const xCenter = (xMin + xMax) / 2;
const yCenter = (yMin + yMax) / 2;
const zCenter = (zMin + zMax) / 2;
const maxHalfRange = Math.max((xMax - xMin) / 2, (yMax - yMin) / 2, (zMax - zMin) / 2);

function projectRaw(x, y, z) {
  const xn = (x - xCenter) / maxHalfRange;
  const yn = (y - yCenter) / maxHalfRange;
  const zn = (z - zCenter) / maxHalfRange;
  const screenX = -xn * sinAz + yn * cosAz;
  const screenY = -xn * cosAz * sinEl - yn * sinAz * sinEl + zn * cosEl;
  const depth = xn * cosEl * cosAz + yn * cosEl * sinAz + zn * sinEl;
  return { screenX, screenY, depth };
}

// X and Y sit on the box corner farthest from the camera on screen (lowest),
// so ticks/labels stay clear of the trajectory; Z rises from the corner the
// azimuth pins to the box's far-left screen edge for its whole height.
const CORNER_X = yMax;
const Z_CORNER_X = xMax;
const Z_CORNER_Y = yMin;
// The six axis-frame endpoints, in data space.
const frameCorners = [
  [xMin, CORNER_X, zMin],
  [xMax, CORNER_X, zMin],
  [xMax, yMin, zMin],
  [xMax, yMax, zMin],
  [Z_CORNER_X, Z_CORNER_Y, zMin],
  [Z_CORNER_X, Z_CORNER_Y, zMax],
];

// --- Fit the projected bounding box into the mount, leaving title room -----
// Fit to the union of the trajectory's own footprint AND the axis frame: the
// Lorenz curve never visits every (xMax, yMax, zMax)-style corner
// simultaneously, so fitting the data cube's 8 corners alone leaves the
// rendered curve far smaller than the canvas, while fitting the curve alone
// under-budgets space for the frame (which sits off to one side). PAD adds a
// small multiplicative margin for tick labels/axis titles beyond that union.
const extentPoints = points.concat(frameCorners);
const extentProjected = extentPoints.map((p) => projectRaw(p[0], p[1], p[2]));
const sxs = extentProjected.map((c) => c.screenX);
const sys = extentProjected.map((c) => c.screenY);
const boxW = Math.max(...sxs) - Math.min(...sxs);
const boxH = Math.max(...sys) - Math.min(...sys);
const boxCx = (Math.max(...sxs) + Math.min(...sxs)) / 2;
const boxCy = (Math.max(...sys) + Math.min(...sys)) / 2;

const TOP_MARGIN = 120;
const SIDE_MARGIN = 140;
const BOTTOM_MARGIN = 90;
const drawW = size.width - 2 * SIDE_MARGIN;
const drawH = size.height - TOP_MARGIN - BOTTOM_MARGIN;
const PAD = 1.22; // headroom for tick labels + axis titles beyond the frame
const scale = Math.min(drawW / (boxW * PAD), drawH / (boxH * PAD));
const originX = size.width / 2 - boxCx * scale;
const originY = TOP_MARGIN + drawH / 2 + boxCy * scale;

function toPixel(x, y, z) {
  const { screenX, screenY, depth } = projectRaw(x, y, z);
  return { px: originX + screenX * scale, py: originY - screenY * scale, depth };
}

// --- Trajectory: one segment per consecutive pair, colored by elapsed time -
// Time progression is continuous data, so it takes the Imprint sequential
// ramp (imprint_seq) rather than a categorical color.
function lerpColor(hexA, hexB, frac) {
  const a = [1, 3, 5].map((i) => parseInt(hexA.slice(i, i + 2), 16));
  const b = [1, 3, 5].map((i) => parseInt(hexB.slice(i, i + 2), 16));
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * frac));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

const screenPoints = points.map((p) => toPixel(p[0], p[1], p[2]));
const segments = [];
for (let i = 0; i < N - 1; i += 1) {
  const a = screenPoints[i];
  const b = screenPoints[i + 1];
  segments.push({
    x1: a.px,
    y1: a.py,
    x2: b.px,
    y2: b.py,
    depth: (a.depth + b.depth) / 2,
    color: lerpColor(t.seq[0], t.seq[1], i / (N - 2)),
  });
}
// High point density (N ~ 1500) with heavy self-overlap on a chaotic curve:
// thin strokes + depth-faded alpha keep the wings readable instead of a
// solid smear. Back-to-front draw order approximates hidden-line depth.
segments.sort((s1, s2) => s1.depth - s2.depth);
const dMin = Math.min(...segments.map((s) => s.depth));
const dMax = Math.max(...segments.map((s) => s.depth));
const trajectoryElements = segments.map((s) => {
  const tDepth = dMax > dMin ? (s.depth - dMin) / (dMax - dMin) : 1;
  return {
    type: "line",
    shape: { x1: s.x1, y1: s.y1, x2: s.x2, y2: s.y2 },
    style: { stroke: s.color, lineWidth: 1.7, opacity: 0.45 + 0.5 * tDepth },
    silent: true,
  };
});

// --- Axis frame: three edges of the bounding box, ticks + labels -----------
const AXIS_COLOR = t.inkSoft;
const xTick = (xMax - xMin) * 0.35;
const yTick = (yMax - yMin) * 0.35;
const zTick = (zMax - zMin) * 0.35;
const axisElements = [];

function axisLine(p1, p2) {
  const a = toPixel(...p1);
  const b = toPixel(...p2);
  axisElements.push({
    type: "line",
    shape: { x1: a.px, y1: a.py, x2: b.px, y2: b.py },
    style: { stroke: AXIS_COLOR, lineWidth: 2 },
    silent: true,
  });
}

function tickMark(base, outward) {
  const a = toPixel(...base);
  const b = toPixel(...outward);
  axisElements.push({
    type: "line",
    shape: { x1: a.px, y1: a.py, x2: b.px, y2: b.py },
    style: { stroke: AXIS_COLOR, lineWidth: 2 },
    silent: true,
  });
}

function tickLabel(pos, text) {
  const p = toPixel(...pos);
  axisElements.push({
    type: "text",
    style: {
      text,
      x: p.px,
      y: p.py,
      fill: t.inkSoft,
      fontSize: 13,
      align: "center",
      verticalAlign: "middle",
    },
    silent: true,
  });
}

function axisTitle(pos, text, pixelOffset) {
  const p = toPixel(...pos);
  axisElements.push({
    type: "text",
    style: {
      text,
      x: p.px + pixelOffset[0],
      y: p.py + pixelOffset[1],
      fill: t.ink,
      fontSize: 17,
      fontWeight: "bold",
      align: "center",
      verticalAlign: "middle",
    },
    silent: true,
  });
}

axisLine([xMin, CORNER_X, zMin], [xMax, CORNER_X, zMin]);
[xMin, (xMin + xMax) / 2, xMax].forEach((v) => {
  tickMark([v, CORNER_X, zMin], [v, CORNER_X + xTick, zMin]);
  tickLabel([v, CORNER_X + xTick * 2.2, zMin], v.toFixed(0));
});
axisTitle([(xMin + xMax) / 2, CORNER_X + xTick * 2.2, zMin], "X", [0, 34]);

axisLine([xMax, yMin, zMin], [xMax, yMax, zMin]);
[yMin, (yMin + yMax) / 2, yMax].forEach((v) => {
  tickMark([xMax, v, zMin], [xMax + yTick, v, zMin]);
  tickLabel([xMax + yTick * 2.2, v, zMin], v.toFixed(0));
});
axisTitle([xMax + yTick * 2.2, (yMin + yMax) / 2, zMin], "Y", [34, 0]);

axisLine([Z_CORNER_X, Z_CORNER_Y, zMin], [Z_CORNER_X, Z_CORNER_Y, zMax]);
[zMin, (zMin + zMax) / 2, zMax].forEach((v) => {
  tickMark([Z_CORNER_X, Z_CORNER_Y, v], [Z_CORNER_X, Z_CORNER_Y - zTick, v]);
  tickLabel([Z_CORNER_X, Z_CORNER_Y - zTick * 2.2, v], v.toFixed(0));
});
axisTitle([Z_CORNER_X, Z_CORNER_Y, zMax], "Z", [0, -34]);

// --- Time-progression color key (imprint_seq: t=0 -> t=STEPS*DT) -----------
// Bottom-left, clear of the X/Y/Z axis frame which sits toward the right.
const KEY_X = SIDE_MARGIN;
const KEY_Y = size.height - 56;
const KEY_W = 200;
const legendElements = [
  {
    type: "text",
    style: {
      text: "time",
      x: KEY_X,
      y: KEY_Y - 20,
      fill: t.inkSoft,
      fontSize: 13,
      align: "left",
    },
    silent: true,
  },
  {
    type: "rect",
    shape: { x: KEY_X, y: KEY_Y, width: KEY_W, height: 10 },
    style: {
      fill: {
        type: "linear",
        x: 0,
        y: 0,
        x2: 1,
        y2: 0,
        colorStops: [
          { offset: 0, color: t.seq[0] },
          { offset: 1, color: t.seq[1] },
        ],
      },
    },
    silent: true,
  },
  {
    type: "text",
    style: {
      text: "t=0",
      x: KEY_X,
      y: KEY_Y + 24,
      fill: t.inkSoft,
      fontSize: 12,
      align: "left",
    },
    silent: true,
  },
  {
    type: "text",
    style: {
      text: `t=${(STEPS * DT).toFixed(0)}`,
      x: KEY_X + KEY_W,
      y: KEY_Y + 24,
      fill: t.inkSoft,
      fontSize: 12,
      align: "right",
    },
    silent: true,
  },
];

// --- Init + option -----------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "line-3d-trajectory · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  graphic: { elements: [...trajectoryElements, ...axisElements, ...legendElements] },
});
chart.on("finished", () => {
  window.__anyplotReady = true;
});
