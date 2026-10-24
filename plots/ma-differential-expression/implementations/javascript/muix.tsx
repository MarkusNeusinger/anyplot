// anyplot.ai
// ma-differential-expression: MA Plot for Differential Expression
// Library: muix 9.x | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-21

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
const MEAN_EXPR_COL = "Mean Expression (log₂ A)" as const;
const LFC_COL = "Log₂ Fold Change (M)" as const;
const SIG_COL = "Significant" as const;
const STATUS_COL = "Regulation Status" as const;

const LFC_THRESHOLD = 1;
const PADJ_CUTOFF = 0.05;
const MIN_SIG_LFC = 0.5;
const N_SMOOTH_BINS = 24;
const SMOOTH_BW_FACTOR = 2.2;
const NOT_SIG_ALPHA_HEX = "55";

const SEMANTIC_COLORS: Record<string, string> = {
  "Up-regulated": t.palette[0],
  "Down-regulated": t.palette[4],
};

// Data — simulated RNA-seq differential expression (10,000 genes)
const N_GENES = 10000;
let seed = 42 >>> 0;

const DATA: Array<Record<string, number | string | boolean>> = [];
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
  const status = !sig ? "Not significant" : m > 0 ? "Up-regulated" : "Down-regulated";

  DATA.push({
    [MEAN_EXPR_COL]: a,
    [LFC_COL]: m,
    [SIG_COL]: sig,
    [STATUS_COL]: status,
  });
}

// Derive axis bounds from data extent
let minA = Infinity;
let maxA = -Infinity;
let minM = Infinity;
let maxM = -Infinity;
for (const row of DATA) {
  const a = Number(row[MEAN_EXPR_COL]);
  const m = Number(row[LFC_COL]);
  if (a < minA) minA = a;
  if (a > maxA) maxA = a;
  if (m < minM) minM = m;
  if (m > maxM) maxM = m;
}
const xAxisMin = Math.floor(minA);
const xAxisMax = Math.ceil(maxA);
const yBound = Math.ceil(Math.max(Math.abs(minM), Math.abs(maxM)));
const yAxisMin = -yBound;
const yAxisMax = yBound;

// Discover regulation statuses and assign colors
const statusList: string[] = ["Not significant", "Up-regulated", "Down-regulated"].filter((s) =>
  DATA.some((r) => String(r[STATUS_COL]) === s),
);
const usedColors = new Set(Object.values(SEMANTIC_COLORS));
let nextPaletteIdx = 0;
const statusColorMap: Record<string, string> = {};
for (const s of statusList) {
  if (s === "Not significant") {
    statusColorMap[s] = `${t.inkSoft}${NOT_SIG_ALPHA_HEX}`;
  } else if (SEMANTIC_COLORS[s]) {
    statusColorMap[s] = SEMANTIC_COLORS[s];
  } else {
    while (usedColors.has(t.palette[nextPaletteIdx])) nextPaletteIdx++;
    statusColorMap[s] = t.palette[nextPaletteIdx];
    usedColors.add(t.palette[nextPaletteIdx]);
  }
}
while (usedColors.has(t.palette[nextPaletteIdx])) nextPaletteIdx++;
const trendColor = t.palette[5] ?? t.palette[nextPaletteIdx];

const notSigPts: Array<{ id: number; x: number; y: number }> = [];
const upRegPts: Array<{ id: number; x: number; y: number }> = [];
const downRegPts: Array<{ id: number; x: number; y: number }> = [];

for (let i = 0; i < DATA.length; i++) {
  const row = DATA[i];
  const pt = { id: i, x: Number(row[MEAN_EXPR_COL]), y: Number(row[LFC_COL]) };
  if (!row[SIG_COL]) {
    notSigPts.push(pt);
  } else if (pt.y > 0) {
    upRegPts.push(pt);
  } else {
    downRegPts.push(pt);
  }
}

