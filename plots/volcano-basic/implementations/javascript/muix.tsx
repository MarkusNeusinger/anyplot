// anyplot.ai
// volcano-basic: Volcano Plot for Statistical Significance
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-09
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// Constants
const P_CUTOFF = 0.05; // significance cutoff on the p-value
const FC_CUTOFF = 1; // effect-size cutoff on |log2 fold change|, a 2-fold change
const X_PAD = 0.12; // share of the largest |fold change| added on both sides
const Y_PAD = 0.08; // share of the largest -log10 p-value added above it
const Y_FLOOR_PAD = 0.02; // share of the axis height left below zero, so points at p = 1 clear the axis line
const X_TICKS = 10; // tick count hint for the fold-change axis
// Status colors follow the omics convention the spec names (Semantic exception
// in the style guide): up-regulated matte red, down-regulated blue, the rest a
// translucent neutral gray. Hex alpha suffixes give the points transparency.
const UP_COLOR = `${t.palette[4]}D9`;
const DOWN_COLOR = `${t.palette[2]}D9`;
const NS_COLOR = `${t.inkSoft}73`;
const TITLE = "volcano-basic · javascript · muix · anyplot.ai";
const TITLE_H = 72;
const LEGEND_H = 44;

// Columns: set these to your data's column names
const LOG2_FC = "log₂ fold change"; // role: log2_fold_change
const NEG_LOG10_P = "−log₁₀(p-value)"; // role: neg_log10_pvalue

// Data: replace this block with your own records, one object per row
// RNA-seq differential expression, treatment vs. control across 350 genes.
// Genes with a larger effect tend to carry stronger evidence (the volcano
// funnel), with enough noise that the thresholds still have to classify.
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (Math.imul(seed, 1103515245) + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  const gaussian = () => Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
  return Array.from({ length: 350 }, () => {
    const log2FoldChange = gaussian() * 1.4;
    const noise = gaussian() * 0.8;
    const negLog10P = Math.max(0.01, Math.abs(log2FoldChange) * 1.6 + noise + rand() * 0.6);
    return { [LOG2_FC]: Number(log2FoldChange.toFixed(3)), [NEG_LOG10_P]: Number(negLog10P.toFixed(3)) };
  });
})();

// Plot: reads only data and the constants above
const P_THRESHOLD = -Math.log10(P_CUTOFF);
const points = data
  .filter((d) => d[LOG2_FC] != null && d[NEG_LOG10_P] != null)
  .map((d, i) => ({ id: i, x: d[LOG2_FC], y: d[NEG_LOG10_P] }));
const upRegulated = points.filter((p) => p.y > P_THRESHOLD && p.x > FC_CUTOFF);
const downRegulated = points.filter((p) => p.y > P_THRESHOLD && p.x < -FC_CUTOFF);
const notSignificant = points.filter((p) => !(p.y > P_THRESHOLD && Math.abs(p.x) > FC_CUTOFF));

const xAbsMax = Math.max(...points.map((p) => Math.abs(p.x)), FC_CUTOFF);
const xLimit = xAbsMax * (1 + X_PAD);
const yLimit = Math.max(...points.map((p) => p.y), P_THRESHOLD) * (1 + Y_PAD);
const FOLD = 2 ** FC_CUTOFF;
const THRESHOLD_LINE = { stroke: t.inkSoft, strokeDasharray: "7 5", strokeWidth: 1.5 };
const THRESHOLD_LABEL = { fontSize: 15, fill: t.inkSoft };

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ScatterChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true, vertical: true }}
        margin={{ left: 24, right: 40, top: 16, bottom: 12 }}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: { fontSize: 16, color: t.ink },
          },
        }}
        xAxis={[
          {
            min: -xLimit,
            max: xLimit,
            tickNumber: X_TICKS,
            height: 72,
            label: LOG2_FC,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            min: -yLimit * Y_FLOOR_PAD,
            max: yLimit,
            width: 80,
            label: NEG_LOG10_P,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        series={[
          { id: "not-significant", label: "Not significant", data: notSignificant, markerSize: 6, color: NS_COLOR },
          { id: "down", label: "Down-regulated", data: downRegulated, markerSize: 8, color: DOWN_COLOR },
          { id: "up", label: "Up-regulated", data: upRegulated, markerSize: 8, color: UP_COLOR },
        ]}
        sx={{
          "& .MuiScatterChart-marker": { stroke: t.pageBg, strokeWidth: 0.5 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsReferenceLine y={P_THRESHOLD} label={`p = ${P_CUTOFF}`} labelAlign="end" labelStyle={THRESHOLD_LABEL} lineStyle={THRESHOLD_LINE} />
        <ChartsReferenceLine x={FC_CUTOFF} label={`FC = ${FOLD}`} labelAlign="start" labelStyle={THRESHOLD_LABEL} lineStyle={THRESHOLD_LINE} />
        <ChartsReferenceLine x={-FC_CUTOFF} label={`FC = −${FOLD}`} labelAlign="start" labelStyle={THRESHOLD_LABEL} lineStyle={THRESHOLD_LINE} />
      </ScatterChart>
    </div>
  );
}
