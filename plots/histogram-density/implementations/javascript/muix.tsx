// anyplot.ai
// histogram-density: Density Histogram
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-05

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { axisClasses } from "@mui/x-charts/ChartsAxis";
import { useDrawingArea } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;
const FONT = "system-ui, -apple-system, sans-serif";

// Constants
const VALUES_COL = "values";
const BIN_COUNT = 18;
const Y_HEADROOM_RATIO = 0.15;

const BRAND = t.palette[0];
const CURVE = t.palette[1];

// Data
type DensityRow = {
  [VALUES_COL]: number;
};

const DATA: DensityRow[] = [];
let seed = 7 >>> 0;
const sampleSize = 400;

for (let i = 0; i < sampleSize; i++) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const u1 = Math.max(seed / 0x100000000, 1e-10);
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const u2 = seed / 0x100000000;
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  DATA.push({
    [VALUES_COL]: Number((500 + z * 6).toFixed(3)),
  });
}

const weights = DATA.map((r) => r[VALUES_COL]);
const n = weights.length;
const dataMin = Math.min(...weights);
const dataMax = Math.max(...weights);
const binWidth = Math.max(1e-6, (dataMax - dataMin) / BIN_COUNT);

const binCounts = new Array(BIN_COUNT).fill(0);
for (const w of weights) {
  const idx = Math.min(
    BIN_COUNT - 1,
    Math.max(0, Math.floor((w - dataMin) / binWidth)),
  );
  binCounts[idx] += 1;
}

const density = binCounts.map((c) => c / (n * binWidth));
const binCenters = binCounts.map((_, i) => dataMin + (i + 0.5) * binWidth);

const sampleMean = weights.reduce((s, w) => s + w, 0) / n;
const sampleSd = Math.sqrt(
  weights.reduce((s, w) => s + (w - sampleMean) ** 2, 0) / Math.max(1, n - 1),
);
const normalPdf = binCenters.map((x) => {
  const z = (x - sampleMean) / sampleSd;
  return Math.exp(-0.5 * z * z) / (sampleSd * Math.sqrt(2 * Math.PI));
});

const totalArea = density.reduce((acc, d) => acc + d * binWidth, 0);
const yMax = Math.max(...density, ...normalPdf) * (1 + Y_HEADROOM_RATIO);

const TITLE = "histogram-density · javascript · muix · anyplot.ai";
const SUBTITLE = `Package weight distribution (n = ${n}, bin width = ${binWidth.toFixed(2)} g, total area = ${totalArea.toFixed(2)}) · Mean ${sampleMean.toFixed(1)} g, SD ${sampleSd.toFixed(1)} g`;

function DensityLegendLayer() {
  const { left, top, width } = useDrawingArea();
  const lx = left + width - 220;
  const ly = top + 16;

  return (
    <g fontFamily={FONT}>
      <rect
        x={lx - 14}
        y={ly - 12}
        width={224}
        height={68}
        rx={6}
        fill={t.elevatedBg}
        stroke={t.grid}
        strokeWidth={1}
      />
      <rect
        x={lx}
        y={ly}
        width={20}
        height={14}
        rx={2}
        fill={BRAND}
      />
      <text x={lx + 28} y={ly + 12} fontSize={14} fontWeight={600} fill={t.ink}>
        Observed density
      </text>

      <line
        x1={lx}
        y1={ly + 34}
        x2={lx + 20}
        y2={ly + 34}
        stroke={CURVE}
        strokeWidth={3.5}
      />
      <text x={lx + 28} y={ly + 39} fontSize={14} fontWeight={600} fill={t.ink}>
        Fitted Normal PDF
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const TITLE_H = 78;

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
          fontSize: 22,
          fontWeight: 600,
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
      <Typography
        sx={{
          fontSize: 15,
          fontWeight: 400,
          color: t.inkSoft,
          px: "40px",
          pt: "4px",
          pb: 0,
          lineHeight: 1.2,
          fontFamily: FONT,
        }}
      >
        {SUBTITLE}
      </Typography>

      <ChartsContainer
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
            curve: "monotoneX",
          },
        ]}
        xAxis={[
          {
            id: "weight-axis",
            scaleType: "band",
            data: binCenters,
            categoryGapRatio: 0.02,
            height: 60,
            label: "Package Weight (g)",
            valueFormatter: (v: number) => v.toFixed(1),
            tickLabelInterval: (_v: number, i: number) => i % 2 === 0,
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          },
        ]}
        yAxis={[
          {
            id: "density-axis",
            min: 0,
            max: yMax,
            width: 96,
            label: "Probability Density (1/g)",
            valueFormatter: (v: number) => v.toFixed(3),
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          },
        ]}
        margin={{ top: 24, right: 40, bottom: 20, left: 20 }}
        skipAnimation
      >
        <ChartsGrid
          horizontal
          sx={{ "& line": { stroke: t.grid, strokeWidth: 0.8 } }}
        />
        <BarPlot skipAnimation />
        <LinePlot
          skipAnimation
          slotProps={{ line: { sx: { strokeWidth: 3.5 } } }}
        />
        <DensityLegendLayer />
        <ChartsXAxis
          axisId="weight-axis"
          sx={{
            [`& .${axisClasses.line}`]: { stroke: t.grid },
            [`& .${axisClasses.tick}`]: { stroke: t.grid },
          }}
        />
        <ChartsYAxis
          axisId="density-axis"
          sx={{
            [`& .${axisClasses.line}`]: { stroke: t.grid },
            [`& .${axisClasses.tick}`]: { stroke: t.grid },
          }}
        />
      </ChartsContainer>
    </Box>
  );
}