// Windowed tricube local average (LOESS trend) across expression range
const smoothPoints: Array<{ x: number; y: number }> = [];
const xSpan = xAxisMax - xAxisMin || 1;
const bw = (xSpan / N_SMOOTH_BINS) * SMOOTH_BW_FACTOR;
for (let b = 0; b <= N_SMOOTH_BINS; b++) {
  const cx = xAxisMin + (b * xSpan) / N_SMOOTH_BINS;
  let wSum = 0;
  let wySum = 0;
  for (let i = 0; i < DATA.length; i++) {
    const dx = Math.abs(Number(DATA[i][MEAN_EXPR_COL]) - cx);
    if (dx < bw) {
      const u = dx / bw;
      const w = Math.pow(1 - u * u * u, 3);
      wSum += w;
      wySum += w * Number(DATA[i][LFC_COL]);
    }
  }
  if (wSum > 0) {
    smoothPoints.push({ x: cx, y: wySum / wSum });
  }
}

function MaOverlay() {
  const xScale = useXScale("x") as (v: number) => number | undefined;
  const yScale = useYScale("y") as (v: number) => number | undefined;

  const toX = (v: number) => Number(xScale(v) ?? 0);
  const toY = (v: number) => Number(yScale(v) ?? 0);

  const R = 6.5;
  const H = R * 0.866;

  const smoothD = smoothPoints
    .map((p, i) => `${i === 0 ? "M" : "L"}${toX(p.x).toFixed(1)},${toY(p.y).toFixed(1)}`)
    .join(" ");

  return (
    <g>
      {upRegPts.map((p) => {
        const x = toX(p.x);
        const y = toY(p.y);
        return (
          <polygon
            key={p.id}
            points={`${x},${y - R} ${x - H},${y + R * 0.5} ${x + H},${y + R * 0.5}`}
            fill={statusColorMap["Up-regulated"]}
          />
        );
      })}
      {downRegPts.map((p) => {
        const x = toX(p.x);
        const y = toY(p.y);
        return (
          <polygon
            key={p.id}
            points={`${x},${y + R} ${x - H},${y - R * 0.5} ${x + H},${y - R * 0.5}`}
            fill={statusColorMap["Down-regulated"]}
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
        x1={toX(xAxisMin)}
        y1={toY(0)}
        x2={toX(xAxisMax)}
        y2={toY(0)}
        stroke={t.ink}
        strokeWidth={1.8}
        strokeOpacity={0.75}
      />
      <line
        x1={toX(xAxisMin)}
        y1={toY(LFC_THRESHOLD)}
        x2={toX(xAxisMax)}
        y2={toY(LFC_THRESHOLD)}
        stroke={t.ink}
        strokeWidth={1.6}
        strokeDasharray="8 4"
        strokeOpacity={0.85}
      />
      <line
        x1={toX(xAxisMin)}
        y1={toY(-LFC_THRESHOLD)}
        x2={toX(xAxisMax)}
        y2={toY(-LFC_THRESHOLD)}
        stroke={t.ink}
        strokeWidth={1.6}
        strokeDasharray="8 4"
        strokeOpacity={0.85}
      />
      <text
        x={toX(xAxisMax) + 10}
        y={toY(LFC_THRESHOLD)}
        fontSize={14}
        fill={t.inkSoft}
        dominantBaseline="middle"
      >
        {`log₂FC = +${LFC_THRESHOLD}`}
      </text>
      <text
        x={toX(xAxisMax) + 10}
        y={toY(-LFC_THRESHOLD)}
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
  { label: "Not significant", color: t.inkSoft, kind: "dot" as const },
  { label: "Up-regulated", color: statusColorMap["Up-regulated"], kind: "up" as const },
  { label: "Down-regulated", color: statusColorMap["Down-regulated"], kind: "down" as const },
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
            label: "Not significant",
            data: notSigPts,
            color: statusColorMap["Not significant"],
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
            label: MEAN_EXPR_COL,
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
            label: LFC_COL,
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
