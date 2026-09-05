// anyplot.ai
// lift-curve: Model Lift Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-05
//# anyplot-orientation: landscape
// anyplot.ai
// lift-curve: Model Lift Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-05

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Deterministic LCG — the browser has no seeded RNG, and Math.random() isn't reproducible.
let seed = 42;
function nextRandom() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

// Simulated transaction population: fraud flag + model's predicted fraud score.
// Fraudulent cases skew toward higher scores, but with enough noise that the
// model isn't perfect — a realistic imperfect classifier.
const populationSize = 2000;
const fraudRate = 0.08;
const trueLabels = [];
const modelScores = [];
for (let i = 0; i < populationSize; i += 1) {
  const isFraud = nextRandom() < fraudRate ? 1 : 0;
  const signal = isFraud ? 0.75 : 0.3;
  const noise = (nextRandom() - 0.5) * 0.7;
  modelScores.push(Math.min(1, Math.max(0, signal + noise)));
  trueLabels.push(isFraud);
}

// Rank transactions by predicted score, descending — the order the model would target.
const ranked = trueLabels
  .map((label, i) => ({ label, score: modelScores[i] }))
  .sort((a, b) => b.score - a.score);

let running = 0;
const cumulativeFraud = ranked.map((r) => {
  running += r.label;
  return running;
});
const baselineRate = running / populationSize;

// Cumulative lift ratio at each 5% slice of the targeted population.
const percentages = Array.from({ length: 20 }, (_, i) => (i + 1) * 5);
const liftByPct = percentages.map((pct) => {
  const cutoff = Math.round((pct / 100) * populationSize);
  const targetedRate = cumulativeFraud[cutoff - 1] / cutoff;
  return targetedRate / baselineRate;
});

// --- Chart (default-exported component — the harness mounts it) ------------
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
        Fraud Detection Lift · lift-curve · javascript · muix · anyplot.ai
      </div>

      <LineChart
        width={window.ANYPLOT_SIZE.width}
        height={window.ANYPLOT_SIZE.height}
        skipAnimation
        series={[
          {
            data: liftByPct,
            label: "Model (ranked by predicted fraud score)",
            color: t.palette[0],
            curve: "monotoneX",
            showMark: true,
          },
        ]}
        xAxis={[
          {
            data: percentages,
            scaleType: "point",
            label: "Population targeted (%)",
            valueFormatter: (v) => `${v}%`,
          },
        ]}
        yAxis={[
          {
            label: "Cumulative lift",
            min: 0,
            valueFormatter: (v) => `${v.toFixed(1)}×`,
            // Widens the axis-label offset to clear the "×"-suffixed tick text
            // (MUI X reserves space from this prop, not from measured tick width).
            tickFontSize: 48,
          },
        ]}
        grid={{ horizontal: true }}
        sx={{
          "& .MuiChartsAxis-label": {
            fontSize: "16px !important",
          },
          "& .MuiChartsAxis-tickLabel": {
            fontSize: "14px !important",
          },
          "& .MuiLineElement-root": {
            strokeWidth: "3.5px",
          },
          "& .MuiMarkElement-root": {
            strokeWidth: "2px",
          },
        }}
        slotProps={{
          legend: { hidden: true },
        }}
        margin={{ top: 70, right: 60, bottom: 70, left: 100 }}
      >
        <ChartsReferenceLine
          y={1}
          label="Random targeting (no lift)"
          labelAlign="start"
          lineStyle={{
            stroke: t.ink,
            strokeDasharray: "6 4",
            strokeWidth: 2,
            strokeOpacity: 0.6,
          }}
          labelStyle={{
            fill: t.inkSoft,
            fontSize: 14,
          }}
        />
      </LineChart>
    </div>
  );
}
