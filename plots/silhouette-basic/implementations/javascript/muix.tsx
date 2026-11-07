// anyplot.ai
// silhouette-basic: Silhouette Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-09
//# anyplot-orientation: square

import { BarChart } from "@mui/x-charts/BarChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useDrawingArea, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SCORE_MAX = 1; // upper bound of the silhouette coefficient
const X_PAD_SHARE = 0.04; // padding below the lowest score, as a share of the axis span
const ANNOTATION_W = 180; // px band right of the bars for the cluster averages

// Columns: set these to your data's column names
const CLUSTER = "Customer segment"; // role: cluster_labels
const SILHOUETTE = "Silhouette coefficient"; // role: silhouette_values

// Data: replace this block with your own records, one object per row
// Silhouette coefficient per customer of a k-means segmentation on RFM features (k = 4).
const segments: [string, number, number, number][] = [
  // name, mean score, spread, customers
  ["Champions", 0.6, 0.16, 22],
  ["Loyal", 0.35, 0.22, 20],
  ["At-Risk", 0.12, 0.22, 19],
  ["Lost", -0.05, 0.24, 19],
];
let seed = 42;
const data: Record<string, number | string>[] = [];
for (const [name, mean, spread, count] of segments) {
  for (let i = 0; i < count; i += 1) {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    const u1 = Math.max(seed / 4294967296, 1e-9);
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    const u2 = seed / 4294967296;
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    data.push({ [CLUSTER]: name, [SILHOUETTE]: Number(Math.max(-0.6, Math.min(0.95, mean + z * spread)).toFixed(3)) });
  }
}

// Plot: reads only data and the constants above
const clusters = [...new Set(data.map((d) => String(d[CLUSTER])))];
const blocks = clusters.map((cluster) => {
  const scores = data
    .filter((d) => d[CLUSTER] === cluster)
    .map((d) => Number(d[SILHOUETTE]))
    .sort((a, b) => b - a);
  return { cluster, scores, avg: scores.reduce((s, v) => s + v, 0) / scores.length };
});

// One band per sample, cluster after cluster; each cluster is one series, null elsewhere
const categories = blocks.flatMap((b, bi) => b.scores.map((_, i) => `${bi}-${i}`));
let cursor = 0;
const series = blocks.map((b, bi) => {
  const values: (number | null)[] = categories.map(() => null);
  b.scores.forEach((v, i) => {
    values[cursor + i] = v;
  });
  cursor += b.scores.length;
  return { id: `cluster-${bi}`, label: b.cluster, data: values, color: t.palette[bi], stack: "silhouette" };
});
const midCategory = blocks.map((b, bi) => `${bi}-${Math.floor((b.scores.length - 1) / 2)}`);

const allScores = blocks.flatMap((b) => b.scores);
const overallAvg = allScores.reduce((s, v) => s + v, 0) / allScores.length;
const xLow = Math.min(0, ...allScores);
const xMin = xLow - (SCORE_MAX - xLow) * X_PAD_SHARE;

const title = "silhouette-basic · javascript · muix · anyplot.ai";
const subtitle = `${allScores.length} samples in ${clusters.length} clusters · bars sorted within each cluster`;
const HEADER_H = 84;

function ClusterAverages() {
  const yScale = useYScale() as ((v: string) => number) & { bandwidth: () => number };
  const { left, width } = useDrawingArea();
  const x = left + width + 16;
  return (
    <g>
      {blocks.map((b, bi) => {
        const y = yScale(midCategory[bi]) + yScale.bandwidth() / 2;
        return (
          <g key={b.cluster}>
            <rect x={x} y={y - 22} width={12} height={12} fill={t.palette[bi]} />
            <text x={x + 20} y={y - 16} dominantBaseline="central" fontSize={16} fontWeight={600} fill={t.ink}>
              {b.cluster}
            </text>
            <text x={x + 20} y={y + 6} dominantBaseline="central" fontSize={15} fill={t.inkSoft}>
              {`avg ${b.avg.toFixed(2)}`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{title}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <BarChart
        width={width}
        height={height - HEADER_H}
        layout="horizontal"
        skipAnimation
        borderRadius={0}
        margin={{ top: 16, right: ANNOTATION_W, bottom: 8, left: 16 }}
        series={series}
        yAxis={[
          {
            scaleType: "band",
            data: categories,
            categoryGapRatio: 0.04,
            label: "Samples, sorted within each cluster",
            width: 40,
            disableTicks: true,
            disableLine: true,
            tickLabelInterval: () => false,
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        xAxis={[
          {
            min: xMin,
            max: SCORE_MAX,
            label: SILHOUETTE,
            height: 64,
            valueFormatter: (v: number) => v.toFixed(1),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
            sx: { "& .MuiChartsAxis-line, & .MuiChartsAxis-tick": { stroke: t.inkSoft } },
          },
        ]}
        grid={{ vertical: true }}
        hideLegend
      >
        <ChartsReferenceLine
          x={overallAvg}
          label={`Average ${overallAvg.toFixed(2)}`}
          labelAlign="end"
          labelStyle={{ fontSize: 15, fill: t.ink, fontWeight: 600 }}
          lineStyle={{ stroke: t.ink, strokeDasharray: "6 4", strokeWidth: 2 }}
        />
        <ClusterAverages />
      </BarChart>
    </div>
  );
}
