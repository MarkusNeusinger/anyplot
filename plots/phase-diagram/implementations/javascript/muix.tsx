// anyplot.ai
// phase-diagram: Phase Diagram (State Space Plot)
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 84/100 | Updated: 2026-10-23

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsText } from "@mui/x-charts/ChartsText";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const X = "Position x"; // role: x
const DX_DT = "Velocity dx/dt"; // role: dx_dt
const TIME = "Time t"; // role: t
const TRAJECTORY = "Trajectory"; // role: extra

// Data: replace this block with your own records, one object per row
const data = (() => {
  const omega = 1; // natural frequency, rad/s
  const zeta = 0.15; // damping ratio (< 1 -> underdamped, spirals to the origin)
  const omegaD = omega * Math.sqrt(1 - zeta * zeta);
  const steps = 360;
  const tMax = (4.5 * 2 * Math.PI) / omegaD;
  const initials = [
    [2.2, 0],
    [-2.0, 0.6],
    [0, 2.6],
    [1.3, -2.0],
  ];

  const rows: {
    [TRAJECTORY]: string;
    [TIME]: number;
    [X]: number;
    [DX_DT]: number;
  }[] = [];

  for (const [x0, v0] of initials) {
    const label = `x₀=${x0}, v₀=${v0}`;
    const A = x0;
    const B = (v0 + zeta * omega * A) / omegaD;
    for (let i = 0; i <= steps; i++) {
      const time = (i / steps) * tMax;
      const decay = Math.exp(-zeta * omega * time);
      const cosTerm = Math.cos(omegaD * time);
      const sinTerm = Math.sin(omegaD * time);
      const xVal = decay * (A * cosTerm + B * sinTerm);
      const vVal =
        decay *
        (-zeta * omega * (A * cosTerm + B * sinTerm) +
          omegaD * (-A * sinTerm + B * cosTerm));
      rows.push({
        [TRAJECTORY]: label,
        [TIME]: time,
        [X]: xVal,
        [DX_DT]: vVal,
      });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const trajectoryLabels = Array.from(new Set(data.map((d) => d[TRAJECTORY])));
const trajectories = trajectoryLabels.map((label, i) => {
  // Time order, not row order, decides the path and the direction arrows.
  const pts = data
    .filter((d) => d[TRAJECTORY] === label)
    .sort((a, b) => a[TIME] - b[TIME]);
  return {
    axisId: `x-axis-${i}`,
    color: t.palette[i],
    label,
    x: pts.map((d) => d[X]),
    v: pts.map((d) => d[DX_DT]),
  };
});

const allX = data.map((d) => d[X]);
const allV = data.map((d) => d[DX_DT]);
const xSpan = Math.max(...allX) - Math.min(...allX);
const vSpan = Math.max(...allV) - Math.min(...allV);
const X_MIN = Math.min(...allX) - xSpan * 0.12;
const X_MAX = Math.max(...allX) + xSpan * 0.12;
const V_MIN = Math.min(...allV) - vSpan * 0.12;
const V_MAX = Math.max(...allV) + vSpan * 0.12;

const TITLE =
  "Damped Oscillator · phase-diagram · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 70;
const TITLE_FONT_SIZE = Math.max(
  15,
  Math.round(22 * Math.min(1, 67 / TITLE.length)),
);

const MARGIN = { top: 30, bottom: 20, left: 46, right: 60 };

const ARROW_FRACTIONS = [0.08, 0.24, 0.44, 0.68];
const ARROW_TANGENT_STEP = 2;
const ARROW_SIZE = 9;
const ARROW_SPREAD = 0.5;

function arrowPoints(cx: number, cy: number, angle: number, size: number) {
  const backAngle = angle + Math.PI;
  const tip = [cx + Math.cos(angle) * size, cy + Math.sin(angle) * size];
  const left = [
    cx + Math.cos(backAngle - ARROW_SPREAD) * size,
    cy + Math.sin(backAngle - ARROW_SPREAD) * size,
  ];
  const right = [
    cx + Math.cos(backAngle + ARROW_SPREAD) * size,
    cy + Math.sin(backAngle + ARROW_SPREAD) * size,
  ];
  return `${tip.join(",")} ${left.join(",")} ${right.join(",")}`;
}

function PhaseMarkers() {
  const yScale = useYScale();
  const xScale = useXScale(trajectories[0].axisId);

  const origin = { x: xScale(0)!, y: yScale(0)! };

  return (
    <g>
      {trajectories.map((traj) => {
        const maxIdx = traj.x.length - 1;
        const start = { x: xScale(traj.x[0])!, y: yScale(traj.v[0])! };
        return (
          <g key={traj.axisId}>
            {ARROW_FRACTIONS.map((frac) => {
              const idx = Math.min(
                maxIdx - ARROW_TANGENT_STEP,
                Math.round(frac * maxIdx),
              );
              const p0 = { x: xScale(traj.x[idx])!, y: yScale(traj.v[idx])! };
              const p1 = {
                x: xScale(traj.x[idx + ARROW_TANGENT_STEP])!,
                y: yScale(traj.v[idx + ARROW_TANGENT_STEP])!,
              };
              const angle = Math.atan2(p1.y - p0.y, p1.x - p0.x);
              return (
                <polygon
                  key={`${traj.axisId}-arrow-${frac}`}
                  points={arrowPoints(p0.x, p0.y, angle, ARROW_SIZE)}
                  fill={traj.color}
                  stroke={t.pageBg}
                  strokeWidth={1}
                />
              );
            })}
            <circle
              cx={start.x}
              cy={start.y}
              r={10}
              fill={traj.color}
              stroke={t.pageBg}
              strokeWidth={2.5}
            />
          </g>
        );
      })}
      <circle
        cx={origin.x}
        cy={origin.y}
        r={13}
        fill={t.ink}
        stroke={t.pageBg}
        strokeWidth={3}
      />
      <rect
        x={origin.x + 18}
        y={origin.y - 38}
        width={190}
        height={28}
        rx={5}
        fill={t.elevatedBg}
        opacity={0.9}
      />
      <ChartsText
        x={origin.x + 26}
        y={origin.y - 24}
        text="Equilibrium (0, 0)"
        style={{ fontSize: 16, fill: t.inkSoft, dominantBaseline: "central" }}
      />
    </g>
  );
}

export default function Chart() {
  return (
    <div
      style={{
        width: window.ANYPLOT_SIZE.width,
        height: window.ANYPLOT_SIZE.height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: TITLE_FONT_SIZE,
          fontWeight: 500,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartsDataProvider
        width={window.ANYPLOT_SIZE.width}
        height={window.ANYPLOT_SIZE.height - TITLE_HEIGHT}
        margin={MARGIN}
        skipAnimation
        xAxis={trajectories.map((traj, i) => ({
          id: traj.axisId,
          scaleType: "linear",
          data: traj.x,
          min: X_MIN,
          max: X_MAX,
          position: i === 0 ? "bottom" : "none",
          height: i === 0 ? 68 : 0,
          label: i === 0 ? X : undefined,
          labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        }))}
        yAxis={[
          {
            scaleType: "linear",
            min: V_MIN,
            max: V_MAX,
            width: 84,
            label: DX_DT,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        series={trajectories.map((traj) => ({
          type: "line",
          data: traj.v,
          xAxisId: traj.axisId,
          color: traj.color,
          label: traj.label,
          curve: "linear",
          showMark: false,
        }))}
      >
        <ChartsWrapper
          legendPosition={{ vertical: "bottom", horizontal: "center" }}
          legendDirection="horizontal"
          sx={{ width: "100%", height: "100%" }}
        >
          <ChartsSurface
            sx={{
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
              "& .MuiChartsGrid-line": { stroke: t.grid },
            }}
          >
            <ChartsGrid horizontal vertical />
            <ChartsReferenceLine
              axisId={trajectories[0].axisId}
              x={0}
              lineStyle={{ stroke: t.grid, strokeWidth: 2 }}
            />
            <ChartsReferenceLine
              y={0}
              lineStyle={{ stroke: t.grid, strokeWidth: 2 }}
            />
            <LinePlot />
            <PhaseMarkers />
            <ChartsXAxis
              axisId={trajectories[0].axisId}
              label={X}
              labelStyle={{ fontSize: 16, fill: t.ink, fontWeight: 500 }}
              tickLabelStyle={{ fontSize: 14, fill: t.inkSoft }}
              stroke={t.inkSoft}
            />
            <ChartsYAxis
              label={DX_DT}
              labelStyle={{ fontSize: 16, fill: t.ink, fontWeight: 500 }}
              tickLabelStyle={{ fontSize: 14, fill: t.inkSoft }}
              stroke={t.inkSoft}
            />
          </ChartsSurface>
          <ChartsLegend
            sx={{
              fontSize: 14,
              color: t.inkSoft,
              pb: "18px",
              "& .MuiChartsLegend-label": { fontSize: 14, color: t.inkSoft },
            }}
          />
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
