// anyplot.ai
// tree-phylogenetic: Phylogenetic Tree Diagram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-09
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const HIGHLIGHT_CLADE = "homininae";
const TITLE_HEIGHT = 64;
const MARGIN = { top: 24, right: 230, bottom: 90, left: 110 };
const PARENT_COL = "Parent Node";
const CLADE_COL = "Clade";

// Columns: set these to your data's column names
const NEWICK_STRING =
  "(((Human:0.02,Chimpanzee:0.021):0.03,Gorilla:0.04)homininae:0.06,(Orangutan:0.05,(Gibbon:0.07,(Rhesus Macaque:0.09,(Marmoset:0.15,Lemur:0.20):0.05):0.04):0.03):0.02);"; // role: newick_string
const SPECIES_NAMES = "Species / Node"; // role: species_names
const BRANCH_LENGTHS = "Evolutionary distance (substitutions per site)"; // role: branch_lengths

// Data: replace this block with your own records
const data: Array<Record<string, string | number>> = [
  { [SPECIES_NAMES]: "root", [PARENT_COL]: "", [BRANCH_LENGTHS]: 0, [CLADE_COL]: "", newick: NEWICK_STRING },
  { [SPECIES_NAMES]: "homininae", [PARENT_COL]: "root", [BRANCH_LENGTHS]: 0.06, [CLADE_COL]: "homininae" },
  { [SPECIES_NAMES]: "hominini", [PARENT_COL]: "homininae", [BRANCH_LENGTHS]: 0.03, [CLADE_COL]: "homininae" },
  { [SPECIES_NAMES]: "Human", [PARENT_COL]: "hominini", [BRANCH_LENGTHS]: 0.02, [CLADE_COL]: "homininae" },
  { [SPECIES_NAMES]: "Chimpanzee", [PARENT_COL]: "hominini", [BRANCH_LENGTHS]: 0.021, [CLADE_COL]: "homininae" },
  { [SPECIES_NAMES]: "Gorilla", [PARENT_COL]: "homininae", [BRANCH_LENGTHS]: 0.04, [CLADE_COL]: "homininae" },
  { [SPECIES_NAMES]: "non-homininae", [PARENT_COL]: "root", [BRANCH_LENGTHS]: 0.02, [CLADE_COL]: "other" },
  { [SPECIES_NAMES]: "Orangutan", [PARENT_COL]: "non-homininae", [BRANCH_LENGTHS]: 0.05, [CLADE_COL]: "other" },
  { [SPECIES_NAMES]: "catarrhini-other", [PARENT_COL]: "non-homininae", [BRANCH_LENGTHS]: 0.03, [CLADE_COL]: "other" },
  { [SPECIES_NAMES]: "Gibbon", [PARENT_COL]: "catarrhini-other", [BRANCH_LENGTHS]: 0.07, [CLADE_COL]: "other" },
  { [SPECIES_NAMES]: "monkey-lemur", [PARENT_COL]: "catarrhini-other", [BRANCH_LENGTHS]: 0.04, [CLADE_COL]: "other" },
  { [SPECIES_NAMES]: "Rhesus Macaque", [PARENT_COL]: "monkey-lemur", [BRANCH_LENGTHS]: 0.09, [CLADE_COL]: "other" },
  { [SPECIES_NAMES]: "platyrrhini-strepsirrhini", [PARENT_COL]: "monkey-lemur", [BRANCH_LENGTHS]: 0.05, [CLADE_COL]: "other" },
  { [SPECIES_NAMES]: "Marmoset", [PARENT_COL]: "platyrrhini-strepsirrhini", [BRANCH_LENGTHS]: 0.15, [CLADE_COL]: "other" },
  { [SPECIES_NAMES]: "Lemur", [PARENT_COL]: "platyrrhini-strepsirrhini", [BRANCH_LENGTHS]: 0.2, [CLADE_COL]: "other" },
];

// Plot: reads only data and the constants above
const nodes = data.map((row) => ({
  id: String(row[SPECIES_NAMES]),
  parent: String(row[PARENT_COL]),
  length: Number(row[BRANCH_LENGTHS]),
  clade: String(row[CLADE_COL]),
  x: 0,
  y: 0,
  isLeaf: false,
}));

const nodeById: Record<string, (typeof nodes)[number]> = {};
for (const n of nodes) {
  nodeById[n.id] = n;
}

const root = nodes.find((n) => !n.parent)!;
const preOrder: Array<(typeof nodes)[number]> = [];
const stack = [root];
while (stack.length > 0) {
  const cur = stack.pop()!;
  if (cur.parent) {
    const p = nodeById[cur.parent];
    cur.x = p.x + cur.length;
    if (!cur.clade) cur.clade = p.clade;
  }
  preOrder.push(cur);
  const kids = nodes.filter((n) => n.parent === cur.id);
  cur.isLeaf = kids.length === 0;
  for (let i = kids.length - 1; i >= 0; i--) {
    stack.push(kids[i]);
  }
}

