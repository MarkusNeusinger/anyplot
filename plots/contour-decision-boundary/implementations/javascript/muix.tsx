// anyplot.ai
// contour-decision-boundary: Decision Boundary Classifier Visualization
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-04
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const K_NEIGHBORS = 13; // k-nearest-neighbour classifier: majority vote of the 13 closest training points
const MESH_STEPS = 180; // prediction mesh nodes per axis, fine enough that the boundary shows no grid steps
const PAD_SHARE = 0.12; // feature plane beyond the training points, as a share of each feature's range
const REGION_OPACITY = 0.24; // region tint, light enough that the training points stay the strongest marks

// Columns: set these to your data's column names
const PETAL_LENGTH = "Petal length (cm)"; // role: X1
const PETAL_WIDTH = "Petal width (cm)"; // role: X2
const SPECIES = "Species"; // role: y

// Data: replace this block with your own records, one object per training point
// Synthetic iris-like petal measurements of three species: setosa separates cleanly on these two
// features, versicolor and virginica overlap near their shared boundary as in the real iris data
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };
  const gaussian = () => Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
  const species = [
    { name: "Setosa", meanLength: 1.5, meanWidth: 0.25, sdLength: 0.17, sdWidth: 0.1, n: 50 },
    { name: "Versicolor", meanLength: 4.3, meanWidth: 1.3, sdLength: 0.47, sdWidth: 0.2, n: 55 },
    { name: "Virginica", meanLength: 5.55, meanWidth: 2.03, sdLength: 0.55, sdWidth: 0.27, n: 55 },
  ];
  return species.flatMap((sp) =>
    Array.from({ length: sp.n }, () => {
      const length = Math.round((sp.meanLength + gaussian() * sp.sdLength) * 100) / 100;
      const width = Math.round((sp.meanWidth + gaussian() * sp.sdWidth) * 100) / 100;
      // petals are never thinner than 0.1 cm, the smallest width in the real iris data
      return { [PETAL_LENGTH]: length, [PETAL_WIDTH]: Math.max(0.1, width), [SPECIES]: sp.name };
    }),
  );
})();

// Plot: reads only data and the constants above
// Classes in order of first appearance, one palette position each
const classes = [...new Set(data.map((d) => d[SPECIES]))];
const points = data
  .filter((d) => Number.isFinite(d[PETAL_LENGTH]) && Number.isFinite(d[PETAL_WIDTH]))
  .map((d, i) => ({ id: `point-${i}`, x: d[PETAL_LENGTH], y: d[PETAL_WIDTH], cls: classes.indexOf(d[SPECIES]) }));

// Feature plane: the training extent plus a padding share; a feature that is never negative keeps a
// non-negative axis
const [xDomain, yDomain] = [points.map((p) => p.x), points.map((p) => p.y)].map((values) => {
  const low = Math.min(...values);
  const high = Math.max(...values);
  const pad = (high - low) * PAD_SHARE;
  return [low >= 0 ? Math.max(0, low - pad) : low - pad, high + pad];
});
const meshX = Array.from({ length: MESH_STEPS }, (_, i) => xDomain[0] + (i / (MESH_STEPS - 1)) * (xDomain[1] - xDomain[0]));
const meshY = Array.from({ length: MESH_STEPS }, (_, j) => yDomain[0] + (j / (MESH_STEPS - 1)) * (yDomain[1] - yDomain[0]));

// k-NN votes per class: every training point is classified leave-one-out (it never votes for itself),
// every mesh node by all training points
const queries = [
  ...points.map((p, i) => ({ x: p.x, y: p.y, skip: i })),
  ...meshY.flatMap((y) => meshX.map((x) => ({ x, y, skip: -1 }))),
];
const votes = queries.map((q) => {
  const nearest = points
    .map((p, i) => ({ i, cls: p.cls, d2: (p.x - q.x) ** 2 + (p.y - q.y) ** 2 }))
    .filter((n) => n.i !== q.skip)
    .sort((a, b) => a.d2 - b.d2)
    .slice(0, K_NEIGHBORS);
  return classes.map((_, c) => nearest.filter((n) => n.cls === c).length);
});
const predicted = points.map((_, i) => votes[i].indexOf(Math.max(...votes[i])));
const misclassified = points.filter((p, i) => predicted[i] !== p.cls);

