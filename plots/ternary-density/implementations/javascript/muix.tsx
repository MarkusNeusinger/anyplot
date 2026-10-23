//# anyplot-orientation: square
// anyplot.ai
// ternary-density: Ternary Density Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const COMPONENT_A = "Sand"; // role: component_a
const COMPONENT_B = "Silt"; // role: component_b
const COMPONENT_C = "Clay"; // role: component_c

// Data: replace this block with your own records, one object per row
const data = (() => {
  let seed = 20260902 >>> 0;
  const rand = () => {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const erlang = (k: number) => {
    let s = 0;
    for (let i = 0; i < k; i++) s += -Math.log(rand() || 1e-9);
    return s;
  };

  const clusters = [
    { n: 190, shape: [19, 4, 3] }, // sandy soils
    { n: 220, shape: [8, 8, 4] }, // loamy soils
    { n: 170, shape: [4, 5, 11] }, // clay-rich soils
  ];

  const rows: {
    [COMPONENT_A]: number;
    [COMPONENT_B]: number;
    [COMPONENT_C]: number;
  }[] = [];

  for (const cluster of clusters) {
    for (let i = 0; i < cluster.n; i++) {
      const gA = erlang(cluster.shape[0]);
      const gB = erlang(cluster.shape[1]);
      const gC = erlang(cluster.shape[2]);
      const total = gA + gB + gC;
      rows.push({
        [COMPONENT_A]: (gA / total) * 100,
        [COMPONENT_B]: (gB / total) * 100,
        [COMPONENT_C]: (gC / total) * 100,
      });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const SIZE = window.ANYPLOT_SIZE;
const TITLE =
  "Soil Texture Density · ternary-density · javascript · muix · anyplot.ai";
const FONT =
  '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';

const SQRT3_2 = Math.sqrt(3) / 2;
function toXY(a: number, b: number, c: number) {
  const total = a + b + c;
  const aN = a / total;
  const cN = c / total;
  return { x: cN + aN / 2, y: SQRT3_2 * aN };
}
const VERTEX_TOP = toXY(1, 0, 0);
const VERTEX_LEFT = toXY(0, 1, 0);
const VERTEX_RIGHT = toXY(0, 0, 1);

const samplePoints = data.map((d) =>
  toXY(d[COMPONENT_A], d[COMPONENT_B], d[COMPONENT_C]),
);

const GRID_N = 46;
const BANDWIDTH = 0.055;
const TWO_H2 = 2 * BANDWIDTH * BANDWIDTH;

const densityPoints: {
  x: number;
  y: number;
  z: number;
  rawZ: number;
  id: string;
}[] = [];
const aPct: number[] = [];
const bPct: number[] = [];
const cPct: number[] = [];
let maxDensity = 0;
for (let i = 0; i <= GRID_N; i++) {
  for (let j = 0; j <= GRID_N - i; j++) {
    const k = GRID_N - i - j;
    const { x, y } = toXY(i, j, k);
    let density = 0;
    for (let s = 0; s < samplePoints.length; s++) {
      const dx = x - samplePoints[s].x;
      const dy = y - samplePoints[s].y;
      density += Math.exp(-(dx * dx + dy * dy) / TWO_H2);
    }
    density /= samplePoints.length;
    if (density > maxDensity) maxDensity = density;
    densityPoints.push({ x, y, z: density, rawZ: density, id: `cell-${i}-${j}` });
    aPct.push(Math.round((i / GRID_N) * 100));
    bPct.push(Math.round((j / GRID_N) * 100));
    cPct.push(Math.round((k / GRID_N) * 100));
  }
}

const COLOR_GAMMA = 1.7;
for (const p of densityPoints) {
  p.z = Math.pow(p.rawZ / maxDensity, COLOR_GAMMA) * maxDensity;
}

const GRID_LEVELS = [0.2, 0.4, 0.6, 0.8];
const GRID_SEGMENTS: { x: number; y: number }[][] = [];
for (const f of GRID_LEVELS) {
  GRID_SEGMENTS.push([toXY(f, 1 - f, 0), toXY(f, 0, 1 - f)]);
  GRID_SEGMENTS.push([toXY(1 - f, f, 0), toXY(0, f, 1 - f)]);
  GRID_SEGMENTS.push([toXY(1 - f, 0, f), toXY(0, 1 - f, f)]);
}
const TICK_LEVELS = [20, 40, 60, 80];
const LEFT_TICKS = TICK_LEVELS.map((pct) => ({
  pct,
  pos: toXY(pct / 100, 1 - pct / 100, 0),
}));
const BOTTOM_TICKS = TICK_LEVELS.map((pct) => ({
  pct,
  pos: toXY(0, pct / 100, 1 - pct / 100),
}));
const RIGHT_TICKS = TICK_LEVELS.map((pct) => ({
  pct,
  pos: toXY(1 - pct / 100, 0, pct / 100),
}));

const X_MIN = -0.108;
const X_MAX = 1.108;
const Y_MIN = -0.26;
const Y_MAX = 0.956;

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

function DensityLayer() {
  const xs = useXScale();
  const ys = useYScale();
  const clipD = `M${xs(VERTEX_TOP.x)} ${ys(VERTEX_TOP.y)} L${xs(VERTEX_LEFT.x)} ${ys(VERTEX_LEFT.y)} L${xs(VERTEX_RIGHT.x)} ${ys(VERTEX_RIGHT.y)} Z`;
  return (
    <>
      <defs>
        <clipPath id="ternaryTriangleClip">
          <path d={clipD} />
        </clipPath>
      </defs>
      <g clipPath="url(#ternaryTriangleClip)" opacity={0.85}>
        <ScatterPlot />
      </g>
    </>
  );
}

function GridOverlay() {
  const xs = useXScale();
  const ys = useYScale();
  return (
    <g>
      {GRID_SEGMENTS.map((seg, i) => (
        <line
          key={`halo-${i}`}
          x1={xs(seg[0].x)}
          y1={ys(seg[0].y)}
          x2={xs(seg[1].x)}
          y2={ys(seg[1].y)}
          stroke={t.pageBg}
          strokeWidth={4}
          strokeOpacity={0.6}
          strokeDasharray="6 5"
        />
      ))}
      {GRID_SEGMENTS.map((seg, i) => (
        <line
          key={`line-${i}`}
          x1={xs(seg[0].x)}
          y1={ys(seg[0].y)}
          x2={xs(seg[1].x)}
          y2={ys(seg[1].y)}
          stroke={t.grid}
          strokeWidth={1.5}
          strokeDasharray="6 5"
        />
      ))}
    </g>
  );
}

function EdgeTicks() {
  const xs = useXScale();
  const ys = useYScale();
  const label = (
    tick: { pct: number; pos: { x: number; y: number } },
    dx: number,
    dy: number,
    anchor: "start" | "middle" | "end",
  ) => (
    <text
      key={`${dx}-${dy}-${tick.pct}`}
      x={xs(tick.pos.x)! + dx}
      y={ys(tick.pos.y)! + dy}
      textAnchor={anchor}
      dominantBaseline="middle"
      fontFamily={FONT}
      fontSize={13}
      fill={t.inkSoft}
    >
      {tick.pct}%
    </text>
  );
  return (
    <g>
      {LEFT_TICKS.map((tk) => label(tk, -16, 0, "end"))}
      {BOTTOM_TICKS.map((tk) => label(tk, 0, 22, "middle"))}
      {RIGHT_TICKS.map((tk) => label(tk, 16, 0, "start"))}
    </g>
  );
}

function VertexLabels() {
  const xs = useXScale();
  const ys = useYScale();
  return (
    <g fontFamily={FONT} fontSize={22} fontWeight={700} fill={t.ink}>
      <text
        x={xs(VERTEX_TOP.x)}
        y={ys(VERTEX_TOP.y)! - 22}
        textAnchor="middle"
        dominantBaseline="baseline"
      >
        {COMPONENT_A}
      </text>
      <text
        x={xs(VERTEX_LEFT.x)}
        y={ys(VERTEX_LEFT.y)! + 30}
        textAnchor="middle"
        dominantBaseline="hanging"
      >
        {COMPONENT_B}
      </text>
      <text
        x={xs(VERTEX_RIGHT.x)}
        y={ys(VERTEX_RIGHT.y)! + 30}
        textAnchor="middle"
        dominantBaseline="hanging"
      >
        {COMPONENT_C}
      </text>
    </g>
  );
}

function DensityLegend() {
  const { left, top, width, height } = useDrawingArea();
  const barWidth = Math.min(380, width * 0.36);
  const barHeight = 20;
  const cx = left + width / 2;
  const barY = top + height - 92;
  const barX = cx - barWidth / 2;
  return (
    <g fontFamily={FONT}>
      <defs>
        <linearGradient id="ternaryDensityGradient" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>
      <text
        x={cx}
        y={barY - 14}
        textAnchor="middle"
        fontSize={15}
        fill={t.inkSoft}
      >
        Relative sample density
      </text>
      <rect
        x={barX}
        y={barY}
        width={barWidth}
        height={barHeight}
        rx={4}
        fill="url(#ternaryDensityGradient)"
        stroke={t.ink}
        strokeOpacity={0.15}
      />
      <text
        x={barX}
        y={barY + barHeight + 20}
        textAnchor="start"
        fontSize={13}
        fill={t.inkSoft}
      >
        Low
      </text>
      <text
        x={barX + barWidth}
        y={barY + barHeight + 20}
        textAnchor="end"
        fontSize={13}
        fill={t.inkSoft}
      >
        High
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
      y={ys(Y_MAX)! + 4}
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

export default function Chart() {
  return (
    <ChartsContainer
      width={SIZE.width}
      height={SIZE.height}
      margin={{ top: 24, right: 24, bottom: 24, left: 24 }}
      series={[
        {
          type: "scatter",
          label: "Sample density",
          color: t.seq[0],
          markerSize: 13,
          data: densityPoints,
          valueFormatter: (_value: any, ctx: any) =>
            `${COMPONENT_A} ${aPct[ctx.dataIndex]}% · ${COMPONENT_B} ${bPct[ctx.dataIndex]}% · ${COMPONENT_C} ${cPct[ctx.dataIndex]}% — ${Math.round((densityPoints[ctx.dataIndex].rawZ / maxDensity) * 100)}% of peak density`,
        },
      ]}
      xAxis={[{ scaleType: "linear", min: X_MIN, max: X_MAX, position: "none" }]}
      yAxis={[{ scaleType: "linear", min: Y_MIN, max: Y_MAX, position: "none" }]}
      zAxis={[
        {
          id: "density",
          min: 0,
          max: maxDensity,
          colorMap: { type: "continuous", color: [t.seq[0], t.seq[1]] },
        },
      ]}
      skipAnimation
    >
      <TriangleGrid />
      <DensityLayer />
      <GridOverlay />
      <EdgeTicks />
      <VertexLabels />
      <DensityLegend />
      <Title />
      <ChartsTooltip trigger="item" />
    </ChartsContainer>
  );
}
