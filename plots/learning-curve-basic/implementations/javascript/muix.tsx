// anyplot.ai
// learning-curve-basic: Model Learning Curve
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 85/100 | Updated: 2026-10-23
import { LineChart } from "@mui/x-charts/LineChart";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// Constants
const METRIC = "Classification Accuracy (%)"; // the score both curves report, as a 0–1 fraction

// Columns: set these to your data's column names
const TRAIN_SIZE = "Training Set Size (labeled emails)"; // role: train_sizes
const TRAIN_MEAN = "Training score"; // role: train_scores (mean across folds)
const TRAIN_STD = "Training score std"; // role: train_scores (std across folds)
const VAL_MEAN = "Validation score"; // role: validation_scores (mean across folds)
const VAL_STD = "Validation score std"; // role: validation_scores (std across folds)

// Data: replace this block with your own records, one object per training size
// A spam-filter classifier evaluated at 10 training-set sizes via 8-fold
// cross-validation. Training accuracy drifts slightly downward as the fixed
// model has to fit more varied examples, while validation accuracy climbs and
// the two converge — but don't fully close — as more labeled email tightens
// the ±1 std-dev spread across folds.
const data = [
  { [TRAIN_SIZE]: 200, [TRAIN_MEAN]: 0.985, [TRAIN_STD]: 0.012, [VAL_MEAN]: 0.76, [VAL_STD]: 0.055 },
  { [TRAIN_SIZE]: 400, [TRAIN_MEAN]: 0.978, [TRAIN_STD]: 0.01, [VAL_MEAN]: 0.82, [VAL_STD]: 0.045 },
  { [TRAIN_SIZE]: 800, [TRAIN_MEAN]: 0.968, [TRAIN_STD]: 0.009, [VAL_MEAN]: 0.868, [VAL_STD]: 0.035 },
  { [TRAIN_SIZE]: 1200, [TRAIN_MEAN]: 0.96, [TRAIN_STD]: 0.008, [VAL_MEAN]: 0.892, [VAL_STD]: 0.028 },
  { [TRAIN_SIZE]: 1600, [TRAIN_MEAN]: 0.955, [TRAIN_STD]: 0.007, [VAL_MEAN]: 0.905, [VAL_STD]: 0.023 },
  { [TRAIN_SIZE]: 2000, [TRAIN_MEAN]: 0.951, [TRAIN_STD]: 0.006, [VAL_MEAN]: 0.913, [VAL_STD]: 0.02 },
  { [TRAIN_SIZE]: 2400, [TRAIN_MEAN]: 0.948, [TRAIN_STD]: 0.006, [VAL_MEAN]: 0.919, [VAL_STD]: 0.017 },
  { [TRAIN_SIZE]: 2800, [TRAIN_MEAN]: 0.946, [TRAIN_STD]: 0.005, [VAL_MEAN]: 0.923, [VAL_STD]: 0.015 },
  { [TRAIN_SIZE]: 3200, [TRAIN_MEAN]: 0.944, [TRAIN_STD]: 0.005, [VAL_MEAN]: 0.926, [VAL_STD]: 0.014 },
  { [TRAIN_SIZE]: 3600, [TRAIN_MEAN]: 0.943, [TRAIN_STD]: 0.004, [VAL_MEAN]: 0.928, [VAL_STD]: 0.013 },
];

// Plot: reads only data and the constants above
const sizes = data.map((d) => d[TRAIN_SIZE]);
const trainMean = data.map((d) => d[TRAIN_MEAN]);
const valMean = data.map((d) => d[VAL_MEAN]);

// ±1 std-dev confidence band via the stacked-area trick: a fully transparent
// "lower" series carries the band's floor, and a "width" series (2×std)
// stacked on top of it fills exactly the [mean-std, mean+std] interval.
const trainLower = data.map((d) => d[TRAIN_MEAN] - d[TRAIN_STD]);
const trainWidth = data.map((d) => 2 * d[TRAIN_STD]);
const valLower = data.map((d) => d[VAL_MEAN] - d[VAL_STD]);
const valWidth = data.map((d) => 2 * d[VAL_STD]);

