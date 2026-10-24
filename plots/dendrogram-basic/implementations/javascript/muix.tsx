// anyplot.ai
// dendrogram-basic: Basic Dendrogram
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 90/100 | Created: 2026-06-18

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

// Data
const LABEL = "Sample ID";
const SPECIES = "Species";
const SEPAL_L = "Sepal Length (cm)";
const SEPAL_W = "Sepal Width (cm)";
const PETAL_L = "Petal Length (cm)";
const PETAL_W = "Petal Width (cm)";
const DISTANCE = "Distance (Complete Linkage)";
const SUBTITLE = "Complete-linkage hierarchical clustering of Iris floral measurements";

const DATA = [
  { [LABEL]: "S-01", [SPECIES]: "Iris setosa", [SEPAL_L]: 5.1, [SEPAL_W]: 3.5, [PETAL_L]: 1.4, [PETAL_W]: 0.2 },
  { [LABEL]: "S-02", [SPECIES]: "Iris setosa", [SEPAL_L]: 4.9, [SEPAL_W]: 3.0, [PETAL_L]: 1.4, [PETAL_W]: 0.2 },
  { [LABEL]: "S-03", [SPECIES]: "Iris setosa", [SEPAL_L]: 4.7, [SEPAL_W]: 3.2, [PETAL_L]: 1.3, [PETAL_W]: 0.2 },
  { [LABEL]: "S-04", [SPECIES]: "Iris setosa", [SEPAL_L]: 5.0, [SEPAL_W]: 3.6, [PETAL_L]: 1.4, [PETAL_W]: 0.2 },
  { [LABEL]: "S-05", [SPECIES]: "Iris setosa", [SEPAL_L]: 5.4, [SEPAL_W]: 3.9, [PETAL_L]: 1.7, [PETAL_W]: 0.4 },
  { [LABEL]: "Ve-01", [SPECIES]: "Iris versicolor", [SEPAL_L]: 7.0, [SEPAL_W]: 3.2, [PETAL_L]: 4.7, [PETAL_W]: 1.4 },
  { [LABEL]: "Ve-02", [SPECIES]: "Iris versicolor", [SEPAL_L]: 6.4, [SEPAL_W]: 3.2, [PETAL_L]: 4.5, [PETAL_W]: 1.5 },
  { [LABEL]: "Ve-03", [SPECIES]: "Iris versicolor", [SEPAL_L]: 6.9, [SEPAL_W]: 3.1, [PETAL_L]: 4.9, [PETAL_W]: 1.5 },
  { [LABEL]: "Ve-04", [SPECIES]: "Iris versicolor", [SEPAL_L]: 5.5, [SEPAL_W]: 2.3, [PETAL_L]: 4.0, [PETAL_W]: 1.3 },
  { [LABEL]: "Ve-05", [SPECIES]: "Iris versicolor", [SEPAL_L]: 6.5, [SEPAL_W]: 2.8, [PETAL_L]: 4.6, [PETAL_W]: 1.5 },
  { [LABEL]: "Vi-01", [SPECIES]: "Iris virginica", [SEPAL_L]: 6.3, [SEPAL_W]: 3.3, [PETAL_L]: 6.0, [PETAL_W]: 2.5 },
  { [LABEL]: "Vi-02", [SPECIES]: "Iris virginica", [SEPAL_L]: 5.8, [SEPAL_W]: 2.7, [PETAL_L]: 5.1, [PETAL_W]: 1.9 },
  { [LABEL]: "Vi-03", [SPECIES]: "Iris virginica", [SEPAL_L]: 7.1, [SEPAL_W]: 3.0, [PETAL_L]: 5.9, [PETAL_W]: 2.1 },
  { [LABEL]: "Vi-04", [SPECIES]: "Iris virginica", [SEPAL_L]: 6.3, [SEPAL_W]: 2.9, [PETAL_L]: 5.6, [PETAL_W]: 1.8 },
  { [LABEL]: "Vi-05", [SPECIES]: "Iris virginica", [SEPAL_L]: 6.5, [SEPAL_W]: 3.0, [PETAL_L]: 5.8, [PETAL_W]: 2.2 },
];

// Constants
const t = window.ANYPLOT_TOKENS;
const FONT = "Inter, system-ui, -apple-system, sans-serif";
const FEATURE_COLS = [SEPAL_L, SEPAL_W, PETAL_L, PETAL_W];
const Y_PAD_SHARE = 0.08;

// Preparation
const n = DATA.length;
const SPECIES_NAMES = Array.from(new Set(DATA.map((d) => String(d[SPECIES]))));
const SPECIES_COLORS = Object.fromEntries(
  SPECIES_NAMES.map((sp, i) => [sp, t.palette[i]])
);

const distMatrix = Array.from({ length: n }, () => new Array(n).fill(0));
for (let i = 0; i < n; i++) {
  for (let j = i + 1; j < n; j++) {
    let sumSq = 0;
    for (const col of FEATURE_COLS) {
      const diff = Number(DATA[i][col]) - Number(DATA[j][col]);
      sumSq += diff * diff;
    }
    const d = Math.sqrt(sumSq);
    distMatrix[i][j] = d;
    distMatrix[j][i] = d;
  }
}

type TreeNode = {
  id: number;
  height: number;
  leaves: number[];
  children: [TreeNode, TreeNode] | null;
  x: number;
  species: string | null;
};

const allNodes: TreeNode[] = DATA.map((row, i) => ({
  id: i,
  height: 0,
  leaves: [i],
  children: null,
  x: 0,
  species: String(row[SPECIES]),
}));

