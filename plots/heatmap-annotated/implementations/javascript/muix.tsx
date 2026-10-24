// anyplot.ai
// heatmap-annotated: Annotated Heatmap
// Library: muix 9.2.1 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-08-05
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const W = window.ANYPLOT_SIZE.width;
const H = window.ANYPLOT_SIZE.height;

// Constants
const X_COL = "x";
const Y_COL = "y";
const VALUE_COL = "value";

const FONT = "system-ui, -apple-system, sans-serif";
const TITLE = "heatmap-annotated · javascript · muix · anyplot.ai";
const SUBTITLE_PREFIX = "Pearson correlation matrix across daily wellness metrics";
const COLORBAR_LABEL = "Pearson r";
const DOMAIN_MIN = -1;
const DOMAIN_MID = 0;
const DOMAIN_MAX = 1;
const COLORBAR_TICKS = [-1.0, -0.5, 0.0, 0.5, 1.0];

// Data — symmetric 7x7 Pearson correlation matrix across daily wellness metrics
const data: Record<string, string | number>[] = [
  { [Y_COL]: "Sleep", [X_COL]: "Sleep", [VALUE_COL]: 1.0 },
  { [Y_COL]: "Sleep", [X_COL]: "Exercise", [VALUE_COL]: 0.35 },
  { [Y_COL]: "Sleep", [X_COL]: "Screen Time", [VALUE_COL]: -0.42 },
  { [Y_COL]: "Sleep", [X_COL]: "Stress", [VALUE_COL]: -0.58 },
  { [Y_COL]: "Sleep", [X_COL]: "Water", [VALUE_COL]: 0.22 },
  { [Y_COL]: "Sleep", [X_COL]: "Steps", [VALUE_COL]: 0.31 },
  { [Y_COL]: "Sleep", [X_COL]: "Mood", [VALUE_COL]: 0.61 },

  { [Y_COL]: "Exercise", [X_COL]: "Sleep", [VALUE_COL]: 0.35 },
  { [Y_COL]: "Exercise", [X_COL]: "Exercise", [VALUE_COL]: 1.0 },
  { [Y_COL]: "Exercise", [X_COL]: "Screen Time", [VALUE_COL]: -0.28 },
  { [Y_COL]: "Exercise", [X_COL]: "Stress", [VALUE_COL]: -0.33 },
  { [Y_COL]: "Exercise", [X_COL]: "Water", [VALUE_COL]: 0.45 },
  { [Y_COL]: "Exercise", [X_COL]: "Steps", [VALUE_COL]: 0.82 },
  { [Y_COL]: "Exercise", [X_COL]: "Mood", [VALUE_COL]: 0.57 },

  { [Y_COL]: "Screen Time", [X_COL]: "Sleep", [VALUE_COL]: -0.42 },
  { [Y_COL]: "Screen Time", [X_COL]: "Exercise", [VALUE_COL]: -0.28 },
  { [Y_COL]: "Screen Time", [X_COL]: "Screen Time", [VALUE_COL]: 1.0 },
  { [Y_COL]: "Screen Time", [X_COL]: "Stress", [VALUE_COL]: 0.49 },
  { [Y_COL]: "Screen Time", [X_COL]: "Water", [VALUE_COL]: -0.18 },
  { [Y_COL]: "Screen Time", [X_COL]: "Steps", [VALUE_COL]: -0.39 },
  { [Y_COL]: "Screen Time", [X_COL]: "Mood", [VALUE_COL]: -0.44 },

  { [Y_COL]: "Stress", [X_COL]: "Sleep", [VALUE_COL]: -0.58 },
  { [Y_COL]: "Stress", [X_COL]: "Exercise", [VALUE_COL]: -0.33 },
  { [Y_COL]: "Stress", [X_COL]: "Screen Time", [VALUE_COL]: 0.49 },
  { [Y_COL]: "Stress", [X_COL]: "Stress", [VALUE_COL]: 1.0 },
  { [Y_COL]: "Stress", [X_COL]: "Water", [VALUE_COL]: -0.15 },
  { [Y_COL]: "Stress", [X_COL]: "Steps", [VALUE_COL]: -0.36 },
  { [Y_COL]: "Stress", [X_COL]: "Mood", [VALUE_COL]: -0.71 },

  { [Y_COL]: "Water", [X_COL]: "Sleep", [VALUE_COL]: 0.22 },
  { [Y_COL]: "Water", [X_COL]: "Exercise", [VALUE_COL]: 0.45 },
  { [Y_COL]: "Water", [X_COL]: "Screen Time", [VALUE_COL]: -0.18 },
  { [Y_COL]: "Water", [X_COL]: "Stress", [VALUE_COL]: -0.15 },
  { [Y_COL]: "Water", [X_COL]: "Water", [VALUE_COL]: 1.0 },
  { [Y_COL]: "Water", [X_COL]: "Steps", [VALUE_COL]: 0.28 },
  { [Y_COL]: "Water", [X_COL]: "Mood", [VALUE_COL]: 0.19 },

  { [Y_COL]: "Steps", [X_COL]: "Sleep", [VALUE_COL]: 0.31 },
  { [Y_COL]: "Steps", [X_COL]: "Exercise", [VALUE_COL]: 0.82 },
  { [Y_COL]: "Steps", [X_COL]: "Screen Time", [VALUE_COL]: -0.39 },
  { [Y_COL]: "Steps", [X_COL]: "Stress", [VALUE_COL]: -0.36 },
  { [Y_COL]: "Steps", [X_COL]: "Water", [VALUE_COL]: 0.28 },
  { [Y_COL]: "Steps", [X_COL]: "Steps", [VALUE_COL]: 1.0 },
  { [Y_COL]: "Steps", [X_COL]: "Mood", [VALUE_COL]: 0.52 },

  { [Y_COL]: "Mood", [X_COL]: "Sleep", [VALUE_COL]: 0.61 },
  { [Y_COL]: "Mood", [X_COL]: "Exercise", [VALUE_COL]: 0.57 },
  { [Y_COL]: "Mood", [X_COL]: "Screen Time", [VALUE_COL]: -0.44 },
  { [Y_COL]: "Mood", [X_COL]: "Stress", [VALUE_COL]: -0.71 },
  { [Y_COL]: "Mood", [X_COL]: "Water", [VALUE_COL]: 0.19 },
  { [Y_COL]: "Mood", [X_COL]: "Steps", [VALUE_COL]: 0.52 },
  { [Y_COL]: "Mood", [X_COL]: "Mood", [VALUE_COL]: 1.0 },
];

