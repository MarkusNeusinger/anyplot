//# anyplot-orientation: square
// anyplot.ai
// heatmap-correlation: Correlation Matrix Heatmap
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-18

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";

const tokens = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) — portfolio diversification example ---
const variables = ["Equities", "Bonds", "Real Estate", "Commodities", "Gold", "Cash"];
const correlationMatrix = [
  [1.0, -0.35, 0.55, 0.2, -0.1, -0.05],
  [-0.35, 1.0, 0.15, -0.2, 0.3, 0.1],
  [0.55, 0.15, 1.0, 0.25, 0.05, -0.15],
  [0.2, -0.2, 0.25, 1.0, 0.65, -0.1],
  [-0.1, 0.3, 0.05, 0.65, 1.0, 0.2],
  [-0.05, 0.1, -0.15, -0.1, 0.2, 1.0],
];

// Mask the strict upper triangle — a symmetric matrix repeats every
// off-diagonal value, so only the diagonal and lower triangle carry ink.
const points = [];
for (let row = 0; row < variables.length; row += 1) {
  for (let col = 0; col <= row; col += 1) {
    points.push({
      id: `${row}-${col}`,
      x: variables[col],
      y: variables[row],
      z: correlationMatrix[row][col],
    });
  }
}

// --- Diverging Imprint color scale (imprint_div, theme-adaptive midpoint) ---
function mixHex(hexA, hexB, ratio) {
  const a = parseInt(hexA.slice(1), 16);
  const b = parseInt(hexB.slice(1), 16);
  const channel = (shift) => {
    const av = (a >> shift) & 255;
    const bv = (b >> shift) & 255;
    return Math.round(av + (bv - av) * ratio);
  };
  return `#${[16, 8, 0].map((shift) => channel(shift).toString(16).padStart(2, "0")).join("")}`;
}

// `t` arrives pre-normalized to [0, 1] by the zAxis colorMap's scaleSequential
// (from the -1..1 domain below) — 0 is the red end, 0.5 the neutral midpoint.
function divergingColor(t) {
  const [low, mid, high] = tokens.div;
  return t <= 0.5 ? mixHex(low, mid, t / 0.5) : mixHex(mid, high, (t - 0.5) / 0.5);
}

function relativeLuminance(hex) {
  const n = parseInt(hex.slice(1), 16);
  const r = ((n >> 16) & 255) / 255;
  const g = ((n >> 8) & 255) / 255;
  const b = (n & 255) / 255;
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

// Custom marker: filled square cells (matrix entries) instead of the default
// circles, each annotated with its correlation value to 2 decimal places.
function CorrelationCell(props) {
  const { series, xScale, yScale, colorGetter, color } = props;
  const cellWidth = xScale.bandwidth();
  const cellHeight = yScale.bandwidth();
  const fontSize = Math.round(Math.min(cellWidth, cellHeight) * 0.22);

  return (
    <g>
      {series.data.map((point, i) => {
        const x0 = xScale(point.x) ?? 0;
        const y0 = yScale(point.y) ?? 0;
        const fill = colorGetter ? colorGetter(i) : color;
        const textFill = relativeLuminance(fill) > 0.5 ? "#1A1A17" : "#F0EFE8";
        return (
          <g key={point.id}>
            <rect x={x0} y={y0} width={cellWidth} height={cellHeight} fill={fill} />
            <text
              x={x0 + cellWidth / 2}
              y={y0 + cellHeight / 2}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={fontSize}
              fontFamily="inherit"
              fill={textFill}
            >
              {point.z.toFixed(2)}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const TITLE_HEIGHT = 80;
  const RIGHT_BUFFER = 40; // room for the legend's max-value label at the true edge
  const TOP_MARGIN = 70;
  const LEFT_MARGIN = 160;
  const RIGHT_MARGIN = 20;
  const LEGEND_SPACE = 70;

  const chartWidth = width - RIGHT_BUFFER;
  const chartHeight = height - TITLE_HEIGHT;

  return (
    <Box sx={{ width, height, bgcolor: tokens.pageBg, display: "flex", flexDirection: "column" }}>
      <Typography
        sx={{
          color: tokens.ink,
          fontSize: 22,
          fontWeight: 500,
          textAlign: "center",
          lineHeight: 1.2,
          pt: "16px",
          height: TITLE_HEIGHT,
          fontFamily: "inherit",
        }}
      >
        heatmap-correlation · javascript · muix · anyplot.ai
      </Typography>
      <Box sx={{ flex: 1, display: "flex", alignItems: "flex-start", justifyContent: "flex-start" }}>
        <ScatterChart
          width={chartWidth}
          height={chartHeight}
          skipAnimation
          disableVoronoi
          series={[
            {
              id: "correlation",
              type: "scatter",
              data: points,
              label: "Correlation",
              xAxisId: "col",
              yAxisId: "row",
              zAxisId: "corr",
            },
          ]}
          xAxis={[
            {
              id: "col",
              scaleType: "band",
              data: variables,
              categoryGapRatio: 0.08,
              tickLabelStyle: { fontSize: 16, fill: tokens.inkSoft },
              disableTicks: true,
              disableLine: true,
            },
          ]}
          yAxis={[
            {
              id: "row",
              scaleType: "band",
              data: variables,
              categoryGapRatio: 0.08,
              tickLabelStyle: { fontSize: 16, fill: tokens.inkSoft },
              disableTicks: true,
              disableLine: true,
            },
          ]}
          zAxis={[
            {
              id: "corr",
              min: -1,
              max: 1,
              colorMap: { type: "continuous", min: -1, max: 1, color: divergingColor },
            },
          ]}
          topAxis="col"
          bottomAxis={null}
          leftAxis="row"
          rightAxis={null}
          margin={{ top: TOP_MARGIN, right: RIGHT_MARGIN, bottom: LEGEND_SPACE, left: LEFT_MARGIN }}
          slots={{ scatter: CorrelationCell }}
          slotProps={{ legend: { hidden: true } }}
        >
          <ContinuousColorLegend
            axisId="corr"
            axisDirection="z"
            position={{ horizontal: "right", vertical: "bottom" }}
            direction="row"
            length="50%"
            thickness={14}
            labelStyle={{ fontSize: 14, fill: tokens.inkSoft, fontFamily: "inherit" }}
          />
        </ScatterChart>
      </Box>
    </Box>
  );
}
