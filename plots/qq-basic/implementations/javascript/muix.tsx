// anyplot.ai
// qq-basic: Basic Q-Q Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-07-24

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Deterministic LCG (seed 42) — no Math.random() in browser harness
let _seed = 42;
function lcg() {
  _seed = (1664525 * _seed + 1013904223) >>> 0;
  return _seed / 4294967296;
}
function randn() {
  const u = lcg(), v = lcg();
  return Math.sqrt(-2 * Math.log(u + 1e-15)) * Math.cos(2 * Math.PI * v);
}

// Inverse standard-normal CDF (Acklam's rational approximation, |err| < 1.15e-9)
function invNorm(p) {
  const a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00];
  const b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01];
  const c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00];
  const d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00];
  const pLow = 0.02425;
  if (p < pLow) {
    const q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
      ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  if (p <= 1 - pLow) {
    const q = p - 0.5, r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
      (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  const q = Math.sqrt(-2 * Math.log(1 - p));
  return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
    ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
}

// Order-fulfillment time (hours), right-skewed lognormal process — a classic
// "does this follow a Normal distribution" QC question. Deliberately non-normal
// so the plot demonstrates a real curvature away from the diagonal.
const N = 60;
const MU = 3.4, SIGMA = 0.35;
const rawSample = Array.from({ length: N }, () => Math.exp(MU + SIGMA * randn()));
const sorted = [...rawSample].sort((x, y) => x - y);

const mean = sorted.reduce((s, v) => s + v, 0) / N;
const variance = sorted.reduce((s, v) => s + (v - mean) ** 2, 0) / (N - 1);
const std = Math.sqrt(variance);

// Blom plotting positions, standardized sample quantiles so a perfectly Normal
// sample lands exactly on y = x.
const points = sorted.map((v, i) => {
  const p = (i + 1 - 0.375) / (N + 0.25);
  const x = invNorm(p);
  const y = (v - mean) / std;
  return { x, y, id: i };
});

const allValues = points.flatMap((pt) => [pt.x, pt.y]);
const rangeMin = Math.min(...allValues);
const rangeMax = Math.max(...allValues);
const pad = (rangeMax - rangeMin) * 0.08;
const axMin = rangeMin - pad;
const axMax = rangeMax + pad;

// Diagonal y = x reference line — rendered via MUI X axis scale hooks
function ReferenceLine() {
  const xScale = useXScale();
  const yScale = useYScale();
  if (!xScale || !yScale) return null;
  return (
    <line
      x1={xScale(axMin)} y1={yScale(axMin)}
      x2={xScale(axMax)} y2={yScale(axMax)}
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

const TITLE = "qq-basic · javascript · muix · anyplot.ai";
const MARGIN = { top: 80, right: 60, bottom: 96, left: 110 };

export default function Chart() {
  return (
    <ChartContainer
      width={width}
      height={height}
      margin={MARGIN}
      series={series}
      xAxis={[{
        scaleType: "linear",
        min: axMin,
        max: axMax,
        label: "Theoretical Quantiles",
        tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        labelStyle: { fontSize: 16, fill: t.ink },
      }]}
      yAxis={[{
        scaleType: "linear",
        min: axMin,
        max: axMax,
        label: "Sample Quantiles",
        tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        labelStyle: { fontSize: 16, fill: t.ink },
      }]}
    >
      <ChartsGrid horizontal vertical />
      <ReferenceLine />
      <ScatterPlot skipAnimation />
      <ChartsXAxis />
      <ChartsYAxis />
      {/* L-frame: mask top and right spines with background color */}
      <line
        x1={MARGIN.left - 1} y1={MARGIN.top}
        x2={width - MARGIN.right + 1} y2={MARGIN.top}
        stroke={t.pageBg}
        strokeWidth={3}
      />
      <line
        x1={width - MARGIN.right} y1={MARGIN.top - 1}
        x2={width - MARGIN.right} y2={height - MARGIN.bottom + 1}
        stroke={t.pageBg}
        strokeWidth={3}
      />
      {/* Title */}
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
      {/* Subtitle */}
      <text
        x={width / 2}
        y={58}
        textAnchor="middle"
        fontSize={14}
        fill={t.inkSoft}
      >
        Order fulfillment time (n = 60, standardized) vs. Normal — upper-tail curvature reveals right skew
      </text>
      {/* Reference-line caption */}
      <text
        x={width - MARGIN.right - 14}
        y={MARGIN.top + 28}
        textAnchor="end"
        fontSize={14}
        fill={t.inkSoft}
      >
        {"– – –  y = x  (perfect Normal fit)"}
      </text>
    </ChartContainer>
  );
}