// y limits: the bands' extent, padded, capped at a perfect score
const bandLow = Math.min(...trainLower, ...valLower);
const bandHigh = Math.max(...data.map((d) => Math.max(d[TRAIN_MEAN] + d[TRAIN_STD], d[VAL_MEAN] + d[VAL_STD])));
const pad = (bandHigh - bandLow) * 0.08;
const yMin = Math.max(0, bandLow - pad);
const yMax = Math.min(1, bandHigh + pad);

const TITLE = "learning-curve-basic · javascript · muix · anyplot.ai";
const pct = (v) => `${(v * 100).toFixed(1)}%`;

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const titleH = 64;
  const legendH = 40;
  const chartH = size.height - titleH - legendH;

  return (
    <Box
      sx={{
        width: size.width,
        height: size.height,
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box sx={{ height: titleH, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600 }}>{TITLE}</Typography>
      </Box>
      <LineChart
        width={size.width}
        height={chartH}
        skipAnimation
        margin={{ top: 20, right: 40, bottom: 8, left: 24 }}
        series={[
          { id: "trainLower", data: trainLower, stack: "trainBand", area: true, curve: "linear", color: t.palette[0] },
          { id: "trainBand", data: trainWidth, stack: "trainBand", area: true, curve: "linear", color: t.palette[0] },
          {
            id: "trainMean",
            data: trainMean,
            label: TRAIN_MEAN,
            color: t.palette[0],
            showMark: true,
            shape: "circle",
            curve: "linear",
            valueFormatter: pct,
          },
          { id: "valLower", data: valLower, stack: "valBand", area: true, curve: "linear", color: t.palette[1] },
          { id: "valBand", data: valWidth, stack: "valBand", area: true, curve: "linear", color: t.palette[1] },
          {
            id: "valMean",
            data: valMean,
            label: VAL_MEAN,
            color: t.palette[1],
            showMark: true,
            shape: "circle",
            curve: "linear",
            valueFormatter: pct,
          },
        ]}
        xAxis={[
          {
            data: sizes,
            scaleType: "linear",
            label: TRAIN_SIZE,
            height: 64,
            tickNumber: 10,
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        yAxis={[
          {
            min: yMin,
            max: yMax,
            label: METRIC,
            valueFormatter: (v) => `${Math.round(v * 100)}%`,
            width: 84,
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        grid={{ horizontal: true }}
        slotProps={{
          legend: {
            position: { vertical: "bottom", horizontal: "center" },
            direction: "horizontal",
            sx: { fontSize: 16 },
          },
        }}
        sx={{
          '& .MuiLineChart-line[data-series="trainMean"], & .MuiLineChart-line[data-series="valMean"]': {
            strokeWidth: 3,
          },
          '& .MuiLineChart-line[data-series="trainLower"], & .MuiLineChart-line[data-series="valLower"]': {
            stroke: "none",
          },
          '& .MuiLineChart-line[data-series="trainBand"]': { stroke: t.palette[0], strokeWidth: 1, strokeOpacity: 0.5 },
          '& .MuiLineChart-line[data-series="valBand"]': { stroke: t.palette[1], strokeWidth: 1, strokeOpacity: 0.5 },
          '& .MuiLineChart-area[data-series="trainLower"], & .MuiLineChart-area[data-series="valLower"]': {
            fillOpacity: 0,
          },
          '& .MuiLineChart-area[data-series="trainBand"], & .MuiLineChart-area[data-series="valBand"]': {
            fillOpacity: 0.18,
          },
          '& .MuiLineChart-mark[data-series="trainMean"]': { r: 7, fill: t.palette[0], stroke: t.pageBg, strokeWidth: 2 },
          '& .MuiLineChart-mark[data-series="valMean"]': { r: 7, fill: t.palette[1], stroke: t.pageBg, strokeWidth: 2 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      />
    </Box>
  );
}
