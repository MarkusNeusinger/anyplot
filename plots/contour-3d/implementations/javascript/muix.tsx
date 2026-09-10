// anyplot.ai
// contour-3d: 3D Contour Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 66/100 | Created: 2026-09-10

// Community @mui/x-charts has no 3D/surface primitive. A genuine surrogate
// built from real MUI X pieces: a ChartContainer with a `zAxis` piecewise
// colorMap (drives both the elevation-band fill and the PiecewiseColorLegend
// "colorbar") and a custom layer that reads the container's own xScale/yScale
// hooks to place elevation bands + marching-triangle contour lines. The
// spec's "project contours onto the base plane" note is honored by drawing a
// muted, offset echo of the same isolines beneath the crisp on-surface ones.

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsText } from "@mui/x-charts/ChartsText";
import { PiecewiseColorLegend } from "@mui/x-charts/ChartsLegend";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;

// --- Grid: deterministic chemical-process yield response surface -----------
const GRID_N = 34;
const TEMP_MIN = 150, TEMP_MAX = 250;
const PRESSURE_MIN = 10, PRESSURE_MAX = 50;

const temps = Array.from(
  { length: GRID_N },
  (_, i) => TEMP_MIN + (i / (GRID_N - 1)) * (TEMP_MAX - TEMP_MIN),
);
const pressures = Array.from(
  { length: GRID_N },
  (_, j) => PRESSURE_MIN + (j / (GRID_N - 1)) * (PRESSURE_MAX - PRESSURE_MIN),
);

// Second-order response-surface model (classic RSM form: intercept + linear +
// quadratic + interaction terms) with a mild ripple so contour bands aren't
// perfectly elliptical -- gives the surface a visible saddle/critical-point
// region, matching the spec's "optimization landscape with critical points".
function yieldAt(temp, pressure) {
  const u = (temp - 200) / 50;
  const v = (pressure - 30) / 20;
  return 90 - 15 * u * u - 20 * v * v + 8 * u * v + 3 * Math.sin(3 * u) * Math.cos(2 * v);
}

// zGrid[j][i] = yield at (temps[i], pressures[j])
const zGrid = pressures.map((p) => temps.map((temp) => yieldAt(temp, p)));
const allZ = zGrid.flat();
const zMin = Math.min(...allZ);
const zMax = Math.max(...allZ);

// --- Imprint sequential colormap (single-polarity data: t.seq = [green, blue]) -
function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function lerpChannel(a, b, ratio) {
  return Math.round(a + (b - a) * ratio);
}
function imprintSeqInterpolator(stops) {
  const [lo, hi] = stops.map(hexToRgb);
  return (position) => {
    const [r, g, b] = [0, 1, 2].map((c) => lerpChannel(lo[c], hi[c], position));
    return `rgb(${r}, ${g}, ${b})`;
  };
}
const seqColor = imprintSeqInterpolator(t.seq);

const NUM_BANDS = 8;
const bandThresholds = Array.from(
  { length: NUM_BANDS - 1 },
  (_, k) => zMin + ((k + 1) / NUM_BANDS) * (zMax - zMin),
);
const bandColors = Array.from({ length: NUM_BANDS }, (_, k) => seqColor(k / (NUM_BANDS - 1)));

// --- Marching-triangles filled-contour geometry ------------------------------
// Each grid cell is split into 4 triangles around its centroid so every
// super-level-set boundary resolves without the marching-squares saddle
// ambiguity; painting bands low-to-high (painter's algorithm) then produces
// correct filled bands regardless of how many disjoint regions a level has.
function buildTriangles() {
  const tris = [];
  for (let j = 0; j < GRID_N - 1; j += 1) {
    for (let i = 0; i < GRID_N - 1; i += 1) {
      const sw = { x: temps[i], y: pressures[j], z: zGrid[j][i] };
      const se = { x: temps[i + 1], y: pressures[j], z: zGrid[j][i + 1] };
      const ne = { x: temps[i + 1], y: pressures[j + 1], z: zGrid[j + 1][i + 1] };
      const nw = { x: temps[i], y: pressures[j + 1], z: zGrid[j + 1][i] };
      const center = {
        x: (sw.x + se.x) / 2,
        y: (sw.y + nw.y) / 2,
        z: (sw.z + se.z + ne.z + nw.z) / 4,
      };
      tris.push([sw, se, center], [se, ne, center], [ne, nw, center], [nw, sw, center]);
    }
  }
  return tris;
}
const triangles = buildTriangles();

