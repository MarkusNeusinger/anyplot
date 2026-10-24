// anyplot.ai
// histogram-density: Density Histogram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { axisClasses } from "@mui/x-charts/ChartsAxis";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = "system-ui, -apple-system, sans-serif";
const TITLE = "histogram-density · javascript · muix · anyplot.ai";
const BIN_COUNT = 18;
const Y_HEADROOM_RATIO = 0.15;

const BRAND = t.palette[0];
const CURVE = t.palette[1];

// Columns: set these to your data's column names
const WEIGHT = "Package weight (g)"; // role: values

// Data: replace this block with your own records
type DensityRow = {
  [WEIGHT]: number;
};

const data: DensityRow[] = [];
let seed = 7 >>> 0;
const sampleSize = 400;

for (let i = 0; i < sampleSize; i++) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const u1 = Math.max(seed / 0x100000000, 1e-10);
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const u2 = seed / 0x100000000;
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  data.push({
    [WEIGHT]: Number((500 + z * 6).toFixed(3)),
  });
}

// Plot: reads only data and the constants above
const weights = data.map((r) => r[WEIGHT]);
const n = weights.length;
const dataMin = Math.min(...weights);
const dataMax = Math.max(...weights);
const binWidth = (dataMax - dataMin) / BIN_COUNT;

const binCounts = new Array(BIN_COUNT).fill(0);
for (const w of weights) {
  const idx = Math.min(BIN_COUNT - 1, Math.floor((w - dataMin) / binWidth));
  binCounts[idx] += 1;
}

const density = binCounts.map((c) => c / (n * binWidth));
const binCenters = binCounts.map((_, i) => dataMin + (i + 0.5) * binWidth);

const sampleMean = weights.reduce((s, w) => s + w, 0) / n;
const sampleSd = Math.sqrt(
  weights.reduce((s, w) => s + (w - sampleMean) ** 2, 0) / (n - 1),
);
const normalPdf = binCenters.map((x) => {
  const z = (x - sampleMean) / sampleSd;
  return Math.exp(-0.5 * z * z) / (sampleSd * Math.sqrt(2 * Math.PI));
});

const yMax = Math.max(...density, ...normalPdf) * (1 + Y_HEADROOM_RATIO);

const unitMatch = WEIGHT.match(/\(([^)]+)\)/);
const unitStr = unitMatch ? unitMatch[1] : "";
const unitSuffix = unitStr ? ` ${unitStr}` : "";
const SUBTITLE = `${WEIGHT} (n = ${n}, bin width = ${binWidth.toFixed(2)}${unitSuffix}) · Mean ${sampleMean.toFixed(1)}${unitSuffix}, SD ${sampleSd.toFixed(1)}${unitSuffix}`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const HEADER_H = 108;

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
          pt: "14px",
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

      {/* Series legend rendered in HTML outside the SVG drawing area */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: "24px",
          px: "40px",
          pt: "8px",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Box
            sx={{
              width: 18,
              height: 12,
              bgcolor: BRAND,
              borderRadius: "2px",
            }}
          />
          <Typography
            sx={{ fontSize: 14, fontWeight: 600, color: t.ink, fontFamily: FONT }}
          >
            Observed density ({BIN_COUNT} bins)
          </Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Box
            sx={{ width: 20, height: 3.5, bgcolor: CURVE, borderRadius: "2px" }}
          />
          <Typography
            sx={{ fontSize: 14, fontWeight: 600, color: t.ink, fontFamily: FONT }}
          >
            Fitted Normal PDF
          </Typography>
        </Box>
      </Box>

      <ChartsContainer
        width={width}
        height={height - HEADER_H}
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
            label: WEIGHT,
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
            label: unitStr ? `Probability Density (1/${unitStr})` : "Probability Density",
            valueFormatter: (v: number) => v.toFixed(3),
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          },
        ]}
        margin={{ top: 20, right: 40, bottom: 20, left: 20 }}
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
