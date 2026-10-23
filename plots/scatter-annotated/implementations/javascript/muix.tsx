// anyplot.ai
// scatter-annotated: Annotated Scatter Plot with Text Labels
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 86/100 | Updated: 2026-10-23

import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const isDark = window.ANYPLOT_THEME === "dark";
const MUTED = isDark ? "#A8A79F" : "#6B6A63";

// Columns: set these to your data's column names
const X = "Annual Revenue ($B)"; // role: x
const Y = "Market Cap ($B)"; // role: y
const LABEL = "Company"; // role: label

// Data: replace this block with your own records, one object per row
// Annual revenue ($B) vs. market cap ($B) for a cohort of tech companies;
// notable outliers carry a company label while peer companies have an empty label.
const data = [
  { [X]: 8, [Y]: 210, [LABEL]: "NexaCloud" },
  { [X]: 45, [Y]: 60, [LABEL]: "Solstice Robotics" },
  { [X]: 62, [Y]: 340, [LABEL]: "Vertex Analytics" },
  { [X]: 120, [Y]: 95, [LABEL]: "Ferrotech Dynamics" },
  { [X]: 15, [Y]: 180, [LABEL]: "Lumen Bioworks" },
  { [X]: 88, [Y]: 410, [LABEL]: "Aurora Semiconductors" },
  { [X]: 150, [Y]: 60, [LABEL]: "Cascade Networks" },
  { [X]: 30, [Y]: 265, [LABEL]: "Nimbus Software" },
  { [X]: 95, [Y]: 70, [LABEL]: "Ridgeline Hardware" },
  { [X]: 55, [Y]: 40, [LABEL]: "Halcyon Games" },
  { [X]: 22, [Y]: 155, [LABEL]: "Zephyr Mobility" },
  { [X]: 110, [Y]: 130, [LABEL]: "Granite Payments" },
  { [X]: 7, [Y]: 38, [LABEL]: "" },
  { [X]: 12, [Y]: 72, [LABEL]: "" },
  { [X]: 19, [Y]: 58, [LABEL]: "" },
  { [X]: 27, [Y]: 104, [LABEL]: "" },
  { [X]: 31, [Y]: 79, [LABEL]: "" },
  { [X]: 38, [Y]: 126, [LABEL]: "" },
  { [X]: 44, [Y]: 98, [LABEL]: "" },
  { [X]: 51, [Y]: 141, [LABEL]: "" },
  { [X]: 58, [Y]: 112, [LABEL]: "" },
  { [X]: 64, [Y]: 168, [LABEL]: "" },
  { [X]: 71, [Y]: 139, [LABEL]: "" },
  { [X]: 77, [Y]: 192, [LABEL]: "" },
  { [X]: 84, [Y]: 158, [LABEL]: "" },
  { [X]: 92, [Y]: 214, [LABEL]: "" },
  { [X]: 101, [Y]: 176, [LABEL]: "" },
  { [X]: 107, [Y]: 238, [LABEL]: "" },
  { [X]: 118, [Y]: 197, [LABEL]: "" },
  { [X]: 126, [Y]: 252, [LABEL]: "" },
  { [X]: 133, [Y]: 214, [LABEL]: "" },
  { [X]: 141, [Y]: 271, [LABEL]: "" },
];

// Plot: reads only data and the constants above
const allX = data.map((d) => d[X]);
const allY = data.map((d) => d[Y]);
const X_MAX = Math.ceil((Math.max(...allX) * 1.1) / 5) * 5;
const Y_MAX = Math.ceil((Math.max(...allY) + 20) / 10) * 10;

const OFFSET_CYCLE = [
  { dx: 40, dy: -16 },
  { dx: -44, dy: -18 },
  { dx: 42, dy: -14 },
  { dx: 44, dy: -16 },
  { dx: 40, dy: 20 },
  { dx: 44, dy: 18 },
  { dx: -46, dy: -16 },
  { dx: 42, dy: -12 },
  { dx: 40, dy: 20 },
  { dx: 40, dy: -20 },
  { dx: -42, dy: 20 },
  { dx: -46, dy: -16 },
];

const highlighted = data
  .filter((d) => Boolean(d[LABEL]))
  .map((d, i) => {
    const candidate = OFFSET_CYCLE[i % OFFSET_CYCLE.length];
    const nearLeft = d[X] < X_MAX * 0.12;
    const nearRight = d[X] > X_MAX * 0.85;
    const dx = nearLeft
      ? Math.abs(candidate.dx)
      : nearRight
      ? -Math.abs(candidate.dx)
      : candidate.dx;
    const dy = candidate.dy;
    return {
      id: `hl-${i}`,
      x: d[X],
      y: d[Y],
      label: d[LABEL],
      dx,
      dy,
    };
  });

const peers = data
  .filter((d) => !d[LABEL])
  .map((d, i) => ({
    id: `peer-${i}`,
    x: d[X],
    y: d[Y],
  }));

function PointAnnotations() {
  const xScale = useXScale() as any;
  const yScale = useYScale() as any;
  if (!xScale || !yScale) return null;

  return (
    <g>
      {highlighted.map((p) => {
        const px = xScale(p.x);
        const py = yScale(p.y);
        const lx = px + p.dx;
        const ly = py + p.dy;
        const tx = lx + (p.dx >= 0 ? 6 : -6);
        return (
          <g key={p.id}>
            <line x1={px} y1={py} x2={lx} y2={ly} stroke={MUTED} strokeWidth={1.2} opacity={0.65} />
            <text
              x={tx}
              y={ly}
              fontSize={14}
              fontWeight={500}
              fill={t.ink}
              textAnchor={p.dx >= 0 ? "start" : "end"}
              dominantBaseline="middle"
            >
              {p.label}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleHeight = 56;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "'Roboto', 'Helvetica', 'Arial', sans-serif",
      }}
    >
      <div
        style={{
          height: titleHeight,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 20,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        Tech Company Valuations · scatter-annotated · javascript · muix · anyplot.ai
      </div>

      <ScatterChart
        width={width}
        height={height - titleHeight}
        skipAnimation
        disableHitArea
        grid={{ horizontal: true, vertical: true }}
        xAxis={[
          {
            height: 64,
            label: X,
            min: 0,
            max: X_MAX,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            width: 84,
            label: Y,
            min: 0,
            max: Y_MAX,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "highlighted",
            label: "Highlighted",
            data: highlighted,
            markerSize: 9,
            color: t.palette[0],
          },
          {
            id: "peers",
            label: "Peer companies",
            data: peers,
            markerSize: 5.5,
            color: MUTED,
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
          },
        }}
        sx={{
          "& .MuiScatterChart-marker": { fillOpacity: 0.7 },
          "& .MuiChartsLegend-root": { color: t.ink, pb: "12px" },
          "& .MuiChartsLegend-label": { fontSize: "15px !important", color: t.ink },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
        margin={{ top: 20, right: 60, bottom: 16, left: 40 }}
      >
        <PointAnnotations />
      </ScatterChart>
    </div>
  );
}
