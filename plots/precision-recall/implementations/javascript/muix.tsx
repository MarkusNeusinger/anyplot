// anyplot.ai
// precision-recall: Precision-Recall Curve
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// Constants
const UNIT_TICKS = Array.from({ length: 11 }, (_, i) => i / 10); // recall and precision live on 0–1
const AXIS_PAD = 0.02; // share of the 0–1 range kept free around the curves
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 40;

// Columns: set these to your data's column names
const IS_FRAUD = "Fraud (1 = yes)"; // role: y_true
const SCORES = ["Gradient boosting", "Logistic regression"]; // role: y_scores

// Data: replace this block with your own records, one object per row
// 600 card transactions (a 6 % fraud draw that yields 24 positives, 4 %, in this sample) scored
// by two classifiers, predict_proba()-style outputs from a fixed-seed LCG with Box-Muller
// normals mapped through a sigmoid
let lcgState = 42 >>> 0;
const draws = Array.from({ length: 600 * 5 }, () => {
  lcgState = (Math.imul(lcgState, 1664525) + 1013904223) >>> 0;
  return lcgState / 4294967296;
});
const fraud = draws.slice(0, 600).map((u) => (u < 0.06 ? 1 : 0));
const normals = Array.from({ length: 1200 }, (_, k) => {
  const u1 = Math.max(draws[600 + 2 * k], 1e-9);
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * draws[601 + 2 * k]);
});
const data = fraud.map((label, i) => ({
  [IS_FRAUD]: label,
  [SCORES[0]]: Math.round((1 / (1 + Math.exp(-(label === 1 ? 2.1 + normals[i] : -1.3 + normals[i])))) * 1e4) / 1e4,
  [SCORES[1]]: Math.round((1 / (1 + Math.exp(-(label === 1 ? 0.9 + 1.3 * normals[600 + i] : -0.3 + 1.3 * normals[600 + i])))) * 1e4) / 1e4,
}));

// Plot: reads only data and the constants above
const labelled = data.filter((d) => d[IS_FRAUD] === 0 || d[IS_FRAUD] === 1);
const positives = labelled.filter((d) => d[IS_FRAUD] === 1).length;
const baseline = positives / labelled.length;

// One precision-recall curve per score column: thresholds at every distinct score, highest first
const curves = SCORES.map((model) => {
  const scored = labelled.filter((d) => Number.isFinite(d[model])).sort((a, b) => b[model] - a[model]);
  const modelPositives = scored.filter((d) => d[IS_FRAUD] === 1).length;
  const recall = [0];
  const precision = [1];
  let truePositives = 0;
  let falsePositives = 0;
  let i = 0;
  while (i < scored.length) {
    const score = scored[i][model];
    while (i < scored.length && scored[i][model] === score) {
      if (scored[i][IS_FRAUD] === 1) truePositives += 1;
      else falsePositives += 1;
      i += 1;
    }
    recall.push(truePositives / modelPositives);
    precision.push(truePositives / (truePositives + falsePositives));
  }
  // Average precision, AP = sum over thresholds of (R_n - R_(n-1)) * P_n
  let ap = 0;
  for (let k = 1; k < recall.length; k++) ap += (recall[k] - recall[k - 1]) * precision[k];
  return { model, recall, precision, ap };
});

const TITLE = "Fraud Detection · precision-recall · javascript · muix · anyplot.ai";
const SUBTITLE = `${labelled.length} transactions · ${positives} positives (${(baseline * 100).toFixed(1)} %) · step curves through every score threshold`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <LineChart
        width={width}
        height={height - TITLE_H - SUBTITLE_H - LEGEND_H}
        skipAnimation
        margin={{ top: 16, right: 48, bottom: 8, left: 16 }}
        grid={{ horizontal: true, vertical: true }}
        xAxis={curves.map((c, i) => ({
          id: `recall-${i}`,
          data: c.recall,
          scaleType: "linear",
          min: -AXIS_PAD,
          max: 1 + AXIS_PAD,
          tickInterval: UNIT_TICKS,
          valueFormatter: (v) => v.toFixed(1),
          position: i === 0 ? "bottom" : "none",
          label: "Recall",
          height: 64,
          labelStyle: { fontSize: 16, fill: t.ink },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        }))}
        yAxis={[
          {
            min: -AXIS_PAD,
            max: 1 + AXIS_PAD,
            tickInterval: UNIT_TICKS,
            valueFormatter: (v) => v.toFixed(1),
            label: "Precision",
            width: 72,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        series={curves.map((c, i) => ({
          id: `model-${i}`,
          xAxisId: `recall-${i}`,
          data: c.precision,
          label: `${c.model} (AP = ${c.ap.toFixed(2)})`,
          color: t.palette[i],
          curve: "stepBefore",
          showMark: false,
        }))}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 15, color: t.inkSoft },
          },
        }}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <ChartsReferenceLine
          y={baseline}
          label={`Random classifier: precision = positive rate ${baseline.toFixed(3)}`}
          labelAlign="start"
          spacing={{ x: 12, y: 10 }}
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "7 5", strokeWidth: 2 }}
          labelStyle={{ fontSize: 14, fill: t.inkSoft }}
        />
      </LineChart>
    </div>
  );
}
