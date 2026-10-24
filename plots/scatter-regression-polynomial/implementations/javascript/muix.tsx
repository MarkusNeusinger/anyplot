// anyplot.ai
// scatter-regression-polynomial: Scatter Plot with Polynomial Regression
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 91/100 | Created: 2026-08-11

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "scatter-regression-polynomial · javascript · muix · anyplot.ai";
const DEGREE = 2;
const CURVE_POINTS = 60;

// Columns: set these to your data's column names
const X_VAL = "Horizontal Distance (m)"; // role: x
const Y_VAL = "Height (m)"; // role: y

// Data: replace this block with your own records
const V0X = 18;
const V0Y = 14;
const H0 = 1.3;
const G = 9.81;
const POINT_COUNT = 85;

const trueA = -G / (2 * V0X ** 2);
const trueB = V0Y / V0X;
const trueC = H0;
const flightRange = (-trueB - Math.sqrt(trueB ** 2 - 4 * trueA * trueC)) / (2 * trueA);

let seed = 42;
const data = [];
for (let i = 0; i < POINT_COUNT; i += 1) {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  const uX = seed / 4294967296;
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  const u1 = Math.max(seed / 4294967296, 1e-9);
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  const u2 = seed / 4294967296;
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  const x = uX * flightRange;
  const trueY = trueA * x ** 2 + trueB * x + trueC;
  const measured = Math.max(trueY + z * 0.4, 0);
  data.push({
    [X_VAL]: Number(x.toFixed(2)),
    [Y_VAL]: Number(measured.toFixed(2)),
  });
}

// Plot: reads only data and the constants above
const xs = data.map((row) => Number(row[X_VAL]));
const ys = data.map((row) => Number(row[Y_VAL]));
const n = xs.length;

const sysSize = DEGREE + 1;
const ata = Array.from({ length: sysSize }, () => new Array(sysSize).fill(0));
const aty = new Array(sysSize).fill(0);
for (let i = 0; i < n; i += 1) {
  const powers = new Array(sysSize);
  let p = 1;
  for (let k = 0; k < sysSize; k += 1) {
    powers[k] = p;
    p *= xs[i];
  }
  for (let r = 0; r < sysSize; r += 1) {
    aty[r] += powers[r] * ys[i];
    for (let c = 0; c < sysSize; c += 1) {
      ata[r][c] += powers[r] * powers[c];
    }
  }
}

const augmented = ata.map((row, i) => [...row, aty[i]]);
for (let col = 0; col < sysSize; col += 1) {
  let pivotRow = col;
  for (let row = col + 1; row < sysSize; row += 1) {
    if (Math.abs(augmented[row][col]) > Math.abs(augmented[pivotRow][col])) {
      pivotRow = row;
    }
  }
  [augmented[col], augmented[pivotRow]] = [augmented[pivotRow], augmented[col]];
  const pivot = augmented[col][col];
  for (let c = col; c <= sysSize; c += 1) {
    augmented[col][c] /= pivot;
  }
  for (let row = 0; row < sysSize; row += 1) {
    if (row === col) continue;
    const factor = augmented[row][col];
    for (let c = col; c <= sysSize; c += 1) {
      augmented[row][c] -= factor * augmented[col][c];
    }
  }
}
const coeffs = augmented.map((row) => row[sysSize]);

const yMean = ys.reduce((sum, y) => sum + y, 0) / n;
let ssRes = 0;
let ssTot = 0;
for (let i = 0; i < n; i += 1) {
  const fitted = coeffs[0] + coeffs[1] * xs[i] + coeffs[2] * xs[i] ** 2;
  ssRes += (ys[i] - fitted) ** 2;
  ssTot += (ys[i] - yMean) ** 2;
}
const rSquared = 1 - ssRes / ssTot;

const xMin = Math.min(...xs);
const xMax = Math.max(...xs);
const curveX = Array.from(
  { length: CURVE_POINTS },
  (_, i) => xMin + ((xMax - xMin) * i) / (CURVE_POINTS - 1)
);
const curveY = curveX.map((x) => coeffs[0] + coeffs[1] * x + coeffs[2] * x ** 2);

const scatterData = xs.map((x, i) => ({ x, y: ys[i], id: `pt-${i}` }));

const yAllValues = [...ys, ...curveY];
const yPad = (Math.max(...yAllValues) - Math.min(...yAllValues)) * 0.1;
const yDomainMin = Math.min(0, Math.min(...yAllValues) - yPad);
const yDomainMax = Math.max(...yAllValues) + yPad;

const regressionColor = t.palette[1];
const linearTerm = `${coeffs[1] >= 0 ? "+" : "-"} ${Math.abs(coeffs[1]).toFixed(3)}`;
const constantTerm = `${coeffs[0] >= 0 ? "+" : "-"} ${Math.abs(coeffs[0]).toFixed(2)}`;
const equationLabel = `h(x) = ${coeffs[2].toFixed(4)}x² ${linearTerm}x ${constantTerm}`;
const fitLabel = `R² = ${rSquared.toFixed(3)}`;

export default function Chart() {
  const { width, height: chartHeight } = window.ANYPLOT_SIZE;

  return (
    <ChartsContainer
      width={width}
      height={chartHeight}
      margin={{ top: 104, right: 56, bottom: 24, left: 28 }}
      series={[
        {
          type: "scatter",
          id: "observations",
          data: scatterData,
          markerSize: 7,
          color: `${t.palette[0]}aa`,
        },
        {
          type: "line",
          id: "regression",
          data: curveY,
          curve: "natural",
          color: regressionColor,
          showMark: false,
          disableHighlight: true,
        },
      ]}
      xAxis={[
        {
          data: curveX,
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
          width: 84,
          label: Y_VAL,
          tickLabelStyle: { fontSize: 14 },
          labelStyle: { fontSize: 16 },
        },
      ]}
      skipAnimation
    >
      <ChartsGrid
        vertical
        horizontal
        sx={{ "& line": { stroke: t.grid, strokeOpacity: 0.15 } }}
      />
      <LinePlot
        skipAnimation
        slotProps={{
          line: {
            style: { strokeWidth: 3.5, filter: `drop-shadow(0 0 1px ${t.ink})` },
          },
        }}
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
      <text x={112} y={72} fontSize={15} fill={t.inkSoft}>
        {equationLabel}
      </text>
      <text
        x={112}
        y={96}
        fontSize={19}
        fontWeight={700}
        fill={regressionColor}
        stroke={t.ink}
        strokeWidth={0.5}
        paintOrder="stroke"
      >
        {fitLabel}
      </text>
    </ChartsContainer>
  );
}
