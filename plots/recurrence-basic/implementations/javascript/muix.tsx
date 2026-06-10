//# anyplot-orientation: square
// anyplot.ai
// recurrence-basic: Recurrence Plot for Nonlinear Time Series
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-10

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Logistic map — chaotic regime (r = 3.95), deterministic seed via fixed start
const N = 300;
const r = 3.95;
const ts: number[] = [0.4];
for (let i = 1; i < N; i++) {
  ts.push(r * ts[i - 1] * (1 - ts[i - 1]));
}

// Time-delay embedding: state[i] = [ts[i], ts[i + tau]] (Takens' theorem)
const tau = 5;
const M = N - tau;
const states = Array.from({ length: M }, (_, i) => [ts[i], ts[i + tau]]);

// Binary recurrence: pairs (i, j) where Euclidean distance < epsilon
const epsilon = 0.15;
const recPts: { x: number; y: number; id: number }[] = [];
let ptId = 0;
for (let i = 0; i < M; i++) {
  for (let j = 0; j < M; j++) {
    const dx = states[i][0] - states[j][0];
    const dy = states[i][1] - states[j][1];
    if (dx * dx + dy * dy < epsilon * epsilon) {
      recPts.push({ x: i, y: j, id: ptId++ });
    }
  }
}

const TITLE_H = 56;

// Annotated identity line (i = j) — drawn via useDrawingArea hook in SVG space.
// In MUI X linear scatter axes, data (0,0) maps to SVG (left, top+height) and
// data (M-1, M-1) maps to SVG (left+width, top), so this diagonal is exact.
function IdentityLine() {
  const { left, top, width, height } = useDrawingArea();
  const labelX = left + width * 0.87;
  const labelY = top + height * 0.07;
  return (
    <g>
      <line
        x1={left}
        y1={top + height}
        x2={left + width}
        y2={top}
        stroke={t.amber}
        strokeWidth={2}
        strokeDasharray="9 5"
        opacity={0.8}
      />
      <text
        x={labelX}
        y={labelY}
        fill={t.amber}
        textAnchor="middle"
        opacity={0.9}
        style={{ fontSize: 12, fontFamily: "Inter, system-ui, sans-serif", fontWeight: 500 }}
      >
        i = j
      </text>
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const side = H - TITLE_H;

  return (
    <div
      style={{
        width: W,
        height: H,
        background: t.pageBg,
        fontFamily: "Inter, system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <div
        style={{
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          recurrence-basic · javascript · muix · anyplot.ai
        </span>
      </div>
      <ChartContainer
        width={side}
        height={side}
        skipAnimation
        colors={[t.palette[0]]}
        margin={{ top: 15, bottom: 72, left: 80, right: 25 }}
        series={[
          {
            type: "scatter",
            data: recPts,
            markerSize: 2,
            label: "Recurrent",
          },
        ]}
        xAxis={[
          {
            min: 0,
            max: M - 1,
            label: "Time Index i",
            tickLabelStyle: { fontSize: 11 },
            labelStyle: { fontSize: 13 },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: M - 1,
            label: "Time Index j",
            tickLabelStyle: { fontSize: 11 },
            labelStyle: { fontSize: 13 },
          },
        ]}
        sx={{
          "& .MuiChartsLegend-root": { display: "none" },
          "& .MuiChartsAxis-line": { display: "none" },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <ChartsGrid vertical horizontal />
        <ScatterPlot />
        <ChartsXAxis />
        <ChartsYAxis />
        <IdentityLine />
      </ChartContainer>
    </div>
  );
}