// Derive ordered category lists in order of first appearance
const xCategories = Array.from(new Set(data.map((r) => String(r[X_COL]))));
const yCategories = Array.from(new Set(data.map((r) => String(r[Y_COL]))));

const divStopInts = t.div.map((hex) => parseInt(hex.replace("#", ""), 16));
const divStopsRgb: [number, number, number][] = divStopInts.map((v) => [
  (v >> 16) & 255,
  (v >> 8) & 255,
  v & 255,
]);

const cells = data.map((row) => {
  const xKey = String(row[X_COL]);
  const yKey = String(row[Y_COL]);
  const value = Number(row[VALUE_COL]);
  const [r0, g0, b0] = divStopsRgb[0];
  const [r1, g1, b1] = divStopsRgb[1];
  const [r2, g2, b2] = divStopsRgb[2];

  const isNeg = value <= DOMAIN_MID;
  const [ra, ga, ba] = isNeg ? [r0, g0, b0] : [r1, g1, b1];
  const [rb, gb, bb] = isNeg ? [r1, g1, b1] : [r2, g2, b2];
  const f = isNeg
    ? (value - DOMAIN_MIN) / (DOMAIN_MID - DOMAIN_MIN || 1)
    : (value - DOMAIN_MID) / (DOMAIN_MAX - DOMAIN_MID || 1);

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
  const xScale = useXScale("vars_x");
  const yScale = useYScale("vars_y");
  const { left, top, width, height } = useDrawingArea();

  if (!xScale || !yScale || typeof (xScale as any).bandwidth !== "function") return null;
  const bw = (xScale as any).bandwidth() as number;
  const bh = (yScale as any).bandwidth() as number;
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
        if (x0 === undefined || y0 === undefined) return null;
        return (
          <g key={cell.key}>
            <rect
              x={Number(x0) + 2}
              y={Number(y0) + 2}
              width={bw - 4}
              height={bh - 4}
              fill={cell.fill}
              rx={4}
            />
            <text
              x={Number(x0) + bw / 2}
              y={Number(y0) + bh / 2 + 7}
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
        {COLORBAR_LABEL}
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
  const subtitle = `${SUBTITLE_PREFIX} (${xCategories.length}×${yCategories.length})`;

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
