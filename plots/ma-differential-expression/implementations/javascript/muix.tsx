// anyplot.ai
// ma-differential-expression: MA Plot for Differential Expression
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: pending | Created: 2026-06-21

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const LFC_THRESHOLD = 1;
const N_SMOOTH_BINS = 24;
const SMOOTH_BW_FACTOR = 2.2;
const NOT_SIG_ALPHA_HEX = "55";
const X_PAD_SHARE = 0.02;
const Y_PAD_SHARE = 0.06;

const NOT_SIG_LABEL = "Not significant";
const UP_REG_LABEL = "Up-regulated";
const DOWN_REG_LABEL = "Down-regulated";

const SEMANTIC_COLORS: Record<string, string> = {
  [UP_REG_LABEL]: t.palette[0],
  [DOWN_REG_LABEL]: t.palette[4],
};

// Columns: set these to your data's column names
const MEAN_EXPR = "Mean expression (log₂ A)"; // role: mean_expression
const LFC = "Log₂ fold change (M)"; // role: log_fold_change
const SIG = "Significant"; // role: significant

// Data: replace this block with your own records
const N_GENES = 10000;
const PADJ_CUTOFF = 0.05;
const MIN_SIG_LFC = 0.5;
let seed = 42 >>> 0;

const data: Array<Record<string, number | boolean>> = [];
for (let i = 0; i < N_GENES; i++) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const r1 = seed / 0x100000000;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const r2 = seed / 0x100000000;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const r3 = seed / 0x100000000;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const r4 = seed / 0x100000000;

  const a = r1 * 6;
  const dispersion = 2.5 / (a + 0.8);
  const m = (r2 - 0.5) * 5 * dispersion + (r3 - 0.5) * 0.3;
  const padj = Math.exp(-Math.abs(m) * (a + 0.3) * 0.8) * r4;
  const sig = padj < PADJ_CUTOFF && Math.abs(m) > MIN_SIG_LFC;

  data.push({
    [MEAN_EXPR]: a,
    [LFC]: m,
    [SIG]: sig,
  });
}

// Plot: reads only data and the constants above
let minA = Infinity;
let maxA = -Infinity;
let minM = Infinity;
let maxM = -Infinity;
for (const row of data) {
  const a = Number(row[MEAN_EXPR]);
  const m = Number(row[LFC]);
  if (a < minA) minA = a;
  if (a > maxA) maxA = a;
  if (m < minM) minM = m;
  if (m > maxM) maxM = m;
}
const rawXSpan = maxA - minA;
const xAxisMin = minA - rawXSpan * X_PAD_SHARE;
const xAxisMax = maxA + rawXSpan * X_PAD_SHARE;
const maxAbsM = Math.max(Math.abs(minM), Math.abs(maxM));
const yBound = maxAbsM * (1 + Y_PAD_SHARE);
const yAxisMin = -yBound;
const yAxisMax = yBound;

const usedColors = new Set(Object.values(SEMANTIC_COLORS));
let nextPaletteIdx = 0;
const statusColorMap: Record<string, string> = {
  [NOT_SIG_LABEL]: `${t.inkSoft}${NOT_SIG_ALPHA_HEX}`,
  [UP_REG_LABEL]: SEMANTIC_COLORS[UP_REG_LABEL],
  [DOWN_REG_LABEL]: SEMANTIC_COLORS[DOWN_REG_LABEL],
};
while (usedColors.has(t.palette[nextPaletteIdx])) nextPaletteIdx++;
const trendColor = t.palette[nextPaletteIdx];

const notSigPts: Array<{ id: number; x: number; y: number }> = [];
const upRegPts: Array<{ id: number; x: number; y: number }> = [];
const downRegPts: Array<{ id: number; x: number; y: number }> = [];

for (let i = 0; i < data.length; i++) {
  const row = data[i];
  const pt = { id: i, x: Number(row[MEAN_EXPR]), y: Number(row[LFC]) };
  if (!row[SIG]) {
    notSigPts.push(pt);
  } else if (pt.y > 0) {
    upRegPts.push(pt);
  } else {
    downRegPts.push(pt);
  }
}

// Windowed tricube local average (LOESS trend) across expression range
const smoothPoints: Array<{ x: number; y: number }> = [];
const xSpan = xAxisMax - xAxisMin;
const bw = (xSpan / N_SMOOTH_BINS) * SMOOTH_BW_FACTOR;
for (let b = 0; b <= N_SMOOTH_BINS; b++) {
  const cx = xAxisMin + (b * xSpan) / N_SMOOTH_BINS;
  let wSum = 0;
  let wySum = 0;
  for (let i = 0; i < data.length; i++) {
    const dx = Math.abs(Number(data[i][MEAN_EXPR]) - cx);
    if (dx < bw) {
      const u = dx / bw;
      const w = Math.pow(1 - u * u * u, 3);
      wSum += w;
      wySum += w * Number(data[i][LFC]);
    }
  }
  if (wSum > 0) {
    smoothPoints.push({ x: cx, y: wySum / wSum });
  }
}

