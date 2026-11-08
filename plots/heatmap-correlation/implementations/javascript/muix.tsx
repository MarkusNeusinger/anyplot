// anyplot.ai
// heatmap-correlation: Correlation Matrix Heatmap
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-08-18
//# anyplot-orientation: square
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const R_MIN = -1; // the colour bar spans the full correlation range
const R_MAX = 1;
const COLORBAR_TICKS = [-1, -0.5, 0, 0.5, 1];
const TITLE = "heatmap-correlation · javascript · muix · anyplot.ai";
const TITLE_H = 92;
const Y_AXIS_W = 130;
const X_AXIS_H = 48;
const COLORBAR_AREA_W = 150;
const DIV_RGB = t.div.map((hex: string) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)));

// Columns: set these to your data's column names
const ASSET = "Asset class"; // role: variables
const CORRELATION = "Correlation (Pearson r)"; // role: correlation_matrix

// Data: replace this block with your own records, one row of the square matrix per object,
// keyed by the row's name and one column per variable
// Correlations of monthly returns across six asset classes in a diversified portfolio
const data = [
  { [ASSET]: "Equities", Equities: 1.0, Bonds: -0.35, "Real Estate": 0.55, Commodities: 0.2, Gold: -0.1, Cash: -0.05 },
  { [ASSET]: "Bonds", Equities: -0.35, Bonds: 1.0, "Real Estate": 0.15, Commodities: -0.2, Gold: 0.3, Cash: 0.1 },
  { [ASSET]: "Real Estate", Equities: 0.55, Bonds: 0.15, "Real Estate": 1.0, Commodities: 0.25, Gold: 0.05, Cash: -0.15 },
  { [ASSET]: "Commodities", Equities: 0.2, Bonds: -0.2, "Real Estate": 0.25, Commodities: 1.0, Gold: 0.65, Cash: -0.1 },
  { [ASSET]: "Gold", Equities: -0.1, Bonds: 0.3, "Real Estate": 0.05, Commodities: 0.65, Gold: 1.0, Cash: 0.2 },
  { [ASSET]: "Cash", Equities: -0.05, Bonds: 0.1, "Real Estate": -0.15, Commodities: -0.1, Gold: 0.2, Cash: 1.0 },
];

// Plot: reads only data and the constants above
// The variable list comes from the row labels and the column keys, in order of first appearance
const variables = [
  ...new Set([...data.map((d) => String(d[ASSET])), ...data.flatMap((d) => Object.keys(d).filter((k) => k !== ASSET))]),
];
const rowOf = new Map(data.map((d) => [String(d[ASSET]), d]));

// The matrix is symmetric: show the diagonal and the lower triangle, mask the mirrored upper triangle
const cells = variables.flatMap((row, i) =>
  variables.slice(0, i + 1).map((col) => ({ key: `${row}|${col}`, row, col, r: Number(rowOf.get(row)?.[col]) })),
);
const offDiagonal = cells.filter((c) => c.row !== c.col && Number.isFinite(c.r));
const strongest = offDiagonal.reduce((best, c) => (Math.abs(c.r) > Math.abs(best.r) ? c : best), offDiagonal[0]);
const subtitle = `${variables.length} × ${variables.length} matrix, lower triangle shown (the upper one mirrors it) · strongest pair: ${strongest.row} – ${strongest.col}, r = ${strongest.r.toFixed(2)}`;

function CorrelationLayer() {
  const xScale = useXScale() as unknown as ((v: string) => number) & { bandwidth: () => number };
  const yScale = useYScale() as unknown as ((v: string) => number) & { bandwidth: () => number };
  const colorScale = useZColorScale() as unknown as (v: number) => string;
  const { left, top, width, height } = useDrawingArea();
  const cellW = xScale.bandwidth();
  const cellH = yScale.bandwidth();
  const barX = left + width + 36;
  const barW = 22;
  return (
    <g>
      <defs>
        <linearGradient id="correlation-colorbar" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.div[0]} />
          <stop offset="50%" stopColor={t.div[1]} />
          <stop offset="100%" stopColor={t.div[2]} />
        </linearGradient>
      </defs>
      {cells
        .filter((c) => Number.isFinite(c.r))
        .map((c) => {
          const fill = colorScale(c.r);
          const [r, g, b] = (fill.match(/\d+/g) ?? []).map(Number);
          const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
          return (
            <g key={c.key}>
              <rect x={xScale(c.col)} y={yScale(c.row)} width={cellW} height={cellH} fill={fill} stroke={t.grid} strokeWidth={1} />
              <text
                x={xScale(c.col) + cellW / 2}
                y={yScale(c.row) + cellH / 2}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={24}
                fontWeight={600}
                fill={luminance > 0.5 ? "#1A1A17" : "#FAF8F1"}
              >
                {c.r.toFixed(2)}
              </text>
            </g>
          );
        })}
      <rect x={barX} y={top} width={barW} height={height} fill="url(#correlation-colorbar)" stroke={t.inkSoft} strokeWidth={1} />
      {COLORBAR_TICKS.map((tick) => {
        const ty = top + height * (1 - (tick - R_MIN) / (R_MAX - R_MIN));
        return (
          <g key={tick}>
            <line x1={barX + barW} x2={barX + barW + 6} y1={ty} y2={ty} stroke={t.inkSoft} strokeWidth={1} />
            <text x={barX + barW + 10} y={ty} fontSize={14} fill={t.inkSoft} dominantBaseline="central">
              {tick.toFixed(1)}
            </text>
          </g>
        );
      })}
      <text
        x={barX + barW + 66}
        y={top + height / 2}
        fontSize={16}
        fill={t.ink}
        textAnchor="middle"
        transform={`rotate(-90, ${barX + barW + 66}, ${top + height / 2})`}
      >
        {CORRELATION}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartH = height - TITLE_H;
  // Square cells: the matrix is a square of the smaller available side, centred vertically
  const availW = width - 16 - Y_AXIS_W - COLORBAR_AREA_W;
  const availH = chartH - 32 - X_AXIS_H;
  const side = Math.min(availW, availH);
  return (
    <Box sx={{ width, height, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, pt: "20px", px: "24px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, mt: "6px" }}>{subtitle}</Typography>
      </Box>
      <ChartsContainer
        width={width}
        height={chartH}
        series={[]}
        skipAnimation
        margin={{
          top: 16 + (availH - side) / 2,
          bottom: 16 + (availH - side) / 2,
          left: 16,
          right: COLORBAR_AREA_W + availW - side,
        }}
        xAxis={[
          {
            scaleType: "band",
            data: variables,
            height: X_AXIS_H,
            categoryGapRatio: 0.04,
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: { fontSize: 16, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: variables,
            width: Y_AXIS_W,
            categoryGapRatio: 0.04,
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: { fontSize: 16, fill: t.inkSoft },
          },
        ]}
        zAxis={[
          {
            colorMap: {
              type: "continuous",
              min: R_MIN,
              max: R_MAX,
              // Three-stop Imprint diverging ramp: red at −1, the page colour at 0, blue at +1
              color: (f: number) => {
                const [from, to, share] = f < 0.5 ? [DIV_RGB[0], DIV_RGB[1], f * 2] : [DIV_RGB[1], DIV_RGB[2], f * 2 - 1];
                return `rgb(${from.map((c: number, i: number) => Math.round(c + (to[i] - c) * share)).join(", ")})`;
              },
            },
          },
        ]}
      >
        <CorrelationLayer />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </Box>
  );
}
