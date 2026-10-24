// anyplot.ai
// scatter-regression-lowess: Scatter Plot with LOWESS Regression
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-09

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "scatter-regression-lowess · javascript · muix · anyplot.ai";
const LOWESS_FRAC = 0.4;
const GRID_SIZE = 120;
const CHART_TOP = 64;
const OBSERVED_LABEL = "Vehicles (observed)";
const FIT_LABEL = "LOWESS fit";

// Columns: set these to your data's column names
const X_VAL = "Vehicle Speed (km/h)"; // role: x
const Y_VAL = "Fuel Efficiency (km/L)"; // role: y

// Data: replace this block with your own records
const SAMPLE_SIZE = 170;
let seed = 42;
const data = [];
for (let i = 0; i < SAMPLE_SIZE; i += 1) {
  seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
  const uSpeed = seed / 4294967296;
  seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
  const u1 = Math.max(seed / 4294967296, 1e-9);
  seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
  const u2 = seed / 4294967296;
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  const speed = 20 + uSpeed * 120;
  const trend = 18.5 - 0.0021 * (speed - 78) ** 2;
  const value = Math.max(3, trend + z * 1.6);
  data.push({ [X_VAL]: speed, [Y_VAL]: value });
}

// Plot: reads only data and the constants above
const xs = data.map((row) => Number(row[X_VAL]));
const ys = data.map((row) => Number(row[Y_VAL]));
const n = xs.length;
const windowSize = Math.round(LOWESS_FRAC * n);
const xMin = Math.min(...xs);
const xMax = Math.max(...xs);
const smoothedX = Array.from({ length: GRID_SIZE }, (_, i) => xMin + ((xMax - xMin) * i) / (GRID_SIZE - 1));

const smoothed = smoothedX.map((x0) => {
  const distances = xs.map((xi) => Math.abs(xi - x0));
  const bandwidth = [...distances].sort((a, b) => a - b)[windowSize - 1];
  const weights = distances.map((d) => {
    const u = Math.min(d / bandwidth, 1);
    return (1 - u ** 3) ** 3;
  });

  let sw = 0;
  let swx = 0;
  let swy = 0;
  let swxx = 0;
  let swxy = 0;
  for (let i = 0; i < n; i += 1) {
    const w = weights[i];
    sw += w;
    swx += w * xs[i];
    swy += w * ys[i];
    swxx += w * xs[i] * xs[i];
    swxy += w * xs[i] * ys[i];
  }
  const denom = sw * swxx - swx * swx;
  const slope = (sw * swxy - swx * swy) / denom;
  const intercept = (swy - slope * swx) / sw;

  let swResidSq = 0;
  for (let i = 0; i < n; i += 1) {
    const resid = ys[i] - (intercept + slope * xs[i]);
    swResidSq += weights[i] * resid * resid;
  }
  const band = Math.sqrt(swResidSq / sw);

  return { x: x0, y: intercept + slope * x0, band };
});

const smoothedY = smoothed.map((point) => point.y);
const smoothedUpper = smoothed.map((point) => point.y + point.band);
const smoothedLower = smoothed.map((point) => point.y - point.band);

const scatterData = xs.map((speed, i) => ({
  x: speed,
  y: ys[i],
  id: i,
}));

const p0 = parseInt(t.palette[0].slice(1), 16);
const pointColor = `rgba(${(p0 >> 16) & 255}, ${(p0 >> 8) & 255}, ${p0 & 255}, 0.6)`;
const mutedHex = t.theme === "dark" ? "#A8A79F" : "#6B6A63";
const mNum = parseInt(mutedHex.slice(1), 16);
const bandFill = `rgba(${(mNum >> 16) & 255}, ${(mNum >> 8) & 255}, ${mNum & 255}, 0.18)`;

function ConfidenceBand() {
  const xScale = useXScale("speed");
  const yScale = useYScale();
  const topEdge = smoothedX.map((xi, i) => `${i === 0 ? "M" : "L"}${xScale(xi)},${yScale(smoothedUpper[i])}`);
  const bottomEdge = [...smoothedX]
    .map((xi, i) => ({ xi, y: smoothedLower[i] }))
    .reverse()
    .map((point) => `L${xScale(point.xi)},${yScale(point.y)}`);
  return <path d={`${topEdge.join(" ")} ${bottomEdge.join(" ")} Z`} fill={bandFill} stroke="none" />;
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const titleSize = TITLE.length > 67 ? Math.round((22 * 67) / TITLE.length) : 22;

  return (
    <Box sx={{ position: "relative", width: W, height: H, bgcolor: t.pageBg }}>
      <Box
        sx={{
          position: "absolute",
          top: 0,
          left: 56,
          right: 40,
          height: CHART_TOP,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Typography sx={{ color: t.ink, fontSize: titleSize, fontWeight: 500 }}>{TITLE}</Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: "24px" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Box sx={{ width: 12, height: 12, borderRadius: "50%", bgcolor: pointColor }} />
            <Typography sx={{ color: t.ink, fontSize: 14 }}>{OBSERVED_LABEL}</Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Box sx={{ width: 22, height: 3.5, borderRadius: "2px", bgcolor: t.palette[1] }} />
            <Typography sx={{ color: t.ink, fontSize: 14 }}>{FIT_LABEL}</Typography>
          </Box>
        </Box>
      </Box>
      <Box sx={{ position: "absolute", top: CHART_TOP, left: 0, right: 0, bottom: 0 }}>
        <ChartsContainer
          width={W}
          height={H - CHART_TOP}
          skipAnimation
          margin={{ top: 20, right: 40, bottom: 24, left: 24 }}
          series={[
            {
              type: "scatter",
              id: "observed",
              data: scatterData,
              color: pointColor,
              markerSize: 8,
              label: OBSERVED_LABEL,
            },
            {
              type: "line",
              id: "lowess",
              data: smoothedY,
              xAxisId: "speed",
              color: t.palette[1],
              curve: "natural",
              showMark: false,
              label: FIT_LABEL,
            },
          ]}
          xAxis={[
            {
              id: "speed",
              data: smoothedX,
              scaleType: "linear",
              height: 64,
              label: X_VAL,
              labelStyle: { fontSize: 16 },
              tickLabelStyle: { fontSize: 14 },
              valueFormatter: (value: number) => value.toFixed(0),
            },
          ]}
          yAxis={[
            {
              width: 84,
              label: Y_VAL,
              labelStyle: { fontSize: 16 },
              tickLabelStyle: { fontSize: 14 },
            },
          ]}
          sx={{
            "& .MuiLineChart-line": { strokeWidth: 3.5 },
          }}
        >
          <ChartsGrid horizontal vertical />
          <ConfidenceBand />
          <ScatterPlot />
          <LinePlot />
          <ChartsXAxis />
          <ChartsYAxis />
          <ChartsTooltip trigger="item" />
        </ChartsContainer>
      </Box>
    </Box>
  );
}