function MaOverlay() {
  const xScale = useXScale("x") as (v: number) => number;
  const yScale = useYScale("y") as (v: number) => number;

  const R = 6.5;
  const H = R * 0.866;

  const smoothD = smoothPoints
    .map((p, i) => `${i === 0 ? "M" : "L"}${xScale(p.x).toFixed(1)},${yScale(p.y).toFixed(1)}`)
    .join(" ");

  return (
    <g>
      {upRegPts.map((p) => {
        const x = xScale(p.x);
        const y = yScale(p.y);
        return (
          <polygon
            key={p.id}
            points={`${x},${y - R} ${x - H},${y + R * 0.5} ${x + H},${y + R * 0.5}`}
            fill={statusColorMap[UP_REG_LABEL]}
          />
        );
      })}
      {downRegPts.map((p) => {
        const x = xScale(p.x);
        const y = yScale(p.y);
        return (
          <polygon
            key={p.id}
            points={`${x},${y + R} ${x - H},${y - R * 0.5} ${x + H},${y - R * 0.5}`}
            fill={statusColorMap[DOWN_REG_LABEL]}
          />
        );
      })}
      <path
        d={smoothD}
        fill="none"
        stroke={trendColor}
        strokeWidth={3}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Reference lines and right-margin threshold labels drawn above the dense cloud */}
      <line
        x1={xScale(xAxisMin)}
        y1={yScale(0)}
        x2={xScale(xAxisMax)}
        y2={yScale(0)}
        stroke={t.ink}
        strokeWidth={1.8}
        strokeOpacity={0.75}
      />
      <line
        x1={xScale(xAxisMin)}
        y1={yScale(LFC_THRESHOLD)}
        x2={xScale(xAxisMax)}
        y2={yScale(LFC_THRESHOLD)}
        stroke={t.ink}
        strokeWidth={1.6}
        strokeDasharray="8 4"
        strokeOpacity={0.85}
      />
      <line
        x1={xScale(xAxisMin)}
        y1={yScale(-LFC_THRESHOLD)}
        x2={xScale(xAxisMax)}
        y2={yScale(-LFC_THRESHOLD)}
        stroke={t.ink}
        strokeWidth={1.6}
        strokeDasharray="8 4"
        strokeOpacity={0.85}
      />
      <text
        x={xScale(xAxisMax) + 10}
        y={yScale(LFC_THRESHOLD)}
        fontSize={14}
        fill={t.inkSoft}
        dominantBaseline="middle"
      >
        {`log₂FC = +${LFC_THRESHOLD}`}
      </text>
      <text
        x={xScale(xAxisMax) + 10}
        y={yScale(-LFC_THRESHOLD)}
        fontSize={14}
        fill={t.inkSoft}
        dominantBaseline="middle"
      >
        {`log₂FC = −${LFC_THRESHOLD}`}
      </text>
    </g>
  );
}

const LEGEND_ITEMS = [
  { label: NOT_SIG_LABEL, color: t.inkSoft, kind: "dot" as const },
  { label: UP_REG_LABEL, color: statusColorMap[UP_REG_LABEL], kind: "up" as const },
  { label: DOWN_REG_LABEL, color: statusColorMap[DOWN_REG_LABEL], kind: "down" as const },
  { label: "LOESS trend", color: trendColor, kind: "line" as const },
];

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const TITLE_H = 54;
  const LEGEND_H = 42;
  const chartH = height - TITLE_H - LEGEND_H;

  return (
    <Box
      sx={{
        width,
        height,
        display: "flex",
        flexDirection: "column",
        bgcolor: t.pageBg,
      }}
    >
      <Typography
        sx={{
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
          px: 4,
          flexShrink: 0,
        }}
      >
        ma-differential-expression · javascript · muix · anyplot.ai
      </Typography>

      <ChartsContainer
        width={width}
        height={chartH}
        skipAnimation
        margin={{ top: 12, right: 116, bottom: 16, left: 20 }}
        series={[
          {
            type: "scatter",
            id: "notSig",
            label: NOT_SIG_LABEL,
            data: notSigPts,
            color: statusColorMap[NOT_SIG_LABEL],
            markerSize: 2.5,
            xAxisId: "x",
            yAxisId: "y",
          },
        ]}
        xAxis={[
          {
            id: "x",
            scaleType: "linear",
            min: xAxisMin,
            max: xAxisMax,
            height: 54,
            label: MEAN_EXPR,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            tickNumber: 7,
          },
        ]}
        yAxis={[
          {
            id: "y",
            scaleType: "linear",
            min: yAxisMin,
            max: yAxisMax,
            width: 76,
            label: LFC,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            tickNumber: 9,
          },
        ]}
      >
        <ChartsGrid horizontal />
        <ScatterPlot />
        <MaOverlay />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId="y" />
      </ChartsContainer>

      <Box
        sx={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "28px",
          pb: "6px",
        }}
      >
        {LEGEND_ITEMS.map((item) => (
          <Box
            key={item.label}
            sx={{ display: "flex", alignItems: "center", gap: "8px" }}
          >
            {item.kind === "dot" ? (
              <Box
                sx={{
                  width: 9,
                  height: 9,
                  borderRadius: "50%",
                  bgcolor: item.color,
                  opacity: 0.65,
                }}
              />
            ) : item.kind === "up" ? (
              <svg width={14} height={14} viewBox="0 0 14 14">
                <polygon points="7,1 1,12 13,12" fill={item.color} />
              </svg>
            ) : item.kind === "down" ? (
              <svg width={14} height={14} viewBox="0 0 14 14">
                <polygon points="7,13 1,2 13,2" fill={item.color} />
              </svg>
            ) : (
              <Box
                sx={{
                  width: 20,
                  height: 3.5,
                  bgcolor: item.color,
                  borderRadius: "2px",
                }}
              />
            )}
            <Typography sx={{ color: t.inkSoft, fontSize: "14px", lineHeight: 1 }}>
              {item.label}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
