// anyplot.ai
// line-3d-trajectory: 3D Line Plot for Trajectory Visualization
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-10
//# anyplot-orientation: landscape
// anyplot.ai
// line-3d-trajectory: 3D Line Plot for Trajectory Visualization
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-10

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// --- Data: Lorenz attractor, two trajectories from nearly identical initial
// conditions — the classic demonstration of chaotic sensitivity to initial
// conditions ("butterfly effect"), integrated with RK4. ---------------------
const SIGMA = 10;
const RHO = 28;
const BETA = 8 / 3;
const DT = 0.01;
const STEPS = 4000; // 40 time units — long enough for the two trajectories to
const TRANSIENT = 400; // switch attractor wings at different moments
const SUBSAMPLE = 2; // effective 0.02 step keeps the tight loops smooth

function lorenzDerivative(state: number[]) {
  const [x, y, z] = state;
  return [SIGMA * (y - x), x * (RHO - z) - y, x * y - BETA * z];
}

function rk4Step(state: number[], dt: number) {
  const k1 = lorenzDerivative(state);
  const k2 = lorenzDerivative(state.map((v, i) => v + (dt / 2) * k1[i]));
  const k3 = lorenzDerivative(state.map((v, i) => v + (dt / 2) * k2[i]));
  const k4 = lorenzDerivative(state.map((v, i) => v + dt * k3[i]));
  return state.map((v, i) => v + (dt / 6) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]));
}

function simulate(initial: number[]) {
  let state = initial;
  const points: number[][] = [];
  for (let i = 0; i < STEPS; i++) {
    state = rk4Step(state, DT);
    if (i >= TRANSIENT && (i - TRANSIENT) % SUBSAMPLE === 0) points.push(state.slice());
  }
  return points;
}

const trajectoryA = simulate([0.1, 0, 0]);
const trajectoryB = simulate([0.1001, 0, 0]); // perturbed by 0.0001 in x

// --- Normalize to a unit cube so the isometric projection treats every axis
// equivalently, then project 3D -> 2D with a fixed camera angle (elevation
// 20°, azimuth 32°) — the same technique a static mplot3d render uses. ------
const allPoints = [...trajectoryA, ...trajectoryB];
const X_MIN = Math.min(...allPoints.map((p) => p[0]));
const X_MAX = Math.max(...allPoints.map((p) => p[0]));
const Y_MIN = Math.min(...allPoints.map((p) => p[1]));
const Y_MAX = Math.max(...allPoints.map((p) => p[1]));
const Z_MIN = Math.min(...allPoints.map((p) => p[2]));
const Z_MAX = Math.max(...allPoints.map((p) => p[2]));

function normalize(p: number[]) {
  return [
    (2 * (p[0] - X_MIN)) / (X_MAX - X_MIN) - 1,
    (2 * (p[1] - Y_MIN)) / (Y_MAX - Y_MIN) - 1,
    (2 * (p[2] - Z_MIN)) / (Z_MAX - Z_MIN) - 1,
  ];
}

const ELEV = (20 * Math.PI) / 180;
const AZIM = (32 * Math.PI) / 180;

function projectUnit(x: number, y: number, z: number) {
  const xRot = x * Math.cos(AZIM) - y * Math.sin(AZIM);
  const yRot = x * Math.sin(AZIM) + y * Math.cos(AZIM);
  return { sx: xRot, sy: yRot * Math.sin(ELEV) + z * Math.cos(ELEV) };
}

function project(p: number[]) {
  const [x, y, z] = normalize(p);
  return projectUnit(x, y, z);
}

const projectedA = trajectoryA.map(project);
const projectedB = trajectoryB.map(project);
const allProjected = [...projectedA, ...projectedB];

const SX_MIN = Math.min(...allProjected.map((p) => p.sx));
const SX_MAX = Math.max(...allProjected.map((p) => p.sx));
const SY_MIN = Math.min(...allProjected.map((p) => p.sy));
const SY_MAX = Math.max(...allProjected.map((p) => p.sy));
const PAD_X = (SX_MAX - SX_MIN) * 0.08;
const PAD_Y = (SY_MAX - SY_MIN) * 0.12;

