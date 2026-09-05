// anyplot.ai
// heatmap-clustered: Clustered Heatmap
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05
//# anyplot-orientation: square
// anyplot.ai
// heatmap-clustered: Clustered Heatmap
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-05
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsText } from "@mui/x-charts/ChartsText";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { useXScale, useYScale, useZColorScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;

// --- Data: synthetic gene-expression matrix (in-memory, deterministic LCG) ---------
function makeLcg(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = makeLcg(42);
const noise = (range) => (rand() * 2 - 1) * range;

const GENES = [
  "IL6", "TNF", "IFNG", "IL1B", "CXCL10", "STAT1", // inflammatory response
  "COL1A1", "COL3A1", "ACTA2", "FN1", "VIM", // fibrosis markers
  "MKI67", "PCNA", "TOP2A", "CCND1", "CDK4", // proliferation markers
];
const geneClusterOf = (i) => (i < 6 ? 0 : i < 11 ? 1 : 2);
const GENE_CLUSTER_LABELS = ["Inflammatory", "Fibrosis", "Proliferation"];
// Palette positions distinct from the Control/Treated strip (0, 1) and from the
// diverging heatmap's red/blue endpoints (4, 2), so the row groups read as their own signal.
const GENE_CLUSTER_PALETTE_IDX = [3, 5, 6];

const SAMPLES = [
  "Control-01", "Control-02", "Control-03", "Control-04", "Control-05", "Control-06",
  "Treated-01", "Treated-02", "Treated-03", "Treated-04", "Treated-05", "Treated-06",
];
const conditionOf = (j) => (j < 6 ? 0 : 1);

// Representative log2 fold-change per (gene cluster, condition)
const CLUSTER_BASE = [
  [-0.3, 2.4], // inflammatory: flat in control, up in treated
  [0.3, -2.2], // fibrosis: flat in control, down in treated
  [0.6, 1.4], // proliferation: mild rise under treatment
];

const geneOffset = GENES.map(() => noise(0.25));
const sampleBatch = SAMPLES.map(() => noise(0.3));
const matrix = GENES.map((_, i) =>
  SAMPLES.map((_, j) => {
    const base = CLUSTER_BASE[geneClusterOf(i)][conditionOf(j)];
    return base + geneOffset[i] + sampleBatch[j] + noise(0.35);
  }),
);
const maxAbsValue = Math.max(...matrix.flat().map(Math.abs));
const COLOR_DOMAIN = Math.ceil(maxAbsValue * 10) / 10;

// --- Hierarchical clustering (Ward's minimum-variance linkage, Euclidean distance) -
function squaredEuclidean(a, b) {
  let sum = 0;
  for (let k = 0; k < a.length; k += 1) sum += (a[k] - b[k]) ** 2;
  return sum;
}

function buildTree(vectors) {
  let nodes = vectors.map((v, i) => ({
    height: 0,
    leaves: [i],
    children: null,
    pos: 0,
    centroid: v.slice(),
    size: 1,
  }));
  while (nodes.length > 1) {
    let minCost = Infinity;
    let mi = 0;
    let mj = 1;
    for (let i = 0; i < nodes.length; i += 1) {
      for (let j = i + 1; j < nodes.length; j += 1) {
        const a = nodes[i];
        const b = nodes[j];
        // Ward's criterion: increase in within-cluster sum of squares from merging a, b.
        const cost = ((a.size * b.size) / (a.size + b.size)) * squaredEuclidean(a.centroid, b.centroid);
        if (cost < minCost) {
          minCost = cost;
          mi = i;
          mj = j;
        }
      }
    }
    const a = nodes[mi];
    const b = nodes[mj];
    const size = a.size + b.size;
    const centroid = a.centroid.map((v, k) => (v * a.size + b.centroid[k] * b.size) / size);
    const merged = {
      height: Math.sqrt(minCost),
      leaves: [...a.leaves, ...b.leaves],
      children: [a, b],
      pos: 0,
      centroid,
      size,
    };
    nodes.splice(mj, 1);
    nodes.splice(mi, 1);
    nodes.push(merged);
  }
  return nodes[0];
}

function leafOrder(node) {
  if (!node.children) return [node.leaves[0]];
  return [...leafOrder(node.children[0]), ...leafOrder(node.children[1])];
}

function assignPos(node, posMap) {
  if (!node.children) {
    node.pos = posMap[node.leaves[0]];
    return;
  }
  assignPos(node.children[0], posMap);
  assignPos(node.children[1], posMap);
  node.pos = (node.children[0].pos + node.children[1].pos) / 2;
}

function getSegments(node) {
  if (!node.children) return [];
  const [l, r] = node.children;
  return [
    { p1: l.pos, d1: node.height, p2: r.pos, d2: node.height },
    { p1: l.pos, d1: l.height, p2: l.pos, d2: node.height },
    { p1: r.pos, d1: r.height, p2: r.pos, d2: node.height },
    ...getSegments(l),
    ...getSegments(r),
  ];
}

const rowTree = buildTree(matrix);
const colTree = buildTree(SAMPLES.map((_, j) => GENES.map((_, i) => matrix[i][j])));
const rowOrder = leafOrder(rowTree);
const colOrder = leafOrder(colTree);
const rowPosMap = {};
rowOrder.forEach((gi, pos) => { rowPosMap[gi] = pos; });
const colPosMap = {};
colOrder.forEach((sj, pos) => { colPosMap[sj] = pos; });
assignPos(rowTree, rowPosMap);
assignPos(colTree, colPosMap);
const rowSegments = getSegments(rowTree);
const colSegments = getSegments(colTree);

const orderedGeneLabels = rowOrder.map((i) => GENES[i]);
const orderedSampleLabels = colOrder.map((j) => SAMPLES[j]);

const cells = [];
for (let pr = 0; pr < orderedGeneLabels.length; pr += 1) {
  for (let pc = 0; pc < orderedSampleLabels.length; pc += 1) {
    const gi = rowOrder[pr];
    const sj = colOrder[pc];
    cells.push({
      id: `${gi}-${sj}`,
      x: orderedSampleLabels[pc],
      y: orderedGeneLabels[pr],
      value: matrix[gi][sj],
    });
  }
}

// --- Colour: diverging Imprint colormap (imprint_div) ------------------------------
function hexToRgb(hex) {
  const int = parseInt(hex.slice(1), 16);
  return [(int >> 16) & 255, (int >> 8) & 255, int & 255];
}
function lerp(a, b, ratio) {
  return Math.round(a + (b - a) * ratio);
}
function imprintDivInterpolator(stops) {
  const [low, mid, high] = stops.map(hexToRgb);
  return (position) => {
    const [start, end, localRatio] =
      position < 0.5 ? [low, mid, position / 0.5] : [mid, high, (position - 0.5) / 0.5];
    const [r, g, b] = [0, 1, 2].map((c) => lerp(start[c], end[c], localRatio));
    return `rgb(${r}, ${g}, ${b})`;
  };
}

// --- Layout constants (square 1200x1200 CSS mount) ---------------------------------
const TITLE_H = 60;
const COL_DENDRO_H = 100;
const ANNOT_H = 16;
const ROW_DENDRO_W = 110;
const LABEL_RESERVE = 88;
const ROW_ANNOT_W = 16;
const ROW_ANNOT_GAP = 6;
const MARGIN = {
  top: TITLE_H + 14 + COL_DENDRO_H + 6 + ANNOT_H + 6,
  right: 190,
  bottom: 130,
  left: ROW_DENDRO_W + 8 + LABEL_RESERVE + ROW_ANNOT_GAP + ROW_ANNOT_W + ROW_ANNOT_GAP,
};

// --- Overlay: dendrograms, condition strip, and heatmap cells drawn in one pass ----
function ClusteredOverlay() {
  const xScale = useXScale();
  const yScale = useYScale();
  const colorScale = useZColorScale();
  const drawingArea = useDrawingArea();

  const colCenterX = (pos) => drawingArea.left + (drawingArea.width / orderedSampleLabels.length) * (pos + 0.5);
  const rowCenterY = (pos) => drawingArea.top + (drawingArea.height / orderedGeneLabels.length) * (pos + 0.5);

  const colDendroYBottom = drawingArea.top - ANNOT_H - 12;
  const colDendroYTop = TITLE_H + 14;
  const colDistY = (dist) =>
    colDendroYBottom - (dist / colTree.height) * (colDendroYBottom - colDendroYTop);

  const rowDendroXRight = drawingArea.left - ROW_ANNOT_GAP - ROW_ANNOT_W - ROW_ANNOT_GAP - LABEL_RESERVE - 8;
  const rowDendroXLeft = 12;
  const rowDistX = (dist) =>
    rowDendroXRight - (dist / rowTree.height) * (rowDendroXRight - rowDendroXLeft);

  const stripTop = drawingArea.top - ANNOT_H - 4;
  const rowStripRight = drawingArea.left - ROW_ANNOT_GAP;
  const rowStripLeft = rowStripRight - ROW_ANNOT_W;
  const rowHeight = drawingArea.height / orderedGeneLabels.length;

  return (
    <g>
      {/* Heatmap cells */}
      {cells.map((cell) => (
        <rect
          key={cell.id}
          x={xScale(cell.x) ?? 0}
          y={yScale(cell.y) ?? 0}
          width={xScale.bandwidth()}
          height={yScale.bandwidth()}
          fill={colorScale(cell.value)}
        />
      ))}

      {/* Condition annotation strip (Control vs. Treated) */}
      {colOrder.map((sj, pos) => (
        <rect
          key={`strip-${sj}`}
          x={colCenterX(pos) - drawingArea.width / orderedSampleLabels.length / 2}
          y={stripTop}
          width={drawingArea.width / orderedSampleLabels.length}
          height={ANNOT_H}
          fill={t.palette[conditionOf(sj)]}
        />
      ))}

      {/* Gene-cluster annotation strip (Inflammatory / Fibrosis / Proliferation) */}
      {rowOrder.map((gi, pos) => (
        <rect
          key={`row-strip-${gi}`}
          x={rowStripLeft}
          y={rowCenterY(pos) - rowHeight / 2}
          width={ROW_ANNOT_W}
          height={rowHeight}
          fill={t.palette[GENE_CLUSTER_PALETTE_IDX[geneClusterOf(gi)]]}
        />
      ))}

      {/* Column dendrogram (samples) */}
      {colSegments.map((s, i) => (
        <line
          key={`col-seg-${i}`}
          x1={colCenterX(s.p1)}
          y1={colDistY(s.d1)}
          x2={colCenterX(s.p2)}
          y2={colDistY(s.d2)}
          stroke={t.ink}
          strokeWidth={1.5}
          strokeLinecap="round"
        />
      ))}

      {/* Row dendrogram (genes) */}
      {rowSegments.map((s, i) => (
        <line
          key={`row-seg-${i}`}
          x1={rowDistX(s.d1)}
          y1={rowCenterY(s.p1)}
          x2={rowDistX(s.d2)}
          y2={rowCenterY(s.p2)}
          stroke={t.ink}
          strokeWidth={1.5}
          strokeLinecap="round"
        />
      ))}

      {/* Condition legend swatches */}
      <circle cx={SIZE.width - 168} cy={30} r={6} fill={t.palette[0]} />
      <ChartsText
        text="Control"
        x={SIZE.width - 154}
        y={30}
        style={{ fontSize: 13, fill: t.inkSoft, textAnchor: "start", dominantBaseline: "central" }}
      />
      <circle cx={SIZE.width - 168} cy={50} r={6} fill={t.palette[1]} />
      <ChartsText
        text="Treated"
        x={SIZE.width - 154}
        y={50}
        style={{ fontSize: 13, fill: t.inkSoft, textAnchor: "start", dominantBaseline: "central" }}
      />

      {/* Gene-cluster legend swatches */}
      {GENE_CLUSTER_LABELS.map((label, idx) => (
        <g key={`gc-legend-${label}`}>
          <circle cx={SIZE.width - 168} cy={76 + idx * 20} r={6} fill={t.palette[GENE_CLUSTER_PALETTE_IDX[idx]]} />
          <ChartsText
            text={label}
            x={SIZE.width - 154}
            y={76 + idx * 20}
            style={{ fontSize: 13, fill: t.inkSoft, textAnchor: "start", dominantBaseline: "central" }}
          />
        </g>
      ))}

      <ChartsText
        text="Log2 fold change"
        x={SIZE.width - 22}
        y={SIZE.height / 2}
        style={{ fontSize: 12, fill: t.inkSoft, textAnchor: "middle", angle: -90 }}
      />
    </g>
  );
}

// --- Chart (default-exported component — the harness mounts it) -------------------
const TITLE = "heatmap-clustered · javascript · muix · anyplot.ai";

export default function Chart() {
  return (
    <ChartContainer
      width={SIZE.width}
      height={SIZE.height}
      series={[]}
      margin={MARGIN}
      skipAnimation
      xAxis={[
        {
          scaleType: "band",
          data: orderedSampleLabels,
          categoryGapRatio: 0.1,
          disableLine: true,
          disableTicks: true,
          tickLabelStyle: { fontSize: 13, fill: t.inkSoft, angle: -45, textAnchor: "end" },
        },
      ]}
      yAxis={[
        {
          scaleType: "band",
          data: orderedGeneLabels,
          categoryGapRatio: 0.1,
          disableLine: true,
          disableTicks: true,
          tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
        },
      ]}
      zAxis={[
        {
          colorMap: {
            type: "continuous",
            min: -COLOR_DOMAIN,
            max: COLOR_DOMAIN,
            color: imprintDivInterpolator(t.div),
          },
        },
      ]}
    >
      <ClusteredOverlay />
      <ChartsXAxis />
      <ChartsYAxis />
      <ContinuousColorLegend
        position={{ horizontal: "right", vertical: "middle" }}
        direction="column"
        length="45%"
        thickness={18}
        labelStyle={{ fontSize: 12, fill: t.inkSoft }}
      />
      <ChartsText
        text={TITLE}
        x={SIZE.width / 2}
        y={32}
        style={{ fontSize: 22, fontWeight: 600, fill: t.ink, textAnchor: "middle" }}
      />
    </ChartContainer>
  );
}
