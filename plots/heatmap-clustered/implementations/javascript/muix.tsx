// anyplot.ai
// heatmap-clustered: Clustered Heatmap
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 88/100 | Updated: 2026-10-24
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SIZE = window.ANYPLOT_SIZE;
const TITLE = "heatmap-clustered · javascript · muix · anyplot.ai";

const HEADER_H = 80;
const COL_DENDRO_H = 92;
const ANNOT_H = 16;
const ROW_DENDRO_LEFT = 22;
const ROW_DENDRO_W = 112;
const ROW_ANNOT_W = 16;
const Y_AXIS_WIDTH = 92;
const X_AXIS_HEIGHT = 96;

const MARGIN = {
  top: HEADER_H + COL_DENDRO_H + ANNOT_H + 16,
  right: 176,
  bottom: 24,
  left: ROW_DENDRO_LEFT + ROW_DENDRO_W + 8 + ROW_ANNOT_W + 8,
};

// Columns: set these to your data's column names
const GENE = "Gene"; // role: row_labels
const PATHWAY = "Pathway";
const SAMPLE = "Sample"; // role: column_labels
const CONDITION = "Condition";
const LOG2_FC = "Log2 fold change"; // role: matrix

// Data: replace this block with your own records
const GENE_SPECS = [
  "IL6|Inflammatory|-0.3|2.4",
  "TNF|Inflammatory|-0.3|2.4",
  "IFNG|Inflammatory|-0.3|2.4",
  "IL1B|Inflammatory|-0.3|2.4",
  "CXCL10|Inflammatory|-0.3|2.4",
  "STAT1|Inflammatory|-0.3|2.4",
  "COL1A1|Fibrosis|0.3|-2.2",
  "COL3A1|Fibrosis|0.3|-2.2",
  "ACTA2|Fibrosis|0.3|-2.2",
  "FN1|Fibrosis|0.3|-2.2",
  "VIM|Fibrosis|0.3|-2.2",
  "MKI67|Proliferation|0.6|1.4",
  "PCNA|Proliferation|0.6|1.4",
  "TOP2A|Proliferation|0.6|1.4",
  "CCND1|Proliferation|0.6|1.4",
  "CDK4|Proliferation|0.6|1.4",
];

const SAMPLE_SPECS = [
  "Control-01|Control",
  "Control-02|Control",
  "Control-03|Control",
  "Control-04|Control",
  "Control-05|Control",
  "Control-06|Control",
  "Treated-01|Treated",
  "Treated-02|Treated",
  "Treated-03|Treated",
  "Treated-04|Treated",
  "Treated-05|Treated",
  "Treated-06|Treated",
];

let lcgState = 42 >>> 0;
const geneOffsets = GENE_SPECS.map(() => {
  lcgState = (lcgState * 1664525 + 1013904223) >>> 0;
  return ((lcgState / 4294967296) * 2 - 1) * 0.25;
});
const sampleBatches = SAMPLE_SPECS.map(() => {
  lcgState = (lcgState * 1664525 + 1013904223) >>> 0;
  return ((lcgState / 4294967296) * 2 - 1) * 0.3;
});

const data: Record<string, string | number>[] = [];
for (let i = 0; i < GENE_SPECS.length; i++) {
  const [gene, pathway, ctrlStr, trtStr] = GENE_SPECS[i].split("|");
  const ctrlBase = Number(ctrlStr);
  const trtBase = Number(trtStr);
  for (let j = 0; j < SAMPLE_SPECS.length; j++) {
    const [sample, condition] = SAMPLE_SPECS[j].split("|");
    lcgState = (lcgState * 1664525 + 1013904223) >>> 0;
    const cellNoise = ((lcgState / 4294967296) * 2 - 1) * 0.35;
    const base = condition === "Control" ? ctrlBase : trtBase;
    const val = Number((base + geneOffsets[i] + sampleBatches[j] + cellNoise).toFixed(4));
    data.push({
      [GENE]: gene,
      [PATHWAY]: pathway,
      [SAMPLE]: sample,
      [CONDITION]: condition,
      [LOG2_FC]: val,
    });
  }
}

