// anyplot.ai
// calibration-beer-lambert: Beer-Lambert Calibration Curve
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 85/100 | Updated: 2026-10-23
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const THEME = window.ANYPLOT_THEME === "dark" ? "dark" : "light";
const INK_MUTED = THEME === "dark" ? "#A8A79F" : "#6B6A63";

// Constants
const PREDICTION_LEVEL = 95; // two-sided prediction interval, percent
const GRID_POINTS = 40;

// Columns: set these to your data's column names
const CONCENTRATION = "Concentration (mg/L)"; // role: concentration
const ABSORBANCE = "Absorbance"; // role: absorbance
const SAMPLE_TYPE = "Sample type"; // role: extra

// Data: replace this block with your own records, one object per row
const data = [
  { [CONCENTRATION]: 0, [ABSORBANCE]: 0.008, [SAMPLE_TYPE]: "Calibration standards" },
  { [CONCENTRATION]: 2, [ABSORBANCE]: 0.178, [SAMPLE_TYPE]: "Calibration standards" },
  { [CONCENTRATION]: 4, [ABSORBANCE]: 0.325, [SAMPLE_TYPE]: "Calibration standards" },
  { [CONCENTRATION]: 6, [ABSORBANCE]: 0.512, [SAMPLE_TYPE]: "Calibration standards" },
  { [CONCENTRATION]: 8, [ABSORBANCE]: 0.671, [SAMPLE_TYPE]: "Calibration standards" },
  { [CONCENTRATION]: 10, [ABSORBANCE]: 0.845, [SAMPLE_TYPE]: "Calibration standards" },
  { [CONCENTRATION]: 12, [ABSORBANCE]: 1.029, [SAMPLE_TYPE]: "Calibration standards" },
  { [CONCENTRATION]: null, [ABSORBANCE]: 0.6, [SAMPLE_TYPE]: "Unknown sample" },
];

// Plot: reads only data and the constants above
const standards = data.filter((d) => d[CONCENTRATION] !== null);
const unknownRow = data.find((d) => d[CONCENTRATION] === null) ?? standards[Math.floor(standards.length / 2)];
const standardsLabel = standards[0][SAMPLE_TYPE];
const unknownSampleLabel = unknownRow[SAMPLE_TYPE];
const concentration = standards.map((d) => d[CONCENTRATION]);
const absorbance = standards.map((d) => d[ABSORBANCE]);

const n = standards.length;
const xMean = concentration.reduce((a, b) => a + b, 0) / n;
const yMean = absorbance.reduce((a, b) => a + b, 0) / n;
let sxy = 0;
let sxx = 0;
for (let i = 0; i < n; i += 1) {
  sxy += (concentration[i] - xMean) * (absorbance[i] - yMean);
  sxx += (concentration[i] - xMean) ** 2;
}
const slope = sxy / sxx;
const intercept = yMean - slope * xMean;

let ssRes = 0;
let ssTot = 0;
for (let i = 0; i < n; i += 1) {
  const fitted = intercept + slope * concentration[i];
  ssRes += (absorbance[i] - fitted) ** 2;
  ssTot += (absorbance[i] - yMean) ** 2;
}
const rSquared = 1 - ssRes / ssTot;
const df = Math.max(1, n - 2);
const residualStdErr = Math.sqrt(ssRes / df);

// Two-tailed t critical values by interval level (percent): df 1..30, then the
// normal quantile. A level without a table fails loudly instead of mislabelling.
const T_CRIT: Record<number, { byDf: number[]; normal: number }> = {
  95: {
    byDf: [
      12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
      2.201, 2.179, 2.16, 2.145, 2.131, 2.12, 2.11, 2.101, 2.093, 2.086,
      2.08, 2.074, 2.069, 2.064, 2.06, 2.056, 2.052, 2.048, 2.045, 2.042,
    ],
    normal: 1.96,
  },
};
const tTable = T_CRIT[PREDICTION_LEVEL];
const tCrit = df <= tTable.byDf.length ? tTable.byDf[df - 1] : tTable.normal;

const xMin = Math.min(...concentration);
const xMax = Math.max(...concentration);
const xPad = (xMax - xMin) * 0.03;
const xDomainMin = xMin - xPad;
const xDomainMax = xMax + xPad;
const gridX = Array.from(
  { length: GRID_POINTS },
  (_, i) => xMin + ((xMax - xMin) * i) / (GRID_POINTS - 1),
);
const fittedY = gridX.map((x) => intercept + slope * x);
const halfWidth = gridX.map(
  (x) =>
    tCrit *
    residualStdErr *
    Math.sqrt(1 + 1 / n + (x - xMean) ** 2 / sxx),
);
const upperY = fittedY.map((y, i) => y + halfWidth[i]);
const lowerY = fittedY.map((y, i) => Math.max(0, y - halfWidth[i]));

