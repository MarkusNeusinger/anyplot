// anyplot.ai
// wireframe-3d-basic: Basic 3D Wireframe Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const ELEVATION_DEG = 22; // viewing elevation above the x-y plane
const AZIMUTH_DEG = -38; // viewing azimuth around the z axis
const CAMERA_DISTANCE = 3.5; // camera distance from the scene centre, in scene radii
const AXIS_TICKS = 4; // about this many ticks per axis
const NICE_STEPS = [1, 2, 2.5, 5, 10]; // round tick step multipliers
const VIEW_PAD = 0.1; // share of the projected extent kept free around the drawing
const TICK_PX = 9; // tick mark half length
const TITLE = "wireframe-3d-basic · javascript · muix · anyplot.ai";
const TITLE_H = 80;

// Columns: set these to your data's column names
const X = "x"; // role: x
const Y = "y"; // role: y
const Z = "z = sin(x) · cos(y)"; // role: z

// Data: replace this block with your own records, one object per grid point
// The wave surface z = sin(x) · cos(y) on an evenly spaced 24 × 24 grid.
const data = (() => {
  const n = 24;
  const lo = -3.2;
  const hi = 3.2;
  const axis = Array.from({ length: n }, (_, i) => lo + ((hi - lo) * i) / (n - 1));
  return axis.flatMap((x) =>
    axis.map((y) => ({
      [X]: Math.round(x * 1e4) / 1e4,
      [Y]: Math.round(y * 1e4) / 1e4,
      [Z]: Math.round(Math.sin(x) * Math.cos(y) * 1e4) / 1e4,
    })),
  );
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[X] != null && d[Y] != null && d[Z] != null);
const xs = [...new Set(rows.map((d) => d[X]))].sort((a, b) => a - b);
const ys = [...new Set(rows.map((d) => d[Y]))].sort((a, b) => a - b);
const zAt = new Map(rows.map((d) => [`${d[X]}|${d[Y]}`, d[Z]]));
const zs = rows.map((d) => d[Z]);
const lo = [xs[0], ys[0], Math.min(...zs)];
const hi = [xs[xs.length - 1], ys[ys.length - 1], Math.max(...zs)];

// View rotation: rows of P give the screen x, the screen y (up) and the depth
// (away from the camera) of a 3D point relative to the scene centre.
const az = (AZIMUTH_DEG * Math.PI) / 180;
const el = (ELEVATION_DEG * Math.PI) / 180;
const P = [
  [Math.cos(az), -Math.sin(az), 0],
  [Math.sin(az) * Math.sin(el), Math.cos(az) * Math.sin(el), Math.cos(el)],
  [Math.sin(az) * Math.cos(el), Math.cos(az) * Math.cos(el), -Math.sin(el)],
];
const center = lo.map((v, c) => (v + hi[c]) / 2);
const camera = CAMERA_DISTANCE * 0.5 * Math.hypot(...lo.map((v, c) => hi[c] - v));

// Axis arms: x and y along the two base edges that meet at the corner nearest
// the viewer (lowest on screen), z upright at the leftmost base corner.
const baseCorners = [
  [lo[0], lo[1], lo[2]],
  [hi[0], lo[1], lo[2]],
  [lo[0], hi[1], lo[2]],
  [hi[0], hi[1], lo[2]],
];
const baseScreen = baseCorners.map((p) => P.map((r) => r.reduce((s, w, c) => s + w * (p[c] - center[c]), 0)));
const front = baseCorners[baseScreen.reduce((b, s, i) => (s[1] < baseScreen[b][1] ? i : b), 0)];
const leftmost = baseCorners[baseScreen.reduce((b, s, i) => (s[0] < baseScreen[b][0] ? i : b), 0)];
const arms = [
  { name: X, k: 0, from: [lo[0], front[1], lo[2]], to: [hi[0], front[1], lo[2]] },
  { name: Y, k: 1, from: [front[0], lo[1], lo[2]], to: [front[0], hi[1], lo[2]] },
  { name: Z, k: 2, from: leftmost, to: [leftmost[0], leftmost[1], hi[2]] },
];

// Round tick values inside each axis' extent, placed on its arm
const ticks = arms.flatMap((arm) => {
  const raw = (hi[arm.k] - lo[arm.k]) / AXIS_TICKS;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const step = NICE_STEPS.map((m) => m * magnitude).find((s) => s >= raw);
  const first = Math.ceil(lo[arm.k] / step - 1e-9) * step;
  const count = Math.floor((hi[arm.k] - first) / step + 1e-9) + 1;
  return Array.from({ length: count }, (_, i) => {
    const value = first + i * step;
    return { arm: arm.k, value, p: arm.from.map((v, c) => (c === arm.k ? value : v)) };
  });
});

// Project everything once in perspective, nearer points drawn larger: arm
// ends, ticks, then the mesh (row-major over x, then y).
const grid3d = xs.flatMap((x) => ys.map((y) => [x, y, zAt.get(`${x}|${y}`) ?? null]));
const anchors = [...arms.flatMap((a) => [a.from, a.to]), ...ticks.map((tk) => tk.p), ...grid3d];
const projected = anchors.map((p) => {
  if (p[2] == null) return null;
  const [sx, sy, depth] = P.map((r) => r.reduce((s, w, c) => s + w * (p[c] - center[c]), 0));
  return [(sx * camera) / (camera + depth), (sy * camera) / (camera + depth)];
});
const arms2d = arms.map((_, a) => [projected[2 * a], projected[2 * a + 1]]);
const ticks2d = projected.slice(2 * arms.length, 2 * arms.length + ticks.length);
const grid2d = projected.slice(2 * arms.length + ticks.length);
// Mesh lines in both directions: along x at each y, and along y at each x
const meshLines = [
  ...ys.map((_, j) => xs.map((_, i) => grid2d[i * ys.length + j])),
  ...xs.map((_, i) => ys.map((_, j) => grid2d[i * ys.length + j])),
];

const drawn = projected.filter((p) => p != null);
const sxLo = Math.min(...drawn.map((p) => p[0]));
const sxHi = Math.max(...drawn.map((p) => p[0]));
const syLo = Math.min(...drawn.map((p) => p[1]));
const syHi = Math.max(...drawn.map((p) => p[1]));
const meshPts = grid2d.filter((p) => p != null);
const meshCenter = [0, 1].map((c) => meshPts.reduce((s, p) => s + p[c], 0) / meshPts.length);
const SUBTITLE = `${xs.length} × ${ys.length} grid · perspective view from ${ELEVATION_DEG}° elevation, ${AZIMUTH_DEG}° azimuth`;

// The community package has no 3D chart: a custom layer maps the projected
// mesh onto the drawing area with one scale for both screen directions.
function WireframeLayer() {
  const { left, top, width, height } = useDrawingArea();
  const k = Math.min(width / ((sxHi - sxLo) * (1 + 2 * VIEW_PAD)), height / ((syHi - syLo) * (1 + 2 * VIEW_PAD)));
  const ox = left + width / 2 - ((sxLo + sxHi) / 2) * k;
  const oy = top + height / 2 + ((syLo + syHi) / 2) * k;
  const cx = ox + meshCenter[0] * k;
  const cy = oy - meshCenter[1] * k;

  return (
    <g>
      {meshLines.map((line, idx) => (
        <path
          key={idx}
          d={line
            .map((p, m) => (p == null ? "" : `${m === 0 || line[m - 1] == null ? "M" : "L"}${ox + p[0] * k},${oy - p[1] * k}`))
            .join("")}
          fill="none"
          stroke={t.palette[0]}
          strokeWidth={1.5}
          strokeOpacity={0.9}
          strokeLinejoin="round"
        />
      ))}
      {arms2d.map(([from, to], a) => {
        const x1 = ox + from[0] * k;
        const y1 = oy - from[1] * k;
        const x2 = ox + to[0] * k;
        const y2 = oy - to[1] * k;
        const len = Math.hypot(x2 - x1, y2 - y1) || 1;
        // unit normal to the arm, turned to point away from the mesh centre
        const flip = ((x1 + x2) / 2 - cx) * -(y2 - y1) + ((y1 + y2) / 2 - cy) * (x2 - x1) < 0 ? -1 : 1;
        const nx = (flip * -(y2 - y1)) / len;
        const ny = (flip * (x2 - x1)) / len;
        // the arm title runs along its arm and reads toward the right or upward
        const readSign = x2 - x1 - (y2 - y1) >= 0 ? 1 : -1;
        const titleDeg = (Math.atan2(readSign * (y2 - y1), readSign * (x2 - x1)) * 180) / Math.PI;
        const titleX = (x1 + x2) / 2 + nx * TICK_PX * 7.5;
        const titleY = (y1 + y2) / 2 + ny * TICK_PX * 7.5;
        return (
          <g key={arms[a].name}>
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={t.inkSoft} strokeWidth={2} />
            {ticks.map((tick, m) => {
              if (tick.arm !== arms[a].k) return null;
              const tx = ox + ticks2d[m][0] * k;
              const ty = oy - ticks2d[m][1] * k;
              return (
                <g key={tick.value}>
                  <line x1={tx} y1={ty} x2={tx + nx * TICK_PX} y2={ty + ny * TICK_PX} stroke={t.inkSoft} strokeWidth={1.5} />
                  <text x={tx + nx * TICK_PX * 2.8} y={ty + ny * TICK_PX * 2.8} dy="0.35em" textAnchor="middle" fontSize={15} fill={t.inkSoft}>
                    {Number(tick.value.toFixed(6))}
                  </text>
                </g>
              );
            })}
            <text
              x={titleX}
              y={titleY}
              transform={`rotate(${titleDeg} ${titleX} ${titleY})`}
              dy="0.35em"
              textAnchor="middle"
              fontSize={16}
              fontWeight={600}
              fill={t.ink}
            >
              {arms[a].name}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "18px 36px 0", boxSizing: "border-box", textAlign: "center" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H}
        series={[]}
        skipAnimation
        margin={{ top: 16, bottom: 24, left: 32, right: 32 }}
      >
        <WireframeLayer />
      </ChartsContainer>
    </div>
  );
}