// Plot: reads only data and the constants above
const genes = Array.from(new Set(data.map((r) => String(r[GENE]))));
const samples = Array.from(new Set(data.map((r) => String(r[SAMPLE]))));
const conditions = Array.from(new Set(data.map((r) => String(r[CONDITION]))));
const pathways = Array.from(new Set(data.map((r) => String(r[PATHWAY]))));

const usedPaletteColors = new Set<string>([t.div[0].toUpperCase(), t.div[2].toUpperCase()]);
const conditionColorMap = new Map<string, string>();
conditions.forEach((c, idx) => {
  const col = t.palette[idx];
  conditionColorMap.set(c, col);
  usedPaletteColors.add(col.toUpperCase());
});
const availablePathwayColors = t.palette.filter((col) => !usedPaletteColors.has(col.toUpperCase()));
const pathwayColorMap = new Map<string, string>();
pathways.forEach((p, idx) => {
  pathwayColorMap.set(p, availablePathwayColors[idx]);
});

const geneToPathway = new Map<string, string>();
const sampleToCondition = new Map<string, string>();
const valLookup = new Map<string, number>();
for (const r of data) {
  const g = String(r[GENE]);
  const s = String(r[SAMPLE]);
  geneToPathway.set(g, String(r[PATHWAY]));
  sampleToCondition.set(s, String(r[CONDITION]));
  valLookup.set(`${g}|${s}`, Number(r[LOG2_FC]));
}

const rowVectors = genes.map((g) => samples.map((s) => valLookup.get(`${g}|${s}`)!));
const colVectors = samples.map((s) => genes.map((g) => valLookup.get(`${g}|${s}`)!));

const allAbsVals = data.map((r) => Math.abs(Number(r[LOG2_FC])));
const colorDomain = Math.ceil(Math.max(...allAbsVals) * 10) / 10;

type ClusterNode = {
  id: number;
  height: number;
  leaves: number[];
  leftId: number | null;
  rightId: number | null;
  pos: number;
  centroid: number[];
  size: number;
};

type DendroSeg = { p1: number; d1: number; p2: number; d2: number };

const clusterTargets = [
  { vectors: rowVectors, orderOut: [] as number[], segsOut: [] as DendroSeg[], maxHeight: 0 },
  { vectors: colVectors, orderOut: [] as number[], segsOut: [] as DendroSeg[], maxHeight: 0 },
];

