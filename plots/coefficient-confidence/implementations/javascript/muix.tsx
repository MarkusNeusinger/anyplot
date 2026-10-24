// anyplot.ai
// coefficient-confidence: Coefficient Plot with Confidence Intervals
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 95/100 | Created: 2026-09-01

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

// Data
const VARIABLE = "Predictor Variable";
const COEFFICIENT = "Coefficient Estimate (Standardized β)";
const CI_LOWER = "95% CI Lower";
const CI_UPPER = "95% CI Upper";
const SUBTITLE = "Housing Price Multiple Linear Regression · Standardized β with 95% confidence intervals";

const RAW_DATA = [
  { [VARIABLE]: "Proximity to Highway", [COEFFICIENT]: -0.04, [CI_LOWER]: -0.19, [CI_UPPER]: 0.11 },
  { [VARIABLE]: "Number of Bedrooms", [COEFFICIENT]: -0.05, [CI_LOWER]: -0.21, [CI_UPPER]: 0.11 },
  { [VARIABLE]: "Garage Spaces", [COEFFICIENT]: 0.08, [CI_LOWER]: -0.09, [CI_UPPER]: 0.25 },
  { [VARIABLE]: "Lot Size", [COEFFICIENT]: 0.11, [CI_LOWER]: -0.06, [CI_UPPER]: 0.28 },
  { [VARIABLE]: "Renovated (Yes/No)", [COEFFICIENT]: 0.15, [CI_LOWER]: -0.02, [CI_UPPER]: 0.32 },
  { [VARIABLE]: "Number of Bathrooms", [COEFFICIENT]: 0.19, [CI_LOWER]: 0.05, [CI_UPPER]: 0.33 },
  { [VARIABLE]: "Age of Home", [COEFFICIENT]: -0.22, [CI_LOWER]: -0.35, [CI_UPPER]: -0.09 },
  { [VARIABLE]: "Crime Rate", [COEFFICIENT]: -0.29, [CI_LOWER]: -0.44, [CI_UPPER]: -0.14 },
  { [VARIABLE]: "Distance to City Center", [COEFFICIENT]: -0.34, [CI_LOWER]: -0.47, [CI_UPPER]: -0.21 },
  { [VARIABLE]: "School Rating", [COEFFICIENT]: 0.38, [CI_LOWER]: 0.24, [CI_UPPER]: 0.52 },
  { [VARIABLE]: "Square Footage", [COEFFICIENT]: 0.52, [CI_LOWER]: 0.41, [CI_UPPER]: 0.63 },
];

// Constants
const t = window.ANYPLOT_TOKENS;
const FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
const SIG_COLOR = t.palette[0];
const NON_SIG_COLOR = t.inkSoft;
const X_PAD_SHARE = 0.14;
const WHISKER_CAP = 9;

// Preparation
const COEFFICIENTS = [...RAW_DATA]
  .sort((a, b) => Math.abs(a[COEFFICIENT]) - Math.abs(b[COEFFICIENT]))
  .map((d, i) => ({
    i,
    variable: d[VARIABLE],
    coefficient: d[COEFFICIENT],
    ciLower: d[CI_LOWER],
    ciUpper: d[CI_UPPER],
    significant: d[CI_LOWER] > 0 || d[CI_UPPER] < 0,
  }));

const VARIABLES = COEFFICIENTS.map((d) => d.variable);
const N = COEFFICIENTS.length;

const rawMin = Math.min(0, ...COEFFICIENTS.map((d) => d.ciLower));
const rawMax = Math.max(0, ...COEFFICIENTS.map((d) => d.ciUpper));
const rawSpan = rawMax - rawMin || 1;
const xMin = Number((rawMin - rawSpan * X_PAD_SHARE).toFixed(2));
const xMax = Number((rawMax + rawSpan * X_PAD_SHARE).toFixed(2));

const significantPoints = COEFFICIENTS.filter((d) => d.significant).map((d) => ({
  id: d.i,
  x: d.coefficient,
  y: d.i,
}));
const notSignificantPoints = COEFFICIENTS.filter((d) => !d.significant).map((d) => ({
  id: d.i,
  x: d.coefficient,
  y: d.i,
}));

const LEGEND_ITEMS = [
  { label: "Significant (95% CI excludes 0)", color: SIG_COLOR },
  { label: "Not significant (95% CI includes 0)", color: NON_SIG_COLOR },
];

