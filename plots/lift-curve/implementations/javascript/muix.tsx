// anyplot.ai
// lift-curve: Model Lift Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const SLICES = 20; // the curve is evaluated at every 1/20 of the ranked population (5 % steps)
const PERCENT_MAX = 100; // the targeted share runs from 0 to 100 %
const X_TICK_STEPS = 10; // one tick every tenth of the population
const NO_LIFT = 1; // a lift of 1 is random selection
const KEY_PERCENTS = [10, 25, 50]; // targeted shares whose lift is written beside the curve
const Y_HEADROOM_SHARE = 0.12; // room above the highest lift
const X_PAD_SHARE = 0.015; // room right of 100 % so the last mark stays inside the plot

// Columns: set these to your data's column names
const FRAUD = "Fraudulent transaction (1 = yes)"; // role: y_true
const SCORE = "Model fraud score"; // role: y_score

// Data: replace this block with your own records, one object per case
// 2,000 card transactions with a 3 % fraud rate; fraud cases score around 0.75 and
// legitimate ones around 0.30, with enough noise that the model is far from perfect.
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  return Array.from({ length: 2000 }, () => {
    const fraud = rand() < 0.03 ? 1 : 0;
    const score = Math.min(1, Math.max(0, (fraud ? 0.75 : 0.3) + (rand() - 0.5) * 0.7));
    return { [FRAUD]: fraud, [SCORE]: Number(score.toFixed(4)) };
  });
})();

// Plot: reads only data and the constants above
// Cases ranked by score, highest first: the order in which the model would target them
const ranked = data
  .filter((d) => d[FRAUD] != null && d[SCORE] != null)
  .sort((a, b) => b[SCORE] - a[SCORE]);
const n = ranked.length;
const cumulativePositives: number[] = [];
let running = 0;
for (const d of ranked) {
  running += d[FRAUD] === 1 ? 1 : 0;
  cumulativePositives.push(running);
}
const positives = running;
const baseRate = positives / n;

// Cumulative lift: the response rate among the top share of the ranking over the base rate
const percents = Array.from({ length: SLICES }, (_, i) => ((i + 1) * PERCENT_MAX) / SLICES);
const lift = percents.map((p) => {
  const cutoff = Math.max(1, Math.round((p / PERCENT_MAX) * n));
  return cumulativePositives[cutoff - 1] / cutoff / baseRate;
});
const liftMax = Math.max(...lift, NO_LIFT);
const keyPoints = KEY_PERCENTS.map((p) => percents.indexOf(p)).filter((i) => i >= 0);

const TITLE = "lift-curve · javascript · muix · anyplot.ai";
const SUBTITLE =
  `n = ${n.toLocaleString("en-US")} cases · ${positives} positive (base rate ${(baseRate * 100).toFixed(1)} %) · ` +
  `marks every ${PERCENT_MAX / SLICES} % of the ranked population`;
const HEADER_H = 84;

function KeyLiftLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {keyPoints.map((i) => (
        <text
          key={percents[i]}
          x={xScale(percents[i]) + 12}
          y={yScale(lift[i]) - 14}
          textAnchor="start"
          fontSize={15}
          fontWeight={600}
          fill={t.ink}
        >
          {`${lift[i].toFixed(2)}× at ${percents[i]} %`}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "14px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.6 }}>{SUBTITLE}</Typography>
      </Box>
      <LineChart
        width={width}
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        margin={{ top: 16, right: 48, bottom: 16, left: 20 }}
        series={[
          {
            id: "lift",
            data: lift,
            label: "Cumulative lift",
            color: t.palette[0],
            curve: "linear",
            showMark: true,
            shape: "circle",
            valueFormatter: (v) => `${v.toFixed(2)}×`,
          },
        ]}
        xAxis={[
          {
            data: percents,
            scaleType: "linear",
            min: 0,
            max: PERCENT_MAX * (1 + X_PAD_SHARE),
            tickInterval: Array.from({ length: X_TICK_STEPS + 1 }, (_, i) => (i * PERCENT_MAX) / X_TICK_STEPS),
            valueFormatter: (v: number) => `${v} %`,
            label: "Population targeted, ranked by score (%)",
            height: 64,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: liftMax * (1 + Y_HEADROOM_SHARE),
            width: 72,
            label: "Cumulative lift (model rate ÷ base rate)",
            valueFormatter: (v: number) => `${v.toFixed(1)}×`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3.5 },
          "& .MuiLineChart-mark": { strokeWidth: 2.5 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsReferenceLine
          y={NO_LIFT}
          label="Random selection (lift 1×)"
          labelAlign="start"
          spacing={{ x: 10, y: 10 }}
          labelStyle={{ fontSize: 15, fill: t.inkSoft }}
          lineStyle={{ stroke: t.inkSoft, strokeWidth: 2, strokeDasharray: "8 5" }}
        />
        <KeyLiftLabels />
      </LineChart>
    </Box>
  );
}