for (const target of clusterTargets) {
  const vecs = target.vectors;
  const allNodes: ClusterNode[] = vecs.map((v, i) => ({
    id: i,
    height: 0,
    leaves: [i],
    leftId: null,
    rightId: null,
    pos: 0,
    centroid: v.slice(),
    size: 1,
  }));
  const activeIds = vecs.map((_, i) => i);

  while (activeIds.length > 1) {
    let minCost = Infinity;
    let bestAIdx = 0;
    let bestBIdx = 1;
    for (let i = 0; i < activeIds.length; i++) {
      for (let j = i + 1; j < activeIds.length; j++) {
        const nodeA = allNodes[activeIds[i]];
        const nodeB = allNodes[activeIds[j]];
        let sqDist = 0;
        for (let k = 0; k < nodeA.centroid.length; k++) {
          const diff = nodeA.centroid[k] - nodeB.centroid[k];
          sqDist += diff * diff;
        }
        const cost = ((nodeA.size * nodeB.size) / (nodeA.size + nodeB.size)) * sqDist;
        if (cost < minCost) {
          minCost = cost;
          bestAIdx = i;
          bestBIdx = j;
        }
      }
    }
    const idA = activeIds[bestAIdx];
    const idB = activeIds[bestBIdx];
    const nodeA = allNodes[idA];
    const nodeB = allNodes[idB];
    const mergedSize = nodeA.size + nodeB.size;
    const mergedCentroid = nodeA.centroid.map(
      (v, k) => (v * nodeA.size + nodeB.centroid[k] * nodeB.size) / mergedSize,
    );
    const newId = allNodes.length;
    allNodes.push({
      id: newId,
      height: Math.sqrt(minCost),
      leaves: [...nodeA.leaves, ...nodeB.leaves],
      leftId: idA,
      rightId: idB,
      pos: 0,
      centroid: mergedCentroid,
      size: mergedSize,
    });
    activeIds.splice(bestBIdx, 1);
    activeIds.splice(bestAIdx, 1);
    activeIds.push(newId);
  }

  const rootNode = allNodes[activeIds[0]];
  target.maxHeight = rootNode.height;

  const stack = [rootNode.id];
  while (stack.length > 0) {
    const curr = allNodes[stack.pop()!];
    if (curr.leftId === null || curr.rightId === null) {
      target.orderOut.push(curr.leaves[0]);
    } else {
      stack.push(curr.rightId);
      stack.push(curr.leftId);
    }
  }

  const posByLeaf = new Map<number, number>();
  target.orderOut.forEach((leafIdx, pos) => {
    posByLeaf.set(leafIdx, pos);
  });

  for (const node of allNodes) {
    if (node.leftId === null || node.rightId === null) {
      node.pos = posByLeaf.get(node.leaves[0])!;
    } else {
      node.pos = (allNodes[node.leftId].pos + allNodes[node.rightId].pos) / 2;
      const lNode = allNodes[node.leftId];
      const rNode = allNodes[node.rightId];
      target.segsOut.push(
        { p1: lNode.pos, d1: node.height, p2: rNode.pos, d2: node.height },
        { p1: lNode.pos, d1: lNode.height, p2: lNode.pos, d2: node.height },
        { p1: rNode.pos, d1: rNode.height, p2: rNode.pos, d2: node.height },
      );
    }
  }
}

const rowOrder = clusterTargets[0].orderOut;
const rowSegments = clusterTargets[0].segsOut;
const rowMaxHeight = clusterTargets[0].maxHeight;

const colOrder = clusterTargets[1].orderOut;
const colSegments = clusterTargets[1].segsOut;
const colMaxHeight = clusterTargets[1].maxHeight;

const orderedGeneLabels = rowOrder.map((i) => genes[i]);
const orderedSampleLabels = colOrder.map((j) => samples[j]);

const divStopInts = t.div.map((hex) => parseInt(hex.slice(1), 16));
const divStopsRgb: [number, number, number][] = divStopInts.map((v) => [
  (v >> 16) & 255,
  (v >> 8) & 255,
  v & 255,
]);

const cells: { id: string; x: string; y: string; fill: string }[] = [];
for (let pr = 0; pr < orderedGeneLabels.length; pr++) {
  for (let pc = 0; pc < orderedSampleLabels.length; pc++) {
    const gLabel = orderedGeneLabels[pr];
    const sLabel = orderedSampleLabels[pc];
    const value = valLookup.get(`${gLabel}|${sLabel}`);
    if (value === undefined) continue;
    const pos = Math.min(1, Math.max(0, (value + colorDomain) / (2 * colorDomain)));
    const isLowerHalf = pos < 0.5;
    const start = isLowerHalf ? divStopsRgb[0] : divStopsRgb[1];
    const end = isLowerHalf ? divStopsRgb[1] : divStopsRgb[2];
    const localRatio = isLowerHalf ? pos / 0.5 : (pos - 0.5) / 0.5;
    const r = Math.round(start[0] + (end[0] - start[0]) * localRatio);
    const g = Math.round(start[1] + (end[1] - start[1]) * localRatio);
    const b = Math.round(start[2] + (end[2] - start[2]) * localRatio);
    cells.push({
      id: `${gLabel}-${sLabel}`,
      x: sLabel,
      y: gLabel,
      fill: `rgb(${r}, ${g}, ${b})`,
    });
  }
}

const colorbarTicks = [
  -colorDomain,
  Number((-colorDomain / 2).toFixed(1)),
  0,
  Number((colorDomain / 2).toFixed(1)),
  colorDomain,
];

