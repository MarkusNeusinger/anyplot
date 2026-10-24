// anyplot.ai
// qq-basic: Basic Q-Q Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-07-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "qq-basic · javascript · muix · anyplot.ai";
const X_TITLE = "Theoretical Quantiles";
const Y_TITLE = "Sample Quantiles";
const MARGIN = { top: 80, right: 60, bottom: 32, left: 32 };
const ACKLAM_A = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00];
const ACKLAM_B = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01];
const ACKLAM_C = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00];
const ACKLAM_D = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00];
const ACKLAM_P_LOW = 0.02425;

// Columns: set these to your data's column names
const SAMPLE = "Order fulfillment time (h)"; // role: sample

// Data: replace this block with your own records
const N_OBS = 60;
const LOG_MU = 3.4;
const LOG_SIGMA = 0.35;
let seed = 42;
const data = Array.from({ length: N_OBS }, () => {
  seed = (1664525 * seed + 1013904223) >>> 0;
  const u = seed / 4294967296;
  seed = (1664525 * seed + 1013904223) >>> 0;
  const v = seed / 4294967296;
  const z = Math.sqrt(-2 * Math.log(u + 1e-15)) * Math.cos(2 * Math.PI * v);
  return { [SAMPLE]: Math.exp(LOG_MU + LOG_SIGMA * z) };
});

// Plot: reads only data and the constants above
const sorted = data.map((row) => Number(row[SAMPLE])).sort((x, y) => x - y);
const n = sorted.length;
const mean = sorted.reduce((s, v) => s + v, 0) / n;
const variance = sorted.reduce((s, v) => s + (v - mean) ** 2, 0) / (n - 1);
const std = Math.sqrt(variance);

const points = sorted.map((v, i) => {
  const p = (i + 1 - 0.375) / (n + 0.25);
  let x;
  if (p < ACKLAM_P_LOW) {
    const q = Math.sqrt(-2 * Math.log(p));
    x =
      (((((ACKLAM_C[0] * q + ACKLAM_C[1]) * q + ACKLAM_C[2]) * q + ACKLAM_C[3]) * q + ACKLAM_C[4]) * q + ACKLAM_C[5]) /
      ((((ACKLAM_D[0] * q + ACKLAM_D[1]) * q + ACKLAM_D[2]) * q + ACKLAM_D[3]) * q + 1);
  } else if (p <= 1 - ACKLAM_P_LOW) {
    const q = p - 0.5;
    const r = q * q;
    x =
      ((((((ACKLAM_A[0] * r + ACKLAM_A[1]) * r + ACKLAM_A[2]) * r + ACKLAM_A[3]) * r + ACKLAM_A[4]) * r + ACKLAM_A[5]) * q) /
      (((((ACKLAM_B[0] * r + ACKLAM_B[1]) * r + ACKLAM_B[2]) * r + ACKLAM_B[3]) * r + ACKLAM_B[4]) * r + 1);
  } else {
    const q = Math.sqrt(-2 * Math.log(1 - p));
    x =
      -(((((ACKLAM_C[0] * q + ACKLAM_C[1]) * q + ACKLAM_C[2]) * q + ACKLAM_C[3]) * q + ACKLAM_C[4]) * q + ACKLAM_C[5]) /
      ((((ACKLAM_D[0] * q + ACKLAM_D[1]) * q + ACKLAM_D[2]) * q + ACKLAM_D[3]) * q + 1);
  }
  const y = (v - mean) / std;
  return { x, y, id: i };
});

const allValues = points.flatMap((pt) => [pt.x, pt.y]);
const rangeMin = Math.min(...allValues);
const rangeMax = Math.max(...allValues);
const pad = (rangeMax - rangeMin) * 0.08;
const axMin = rangeMin - pad;
const axMax = rangeMax + pad;

function ReferenceLine() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <line
      x1={xScale(axMin)}
      y1={yScale(axMin)}
      x2={xScale(axMax)}
      y2={yScale(axMax)}
      stroke={t.ink}
      strokeWidth={2.5}
      strokeDasharray="10,8"
      opacity={0.5}
    />
  );
}

const series = [
  {
    type: "scatter",
    id: "sample",
    label: "Sample vs. Normal",
    color: t.palette[0],
    markerSize: 9,
    data: points,
  },
];

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <ChartsContainer
      width={width}
      height={height}
      margin={MARGIN}
      series={series}
      skipAnimation
      xAxis={[
        {
          scaleType: "linear",
          min: axMin,
          max: axMax,
          height: 64,
          label: X_TITLE,
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
          label: Y_TITLE,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          labelStyle: { fontSize: 16, fill: t.ink },
        },
      ]}
    >
      <ChartsGrid horizontal vertical />
      <ReferenceLine />
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
        {`${SAMPLE} (n = ${n}, standardized) vs. Normal — upper-tail curvature reveals right skew`}
      </text>
      <text
        x={width - MARGIN.right - 14}
        y={MARGIN.top + 28}
        textAnchor="end"
        fontSize={14}
        fill={t.inkSoft}
      >
        {"– – –  y = x  (perfect Normal fit)"}
      </text>
    </ChartsContainer>
  );
}