const TITLE_H = 60;
const FONT = "Inter, system-ui, sans-serif";

// --- Custom overlay: MUI X's built-in series don't cover 3D paths, so we
// project the trajectories ourselves and paint them as plain SVG inside the
// ChartContainer's drawing area — the composition pattern MUI X documents
// for chart types outside the built-in series set. --------------------------
function Trajectories() {
  const { left, top, width, height: areaHeight } = useDrawingArea();
  const xOf = (sx: number) => left + ((sx - (SX_MIN - PAD_X)) / (SX_MAX + PAD_X - (SX_MIN - PAD_X))) * width;
  const yOf = (sy: number) =>
    top + areaHeight - ((sy - (SY_MIN - PAD_Y)) / (SY_MAX + PAD_Y - (SY_MIN - PAD_Y))) * areaHeight;

  const toPolyline = (pts: { sx: number; sy: number }[]) => pts.map((p) => `${xOf(p.sx)},${yOf(p.sy)}`).join(" ");

  const startPx = { x: xOf(projectedA[0].sx), y: yOf(projectedA[0].sy) };

  // Small axis-orientation gizmo fixed near the corner — a bounding-box axis
  // frame would fight the attractor's irregular, self-crossing shape.
  const gizmoOrigin = { x: left + 66, y: top + areaHeight - 60 };
  const ARM = 60;
  const gizmoAxes = [
    { dir: projectUnit(1, 0, 0), label: "X" },
    { dir: projectUnit(0, 1, 0), label: "Y" },
    { dir: projectUnit(0, 0, 1), label: "Z" },
  ];

  return (
    <g>
      <polyline points={toPolyline(projectedA)} fill="none" stroke={t.palette[0]} strokeWidth={2} opacity={0.9} />
      <polyline points={toPolyline(projectedB)} fill="none" stroke={t.palette[1]} strokeWidth={2} opacity={0.9} />
      <circle cx={startPx.x} cy={startPx.y} r={6} fill={t.ink} />
      <text x={startPx.x + 12} y={startPx.y - 12} fill={t.inkSoft} style={{ fontSize: 14, fontFamily: FONT }}>
        shared start
      </text>

      {gizmoAxes.map((a) => {
        const tip = { x: gizmoOrigin.x + a.dir.sx * ARM, y: gizmoOrigin.y - a.dir.sy * ARM };
        return (
          <g key={a.label}>
            <line
              x1={gizmoOrigin.x}
              y1={gizmoOrigin.y}
              x2={tip.x}
              y2={tip.y}
              stroke={t.inkSoft}
              strokeWidth={2}
            />
            <text
              x={gizmoOrigin.x + a.dir.sx * (ARM + 20)}
              y={gizmoOrigin.y - a.dir.sy * (ARM + 20)}
              fill={t.inkSoft}
              textAnchor="middle"
              style={{ fontSize: 15, fontWeight: 600, fontFamily: FONT }}
            >
              {a.label}
            </text>
          </g>
        );
      })}

      <g transform={`translate(${left + width - 300}, ${top + 6})`}>
        <rect x={0} y={0} width={14} height={14} fill={t.palette[0]} />
        <text x={20} y={12} fill={t.inkSoft} style={{ fontSize: 14, fontFamily: FONT }}>
          Trajectory A · x₀ = 0.1000
        </text>
        <rect x={0} y={24} width={14} height={14} fill={t.palette[1]} />
        <text x={20} y={36} fill={t.inkSoft} style={{ fontSize: 14, fontFamily: FONT }}>
          Trajectory B · x₀ = 0.1001
        </text>
      </g>
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  return (
    <div
      style={{
        width: W,
        height: H,
        background: t.pageBg,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div style={{ height: TITLE_H, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          line-3d-trajectory · javascript · muix · anyplot.ai
        </span>
      </div>
      <ChartContainer
        width={W}
        height={H - TITLE_H}
        skipAnimation
        series={[]}
        xAxis={[{ min: 0, max: 1 }]}
        yAxis={[{ min: 0, max: 1 }]}
        margin={{ top: 20, bottom: 30, left: 30, right: 30 }}
      >
        <Trajectories />
      </ChartContainer>
    </div>
  );
}
