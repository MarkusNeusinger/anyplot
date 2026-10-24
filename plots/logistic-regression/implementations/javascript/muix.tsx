// anyplot.ai
// logistic-regression: Logistic Regression Curve Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-09-02

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Constants
const PROBABILITY_AXIS_LABEL = "Probability";
const DECISION_THRESHOLD = 0.5;
const X_PAD_FRAC = 0.03;
const Y_PAD_FRAC = 0.08;
const JITTER_SPREAD = 0.14;
const CURVE_STEPS = 200;
const GD_ITERATIONS = 600;
const GD_LR = 0.5;
const Z95 = 1.96;
const POINT_ALPHA_HEX = "99"; // ~0.60 alpha

const SEMANTIC_COLORS: Record<number, string> = {
  0: t.palette[4],
  1: t.palette[0],
};

// Columns: set these to your data's column names
const SCORE = "Customer engagement score"; // role: x
const OUTCOME = "Converted"; // role: y
const OUTCOME_LABEL = "Outcome class"; // role: class_label

// Data: replace this block with your own records
const N_POINTS = 180;
let seed = 42 >>> 0;
const rawScores: number[] = [];
for (let i = 0; i < N_POINTS; i++) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  rawScores.push(Math.round((seed / 4294967296) * 1000) / 10);
}

const rawConverted: number[] = [];
for (let i = 0; i < N_POINTS; i++) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const u = seed / 4294967296;
  const pTrue = 1 / (1 + Math.exp(-(0.09 * (rawScores[i] - 55))));
  rawConverted.push(u < pTrue ? 1 : 0);
}

const data: Array<Record<string, number | string>> = [];
for (let i = 0; i < N_POINTS; i++) {
  const yBin = rawConverted[i];
  data.push({
    [SCORE]: rawScores[i],
    [OUTCOME]: yBin,
    [OUTCOME_LABEL]: yBin === 1 ? "Converted (y = 1)" : "Not converted (y = 0)",
  });
}

// Plot: reads only data and the constants above
let jitterSeed = 1337 >>> 0;
const jitteredRows = data.map((r, idx) => {
  jitterSeed = (Math.imul(1664525, jitterSeed) + 1013904223) >>> 0;
  const jitter = (jitterSeed / 4294967296 - 0.5) * JITTER_SPREAD;
  const yBin = Number(r[OUTCOME]);
  const label = r[OUTCOME_LABEL]
    ? String(r[OUTCOME_LABEL])
    : `${OUTCOME} = ${yBin}`;
  return {
    id: idx,
    x: Number(r[SCORE]),
    yBin,
    yJittered: yBin + jitter,
    label,
  };
});

// Discover binary outcomes in order [0, 1] and assign semantic/palette colors
const outcomeBins: number[] = [0, 1].filter((b) =>
  jitteredRows.some((r) => r.yBin === b),
);
for (const r of jitteredRows) {
  if (!outcomeBins.includes(r.yBin)) outcomeBins.push(r.yBin);
}

const usedPalette = new Set(Object.values(SEMANTIC_COLORS));
let nextSlot = 0;
const classColorMap: Record<number, string> = {};
const classLabelMap: Record<number, string> = {};
for (const b of outcomeBins) {
  const firstMatch = jitteredRows.find((r) => r.yBin === b)!;
  classLabelMap[b] = firstMatch.label;
  if (b in SEMANTIC_COLORS) {
    classColorMap[b] = SEMANTIC_COLORS[b];
  } else {
    while (usedPalette.has(t.palette[nextSlot])) nextSlot++;
    classColorMap[b] = t.palette[nextSlot];
    usedPalette.add(t.palette[nextSlot]);
  }
}

