// anyplot.ai
// probability-weibull: Weibull Probability Plot for Reliability Analysis
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-24
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";

const t = window.ANYPLOT_TOKENS;
const THEME = window.ANYPLOT_THEME === "dark" ? "dark" : "light";
// ANYPLOT_TOKENS has no "muted" anchor — derive it from default-style-guide.md
// "Theme-adaptive Chrome" (tertiary text token).
const INK_MUTED = THEME === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data: fixed-seed LCG (the browser has no seeded RNG) -------------------
function makeLcg(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);

// Turbine blade fatigue-life test: cycles to failure, in thousands (kcycles).
const BETA_TRUE = 2.4;
const ETA_TRUE = 420;
const N = 24;
const CENSORED_EVERY = 6; // every 6th-ranked blade pulled for inspection, unfailed

const sortedTimes = Array.from({ length: N }, () => {
  const u = rand();
  return Math.round(ETA_TRUE * Math.pow(-Math.log(1 - u), 1 / BETA_TRUE) * 10) / 10;
}).sort((a, b) => a - b);

// Never censor the very first (smallest) time — a suspension needs at least
// one preceding failure to inherit a plotting position from.
const observations = sortedTimes.map((time, idx) => ({
  time,
  isCensored: idx > 0 && (idx + 1) % CENSORED_EVERY === 0,
}));

// Median-rank plotting positions via Johnson's rank-adjustment method: each
// failure's adjusted rank absorbs the "credit" left behind by suspensions
// that preceded it, then Benard's approximation turns rank into probability.
let adjustedRank = 0;
let lastProbability = 0;
const n = observations.length;
const points = observations.map((obs, idx) => {
  const reverseRank = n - idx;
  if (!obs.isCensored) {
    adjustedRank += (n + 1 - adjustedRank) / (1 + reverseRank);
    lastProbability = (adjustedRank - 0.3) / (n + 0.4);
  }
  return { ...obs, probability: lastProbability };
});

// y = ln(-ln(1-F)) linearizes the Weibull CDF so Weibull data plots straight.
const weibullY = (p: number) => Math.log(-Math.log(1 - p));

const failurePoints = points.filter((p) => !p.isCensored);
const censoredPoints = points.filter((p) => p.isCensored);

const failureData = failurePoints.map((p, i) => ({
  x: p.time,
  y: weibullY(p.probability),
  id: `failure-${i}`,
}));
const censoredData = censoredPoints.map((p, i) => ({
  x: p.time,
  y: weibullY(p.probability),
  id: `censored-${i}`,
}));

// Least-squares fit of ln(t) vs y over failures only: y = beta*ln(t) + b, so
// slope = shape parameter (beta) and eta = exp(-intercept / beta).
const xs = failurePoints.map((p) => Math.log(p.time));
const ys = failureData.map((d) => d.y);
const nF = xs.length;
const meanX = xs.reduce((a, b) => a + b, 0) / nF;
const meanY = ys.reduce((a, b) => a + b, 0) / nF;
let sxy = 0;
let sxx = 0;
for (let i = 0; i < nF; i += 1) {
  sxy += (xs[i] - meanX) * (ys[i] - meanY);
  sxx += (xs[i] - meanX) ** 2;
}
const beta = sxy / sxx;
const intercept = meanY - beta * meanX;
const eta = Math.exp(-intercept / beta);

const X_MIN = 80;
const X_MAX = 1000;
const fitLineX = [X_MIN, X_MAX];
const fitLineY = fitLineX.map((x) => beta * Math.log(x) + intercept);

const yAt632 = weibullY(0.632);

// Probability-paper y-axis: fixed percentage gridlines, deliberately NOT
// evenly spaced in y — that nonlinearity is the whole point of the transform.
const PROB_TICKS = [1, 2, 5, 10, 20, 30, 50, 63.2, 80, 90, 95, 99];
const yTickValues = PROB_TICKS.map((p) => weibullY(p / 100));
const yTickLabels = new Map(PROB_TICKS.map((p, i) => [yTickValues[i], `${p}%`]));
const Y_MIN = weibullY(0.01);
const Y_MAX = weibullY(0.99);

