// anyplot.ai
// scatter-regression-lowess: Scatter Plot with LOWESS Regression
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-09

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const LOWESS_FRAC = 0.4; // smoothing span: share of the points in each local fit
const GRID_POINTS = 120; // x positions at which the LOWESS curve is evaluated
const POINT_OPACITY = 0.6;
const X_PAD_SHARE = 0.03; // axis padding as a share of the data span
const Y_PAD_SHARE = 0.06;

// Columns: set these to your data's column names
const X = "Vehicle speed (km/h)"; // role: x
const Y = "Fuel efficiency (km/L)"; // role: y

// Data: replace this block with your own records, one object per row
// Test-drive log: fuel efficiency peaks at a moderate cruising speed and drops at low
// speed (idling, acceleration) and at high speed (aerodynamic drag).
const data: Record<string, number>[] = [];
let seed = 42;
for (let i = 0; i < 170; i += 1) {
  seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
  const speed = 20 + (seed / 4294967296) * 120;
  seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
  const u1 = Math.max(seed / 4294967296, 1e-9);
  seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
  const u2 = seed / 4294967296;
  const noise = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  data.push({ [X]: speed, [Y]: Math.max(3, 18.5 - 0.0021 * (speed - 78) ** 2 + noise * 1.6) });
}

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[X] - b[X]);
const xs = rows.map((d) => d[X]);
const ys = rows.map((d) => d[Y]);
const n = rows.length;
const xMin = Math.min(...xs);
const xMax = Math.max(...xs);
const windowSize = Math.max(2, Math.round(LOWESS_FRAC * n));

// LOWESS: a tricube-weighted linear fit over the nearest windowSize points at each grid x;
// the weighted RMS of that window's residuals gives a ±1 SD band around the curve.
const gridX = Array.from({ length: GRID_POINTS }, (_, i) => xMin + ((xMax - xMin) * i) / (GRID_POINTS - 1));
const fitY: number[] = [];
const bandSd: number[] = [];
for (const x0 of gridX) {
  const dist = xs.map((xi) => Math.abs(xi - x0));
  const h = [...dist].sort((a, b) => a - b)[windowSize - 1];
  const w = dist.map((d) => (h > 0 ? (1 - Math.min(d / h, 1) ** 3) ** 3 : Number(d === 0)));
  let sw = 0;
  let swx = 0;
  let swy = 0;
  let swxx = 0;
  let swxy = 0;
  for (let i = 0; i < n; i += 1) {
    sw += w[i];
    swx += w[i] * xs[i];
    swy += w[i] * ys[i];
    swxx += w[i] * xs[i] * xs[i];
    swxy += w[i] * xs[i] * ys[i];
  }
  const denom = sw * swxx - swx * swx;
  const slope = denom !== 0 ? (sw * swxy - swx * swy) / denom : 0;
  const intercept = (swy - slope * swx) / sw;
  let swResidSq = 0;
  for (let i = 0; i < n; i += 1) swResidSq += w[i] * (ys[i] - (intercept + slope * xs[i])) ** 2;
  fitY.push(intercept + slope * x0);
  bandSd.push(Math.sqrt(swResidSq / sw));
}
const upperY = fitY.map((y, i) => y + bandSd[i]);
const lowerY = fitY.map((y, i) => y - bandSd[i]);

const xPad = (xMax - xMin) * X_PAD_SHARE;
const yLow = Math.min(...ys, ...lowerY);
const yHigh = Math.max(...ys, ...upperY);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;

const scatterData = rows.map((d, i) => ({ x: d[X], y: d[Y], id: i }));
const title = "LOWESS Smoothing · scatter-regression-lowess · javascript · muix · anyplot.ai";
const subtitle = `n = ${n} observations · span frac = ${LOWESS_FRAC} (${windowSize} nearest points per local fit) · shaded band: ±1 SD of the local residuals`;
const HEADER_H = 88;
const LEGEND_H = 40;

function ResidualBand() {
  const xScale = useXScale();
  const yScale = useYScale();
  const top = gridX.map((x, i) => `${xScale(x)},${yScale(upperY[i])}`).join(" L ");
  const bottom = gridX
    .map((x, i) => `${xScale(x)},${yScale(lowerY[i])}`)
    .reverse()
    .join(" L ");
  return <path d={`M ${top} L ${bottom} Z`} fill={t.inkSoft} fillOpacity={0.16} stroke="none" />;
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{title}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <ChartsDataProvider
        width={width}
        height={height - HEADER_H - LEGEND_H}
        margin={{ top: 12, right: 56, bottom: 16, left: 32 }}
        skipAnimation
        series={[
          {
            type: "scatter",
            id: "observations",
            label: "Observations",
            data: scatterData,
            markerSize: 7,
            color: t.palette[0],
          },
          {
            type: "line",
            id: "lowess",
            label: `LOWESS fit (frac = ${LOWESS_FRAC})`,
            data: fitY,
            color: t.palette[1],
            curve: "linear",
            showMark: false,
          },
        ]}
        xAxis={[
          {
            scaleType: "linear",
            data: gridX,
            min: xMin - xPad,
            max: xMax + xPad,
            label: X,
            height: 68,
            valueFormatter: (v: number) => v.toFixed(0),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
            sx: { "& .MuiChartsAxis-line, & .MuiChartsAxis-tick": { stroke: t.inkSoft } },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: yLow - yPad,
            max: yHigh + yPad,
            label: Y,
            width: 76,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
            sx: { "& .MuiChartsAxis-line, & .MuiChartsAxis-tick": { stroke: t.inkSoft } },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ horizontal: "end", vertical: "top" }} legendDirection="horizontal">
          <ChartsLegend sx={{ fontSize: 16, color: t.ink, pr: 7 }} />
          <ChartsSurface
            sx={{
              "& .MuiScatterChart-marker": { fillOpacity: POINT_OPACITY },
              "& .MuiLineChart-line": { strokeWidth: 3.5 },
            }}
          >
            <ChartsGrid horizontal vertical />
            <ResidualBand />
            <ScatterPlot />
            <LinePlot skipAnimation />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
          <ChartsTooltip trigger="item" />
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