function ClusteredOverlay() {
  const xScale = useXScale() as unknown as ((v: string) => number) & { bandwidth: () => number };
  const yScale = useYScale() as unknown as ((v: string) => number) & { bandwidth: () => number };
  const drawingArea = useDrawingArea();

  const bw = xScale.bandwidth();
  const bh = yScale.bandwidth();

  const nCols = orderedSampleLabels.length;
  const nRows = orderedGeneLabels.length;
  const colStep = drawingArea.width / nCols;
  const rowStep = drawingArea.height / nRows;

  const colDendroYBottom = drawingArea.top - ANNOT_H - 10;
  const colDendroYTop = HEADER_H + 8;

  const rowDendroXLeft = ROW_DENDRO_LEFT;
  const rowDendroXRight = ROW_DENDRO_LEFT + ROW_DENDRO_W;
  const rowStripLeft = rowDendroXRight + 8;

  const stripTop = drawingArea.top - ANNOT_H - 4;

  const cbX = drawingArea.left + drawingArea.width + 28;
  const cbW = 18;
  const cbTop = drawingArea.top + drawingArea.height * 0.25;
  const cbH = drawingArea.height * 0.52;

  const legX = drawingArea.left + drawingArea.width + 18;
  const legY = HEADER_H + 6;
  const pwStartY = legY + 22 + conditions.length * 22 + 14;

  return (
    <g>
      <defs>
        <linearGradient id="clusteredHeatmapDivGrad" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.div[0]} />
          <stop offset="50%" stopColor={t.div[1]} />
          <stop offset="100%" stopColor={t.div[2]} />
        </linearGradient>
      </defs>

      {/* Heatmap cells */}
      {cells.map((cell) => (
        <rect
          key={cell.id}
          x={xScale(cell.x)}
          y={yScale(cell.y)}
          width={bw}
          height={bh}
          fill={cell.fill}
        />
      ))}

      {/* Sample condition annotation strip */}
      {orderedSampleLabels.map((sLabel, pos) => {
        const cond = sampleToCondition.get(sLabel)!;
        const cx = drawingArea.left + colStep * (pos + 0.5);
        return (
          <rect
            key={`col-strip-${sLabel}`}
            x={cx - colStep / 2}
            y={stripTop}
            width={colStep}
            height={ANNOT_H}
            fill={conditionColorMap.get(cond)}
          />
        );
      })}

      {/* Gene pathway annotation strip */}
      {orderedGeneLabels.map((gLabel, pos) => {
        const pathway = geneToPathway.get(gLabel)!;
        const cy = drawingArea.top + rowStep * (pos + 0.5);
        return (
          <rect
            key={`row-strip-${gLabel}`}
            x={rowStripLeft}
            y={cy - rowStep / 2}
            width={ROW_ANNOT_W}
            height={rowStep}
            fill={pathwayColorMap.get(pathway)}
          />
        );
      })}

      {/* Column dendrogram (samples) */}
      {colSegments.map((s, i) => {
        const x1 = drawingArea.left + colStep * (s.p1 + 0.5);
        const x2 = drawingArea.left + colStep * (s.p2 + 0.5);
        const y1 = colDendroYBottom - (s.d1 / colMaxHeight) * (colDendroYBottom - colDendroYTop);
        const y2 = colDendroYBottom - (s.d2 / colMaxHeight) * (colDendroYBottom - colDendroYTop);
        return (
          <line
            key={`col-seg-${i}`}
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke={t.ink}
            strokeWidth={1.5}
            strokeLinecap="round"
          />
        );
      })}

      {/* Row dendrogram (genes) */}
      {rowSegments.map((s, i) => {
        const x1 = rowDendroXRight - (s.d1 / rowMaxHeight) * (rowDendroXRight - rowDendroXLeft);
        const x2 = rowDendroXRight - (s.d2 / rowMaxHeight) * (rowDendroXRight - rowDendroXLeft);
        const y1 = drawingArea.top + rowStep * (s.p1 + 0.5);
        const y2 = drawingArea.top + rowStep * (s.p2 + 0.5);
        return (
          <line
            key={`row-seg-${i}`}
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke={t.ink}
            strokeWidth={1.5}
            strokeLinecap="round"
          />
        );
      })}

      {/* Condition & Pathway legend with square swatches and section titles */}
      <text x={legX} y={legY} fontSize={14} fontWeight={600} fill={t.ink} dominantBaseline="central">
        {CONDITION}
      </text>
      {conditions.map((cond, idx) => {
        const cy = legY + 22 + idx * 22;
        return (
          <g key={`cond-leg-${cond}`}>
            <rect x={legX} y={cy - 6} width={12} height={12} rx={2} fill={conditionColorMap.get(cond)} />
            <text
              x={legX + 18}
              y={cy}
              fontSize={14}
              fill={t.inkSoft}
              dominantBaseline="central"
            >
              {cond}
            </text>
          </g>
        );
      })}
      <text x={legX} y={pwStartY} fontSize={14} fontWeight={600} fill={t.ink} dominantBaseline="central">
        {PATHWAY}
      </text>
      {pathways.map((pw, idx) => {
        const py = pwStartY + 22 + idx * 22;
        return (
          <g key={`pw-leg-${pw}`}>
            <rect x={legX} y={py - 6} width={12} height={12} rx={2} fill={pathwayColorMap.get(pw)} />
            <text x={legX + 18} y={py} fontSize={14} fill={t.inkSoft} dominantBaseline="central">
              {pw}
            </text>
          </g>
        );
      })}

      {/* Diverging colorbar */}
      <rect x={cbX} y={cbTop} width={cbW} height={cbH} fill="url(#clusteredHeatmapDivGrad)" rx={3} />
      {colorbarTicks.map((tick) => {
        const ty = cbTop + cbH * (1 - (tick + colorDomain) / (2 * colorDomain));
        return (
          <g key={tick}>
            <line x1={cbX + cbW} y1={ty} x2={cbX + cbW + 6} y2={ty} stroke={t.inkSoft} strokeWidth={1} />
            <text
              x={cbX + cbW + 10}
              y={ty}
              fontSize={14}
              fill={t.inkSoft}
              dominantBaseline="central"
            >
              {tick.toFixed(1)}
            </text>
          </g>
        );
      })}
      <text
        x={cbX + cbW + 64}
        y={cbTop + cbH / 2}
        fontSize={14}
        fill={t.inkSoft}
        textAnchor="middle"
        transform={`rotate(-90, ${cbX + cbW + 64}, ${cbTop + cbH / 2})`}
      >
        {LOG2_FC}
      </text>
    </g>
  );
}