// Filled sub-polygon(s) of one triangle lying at/above `threshold`, plus the
// interpolated edge (if any) that traces the exact level curve through it.
function triangleFill(a, b, c, threshold) {
  const inA = a.z >= threshold, inB = b.z >= threshold, inC = c.z >= threshold;
  const nIn = (inA ? 1 : 0) + (inB ? 1 : 0) + (inC ? 1 : 0);
  const cross = (p, q) => {
    const ratio = (threshold - p.z) / (q.z - p.z);
    return { x: p.x + ratio * (q.x - p.x), y: p.y + ratio * (q.y - p.y) };
  };

  if (nIn === 0) return { polys: [], cut: null };
  if (nIn === 3) return { polys: [[a, b, c]], cut: null };

  if (nIn === 1) {
    if (inA) { const ab = cross(a, b), ca = cross(c, a); return { polys: [[a, ab, ca]], cut: [ab, ca] }; }
    if (inB) { const ab = cross(a, b), bc = cross(b, c); return { polys: [[b, bc, ab]], cut: [bc, ab] }; }
    const ca = cross(c, a), bc = cross(b, c);
    return { polys: [[c, ca, bc]], cut: [ca, bc] };
  }

  // nIn === 2 (exactly one vertex out)
  if (!inC) { const bc = cross(b, c), ca = cross(c, a); return { polys: [[a, b, bc, ca]], cut: [ca, bc] }; }
  if (!inA) { const ca = cross(c, a), ab = cross(a, b); return { polys: [[b, c, ca, ab]], cut: [ab, ca] }; }
  const ab = cross(a, b), bc = cross(b, c);
  return { polys: [[c, a, ab, bc]], cut: [bc, ab] };
}

// Bands k=1..NUM_BANDS-1 are computed from the triangulation; band k=0 is the
// full domain rect (everything is above zMin), painted first as the base layer.
const bandGeometry = [];
const isolineGeometry = [];
for (let k = 1; k < NUM_BANDS; k += 1) {
  const threshold = bandThresholds[k - 1];
  const polys = [];
  const segments = [];
  for (const tri of triangles) {
    const { polys: p, cut } = triangleFill(tri[0], tri[1], tri[2], threshold);
    if (p.length) polys.push(...p);
    if (cut) segments.push(cut);
  }
  bandGeometry.push(polys);
  isolineGeometry.push(segments);
}

// --- Custom SVG layer: bands + isolines, mapped through the chart's own scales -
const PROJECTION_OFFSET = 14;

function ContourLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const toSVG = (x, y) => [xScale(x), yScale(y)];

  const polysToPath = (polys) =>
    polys
      .map((poly) => {
        const pts = poly.map((p) => toSVG(p.x, p.y));
        const head = `M ${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
        const tail = pts.slice(1).map(([px, py]) => `L ${px.toFixed(1)},${py.toFixed(1)}`).join(" ");
        return `${head} ${tail} Z`;
      })
      .join(" ");

  const segmentsToPath = (segments, dx = 0, dy = 0) =>
    segments
      .map(([p0, p1]) => {
        const [x0, y0] = toSVG(p0.x, p0.y);
        const [x1, y1] = toSVG(p1.x, p1.y);
        return `M ${(x0 + dx).toFixed(1)},${(y0 + dy).toFixed(1)} L ${(x1 + dx).toFixed(1)},${(y1 + dy).toFixed(1)}`;
      })
      .join(" ");

  const [rx0, ry0] = toSVG(TEMP_MIN, PRESSURE_MIN);
  const [rx1, ry1] = toSVG(TEMP_MAX, PRESSURE_MAX);
  const baseRect = `M ${rx0.toFixed(1)},${ry0.toFixed(1)} L ${rx1.toFixed(1)},${ry0.toFixed(1)} L ${rx1.toFixed(1)},${ry1.toFixed(1)} L ${rx0.toFixed(1)},${ry1.toFixed(1)} Z`;

  return (
    <g>
      {/* Elevation bands: the surface viewed from directly above */}
      <path d={baseRect} fill={bandColors[0]} stroke={bandColors[0]} strokeWidth={0.75} />
      {bandGeometry.map((polys, idx) => (
        <path
          key={`band-${idx}`}
          d={polysToPath(polys)}
          fill={bandColors[idx + 1]}
          stroke={bandColors[idx + 1]}
          strokeWidth={0.75}
        />
      ))}

      {/* Contours projected onto the base plane: same level curves, offset + dashed + muted */}
      <g opacity={0.55}>
        {isolineGeometry.map((segments, idx) => (
          <path
            key={`proj-${idx}`}
            d={segmentsToPath(segments, PROJECTION_OFFSET, PROJECTION_OFFSET)}
            stroke={t.inkSoft}
            strokeWidth={1.1}
            strokeDasharray="6 5"
            fill="none"
          />
        ))}
      </g>

      {/* Solid contour lines on the surface itself */}
      {isolineGeometry.map((segments, idx) => (
        <path
          key={`iso-${idx}`}
          d={segmentsToPath(segments)}
          stroke={t.ink}
          strokeOpacity={0.6}
          strokeWidth={1.5}
          fill="none"
        />
      ))}
    </g>
  );
}

// --- Chart (default-exported component — the harness mounts it) -------------
const TITLE = "contour-3d · javascript · muix · anyplot.ai";
const MARGIN = { top: 120, right: 190, bottom: 90, left: 105 };

// PiecewiseColorLegend anchors flush against the literal SVG width, ignoring
// MARGIN.right entirely (its `position: "right"` offset is `svgWidth -
// legendWidth`) -- so the whole right-side cluster (legend + its rotated axis
// title) is wrapped in this leftward shift to keep swatches off the true edge.
const RIGHT_EDGE_INSET = 46;

function bandLabel({ min, max }) {
  if (min === null) return `< ${Math.round(max)}`;
  if (max === null) return `> ${Math.round(min)}`;
  return `${Math.round(min)}–${Math.round(max)}`;
}

export default function Chart() {
  return (
    <ChartContainer
      width={SIZE.width}
      height={SIZE.height}
      series={[]}
      margin={MARGIN}
      skipAnimation
      xAxis={[
        {
          scaleType: "linear",
          min: TEMP_MIN,
          max: TEMP_MAX,
          label: "Temperature (°C)",
          labelStyle: { fontSize: 15, fill: t.ink },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        },
      ]}
      yAxis={[
        {
          scaleType: "linear",
          min: PRESSURE_MIN,
          max: PRESSURE_MAX,
          label: "Pressure (bar)",
          labelStyle: { fontSize: 15, fill: t.ink },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          slotProps: { axisLabel: { x: -58 } },
        },
      ]}
      zAxis={[
        {
          colorMap: {
            type: "piecewise",
            thresholds: bandThresholds,
            colors: bandColors,
          },
        },
      ]}
    >
      <ContourLayer />
      <ChartsXAxis />
      <ChartsYAxis />
      <g transform={`translate(${-RIGHT_EDGE_INSET}, 0)`}>
        <PiecewiseColorLegend
          position={{ horizontal: "right", vertical: "middle" }}
          direction="column"
          labelStyle={{ fontSize: 13, fill: t.inkSoft }}
          labelFormatter={bandLabel}
        />
        <ChartsText
          text="Yield (%)"
          x={SIZE.width - 40}
          y={MARGIN.top - 24}
          style={{ fontSize: 14, fontWeight: 500, fill: t.ink, textAnchor: "middle" }}
        />
      </g>
      <ChartsText
        text={TITLE}
        x={SIZE.width / 2}
        y={50}
        style={{ fontSize: 22, fontWeight: 500, fill: t.ink, textAnchor: "middle" }}
      />
    </ChartContainer>
  );
}
