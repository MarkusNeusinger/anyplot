// anyplot.ai
// line-loss-training: Training Loss Curve
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const EPOCH = "Epoch"; // role: epoch
const TRAIN_LOSS = "Training loss"; // role: train_loss
const VAL_LOSS = "Validation loss"; // role: val_loss

// Data: replace this block with your own records, one object per row
// Training and validation cross-entropy loss across 60 epochs; validation loss
// diverges upward past epoch ~28 (overfitting).
const data = (() => {
  function lcg(seed: number) {
    let state = seed;
    return () => {
      state = (state * 1664525 + 1013904223) % 4294967296;
      return state / 4294967296;
    };
  }
  const rand = lcg(42);
  const totalEpochs = 60;
  const epochs = Array.from({ length: totalEpochs }, (_, i) => i + 1);
  const trainArr = epochs.map(
    (e) => 2.35 * Math.exp(-e / 17) + 0.08 + (rand() - 0.5) * 0.02,
  );
  const valArr = epochs.map((e) => {
    const overfitPenalty = Math.max(0, e - 28) ** 2 * 0.00085;
    return 2.5 * Math.exp(-e / 15.5) + 0.12 + overfitPenalty + (rand() - 0.5) * 0.035;
  });

  return epochs.map((e, i) => ({
    [EPOCH]: e,
    [TRAIN_LOSS]: trainArr[i],
    [VAL_LOSS]: valArr[i],
  }));
})();

// Plot: reads only data and the constants above
const TRAIN_GRADIENT_ID = "lineLossTrainingTrainFill";
const VAL_GRADIENT_ID = "lineLossTrainingValFill";

const epoch = data.map((d) => d[EPOCH]);
const trainLoss = data.map((d) => d[TRAIN_LOSS]);
const valLoss = data.map((d) => d[VAL_LOSS]);
const lastEpoch = epoch[epoch.length - 1];

let bestEpoch = epoch[0];
let bestValLoss = valLoss[0];
valLoss.forEach((v, i) => {
  if (v < bestValLoss) {
    bestValLoss = v;
    bestEpoch = epoch[i];
  }
});

// Highlights the post-early-stop overfitting window (bestEpoch → lastEpoch)
function DivergenceZone() {
  const xScale = useXScale() as any;
  const drawingArea = useDrawingArea();
  if (!xScale) return null;
  const xStart = xScale(bestEpoch);
  const xEnd = xScale(lastEpoch);
  return (
    <rect
      x={xStart}
      y={drawingArea.top}
      width={Math.max(0, xEnd - xStart)}
      height={drawingArea.height}
      fill={t.amber}
      fillOpacity={0.08}
    />
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleHeight = 56;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "'Roboto', 'Helvetica', 'Arial', sans-serif",
      }}
    >
      <div
        style={{
          height: titleHeight,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          letterSpacing: "0.2px",
          color: t.ink,
        }}
      >
        line-loss-training · javascript · muix · anyplot.ai
      </div>

      <LineChart
        width={width}
        height={height - titleHeight}
        skipAnimation
        disableHitArea
        series={[
          {
            id: "train",
            data: trainLoss,
            label: TRAIN_LOSS,
            color: t.palette[0],
            showMark: false,
            curve: "monotoneX",
            area: true,
            baseline: 0,
          },
          {
            id: "val",
            data: valLoss,
            label: VAL_LOSS,
            color: t.palette[1],
            showMark: false,
            curve: "monotoneX",
            area: true,
            baseline: 0,
          },
        ]}
        xAxis={[
          {
            height: 64,
            data: epoch,
            scaleType: "linear",
            label: EPOCH,
            tickMinStep: 5,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fontWeight: 500, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            width: 78,
            label: "Cross-Entropy Loss",
            min: 0,
            valueFormatter: (v: number) => v.toFixed(1),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fontWeight: 500, fill: t.ink },
          },
        ]}
        grid={{ horizontal: true }}
        sx={{
          "& .MuiChartsLegend-root": { color: t.ink, pb: "12px" },
          "& .MuiChartsLegend-label": {
            fontSize: "15px !important",
            color: t.ink,
          },
          "& .MuiLineChart-line": {
            strokeWidth: "3px",
          },
          '& [data-series="train"].MuiLineChart-area': {
            fill: `url(#${TRAIN_GRADIENT_ID})`,
          },
          '& [data-series="val"].MuiLineChart-area': {
            fill: `url(#${VAL_GRADIENT_ID})`,
          },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
          },
        }}
        margin={{ top: 18, right: 40, bottom: 16, left: 40 }}
      >
        <defs>
          <linearGradient id={TRAIN_GRADIENT_ID} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={t.palette[0]} stopOpacity={0.22} />
            <stop offset="100%" stopColor={t.palette[0]} stopOpacity={0.02} />
          </linearGradient>
          <linearGradient id={VAL_GRADIENT_ID} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={t.palette[1]} stopOpacity={0.22} />
            <stop offset="100%" stopColor={t.palette[1]} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <DivergenceZone />
        <ChartsReferenceLine
          x={bestEpoch}
          label={`Early-stop point · epoch ${bestEpoch}`}
          labelAlign="start"
          lineStyle={{ stroke: t.ink, strokeDasharray: "6 6", strokeWidth: 1.5, strokeOpacity: 0.6 }}
          labelStyle={{ fill: t.inkSoft, fontSize: 13 }}
        />
      </LineChart>
    </div>
  );
}
