// anyplot.ai
// scatter-regression-linear: Scatter Plot with Linear Regression
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 89/100 | Created: 2026-08-05

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "scatter-regression-linear · javascript · muix · anyplot.ai";
const GRID_POINTS = 60;
const T_CRIT_95 = 1.987;

// Columns: set these to your data's column names
const X_VAL = "Advertising Spend ($k)"; // role: x
const Y_VAL = "Sales Revenue ($k)"; // role: y

// Data: replace this block with your own records
const POINT_COUNT = 90;
let seed = 42;
const data = [];
for (let i = 0; i < POINT_COUNT; i += 1) {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  const uSpend = seed / 4294967296;
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  const u1 = Math.max(seed / 4294967296, 1e-9);
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  const u2 = seed / 4294967296;
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  const spend = 5 + uSpend * 45;
  const revenue = 22 + spend * 3.4 + z * 24;
  data.push({
    [X_VAL]: Number(spend.toFixed(2)),
    [Y_VAL]: Number(Math.max(revenue, 8).toFixed(2)),
  });
}

// Plot: reads only data and the constants above
const xs = data.map((row) => Number(row[X_VAL]));
const ys = data.map((row) => Number(row[Y_VAL]));
const n = xs.length;
const xMean = xs.reduce((a, b) => a + b, 0) / n;
const yMean = ys.reduce((a, b) => a + b, 0) / n;

let sxy = 0;
let sxx = 0;
for (let i = 0; i < n; i += 1) {
  sxy += (xs[i] - xMean) * (ys[i] - yMean);
  sxx += (xs[i] - xMean) ** 2;
}
const slope = sxy / sxx;
const intercept = yMean - slope * xMean;

let ssRes = 0;
let ssTot = 0;
for (let i = 0; i < n; i += 1) {
  const fitted = intercept + slope * xs[i];
  ssRes += (ys[i] - fitted) ** 2;
  ssTot += (ys[i] - yMean) ** 2;
}
const rSquared = 1 - ssRes / ssTot;
const correlation = Math.sign(slope) * Math.sqrt(rSquared);
const residualStdErr = Math.sqrt(ssRes / (n - 2));

const xMin = Math.min(...xs);
const xMax = Math.max(...xs);
const gridX = Array.from(
  { length: GRID_POINTS },
  (_, i) => xMin + ((xMax - xMin) * i) / (GRID_POINTS - 1)
);
const fittedY = gridX.map((x) => intercept + slope * x);
const bandHalfWidth = gridX.map(
  (x) => T_CRIT_95 * residualStdErr * Math.sqrt(1 / n + (x - xMean) ** 2 / sxx)
);
const upperY = fittedY.map((y, i) => y + bandHalfWidth[i]);
const lowerY = fittedY.map((y, i) => y - bandHalfWidth[i]);

const scatterData = xs.map((x, i) => ({
  x,
  y: ys[i],
  id: `pt-${i}`,
}));

const yAllValues = [...ys, ...upperY, ...lowerY];
const yPad = (Math.max(...yAllValues) - Math.min(...yAllValues)) * 0.08;
const yDomainMin = Math.min(...yAllValues) - yPad;
const yDomainMax = Math.max(...yAllValues) + yPad;

const inkMuted = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";
const regressionColor = t.palette[2];
const equationLabel = `y = ${slope.toFixed(2)}x + ${intercept.toFixed(1)}   ·   R² = ${rSquared.toFixed(3)}   ·   r = ${correlation.toFixed(3)}`;

function ConfidenceBand() {
  const xScale = useXScale();
  const yScale = useYScale();
  const top = gridX.map((x, i) => `${xScale(x)},${yScale(upperY[i])}`).join(" L ");
  const bottomIndices = [...gridX.keys()].reverse();
  const bottom = bottomIndices
    .map((i) => `${xScale(gridX[i])},${yScale(lowerY[i])}`)
    .join(" L ");
  return (
    <path
      d={`M ${top} L ${bottom} Z`}
      fill={inkMuted}
      opacity={0.22}
      stroke="none"
    />
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <ChartsContainer
      width={width}
      height={height}
      margin={{ top: 92, right: 56, bottom: 24, left: 36 }}
      series={[
        {
          type: "scatter",
          id: "observations",
          data: scatterData,
          markerSize: 7,
          color: `${t.palette[0]}99`,
        },
        {
          type: "line",
          id: "regression",
          data: fittedY,
          curve: "linear",
          color: regressionColor,
          showMark: false,
          disableHighlight: true,
        },
      ]}
      xAxis={[
        {
          data: gridX,
          scaleType: "linear",
          height: 64,
          label: X_VAL,
          tickLabelStyle: { fontSize: 14 },
          labelStyle: { fontSize: 16 },
        },
      ]}
      yAxis={[
        {
          scaleType: "linear",
          min: yDomainMin,
          max: yDomainMax,
          width: 96,
          label: Y_VAL,
          tickLabelStyle: { fontSize: 14 },
          labelStyle: { fontSize: 16 },
        },
      ]}
      skipAnimation
    >
      <ChartsGrid horizontal />
      <ConfidenceBand />
      <LinePlot
        skipAnimation
        slotProps={{ line: { style: { strokeWidth: 3 } } }}
      />
      <ScatterPlot />
      <ChartsXAxis />
      <ChartsYAxis />
      <text
        x={width / 2}
        y={40}
        textAnchor="middle"
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
      >
        {TITLE}
      </text>
      <text x={140} y={78} fontSize={15} fill={t.inkSoft}>
        {equationLabel}
      </text>
      <text x={140} y={98} fontSize={13} fill={inkMuted}>
        Shaded band: 95% confidence interval for the mean response
      </text>
    </ChartsContainer>
  );
}