// Fit logistic regression by batch gradient descent on standardized x
const nObs = jitteredRows.length;
const xs = jitteredRows.map((r) => r.x);
const ys = jitteredRows.map((r) => r.yBin);
const xMean = xs.reduce((a, b) => a + b, 0) / nObs;
const xStd = Math.sqrt(xs.reduce((a, b) => a + (b - xMean) ** 2, 0) / nObs);
const xn = xs.map((v) => (v - xMean) / xStd);

let b0 = 0;
let b1 = 0;
for (let iter = 0; iter < GD_ITERATIONS; iter++) {
  let grad0 = 0;
  let grad1 = 0;
  for (let i = 0; i < nObs; i++) {
    const p = 1 / (1 + Math.exp(-(b0 + b1 * xn[i])));
    const err = p - ys[i];
    grad0 += err;
    grad1 += err * xn[i];
  }
  b0 -= (GD_LR * grad0) / nObs;
  b1 -= (GD_LR * grad1) / nObs;
}

// Observed Fisher information covariance (X'WX)^-1
let info00 = 0;
let info01 = 0;
let info11 = 0;
for (let i = 0; i < nObs; i++) {
  const p = 1 / (1 + Math.exp(-(b0 + b1 * xn[i])));
  const w = p * (1 - p);
  info00 += w;
  info01 += w * xn[i];
  info11 += w * xn[i] * xn[i];
}
const det = info00 * info11 - info01 * info01;
const varB0 = info11 / det;
const varB1 = info00 / det;
const covB01 = -info01 / det;

const midpointX = xMean + (-b0 / b1) * xStd;
let correctCount = 0;
for (let i = 0; i < nObs; i++) {
  const p = 1 / (1 + Math.exp(-(b0 + b1 * xn[i])));
  const pred = p >= DECISION_THRESHOLD ? 1 : 0;
  if (pred === ys[i]) correctCount++;
}
const accuracy = correctCount / nObs;

const rawXMin = Math.min(...xs);
const rawXMax = Math.max(...xs);
const xSpan = rawXMax - rawXMin;
const xDataMin = rawXMin - xSpan * X_PAD_FRAC;
const xDataMax = rawXMax + xSpan * X_PAD_FRAC;
const yAxisMin = -Y_PAD_FRAC;
const yAxisMax = 1 + Y_PAD_FRAC;

const curveXs: number[] = [];
const curveY: number[] = [];
const ciLower: number[] = [];
const ciUpper: number[] = [];

for (let i = 0; i < CURVE_STEPS; i++) {
  const xVal = xDataMin + (i / (CURVE_STEPS - 1)) * (xDataMax - xDataMin);
  const z = (xVal - xMean) / xStd;
  const eta = b0 + b1 * z;
  const se = Math.sqrt(Math.max(0, varB0 + 2 * z * covB01 + z * z * varB1));
  curveXs.push(xVal);
  curveY.push(1 / (1 + Math.exp(-eta)));
  ciLower.push(1 / (1 + Math.exp(-(eta - Z95 * se))));
  ciUpper.push(1 / (1 + Math.exp(-(eta + Z95 * se))));
}

const scatterSeries = outcomeBins.map((bin, idx) => {
  const rows = jitteredRows.filter((r) => r.yBin === bin);
  return {
    type: "scatter" as const,
    id: `class-${idx}`,
    data: rows.map((r) => ({
      x: r.x,
      y: r.yJittered,
      id: `${idx}-${r.id}`,
    })),
    label: classLabelMap[bin],
    color: `${classColorMap[bin]}${POINT_ALPHA_HEX}`,
    markerSize: 7,
    xAxisId: "engagement",
    yAxisId: "probability",
  };
});

