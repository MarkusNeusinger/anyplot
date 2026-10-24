// anyplot.ai
// line-3d-trajectory: 3D Line Plot for Trajectory Visualization
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-10

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = '"Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, sans-serif';
const MONO = '"JetBrains Mono", "SFMono-Regular", Menlo, monospace';
const ELEV_DEG = 20;
const AZIM_DEG = 32;
const ELEV_RAD = (ELEV_DEG * Math.PI) / 180;
const AZIM_RAD = (AZIM_DEG * Math.PI) / 180;
const COS_AZ = Math.cos(AZIM_RAD);
const SIN_AZ = Math.sin(AZIM_RAD);
const COS_EL = Math.cos(ELEV_RAD);
const SIN_EL = Math.sin(ELEV_RAD);
const PAD_X_SHARE = 0.12;
const PAD_Y_SHARE = 0.14;

// Columns: set these to your data's column names
const X = "Convection rate (X)"; // role: x
const Y = "Horizontal temp var (Y)"; // role: y
const Z = "Vertical temp var (Z)"; // role: z
const TRAJECTORY = "Trajectory"; // role: color

// Data: replace this block with your own records
const SIGMA = 10;
const RHO = 28;
const BETA = 8 / 3;
const DT = 0.01;
const STEPS = 4000;
const TRANSIENT = 400;
const SUBSAMPLE = 2;

const INITIAL_STATES: Array<{ label: string; init: [number, number, number] }> = [
  { label: "Trajectory A (x₀ = 0.1000)", init: [0.1, 0, 0] },
  { label: "Trajectory B (x₀ = 0.1001)", init: [0.1001, 0, 0] },
];

const data: Array<{
  [TRAJECTORY]: string;
  [X]: number;
  [Y]: number;
  [Z]: number;
}> = [];

for (let s = 0; s < INITIAL_STATES.length; s += 1) {
  const { label, init } = INITIAL_STATES[s];
  let x = init[0];
  let y = init[1];
  let z = init[2];

  for (let i = 0; i < STEPS; i += 1) {
    const k1x = SIGMA * (y - x);
    const k1y = x * (RHO - z) - y;
    const k1z = x * y - BETA * z;

    const x2 = x + 0.5 * DT * k1x;
    const y2 = y + 0.5 * DT * k1y;
    const z2 = z + 0.5 * DT * k1z;
    const k2x = SIGMA * (y2 - x2);
    const k2y = x2 * (RHO - z2) - y2;
    const k2z = x2 * y2 - BETA * z2;

    const x3 = x + 0.5 * DT * k2x;
    const y3 = y + 0.5 * DT * k2y;
    const z3 = z + 0.5 * DT * k2z;
    const k3x = SIGMA * (y3 - x3);
    const k3y = x3 * (RHO - z3) - y3;
    const k3z = x3 * y3 - BETA * z3;

    const x4 = x + DT * k3x;
    const y4 = y + DT * k3y;
    const z4 = z + DT * k3z;
    const k4x = SIGMA * (y4 - x4);
    const k4y = x4 * (RHO - z4) - y4;
    const k4z = x4 * y4 - BETA * z4;

    x += (DT / 6) * (k1x + 2 * k2x + 2 * k3x + k4x);
    y += (DT / 6) * (k1y + 2 * k2y + 2 * k3y + k4y);
    z += (DT / 6) * (k1z + 2 * k2z + 2 * k3z + k4z);

    if (i >= TRANSIENT && (i - TRANSIENT) % SUBSAMPLE === 0) {
      data.push({
        [TRAJECTORY]: label,
        [X]: x,
        [Y]: y,
        [Z]: z,
      });
    }
  }
}

// Plot: reads only data and the constants above
const trajectoryNames = Array.from(
  new Set(data.map((d) => d[TRAJECTORY])),
);

const allX = data.map((d) => d[X]);
const allY = data.map((d) => d[Y]);
const allZ = data.map((d) => d[Z]);
const X_MIN = Math.min(...allX);
const X_MAX = Math.max(...allX);
const Y_MIN = Math.min(...allY);
const Y_MAX = Math.max(...allY);
const Z_MIN = Math.min(...allZ);
const Z_MAX = Math.max(...allZ);

interface ProjectedTrajectory {
  name: string;
  color: string;
  points: Array<{ sx: number; sy: number }>;
}

