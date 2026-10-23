// anyplot.ai
// calibration-curve: Calibration Curve
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 87/100 | Updated: 2026-10-23

import { LineChart } from "@mui/x-charts/LineChart";
import { BarChart } from "@mui/x-charts/BarChart";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const Y_TRUE = "Fraction of Positives"; // role: y_true
const Y_PROB = "Logistic regression (screening)"; // role: y_prob
const Y_PROB_B = "Boosted trees, uncalibrated"; // role: extra

// Data: replace this block with your own records, one object per row
// Predicted disease risk from a well-calibrated logistic-regression screening
// model and an overconfident, uncalibrated boosted-trees model against
// ground-truth binary diagnoses.
const data = (() => {
  function mulberry32(seed: number) {
    return function random() {
      seed = (seed + 0x6d2b79f5) | 0;
      let x = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
      return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
    };
  }

  function gaussian(random: () => number): number {
    const u = Math.max(random(), 1e-9);
    const v = random();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  const clamp01 = (v: number) => Math.min(1, Math.max(0, v));
  const logit = (p: number) => Math.log(p / (1 - p));
  const sigmoid = (z: number) => 1 / (1 + Math.exp(-z));

  const nSamples = 3000;
  const random = mulberry32(42);
  const overconfidenceScale = 2.4;

  const trueRisk = Array.from({ length: nSamples }, () => random());
  const yTrueArr = trueRisk.map((risk) => (random() < risk ? 1 : 0));
  const predAArr = trueRisk.map((risk) => clamp01(risk + 0.05 * gaussian(random)));
  const predBArr = trueRisk.map((risk) =>
    sigmoid(logit(clamp01(risk) * 0.998 + 0.001) * overconfidenceScale),
  );

  return yTrueArr.map((truth, i) => ({
    [Y_TRUE]: truth,
    [Y_PROB]: predAArr[i],
    [Y_PROB_B]: predBArr[i],
  }));
})();

// Plot: reads only data and the constants above
const NUM_BINS = 10;
const yTrue = data.map((d) => d[Y_TRUE]);

// Per model: bin counts, mean predicted probability and fraction of positives
// per bin, then ECE (bin-weighted |fraction − mean prediction|) and Brier score
const models = [Y_PROB, Y_PROB_B].map((col) => {
  const pred = data.map((d) => d[col]);
  const count = Array(NUM_BINS).fill(0);
  const sumPred = Array(NUM_BINS).fill(0);
  const sumTrue = Array(NUM_BINS).fill(0);
  pred.forEach((p, i) => {
    const idx = Math.min(NUM_BINS - 1, Math.floor(p * NUM_BINS));
    count[idx] += 1;
    sumPred[idx] += p;
    sumTrue[idx] += yTrue[i];
  });
  const points = count
    .map((n, b) => (n > 0 ? { x: sumPred[b] / n, y: sumTrue[b] / n, n } : null))
    .filter((pt) => pt !== null);
  const ece = points.reduce((acc, pt) => acc + (pt.n / pred.length) * Math.abs(pt.y - pt.x), 0);
  const brier = pred.reduce((acc, p, i) => acc + (p - yTrue[i]) ** 2, 0) / pred.length;
  return { label: col, count, points, ece, brier };
});

// Shared x axis: every model's own (mean prediction) x values plus the 0/1
// diagonal endpoints; each series is null away from its own points
const xValues = [...new Set([0, 1, ...models.flatMap((m) => m.points.map((pt) => pt.x))])].sort(
  (a, b) => a - b,
);
const modelSeries = models.map((m) => {
  const yAt = new Map(m.points.map((pt) => [pt.x, pt.y]));
  return xValues.map((x) => yAt.get(x) ?? null);
});
const diagonalSeries = xValues.map((x) => (x === 0 || x === 1 ? x : null));

const binLabels = Array.from(
  { length: NUM_BINS },
  (_, i) => `${Math.round((i / NUM_BINS) * 100)}–${Math.round(((i + 1) / NUM_BINS) * 100)}%`,
);

const TITLE_HEIGHT = 78;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartAreaHeight = height - TITLE_HEIGHT;
  const mainHeight = Math.round(chartAreaHeight * 0.62);
  const histHeight = chartAreaHeight - mainHeight;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        paddingTop: "16px",
      }}
    >
      <Typography
        sx={{
          color: t.ink,
          fontSize: 22,
          fontWeight: 500,
          textAlign: "center",
          lineHeight: 1.2,
        }}
      >
        calibration-curve · javascript · muix · anyplot.ai
      </Typography>
      <Typography
        sx={{
          color: t.inkSoft,
          fontSize: 14,
          textAlign: "center",
          lineHeight: 1.4,
          marginTop: "4px",
        }}
      >
        {models.map((m) => `${m.label} — ECE ${m.ece.toFixed(3)}, Brier ${m.brier.toFixed(3)}`).join("   ·   ")}
      </Typography>

      <LineChart
        width={width}
        height={mainHeight}
        skipAnimation
        disableHitArea
        colors={t.palette}
        xAxis={[
          {
            height: 60,
            data: xValues,
            scaleType: "linear",
            min: 0,
            max: 1,
            label: "Mean Predicted Probability",
            valueFormatter: (v: number) => `${Math.round(v * 100)}%`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            width: 84,
            min: 0,
            max: 1,
            label: Y_TRUE,
            valueFormatter: (v: number) => `${Math.round(v * 100)}%`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "diagonal",
            data: diagonalSeries,
            label: "Perfect calibration",
            color: t.ink,
            showMark: false,
            connectNulls: true,
            curve: "linear",
          },
          ...models.map((m, i) => ({
            id: `model${i}`,
            data: modelSeries[i],
            label: m.label,
            color: t.palette[i],
            showMark: true,
            connectNulls: true,
            curve: "linear" as const,
          })),
        ]}
        margin={{ left: 50, right: 40, top: 16, bottom: 16 }}
        sx={{
          "& .MuiChartsLegend-root": { color: t.ink },
          "& .MuiChartsLegend-label": { fontSize: "14px", color: t.ink },
          '& [data-series^="model"].MuiLineChart-line': { strokeWidth: 3 },
          '& [data-series="diagonal"].MuiLineChart-line': { strokeWidth: 2, strokeDasharray: "8 5" },
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <ChartsGrid horizontal />
      </LineChart>

      <BarChart
        width={width}
        height={histHeight}
        skipAnimation
        disableHitArea
        hideLegend
        borderRadius={2}
        xAxis={[
          {
            height: 56,
            scaleType: "band",
            data: binLabels,
            label: "Predicted Probability Bin",
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            width: 84,
            label: "Count",
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={models.map((m, i) => ({ data: m.count, label: m.label, color: t.palette[i] }))}
        margin={{ left: 50, right: 40, top: 8, bottom: 20 }}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      />
    </Box>
  );
}
