// anyplot.ai
// histogram-2d: 2D Histogram Heatmap
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const BINS_X = 26; // bin count along x
const BINS_Y = 18; // bin count along y

// Columns: set these to your data's column names
const X = "Stock A Daily Return (%)"; // role: x
const Y = "Stock B Daily Return (%)"; // role: y

// Data: replace this block with your own records, one object per point
// Joint distribution of two correlated daily stock returns (correlation 0.65,
// volatilities 1.4 % and 1.6 %): 8,000 days, far past what a scatter plot can show.
const data = (() => {
  let seed = 42;
  const random = () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let s = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    s = (s + Math.imul(s ^ (s >>> 7), 61 | s)) ^ s;
    return ((s ^ (s >>> 14)) >>> 0) / 4294967296;
  };
  const gaussian = () => {
    let u = 0;
    let v = 0;
    while (u === 0) u = random();
    while (v === 0) v = random();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  };
  const correlation = 0.65;
  return Array.from({ length: 8000 }, () => {
    const z1 = gaussian();
    const z2 = gaussian();
    return {
      [X]: Number((z1 * 1.4).toFixed(3)),
      [Y]: Number(((correlation * z1 + Math.sqrt(1 - correlation * correlation) * z2) * 1.6).toFixed(3)),
    };
  });
})();

// Plot: reads only data and the constants above
const xs = data.map((d) => d[X]);
const ys = data.map((d) => d[Y]);
const xMin = Math.min(...xs);
const xMax = Math.max(...xs);
const yMin = Math.min(...ys);
const yMax = Math.max(...ys);
const binWidth = (xMax - xMin) / BINS_X;
const binHeight = (yMax - yMin) / BINS_Y;

// Count the points per rectangular bin; the last bin includes the maximum
const binCounts = new Array(BINS_X * BINS_Y).fill(0);
for (const d of data) {
  const bx = Math.min(BINS_X - 1, Math.floor((d[X] - xMin) / binWidth));
  const by = Math.min(BINS_Y - 1, Math.floor((d[Y] - yMin) / binHeight));
  binCounts[by * BINS_X + bx] += 1;
}
// Empty bins are not drawn: the page shows through
const bins = binCounts
  .map((count, k) => ({ id: k, x0: xMin + (k % BINS_X) * binWidth, y0: yMin + Math.floor(k / BINS_X) * binHeight, count }))
  .filter((b) => b.count > 0);
const countMin = Math.min(...bins.map((b) => b.count));
const countMax = Math.max(...bins.map((b) => b.count));

// Pearson correlation of the sample, for the subtitle
const xMean = xs.reduce((s, v) => s + v, 0) / xs.length;
const yMean = ys.reduce((s, v) => s + v, 0) / ys.length;
let sxy = 0;
let sxx = 0;
let syy = 0;
for (let i = 0; i < xs.length; i += 1) {
  sxy += (xs[i] - xMean) * (ys[i] - yMean);
  sxx += (xs[i] - xMean) ** 2;
  syy += (ys[i] - yMean) ** 2;
}
const pearsonR = sxy / Math.sqrt(sxx * syy);

const TITLE = "Correlated Stock Returns · histogram-2d · javascript · muix · anyplot.ai";
const SUBTITLE = `n = ${data.length.toLocaleString("en-US")} · ${BINS_X} × ${BINS_Y} bins · Pearson r = ${pearsonR.toFixed(2)}`;
const LEGEND_LABEL = "Points per bin (log scale)";
const HEADER_H = 82;
const LEGEND_H = 76;

// Bins in data coordinates, coloured by the z axis colour map
function HistogramCells() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const colorScale = useZColorScale() as (v: number) => string;
  return (
    <g>
      {bins.map((b) => {
        const left = xScale(b.x0);
        const right = xScale(b.x0 + binWidth);
        const top = yScale(b.y0 + binHeight);
        const bottom = yScale(b.y0);
        return (
          <rect
            key={b.id}
            x={left}
            y={top}
            width={right - left}
            height={bottom - top}
            fill={colorScale(Math.log(b.count))}
            stroke={colorScale(Math.log(b.count))}
            strokeWidth={0.5}
          />
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartH = height - HEADER_H;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "16px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.5 }}>{SUBTITLE}</Typography>
      </Box>
      <ChartsDataProvider
        width={width}
        height={chartH - LEGEND_H}
        series={[]}
        skipAnimation
        margin={{ top: 16, right: 48, bottom: 8, left: 32 }}
        xAxis={[
          {
            scaleType: "linear",
            min: xMin,
            max: xMax,
            height: 64,
            label: X,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: yMin,
            max: yMax,
            width: 72,
            label: Y,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        // Log colour scale: bin counts fall off steeply from the core to the tails
        zAxis={[
          {
            colorMap: { type: "continuous", min: Math.log(countMin), max: Math.log(countMax), color: [t.seq[0], t.seq[1]] },
          },
        ]}
      >
        <ChartsWrapper
          legendPosition={{ vertical: "bottom", horizontal: "center" }}
          legendDirection="horizontal"
          sx={{ width, height: chartH }}
        >
          <Box
            sx={{
              gridArea: "legend",
              height: LEGEND_H,
              width: width * 0.4,
              display: "flex",
              flexDirection: "column",
              pt: "4px",
              boxSizing: "border-box",
            }}
          >
            <Typography sx={{ color: t.ink, fontSize: 15, textAlign: "center", mb: "4px" }}>{LEGEND_LABEL}</Typography>
            <ContinuousColorLegend
              direction="horizontal"
              thickness={16}
              labelPosition="end"
              minLabel={({ value }) => String(Math.round(Math.exp(Number(value))))}
              maxLabel={({ value }) => String(Math.round(Math.exp(Number(value))))}
              sx={{ color: t.inkSoft, fontSize: 14 }}
            />
          </Box>
          <ChartsSurface>
            <HistogramCells />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
