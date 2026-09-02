// anyplot.ai
// logistic-regression: Logistic Regression Curve Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-02

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Reproducible LCG (seed 42) — no Math.random() in the browser harness context
let seed = 42;
function rng() {
  seed = (1664525 * seed + 1013904223) >>> 0;
  return seed / 4294967296;
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Data: marketing conversion vs. customer engagement score --------------
// True generating relationship — a customer with a higher engagement score
// (0-100) is more likely to convert, with a decision midpoint around 55.
function trueProbability(score) {
  return 1 / (1 + Math.exp(-(0.09 * (score - 55))));
}

const N_POINTS = 180;
const engagementScores = Array.from(
  { length: N_POINTS },
  () => Math.round(rng() * 1000) / 10,
);
const converted = engagementScores.map((score) => (rng() < trueProbability(score) ? 1 : 0));

// Jitter around 0 / 1 so overlapping points stay legible
const scatterClass0 = [];
const scatterClass1 = [];
engagementScores.forEach((score, i) => {
  const jitter = (rng() - 0.5) * 0.1;
  if (converted[i] === 1) {
    scatterClass1.push({ x: score, y: 1 + jitter, id: `converted-${i}` });
  } else {
    scatterClass0.push({ x: score, y: 0 + jitter, id: `not-converted-${i}` });
  }
});

// --- Fit a logistic regression by batch gradient descent (standardized x) --
function fitLogisticRegression(xs, ys, iterations, learningRate) {
  const n = xs.length;
  const mean = xs.reduce((a, b) => a + b, 0) / n;
  const std = Math.sqrt(xs.reduce((a, b) => a + (b - mean) ** 2, 0) / n);
  const xn = xs.map((v) => (v - mean) / std);

  let b0 = 0;
  let b1 = 0;
  for (let iter = 0; iter < iterations; iter++) {
    let grad0 = 0;
    let grad1 = 0;
    for (let i = 0; i < n; i++) {
      const p = 1 / (1 + Math.exp(-(b0 + b1 * xn[i])));
      const error = p - ys[i];
      grad0 += error;
      grad1 += error * xn[i];
    }
    b0 -= (learningRate * grad0) / n;
    b1 -= (learningRate * grad1) / n;
  }

  // Wald standard errors from the observed Fisher information (X'WX)^-1
  let info00 = 0;
  let info01 = 0;
  let info11 = 0;
  for (let i = 0; i < n; i++) {
    const p = 1 / (1 + Math.exp(-(b0 + b1 * xn[i])));
    const w = p * (1 - p);
    info00 += w;
    info01 += w * xn[i];
    info11 += w * xn[i] * xn[i];
  }
  const det = info00 * info11 - info01 * info01;
  return {
    b0,
    b1,
    mean,
    std,
    varB0: info11 / det,
    varB1: info00 / det,
    covB01: -info01 / det,
  };
}

const model = fitLogisticRegression(engagementScores, converted, 600, 0.5);

// 95% Wald confidence interval on the predicted probability, via the delta
// method on the linear predictor (standard logistic-regression CI approach).
const Z95 = 1.96;
function predictWithCI(x) {
  const xn = (x - model.mean) / model.std;
  const eta = model.b0 + model.b1 * xn;
  const se = Math.sqrt(model.varB0 + 2 * xn * model.covB01 + xn * xn * model.varB1);
  const sigmoid = (v) => 1 / (1 + Math.exp(-v));
  return {
    probability: sigmoid(eta),
    lower: sigmoid(eta - Z95 * se),
    upper: sigmoid(eta + Z95 * se),
  };
}

const CURVE_POINTS = 200;
const curveXs = Array.from({ length: CURVE_POINTS }, (_, i) => (i / (CURVE_POINTS - 1)) * 100);
const curvePredictions = curveXs.map(predictWithCI);
const curveY = curvePredictions.map((p) => p.probability);
const ciLower = curvePredictions.map((p) => p.lower);
const ciUpper = curvePredictions.map((p) => p.upper);

// 95% confidence band, drawn as a filled path from the live axis scales —
// the two Imprint stops the band would need don't apply here (this is an
// uncertainty band around a single fit, not sequential/diverging data), so
// it reuses the neutral ink token at low opacity, matching the fitted line.
function ConfidenceBand() {
  const xScale = useXScale();
  const yScale = useYScale();
  if (!xScale || !yScale) return null;

  const upper = curveXs.map((x, i) => [xScale(x), yScale(ciUpper[i])]);
  const lower = curveXs.map((x, i) => [xScale(x), yScale(ciLower[i])]);
  const points = [...upper, ...lower.slice().reverse()];
  const d =
    points.map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ") +
    " Z";

  return <path d={d} fill={t.ink} fillOpacity={0.14} stroke="none" />;
}

const TITLE = "Customer Conversion · logistic-regression · javascript · muix · anyplot.ai";
const TITLE_FONT_DEFAULT = 22;
const titleFontSize =
  TITLE.length > 67 ? Math.round(TITLE_FONT_DEFAULT * (67 / TITLE.length)) : TITLE_FONT_DEFAULT;
const TITLE_HEIGHT = 60;

export default function Chart() {
  return (
    <div style={{ width, height, backgroundColor: t.pageBg }}>
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: titleFontSize,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartContainer
        width={width}
        height={height - TITLE_HEIGHT}
        margin={{ top: 24, right: 64, bottom: 84, left: 92 }}
        sx={{ "& .MuiLineElement-series-fitted-curve": { strokeWidth: 3 } }}
        series={[
          {
            type: "line",
            id: "fitted-curve",
            data: curveY,
            label: "Fitted probability",
            color: t.ink,
            showMark: false,
            curve: "monotoneX",
            xAxisId: "engagement",
          },
          {
            type: "scatter",
            id: "class-0",
            data: scatterClass0,
            label: "Not converted (y = 0)",
            color: hexToRgba(t.palette[4], 0.6),
            markerSize: 10,
            xAxisId: "engagement",
          },
          {
            type: "scatter",
            id: "class-1",
            data: scatterClass1,
            label: "Converted (y = 1)",
            color: hexToRgba(t.palette[0], 0.6),
            markerSize: 10,
            xAxisId: "engagement",
          },
        ]}
        xAxis={[
          {
            id: "engagement",
            scaleType: "linear",
            data: curveXs,
            min: 0,
            max: 100,
            label: "Customer Engagement Score",
            tickInterval: [0, 20, 40, 60, 80, 100],
            valueFormatter: (v) => `${v}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "probability",
            min: -0.08,
            max: 1.08,
            label: "Probability",
            tickInterval: [0, 0.2, 0.4, 0.6, 0.8, 1],
            valueFormatter: (v) => v.toFixed(1),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <ChartsGrid horizontal />
        <ConfidenceBand />
        <ScatterPlot skipAnimation />
        <LinePlot skipAnimation />
        <ChartsXAxis
          axisId="engagement"
          tickLabelStyle={{ fontSize: 14, fill: t.inkSoft }}
          labelStyle={{ fontSize: 16, fill: t.ink }}
        />
        <ChartsYAxis
          axisId="probability"
          tickLabelStyle={{ fontSize: 14, fill: t.inkSoft }}
          labelStyle={{ fontSize: 16, fill: t.ink }}
        />
        <ChartsReferenceLine
          y={0.5}
          axisId="probability"
          label="Decision threshold (p = 0.5)"
          labelAlign="start"
          labelStyle={{ fill: t.inkSoft, fontSize: 13 }}
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "8 5", strokeWidth: 1.5 }}
        />
        <ChartsLegend
          position={{ vertical: "top", horizontal: "right" }}
          slotProps={{
            legend: {
              itemMarkWidth: 20,
              itemMarkHeight: 4,
              markGap: 8,
              itemGap: 24,
              labelStyle: { fontSize: 14, fill: t.ink },
            },
          }}
        />
      </ChartContainer>
    </div>
  );
}
