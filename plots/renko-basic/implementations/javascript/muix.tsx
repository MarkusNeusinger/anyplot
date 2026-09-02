// anyplot.ai
// renko-basic: Basic Renko Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-02

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG PRNG — no fetch, no Math.random) ----
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

// Daily closes for a fictional solar-energy stock across four trend regimes
// (uptrend, consolidation, downtrend, recovery) — the zigzag that a Renko
// chart is built to filter down to a handful of clean bricks.
const REGIMES = [
  { days: 60, drift: 0.34 },
  { days: 50, drift: 0.0 },
  { days: 70, drift: -0.3 },
  { days: 60, drift: 0.26 },
];
const closes = [64.0];
const dates = [new Date(2024, 0, 2)];
for (const regime of REGIMES) {
  for (let d = 0; d < regime.days; d++) {
    const noise = (rand() - 0.5) * 1.6;
    const prev = closes[closes.length - 1];
    closes.push(Math.max(prev + regime.drift + noise, 5));
    const nextDate = new Date(dates[dates.length - 1]);
    nextDate.setDate(nextDate.getDate() + 1);
    dates.push(nextDate);
  }
}

// --- Renko brick construction: a new brick is only drawn once price moves a
// full BRICK_SIZE away from the last brick's boundary — this is what strips
// time and minor noise out of the series, leaving only decisive moves.
const BRICK_SIZE = 1.5;
const bricks = []; // { base, direction: 1 | -1, date }
let anchor = Math.round(closes[0] / BRICK_SIZE) * BRICK_SIZE;
for (let i = 1; i < closes.length; i++) {
  const price = closes[i];
  while (price - anchor >= BRICK_SIZE) {
    bricks.push({ base: anchor, direction: 1, date: dates[i] });
    anchor += BRICK_SIZE;
  }
  while (anchor - price >= BRICK_SIZE) {
    anchor -= BRICK_SIZE;
    bricks.push({ base: anchor, direction: -1, date: dates[i] });
  }
}

const brickLabels = bricks.map((_, i) => `${i + 1}`);
const yMin = Math.min(...bricks.map((b) => b.base));
const yMax = Math.max(...bricks.map((b) => b.base + BRICK_SIZE));
const yPad = (yMax - yMin) * 0.08;

const fmtDate = (d) => d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
const tickEvery = Math.ceil(bricks.length / 10);

// --- Bricks: MUI X community has no native Renko series — draw uniform,
// gapped rectangles against the shared band/linear scales via
// useXScale/useYScale, the documented ChartContainer composition pattern for
// chart types outside the community surface (same idiom as candlestick/OHLC).
// Bullish bricks (price up) are brand green, bearish (price down) matte red —
// the finance up/down semantic exception from the style guide.
function Bricks() {
  const xScale = useXScale("x");
  const yScale = useYScale("y");
  if (!xScale || !yScale) return null;
  const bw = xScale.bandwidth();
  const brickWidth = bw * 0.78;

  return (
    <g>
      {bricks.map((brick, i) => {
        const cx = xScale(brickLabels[i]) + bw / 2;
        const color = brick.direction === 1 ? t.palette[0] : t.palette[4];
        const yTop = yScale(brick.base + BRICK_SIZE);
        const yBottom = yScale(brick.base);
        return (
          <rect
            key={i}
            x={cx - brickWidth / 2}
            y={yTop}
            width={brickWidth}
            height={yBottom - yTop}
            fill={color}
            stroke={t.ink}
            strokeOpacity={0.3}
            strokeWidth={1}
          />
        );
      })}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const TITLE_H = 96;
  const LEGEND_H = 52;
  const chartH = H - TITLE_H - LEGEND_H;

  const title = "SolarGrid Energy Daily Close · renko-basic · javascript · muix · anyplot.ai";
  const titleSize = title.length > 67 ? Math.round((22 * 67) / title.length) : 22;
  const subtitle = `${fmtDate(dates[0])} – ${fmtDate(dates[dates.length - 1])} · $${BRICK_SIZE.toFixed(2)} brick size · ${bricks.length} bricks`;

  const legendItems = [
    { label: "Bullish brick (price up)", color: t.palette[0] },
    { label: "Bearish brick (price down)", color: t.palette[4] },
  ];

  return (
    <Box
      sx={{
        width: W,
        height: H,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "'Roboto', 'Helvetica Neue', Arial, sans-serif",
        boxSizing: "border-box",
      }}
    >
      <Box
        sx={{
          height: TITLE_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "6px",
        }}
      >
        <Typography sx={{ color: t.ink, fontSize: titleSize, fontWeight: 600 }}>{title}</Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 13, fontWeight: 400, letterSpacing: "0.03em" }}>
          {subtitle}
        </Typography>
      </Box>

      <ChartContainer
        width={W}
        height={chartH}
        skipAnimation
        series={[]}
        xAxis={[
          {
            id: "x",
            scaleType: "band",
            data: brickLabels,
            label: "Brick Sequence (estimated dates)",
            valueFormatter: (label) => fmtDate(bricks[Number(label) - 1].date),
            tickLabelInterval: (_value, index) => index % tickEvery === 0,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "y",
            min: yMin - yPad,
            max: yMax + yPad,
            label: "Price (USD)",
            valueFormatter: (v) => `$${v.toFixed(2)}`,
            tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
            labelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        margin={{ top: 24, bottom: 64, left: 96, right: 32 }}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft, strokeOpacity: 0.2 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal />
        <Bricks />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId="y" slotProps={{ axisLabel: { x: -64 } }} />
      </ChartContainer>

      <Box sx={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: "16px" }}>
        {legendItems.map((item) => (
          <Box
            key={item.label}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "6px 16px",
              borderRadius: "999px",
              border: `1px solid ${t.grid}`,
              bgcolor: t.elevatedBg,
            }}
          >
            <Box sx={{ width: 10, height: 10, borderRadius: "2px", bgcolor: item.color }} />
            <Typography sx={{ color: t.inkSoft, fontSize: 13, fontWeight: 500 }}>{item.label}</Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
