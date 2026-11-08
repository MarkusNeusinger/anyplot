// anyplot.ai
// line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 91/100 | Updated: 2026-11-08
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { ChartsAxisHighlight } from "@mui/x-charts/ChartsAxisHighlight";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { BarPlot } from "@mui/x-charts/BarChart";
import { LinePlot, MarkPlot } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const THRESHOLDS = [0.9, 0.95]; // the common component-selection thresholds
const ELBOW_MIN_GAP = 0.1; // an elbow counts as detectable when the normalised curve rises this far above its chord
const Y_DOMAIN_MAX = 1; // cumulative share of the total variance
const Y_HEAD_SHARE = 0.05; // headroom above 100 % so the last marker stays whole
const BAR_GAP = 0.45; // share of each component's band left empty around its bar

// Columns: set these to your data's column names
const COMPONENT = "Number of principal components"; // role: n_components
const RATIO = "Explained variance"; // role: explained_variance_ratio

// Data: replace this block with your own records, one object per row
// PCA on 16 standardised vibration, temperature and pressure sensors of a rotating pump:
// geometrically decaying eigenvalues, as is typical for correlated sensor arrays.
const data = (() => {
  const eigenvalues = [28, 17, 13, 9.5, 7, 5.5, 4.2, 3.2, 2.4, 1.9, 1.5, 1.2, 0.95, 0.75, 0.6, 0.5];
  const total = eigenvalues.reduce((s, v) => s + v, 0);
  return eigenvalues.map((v, i) => ({ [COMPONENT]: i + 1, [RATIO]: v / total }));
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[COMPONENT] - b[COMPONENT]);
const components = rows.map((d) => d[COMPONENT]);
const ratios = rows.map((d) => d[RATIO]);
const cumulative = ratios.map((_, i) => ratios.slice(0, i + 1).reduce((s, v) => s + v, 0));
const n = components.length;
const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

// First component count whose cumulative share reaches each threshold
const hits = THRESHOLDS.map((thr) => ({ thr, k: components[cumulative.findIndex((v) => v >= thr)] }));

// Elbow: the count where the normalised curve sits farthest above the chord from first to last point
const xNorm = components.map((c) => (c - components[0]) / (components[n - 1] - components[0]));
const yNorm = cumulative.map((v) => (v - cumulative[0]) / (cumulative[n - 1] - cumulative[0]));
const gaps = yNorm.map((v, i) => v - xNorm[i]);
const elbowIdx = gaps.indexOf(Math.max(...gaps));
const hasElbow = gaps[elbowIdx] >= ELBOW_MIN_GAP;

const TITLE = "line-pca-variance-cumulative · javascript · muix · anyplot.ai";
const SUBTITLE = `${n} components · largest single share ${pct(Math.max(...ratios))} · smallest ${pct(Math.min(...ratios))}`;
const HEADER_H = 80;
const LEGEND_H = 44;

// A ring and a label on the elbow's own marker
function ElbowMark() {
  const xScale = useXScale<"band">();
  const yScale = useYScale() as (v: number) => number;
  if (!hasElbow) return null;
  const x = (xScale(components[elbowIdx]) ?? 0) + xScale.bandwidth() / 2;
  const y = yScale(cumulative[elbowIdx]);
  return (
    <g>
      <circle cx={x} cy={y} r={14} fill="none" stroke={t.ink} strokeWidth={2} />
      <text x={x + 20} y={y + 34} fontSize={15} fontWeight={600} fill={t.ink}>
        Elbow at {components[elbowIdx]} components, {pct(cumulative[elbowIdx])}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "16px 40px 0 104px", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
      </div>
      <ChartsDataProvider
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        margin={{ top: 12, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            id: "components",
            data: components,
            scaleType: "band",
            categoryGapRatio: BAR_GAP,
            valueFormatter: (v: number) => `${v}`,
            label: COMPONENT,
            height: 64,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "share",
            min: 0,
            max: Y_DOMAIN_MAX * (1 + Y_HEAD_SHARE),
            tickNumber: 6,
            label: `${RATIO} (%)`,
            width: 76,
            valueFormatter: (v: number) => `${Math.round(v * 100)}%`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            type: "line",
            id: "cumulative",
            label: `Cumulative ${RATIO.toLowerCase()}`,
            data: cumulative,
            color: t.palette[0],
            curve: "monotoneX",
            showMark: true,
            shape: "circle",
            labelMarkType: "line+mark",
            valueFormatter: (v: number | null) => (v == null ? "" : pct(v)),
          },
          {
            type: "bar",
            id: "individual",
            label: `${RATIO} per component`,
            data: ratios,
            color: t.palette[1],
            labelMarkType: "square",
            valueFormatter: (v: number | null) => (v == null ? "" : pct(v)),
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "end" }} legendDirection="horizontal">
          <ChartsLegend
            sx={{
              fontSize: 16,
              color: t.ink,
              columnGap: 3,
              pr: 5,
              "& .MuiChartsLegend-mark": { width: 24, height: 24 },
              // Legend glyphs drawn like the series: the cumulative mark filled, the bars as translucent as the plot's
              '& .MuiChartsLegend-item[data-series="cumulative"] .MuiChartsLegend-mark path:last-of-type': { fill: t.palette[0] },
              '& .MuiChartsLegend-item[data-series="individual"] .MuiChartsLegend-mark': { opacity: 0.55 },
            }}
          />
          <ChartsSurface
            sx={{
              '& [data-series="individual"] .MuiBarChart-element': { fillOpacity: 0.55 },
              '& .MuiLineChart-line[data-series="cumulative"]': { strokeWidth: 3.5 },
              '& .MuiLineChart-mark[data-series="cumulative"]': { r: 6, fill: t.palette[0], stroke: t.pageBg, strokeWidth: 2 },
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
              "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
            }}
          >
            <ChartsGrid horizontal />
            {/* Bars first, so the per-component shares sit behind the cumulative curve */}
            <BarPlot borderRadius={3} skipAnimation />
            {hits.map(({ thr, k }) => (
              <ChartsReferenceLine
                key={thr}
                y={thr}
                label={k == null ? `${pct(thr)} not reached` : `${pct(thr)} reached at ${k} components`}
                labelAlign="start"
                spacing={{ x: 12, y: 6 }}
                lineStyle={{ stroke: t.inkSoft, strokeWidth: 1.75, strokeDasharray: "8 5" }}
                labelStyle={{ fontSize: 15, fill: t.ink }}
              />
            ))}
            <ChartsAxisHighlight x="band" />
            <LinePlot skipAnimation />
            <MarkPlot skipAnimation />
            <ElbowMark />
            <ChartsXAxis axisId="components" />
            <ChartsYAxis axisId="share" />
          </ChartsSurface>
          <ChartsTooltip trigger="axis" />
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
