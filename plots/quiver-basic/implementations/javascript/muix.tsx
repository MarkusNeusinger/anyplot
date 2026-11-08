// anyplot.ai
// quiver-basic: Basic Quiver Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: pending | Created: 2026-07-24
//# anyplot-orientation: square

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const ARROW_SHARE = 0.85; // the longest arrow as a share of the grid spacing
const PAD_SHARE = 0.03; // padding around the arrow extent, share of the span
const HEAD_PX = 10; // arrow head length, px
const HEAD_SHARE = 0.6; // a short arrow's head as a share of its own length
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_W = 150;
const X_AXIS_H = 64;
const Y_AXIS_W = 72;
const GAP = 24; // free space around the square drawing area, px

// Columns: set these to your data's column names
const X = "East of storm center (km)"; // role: x
const Y = "North of storm center (km)"; // role: y
const U = "Eastward wind (m/s)"; // role: u
const V = "Northward wind (m/s)"; // role: v

// Data: replace this block with your own records, one object per row
// Cyclonic wind around a low-pressure center (Rankine vortex) on a 15 x 15 grid 1 km apart:
// solid-body rotation inside the 3.2 km core, tangential wind decaying as 1/r outside it,
// 22 m/s at the core radius
const data = Array.from({ length: 15 * 15 }, (_, k) => {
  const x = Math.floor(k / 15) - 7;
  const y = (k % 15) - 7;
  const r = Math.hypot(x, y);
  const speed = r <= 3.2 ? (22 * r) / 3.2 : (22 * 3.2) / r;
  return {
    [X]: x,
    [Y]: y,
    [U]: r === 0 ? 0 : Math.round((-y / r) * speed * 100) / 100,
    [V]: r === 0 ? 0 : Math.round((x / r) * speed * 100) / 100,
  };
});

// Plot: reads only data and the constants above
const rows = data.filter((d) => [d[X], d[Y], d[U], d[V]].every(Number.isFinite));
const speeds = rows.map((d) => Math.hypot(d[U], d[V]));
const maxSpeed = Math.max(...speeds);
const xUnit = X.match(/\(([^)]+)\)/)?.[1] ?? "";
const speedUnit = U.match(/\(([^)]+)\)/)?.[1] ?? "";

// Grid spacing: the smallest gap between neighbouring grid coordinates on either axis
const gaps = [X, Y].flatMap((col) => {
  const values = [...new Set(rows.map((d) => d[col]))].sort((a, b) => a - b);
  return values.slice(1).map((v, i) => v - values[i]);
});
const spacing = Math.min(...gaps);

// One length scale for the whole field: the strongest vector spans ARROW_SHARE of a grid cell
const lengthPerSpeed = maxSpeed > 0 ? (ARROW_SHARE * spacing) / maxSpeed : 0;
const arrows = rows.map((d, i) => ({
  x0: d[X],
  y0: d[Y],
  x1: d[X] + d[U] * lengthPerSpeed,
  y1: d[Y] + d[V] * lengthPerSpeed,
  speed: speeds[i],
}));

// Square window over tails and heads, one span on both axes so directions read true
const xs = arrows.flatMap((a) => [a.x0, a.x1]);
const ys = arrows.flatMap((a) => [a.y0, a.y1]);
const span = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)) * (1 + 2 * PAD_SHARE);
const xMid = (Math.max(...xs) + Math.min(...xs)) / 2;
const yMid = (Math.max(...ys) + Math.min(...ys)) / 2;

const TITLE = "Cyclonic Wind Field · quiver-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length} grid points ${spacing} ${xUnit} apart · arrow length proportional to magnitude, longest ${maxSpeed.toFixed(1)} ${speedUnit}`;

function QuiverArrows() {
  const xScale = useXScale();
  const yScale = useYScale();
  const colorScale = useZColorScale("speed");
  return (
    <g strokeLinecap="round">
      {arrows.map((a, i) => {
        const px0 = xScale(a.x0);
        const py0 = yScale(a.y0);
        const px1 = xScale(a.x1);
        const py1 = yScale(a.y1);
        const length = Math.hypot(px1 - px0, py1 - py0);
        const color = colorScale(a.speed);
        if (length < 1) return <circle key={i} cx={px0} cy={py0} r={2.5} fill={color} />;
        const angle = Math.atan2(py1 - py0, px1 - px0);
        const head = Math.min(HEAD_PX, HEAD_SHARE * length);
        const points = [angle - 0.4, angle + 0.4]
          .map((w) => `${px1 - head * Math.cos(w)},${py1 - head * Math.sin(w)}`)
          .join(" ");
        return (
          <g key={i}>
            <line x1={px0} y1={py0} x2={px1} y2={py1} stroke={color} strokeWidth={2.2} />
            <polygon points={`${px1},${py1} ${points}`} fill={color} />
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const plotW = width - LEGEND_W;
  const plotH = height - TITLE_H - SUBTITLE_H;
  const side = Math.min(plotW - Y_AXIS_W, plotH - X_AXIS_H) - 2 * GAP;
  const sideX = (plotW - Y_AXIS_W - side) / 2;
  const sideY = (plotH - X_AXIS_H - side) / 2;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <ChartsDataProvider
        width={plotW}
        height={plotH}
        skipAnimation
        series={[]}
        margin={{ top: sideY, bottom: sideY, left: sideX, right: sideX }}
        zAxis={[
          {
            id: "speed",
            colorMap: { type: "continuous", min: 0, max: maxSpeed, color: [t.seq[0], t.seq[1]] },
          },
        ]}
        xAxis={[
          {
            scaleType: "linear",
            min: xMid - span / 2,
            max: xMid + span / 2,
            label: X,
            height: X_AXIS_H,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: yMid - span / 2,
            max: yMid + span / 2,
            label: Y,
            width: Y_AXIS_W,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "middle", horizontal: "end" }} legendDirection="vertical" sx={{ width, height: plotH }}>
          <div style={{ gridArea: "legend", width: LEGEND_W, height: side * 0.7, display: "flex", flexDirection: "column", alignItems: "center" }}>
            <div style={{ fontSize: 15, color: t.ink, marginBottom: 10, textAlign: "center" }}>Magnitude ({speedUnit})</div>
            <ContinuousColorLegend
              axisDirection="z"
              axisId="speed"
              direction="vertical"
              thickness={18}
              labelPosition="end"
              minLabel={({ value }) => Number(value).toFixed(0)}
              maxLabel={({ value }) => Number(value).toFixed(1)}
              sx={{ flex: 1, color: t.inkSoft, fontSize: 14 }}
            />
          </div>
          <ChartsSurface
            sx={{
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
            }}
          >
            <QuiverArrows />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
