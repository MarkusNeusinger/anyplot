// anyplot.ai
// ternary-basic: Basic Ternary Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 88/100 | Created: 2026-08-04
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SQRT3_2 = Math.sqrt(3) / 2;
const GRID_LEVELS = [0.2, 0.4, 0.6, 0.8];
const TICK_LEVELS = [0, 20, 40, 60, 80, 100];
const X_MIN = -0.06;
const X_MAX = 1.06;
const Y_MIN = -0.09;
const Y_MAX = 1.03;

// Columns: set these to your data's column names
const COMPONENT_A = "Copper (%)"; // role: component_a
const COMPONENT_B = "Tin (%)"; // role: component_b
const COMPONENT_C = "Zinc (%)"; // role: component_c

// Data: replace this block with your own records
const nSamplesGen = 65;
let lcgSeed = 20260804 >>> 0;
const data: Array<Record<string, number>> = [];

for (let i = 0; i < nSamplesGen; i++) {
  let gCu = 0;
  for (let k = 0; k < 5; k++) {
    lcgSeed = (1664525 * lcgSeed + 1013904223) >>> 0;
    gCu += -Math.log(lcgSeed / 4294967296 || 1e-9);
  }
  let gSn = 0;
  for (let k = 0; k < 2; k++) {
    lcgSeed = (1664525 * lcgSeed + 1013904223) >>> 0;
    gSn += -Math.log(lcgSeed / 4294967296 || 1e-9);
  }
  let gZn = 0;
  for (let k = 0; k < 2; k++) {
    lcgSeed = (1664525 * lcgSeed + 1013904223) >>> 0;
    gZn += -Math.log(lcgSeed / 4294967296 || 1e-9);
  }
  const total = gCu + gSn + gZn;
  data.push({
    [COMPONENT_A]: Number(((gCu / total) * 100).toFixed(2)),
    [COMPONENT_B]: Number(((gSn / total) * 100).toFixed(2)),
    [COMPONENT_C]: Number(((gZn / total) * 100).toFixed(2)),
  });
}

// Plot: reads only data and the constants above
const vertexTop = { x: 0.5, y: SQRT3_2 };
const vertexLeft = { x: 0, y: 0 };
const vertexRight = { x: 1, y: 0 };

const cuVals = data.map((r) => Number(r[COMPONENT_A]));
const snVals = data.map((r) => Number(r[COMPONENT_B]));
const znVals = data.map((r) => Number(r[COMPONENT_C]));

const points = data.map((row, i) => {
  const a = Number(row[COMPONENT_A]);
  const b = Number(row[COMPONENT_B]);
  const c = Number(row[COMPONENT_C]);
  const total = a + b + c || 1;
  const aN = a / total;
  const cN = c / total;
  return {
    x: cN + aN / 2,
    y: SQRT3_2 * aN,
    id: `alloy-${i}`,
  };
});

const gridSegments: Array<[{ x: number; y: number }, { x: number; y: number }]> = [];
for (const f of GRID_LEVELS) {
  gridSegments.push([
    { x: 0 + f / 2, y: SQRT3_2 * f },
    { x: (1 - f) + f / 2, y: SQRT3_2 * f },
  ]);
  gridSegments.push([
    { x: 0 + (1 - f) / 2, y: SQRT3_2 * (1 - f) },
    { x: (1 - f) + 0 / 2, y: 0 },
  ]);
  gridSegments.push([
    { x: f + (1 - f) / 2, y: SQRT3_2 * (1 - f) },
    { x: f + 0 / 2, y: 0 },
  ]);
}

const leftTicks = TICK_LEVELS.map((pct) => {
  const aN = pct / 100;
  return { pct, pos: { x: aN / 2, y: SQRT3_2 * aN } };
});
const bottomTicks = TICK_LEVELS.map((pct) => {
  const cN = (100 - pct) / 100;
  return { pct, pos: { x: cN, y: 0 } };
});
const rightTicks = TICK_LEVELS.map((pct) => {
  const aN = (100 - pct) / 100;
  const cN = pct / 100;
  return { pct, pos: { x: cN + aN / 2, y: SQRT3_2 * aN } };
});

