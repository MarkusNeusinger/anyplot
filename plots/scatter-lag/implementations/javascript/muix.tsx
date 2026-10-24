// anyplot.ai
// scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
// Library: muix 7.29.1 | JavaScript 22.23.0
// Quality: 90/100 | Created: 2026-06-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "scatter-lag · javascript · muix · anyplot.ai";
const MARGIN = { top: 80, right: 60, bottom: 84, left: 28 };
const MARKER_ALPHA = 0.85;

// Columns: set these to your data's column names
const VALUE = "Hourly temperature (°C)"; // role: value

// Data: replace this block with your own records
const LAG = 1; // role: lag
const N_OBS = 200;
const RHO = 0.82;
let seed = 42;
const rawAR = [0.0];
for (let i = 1; i < N_OBS; i += 1) {
  seed = (1664525 * seed + 1013904223) >>> 0;
  const u = seed / 4294967296;
  seed = (1664525 * seed + 1013904223) >>> 0;
  const v = seed / 4294967296;
  const z = Math.sqrt(-2 * Math.log(u + 1e-15)) * Math.cos(2 * Math.PI * v);
  rawAR.push(RHO * rawAR[i - 1] + Math.sqrt(1 - RHO * RHO) * z);
}
const data = rawAR.map((v) => ({ [VALUE]: Number((20 + v * 5).toFixed(2)) }));

// Plot: reads only data and the constants above
const values = data.map((row) => Number(row[VALUE]));
const nObs = values.length;
const lagPairs = values.slice(0, nObs - LAG).map((v, i) => ({
  id: `pair-${i}`,
  x: v,
  y: values[i + LAG],
  z: i,
}));

const gMin = Math.min(...values);
const gMax = Math.max(...values);
const axPad = (gMax - gMin) * 0.07;
const axMin = gMin - axPad;
const axMax = gMax + axPad;

const nPairs = lagPairs.length;
const xMean = lagPairs.reduce((s, p) => s + p.x, 0) / nPairs;
const yMean = lagPairs.reduce((s, p) => s + p.y, 0) / nPairs;
const cov = lagPairs.reduce((s, p) => s + (p.x - xMean) * (p.y - yMean), 0);
const sX = Math.sqrt(lagPairs.reduce((s, p) => s + (p.x - xMean) ** 2, 0));
const sY = Math.sqrt(lagPairs.reduce((s, p) => s + (p.y - yMean) ** 2, 0));
const pearsonR = (cov / (sX * sY)).toFixed(3);

const seq0Num = parseInt(t.seq[0].slice(1), 16);
const seq1Num = parseInt(t.seq[1].slice(1), 16);
const seq0Rgba = `rgba(${(seq0Num >> 16) & 255}, ${(seq0Num >> 8) & 255}, ${seq0Num & 255}, ${MARKER_ALPHA})`;
const seq1Rgba = `rgba(${(seq1Num >> 16) & 255}, ${(seq1Num >> 8) & 255}, ${seq1Num & 255}, ${MARKER_ALPHA})`;

function LagOverlay() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { left, top } = useDrawingArea();
  const { width, height } = window.ANYPLOT_SIZE;

  const cbWidth = 280;
  const cbX = Math.round((width - cbWidth) / 2);
  const cbY = height - 30;

  return (
    <g>
      <line
        x1={xScale(axMin)}
        y1={yScale(axMin)}
        x2={xScale(axMax)}
        y2={yScale(axMax)}
        stroke={t.inkSoft}
        strokeWidth={2.5}
        strokeDasharray="10,8"
        opacity={0.5}
      />
      <text
        x={left + 18}
        y={top + 28}
        textAnchor="start"
        fontSize={16}
        fontWeight={600}
        fill={t.ink}
      >
        {`r(lag = ${LAG}) = ${pearsonR}`}
      </text>

      <defs>
        <linearGradient id="lagTimeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={seq0Rgba} />
          <stop offset="100%" stopColor={seq1Rgba} />
        </linearGradient>
      </defs>
      <text x={cbX - 12} y={cbY + 5} textAnchor="end" fontSize={13} fill={t.inkSoft}>
        {"Observation index t = 0"}
      </text>
      <rect x={cbX} y={cbY - 5} width={cbWidth} height={10} rx={3} fill="url(#lagTimeGrad)" />
      <text x={cbX + cbWidth + 12} y={cbY + 5} textAnchor="start" fontSize={13} fill={t.inkSoft}>
        {`t = ${nPairs - 1}`}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <ChartsContainer
      width={width}
      height={height}
      margin={MARGIN}
      skipAnimation
      zAxis={[
        {
          id: "timeIndex",
          colorMap: {
            type: "continuous",
            min: 0,
            max: nPairs - 1,
            color: [seq0Rgba, seq1Rgba],
          },
        },
      ]}
      series={[
        {
          type: "scatter",
          id: "lag-pairs",
          zAxisId: "timeIndex",
          markerSize: 7,
          data: lagPairs,
        },
      ]}
      xAxis={[
        {
          scaleType: "linear",
          min: axMin,
          max: axMax,
          height: 64,
          label: `y(t) — ${VALUE}`,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          labelStyle: { fontSize: 16, fill: t.ink },
        },
      ]}
      yAxis={[
        {
          scaleType: "linear",
          min: axMin,
          max: axMax,
          width: 84,
          label: `y(t+${LAG}) — ${VALUE}`,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          labelStyle: { fontSize: 16, fill: t.ink },
        },
      ]}
    >
      <ChartsGrid horizontal vertical />
      <LagOverlay />
      <ScatterPlot skipAnimation />
      <ChartsXAxis />
      <ChartsYAxis />
      <text
        x={width / 2}
        y={36}
        textAnchor="middle"
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
      >
        {TITLE}
      </text>
      <text
        x={width / 2}
        y={58}
        textAnchor="middle"
        fontSize={14}
        fill={t.inkSoft}
      >
        {`${VALUE} · lag = ${LAG} · n = ${nObs} observations`}
      </text>
    </ChartsContainer>
  );
}
