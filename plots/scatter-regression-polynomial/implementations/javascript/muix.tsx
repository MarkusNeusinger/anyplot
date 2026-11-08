// anyplot.ai
// scatter-regression-polynomial: Scatter Plot with Polynomial Regression
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 91/100 | Created: 2026-08-11

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

const t = window.ANYPLOT_TOKENS;

// Constants
const POLY_DEGREE = 2; // quadratic by default; 3 or 4 only when the pattern calls for it
const DEGREE_NAMES: Record<number, string> = { 2: "Quadratic", 3: "Cubic", 4: "Quartic" };
const SUPERSCRIPTS = ["", "", "²", "³", "⁴"];
const CURVE_POINTS = 60; // x positions at which the fitted polynomial is evaluated
const POINT_OPACITY = 0.67;
const X_PAD_SHARE = 0.03; // axis padding as a share of the data span
const Y_PAD_SHARE = 0.08;

// Columns: set these to your data's column names
const X = "Horizontal distance (m)"; // role: x
const Y = "Height (m)"; // role: y

// Data: replace this block with your own records, one object per row
// Tracked ball flight: h(x) = -g / (2 v0x²) x² + (v0y / v0x) x + h0, plus sensor noise.
const V0X = 18; // horizontal release velocity, m/s
const V0Y = 14; // vertical release velocity, m/s
const H0 = 1.3; // release height, m
const G = 9.81; // m/s²
const trueA = -G / (2 * V0X ** 2);
const trueB = V0Y / V0X;
const flightRange = (-trueB - Math.sqrt(trueB ** 2 - 4 * trueA * H0)) / (2 * trueA);
const data: Record<string, number>[] = [];
let seed = 42;
for (let i = 0; i < 85; i += 1) {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  const x = (seed / 4294967296) * flightRange;
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  const u1 = Math.max(seed / 4294967296, 1e-9);
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  const u2 = seed / 4294967296;
  const noise = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  const measured = Math.max(trueA * x ** 2 + trueB * x + H0 + noise * 0.4, 0);
  data.push({ [X]: Number(x.toFixed(2)), [Y]: Number(measured.toFixed(2)) });
}

// Plot: reads only data and the constants above
const xs = data.map((d) => d[X]);
const ys = data.map((d) => d[Y]);
const n = data.length;

// Least squares: normal equations (AᵀA)c = Aᵀy, solved by Gauss-Jordan with partial pivoting
const size = POLY_DEGREE + 1;
const augmented: number[][] = Array.from({ length: size }, () => new Array(size + 1).fill(0));
for (let i = 0; i < n; i += 1) {
  for (let r = 0; r < size; r += 1) {
    augmented[r][size] += xs[i] ** r * ys[i];
    for (let c = 0; c < size; c += 1) augmented[r][c] += xs[i] ** (r + c);
  }
}
for (let col = 0; col < size; col += 1) {
  let pivotRow = col;
  for (let row = col + 1; row < size; row += 1) {
    if (Math.abs(augmented[row][col]) > Math.abs(augmented[pivotRow][col])) pivotRow = row;
  }
  [augmented[col], augmented[pivotRow]] = [augmented[pivotRow], augmented[col]];
  const pivot = augmented[col][col];
  for (let c = col; c <= size; c += 1) augmented[col][c] /= pivot;
  for (let row = 0; row < size; row += 1) {
    if (row === col) continue;
    const factor = augmented[row][col];
    for (let c = col; c <= size; c += 1) augmented[row][c] -= factor * augmented[col][c];
  }
}
const coeffs = augmented.map((row) => row[size]); // ascending powers: c0, c1, c2, ...

const fitted = xs.map((x) => coeffs.reduce((sum, c, k) => sum + c * x ** k, 0));
const yMean = ys.reduce((sum, y) => sum + y, 0) / n;
const ssRes = ys.reduce((sum, y, i) => sum + (y - fitted[i]) ** 2, 0);
const ssTot = ys.reduce((sum, y) => sum + (y - yMean) ** 2, 0);
const rSquared = 1 - ssRes / ssTot;

const xMin = Math.min(...xs);
const xMax = Math.max(...xs);
const curveX = Array.from({ length: CURVE_POINTS }, (_, i) => xMin + ((xMax - xMin) * i) / (CURVE_POINTS - 1));
const curveY = curveX.map((x) => coeffs.reduce((sum, c, k) => sum + c * x ** k, 0));

const xPad = (xMax - xMin) * X_PAD_SHARE;
const yLow = Math.min(...ys, ...curveY);
const yHigh = Math.max(...ys, ...curveY);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;

const equation = `y = ${coeffs
  .map((c, k) => ({ c, k }))
  .reverse()
  .map(({ c, k }, i) => {
    const sign = c < 0 ? "−" : i === 0 ? "" : "+";
    const term = `${Math.abs(c).toPrecision(3)}${k > 0 ? "x" : ""}${SUPERSCRIPTS[k]}`;
    return i === 0 ? `${sign}${term}` : `${sign} ${term}`;
  })
  .join(" ")}`;
const fitName = DEGREE_NAMES[POLY_DEGREE];

const scatterData = data.map((d, i) => ({ x: d[X], y: d[Y], id: i }));
const title = "Polynomial Regression · scatter-regression-polynomial · javascript · muix · anyplot.ai";
const HEADER_H = 112;
const LEGEND_H = 40;

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
          gap: 8,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{title}</div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 24 }}>
          <span style={{ fontSize: 24, fontWeight: 700, color: t.ink }}>R² = {rSquared.toFixed(3)}</span>
          <span style={{ fontSize: 16, color: t.inkSoft }}>
            {fitName} least-squares fit: {equation} · n = {n}
          </span>
        </div>
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
            id: "fit",
            label: `${fitName} fit (degree ${POLY_DEGREE})`,
            data: curveY,
            curve: "natural",
            color: t.palette[1],
            showMark: false,
          },
        ]}
        xAxis={[
          {
            scaleType: "linear",
            data: curveX,
            min: xMin - xPad,
            max: xMax + xPad,
            label: X,
            height: 68,
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
            width: 72,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
            sx: { "& .MuiChartsAxis-line, & .MuiChartsAxis-tick": { stroke: t.inkSoft } },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ horizontal: "end", vertical: "top" }} legendDirection="horizontal">
          <ChartsLegend
            sx={{
              fontSize: 16,
              color: t.ink,
              pr: 7,
              '& [data-series="observations"] .MuiChartsLegend-mark': { opacity: POINT_OPACITY },
            }}
          />
          <ChartsSurface
            sx={{
              "& .MuiScatterChart-marker": { fillOpacity: POINT_OPACITY },
              "& .MuiLineChart-line": { strokeWidth: 3.5 },
            }}
          >
            <ChartsGrid horizontal vertical />
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