function TriangleGrid() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  return (
    <g>
      {gridSegments.map((seg, i) => (
        <line
          key={i}
          x1={xs(seg[0].x)}
          y1={ys(seg[0].y)}
          x2={xs(seg[1].x)}
          y2={ys(seg[1].y)}
          stroke={t.grid}
          strokeWidth={1.5}
          strokeDasharray="6 5"
        />
      ))}
      <path
        d={`M${xs(vertexTop.x)} ${ys(vertexTop.y)} L${xs(vertexLeft.x)} ${ys(vertexLeft.y)} L${xs(vertexRight.x)} ${ys(vertexRight.y)} Z`}
        fill="none"
        stroke={t.inkSoft}
        strokeWidth={2.5}
        strokeLinejoin="round"
      />
    </g>
  );
}

function EdgeTicks() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  return (
    <g>
      {leftTicks.map((tk) => (
        <text
          key={`l-${tk.pct}`}
          x={xs(tk.pos.x) - 16}
          y={ys(tk.pos.y)}
          textAnchor="end"
          dominantBaseline="middle"
          fontSize={14}
          fill={t.inkSoft}
        >
          {tk.pct}
        </text>
      ))}
      {bottomTicks.map((tk) => (
        <text
          key={`b-${tk.pct}`}
          x={xs(tk.pos.x)}
          y={ys(tk.pos.y) + 22}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={14}
          fill={t.inkSoft}
        >
          {tk.pct}
        </text>
      ))}
      {rightTicks.map((tk) => (
        <text
          key={`r-${tk.pct}`}
          x={xs(tk.pos.x) + 16}
          y={ys(tk.pos.y)}
          textAnchor="start"
          dominantBaseline="middle"
          fontSize={14}
          fill={t.inkSoft}
        >
          {tk.pct}
        </text>
      ))}
    </g>
  );
}

function VertexLabelsAndTitle() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  return (
    <g>
      <text
        x={xs((X_MIN + X_MAX) / 2)}
        y={ys(Y_MAX) + 22}
        textAnchor="middle"
        dominantBaseline="hanging"
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
      >
        Bronze Alloy Composition · ternary-basic · javascript · muix · anyplot.ai
      </text>
      <g fontSize={22} fontWeight={700} fill={t.ink}>
        <text
          x={xs(vertexTop.x)}
          y={ys(vertexTop.y) - 24}
          textAnchor="middle"
          dominantBaseline="baseline"
        >
          {COMPONENT_A}
        </text>
        <text
          x={xs(vertexLeft.x)}
          y={ys(vertexLeft.y) + 32}
          textAnchor="middle"
          dominantBaseline="hanging"
        >
          {COMPONENT_B}
        </text>
        <text
          x={xs(vertexRight.x)}
          y={ys(vertexRight.y) + 32}
          textAnchor="middle"
          dominantBaseline="hanging"
        >
          {COMPONENT_C}
        </text>
      </g>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg }}>
      <ChartsContainer
        width={width}
        height={height}
        margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
        series={[
          {
            type: "scatter",
            label: "Alloy sample",
            color: "rgba(0, 158, 115, 0.85)",
            markerSize: 8,
            data: points,
            valueFormatter: (_value: unknown, ctx: { dataIndex: number }) =>
              `Cu ${cuVals[ctx.dataIndex].toFixed(0)}% · Sn ${snVals[ctx.dataIndex].toFixed(0)}% · Zn ${znVals[ctx.dataIndex].toFixed(0)}%`,
          },
        ]}
        xAxis={[{ scaleType: "linear", min: X_MIN, max: X_MAX, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: Y_MIN, max: Y_MAX, position: "none" }]}
      >
        <TriangleGrid />
        <ScatterPlot skipAnimation />
        <EdgeTicks />
        <VertexLabelsAndTitle />
        <ChartsTooltip trigger="item" />
      </ChartsContainer>
    </div>
  );
}
