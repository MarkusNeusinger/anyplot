// anyplot.ai
// ternary-basic: Basic Ternary Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 85/100 | Created: 2026-08-04
//# anyplot-orientation: square
// anyplot.ai
// ternary-basic: Basic Ternary Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-04
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;
const TITLE = "Bronze Alloy Composition · ternary-basic · javascript · muix · anyplot.ai";
const FONT = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';

// --- Ternary <-> Cartesian projection ---------------------------------------
// Equilateral triangle: Copper (a) at the top apex, Tin (b) at bottom-left,
// Zinc (c) at bottom-right. Only two degrees of freedom exist (a+b+c=1), so
// every composition maps to a unique point inside (or on) the triangle.
const SQRT3_2 = Math.sqrt(3) / 2;
function toXY(a, b, c) {
  const total = a + b + c;
  const aN = a / total;
  const cN = c / total;
  return { x: cN + aN / 2, y: SQRT3_2 * aN };
}
const VERTEX_TOP = toXY(1, 0, 0);
const VERTEX_LEFT = toXY(0, 1, 0);
const VERTEX_RIGHT = toXY(0, 0, 1);

// --- Data: bronze/gunmetal alloy samples (Cu-Sn-Zn, deterministic) ---------
// Foundry bronze is copper-dominant with smaller tin and zinc fractions, so
// the sample cloud naturally clusters toward the Copper apex while still
// spreading across the simplex — the "story" comes from that real material
// tendency, not from an added annotation.
let seed = 20260804 >>> 0;
function rand() {
  seed = (1664525 * seed + 1013904223) >>> 0;
  return seed / 4294967296;
}
function gammaShape(k) {
  let s = 0;
  for (let i = 0; i < k; i++) s += -Math.log(rand() || 1e-9);
  return s;
}

const N = 65;
const cu = new Array(N);
const sn = new Array(N);
const zn = new Array(N);
const points = new Array(N);
for (let i = 0; i < N; i++) {
  const gCu = gammaShape(5);
  const gSn = gammaShape(2);
  const gZn = gammaShape(2);
  const total = gCu + gSn + gZn;
  const a = gCu / total;
  const b = gSn / total;
  const c = gZn / total;
  cu[i] = a * 100;
  sn[i] = b * 100;
  zn[i] = c * 100;
  const { x, y } = toXY(a, b, c);
  points[i] = { x, y, id: `alloy-${i}` };
}

// --- Grid: lines of constant composition, parallel to each edge ------------
const GRID_LEVELS = [0.2, 0.4, 0.6, 0.8];
const GRID_SEGMENTS = [];
for (const f of GRID_LEVELS) {
  GRID_SEGMENTS.push([toXY(f, 1 - f, 0), toXY(f, 0, 1 - f)]); // constant Copper
  GRID_SEGMENTS.push([toXY(1 - f, f, 0), toXY(0, f, 1 - f)]); // constant Tin
  GRID_SEGMENTS.push([toXY(1 - f, 0, f), toXY(0, 1 - f, f)]); // constant Zinc
}

// --- Edge tick marks (0-100 in steps of 20) ---------------------------------
const TICK_LEVELS = [0, 20, 40, 60, 80, 100];
const LEFT_TICKS = TICK_LEVELS.map((pct) => ({ pct, pos: toXY(pct / 100, 1 - pct / 100, 0) }));
const BOTTOM_TICKS = TICK_LEVELS.map((pct) => ({ pct, pos: toXY(0, pct / 100, 1 - pct / 100) }));
const RIGHT_TICKS = TICK_LEVELS.map((pct) => ({ pct, pos: toXY(1 - pct / 100, 0, pct / 100) }));

// Half-extent margins around the [0,1] x [0, sqrt3/2] triangle. Equal x/y
// spans (1.5) keep the triangle equilateral on the square canvas.
const X_MIN = -0.25;
const X_MAX = 1.25;
const Y_MIN = -0.32;
const Y_MAX = 1.18;