const activeNodes: TreeNode[] = [...allNodes];
while (activeNodes.length > 1) {
  let minD = Infinity;
  let mi = 0;
  let mj = 1;
  for (let i = 0; i < activeNodes.length; i++) {
    for (let j = i + 1; j < activeNodes.length; j++) {
      let d = 0;
      for (const li of activeNodes[i].leaves) {
        for (const lj of activeNodes[j].leaves) {
          if (distMatrix[li][lj] > d) d = distMatrix[li][lj];
        }
      }
      if (d < minD) {
        minD = d;
        mi = i;
        mj = j;
      }
    }
  }
  const leftNode = activeNodes[mi];
  const rightNode = activeNodes[mj];
  const merged: TreeNode = {
    id: allNodes.length,
    height: minD,
    leaves: [...leftNode.leaves, ...rightNode.leaves],
    children: [leftNode, rightNode],
    x: 0,
    species:
      leftNode.species !== null && leftNode.species === rightNode.species
        ? leftNode.species
        : null,
  };
  allNodes.push(merged);
  activeNodes.splice(mj, 1);
  activeNodes.splice(mi, 1);
  activeNodes.push(merged);
}

const root = activeNodes[0];

const order: number[] = [];
const stack: TreeNode[] = [root];
while (stack.length > 0) {
  const cur = stack.pop()!;
  if (!cur.children) {
    order.push(cur.leaves[0]);
  } else {
    stack.push(cur.children[1]);
    stack.push(cur.children[0]);
  }
}

order.forEach((leafIdx, pos) => {
  allNodes[leafIdx].x = pos;
});
for (let id = n; id < allNodes.length; id++) {
  const node = allNodes[id];
  if (node.children) {
    node.x = (node.children[0].x + node.children[1].x) / 2;
  }
}

const segs: { x1: number; y1: number; x2: number; y2: number; color: string }[] = [];
for (let id = n; id < allNodes.length; id++) {
  const node = allNodes[id];
  if (!node.children) continue;
  const [l, r] = node.children;
  const bridgeColor = node.species !== null ? SPECIES_COLORS[node.species] : t.ink;
  const leftColor = l.species !== null ? SPECIES_COLORS[l.species] : t.ink;
  const rightColor = r.species !== null ? SPECIES_COLORS[r.species] : t.ink;
  segs.push(
    { x1: l.x, y1: node.height, x2: r.x, y2: node.height, color: bridgeColor },
    { x1: l.x, y1: l.height, x2: l.x, y2: node.height, color: leftColor },
    { x1: r.x, y1: r.height, x2: r.x, y2: node.height, color: rightColor }
  );
}

const maxH = root.height;
const X_MIN = -0.5;
const X_MAX = n - 0.5;
const Y_MAX = maxH * (1 + Y_PAD_SHARE);
const orderedLabels = order.map((li) => String(DATA[li][LABEL]));

const scatterSeries = SPECIES_NAMES.map((sp) => ({
  type: "scatter" as const,
  id: sp,
  data: order
    .map((li, pos) =>
      DATA[li][SPECIES] === sp ? { id: `${sp}-${pos}`, x: pos, y: 0 } : null
    )
    .filter(Boolean) as { id: string; x: number; y: number }[],
  label: sp,
  color: SPECIES_COLORS[sp],
  markerSize: 7,
  xAxisId: "x",
  yAxisId: "y",
}));

function DendrogramBranches() {
  const xs = useXScale("x");
  const ys = useYScale("y");
  if (!xs || !ys) return null;
  return (
    <g>
      {segs.map((s, i) => (
        <line
          key={i}
          x1={xs(s.x1)}
          y1={ys(s.y1)}
          x2={xs(s.x2)}
          y2={ys(s.y2)}
          stroke={s.color}
          strokeWidth={2.4}
          strokeLinecap="round"
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const HEADER_H = 78;
  const LEGEND_H = 44;

  return (
    <div
      style={{
        width: W,
        height: H,
        background: t.pageBg,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 4,
          paddingTop: 8,
        }}
      >
        <span style={{ fontSize: 22, fontWeight: 700, color: t.ink }}>
          dendrogram-basic · javascript · muix · anyplot.ai
        </span>
        <span style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</span>
      </div>

      <ChartsContainer
        width={W - 48}
        height={H - HEADER_H - LEGEND_H}
        skipAnimation
        series={scatterSeries}
        margin={{ top: 18, right: 36, bottom: 20, left: 24 }}
        xAxis={[
          {
            id: "x",
            min: X_MIN,
            max: X_MAX,
            height: 60,
            label: LABEL,
            tickInterval: Array.from({ length: n }, (_, i) => i),
            valueFormatter: (v: number) => orderedLabels[Math.round(v)] ?? "",
            tickLabelStyle: {
              fontSize: 14,
              fill: t.inkSoft,
              fontFamily: FONT,
            },
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
          },
        ]}
        yAxis={[
          {
            id: "y",
            min: 0,
            max: Y_MAX,
            width: 84,
            label: DISTANCE,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeDasharray: "4 4" },
        }}
      >
        <ChartsGrid horizontal />
        <DendrogramBranches />
        <ScatterPlot />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId="y" />
      </ChartsContainer>

      <div
        style={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 28,
        }}
      >
        {SPECIES_NAMES.map((name) => (
          <div
            key={name}
            style={{ display: "flex", alignItems: "center", gap: 8 }}
          >
            <span
              style={{
                width: 13,
                height: 13,
                borderRadius: "50%",
                background: SPECIES_COLORS[name],
                display: "inline-block",
              }}
            />
            <span
              style={{
                fontSize: 14,
                fontStyle: "italic",
                color: t.ink,
              }}
            >
              {name}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