const projectedTrajectories: ProjectedTrajectory[] = [];
const allScreenPts: Array<{ sx: number; sy: number }> = [];

for (let idx = 0; idx < trajectoryNames.length; idx += 1) {
  const name = trajectoryNames[idx];
  const rows = data.filter((d) => d[TRAJECTORY] === name);
  const pts: Array<{ sx: number; sy: number }> = [];
  for (let i = 0; i < rows.length; i += 1) {
    const r = rows[i];
    const nx = (2 * (r[X] - X_MIN)) / (X_MAX - X_MIN) - 1;
    const ny = (2 * (r[Y] - Y_MIN)) / (Y_MAX - Y_MIN) - 1;
    const nz = (2 * (r[Z] - Z_MIN)) / (Z_MAX - Z_MIN) - 1;
    const xRot = nx * COS_AZ - ny * SIN_AZ;
    const yRot = nx * SIN_AZ + ny * COS_AZ;
    const sx = xRot;
    const sy = yRot * SIN_EL + nz * COS_EL;
    pts.push({ sx, sy });
    allScreenPts.push({ sx, sy });
  }
  projectedTrajectories.push({
    name,
    color: t.palette[idx],
    points: pts,
  });
}

// Project 3D bounding cube corners to include them in screen bounds
const cubeCorners: Array<[number, number, number]> = [
  [-1, -1, -1],
  [1, -1, -1],
  [1, 1, -1],
  [-1, 1, -1],
  [-1, -1, 1],
  [-1, 1, 1],
  [1, 1, 1],
];
const projectedCube = cubeCorners.map(([nx, ny, nz]) => {
  const xRot = nx * COS_AZ - ny * SIN_AZ;
  const yRot = nx * SIN_AZ + ny * COS_AZ;
  return { sx: xRot, sy: yRot * SIN_EL + nz * COS_EL };
});
for (let i = 0; i < projectedCube.length; i += 1) {
  allScreenPts.push(projectedCube[i]);
}

const SX_MIN = Math.min(...allScreenPts.map((p) => p.sx));
const SX_MAX = Math.max(...allScreenPts.map((p) => p.sx));
const SY_MIN = Math.min(...allScreenPts.map((p) => p.sy));
const SY_MAX = Math.max(...allScreenPts.map((p) => p.sy));
const PAD_X = (SX_MAX - SX_MIN) * PAD_X_SHARE;
const PAD_Y = (SY_MAX - SY_MIN) * PAD_Y_SHARE;
const DOM_X0 = SX_MIN - PAD_X;
const DOM_X1 = SX_MAX + PAD_X;
const DOM_Y0 = SY_MIN - PAD_Y;
const DOM_Y1 = SY_MAX + PAD_Y;

const gizmoAxes = [
  {
    label: "X",
    sx: 1 * COS_AZ - 0 * SIN_AZ,
    sy: (1 * SIN_AZ + 0 * COS_AZ) * SIN_EL + 0 * COS_EL,
  },
  {
    label: "Y",
    sx: 0 * COS_AZ - 1 * SIN_AZ,
    sy: (0 * SIN_AZ + 1 * COS_AZ) * SIN_EL + 0 * COS_EL,
  },
  {
    label: "Z",
    sx: 0,
    sy: COS_EL,
  },
];

