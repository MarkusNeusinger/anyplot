// anyplot.ai
// heatmap-basic: Basic Heatmap
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-08-20
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;

// Constants
const X_COL = "x";
const Y_COL = "y";
const VALUE_COL = "value";

const TITLE = "heatmap-basic · javascript · muix · anyplot.ai";
const SUBTITLE_PREFIX = "Pairwise correlation matrix across core business metrics";
const COLORBAR_LABEL = "Correlation coefficient";
const DOMAIN_MIN = -1;
const DOMAIN_MID = 0;
const DOMAIN_MAX = 1;
const COLORBAR_TICKS = [-1.0, -0.5, 0.0, 0.5, 1.0];

// Data — symmetric 8x8 correlation matrix across business metrics
const METRIC_NAMES = [
  "Revenue",
  "Marketing",
  "CSAT",
  "Headcount",
  "R&D",
  "Mkt Share",
  "OpEx",
  "Churn",
];

// Flat scalar upper-triangle correlation string per row (comma-separated for cols i+1..n-1)
const UPPER_TRIANGLE_ROWS = [
  "0.72,0.45,0.68,0.55,0.81,0.60,-0.52",
  "0.30,0.40,0.25,0.66,0.58,-0.20",
  "0.35,0.28,0.50,-0.10,-0.78",
  "0.62,0.47,0.71,-0.18",
  "0.58,0.33,-0.25",
  "0.40,-0.44",
  "0.15",
];

const parsedUpper = UPPER_TRIANGLE_ROWS.map((s) => s.split(",").map(Number));
const nMetrics = METRIC_NAMES.length;
const data: Record<string, string | number>[] = [];

for (let row = 0; row < nMetrics; row++) {
  for (let col = 0; col < nMetrics; col++) {
    const minIdx = Math.min(row, col);
    const maxIdx = Math.max(row, col);
    const val = row === col ? 1.0 : parsedUpper[minIdx][maxIdx - minIdx - 1];
    data.push({
      [Y_COL]: METRIC_NAMES[row],
      [X_COL]: METRIC_NAMES[col],
      [VALUE_COL]: val,
    });
  }
}

const xCategories = Array.from(new Set(data.map((r) => String(r[X_COL]))));
const yCategories = Array.from(new Set(data.map((r) => String(r[Y_COL]))));

const divStopInts = t.div.map((hex) => parseInt(hex.slice(1), 16));
const divStopsRgb: [number, number, number][] = divStopInts.map((v) => [
  (v >> 16) & 255,
  (v >> 8) & 255,
  v & 255,
]);

const cells = data.map((row, idx) => {
  const xKey = String(row[X_COL]);
  const yKey = String(row[Y_COL]);
  const value = Number(row[VALUE_COL]);
  const pos = (value - DOMAIN_MIN) / (DOMAIN_MAX - DOMAIN_MIN || 1);
  const isLowerHalf = pos < 0.5;
  const start = isLowerHalf ? divStopsRgb[0] : divStopsRgb[1];
  const end = isLowerHalf ? divStopsRgb[1] : divStopsRgb[2];
  const localRatio = isLowerHalf ? pos / 0.5 : (pos - 0.5) / 0.5;

  const r = Math.round(start[0] + (end[0] - start[0]) * localRatio);
  const g = Math.round(start[1] + (end[1] - start[1]) * localRatio);
  const b = Math.round(start[2] + (end[2] - start[2]) * localRatio);
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  const textFill = luminance > 140 ? "#1A1A17" : "#FAF8F1";

  return {
    id: `${idx}-${yKey}-${xKey}`,
    x: xKey,
    y: yKey,
    value,
    fill: `rgb(${r}, ${g}, ${b})`,
    textFill,
  };
});

function HeatmapCells() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { left, top, width, height } = useDrawingArea();

  if (!xScale || !yScale || typeof (xScale as any).bandwidth !== "function") return null;
  const bw = (xScale as any).bandwidth() as number;
  const bh = (yScale as any).bandwidth() as number;
  const barX = left + width + 28;
  const barW = 20;

  return (
    <g>
      <defs>
        <linearGradient id="basicHeatmapDivGrad" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.div[0]} />
          <stop offset="50%" stopColor={t.div[1]} />
          <stop offset="100%" stopColor={t.div[2]} />
        </linearGradient>
      </defs>

      {cells.map((cell) => {
        const x = Number(xScale(cell.x) ?? 0);
        const y = Number(yScale(cell.y) ?? 0);
        return (
          <g key={cell.id}>
            <rect x={x} y={y} width={bw} height={bh} fill={cell.fill} rx={4} />
            <text
              x={x + bw / 2}
              y={y + bh / 2}
              fontSize={16}
              fontWeight={600}
              fill={cell.textFill}
              textAnchor="middle"
              dominantBaseline="central"
            >
              {cell.value.toFixed(2)}
            </text>
          </g>
        );
      })}

      {/* Diverging colorbar legend */}
      <rect x={barX} y={top} width={barW} height={height} fill="url(#basicHeatmapDivGrad)" rx={3} />
      {COLORBAR_TICKS.map((tick) => {
        const ty = top + height * (1 - (tick - DOMAIN_MIN) / (DOMAIN_MAX - DOMAIN_MIN));
        return (
          <g key={tick}>
            <line x1={barX + barW} y1={ty} x2={barX + barW + 6} y2={ty} stroke={t.inkSoft} strokeWidth={1} />
            <text
              x={barX + barW + 10}
              y={ty}
              fontSize={14}
              fill={t.inkSoft}
              dominantBaseline="central"
            >
              {tick.toFixed(1)}
            </text>
          </g>
        );
      })}
      <text
        x={barX + barW + 58}
        y={top + height / 2}
        fontSize={15}
        fill={t.inkSoft}
        textAnchor="middle"
        transform={`rotate(-90, ${barX + barW + 58}, ${top + height / 2})`}
      >
        {COLORBAR_LABEL}
      </text>
    </g>
  );
}

const MARGIN = { top: 104, right: 138, bottom: 32, left: 20 };

export default function Chart() {
  const subtitle = `${SUBTITLE_PREFIX} (${xCategories.length}×${yCategories.length})`;

  return (
    <ChartsContainer
      width={SIZE.width}
      height={SIZE.height}
      series={[]}
      margin={MARGIN}
      skipAnimation
      xAxis={[
        {
          scaleType: "band",
          data: xCategories,
          height: 54,
          categoryGapRatio: 0.08,
          disableLine: true,
          disableTicks: true,
          tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
        },
      ]}
      yAxis={[
        {
          scaleType: "band",
          data: yCategories,
          width: 124,
          categoryGapRatio: 0.08,
          disableLine: true,
          disableTicks: true,
          tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
        },
      ]}
    >
      <HeatmapCells />
      <ChartsXAxis />
      <ChartsYAxis />
      <text
        x={SIZE.width / 2}
        y={42}
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
        textAnchor="middle"
      >
        {TITLE}
      </text>
      <text
        x={SIZE.width / 2}
        y={68}
        fontSize={15}
        fill={t.inkSoft}
        textAnchor="middle"
      >
        {subtitle}
      </text>
    </ChartsContainer>
  );
}
