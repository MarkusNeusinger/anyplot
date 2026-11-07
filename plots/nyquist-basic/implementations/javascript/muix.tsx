// anyplot.ai
// nyquist-basic: Nyquist Plot for Control Systems
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 86/100 | Created: 2026-06-17
//# anyplot-orientation: square
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const CRITICAL = { re: -1, im: 0 }; // the Nyquist critical point
const UNIT_CIRCLE_POINTS = 241;
const PAD_SHARE = 0.06; // padding around the drawn extent, share of the span
const ARROW_SHARES = [0.18, 0.42, 0.66]; // arrow positions as shares of the curve's arc length
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 40;
const AXIS_BAND = 64; // y-axis width and x-axis height, px
const MARGIN = { top: 16, right: 40, bottom: 40, left: 16 }; // left + band + right = top + band + bottom keeps the drawing area square

// Columns: set these to your data's column names
const FREQUENCY = "Angular frequency (rad/s)"; // role: frequency
const REAL = "Real"; // role: real
const IMAGINARY = "Imaginary"; // role: imaginary

// Data: replace this block with your own records, one object per row
// Open-loop G(s) = 1 / (s (1 + s)(1 + 0.5 s)) at 600 log-spaced frequencies from 0.4 to 25 rad/s
const data = Array.from({ length: 600 }, (_, k) => {
  const omega = 0.4 * Math.pow(25 / 0.4, k / 599);
  const denRe = -1.5 * omega * omega;
  const denIm = omega * (1 - 0.5 * omega * omega);
  const denSq = denRe * denRe + denIm * denIm;
  return { [FREQUENCY]: omega, [REAL]: denRe / denSq, [IMAGINARY]: -denIm / denSq };
});

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[FREQUENCY] - b[FREQUENCY]);
const re = rows.map((d) => d[REAL]);
const im = rows.map((d) => d[IMAGINARY]);
const unitMatch = FREQUENCY.match(/\(([^)]+)\)/);
const unit = unitMatch ? unitMatch[1] : "";

const circleAngles = Array.from({ length: UNIT_CIRCLE_POINTS }, (_, k) => (2 * Math.PI * k) / (UNIT_CIRCLE_POINTS - 1));

// Gain crossover: the row nearest |G| = 1 where the magnitude first crosses 1;
// phase crossover: the row nearest Im = 0 where the curve first crosses the negative real axis
let gainCrossover = -1;
let phaseCrossover = -1;
for (let i = 0; i < rows.length - 1; i++) {
  const m0 = Math.hypot(re[i], im[i]) - 1;
  const m1 = Math.hypot(re[i + 1], im[i + 1]) - 1;
  if (gainCrossover < 0 && m0 * m1 <= 0) gainCrossover = Math.abs(m0) <= Math.abs(m1) ? i : i + 1;
  if (phaseCrossover < 0 && im[i] * im[i + 1] <= 0 && re[i] < 0) {
    phaseCrossover = Math.abs(im[i]) <= Math.abs(im[i + 1]) ? i : i + 1;
  }
}
const crossovers = [
  gainCrossover >= 0 ? { kind: "gain crossover", i: gainCrossover, dx: 26, dy: -12 } : null,
  phaseCrossover >= 0 ? { kind: "phase crossover", i: phaseCrossover, dx: 14, dy: 28 } : null,
].filter(Boolean);
const phaseMargin = gainCrossover >= 0 ? 180 + (Math.atan2(im[gainCrossover], re[gainCrossover]) * 180) / Math.PI : null;
const gainMarginDb = phaseCrossover >= 0 ? -20 * Math.log10(Math.abs(re[phaseCrossover])) : null;

// Arrow positions along the arc length of the curve, in data units
const arcLength = [0];
for (let i = 1; i < rows.length; i++) arcLength.push(arcLength[i - 1] + Math.hypot(re[i] - re[i - 1], im[i] - im[i - 1]));
const arrowRows = ARROW_SHARES.map((share) => {
  const target = share * arcLength[arcLength.length - 1];
  const i = arcLength.findIndex((s) => s >= target);
  return Math.min(Math.max(i, 1), rows.length - 2);
});

// Square window: the curve, the unit circle and the critical point, padded, with one span on both axes
const reAll = [...re, -1, 1, CRITICAL.re];
const imAll = [...im, -1, 1, CRITICAL.im];
const reMin = Math.min(...reAll);
const reMax = Math.max(...reAll);
const imMin = Math.min(...imAll);
const imMax = Math.max(...imAll);
const span = Math.max(reMax - reMin, imMax - imMin) * (1 + 2 * PAD_SHARE);
const reMid = (reMin + reMax) / 2;
const imMid = (imMin + imMax) / 2;