// Region of a class: mesh nodes where its votes reach the best other class (margin >= 0). Marching
// triangles over that margin give the region polygons and a boundary interpolated between nodes.
const meshVotes = votes.slice(points.length);
const regionPolygons: { x: number; y: number }[][][] = [];
const boundaryCuts: { x: number; y: number }[][][] = [];
classes.forEach((_, c) => {
  const margin = meshVotes.map((v) => v[c] - Math.max(...v.filter((_, k) => k !== c)));
  const polys: { x: number; y: number }[][] = [];
  const cuts: { x: number; y: number }[][] = [];
  for (let j = 0; j < MESH_STEPS - 1; j += 1) {
    for (let i = 0; i < MESH_STEPS - 1; i += 1) {
      const [sw, se, ne, nw] = [
        [i, j],
        [i + 1, j],
        [i + 1, j + 1],
        [i, j + 1],
      ].map(([ii, jj]) => ({ x: meshX[ii], y: meshY[jj], z: margin[jj * MESH_STEPS + ii] }));
      const centre = { x: (sw.x + se.x) / 2, y: (sw.y + nw.y) / 2, z: (sw.z + se.z + ne.z + nw.z) / 4 };
      [[sw, se], [se, ne], [ne, nw], [nw, sw]].forEach(([a, b]) => {
        const tri = [a, b, centre];
        const inside = tri.map((p) => p.z >= 0);
        if (inside.every(Boolean)) {
          polys.push(tri);
          return;
        }
        if (!inside.some(Boolean)) return;
        const ring: { x: number; y: number }[] = [];
        const cut: { x: number; y: number }[] = [];
        tri.forEach((p, k) => {
          const q = tri[(k + 1) % 3];
          if (inside[k]) ring.push(p);
          if (inside[k] !== inside[(k + 1) % 3]) {
            const r = p.z / (p.z - q.z);
            const crossing = { x: p.x + r * (q.x - p.x), y: p.y + r * (q.y - p.y) };
            ring.push(crossing);
            cut.push(crossing);
          }
        });
        polys.push(ring);
        cuts.push(cut);
      });
    }
  }
  regionPolygons.push(polys);
  boundaryCuts.push(cuts);
});

const series = [
  ...classes.map((name, c) => ({
    type: "scatter" as const,
    id: `class-${c}`,
    label: name,
    color: t.palette[c],
    markerSize: 8,
    labelMarkType: "circle" as const,
    data: points.filter((p) => p.cls === c).map(({ id, x, y }) => ({ id, x, y })),
  })),
  {
    type: "scatter" as const,
    id: "misclassified",
    label: "Misclassified (leave-one-out)",
    color: t.ink,
    markerSize: 13,
    labelMarkType: "circle" as const,
    data: misclassified.map(({ id, x, y }) => ({ id: `ring-${id}`, x, y })),
  },
];

const TITLE = "Iris Species by k-NN · contour-decision-boundary · javascript · muix · anyplot.ai";
const subtitle = `${points.length} training points · k = ${K_NEIGHBORS} nearest-neighbour vote on a ${MESH_STEPS} × ${MESH_STEPS} mesh · ${misclassified.length} misclassified in leave-one-out`;
const HEADER_H = 84;
const LEGEND_W = 280;

function RegionLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const toPath = (shapes: { x: number; y: number }[][], close: boolean) =>
    shapes
      .map((shape) => shape.map((p, k) => `${k === 0 ? "M" : "L"}${xScale(p.x)!.toFixed(1)},${yScale(p.y)!.toFixed(1)}`).join("") + (close ? "Z" : ""))
      .join("");
  return (
    <g>
      {/* Opaque fills inside one translucent group: no seams between the mesh triangles */}
      <g opacity={REGION_OPACITY}>
        {regionPolygons.map((polys, c) => (
          <path key={`region-${c}`} d={toPath(polys, true)} fill={t.palette[c]} stroke={t.palette[c]} strokeWidth={0.75} />
        ))}
      </g>
      {boundaryCuts.map((cuts, c) => (
        <path key={`boundary-${c}`} d={toPath(cuts, false)} fill="none" stroke={t.inkSoft} strokeWidth={1.8} strokeLinecap="round" />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: HEADER_H, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "6px", pt: "8px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2 }}>{subtitle}</Typography>
      </Box>
      <ChartsDataProvider
        width={width - LEGEND_W}
        height={height - HEADER_H}
        series={series}
        skipAnimation
        margin={{ top: 16, bottom: 16, left: 24, right: 24 }}
        xAxis={[
          {
            scaleType: "linear",
            min: xDomain[0],
            max: xDomain[1],
            label: PETAL_LENGTH,
            height: 60,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: yDomain[0],
            max: yDomain[1],
            label: PETAL_WIDTH,
            width: 76,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
      >
        <ChartsWrapper
          legendPosition={{ vertical: "middle", horizontal: "end" }}
          legendDirection="vertical"
          sx={{ width, height: height - HEADER_H }}
        >
          <ChartsSurface
            sx={{
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
              "& .MuiScatterChart-marker": { stroke: t.pageBg, strokeWidth: 1.2 },
              '& [data-series="misclassified"] .MuiScatterChart-marker': { fill: "none", stroke: t.ink, strokeWidth: 2.5 },
            }}
          >
            <RegionLayer />
            <ScatterPlot />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
          <ChartsLegend
            direction="vertical"
            sx={{
              width: LEGEND_W,
              pl: "24px",
              gap: "12px",
              "& .MuiChartsLegend-label": { fontSize: 15, color: t.ink },
              '& [data-series="misclassified"] .MuiChartsLabelMark-fill': { fill: "none", stroke: t.ink, strokeWidth: 2.5, r: 5.5 },
            }}
          />
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
