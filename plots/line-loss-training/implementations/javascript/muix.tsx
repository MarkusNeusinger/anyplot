// anyplot.ai
// line-loss-training: Training Loss Curve
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-05

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG for reproducible noise) -------------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

const EPOCHS = 60;
const epoch = Array.from({ length: EPOCHS }, (_, i) => i + 1);

// Training loss keeps decaying smoothly for the full run.
const trainLoss = epoch.map(
  (e) => 2.35 * Math.exp(-e / 17) + 0.08 + (rand() - 0.5) * 0.02,
);

// Validation loss tracks training loss early on, then diverges upward past
// epoch ~28 — the classic overfitting signature this spec is about.
const valLoss = epoch.map((e) => {
  const overfitPenalty = Math.max(0, e - 28) ** 2 * 0.00085;
  return 2.5 * Math.exp(-e / 15.5) + 0.12 + overfitPenalty + (rand() - 0.5) * 0.035;
});

let bestEpoch = epoch[0];
let bestValLoss = valLoss[0];
valLoss.forEach((v, i) => {
  if (v < bestValLoss) {
    bestValLoss = v;
    bestEpoch = epoch[i];
  }
});

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      {/* Title rendered in the chart's top margin space */}
      <div
        style={{
          position: "absolute",
          top: 14,
          left: 0,
          right: 0,
          textAlign: "center",
          zIndex: 1,
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
          pointerEvents: "none",
          fontFamily: "'Roboto', 'Helvetica', 'Arial', sans-serif",
        }}
      >
        line-loss-training · javascript · muix · anyplot.ai
      </div>

      <LineChart
        width={window.ANYPLOT_SIZE.width}
        height={window.ANYPLOT_SIZE.height}
        skipAnimation
        series={[
          {
            data: trainLoss,
            label: "Training loss",
            color: t.palette[0],
            showMark: false,
            curve: "monotoneX",
          },
          {
            data: valLoss,
            label: "Validation loss",
            color: t.palette[1],
            showMark: false,
            curve: "monotoneX",
          },
        ]}
        xAxis={[
          {
            data: epoch,
            scaleType: "linear",
            label: "Epoch",
            tickMinStep: 5,
          },
        ]}
        yAxis={[{ label: "Cross-Entropy Loss" }]}
        grid={{ horizontal: true }}
        sx={{
          "& .MuiChartsAxis-label": {
            fontSize: "16px !important",
          },
          "& .MuiChartsAxis-tickLabel": {
            fontSize: "14px !important",
          },
          "& .MuiChartsLegend-label": {
            fontSize: "15px !important",
          },
          "& .MuiLineElement-root": {
            strokeWidth: "3px",
          },
        }}
        slotProps={{
          legend: {
            direction: "row",
            position: { vertical: "bottom", horizontal: "middle" },
          },
        }}
        margin={{ top: 70, right: 40, bottom: 90, left: 90 }}
      >
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
