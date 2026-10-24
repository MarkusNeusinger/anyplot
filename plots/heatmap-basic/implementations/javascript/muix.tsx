// anyplot.ai
// heatmap-basic: Basic Heatmap
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 73/100 | Updated: 2026-10-24
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SIZE = window.ANYPLOT_SIZE;
const TITLE = "heatmap-basic · javascript · muix · anyplot.ai";
const DOMAIN_MIN = -1;
const DOMAIN_MAX = 1;
const COLORBAR_TICKS = [-1.0, -0.5, 0.0, 0.5, 1.0];
const MARGIN = { top: 104, right: 138, bottom: 32, left: 20 };

// Columns: set these to your data's column names
const COL_METRIC = "Column metric"; // role: x
const ROW_METRIC = "Row metric"; // role: y
const CORRELATION = "Correlation coefficient"; // role: value

// Data: replace this block with your own records
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
      [ROW_METRIC]: METRIC_NAMES[row],
      [COL_METRIC]: METRIC_NAMES[col],
      [CORRELATION]: val,
    });
  }
}

// Plot: reads only data and the constants above
const xCategories = Array.from(new Set(data.map((r) => String(r[COL_METRIC]))));
const yCategories = Array.from(new Set(data.map((r) => String(r[ROW_METRIC]))));

const cells = data.map((row, idx) => ({
  id: `${idx}-${row[ROW_METRIC]}-${row[COL_METRIC]}`,
  x: String(row[COL_METRIC]),
  y: String(row[ROW_METRIC]),
  value: Number(row[CORRELATION]),
}));

// Three-stop imprint_div ramp: red at 0, page-colored midpoint at 0.5, blue at 1
const hexToRgb = (hex: string) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
const DIV_STOPS = t.div.map(hexToRgb);

function divergingColor(frac: number): string {
  const f = Math.min(1, Math.max(0, frac));
  const [from, to, local] = f < 0.5 ? [DIV_STOPS[0], DIV_STOPS[1], f * 2] : [DIV_STOPS[1], DIV_STOPS[2], (f - 0.5) * 2];
  const [r, g, b] = from.map((c, i) => Math.round(c + (to[i] - c) * local));
  return `rgb(${r}, ${g}, ${b})`;
}

function HeatmapCells() {
  const xScale = useXScale() as unknown as ((v: string) => number) & { bandwidth: () => number };
  const yScale = useYScale() as unknown as ((v: string) => number) & { bandwidth: () => number };
  const colorScale = useZColorScale() as (v: number) => string;
  const { left, top, width, height } = useDrawingArea();

  const bw = xScale.bandwidth();
  const bh = yScale.bandwidth();
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
        const x = xScale(cell.x);
        const y = yScale(cell.y);
        const fill = colorScale(cell.value);
        const [r, g, b] = (fill.match(/[\d.]+/g) ?? ["128", "128", "128"]).map(Number);
        const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
        const textFill = luminance > 140 ? "#1A1A17" : "#FAF8F1";

        return (
          <g key={cell.id}>
            <rect x={x} y={y} width={bw} height={bh} fill={fill} rx={4} />
            <text
              x={x + bw / 2}
              y={y + bh / 2}
              fontSize={16}
              fontWeight={600}
              fill={textFill}
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
        {CORRELATION}
      </text>
    </g>
  );
}

export default function Chart() {
  const subtitle = `${CORRELATION} matrix (${xCategories.length} × ${yCategories.length})`;

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
      zAxis={[
        {
          colorMap: {
            type: "continuous",
            min: DOMAIN_MIN,
            max: DOMAIN_MAX,
            color: divergingColor,
          },
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