const TITLE = "nyquist-basic · javascript · muix · anyplot.ai";
const SUBTITLE = [
  `${rows.length} frequencies from ${rows[0][FREQUENCY].toFixed(2)} to ${rows[rows.length - 1][FREQUENCY].toFixed(1)} ${unit}`,
  phaseMargin !== null ? `phase margin ${phaseMargin.toFixed(1)}°` : null,
  gainMarginDb !== null ? `gain margin ${gainMarginDb.toFixed(1)} dB` : null,
]
  .filter(Boolean)
  .join(" · ");

function CurveAnnotations() {
  const xScale = useXScale("re");
  const yScale = useYScale("im");
  return (
    <g>
      {arrowRows.map((i) => {
        const angle = (Math.atan2(yScale(im[i + 1]) - yScale(im[i - 1]), xScale(re[i + 1]) - xScale(re[i - 1])) * 180) / Math.PI;
        return (
          <path
            key={i}
            d="M 11 0 L -8 -8 L -8 8 Z"
            transform={`translate(${xScale(re[i])},${yScale(im[i])}) rotate(${angle})`}
            fill={t.palette[0]}
          />
        );
      })}
      {crossovers.map((c) => (
        <text
          key={c.kind}
          x={xScale(re[c.i]) + c.dx}
          y={yScale(im[c.i]) + c.dy}
          fontSize={15}
          fill={t.ink}
        >
          {c.kind} · ω = {rows[c.i][FREQUENCY].toFixed(2)} {unit}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const side = Math.min(width, height - TITLE_H - SUBTITLE_H - LEGEND_H);

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <ChartsDataProvider
        width={side}
        height={side}
        margin={MARGIN}
        skipAnimation
        series={[
          {
            type: "line",
            id: "response",
            label: "Open-loop response G(jω)",
            data: im,
            xAxisId: "re",
            yAxisId: "im",
            color: t.palette[0],
            curve: "linear",
            showMark: false,
          },
          {
            type: "line",
            id: "circle",
            label: "Unit circle",
            data: circleAngles.map((a) => Math.sin(a)),
            xAxisId: "circle",
            yAxisId: "im",
            color: t.inkSoft,
            curve: "linear",
            showMark: false,
          },
          {
            type: "scatter",
            id: "crossovers",
            label: "Crossover frequencies",
            data: crossovers.map((c) => ({ x: re[c.i], y: im[c.i], id: c.kind })),
            xAxisId: "re",
            yAxisId: "im",
            color: t.palette[1],
            markerSize: 7,
          },
          {
            type: "scatter",
            id: "critical",
            label: `Critical point (${CRITICAL.re}, ${CRITICAL.im})`,
            data: [{ x: CRITICAL.re, y: CRITICAL.im, id: "critical" }],
            xAxisId: "re",
            yAxisId: "im",
            color: t.palette[4],
            markerSize: 9,
          },
        ]}
        xAxis={[
          {
            id: "re",
            data: re,
            scaleType: "linear",
            min: reMid - span / 2,
            max: reMid + span / 2,
            label: REAL,
            height: AXIS_BAND,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
          {
            id: "circle",
            data: circleAngles.map((a) => Math.cos(a)),
            scaleType: "linear",
            min: reMid - span / 2,
            max: reMid + span / 2,
            position: "none",
          },
        ]}
        yAxis={[
          {
            id: "im",
            scaleType: "linear",
            min: imMid - span / 2,
            max: imMid + span / 2,
            label: IMAGINARY,
            width: AXIS_BAND,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "center" }} legendDirection="horizontal">
          <ChartsLegend sx={{ fontSize: 15, color: t.inkSoft, height: LEGEND_H, alignItems: "center" }} />
          <ChartsSurface
            sx={{
              "& .MuiLineChart-line[data-series='response']": { strokeWidth: 3 },
              "& .MuiLineChart-line[data-series='circle']": { strokeWidth: 1.5, strokeDasharray: "7 6" },
              "& .MuiChartsGrid-line": { stroke: t.grid },
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
            }}
          >
            <ChartsGrid vertical horizontal />
            <ChartsReferenceLine x={0} axisId="re" lineStyle={{ stroke: t.inkSoft, strokeOpacity: 0.6 }} />
            <ChartsReferenceLine y={0} axisId="im" lineStyle={{ stroke: t.inkSoft, strokeOpacity: 0.6 }} />
            <LinePlot skipAnimation />
            <CurveAnnotations />
            <ScatterPlot />
            <ChartsXAxis axisId="re" />
            <ChartsYAxis axisId="im" />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
