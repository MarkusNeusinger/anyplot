// anyplot.ai
// probability-weibull: Weibull Probability Plot for Reliability Analysis
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 85/100 | Updated: 2026-10-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "probability-weibull · javascript · muix · anyplot.ai";
const CHAR_LIFE_PCT = 63.2;
const PROB_TICKS = [0.1, 0.5, 1, 2, 5, 10, 20, 30, 50, 63.2, 80, 90, 95, 99, 99.9];
const LOG_TICK_MANTISSAS = [1, 1.5, 2, 3, 5, 7];
const DEFAULT_MIN_PROB_PCT = 1;
const DEFAULT_MAX_PROB_PCT = 99;
const Y_PAD_SHARE = 0.08;
const X_MIN_FACTOR = 0.72;
const X_MAX_FACTOR = 1.38;
const MARKER_RADIUS = 7;
const HEADER_HEIGHT = 76;
const PROB_AXIS_LABEL = "Cumulative Failure Probability (%)";
const FAILURE_LABEL = "Failure";
const CENSORED_LABEL = "Suspended (censored)";

// Columns: set these to your data's column names
const TIME = "Cycles to Failure (kcycles)"; // role: x
const IS_CENSORED = "Right Censored"; // role: group

// Data: replace this block with your own records
const BETA_TRUE = 2.4;
const ETA_TRUE = 420;
const SAMPLE_SIZE = 24;
const CENSORED_EVERY = 6;

const rawSamples: number[] = [];
let lcgState = 42 >>> 0;
for (let i = 0; i < SAMPLE_SIZE; i += 1) {
  lcgState = (Math.imul(lcgState, 1664525) + 1013904223) >>> 0;
  const u = lcgState / 4294967296;
  const sampleTime = Math.round(ETA_TRUE * Math.pow(-Math.log(1 - u), 1 / BETA_TRUE) * 10) / 10;
  rawSamples.push(sampleTime);
}
rawSamples.sort((a, b) => a - b);

const data: Array<Record<string, number | boolean>> = rawSamples.map((timeVal, idx) => ({
  [TIME]: timeVal,
  [IS_CENSORED]: idx > 0 && (idx + 1) % CENSORED_EVERY === 0,
}));

// Plot: reads only data and the constants above
const sortedObs = [...data].sort((a, b) => Number(a[TIME]) - Number(b[TIME]));
const totalN = sortedObs.length;
let adjustedRank = 0;
let lastProbability = 0;
const plottedPoints = sortedObs.map((row, idx) => {
  const time = Number(row[TIME]);
  const isCensored = Boolean(row[IS_CENSORED]);
  const reverseRank = totalN - idx;
  if (!isCensored) {
    adjustedRank += (totalN + 1 - adjustedRank) / (1 + reverseRank);
    lastProbability = (adjustedRank - 0.3) / (totalN + 0.4);
  }
  const weibullYVal = Math.log(-Math.log(1 - lastProbability));
  return {
    id: `obs-${idx}`,
    time,
    isCensored,
    probability: lastProbability,
    y: weibullYVal,
  };
});

const failurePoints = plottedPoints.filter((p) => !p.isCensored);
const censoredPoints = plottedPoints.filter((p) => p.isCensored);

const xs = failurePoints.map((p) => Math.log(p.time));
const ys = failurePoints.map((p) => p.y);
const nFailures = xs.length;
const meanX = xs.reduce((a, b) => a + b, 0) / nFailures;
const meanY = ys.reduce((a, b) => a + b, 0) / nFailures;
let sxy = 0;
let sxx = 0;
for (let i = 0; i < nFailures; i += 1) {
  sxy += (xs[i] - meanX) * (ys[i] - meanY);
  sxx += (xs[i] - meanX) ** 2;
}
const beta = sxy / sxx;
const intercept = meanY - beta * meanX;
const eta = Math.exp(-intercept / beta);

const minObsTime = Math.min(...plottedPoints.map((p) => p.time));
const maxObsTime = Math.max(...plottedPoints.map((p) => p.time));
const xMin = minObsTime * X_MIN_FACTOR;
const xMax = maxObsTime * X_MAX_FACTOR;
const xTickValues: number[] = [];
for (let decade = Math.floor(Math.log10(xMin)); decade <= Math.ceil(Math.log10(xMax)); decade += 1) {
  for (const m of LOG_TICK_MANTISSAS) {
    const tick = m * 10 ** decade;
    if (tick >= xMin && tick <= xMax) xTickValues.push(tick);
  }
}
const yAtCharLife =Math.log(-Math.log(1 - CHAR_LIFE_PCT / 100));

const minPlotY = Math.min(...plottedPoints.map((p) => p.y));
const maxPlotY = Math.max(...plottedPoints.map((p) => p.y));
const plotYSpan = maxPlotY - minPlotY;
const yMin = Math.min(
  minPlotY - plotYSpan * Y_PAD_SHARE,
  Math.log(-Math.log(1 - DEFAULT_MIN_PROB_PCT / 100)),
);
const yMax = Math.max(
  maxPlotY + plotYSpan * Y_PAD_SHARE,
  Math.log(-Math.log(1 - DEFAULT_MAX_PROB_PCT / 100)),
);

