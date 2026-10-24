// anyplot.ai
// scatter-embedding: t-SNE and UMAP Embedding Visualization
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-08-11

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "scatter-embedding · javascript · muix · anyplot.ai";
const SUBTITLE = "UMAP (n_neighbors=15) · synthetic single-cell RNA-seq embedding";
const MARGIN = { top: 120, right: 250, bottom: 24, left: 24 };

// Columns: set these to your data's column names
const X_DIM = "UMAP dimension 1"; // role: x
const Y_DIM = "UMAP dimension 2"; // role: y
const LABEL = "Cell type"; // role: label

// Data: replace this block with your own records
const CLUSTER_SPECS = [
  { label: "T cells", cx: -9, cy: 5, spread: 1.9, n: 90 },
  { label: "B cells", cx: 8, cy: 6.5, spread: 1.3, n: 65 },
  { label: "Monocytes", cx: -7, cy: -6.5, spread: 2.1, n: 95 },
  { label: "NK cells", cx: 9.5, cy: -4, spread: 1.4, n: 60 },
  { label: "Dendritic cells", cx: 0.5, cy: 10, spread: 1.6, n: 70 },
  { label: "Platelets", cx: -1, cy: -10, spread: 1.0, n: 55 },
  { label: "Erythrocytes", cx: -12, cy: -1, spread: 1.75, n: 80 },
  { label: "Neutrophils", cx: 13, cy: 1.5, spread: 1.5, n: 65 },
];

let seed = 42;
const data = [];
for (const spec of CLUSTER_SPECS) {
  for (let i = 0; i < spec.n; i += 1) {
    seed = (1664525 * seed + 1013904223) >>> 0;
    const u1x = Math.max(seed / 4294967296, 1e-9);
    seed = (1664525 * seed + 1013904223) >>> 0;
    const u2x = seed / 4294967296;
    const zx = Math.sqrt(-2 * Math.log(u1x)) * Math.cos(2 * Math.PI * u2x);

    seed = (1664525 * seed + 1013904223) >>> 0;
    const u1y = Math.max(seed / 4294967296, 1e-9);
    seed = (1664525 * seed + 1013904223) >>> 0;
    const u2y = seed / 4294967296;
    const zy = Math.sqrt(-2 * Math.log(u1y)) * Math.cos(2 * Math.PI * u2y);

    data.push({
      [X_DIM]: spec.cx + zx * spec.spread,
      [Y_DIM]: spec.cy + zy * spec.spread,
      [LABEL]: spec.label,
    });
  }
}

// Plot: reads only data and the constants above
const clusterLabels = Array.from(new Set(data.map((row) => String(row[LABEL]))));
const clusters = clusterLabels.map((label, i) => {
  const pts = data
    .filter((row) => String(row[LABEL]) === label)
    .map((row, j) => ({
      id: `${label}-${j}`,
      x: Number(row[X_DIM]),
      y: Number(row[Y_DIM]),
    }));
  const n = pts.length;
  const cx = pts.reduce((s, p) => s + p.x, 0) / n;
  const cy = pts.reduce((s, p) => s + p.y, 0) / n;
  const varSum = pts.reduce((s, p) => s + (p.x - cx) ** 2 + (p.y - cy) ** 2, 0) / (2 * n);
  const density = n / varSum;
  return { label, color: t.palette[i % t.palette.length], pts, cx, cy, density };
});

const densities = clusters.map((c) => c.density);
const minDensity = Math.min(...densities);
const maxDensity = Math.max(...densities);
const densitySpan = maxDensity - minDensity;

const allPoints = clusters.flatMap((c) => c.pts);
const xs = allPoints.map((p) => p.x);
const ys = allPoints.map((p) => p.y);
const xPad = (Math.max(...xs) - Math.min(...xs)) * 0.08;
const yPad = (Math.max(...ys) - Math.min(...ys)) * 0.08;
const xMin = Math.min(...xs) - xPad;
const xMax = Math.max(...xs) + xPad;
const yMin = Math.min(...ys) - yPad;
const yMax = Math.max(...ys) + yPad;

function EmbeddingOverlay() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { width, height } = window.ANYPLOT_SIZE;
  const legendX = width - MARGIN.right + 28;
  const legendStartY = Math.round(height / 2 - ((clusters.length - 1) * 32) / 2);

  return (
    <g>
      {clusters.map((cluster) => {
        const cx = xScale(cluster.cx);
        const cy = yScale(cluster.cy) - 20;
        const halfWidth = cluster.label.length * 3.9 + 8;
        return (
          <g key={cluster.label}>
            <rect
              x={cx - halfWidth}
              y={cy - 14}
              width={halfWidth * 2}
              height={20}
              rx={5}
              fill={t.elevatedBg}
              opacity={0.88}
            />
            <text
              x={cx}
              y={cy}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={13}
              fontWeight={600}
              fill={cluster.color}
            >
              {cluster.label}
            </text>
          </g>
        );
      })}

      {clusters.map((cluster, i) => {
        const ly = legendStartY + i * 32;
        return (
          <g key={`legend-${cluster.label}`}>
            <circle cx={legendX} cy={ly} r={6} fill={cluster.color} />
            <text x={legendX + 16} y={ly} fontSize={14} fill={t.ink} dominantBaseline="middle">
              {cluster.label}
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
    <ChartsContainer
      width={width}
      height={height}
      margin={MARGIN}
      skipAnimation
      sx={{ "& .MuiChartsAxis-line, & .MuiChartsAxis-tick": { display: "none" } }}
      series={clusters.map((cluster) => {
        const t01 = densitySpan > 0 ? (cluster.density - minDensity) / densitySpan : 0;
        const alpha = 0.72 - t01 * 0.17;
        const cNum = parseInt(cluster.color.slice(1), 16);
        const rgba = `rgba(${(cNum >> 16) & 255}, ${(cNum >> 8) & 255}, ${cNum & 255}, ${alpha.toFixed(2)})`;
        return {
          type: "scatter",
          id: cluster.label,
          label: cluster.label,
          data: cluster.pts,
          color: rgba,
          markerSize: 5,
        };
      })}
      xAxis={[
        {
          id: "umap1",
          scaleType: "linear",
          min: xMin,
          max: xMax,
          height: 48,
          disableTicks: true,
          disableLine: true,
          tickLabelStyle: { display: "none" },
          label: X_DIM,
          labelStyle: { fontSize: 15, fill: t.inkSoft },
        },
      ]}
      yAxis={[
        {
          id: "umap2",
          scaleType: "linear",
          min: yMin,
          max: yMax,
          width: 48,
          disableTicks: true,
          disableLine: true,
          tickLabelStyle: { display: "none" },
          label: Y_DIM,
          labelStyle: { fontSize: 15, fill: t.inkSoft },
        },
      ]}
    >
      <ScatterPlot skipAnimation />
      <EmbeddingOverlay />
      <ChartsXAxis axisId="umap1" />
      <ChartsYAxis axisId="umap2" />
      <text x={width / 2} y={46} textAnchor="middle" fontSize={28} fontWeight={600} fill={t.ink}>
        {TITLE}
      </text>
      <text x={width / 2} y={82} textAnchor="middle" fontSize={15} fill={t.inkSoft}>
        {SUBTITLE}
      </text>
    </ChartsContainer>
  );
}