export default function Chart() {
  const subtitle = `Ward hierarchical clustering of ${LOG2_FC} (${orderedGeneLabels.length} ${GENE}s × ${orderedSampleLabels.length} ${SAMPLE}s)`;

  return (
    <ChartsContainer
      width={SIZE.width}
      height={SIZE.height}
      series={[]}
      margin={MARGIN}
      skipAnimation
      xAxis={[
        {
          scaleType: "band",
          data: orderedSampleLabels,
          height: X_AXIS_HEIGHT,
          categoryGapRatio: 0.1,
          disableLine: true,
          disableTicks: true,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft, angle: -45, textAnchor: "end" },
        },
      ]}
      yAxis={[
        {
          scaleType: "band",
          data: orderedGeneLabels,
          width: Y_AXIS_WIDTH,
          categoryGapRatio: 0.1,
          disableLine: true,
          disableTicks: true,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        },
      ]}
    >
      <ClusteredOverlay />
      <ChartsXAxis />
      <ChartsYAxis />
      <text
        x={SIZE.width / 2}
        y={34}
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
        textAnchor="middle"
      >
        {TITLE}
      </text>
      <text
        x={SIZE.width / 2}
        y={60}
        fontSize={15}
        fill={t.inkSoft}
        textAnchor="middle"
      >
        {subtitle}
      </text>
    </ChartsContainer>
  );
}