function LogisticOverlay() {
  const xScale = useXScale("engagement") as (v: number) => number;
  const yScale = useYScale("probability") as (v: number) => number;

  const upperPts = curveXs.map((x, i) => [xScale(x), yScale(ciUpper[i])]);
  const lowerPts = curveXs.map((x, i) => [xScale(x), yScale(ciLower[i])]);
  const bandPts = [...upperPts, ...lowerPts.slice().reverse()];
  const bandD =
    bandPts
      .map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)},${p[1].toFixed(1)}`)
      .join(" ") + " Z";

  const curveD = curveXs
    .map((x, i) => `${i === 0 ? "M" : "L"}${xScale(x).toFixed(1)},${yScale(curveY[i]).toFixed(1)}`)
    .join(" ");

  const markerX = xScale(midpointX);
  const markerY = yScale(DECISION_THRESHOLD);
  const labelX = markerX - 68;
  const labelY = yScale(0.62);

  return (
    <g>
      <path d={bandD} fill={t.ink} fillOpacity={0.14} stroke="none" />
      <path
        d={curveD}
        fill="none"
        stroke={t.ink}
        strokeWidth={3}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle
        cx={markerX}
        cy={markerY}
        r={5.5}
        fill={t.pageBg}
        stroke={t.ink}
        strokeWidth={2}
      />
      <text x={labelX} y={labelY} fontSize={14} fill={t.inkSoft} textAnchor="end">
        <tspan x={labelX} dy={0}>{`Midpoint ≈ ${midpointX.toFixed(1)}`}</tspan>
        <tspan x={labelX} dy={19}>{`Accuracy at p=${DECISION_THRESHOLD}: ${(accuracy * 100).toFixed(0)}%`}</tspan>
      </text>
    </g>
  );
}

const TITLE = "logistic-regression · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 64;

const LEGEND_ITEMS = [
  ...outcomeBins.map((b) => ({
    type: "circle" as const,
    color: classColorMap[b],
    label: classLabelMap[b],
  })),
  { type: "line" as const, color: t.ink, label: "Fitted probability (95% CI)" },
];

export default function Chart() {
  return (
    <div style={{ width, height, backgroundColor: t.pageBg }}>
      <div
        style={{
          height: TITLE_HEIGHT,
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
        <div
          style={{
            position: "absolute",
            top: "50%",
            right: 64,
            transform: "translateY(-50%)",
            display: "flex",
            flexDirection: "column",
            gap: 5,
            alignItems: "flex-start",
          }}
        >
          {LEGEND_ITEMS.map((item) => (
            <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {item.type === "circle" ? (
                <span
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    backgroundColor: item.color,
                    flexShrink: 0,
                  }}
                />
              ) : (
                <span
                  style={{
                    width: 18,
                    height: 3,
                    backgroundColor: item.color,
                    flexShrink: 0,
                  }}
                />
              )}
              <span style={{ fontSize: 14, color: t.ink }}>{item.label}</span>
            </div>
          ))}
        </div>
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_HEIGHT}
        skipAnimation
        margin={{ top: 24, right: 64, bottom: 20, left: 20 }}
        series={scatterSeries}
        xAxis={[
          {
            id: "engagement",
            scaleType: "linear",
            data: curveXs,
            min: xDataMin,
            max: xDataMax,
            height: 60,
            label: SCORE,
            tickNumber: 6,
            valueFormatter: (v: number | null) =>
              v === null ? "" : `${Math.round(v)}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "probability",
            min: yAxisMin,
            max: yAxisMax,
            width: 76,
            label: PROBABILITY_AXIS_LABEL,
            tickInterval: [0, 0.2, 0.4, 0.6, 0.8, 1],
            valueFormatter: (v: number | null) => (v != null ? v.toFixed(1) : ""),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <ChartsGrid horizontal />
        <ScatterPlot skipAnimation />
        <LogisticOverlay />
        <ChartsXAxis axisId="engagement" />
        <ChartsYAxis axisId="probability" />
        <ChartsReferenceLine
          y={DECISION_THRESHOLD}
          axisId="probability"
          label={`Decision threshold (p = ${DECISION_THRESHOLD})`}
          labelAlign="start"
          labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "8 5", strokeWidth: 1.5 }}
        />
      </ChartsContainer>
    </div>
  );
}