let nextLeafSlot = 0;
const leaves: Array<{ name: string; x: number; y: number; clade: string }> = [];
for (const n of preOrder) {
  if (n.isLeaf) {
    n.y = nextLeafSlot;
    nextLeafSlot += 1;
    leaves.push({ name: n.id, x: n.x, y: n.y, clade: n.clade });
  }
}

const branches: Array<{
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  clade: string;
}> = [];

for (let idx = preOrder.length - 1; idx >= 0; idx--) {
  const n = preOrder[idx];
  const kids = nodes.filter((k) => k.parent === n.id);
  if (kids.length === 0) continue;
  for (const child of kids) {
    branches.push({
      x1: n.x,
      y1: child.y,
      x2: child.x,
      y2: child.y,
      clade: child.clade || n.clade,
    });
  }
  const childYs = kids.map((c) => c.y);
  const minChildY = Math.min(...childYs);
  const maxChildY = Math.max(...childYs);
  n.y = (minChildY + maxChildY) / 2;
  branches.push({
    x1: n.x,
    y1: minChildY,
    x2: n.x,
    y2: maxChildY,
    clade: n.clade,
  });
}

const maxDistance = Math.max(...leaves.map((leaf) => leaf.x));
const xDomainMax = maxDistance * 1.1;
const leafCount = leaves.length;

const cladeLeaves = leaves.filter((leaf) => leaf.clade === HIGHLIGHT_CLADE);
const otherLeaves = leaves.filter((leaf) => leaf.clade !== HIGHLIGHT_CLADE);
const cladeRootNode = nodes.find((n) => n.id === HIGHLIGHT_CLADE)!;
const cladeOriginX = cladeRootNode.x;
const cladeMinY = Math.min(...cladeLeaves.map((l) => l.y));
const cladeMaxY = Math.max(...cladeLeaves.map((l) => l.y));
const cladeLabelY = (cladeMinY + cladeMaxY) / 2;

function BranchLayer() {
  const { left, top, width: gW, height: gH } = useDrawingArea();
  const xScale = useXScale("distance") as (v: number) => number;
  const yScale = useYScale("leaf") as (v: number) => number;

  return (
    <g>
      <rect
        x={left}
        y={top}
        width={gW}
        height={gH}
        fill={t.inkSoft}
        opacity={0.03}
        rx={4}
      />
      {branches.map((b, i) => (
        <line
          key={i}
          x1={xScale(b.x1)}
          y1={yScale(b.y1)}
          x2={xScale(b.x2)}
          y2={yScale(b.y2)}
          stroke={b.clade === HIGHLIGHT_CLADE ? t.palette[2] : t.palette[0]}
          strokeWidth={b.clade === HIGHLIGHT_CLADE ? 4 : 3}
          strokeLinecap="round"
        />
      ))}
      {leaves.map((leaf) => (
        <text
          key={leaf.name}
          x={xScale(leaf.x) + 16}
          y={yScale(leaf.y)}
          dominantBaseline="middle"
          textAnchor="start"
          fontSize={16}
          fill={t.ink}
        >
          {leaf.name}
        </text>
      ))}
      <text
        x={xScale(cladeOriginX) - 12}
        y={yScale(cladeLabelY)}
        dominantBaseline="middle"
        textAnchor="end"
        fontSize={14}
        fontStyle="italic"
        fontWeight={600}
        fill={t.palette[2]}
      >
        African apes (Homininae)
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        Primate Mitochondrial DNA Phylogeny · tree-phylogenetic · javascript · muix · anyplot.ai
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_HEIGHT}
        margin={MARGIN}
        xAxis={[
          {
            id: "distance",
            scaleType: "linear",
            min: 0,
            max: xDomainMax,
            height: 60,
            label: BRANCH_LENGTHS,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "leaf",
            scaleType: "linear",
            min: -0.6,
            max: leafCount - 0.4,
            reverse: true,
            position: "none",
          },
        ]}
        series={[
          {
            type: "scatter",
            id: "leaves",
            data: otherLeaves.map((leaf, i) => ({
              x: leaf.x,
              y: leaf.y,
              id: `leaf-${i}`,
            })),
            color: t.palette[0],
            markerSize: 8,
          },
          {
            type: "scatter",
            id: "clade-leaves",
            data: cladeLeaves.map((leaf, i) => ({
              x: leaf.x,
              y: leaf.y,
              id: `clade-leaf-${i}`,
            })),
            color: t.palette[2],
            markerSize: 8,
          },
        ]}
      >
        <BranchLayer />
        <ScatterPlot skipAnimation />
        <ChartsXAxis axisId="distance" />
      </ChartsContainer>
    </div>
  );
}