const activeProbTicks = PROB_TICKS.filter((p) => {
  const wy = Math.log(-Math.log(1 - p / 100));
  return wy >= yMin && wy <= yMax;
});
const yTickValues = activeProbTicks.map((p) => Math.log(-Math.log(1 - p / 100)));
const yTickLabels = new Map(activeProbTicks.map((p, i) => [yTickValues[i], `${p}%`]));

const fitXStart = Math.max(xMin, Math.exp((yMin - intercept) / beta));
const fitXEnd = Math.min(xMax, Math.exp((yMax - intercept) / beta));
const fitLineX = [fitXStart, fitXEnd];
const fitLineY = fitLineX.map((x) => beta * Math.log(x) + intercept);

const timeUnitMatch = /\(([^)]+)\)/.exec(TIME);
const timeUnit = timeUnitMatch ? timeUnitMatch[1] : "";
const unitSuffix = timeUnit ? ` ${timeUnit}` : "";
const fitLegendText = `Fit: β ≈ ${beta.toFixed(2)}, η ≈ ${Math.round(eta)}${unitSuffix}`;
const charLifeCalloutText = `${CHAR_LIFE_PCT}% · η ≈ ${Math.round(eta)}${unitSuffix}`;

function WeibullOverlay() {
  const { left, width: drawWidth } = useDrawingArea();
  const xScale = useXScale();
  const yScale = useYScale();

  const yPixelChar = Number(yScale(yAtCharLife));
  const paddingX = 10;
  const boxWidth = charLifeCalloutText.length * 7.6 + paddingX * 2;
  const boxHeight = 26;
  const boxX = left + drawWidth - boxWidth - 10;
  const boxY = yPixelChar - boxHeight - 8;

  return (
    <g>
      {failurePoints.map((pt) => (
        <circle
          key={pt.id}
          cx={xScale(pt.time)}
          cy={yScale(pt.y)}
          r={MARKER_RADIUS}
          fill={t.palette[0]}
          stroke={t.pageBg}
          strokeWidth={1.5}
        />
      ))}
      {censoredPoints.map((pt) => (
        <circle
          key={pt.id}
          cx={xScale(pt.time)}
          cy={yScale(pt.y)}
          r={MARKER_RADIUS}
          fill={t.pageBg}
          stroke={t.palette[0]}
          strokeWidth={2.5}
        />
      ))}
      <rect
        x={boxX}
        y={boxY}
        width={boxWidth}
        height={boxHeight}
        rx={4}
        fill={t.elevatedBg}
        stroke={t.inkSoft}
        strokeWidth={1}
      />
      <text
        x={boxX + boxWidth / 2}
        y={boxY + boxHeight / 2}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={14}
        fill={t.ink}
      >
        {charLifeCalloutText}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - HEADER_HEIGHT;

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          height: HEADER_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 48px 0 32px",
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <svg width="24" height="14" aria-hidden="true">
              <line
                x1="2"
                y1="7"
                x2="22"
                y2="7"
                stroke={t.ink}
                strokeWidth={2.5}
                strokeDasharray="6 3"
              />
            </svg>
            <span style={{ fontSize: 14, color: t.inkSoft, fontWeight: 500 }}>{fitLegendText}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <svg width="18" height="18" aria-hidden="true">
              <circle cx="9" cy="9" r="6.5" fill={t.palette[0]} />
            </svg>
            <span style={{ fontSize: 14, color: t.inkSoft, fontWeight: 500 }}>{FAILURE_LABEL}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <svg width="18" height="18" aria-hidden="true">
              <circle
                cx="9"
                cy="9"
                r="6.5"
                fill="none"
                stroke={t.palette[0]}
                strokeWidth={2.5}
              />
            </svg>
            <span style={{ fontSize: 14, color: t.inkSoft, fontWeight: 500 }}>
              {CENSORED_LABEL}
            </span>
          </div>
        </div>
      </div>
      <ChartsContainer
        width={width}
        height={chartHeight}
        margin={{ top: 14, right: 48, bottom: 18, left: 20 }}
        series={[
          {
            type: "line",
            id: "fit",
            data: fitLineY,
            curve: "linear",
            color: t.ink,
            showMark: false,
            disableHighlight: true,
          },
        ]}
        xAxis={[
          {
            data: fitLineX,
            scaleType: "log",
            min: xMin,
            max: xMax,
            height: 58,
            tickInterval: xTickValues,
            valueFormatter: (v: number) => `${Number(v.toPrecision(3))}`,
            label: TIME,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: yMin,
            max: yMax,
            width: 96,
            tickInterval: yTickValues,
            valueFormatter: (v: number) => yTickLabels.get(v) ?? "",
            label: PROB_AXIS_LABEL,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        skipAnimation
      >
        <ChartsGrid horizontal vertical />
        <LinePlot
          skipAnimation
          slotProps={{ line: { strokeDasharray: "12 7", strokeWidth: 2.5 } }}
        />
        <ChartsReferenceLine
          y={yAtCharLife}
          lineStyle={{
            stroke: t.inkSoft,
            strokeDasharray: "4 4",
            strokeWidth: 1.5,
          }}
        />
        <WeibullOverlay />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </div>
  );
}