function ConfidenceWhiskers() {
  const xScale = useXScale("x");
  const yScale = useYScale("y");
  if (!xScale || !yScale) return null;

  return (
    <g>
      {COEFFICIENTS.map((d) => {
        const x1 = xScale(d.ciLower) ?? 0;
        const x2 = xScale(d.ciUpper) ?? 0;
        const y = yScale(d.i) ?? 0;
        const color = d.significant ? SIG_COLOR : NON_SIG_COLOR;
        return (
          <g key={d.variable}>
            <line
              x1={x1}
              y1={y}
              x2={x2}
              y2={y}
              stroke={color}
              strokeWidth={3}
              strokeLinecap="round"
            />
            <line
              x1={x1}
              y1={y - WHISKER_CAP}
              x2={x1}
              y2={y + WHISKER_CAP}
              stroke={color}
              strokeWidth={3}
              strokeLinecap="round"
            />
            <line
              x1={x2}
              y1={y - WHISKER_CAP}
              x2={x2}
              y2={y + WHISKER_CAP}
              stroke={color}
              strokeWidth={3}
              strokeLinecap="round"
            />
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const chartW = W - 48;
  const chartH = H - 150;

  return (
    <Box
      sx={{
        width: W,
        height: H,
        bgcolor: t.pageBg,
        color: t.ink,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        pt: "18px",
        px: "24px",
        boxSizing: "border-box",
      }}
    >
      <Typography
        sx={{
          fontSize: 22,
          fontWeight: 700,
          color: t.ink,
          fontFamily: FONT,
          textAlign: "center",
          lineHeight: 1.2,
        }}
      >
        coefficient-confidence · javascript · muix · anyplot.ai
      </Typography>
      <Typography
        sx={{
          fontSize: 15,
          color: t.inkSoft,
          fontFamily: FONT,
          textAlign: "center",
          mt: "4px",
          mb: "4px",
        }}
      >
        {SUBTITLE}
      </Typography>

      <ChartsContainer
        width={chartW}
        height={chartH}
        skipAnimation
        series={[
          {
            type: "scatter",
            id: "significant",
            label: LEGEND_ITEMS[0].label,
            data: significantPoints,
            color: SIG_COLOR,
            markerSize: 8,
            xAxisId: "x",
            yAxisId: "y",
          },
          {
            type: "scatter",
            id: "notSignificant",
            label: LEGEND_ITEMS[1].label,
            data: notSignificantPoints,
            color: NON_SIG_COLOR,
            markerSize: 8,
            xAxisId: "x",
            yAxisId: "y",
          },
        ]}
        xAxis={[
          {
            id: "x",
            min: xMin,
            max: xMax,
            height: 60,
            label: COEFFICIENT,
            labelStyle: { fontSize: 16, fill: t.ink, fontFamily: FONT },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          },
        ]}
        yAxis={[
          {
            id: "y",
            min: -0.5,
            max: N - 0.5,
            width: 230,
            tickMinStep: 1,
            disableLine: true,
            disableTicks: true,
            valueFormatter: (v) => VARIABLES[Math.round(v)] ?? "",
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft, fontFamily: FONT },
          },
        ]}
        margin={{ top: 28, bottom: 16, left: 20, right: 40 }}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeDasharray: "4 4" },
        }}
      >
        <ChartsGrid vertical />
        <ChartsReferenceLine
          x={0}
          axisId="x"
          label="No effect (β = 0)"
          labelAlign="start"
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 4", strokeWidth: 1.5 }}
          labelStyle={{ fontSize: 14, fill: t.inkSoft, fontStyle: "italic", fontFamily: FONT }}
        />
        <ConfidenceWhiskers />
        <ScatterPlot />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId="y" />
        <ChartsTooltip trigger="item" />
      </ChartsContainer>

      <Box
        sx={{
          display: "flex",
          gap: "28px",
          alignItems: "center",
          justifyContent: "center",
          mt: "4px",
        }}
      >
        {LEGEND_ITEMS.map((item) => (
          <Box key={item.label} sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <svg width={24} height={14}>
              <line x1={2} y1={7} x2={22} y2={7} stroke={item.color} strokeWidth={3} strokeLinecap="round" />
              <circle cx={12} cy={7} r={5.5} fill={item.color} />
            </svg>
            <Typography sx={{ fontSize: 14, color: t.ink, fontFamily: FONT }}>{item.label}</Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
