// anyplot.ai
// funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 91/100 | Created: 2026-06-10
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const Z_95 = 1.96; // two-sided 95 % normal quantile for the pseudo-confidence limits
const NULL_EFFECT = 0; // no effect on a log odds ratio scale
const X_PAD_SHARE = 0.05; // x padding as a share of the plotted span
const SE_PAD_SHARE = 0.08; // standard-error padding below the least precise study
const TITLE = "funnel-meta-analysis · javascript · muix · anyplot.ai";
const TITLE_H = 84;

// Columns: set these to your data's column names
const EFFECT = "Log odds ratio"; // role: effect_size
const STD_ERROR = "Standard error"; // role: std_error
const STUDY = "Study"; // role: study

// Data: replace this block with your own records, one object per row
// 18 randomized trials of antihypertensive therapy vs placebo on major cardiovascular events
// (negative log odds ratio = protective); the small trials lean to the protective side
const data = [
  { [STUDY]: "Halvorsen 2008", [EFFECT]: -0.42, [STD_ERROR]: 0.1 },
  { [STUDY]: "Okonkwo 2011", [EFFECT]: -0.29, [STD_ERROR]: 0.12 },
  { [STUDY]: "Brandt 2014", [EFFECT]: -0.38, [STD_ERROR]: 0.11 },
  { [STUDY]: "Varga 2006", [EFFECT]: -0.55, [STD_ERROR]: 0.22 },
  { [STUDY]: "Delacroix 2012", [EFFECT]: -0.18, [STD_ERROR]: 0.2 },
  { [STUDY]: "Sundqvist 2009", [EFFECT]: -0.47, [STD_ERROR]: 0.24 },
  { [STUDY]: "Moreau 2015", [EFFECT]: -0.33, [STD_ERROR]: 0.19 },
  { [STUDY]: "Ishikawa 2007", [EFFECT]: -0.61, [STD_ERROR]: 0.26 },
  { [STUDY]: "Castellano 2016", [EFFECT]: -0.12, [STD_ERROR]: 0.23 },
  { [STUDY]: "Novak 2004", [EFFECT]: -0.72, [STD_ERROR]: 0.38 },
  { [STUDY]: "Achterberg 2013", [EFFECT]: -0.25, [STD_ERROR]: 0.35 },
  { [STUDY]: "Petrakis 2005", [EFFECT]: -0.88, [STD_ERROR]: 0.42 },
  { [STUDY]: "Lindgren 2010", [EFFECT]: -0.5, [STD_ERROR]: 0.4 },
  { [STUDY]: "Ferreira 2003", [EFFECT]: -1.04, [STD_ERROR]: 0.46 },
  { [STUDY]: "Kowalczyk 2008", [EFFECT]: -0.65, [STD_ERROR]: 0.58 },
  { [STUDY]: "Abernathy 2002", [EFFECT]: -1.2, [STD_ERROR]: 0.62 },
  { [STUDY]: "Rahman 2017", [EFFECT]: -0.4, [STD_ERROR]: 0.55 },
  { [STUDY]: "Østergaard 2006", [EFFECT]: -0.8, [STD_ERROR]: 0.6 },
];

// Plot: reads only data and the constants above
const studies = data.filter((d) => Number.isFinite(d[EFFECT]) && Number.isFinite(d[STD_ERROR]) && d[STD_ERROR] > 0);

// Fixed-effect (inverse-variance) pooled estimate
const weights = studies.map((d) => 1 / d[STD_ERROR] ** 2);
const totalWeight = weights.reduce((a, b) => a + b, 0);
const pooled = studies.reduce((sum, d, i) => sum + d[EFFECT] * weights[i], 0) / totalWeight;

// The funnel opens to the padded bottom of the axis; the x extent holds the points, both limits and the null line
const seMax = Math.max(...studies.map((d) => d[STD_ERROR])) * (1 + SE_PAD_SHARE);
const xLow = Math.min(...studies.map((d) => d[EFFECT]), pooled - Z_95 * seMax, NULL_EFFECT);
const xHigh = Math.max(...studies.map((d) => d[EFFECT]), pooled + Z_95 * seMax, NULL_EFFECT);
const xPad = (xHigh - xLow) * X_PAD_SHARE;

const points = studies.map((d) => ({ id: d[STUDY], x: d[EFFECT], y: d[STD_ERROR] }));
const subtitle = `n = ${studies.length} studies · inverse-variance pooled effect ${pooled.toFixed(2)} · funnel: pooled ± ${Z_95} × SE (pseudo 95 % limits)`;

function FunnelLimits() {
  const xScale = useXScale() as unknown as (v: number) => number;
  const yScale = useYScale() as unknown as (v: number) => number;
  const apexX = xScale(pooled);
  const apexY = yScale(0);
  const baseY = yScale(seMax);
  const leftX = xScale(pooled - Z_95 * seMax);
  const rightX = xScale(pooled + Z_95 * seMax);
  return (
    <g>
      <polygon points={`${apexX},${apexY} ${leftX},${baseY} ${rightX},${baseY}`} fill={t.inkSoft} fillOpacity={0.07} />
      <line x1={apexX} y1={apexY} x2={leftX} y2={baseY} stroke={t.inkSoft} strokeWidth={2} strokeDasharray="10 6" />
      <line x1={apexX} y1={apexY} x2={rightX} y2={baseY} stroke={t.inkSoft} strokeWidth={2} strokeDasharray="10 6" />
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <Box sx={{ width, height, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, pt: "20px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, mt: "6px" }}>{subtitle}</Typography>
      </Box>
      <ChartsContainer
        width={width}
        height={height - TITLE_H}
        skipAnimation
        margin={{ top: 16, right: 56, bottom: 20, left: 24 }}
        series={[
          {
            type: "scatter",
            id: "studies",
            label: STUDY,
            data: points,
            color: t.palette[0],
            markerSize: 8,
            valueFormatter: (v) => `${v?.id}: ${EFFECT} ${v?.x}, ${STD_ERROR} ${v?.y}`,
          },
        ]}
        xAxis={[
          {
            scaleType: "linear",
            min: xLow - xPad,
            max: xHigh + xPad,
            label: EFFECT,
            height: 68,
            tickNumber: 10,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: 0,
            max: seMax,
            reverse: true,
            label: STD_ERROR,
            width: 84,
            tickNumber: 7,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid vertical horizontal />
        <FunnelLimits />
        {pooled !== NULL_EFFECT && (
          <ChartsReferenceLine
            x={NULL_EFFECT}
            label={`Null effect ${NULL_EFFECT}`}
            labelAlign="end"
            lineStyle={{ stroke: t.inkSoft, strokeWidth: 2, strokeDasharray: "8 6" }}
            labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
          />
        )}
        <ChartsReferenceLine
          x={pooled}
          label={`Pooled ${pooled.toFixed(2)}`}
          labelAlign="end"
          lineStyle={{ stroke: t.ink, strokeWidth: 2.5 }}
          labelStyle={{ fill: t.ink, fontSize: 14 }}
        />
        <ScatterPlot />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </Box>
  );
}
