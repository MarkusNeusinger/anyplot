// anyplot.ai
// line-impurity-comparison: Gini Impurity vs Entropy Comparison
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-08-26

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const GINI_LABEL = "Gini impurity: 2p(1 − p)";
const ENTROPY_LABEL = "Entropy: −p log₂p − (1 − p) log₂(1 − p)";
const IMPURITY_LABEL = "Impurity";
const Y_DOMAIN_MAX = 1; // both criteria share the axis 0 to 1
const Y_HEAD_SHARE = 0.08; // headroom above 1 so the entropy peak and its label stay inside

// Columns: set these to your data's column names
const P = "Probability of class 1 (p)"; // role: p

// Data: replace this block with your own records, one object per row
// 101 evenly spaced probabilities, so p = 0.5 is one of the samples.
const data = Array.from({ length: 101 }, (_, i) => ({ [P]: i / 100 }));

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[P] - b[P]);
const ps = rows.map((d) => d[P]);
const gini = ps.map((p) => 2 * p * (1 - p));
// 0 · log₂0 is undefined; its limit 0 closes the entropy curve at p = 0 and p = 1.
const entropy = ps.map((p) => (p > 0 && p < 1 ? -p * Math.log2(p) - (1 - p) * Math.log2(1 - p) : 0));

// Both curves fall strictly with |p − 0.5|, so the sample nearest 0.5 is the maximum of both.
const peakIdx = gini.indexOf(Math.max(...gini));
const peakP = ps[peakIdx];
const curves = [
  { id: "gini", label: GINI_LABEL, values: gini },
  { id: "entropy", label: ENTROPY_LABEL, values: entropy },
].map((c, i) => ({ ...c, color: t.palette[i], peak: c.values[peakIdx] }));
const step = (ps[ps.length - 1] - ps[0]) / (ps.length - 1);

const TITLE = "line-impurity-comparison · javascript · muix · anyplot.ai";
const SUBTITLE = `${ps.length} evaluation points, p = ${ps[0].toFixed(2)} to ${ps[ps.length - 1].toFixed(2)} in steps of ${step.toFixed(2)}`;
const HEADER_H = 80;
const LEGEND_H = 44;

// Value labels beside the two peak marks, placed in data coordinates
function PeakLabels() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  return (
    <g>
      {curves.map((c) => (
        <text key={c.id} x={xScale(peakP) + 16} y={yScale(c.peak) - 14} fontSize={15} fontWeight={600} fill={t.ink}>
          Maximum {c.peak.toFixed(2)}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "16px 40px 0 108px", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
      </div>
      <LineChart
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true }}
        margin={{ top: 12, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            data: ps,
            scaleType: "linear",
            min: ps[0],
            max: ps[ps.length - 1],
            tickNumber: 6,
            label: P,
            height: 64,
            valueFormatter: (v: number) => v.toFixed(2),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: Y_DOMAIN_MAX * (1 + Y_HEAD_SHARE),
            tickNumber: 6,
            label: IMPURITY_LABEL,
            width: 76,
            valueFormatter: (v: number) => v.toFixed(1),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={curves.map((c) => ({
          id: c.id,
          data: c.values,
          label: c.label,
          color: c.color,
          curve: "natural",
          area: true,
          shape: "circle",
          showMark: ({ index }: { index: number }) => index === peakIdx,
          valueFormatter: (v: number | null) => (v == null ? "" : v.toFixed(3)),
        }))}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: {
              fontSize: 16,
              color: t.ink,
              columnGap: 4,
              // The peak marks are filled with their series colour, so the legend glyphs are filled too
              ...Object.fromEntries(
                curves.map((c) => [`& .MuiChartsLegend-item[data-series="${c.id}"] .MuiChartsLegend-mark path:last-of-type`, { fill: c.color }]),
              ),
            },
          },
        }}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3.5 },
          // Gini's fill sits under entropy's: the lone entropy wash between the curves shows where they differ.
          '& .MuiLineChart-area[data-series="gini"]': { fillOpacity: 0.22 },
          '& .MuiLineChart-area[data-series="entropy"]': { fillOpacity: 0.16 },
          "& .MuiLineChart-mark": { r: 7, strokeWidth: 2.5, stroke: t.pageBg },
          ...Object.fromEntries(curves.map((c) => [`& .MuiLineChart-mark[data-series="${c.id}"]`, { fill: c.color }])),
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <ChartsReferenceLine
          x={peakP}
          label={`Maximum impurity at p = ${peakP.toFixed(2)}`}
          labelAlign="end"
          spacing={{ x: 12, y: 14 }}
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 4", strokeWidth: 1.5 }}
          labelStyle={{ fontSize: 15, fill: t.inkSoft }}
        />
        <PeakLabels />
      </LineChart>
    </div>
  );
}
