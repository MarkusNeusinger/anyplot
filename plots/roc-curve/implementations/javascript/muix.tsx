// anyplot.ai
// roc-curve: ROC Curve with AUC
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08
//# anyplot-orientation: square

import { LineChart } from "@mui/x-charts/LineChart";

const t = window.ANYPLOT_TOKENS;

// Constants
const UNIT_TICKS = Array.from({ length: 11 }, (_, i) => i / 10); // both rates live on 0–1
const AXIS_PAD = 0.02; // share of the 0–1 range kept free around the curves
const RANDOM_AUC = 0.5; // the area under the diagonal of a random classifier
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 44;
const X_AXIS_H = 64;
const Y_AXIS_W = 72;
const GAP = 24; // free space around the square drawing area, px

// Columns: set these to your data's column names
const MODEL = "Model"; // role: extra
const FPR = "False positive rate"; // role: fpr
const TPR = "True positive rate"; // role: tpr

// Data: replace this block with your own records, one object per row
// Biopsy classification, 500 malignant and 500 benign samples scored by two models; each row is one
// operating point of sklearn.metrics.roc_curve, threshold swept from the highest score down.
// Fixed-seed LCG with Box-Muller normals; the forest separates the classes by 2.3 SD, the
// logistic model by 1.15 SD.
const data = (() => {
  let s = 42 >>> 0;
  const rand = () => {
    s = (Math.imul(1664525, s) + 1013904223) >>> 0;
    return s / 4294967295;
  };
  const normal = (mean) => mean + Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
  return [
    ["Random Forest", 2.3],
    ["Logistic Regression", 1.15],
  ].flatMap(([model, shift]) => {
    const scored = [
      ...Array.from({ length: 500 }, () => ({ score: normal(shift), positive: true })),
      ...Array.from({ length: 500 }, () => ({ score: normal(0), positive: false })),
    ].sort((a, b) => b.score - a.score);
    let tp = 0;
    let fp = 0;
    return [
      { [MODEL]: model, [FPR]: 0, [TPR]: 0 },
      ...scored.map((d) => {
        if (d.positive) tp += 1;
        else fp += 1;
        return { [MODEL]: model, [FPR]: fp / 500, [TPR]: tp / 500 };
      }),
    ];
  });
})();

// Plot: reads only data and the constants above
// One curve per model, its operating points sorted by FPR, AUC by the trapezoidal rule
const models = [...new Set(data.map((d) => d[MODEL]))];
const curves = models.map((model) => {
  const points = data
    .filter((d) => d[MODEL] === model && Number.isFinite(d[FPR]) && Number.isFinite(d[TPR]))
    .sort((a, b) => a[FPR] - b[FPR] || a[TPR] - b[TPR]);
  const auc = points.slice(1).reduce((s, p, i) => s + ((p[FPR] - points[i][FPR]) * (p[TPR] + points[i][TPR])) / 2, 0);
  return { model, fpr: points.map((p) => p[FPR]), tpr: points.map((p) => p[TPR]), auc };
});
const pointsPerCurve = Math.max(...curves.map((c) => c.fpr.length));

const TITLE = "roc-curve · javascript · muix · anyplot.ai";
const SUBTITLE = `${models.length} classifiers · up to ${pointsPerCurve} operating points per curve · AUC by the trapezoidal rule`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartH = height - TITLE_H - SUBTITLE_H - LEGEND_H;
  const side = Math.min(width - Y_AXIS_W, chartH - X_AXIS_H) - 2 * GAP;
  const sideX = (width - Y_AXIS_W - side) / 2;
  const sideY = (chartH - X_AXIS_H - side) / 2;
  const unitAxis = {
    scaleType: "linear",
    min: -AXIS_PAD,
    max: 1 + AXIS_PAD,
    tickInterval: UNIT_TICKS,
    valueFormatter: (v) => v.toFixed(1),
  };

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
        height={chartH}
        skipAnimation
        margin={{ top: sideY, bottom: sideY, left: sideX, right: sideX }}
        grid={{ horizontal: true, vertical: true }}
        xAxis={[
          ...curves.map((c, i) => ({
            ...unitAxis,
            id: `fpr-${i}`,
            data: c.fpr,
            position: i === 0 ? "bottom" : "none",
            label: FPR,
            height: X_AXIS_H,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          })),
          { ...unitAxis, id: "diagonal", data: [0, 1], position: "none" },
        ]}
        yAxis={[
          {
            ...unitAxis,
            label: TPR,
            width: Y_AXIS_W,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        series={[
          ...curves.map((c, i) => ({
            id: `model-${i}`,
            xAxisId: `fpr-${i}`,
            data: c.tpr,
            label: `${c.model} (AUC = ${c.auc.toFixed(2)})`,
            color: t.palette[i],
            curve: "linear",
            showMark: false,
          })),
          {
            id: "diagonal",
            xAxisId: "diagonal",
            data: [0, 1],
            label: `Random classifier (AUC = ${RANDOM_AUC.toFixed(2)})`,
            color: t.inkSoft,
            curve: "linear",
            showMark: false,
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 15, color: t.ink },
          },
        }}
        sx={{
          '& .MuiLineChart-line[data-series^="model"]': { strokeWidth: 3 },
          '& .MuiLineChart-line[data-series="diagonal"]': { strokeWidth: 2, strokeDasharray: "10 6" },
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      />
    </div>
  );
}
