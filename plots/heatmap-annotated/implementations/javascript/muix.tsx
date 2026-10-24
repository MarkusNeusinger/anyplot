// anyplot.ai
// heatmap-annotated: Annotated Heatmap
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: pending | Created: 2026-08-05
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const W = window.ANYPLOT_SIZE.width;
const H = window.ANYPLOT_SIZE.height;
const FONT = "system-ui, -apple-system, sans-serif";
const TITLE = "heatmap-annotated · javascript · muix · anyplot.ai";
const DOMAIN_MIN = -1;
const DOMAIN_MID = 0;
const DOMAIN_MAX = 1;
const COLORBAR_TICKS = [-1.0, -0.5, 0.0, 0.5, 1.0];

// Columns: set these to your data's column names
const COL_VAR = "Column variable"; // role: x
const ROW_VAR = "Row variable"; // role: y
const CORRELATION = "Pearson r"; // role: value

// Data: replace this block with your own records
const data: Record<string, string | number>[] = [
  { [ROW_VAR]: "Sleep", [COL_VAR]: "Sleep", [CORRELATION]: 1.0 },
  { [ROW_VAR]: "Sleep", [COL_VAR]: "Exercise", [CORRELATION]: 0.35 },
  { [ROW_VAR]: "Sleep", [COL_VAR]: "Screen Time", [CORRELATION]: -0.42 },
  { [ROW_VAR]: "Sleep", [COL_VAR]: "Stress", [CORRELATION]: -0.58 },
  { [ROW_VAR]: "Sleep", [COL_VAR]: "Water", [CORRELATION]: 0.22 },
  { [ROW_VAR]: "Sleep", [COL_VAR]: "Steps", [CORRELATION]: 0.31 },
  { [ROW_VAR]: "Sleep", [COL_VAR]: "Mood", [CORRELATION]: 0.61 },

  { [ROW_VAR]: "Exercise", [COL_VAR]: "Sleep", [CORRELATION]: 0.35 },
  { [ROW_VAR]: "Exercise", [COL_VAR]: "Exercise", [CORRELATION]: 1.0 },
  { [ROW_VAR]: "Exercise", [COL_VAR]: "Screen Time", [CORRELATION]: -0.28 },
  { [ROW_VAR]: "Exercise", [COL_VAR]: "Stress", [CORRELATION]: -0.33 },
  { [ROW_VAR]: "Exercise", [COL_VAR]: "Water", [CORRELATION]: 0.45 },
  { [ROW_VAR]: "Exercise", [COL_VAR]: "Steps", [CORRELATION]: 0.82 },
  { [ROW_VAR]: "Exercise", [COL_VAR]: "Mood", [CORRELATION]: 0.57 },

  { [ROW_VAR]: "Screen Time", [COL_VAR]: "Sleep", [CORRELATION]: -0.42 },
  { [ROW_VAR]: "Screen Time", [COL_VAR]: "Exercise", [CORRELATION]: -0.28 },
  { [ROW_VAR]: "Screen Time", [COL_VAR]: "Screen Time", [CORRELATION]: 1.0 },
  { [ROW_VAR]: "Screen Time", [COL_VAR]: "Stress", [CORRELATION]: 0.49 },
  { [ROW_VAR]: "Screen Time", [COL_VAR]: "Water", [CORRELATION]: -0.18 },
  { [ROW_VAR]: "Screen Time", [COL_VAR]: "Steps", [CORRELATION]: -0.39 },
  { [ROW_VAR]: "Screen Time", [COL_VAR]: "Mood", [CORRELATION]: -0.44 },

  { [ROW_VAR]: "Stress", [COL_VAR]: "Sleep", [CORRELATION]: -0.58 },
  { [ROW_VAR]: "Stress", [COL_VAR]: "Exercise", [CORRELATION]: -0.33 },
  { [ROW_VAR]: "Stress", [COL_VAR]: "Screen Time", [CORRELATION]: 0.49 },
  { [ROW_VAR]: "Stress", [COL_VAR]: "Stress", [CORRELATION]: 1.0 },
  { [ROW_VAR]: "Stress", [COL_VAR]: "Water", [CORRELATION]: -0.15 },
  { [ROW_VAR]: "Stress", [COL_VAR]: "Steps", [CORRELATION]: -0.36 },
  { [ROW_VAR]: "Stress", [COL_VAR]: "Mood", [CORRELATION]: -0.71 },

  { [ROW_VAR]: "Water", [COL_VAR]: "Sleep", [CORRELATION]: 0.22 },
  { [ROW_VAR]: "Water", [COL_VAR]: "Exercise", [CORRELATION]: 0.45 },
  { [ROW_VAR]: "Water", [COL_VAR]: "Screen Time", [CORRELATION]: -0.18 },
  { [ROW_VAR]: "Water", [COL_VAR]: "Stress", [CORRELATION]: -0.15 },
  { [ROW_VAR]: "Water", [COL_VAR]: "Water", [CORRELATION]: 1.0 },
  { [ROW_VAR]: "Water", [COL_VAR]: "Steps", [CORRELATION]: 0.28 },
  { [ROW_VAR]: "Water", [COL_VAR]: "Mood", [CORRELATION]: 0.19 },

  { [ROW_VAR]: "Steps", [COL_VAR]: "Sleep", [CORRELATION]: 0.31 },
  { [ROW_VAR]: "Steps", [COL_VAR]: "Exercise", [CORRELATION]: 0.82 },
  { [ROW_VAR]: "Steps", [COL_VAR]: "Screen Time", [CORRELATION]: -0.39 },
  { [ROW_VAR]: "Steps", [COL_VAR]: "Stress", [CORRELATION]: -0.36 },
  { [ROW_VAR]: "Steps", [COL_VAR]: "Water", [CORRELATION]: 0.28 },
  { [ROW_VAR]: "Steps", [COL_VAR]: "Steps", [CORRELATION]: 1.0 },
  { [ROW_VAR]: "Steps", [COL_VAR]: "Mood", [CORRELATION]: 0.52 },

  { [ROW_VAR]: "Mood", [COL_VAR]: "Sleep", [CORRELATION]: 0.61 },
  { [ROW_VAR]: "Mood", [COL_VAR]: "Exercise", [CORRELATION]: 0.57 },
  { [ROW_VAR]: "Mood", [COL_VAR]: "Screen Time", [CORRELATION]: -0.44 },
  { [ROW_VAR]: "Mood", [COL_VAR]: "Stress", [CORRELATION]: -0.71 },
  { [ROW_VAR]: "Mood", [COL_VAR]: "Water", [CORRELATION]: 0.19 },
  { [ROW_VAR]: "Mood", [COL_VAR]: "Steps", [CORRELATION]: 0.52 },
  { [ROW_VAR]: "Mood", [COL_VAR]: "Mood", [CORRELATION]: 1.0 },
];

