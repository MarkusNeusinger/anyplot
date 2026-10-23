// anyplot.ai
// confusion-matrix: Confusion Matrix Heatmap
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 87/100 | Updated: 2026-10-23
//# anyplot-orientation: square
// anyplot.ai
// confusion-matrix: Confusion Matrix Heatmap
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-04

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";

const tokens = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const TRUE_LABELS = "True Label"; // role: true_labels
const PREDICTED_LABELS = "Predicted Label"; // role: predicted_labels

// Data: replace this block with your own records, one object per row
const data = (() => {
  const sampleClasses = ["Paper", "Glass", "Metal", "Plastic", "Organic"];
  const countsMatrix = [
    [182, 4, 1, 6, 3],
    [5, 151, 3, 9, 2],
    [1, 4, 142, 11, 0],
    [7, 9, 12, 158, 5],
    [2, 1, 0, 6, 176],
  ];
  const rows: {
    [TRUE_LABELS]: string;
    [PREDICTED_LABELS]: string;
  }[] = [];
  sampleClasses.forEach((trueClass, r) => {
    sampleClasses.forEach((predictedClass, c) => {
      const n = countsMatrix[r][c];
      for (let k = 0; k < n; k += 1) {
        rows.push({
          [TRUE_LABELS]: trueClass,
          [PREDICTED_LABELS]: predictedClass,
        });
      }
    });
  });
  return rows;
})();

// Plot: reads only data and the constants above
// Every class seen as a true or a predicted label, in order of first appearance,
// so a class that is only ever predicted still gets its row and column.
const classes = Array.from(
  new Set(data.flatMap((d) => [d[TRUE_LABELS], d[PREDICTED_LABELS]])),
);

const pairCounts = new Map<string, number>();
const rowTotals = new Map<string, number>();
data.forEach((d) => {
  const tLabel = d[TRUE_LABELS];
  const pLabel = d[PREDICTED_LABELS];
  const key = `${tLabel}__${pLabel}`;
  pairCounts.set(key, (pairCounts.get(key) ?? 0) + 1);
  rowTotals.set(tLabel, (rowTotals.get(tLabel) ?? 0) + 1);
});

const points: {
  id: string;
  x: string;
  y: string;
  z: number;
  count: number;
  rowPct: number;
}[] = [];
let maxCount = 0;
classes.forEach((trueClass, row) => {
  const rowTotal = rowTotals.get(trueClass) ?? 1;
  classes.forEach((predictedClass, col) => {
    const count = pairCounts.get(`${trueClass}__${predictedClass}`) ?? 0;
    if (count > maxCount) maxCount = count;
    points.push({
      id: `${row}-${col}`,
      x: predictedClass,
      y: trueClass,
      z: count,
      count,
      rowPct: Math.round((count / rowTotal) * 100),
    });
  });
});

function mixHex(hexA: string, hexB: string, ratio: number) {
  const a = parseInt(hexA.slice(1), 16);
  const b = parseInt(hexB.slice(1), 16);
  const channel = (shift: number) => {
    const av = (a >> shift) & 255;
    const bv = (b >> shift) & 255;
    return Math.round(av + (bv - av) * ratio);
  };
  return `#${[16, 8, 0].map((shift) => channel(shift).toString(16).padStart(2, "0")).join("")}`;
}

function sequentialColor(t: number) {
  const [low, high] = tokens.seq;
  return mixHex(low, high, Math.pow(t, 0.45));
}

