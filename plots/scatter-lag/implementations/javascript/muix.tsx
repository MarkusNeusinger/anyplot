// anyplot.ai
// scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const LAG = 1; // lag order k (the spec's lag role): each observation is paired with the one k steps later
const EXTENT_PAD_SHARE = 0.07; // room beyond the extreme values, as a share of the value span
const POINT_OPACITY = 0.85;
const TICK_COUNT = 12; // about this many ticks on each axis, so both share one step

// Columns: set these to your data's column names
const HOUR = "Hour of record"; // role: extra
const TEMPERATURE = "Temperature (°C)"; // role: value

// Data: replace this block with your own records, one object per row
// Hourly station temperature as an AR(1) process: rho 0.82 around 20 °C, sigma about 5 °C.
const data = (() => {
  let seed = 42;
  const uniform = () => {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const rho = 0.82;
  let state = 0;
  const rows = [];
  for (let hour = 0; hour < 200; hour += 1) {
    if (hour > 0) {
      const u = uniform();
      const v = uniform();
      const shock = Math.sqrt(-2 * Math.log(u + 1e-15)) * Math.cos(2 * Math.PI * v);
      state = rho * state + Math.sqrt(1 - rho * rho) * shock;
    }
    rows.push({ [HOUR]: hour, [TEMPERATURE]: Number((20 + state * 5).toFixed(2)) });
  }
  return rows;
})();

// Plot: reads only data and the constants above
const series = [...data].sort((a, b) => a[HOUR] - b[HOUR]);
const pairs = series.slice(LAG).map((later, i) => ({
  id: `pair-${i}`,
  x: series[i][TEMPERATURE],
  y: later[TEMPERATURE],
  z: series[i][HOUR],
}));

// Pearson r of the lagged pairs
const n = pairs.length;
const xMean = pairs.reduce((s, p) => s + p.x, 0) / n;
const yMean = pairs.reduce((s, p) => s + p.y, 0) / n;
const cov = pairs.reduce((s, p) => s + (p.x - xMean) * (p.y - yMean), 0);
const sx = Math.sqrt(pairs.reduce((s, p) => s + (p.x - xMean) ** 2, 0));
const sy = Math.sqrt(pairs.reduce((s, p) => s + (p.y - yMean) ** 2, 0));
const pearsonR = cov / (sx * sy);

// Both axes show the same variable, so they share one padded range and y = x is the plot's diagonal
const values = series.map((d) => d[TEMPERATURE]);
const pad = (Math.max(...values) - Math.min(...values)) * EXTENT_PAD_SHARE;
const axisMin = Math.min(...values) - pad;
const axisMax = Math.max(...values) + pad;
const hours = pairs.map((p) => p.z);
const hourMin = Math.min(...hours);
const hourMax = Math.max(...hours);

const TITLE = "scatter-lag · javascript · muix · anyplot.ai";
const SUBTITLE = `Lag k = ${LAG} · ${n} pairs from ${series.length} observations · dashed line: y = x`;
const HEADER_HEIGHT = 76;
const LEGEND_WIDTH = 150;
const LEGEND_HEIGHT = 420;

function DiagonalAndR() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { left, top, width } = useDrawingArea();
  // Positive autocorrelation leaves the top-left corner empty, negative leaves the top-right
  const onLeft = pearsonR >= 0;
  return (
    <g>
      <line
        x1={xScale(axisMin)}
        y1={yScale(axisMin)}
        x2={xScale(axisMax)}
        y2={yScale(axisMax)}
        stroke={t.inkSoft}
        strokeOpacity={0.6}
        strokeWidth={2}
        strokeDasharray="10 8"
      />
      <text
        x={onLeft ? left + 20 : left + width - 20}
        y={top + 34}
        textAnchor={onLeft ? "start" : "end"}
        fontSize={18}
        fontWeight={600}
        fill={t.ink}
        stroke={t.pageBg}
        strokeWidth={4}
        paintOrder="stroke"
      >
        {`r(lag ${LAG}) = ${pearsonR.toFixed(3)}`}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_HEIGHT,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsDataProvider
        width={width - LEGEND_WIDTH}
        height={height - HEADER_HEIGHT}
        margin={{ top: 8, right: 24, bottom: 16, left: 24 }}
        skipAnimation
        series={[
          {
            type: "scatter",
            id: "pairs",
            label: `${TEMPERATURE} at t + ${LAG}`,
            data: pairs,
            markerSize: 6,
            zAxisId: "time",
          },
        ]}
        xAxis={[
          {
            id: "earlier",
            scaleType: "linear",
            min: axisMin,
            max: axisMax,
            label: `${TEMPERATURE} at t`,
            tickNumber: TICK_COUNT,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 17, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "later",
            scaleType: "linear",
            min: axisMin,
            max: axisMax,
            label: `${TEMPERATURE} at t + ${LAG}`,
            tickNumber: TICK_COUNT,
            width: 76,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 17, fill: t.ink },
          },
        ]}
        zAxis={[
          {
            id: "time",
            min: hourMin,
            max: hourMax,
            colorMap: { type: "continuous", min: hourMin, max: hourMax, color: [t.seq[0], t.seq[1]] },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "middle", horizontal: "end" }} legendDirection="vertical">
          <div
            style={{
              gridArea: "legend",
              width: LEGEND_WIDTH,
              height: LEGEND_HEIGHT,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <div style={{ color: t.ink, fontSize: 16, marginBottom: 10, textAlign: "center" }}>{HOUR}</div>
            <ContinuousColorLegend
              axisDirection="z"
              axisId="time"
              direction="vertical"
              thickness={18}
              labelPosition="end"
              sx={{ flex: 1, color: t.inkSoft, fontSize: 15 }}
            />
          </div>
          <ChartsSurface
            sx={{
              "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
              "& .MuiScatterChart-marker": { fillOpacity: POINT_OPACITY },
            }}
          >
            <ChartsGrid horizontal vertical />
            <ChartsXAxis />
            <ChartsYAxis />
            <DiagonalAndR />
            <ScatterPlot />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