// Plot: reads only data and the constants above
const xCategories = Array.from(new Set(data.map((r) => String(r[COL_VAR]))));
const yCategories = Array.from(new Set(data.map((r) => String(r[ROW_VAR]))));

const divStopInts = t.div.map((hex) => parseInt(hex.replace("#", ""), 16));
const divStopsRgb: [number, number, number][] = divStopInts.map((v) => [
  (v >> 16) & 255,
  (v >> 8) & 255,
  v & 255,
]);

const cells = data.map((row) => {
  const xKey = String(row[COL_VAR]);
  const yKey = String(row[ROW_VAR]);
  const value = Number(row[CORRELATION]);
  const [r0, g0, b0] = divStopsRgb[0];
  const [r1, g1, b1] = divStopsRgb[1];
  const [r2, g2, b2] = divStopsRgb[2];

  const isNeg = value <= DOMAIN_MID;
  const [ra, ga, ba] = isNeg ? [r0, g0, b0] : [r1, g1, b1];
  const [rb, gb, bb] = isNeg ? [r1, g1, b1] : [r2, g2, b2];
  const f = isNeg
    ? (value - DOMAIN_MIN) / (DOMAIN_MID - DOMAIN_MIN)
    : (value - DOMAIN_MID) / (DOMAIN_MAX - DOMAIN_MID);

  const r = Math.round(ra + (rb - ra) * f);
  const g = Math.round(ga + (gb - ga) * f);
  const b = Math.round(ba + (bb - ba) * f);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  const textFill = luminance > 0.55 ? "#1A1A17" : "#FAF8F1";

  return {
    key: `${yKey}-${xKey}`,
    xKey,
    yKey,
    value,
    fill: `rgb(${r},${g},${b})`,
    textFill,
  };
});

