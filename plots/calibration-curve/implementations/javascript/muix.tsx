// anyplot.ai
// calibration-curve: Calibration Curve
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-02

import { LineChart } from "@mui/x-charts/LineChart";
import { BarChart } from "@mui/x-charts/BarChart";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const Y_TRUE = "Fraction of Positives"; // role: y_true
const Y_PROB = "Model A (well-calibrated)"; // role: y_prob
const Y_PROB_B = "Model B (overconfident)"; // role: extra

// Data: replace this block with your own records, one object per row
// Predicted probabilities for a well-calibrated screening model (Model A) and
// an overconfident model (Model B) against ground-truth binary diagnoses.
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
const N_SAMPLES = data.length;
const yTrue = data.map((d) => d[Y_TRUE]);
const predA = data.map((d) => d[Y_PROB]);
const predB = data.map((d) => d[Y_PROB_B]);

type Bin = { center: number; fracPos: number | null; count: number };

function calibrationBins(yProb: number[]): Bin[] {
  const sums = Array.from({ length: NUM_BINS }, () => ({ count: 0, sumTrue: 0 }));
  yProb.forEach((p, i) => {
    const idx = Math.min(NUM_BINS - 1, Math.floor(p * NUM_BINS));
    sums[idx].count += 1;
    sums[idx].sumTrue += yTrue[i];
  });
  return sums.map((b, i) => ({
    center: (i + 0.5) / NUM_BINS,
    fracPos: b.count > 0 ? b.sumTrue / b.count : null,
    count: b.count,
  }));
}

function brierScore(yProb: number[]): number {
  const sse = yProb.reduce((acc, p, i) => acc + (p - yTrue[i]) ** 2, 0);
  return sse / yProb.length;
}

function expectedCalibrationError(bins: Bin[], total: number): number {
  return bins.reduce((acc, b) => {
    if (b.fracPos === null) return acc;
    return acc + (b.count / total) * Math.abs(b.fracPos - b.center);
  }, 0);
}

const binsA = calibrationBins(predA);
const binsB = calibrationBins(predB);
const eceA = expectedCalibrationError(binsA, N_SAMPLES);
const eceB = expectedCalibrationError(binsB, N_SAMPLES);
const brierA = brierScore(predA);
const brierB = brierScore(predB);

const xValues = [0, ...binsA.map((b) => b.center), 1];
const modelASeries = [null, ...binsA.map((b) => b.fracPos), null];
const modelBSeries = [null, ...binsB.map((b) => b.fracPos), null];
const diagonalSeries = xValues;

const binLabels = binsA.map((b) => {
  const lo = Math.round((b.center - 0.05) * 100);
  const hi = Math.round((b.center + 0.05) * 100);
  return `${lo}–${hi}%`;
});

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
        {`Model A — ECE ${eceA.toFixed(3)}, Brier ${brierA.toFixed(3)}   ·   Model B — ECE ${eceB.toFixed(3)}, Brier ${brierB.toFixed(3)}`}
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
            curve: "linear",
          },
          {
            id: "modelA",
            data: modelASeries,
            label: Y_PROB,
            color: t.palette[0],
            showMark: true,
            curve: "linear",
          },
          {
            id: "modelB",
            data: modelBSeries,
            label: Y_PROB_B,
            color: t.palette[1],
            showMark: true,
            curve: "linear",
          },
        ]}
        margin={{ left: 50, right: 40, top: 16, bottom: 16 }}
        sx={{
          "& .MuiChartsLegend-root": { color: t.ink },
          "& .MuiChartsLegend-label": { fontSize: "14px", color: t.ink },
          '& [data-series="modelA"].MuiLineChart-line': { strokeWidth: 3 },
          '& [data-series="modelB"].MuiLineChart-line': { strokeWidth: 3 },
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
            tickLabelStyle: { fontSize: 12, fill: t.inkSoft },
            labelStyle: { fontSize: 14, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            width: 84,
            label: "Count",
            tickLabelStyle: { fontSize: 12, fill: t.inkSoft },
            labelStyle: { fontSize: 14, fill: t.ink },
          },
        ]}
        series={[
          { data: binsA.map((b) => b.count), label: Y_PROB, color: t.palette[0] },
          { data: binsB.map((b) => b.count), label: Y_PROB_B, color: t.palette[1] },
        ]}
        margin={{ left: 50, right: 40, top: 8, bottom: 20 }}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      />
    </Box>
  );
}
