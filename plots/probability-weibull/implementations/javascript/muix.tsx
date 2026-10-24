// anyplot.ai
// probability-weibull: Weibull Probability Plot for Reliability Analysis
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-08-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const TITLE = "probability-weibull · javascript · muix · anyplot.ai";

// Constants
const TIME_COL = "Cycles to Failure (kcycles)";
const IS_CENSORED_COL = "Right Censored";
const PROB_COL = "Cumulative Failure Probability (%)";

const BETA_TRUE = 2.4;
const ETA_TRUE = 420;
const SAMPLE_SIZE = 24;
const CENSORED_EVERY = 6;
const CHAR_LIFE_PCT = 63.2;
const PROB_TICKS = [1, 2, 5, 10, 20, 30, 50, 63.2, 80, 90, 95, 99];
const X_MIN_FACTOR = 0.72;
const X_MAX_FACTOR = 1.38;
const MARKER_RADIUS = 7;
const HEADER_HEIGHT = 76;

const FAILURE_LABEL = "Failure";
const CENSORED_LABEL = "Suspended (censored)";

// Data — deterministic turbine blade fatigue-life test (flat scalar records)
const rawSamples = [];
let lcgState = 42 >>> 0;
for (let i = 0; i < SAMPLE_SIZE; i += 1) {
  lcgState = (Math.imul(lcgState, 1664525) + 1013904223) >>> 0;
  const u = lcgState / 4294967296;
  const sampleTime = Math.round(ETA_TRUE * Math.pow(-Math.log(1 - u), 1 / BETA_TRUE) * 10) / 10;
  rawSamples.push(sampleTime);
}
rawSamples.sort((a, b) => a - b);

const DATA = rawSamples.map((timeVal, idx) => ({
  [TIME_COL]: timeVal,
  [IS_CENSORED_COL]: idx > 0 && (idx + 1) % CENSORED_EVERY === 0,
}));

// Sort observations by time and compute Johnson median-rank plotting positions
const sortedObs = [...DATA].sort((a, b) => Number(a[TIME_COL]) - Number(b[TIME_COL]));
const totalN = sortedObs.length;
let adjustedRank = 0;
let lastProbability = 0;
const plottedPoints = sortedObs.map((row, idx) => {
  const time = Number(row[TIME_COL]);
  const isCensored = Boolean(row[IS_CENSORED_COL]);
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

// Least-squares fit of ln(t) vs linearized Weibull y over observed failures
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

// Derive log x-axis bounds from data extent
const minObsTime = Math.min(...plottedPoints.map((p) => p.time));
const maxObsTime = Math.max(...plottedPoints.map((p) => p.time));
const xMin = Math.floor((minObsTime * X_MIN_FACTOR) / 10) * 10;
const xMax = Math.ceil((maxObsTime * X_MAX_FACTOR) / 50) * 50;
const yAtCharLife = Math.log(-Math.log(1 - CHAR_LIFE_PCT / 100));
const yTickValues = PROB_TICKS.map((p) => Math.log(-Math.log(1 - p / 100)));
const yTickLabels = new Map(PROB_TICKS.map((p, i) => [yTickValues[i], `${p}%`]));
const yMin = yTickValues[0];
const yMax = yTickValues[yTickValues.length - 1];

const fitXStart = Math.max(xMin, Math.exp((yMin - intercept) / beta));
const fitXEnd = Math.min(xMax, Math.exp((yMax - intercept) / beta));
const fitLineX = [fitXStart, fitXEnd];
const fitLineY = fitLineX.map((x) => beta * Math.log(x) + intercept);

const timeUnitMatch = TIME_COL.match(/\(([^)]+)\)/);
const timeUnit = timeUnitMatch ? timeUnitMatch[1] : "";
const fitLegendText = `Fit: β ≈ ${beta.toFixed(2)}, η ≈ ${Math.round(eta)} ${timeUnit}`;
const charLifeCalloutText = `${CHAR_LIFE_PCT}% · η ≈ ${Math.round(eta)} ${timeUnit}`;

function WeibullOverlay() {
  const { left, width: drawWidth } = useDrawingArea();
  const xScale = useXScale();
  const yScale = useYScale();
  if (!xScale || !yScale) return null;

  const yPixelChar = yScale(yAtCharLife);
  const paddingX = 10;
  const boxWidth = charLifeCalloutText.length * 7.6 + paddingX * 2;
  const boxHeight = 26;
  const boxX = left + drawWidth - boxWidth - 10;
  const boxY = yPixelChar - boxHeight - 8;

  return (
    <g>
      {/* Observed failures (filled circles) */}
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
      {/* Right-censored suspensions (hollow rings) */}
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
      {/* Characteristic life (63.2%) callout pill */}
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
            <span style={{ fontSize: 14, color: t.inkSoft, fontWeight: 500 }}>{CENSORED_LABEL}</span>
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
            valueFormatter: (v: number) => `${Math.round(v)}`,
            label: TIME_COL,
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
            label: PROB_COL,
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