function HeatmapLayer() {
  const xScale = useXScale("vars_x") as unknown as ((v: string) => number) & { bandwidth: () => number };
  const yScale = useYScale("vars_y") as unknown as ((v: string) => number) & { bandwidth: () => number };
  const { left, top, width, height } = useDrawingArea();

  const bw = xScale.bandwidth();
  const bh = yScale.bandwidth();
  const barX = left + width + 26;

  return (
    <g>
      <defs>
        <linearGradient id="divGrad" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.div[0]} />
          <stop offset="50%" stopColor={t.div[1]} />
          <stop offset="100%" stopColor={t.div[2]} />
        </linearGradient>
      </defs>

      {cells.map((cell) => {
        const x0 = xScale(cell.xKey);
        const y0 = yScale(cell.yKey);
        return (
          <g key={cell.key}>
            <rect
              x={x0 + 2}
              y={y0 + 2}
              width={bw - 4}
              height={bh - 4}
              fill={cell.fill}
              rx={4}
            />
            <text
              x={x0 + bw / 2}
              y={y0 + bh / 2 + 7}
              textAnchor="middle"
              fontSize={20}
              fontWeight="600"
              fill={cell.textFill}
              fontFamily={FONT}
            >
              {cell.value.toFixed(2)}
            </text>
          </g>
        );
      })}

      {/* Diverging colorbar legend */}
      <text
        x={barX + 10}
        y={top - 14}
        textAnchor="middle"
        fontSize={14}
        fontWeight="600"
        fill={t.inkSoft}
        fontFamily={FONT}
      >
        {CORRELATION}
      </text>
      <rect x={barX} y={top} width={20} height={height} fill="url(#divGrad)" rx={3} />
      {COLORBAR_TICKS.map((tick) => {
        const ty = top + height * (1 - (tick - DOMAIN_MIN) / (DOMAIN_MAX - DOMAIN_MIN));
        return (
          <g key={tick}>
            <line x1={barX + 20} y1={ty} x2={barX + 27} y2={ty} stroke={t.inkSoft} strokeWidth={1} />
            <text x={barX + 32} y={ty + 5} fontSize={14} fill={t.inkSoft} fontFamily={FONT}>
              {tick.toFixed(1)}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const margin = { left: 20, top: 96, right: 118, bottom: 28 };
  const subtitle = `${CORRELATION} matrix (${xCategories.length} × ${yCategories.length})`;

  return (
    <ChartsContainer
      width={W}
      height={H}
      margin={margin}
      series={[]}
      skipAnimation
      xAxis={[
        {
          id: "vars_x",
          scaleType: "band",
          data: xCategories,
          height: 54,
          categoryGapRatio: 0.04,
          tickLabelStyle: { fontSize: 15, fill: t.inkSoft, fontFamily: FONT },
        },
      ]}
      yAxis={[
        {
          id: "vars_y",
          scaleType: "band",
          data: yCategories,
          width: 128,
          categoryGapRatio: 0.04,
          tickLabelStyle: { fontSize: 15, fill: t.inkSoft, fontFamily: FONT },
        },
      ]}
    >
      <text x={W / 2} y={38} textAnchor="middle" fontSize={22} fontWeight="600" fill={t.ink} fontFamily={FONT}>
        {TITLE}
      </text>
      <text x={W / 2} y={64} textAnchor="middle" fontSize={15} fill={t.inkSoft} fontFamily={FONT}>
        {subtitle}
      </text>
      <HeatmapLayer />
      <ChartsXAxis axisId="vars_x" />
      <ChartsYAxis axisId="vars_y" />
    </ChartsContainer>
  );
}