function TrajectoriesLayer() {
  const { left, top, width, height: areaHeight } = useDrawingArea();

  const xDomSpan = DOM_X1 - DOM_X0;
  const yDomSpan = DOM_Y1 - DOM_Y0;
  const scale = Math.min(width / xDomSpan, areaHeight / yDomSpan);
  const offsetX = left + (width - xDomSpan * scale) / 2;
  const offsetY = top + (areaHeight - yDomSpan * scale) / 2;

  const c0 = {
    x: offsetX + (projectedCube[0].sx - DOM_X0) * scale,
    y: offsetY + (DOM_Y1 - projectedCube[0].sy) * scale,
  };
  const c1 = {
    x: offsetX + (projectedCube[1].sx - DOM_X0) * scale,
    y: offsetY + (DOM_Y1 - projectedCube[1].sy) * scale,
  };
  const c2 = {
    x: offsetX + (projectedCube[2].sx - DOM_X0) * scale,
    y: offsetY + (DOM_Y1 - projectedCube[2].sy) * scale,
  };
  const c3 = {
    x: offsetX + (projectedCube[3].sx - DOM_X0) * scale,
    y: offsetY + (DOM_Y1 - projectedCube[3].sy) * scale,
  };
  const c5 = {
    x: offsetX + (projectedCube[5].sx - DOM_X0) * scale,
    y: offsetY + (DOM_Y1 - projectedCube[5].sy) * scale,
  };
  const c6 = {
    x: offsetX + (projectedCube[6].sx - DOM_X0) * scale,
    y: offsetY + (DOM_Y1 - projectedCube[6].sy) * scale,
  };

  const firstPt = projectedTrajectories[0].points[0];
  const startsClose =
    projectedTrajectories.length > 1 &&
    projectedTrajectories.every(
      (tr) =>
        Math.hypot(tr.points[0].sx - firstPt.sx, tr.points[0].sy - firstPt.sy) <
        0.02,
    );
  const startPx = {
    x: offsetX + (firstPt.sx - DOM_X0) * scale,
    y: offsetY + (DOM_Y1 - firstPt.sy) * scale,
  };
  const labelAnchor = { x: c3.x + 156, y: c5.y + 44 };
  const gizmoOrigin = { x: left + 108, y: top + areaHeight - 78 };
  const ARM = 58;

  return (
    <g>
      {/* 3D floor and back-wall reference wireframe */}
      <polygon
        points={`${c0.x},${c0.y} ${c1.x},${c1.y} ${c2.x},${c2.y} ${c3.x},${c3.y}`}
        fill={t.elevatedBg}
        fillOpacity={0.35}
        stroke={t.grid}
        strokeWidth={1.2}
      />
      <polygon
        points={`${c3.x},${c3.y} ${c2.x},${c2.y} ${c6.x},${c6.y} ${c5.x},${c5.y}`}
        fill={t.elevatedBg}
        fillOpacity={0.18}
        stroke={t.grid}
        strokeWidth={1.2}
        strokeDasharray="4 4"
      />
      <line
        x1={c0.x}
        y1={c0.y}
        x2={c3.x}
        y2={c3.y}
        stroke={t.grid}
        strokeWidth={1.2}
      />

      {/* Labeled outer 3D axis edges (never crossing trajectories) */}
      <line
        x1={c0.x}
        y1={c0.y}
        x2={c1.x}
        y2={c1.y}
        stroke={t.inkSoft}
        strokeWidth={2}
      />
      <text
        x={(c0.x + c1.x) / 2 + 12}
        y={(c0.y + c1.y) / 2 + 28}
        fill={t.ink}
        fontSize={14}
        fontWeight={600}
        textAnchor="middle"
      >
        {X} [{X_MIN.toFixed(0)} to +{X_MAX.toFixed(0)}]
      </text>

      <line
        x1={c1.x}
        y1={c1.y}
        x2={c2.x}
        y2={c2.y}
        stroke={t.inkSoft}
        strokeWidth={2}
      />
      <text
        x={(c1.x + c2.x) / 2 + 22}
        y={(c1.y + c2.y) / 2 - 6}
        fill={t.ink}
        fontSize={14}
        fontWeight={600}
        textAnchor="start"
      >
        {Y} [{Y_MIN.toFixed(0)} to +{Y_MAX.toFixed(0)}]
      </text>

      <line
        x1={c3.x}
        y1={c3.y}
        x2={c5.x}
        y2={c5.y}
        stroke={t.inkSoft}
        strokeWidth={2}
      />
      <text
        x={c3.x - 16}
        y={(c3.y + c5.y) / 2}
        fill={t.ink}
        fontSize={14}
        fontWeight={600}
        textAnchor="end"
        dominantBaseline="middle"
      >
        {Z} [{Z_MIN.toFixed(0)} to {Z_MAX.toFixed(0)}]
      </text>

      {/* Trajectories */}
      {projectedTrajectories.map((traj) => {
        const poly = traj.points
          .map(
            (p) =>
              `${(offsetX + (p.sx - DOM_X0) * scale).toFixed(1)},${(
                offsetY +
                (DOM_Y1 - p.sy) * scale
              ).toFixed(1)}`,
          )
          .join(" ");
        const endPt = traj.points[traj.points.length - 1];
        const endX = offsetX + (endPt.sx - DOM_X0) * scale;
        const endY = offsetY + (DOM_Y1 - endPt.sy) * scale;

        return (
          <g key={traj.name}>
            <polyline
              points={poly}
              fill="none"
              stroke={traj.color}
              strokeWidth={1.65}
              opacity={0.62}
            />
            <circle
              cx={endX}
              cy={endY}
              r={5}
              fill={traj.color}
              stroke={t.pageBg}
              strokeWidth={1.5}
            />
          </g>
        );
      })}

      {/* Start marker and conditional shared-start callout */}
      {startsClose ? (
        <g>
          <circle
            cx={startPx.x}
            cy={startPx.y}
            r={6.5}
            fill={t.ink}
            stroke={t.pageBg}
            strokeWidth={1.5}
          />
          <line
            x1={startPx.x}
            y1={startPx.y}
            x2={labelAnchor.x + 8}
            y2={labelAnchor.y + 4}
            stroke={t.inkSoft}
            strokeWidth={1.3}
            strokeDasharray="4 3"
            opacity={0.8}
          />
          <text
            x={labelAnchor.x}
            y={labelAnchor.y}
            fill={t.ink}
            fontSize={14}
            fontWeight={600}
            fontFamily={MONO}
            textAnchor="end"
          >
            Shared start
          </text>
        </g>
      ) : (
        projectedTrajectories.map((traj) => {
          const s0 = traj.points[0];
          return (
            <circle
              key={`start-${traj.name}`}
              cx={offsetX + (s0.sx - DOM_X0) * scale}
              cy={offsetY + (DOM_Y1 - s0.sy) * scale}
              r={5}
              fill={t.ink}
              stroke={traj.color}
              strokeWidth={2}
            />
          );
        })
      )}

      {/* 3D orientation triad gizmo */}
      {gizmoAxes.map((a) => {
        const tipX = gizmoOrigin.x + a.sx * ARM;
        const tipY = gizmoOrigin.y - a.sy * ARM;
        return (
          <g key={a.label}>
            <line
              x1={gizmoOrigin.x}
              y1={gizmoOrigin.y}
              x2={tipX}
              y2={tipY}
              stroke={t.inkSoft}
              strokeWidth={2}
            />
            <text
              x={gizmoOrigin.x + a.sx * (ARM + 18)}
              y={gizmoOrigin.y - a.sy * (ARM + 18)}
              fill={t.ink}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={15}
              fontWeight={700}
            >
              {a.label}
            </text>
          </g>
        );
      })}
      <text
        x={gizmoOrigin.x}
        y={gizmoOrigin.y + 24}
        fill={t.inkSoft}
        textAnchor="middle"
        fontSize={14}
        fontFamily={MONO}
      >
        elev {ELEV_DEG}°, azim {AZIM_DEG}°
      </text>
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const HEADER_H = 84;
  const chartH = H - HEADER_H;

  return (
    <div
      style={{
        width: W,
        height: H,
        background: t.pageBg,
        color: t.ink,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          padding: "14px 44px 4px 44px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          boxSizing: "border-box",
        }}
      >
        <div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: t.ink,
              lineHeight: 1.2,
            }}
          >
            line-3d-trajectory · javascript · muix · anyplot.ai
          </div>
          <div
            style={{
              fontSize: 14,
              color: t.inkSoft,
              marginTop: 4,
              fontFamily: MONO,
            }}
          >
            {projectedTrajectories.length} trajectories ·{" "}
            {projectedTrajectories[0].points.length.toLocaleString()} points per
            trajectory ({X}, {Y}, {Z})
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 24,
            fontSize: 15,
            color: t.ink,
          }}
        >
          {projectedTrajectories.map((traj) => (
            <div
              key={traj.name}
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <span
                style={{
                  width: 22,
                  height: 3,
                  borderRadius: 2,
                  background: traj.color,
                  display: "inline-block",
                }}
              />
              <span>{traj.name}</span>
            </div>
          ))}
        </div>
      </div>

      <ChartsContainer
        width={W}
        height={chartH}
        skipAnimation
        series={[]}
        xAxis={[{ min: 0, max: 1, position: "none" }]}
        yAxis={[{ min: 0, max: 1, position: "none" }]}
        margin={{ top: 12, bottom: 24, left: 32, right: 32 }}
      >
        <TrajectoriesLayer />
      </ChartsContainer>
    </div>
  );
}