// Custom scatter marker: filled circle for observed failures, hollow ring for
// right-censored (suspended) units — same hue, status told by fill alone.
function StatusMarker({ series, xScale, yScale, color, markerSize }: any) {
  const isCensored = series.id === "censored";
  return (
    <g>
      {series.data.map((point: any) => (
        <circle
          key={point.id}
          cx={xScale(point.x)}
          cy={yScale(point.y)}
          r={markerSize}
          fill={isCensored ? "none" : color}
          stroke={color}
          strokeWidth={isCensored ? 2.5 : 0}
        />
      ))}
    </g>
  );
}

const TITLE = "probability-weibull · javascript · muix · anyplot.ai";
const TITLE_FONT_SIZE =
  TITLE.length > 67 ? Math.max(15, Math.round((22 * 67) / TITLE.length)) : 22;

// Chart margins — the y-axis label below is a hand-placed <text>, not the
// built-in `label` prop, because ChartsYAxis offsets it by a fixed
// `tickFontSize + tickSize + 10` regardless of the actual (custom-formatted)
// tick label width, which collided with "63.2%"-style ticks.
const MARGIN = { top: 96, right: 64, bottom: 84, left: 140 };

// --- Chart (default-exported component — the harness mounts it) -----------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const plotMidY = MARGIN.top + (height - MARGIN.top - MARGIN.bottom) / 2;

  return (
    <ChartContainer width={width} height={height} margin={MARGIN}
      series={[
        {
          type: "line",
          id: "fit",
          data: fitLineY,
          curve: "linear",
          color: t.ink,
          showMark: false,
          disableHighlight: true,
          label: `Fit: β≈${beta.toFixed(2)}, η≈${Math.round(eta)} kcycles`,
        },
        {
          type: "scatter",
          id: "failure",
          label: "Failure",
          data: failureData,
          markerSize: 9,
          color: t.palette[0],
        },
        {
          type: "scatter",
          id: "censored",
          label: "Suspended (censored)",
          data: censoredData,
          markerSize: 9,
          color: t.palette[0],
        },
      ]}
      xAxis={[
        {
          data: fitLineX,
          scaleType: "log",
          min: X_MIN,
          max: X_MAX,
          tickInterval: [100, 200, 300, 500, 700, 1000],
          valueFormatter: (v: number) => `${v}`,
          label: "Cycles to Failure (thousands)",
          tickLabelStyle: { fontSize: 14 },
          labelStyle: { fontSize: 16 },
        },
      ]}
      yAxis={[
        {
          scaleType: "linear",
          min: Y_MIN,
          max: Y_MAX,
          tickInterval: yTickValues,
          valueFormatter: (v: number) => yTickLabels.get(v) ?? "",
          tickLabelStyle: { fontSize: 14 },
        },
      ]}
      skipAnimation
    >
      <ChartsGrid horizontal vertical />
      <LinePlot
        skipAnimation
        slotProps={{ line: { strokeDasharray: "12 7", strokeWidth: 2.5 } }}
      />
      <ScatterPlot slots={{ scatter: StatusMarker }} />
      <ChartsXAxis />
      <ChartsYAxis />
      <ChartsReferenceLine
        y={yAt632}
        label={`63.2% · η ≈ ${Math.round(eta)} kcycles`}
        labelAlign="end"
        lineStyle={{ stroke: INK_MUTED, strokeDasharray: "4 4", strokeWidth: 1.5 }}
        labelStyle={{ fill: INK_MUTED, fontSize: 13 }}
      />
      <ChartsLegend
        direction="row"
        position={{ horizontal: "right", vertical: "top" }}
        itemMarkWidth={14}
        itemMarkHeight={14}
        labelStyle={{ fontSize: 13, fill: t.inkSoft }}
      />
      <text
        x={width / 2}
        y={44}
        textAnchor="middle"
        fontSize={TITLE_FONT_SIZE}
        fontWeight={600}
        fill={t.ink}
      >
        {TITLE}
      </text>
      <text
        x={0}
        y={0}
        textAnchor="middle"
        fontSize={16}
        fill={t.ink}
        transform={`translate(36, ${plotMidY}) rotate(-90)`}
      >
        Cumulative Failure Probability
      </text>
    </ChartContainer>
  );
}
