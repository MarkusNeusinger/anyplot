// anyplot.ai
// scatter-embedding: t-SNE and UMAP Embedding Visualization
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const EMBEDDING_METHOD = "UMAP (n_neighbors = 15)"; // the projection behind the two embedding columns
const POINT_OPACITY = 0.62; // slight transparency, so dense cores read darker
const EXTENT_PAD_SHARE = 0.05; // room beyond the outermost points, as a share of each axis span
const LABEL_FONT_SIZE = 15;
const LABEL_CHAR_WIDTH = 0.56; // average glyph width of the centroid labels, as a share of the font size

// Columns: set these to your data's column names
const X = "UMAP dimension 1"; // role: x
const Y = "UMAP dimension 2"; // role: y
const LABEL = "Cell type"; // role: label

// Data: replace this block with your own records, one object per row
// Simulated UMAP projection of single-cell RNA-seq profiles: eight cell types
// of differing size and compactness around their own centres.
const data = (() => {
  let seed = 42;
  const uniform = () => {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const gaussian = () => Math.sqrt(-2 * Math.log(Math.max(uniform(), 1e-9))) * Math.cos(2 * Math.PI * uniform());
  const cellTypes = [
    { name: "T cells", cx: -9, cy: 5, spread: 1.9, n: 90 },
    { name: "B cells", cx: 8, cy: 6.5, spread: 1.3, n: 65 },
    { name: "Monocytes", cx: -7, cy: -6.5, spread: 2.1, n: 95 },
    { name: "NK cells", cx: 9.5, cy: -4, spread: 1.4, n: 60 },
    { name: "Dendritic cells", cx: 0.5, cy: 10, spread: 1.6, n: 70 },
    { name: "Platelets", cx: -1, cy: -10, spread: 1.0, n: 55 },
    { name: "Erythrocytes", cx: -12, cy: -1, spread: 1.75, n: 80 },
    { name: "Neutrophils", cx: 13, cy: 1.5, spread: 1.5, n: 65 },
  ];
  return cellTypes.flatMap((c) =>
    Array.from({ length: c.n }, () => ({
      [X]: Number((c.cx + gaussian() * c.spread).toFixed(3)),
      [Y]: Number((c.cy + gaussian() * c.spread).toFixed(3)),
      [LABEL]: c.name,
    })),
  );
})();

// Plot: reads only data and the constants above
const labels = [...new Set(data.map((d) => d[LABEL]))];
const groups = labels.map((label, i) => {
  const rows = data.filter((d) => d[LABEL] === label);
  return {
    label,
    color: t.palette[i],
    points: rows.map((d, k) => ({ id: `${i}-${k}`, x: d[X], y: d[Y] })),
    centroidX: rows.reduce((s, d) => s + d[X], 0) / rows.length,
    centroidY: rows.reduce((s, d) => s + d[Y], 0) / rows.length,
  };
});

const xs = data.map((d) => d[X]);
const ys = data.map((d) => d[Y]);
const xPad = (Math.max(...xs) - Math.min(...xs)) * EXTENT_PAD_SHARE;
const yPad = (Math.max(...ys) - Math.min(...ys)) * EXTENT_PAD_SHARE;

const TITLE = "scatter-embedding · javascript · muix · anyplot.ai";
const SUBTITLE = `${EMBEDDING_METHOD} · n = ${data.length} · coloured by ${LABEL.toLowerCase()} (${labels.length} groups)`;
const HEADER_HEIGHT = 84;
const LEGEND_WIDTH = 220;

function CentroidLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {groups.map((g) => {
        const cx = xScale(g.centroidX);
        const cy = yScale(g.centroidY);
        const halfWidth = (g.label.length * LABEL_FONT_SIZE * LABEL_CHAR_WIDTH) / 2 + 10;
        return (
          <g key={g.label}>
            <rect
              x={cx - halfWidth}
              y={cy - 14}
              width={halfWidth * 2}
              height={28}
              rx={6}
              fill={t.elevatedBg}
              fillOpacity={0.88}
              stroke={g.color}
              strokeWidth={2}
            />
            <text
              x={cx}
              y={cy + 1}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={LABEL_FONT_SIZE}
              fontWeight={600}
              fill={t.ink}
            >
              {g.label}
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
          height: HEADER_HEIGHT,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 16, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsDataProvider
        width={width - LEGEND_WIDTH}
        height={height - HEADER_HEIGHT}
        margin={{ top: 12, right: 24, bottom: 16, left: 24 }}
        skipAnimation
        series={groups.map((g, i) => ({
          type: "scatter" as const,
          id: `group-${i}`,
          label: g.label,
          data: g.points,
          color: g.color,
          markerSize: 5,
        }))}
        xAxis={[
          {
            id: "x",
            scaleType: "linear",
            min: Math.min(...xs) - xPad,
            max: Math.max(...xs) + xPad,
            label: X,
            height: 40,
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: { display: "none" },
            labelStyle: { fontSize: 16, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "y",
            scaleType: "linear",
            min: Math.min(...ys) - yPad,
            max: Math.max(...ys) + yPad,
            label: Y,
            width: 40,
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: { display: "none" },
            labelStyle: { fontSize: 16, fill: t.inkSoft },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "middle", horizontal: "end" }} legendDirection="vertical">
          <ChartsLegend direction="vertical" sx={{ fontSize: 16, color: t.ink, width: LEGEND_WIDTH, gap: 1.5, pl: 3 }} />
          <ChartsSurface sx={{ "& .MuiScatterChart-marker": { fillOpacity: POINT_OPACITY } }}>
            <ChartsXAxis />
            <ChartsYAxis />
            <ScatterPlot />
            <CentroidLabels />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
