// anyplot.ai
// histogram-density: Density Histogram
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-05
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;
const FONT = "system-ui, -apple-system, sans-serif";

// --- Data (in-memory, deterministic) ----------------------------------------
// Fixed-seed LCG + Box-Muller — the browser has no seeded Math.random.
let seed = 7;
function lcg() {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  return seed / 0x100000000;
}
function randn() {
  const u1 = Math.max(lcg(), 1e-10);
  const u2 = lcg();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// A filling line's package weights (g). Nominal fill is 500g with small,
// roughly-Gaussian process variability — the classic case for checking
// observed density against a fitted Normal curve.
const N = 400;
const NOMINAL_WEIGHT = 500;
const PROCESS_SD = 6;
const weights = Array.from(
  { length: N },
  () => NOMINAL_WEIGHT + randn() * PROCESS_SD
);

// --- Bin into a density histogram (bar area sums to 1) -----------------------
const dataMin = Math.min(...weights);
const dataMax = Math.max(...weights);
const BIN_COUNT = 18;
const binWidth = (dataMax - dataMin) / BIN_COUNT;
const binCounts = new Array(BIN_COUNT).fill(0);
weights.forEach((w) => {
  const idx = Math.min(BIN_COUNT - 1, Math.floor((w - dataMin) / binWidth));
  binCounts[idx] += 1;
});
const density = binCounts.map((c) => c / (N * binWidth));
const binCenters = binCounts.map((_, i) => dataMin + (i + 0.5) * binWidth);

// --- Fitted Normal PDF, sampled at the same bin centers ----------------------
// Sampled at the bin centers (not a finer grid) so it shares the histogram's
// band-scale x-axis as a genuine MUI X combo chart, no manual SVG positioning.
const sampleMean = weights.reduce((s, w) => s + w, 0) / N;
const sampleSd = Math.sqrt(
  weights.reduce((s, w) => s + (w - sampleMean) ** 2, 0) / (N - 1)
);
const normalPdf = binCenters.map((x) => {
  const z = (x - sampleMean) / sampleSd;
  return Math.exp(-0.5 * z * z) / (sampleSd * Math.sqrt(2 * Math.PI));
});

const Y_MAX = Math.max(...density, ...normalPdf) * 1.15;

// Imprint palette colors — canonical order (bars = position 1, curve = position 2)
const BRAND = t.palette[0]; // #009E73
const CURVE = t.palette[1]; // #C475FD

// Title sizing (scale down for longer-than-67-char titles)
const TITLE = "histogram-density · javascript · muix · anyplot.ai";
const titleSize = Math.max(11, Math.round(22 * (67 / TITLE.length)));

// --- Main component (default-exported — the harness mounts it) --------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const TITLE_H = 56;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <Typography
        sx={{
          fontSize: titleSize,
          fontWeight: 500,
          color: t.ink,
          pt: "16px",
          px: "40px",
          pb: 0,
          lineHeight: 1.2,
          fontFamily: FONT,
        }}
      >
        {TITLE}
      </Typography>

      <ChartContainer
        width={width}
        height={height - TITLE_H}
        series={[
          {
            type: "bar",
            id: "observed",
            data: density,
            label: "Observed density",
            color: BRAND,
          },
          {
            type: "line",
            id: "fitted",
            data: normalPdf,
            label: "Fitted Normal PDF",
            color: CURVE,
            showMark: false,
          },
        ]}
        xAxis={[
          {
            id: "weight-axis",
            scaleType: "band",
            data: binCenters,
            label: "Package Weight (g)",
            valueFormatter: (v) => v.toFixed(0),
            tickLabelInterval: (_v, i) => i % 2 === 0,
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: Y_MAX,
            label: "Density",
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
            tickLabelStyle: { fontSize: 13, fill: t.inkSoft, fontFamily: FONT },
          },
        ]}
        margin={{ top: 24, right: 40, bottom: 80, left: 110 }}
        skipAnimation
      >
        <ChartsGrid horizontal sx={{ "& line": { stroke: t.grid, strokeWidth: 0.8 } }} />
        <BarPlot skipAnimation />
        <LinePlot skipAnimation slotProps={{ line: { sx: { strokeWidth: 3.5 } } }} />
        <ChartsXAxis axisId="weight-axis" />
        {/* Explicit axisLabel x offset — the default offset formula assumes
            short tick labels and clips against our 4-char decimal density values. */}
        <ChartsYAxis slotProps={{ axisLabel: { x: -72 } }} />
        <ChartsLegend
          position={{ vertical: "top", horizontal: "right" }}
          slotProps={{
            legend: {
              labelStyle: { fontSize: 15, fill: t.inkSoft, fontFamily: FONT },
              itemGap: 20,
            },
          }}
        />
      </ChartContainer>
    </Box>
  );
}
