// anyplot.ai
// logistic-regression: Logistic Regression Curve Plot
// Library: muix 9.x | JavaScript 22.23.2
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
const SCORE_COL = "Customer Engagement Score" as const;
const OUTCOME_COL = "Converted" as const;
const CLASS_LABEL_COL = "Outcome Class" as const;
const JITTER_Y_COL = "Probability" as const;

const DECISION_THRESHOLD = 0.5;
const Y_PAD_FRAC = 0.08;
const CURVE_STEPS = 200;
const GD_ITERATIONS = 600;
const GD_LR = 0.5;
const POINT_ALPHA_HEX = "99"; // ~0.60 alpha

const T_CRIT_95: Array<[number, number]> = [
  [10, 2.228],
  [20, 2.086],
  [30, 2.042],
  [60, 2.0],
  [120, 1.98],
  [Infinity, 1.96],
];

const SEMANTIC_COLORS: Record<string, string> = {
  "Not converted (y = 0)": t.palette[4],
  "Converted (y = 1)": t.palette[0],
};

// Data — marketing conversion vs. customer engagement score (180 observations)
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

const DATA: Array<Record<string, number | string>> = [];
for (let i = 0; i < N_POINTS; i++) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const jitter = (seed / 4294967296 - 0.5) * 0.14;
  const yBin = rawConverted[i];
  DATA.push({
    [SCORE_COL]: rawScores[i],
    [OUTCOME_COL]: yBin,
    [CLASS_LABEL_COL]: yBin === 1 ? "Converted (y = 1)" : "Not converted (y = 0)",
    [JITTER_Y_COL]: yBin + jitter,
  });
}

// Discover outcome classes in order of appearance and assign semantic/palette colors
const classes: string[] = ["Not converted (y = 0)", "Converted (y = 1)"].filter((c) =>
  DATA.some((r) => String(r[CLASS_LABEL_COL]) === c),
);
for (const row of DATA) {
  const c = String(row[CLASS_LABEL_COL]);
  if (!classes.includes(c)) classes.push(c);
}

const usedPalette = new Set(Object.values(SEMANTIC_COLORS));
let nextSlot = 0;
const classColorMap: Record<string, string> = {};
for (const c of classes) {
  if (SEMANTIC_COLORS[c]) {
    classColorMap[c] = SEMANTIC_COLORS[c];
  } else {
    while (usedPalette.has(t.palette[nextSlot])) nextSlot++;
    classColorMap[c] = t.palette[nextSlot];
    usedPalette.add(t.palette[nextSlot]);
  }
}

// Fit logistic regression by batch gradient descent on standardized x
const nObs = DATA.length;
const xs = DATA.map((r) => Number(r[SCORE_COL]));
const ys = DATA.map((r) => Number(r[OUTCOME_COL]));
const xMean = xs.reduce((a, b) => a + b, 0) / nObs;
const xStd = Math.sqrt(xs.reduce((a, b) => a + (b - xMean) ** 2, 0) / nObs) || 1;
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
const det = info00 * info11 - info01 * info01 || 1;
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

const df = Math.max(1, nObs - 2);
const tCrit95 = (T_CRIT_95.find(([limit]) => df <= limit) ?? T_CRIT_95[T_CRIT_95.length - 1])[1];

const xDataMin = Math.floor(Math.min(...xs) / 10) * 10;
const xDataMax = Math.ceil(Math.max(...xs) / 10) * 10;
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
  ciLower.push(1 / (1 + Math.exp(-(eta - tCrit95 * se))));
  ciUpper.push(1 / (1 + Math.exp(-(eta + tCrit95 * se))));
}

const scatterSeries = classes.map((classLabel, idx) => {
  const rows = DATA.filter((r) => String(r[CLASS_LABEL_COL]) === classLabel);
  return {
    type: "scatter" as const,
    id: `class-${idx}`,
    data: rows.map((r, i) => ({
      x: Number(r[SCORE_COL]),
      y: Number(r[JITTER_Y_COL]),
      id: `${idx}-${i}`,
    })),
    label: classLabel,
    color: `${classColorMap[classLabel]}${POINT_ALPHA_HEX}`,
    markerSize: 7,
    xAxisId: "engagement",
    yAxisId: "probability",
  };
});

function LogisticOverlay() {
  const xScale = useXScale("engagement") as (v: number) => number | undefined;
  const yScale = useYScale("probability") as (v: number) => number | undefined;

  const toX = (v: number) => Number(xScale(v) ?? 0);
  const toY = (v: number) => Number(yScale(v) ?? 0);

  const upperPts = curveXs.map((x, i) => [toX(x), toY(ciUpper[i])]);
  const lowerPts = curveXs.map((x, i) => [toX(x), toY(ciLower[i])]);
  const bandPts = [...upperPts, ...lowerPts.slice().reverse()];
  const bandD =
    bandPts
      .map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)},${p[1].toFixed(1)}`)
      .join(" ") + " Z";

  const curveD = curveXs
    .map((x, i) => `${i === 0 ? "M" : "L"}${toX(x).toFixed(1)},${toY(curveY[i]).toFixed(1)}`)
    .join(" ");

  const markerX = toX(midpointX);
  const markerY = toY(DECISION_THRESHOLD);
  const labelX = markerX - 68;
  const labelY = toY(0.62);

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

const TITLE = "Customer Conversion · logistic-regression · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 64;

const LEGEND_ITEMS = [
  ...classes.map((c) => ({ type: "circle" as const, color: classColorMap[c], label: c })),
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
            label: SCORE_COL,
            tickNumber: 6,
            valueFormatter: (v: number | null) => `${v ?? ""}`,
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
            label: JITTER_Y_COL,
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