function TriangleGrid() {
  const xs = useXScale();
  const ys = useYScale();
  return (
    <g>
      {GRID_SEGMENTS.map((seg, i) => (
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
        d={`M${xs(VERTEX_TOP.x)} ${ys(VERTEX_TOP.y)} L${xs(VERTEX_LEFT.x)} ${ys(VERTEX_LEFT.y)} L${xs(VERTEX_RIGHT.x)} ${ys(VERTEX_RIGHT.y)} Z`}
        fill="none"
        stroke={t.inkSoft}
        strokeWidth={2.5}
        strokeLinejoin="round"
      />
    </g>
  );
}

function EdgeTicks() {
  const xs = useXScale();
  const ys = useYScale();
  const label = (tick, dx, dy, anchor) => (
    <text
      key={`${dx}-${dy}-${tick.pct}`}
      x={xs(tick.pos.x) + dx}
      y={ys(tick.pos.y) + dy}
      textAnchor={anchor}
      dominantBaseline="middle"
      fontFamily={FONT}
      fontSize={14}
      fill={t.inkSoft}
    >
      {tick.pct}
    </text>
  );
  return (
    <g>
      {LEFT_TICKS.map((tk) => label(tk, -12, 0, "end"))}
      {BOTTOM_TICKS.map((tk) => label(tk, 0, 22, "middle"))}
      {RIGHT_TICKS.map((tk) => label(tk, 12, 0, "start"))}
    </g>
  );
}

function VertexLabels() {
  const xs = useXScale();
  const ys = useYScale();
  return (
    <g fontFamily={FONT} fontSize={22} fontWeight={700} fill={t.ink}>
      <text x={xs(VERTEX_TOP.x)} y={ys(VERTEX_TOP.y) - 24} textAnchor="middle" dominantBaseline="baseline">
        Copper (%)
      </text>
      <text x={xs(VERTEX_LEFT.x) - 18} y={ys(VERTEX_LEFT.y) + 34} textAnchor="end" dominantBaseline="baseline">
        Tin (%)
      </text>
      <text x={xs(VERTEX_RIGHT.x) + 18} y={ys(VERTEX_RIGHT.y) + 34} textAnchor="start" dominantBaseline="baseline">
        Zinc (%)
      </text>
    </g>
  );
}

function Title() {
  const xs = useXScale();
  const ys = useYScale();
  const n = TITLE.length;
  const ratio = n > 67 ? 67 / n : 1.0;
  const fontSize = Math.max(15, Math.round(22 * ratio));
  return (
    <text
      x={xs((X_MIN + X_MAX) / 2)}
      y={ys(Y_MAX) + fontSize}
      textAnchor="middle"
      dominantBaseline="hanging"
      fontFamily={FONT}
      fontSize={fontSize}
      fontWeight={600}
      fill={t.ink}
    >
      {TITLE}
    </text>
  );
}

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  return (
    <ChartContainer
      width={SIZE.width}
      height={SIZE.height}
      margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
      series={[
        {
          type: "scatter",
          label: "Alloy sample",
          color: t.palette[0],
          markerSize: 8,
          data: points,
          valueFormatter: (_value, ctx) =>
            `Cu ${cu[ctx.dataIndex].toFixed(0)}% · Sn ${sn[ctx.dataIndex].toFixed(0)}% · Zn ${zn[ctx.dataIndex].toFixed(0)}%`,
        },
      ]}
      xAxis={[{ scaleType: "linear", min: X_MIN, max: X_MAX }]}
      yAxis={[{ scaleType: "linear", min: Y_MIN, max: Y_MAX }]}
      skipAnimation
    >
      <TriangleGrid />
      <ScatterPlot />
      <EdgeTicks />
      <VertexLabels />
      <Title />
      <ChartsTooltip trigger="item" />
    </ChartContainer>
  );
}