function relativeLuminance(hex: string) {
  const n = parseInt(hex.slice(1), 16);
  const r = ((n >> 16) & 255) / 255;
  const g = ((n >> 8) & 255) / 255;
  const b = (n & 255) / 255;
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function ConfusionCell(props: any) {
  const { series, xScale, yScale, colorGetter, color } = props;
  const cellWidth = xScale.bandwidth();
  const cellHeight = yScale.bandwidth();
  const countFontSize = Math.round(Math.min(cellWidth, cellHeight) * 0.2);
  const pctFontSize = Math.round(countFontSize * 0.55);

  return (
    <g>
      {series.data.map((point: any, i: number) => {
        const x0 = xScale(point.x) ?? 0;
        const y0 = yScale(point.y) ?? 0;
        const fill = colorGetter ? colorGetter(i) : color;
        const textFill = relativeLuminance(fill) > 0.55 ? "#1A1A17" : "#F0EFE8";
        const isCorrect = point.x === point.y;
        return (
          <g key={point.id}>
            <rect
              x={x0}
              y={y0}
              width={cellWidth}
              height={cellHeight}
              fill={fill}
              stroke={isCorrect ? tokens.ink : "none"}
              strokeWidth={isCorrect ? 4 : 0}
            />
            <text
              x={x0 + cellWidth / 2}
              y={y0 + cellHeight / 2 - pctFontSize * 0.7}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={countFontSize}
              fontWeight={isCorrect ? 700 : 400}
              fontFamily="inherit"
              fill={textFill}
            >
              {point.count}
            </text>
            <text
              x={x0 + cellWidth / 2}
              y={y0 + cellHeight / 2 + countFontSize * 0.6}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={pctFontSize}
              fontFamily="inherit"
              fill={textFill}
              opacity={0.85}
            >
              {point.rowPct}%
            </text>
          </g>
        );
      })}
    </g>
  );
}

// Color bar with a title naming what the color and the in-cell percentages show
function CountLegend({ sx, ...legendProps }: any) {
  return (
    <Box sx={{ gridArea: "legend", width: "50%", mb: "20px", mr: "20px", fontFamily: "inherit" }}>
      <Typography sx={{ color: tokens.ink, fontSize: 16, fontWeight: 500, fontFamily: "inherit", mb: "6px" }}>
        Count · % = share of true-class row (recall)
      </Typography>
      <ContinuousColorLegend {...legendProps} sx={{ ...sx, width: "100%" }} />
    </Box>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const TITLE_HEIGHT = 80;
  const RIGHT_BUFFER = 40;
  const BOTTOM_BUFFER = 64;
  const chartWidth = width - RIGHT_BUFFER;
  const chartHeight = height - TITLE_HEIGHT - BOTTOM_BUFFER;

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
        confusion-matrix · javascript · muix · anyplot.ai
      </Typography>
      <Box sx={{ flex: 1, display: "flex", alignItems: "flex-start", justifyContent: "flex-start" }}>
        <ScatterChart
          width={chartWidth}
          height={chartHeight}
          skipAnimation
          disableHitArea
          series={[
            {
              id: "confusion",
              type: "scatter",
              data: points,
              label: "Predictions",
              xAxisId: "predicted",
              yAxisId: "actual",
              zAxisId: "count",
            },
          ]}
          xAxis={[
            {
              id: "predicted",
              position: "top",
              height: 84,
              scaleType: "band",
              data: classes,
              categoryGapRatio: 0.08,
              label: PREDICTED_LABELS,
              labelStyle: { fontSize: 18, fill: tokens.ink, fontFamily: "inherit" },
              tickLabelStyle: { fontSize: 16, fill: tokens.inkSoft, fontFamily: "inherit" },
              disableTicks: true,
              disableLine: true,
            },
          ]}
          yAxis={[
            {
              id: "actual",
              position: "left",
              width: 140,
              scaleType: "band",
              data: classes,
              categoryGapRatio: 0.08,
              label: TRUE_LABELS,
              labelStyle: { fontSize: 18, fill: tokens.ink, fontFamily: "inherit" },
              tickLabelStyle: { fontSize: 16, fill: tokens.inkSoft, fontFamily: "inherit" },
              disableTicks: true,
              disableLine: true,
            },
          ]}
          zAxis={[
            {
              id: "count",
              min: 0,
              max: maxCount,
              colorMap: { type: "continuous", min: 0, max: maxCount, color: sequentialColor },
            },
          ]}
          margin={{ top: 20, right: 20, bottom: 24, left: 60 }}
          slots={{ scatter: ConfusionCell, legend: CountLegend }}
          slotProps={{
            legend: {
              axisId: "count",
              axisDirection: "z",
              direction: "horizontal",
              position: { vertical: "bottom", horizontal: "end" },
              thickness: 14,
              sx: {
                color: tokens.inkSoft,
                fontSize: 16,
                fontFamily: "inherit",
              },
            } as any,
          }}
        />
      </Box>
    </Box>
  );
}