const scatterData = standards.map((d, i) => ({
  x: d[CONCENTRATION],
  y: d[ABSORBANCE],
  id: `std-${i}`,
}));

const unknownAbsorbance = unknownRow[ABSORBANCE];
const unknownConcentration = (unknownAbsorbance - intercept) / slope;

const yAllValues = [...absorbance, ...upperY, unknownAbsorbance, 0];
const yPad = (Math.max(...yAllValues) - Math.min(...yAllValues)) * 0.08;
const yDomainMin = Math.min(...yAllValues) - yPad;
const yDomainMax = Math.max(...yAllValues) + yPad;

const unitMatch = CONCENTRATION.match(/\(([^)]+)\)/);
const unitSuffix = unitMatch ? ` ${unitMatch[1]}` : "";
const equationLabel = `y = ${slope.toFixed(4)}x + ${intercept.toFixed(4)}   ·   R² = ${rSquared.toFixed(4)}`;
const unknownLabel = `${unknownSampleLabel}: A =${unknownAbsorbance.toFixed(2)} → c ≈ ${unknownConcentration.toFixed(2)}${unitSuffix}`;

const title = "calibration-beer-lambert · javascript · muix · anyplot.ai";

function PredictionBand() {
  const xScale = useXScale();
  const yScale = useYScale();
  const top = gridX.map((x, i) => `${xScale(x)},${yScale(upperY[i])}`).join(" L ");
  const bottomIndices = [...gridX.keys()].reverse();
  const bottom = bottomIndices
    .map((i) => `${xScale(gridX[i])},${yScale(lowerY[i])}`)
    .join(" L ");
  return <path d={`M ${top} L ${bottom} Z`} fill={INK_MUTED} opacity={0.2} stroke="none" />;
}

function UnknownGuides() {
  const xScale = useXScale();
  const yScale = useYScale();
  const area = useDrawingArea();
  const px = xScale(unknownConcentration);
  const py = yScale(unknownAbsorbance);
  const style = { stroke: INK_MUTED, strokeWidth: 2, strokeDasharray: "8 6" };
  return (
    <g>
      <line x1={px} y1={py} x2={px} y2={area.top + area.height} style={style} />
      <line x1={area.left} y1={py} x2={px} y2={py} style={style} />
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const headerH = 104;
  const chartH = height - headerH;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: headerH,
          padding: "16px 64px 0 132px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            fontSize: 28,
            fontWeight: 600,
            color: t.ink,
            textAlign: "center",
            marginBottom: 8,
          }}
        >
          {title}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{equationLabel}</div>
        <div style={{ fontSize: 13, color: INK_MUTED, marginTop: 2 }}>
          Shaded band: {PREDICTION_LEVEL}% prediction interval · {unknownLabel}
        </div>
      </div>
      <ChartsDataProvider
        width={width}
        height={chartH - 40}
        margin={{ top: 16, right: 64, bottom: 24, left: 48 }}
        series={[
          {
            type: "scatter",
            id: "standards",
            label: standardsLabel,
            data: scatterData,
            markerSize: 13,
            color: t.palette[0],
          },
          {
            type: "scatter",
            id: "unknown",
            label: unknownSampleLabel,
            data: [{ x: unknownConcentration, y: unknownAbsorbance, id: "unknown" }],
            markerSize: 15,
            color: t.palette[1],
          },
          {
            type: "line",
            id: "fit",
            data: fittedY,
            curve: "linear",
            color: t.ink,
            showMark: false,
            disableHighlight: true,
          },
        ]}
        xAxis={[
          {
            data: gridX,
            scaleType: "linear",
            min: xDomainMin,
            max: xDomainMax,
            label: CONCENTRATION,
            height: 72,
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: yDomainMin,
            max: yDomainMax,
            label: ABSORBANCE,
            width: 84,
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        skipAnimation
      >
        <ChartsWrapper
          legendPosition={{ horizontal: "end", vertical: "top" }}
          legendDirection="horizontal"
        >
          <ChartsLegend sx={{ fontSize: 14, color: t.inkSoft, pr: 8 }} />
          <ChartsSurface sx={{ "& .MuiLineChart-line": { strokeWidth: 3 } }}>
            <ChartsGrid horizontal />
            <PredictionBand />
            <LinePlot skipAnimation />
            <UnknownGuides />
            <ChartsXAxis />
            <ChartsYAxis />
            <ScatterPlot />
            <text
              x={width - 64}
              y={chartH - 52}
              textAnchor="end"
              fontSize={12}
              fill={INK_MUTED}
            >
              n = {n} standards{concentration.includes(0) ? " (incl. blank)" : ""}
            </text>
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
