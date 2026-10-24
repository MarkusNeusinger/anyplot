// anyplot.ai
// histogram-kde: Histogram with KDE Overlay
// Library: muix 9.2.1 | JavaScript 22.23.1
// Quality: 89/100 | Created: 2026-08-05

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useDrawingArea } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;
const FONT = "system-ui, -apple-system, sans-serif";

// Constants
const VALUES_COL = "values";
const BIN_COUNT = 30;
const KDE_POINTS = 240;
const X_PAD_RATIO = 0.04;
const Y_HEADROOM_RATIO = 0.15;
const SILVERMAN_FACTOR = 1.06;

const BRAND = t.palette[0];
const BLUE = t.palette[2];

// Data
type KdeRow = {
  [VALUES_COL]: number;
};

const DATA: KdeRow[] = [];
let seed = 42 >>> 0;
const sampleSize = 500;

for (let i = 0; i < sampleSize; i++) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const isShockDay = seed / 0x100000000 < 0.09;
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const u1 = Math.max(seed / 0x100000000, 1e-10);
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const u2 = seed / 0x100000000;
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  const mean = isShockDay ? -2.6 : 0.12;
  const sd = isShockDay ? 2.4 : 0.85;
  DATA.push({
    [VALUES_COL]: Number((mean + z * sd).toFixed(4)),
  });
}

const returns = DATA.map((r) => r[VALUES_COL]);
const n = returns.length;
const dataMin = Math.min(...returns);
const dataMax = Math.max(...returns);
const pad = (dataMax - dataMin) * X_PAD_RATIO;
const xMin = dataMin - pad;
const xMax = dataMax + pad;

const binWidth = Math.max(1e-6, (dataMax - dataMin) / BIN_COUNT);
const binCounts = new Array(BIN_COUNT).fill(0);
for (const v of returns) {
  const idx = Math.min(
    BIN_COUNT - 1,
    Math.max(0, Math.floor((v - dataMin) / binWidth)),
  );
  binCounts[idx] += 1;
}
const histogramDensity = binCounts.map((c) => c / (n * binWidth));

const sampleMean = returns.reduce((s, v) => s + v, 0) / n;
const sampleStd = Math.sqrt(
  returns.reduce((s, v) => s + (v - sampleMean) ** 2, 0) / Math.max(1, n - 1),
);
const bandwidth = SILVERMAN_FACTOR * sampleStd * Math.pow(n, -0.2);

const kdeX = Array.from(
  { length: KDE_POINTS },
  (_, i) => xMin + (i / (KDE_POINTS - 1)) * (xMax - xMin),
);
const kdeDensity = kdeX.map((x) => {
  let sum = 0;
  for (const v of returns) {
    const u = (x - v) / bandwidth;
    sum += Math.exp(-0.5 * u * u);
  }
  return sum / (n * bandwidth * Math.sqrt(2 * Math.PI));
});

const yMax = Math.max(...histogramDensity, ...kdeDensity) * (1 + Y_HEADROOM_RATIO);

const TITLE = "histogram-kde · javascript · muix · anyplot.ai";
const SUBTITLE = `Daily portfolio returns (n = ${n}) · Mean ${sampleMean.toFixed(2)}%, SD ${sampleStd.toFixed(2)}%, Silverman KDE bandwidth h = ${bandwidth.toFixed(2)}%`;

function HistogramBarsLayer() {
  const { left, top, width, height } = useDrawingArea();
  const binPx = (binWidth / (xMax - xMin)) * width;
  return (
    <g>
      {histogramDensity.map((d, i) => {
        const bx =
          left + ((dataMin + i * binWidth - xMin) / (xMax - xMin)) * width;
        const by = top + (1 - d / yMax) * height;
        return (
          <rect
            key={i}
            x={bx + 0.5}
            y={by}
            width={Math.max(0, binPx - 1)}
            height={Math.max(0, top + height - by)}
            fill={BRAND}
            fillOpacity={0.5}
          />
        );
      })}
    </g>
  );
}

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
              width: 16,
              height: 12,
              bgcolor: BRAND,
              opacity: 0.5,
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
            sx={{ width: 18, height: 3.5, bgcolor: BLUE, borderRadius: "2px" }}
          />
          <Typography
            sx={{ fontSize: 14, fontWeight: 600, color: t.ink, fontFamily: FONT }}
          >
            Gaussian KDE estimate
          </Typography>
        </Box>
      </Box>

      <ChartsContainer
        width={width}
        height={height - HEADER_H}
        series={[
          {
            type: "line",
            id: "kde",
            data: kdeDensity,
            label: "KDE estimate",
            color: BLUE,
            showMark: false,
          },
        ]}
        xAxis={[
          {
            id: "return-axis",
            data: kdeX,
            scaleType: "linear",
            min: xMin,
            max: xMax,
            height: 60,
            label: "Daily Return (%)",
            valueFormatter: (v: number) => `${v.toFixed(1)}%`,
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
            label: "Probability Density",
            valueFormatter: (v: number) => v.toFixed(2),
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
        <HistogramBarsLayer />
        <LinePlot
          skipAnimation
          slotProps={{ line: { sx: { strokeWidth: 3.5 } } }}
        />
        <ChartsReferenceLine
          x={sampleMean}
          label={`Mean ${sampleMean.toFixed(2)}%`}
          labelAlign="start"
          lineStyle={{
            stroke: t.inkSoft,
            strokeDasharray: "6 4",
            strokeWidth: 1.5,
          }}
          labelStyle={{
            fontSize: 14,
            fontWeight: 600,
            fill: t.inkSoft,
            fontFamily: FONT,
          }}
        />
        <ChartsXAxis axisId="return-axis" />
        <ChartsYAxis axisId="density-axis" />
      </ChartsContainer>
    </Box>
  );
}
