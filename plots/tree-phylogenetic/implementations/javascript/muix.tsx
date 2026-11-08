// anyplot.ai
// tree-phylogenetic: Phylogenetic Tree Diagram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-09
//# anyplot-orientation: square
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const DISTANCE_PAD = 0.03; // share of the longest root-to-tip distance added right of it
const SLOT_PAD = 0.6; // in tip slots: room above the first and below the last tip
const TITLE = "tree-phylogenetic · javascript · muix · anyplot.ai";
const TITLE_H = 80;
const LEGEND_H = 48;

// Columns: set these to your data's column names
const TAXON = "Taxon"; // role: species_names (tips carry the species, inner nodes an ancestor id)
const PARENT = "Parent"; // role: newick_string (the tree structure, one parent per node)
const BRANCH_LENGTH = "Branch length (substitutions per site)"; // role: branch_lengths
const CLADE = "Clade"; // role: extra

// Data: replace this block with your own records, one object per row
// Primate mitochondrial-DNA phylogeny, written as a Newick string and parsed
// into one row per node: its parent and the length of the branch above it.
const data = (() => {
  const newick =
    "(((((((Human:0.02,Chimpanzee:0.021):0.012,Gorilla:0.04):0.018,Orangutan:0.06):0.016,Gibbon:0.08):0.03,Rhesus Macaque:0.11):0.035,Marmoset:0.16):0.06,Lemur:0.24);";
  const cladeOf = {
    Human: "Apes",
    Chimpanzee: "Apes",
    Gorilla: "Apes",
    Orangutan: "Apes",
    Gibbon: "Apes",
    "Rhesus Macaque": "Old World monkeys",
    Marmoset: "New World monkeys",
    Lemur: "Strepsirrhines",
  };
  const rows = [];
  const addNode = (parent) => {
    const row = { [TAXON]: `ancestor-${rows.length}`, [PARENT]: parent ? parent[TAXON] : null, [BRANCH_LENGTH]: null, [CLADE]: null };
    rows.push(row);
    return row;
  };
  const open = [];
  let current = addNode(null);
  for (const token of newick.match(/[(),;]|:[^(),;]+|[^(),;:]+/g)) {
    if (token === "(") {
      open.push(current);
      current = addNode(current);
    } else if (token === ",") {
      current = addNode(open[open.length - 1]);
    } else if (token === ")") {
      current = open.pop();
    } else if (token.startsWith(":")) {
      current[BRANCH_LENGTH] = Number(token.slice(1));
    } else if (token !== ";") {
      const name = token.trim();
      rows.forEach((r) => {
        if (r[PARENT] === current[TAXON]) r[PARENT] = name;
      });
      current[TAXON] = name;
      current[CLADE] = cladeOf[name] ?? null;
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const byId = new Map(data.map((d) => [d[TAXON], d]));
const children = new Map(data.map((d) => [d[TAXON], []]));
data.forEach((d) => {
  if (d[PARENT] != null) children.get(d[PARENT])?.push(d[TAXON]);
});

// Depth-first order from the root(s): parents always come before their children
const preorder = [];
const stack = data.filter((d) => d[PARENT] == null).map((d) => d[TAXON]).reverse();
while (stack.length > 0) {
  const id = stack.pop();
  preorder.push(id);
  stack.push(...[...children.get(id)].reverse());
}

// x: cumulative branch length from the root, so every branch keeps its own length
const distance = new Map();
preorder.forEach((id) => {
  const row = byId.get(id);
  distance.set(id, row[PARENT] == null ? 0 : distance.get(row[PARENT]) + (row[BRANCH_LENGTH] ?? 0));
});

// y: one slot per tip in depth-first order; an inner node sits midway between
// its first and last child. A node belongs to a clade when every tip below it does.
const tips = preorder.filter((id) => children.get(id).length === 0);
const slot = new Map(tips.map((id, i) => [id, i]));
const nodeClade = new Map();
[...preorder].reverse().forEach((id) => {
  const kids = children.get(id);
  if (kids.length === 0) {
    nodeClade.set(id, byId.get(id)[CLADE] ?? null);
    return;
  }
  const kidSlots = kids.map((k) => slot.get(k));
  slot.set(id, (Math.min(...kidSlots) + Math.max(...kidSlots)) / 2);
  const kidClades = new Set(kids.map((k) => nodeClade.get(k)));
  nodeClade.set(id, kidClades.size === 1 ? [...kidClades][0] : null);
});

const clades = [...new Set(data.map((d) => d[CLADE]).filter((c) => c != null))];
const cladeColor = new Map(clades.map((c, i) => [c, t.palette[i]]));
// A branch spanning several clades (the backbone) stays in the neutral ink
const branchColor = new Map(preorder.map((id) => [id, cladeColor.get(nodeClade.get(id)) ?? t.inkSoft]));

const tipDistances = tips.map((id) => distance.get(id));
const maxDistance = Math.max(...tipDistances);
const tipPoints = new Map(tips.map((id) => [id, { id, x: distance.get(id), y: slot.get(id) }]));
const unassignedTips = tips.filter((id) => nodeClade.get(id) == null);
const tipSeries = [
  ...clades.map((c, i) => ({
    type: "scatter",
    id: `clade-${i}`,
    label: c,
    color: t.palette[i],
    markerSize: 6,
    data: tips.filter((id) => nodeClade.get(id) === c).map((id) => tipPoints.get(id)),
  })),
  ...(unassignedTips.length > 0
    ? [{ type: "scatter", id: "unassigned", label: "No clade", color: t.inkSoft, markerSize: 6, data: unassignedTips.map((id) => tipPoints.get(id)) }]
    : []),
];

const UNIT = BRANCH_LENGTH.match(/\(([^)]+)\)\s*$/)?.[1] ?? "";
const SUBTITLE = `${tips.length} species, ${clades.length} clades · root-to-tip distance ${Math.min(...tipDistances).toFixed(3)}–${maxDistance.toFixed(3)} ${UNIT}`;

// The community package has no tree component: a custom layer draws the
// right-angled branches and tip labels in the container's linear scales.
function PhyloBranches() {
  const xScale = useXScale();
  const yScale = useYScale();
  const inner = preorder.filter((id) => children.get(id).length > 0);
  const stems = preorder.filter((id) => byId.get(id)[PARENT] != null && distance.has(byId.get(id)[PARENT]));

  return (
    <g strokeLinecap="round">
      {inner.map((id) => {
        const kidSlots = children.get(id).map((k) => slot.get(k));
        return (
          <line
            key={`join-${id}`}
            x1={xScale(distance.get(id))}
            x2={xScale(distance.get(id))}
            y1={yScale(Math.min(...kidSlots))}
            y2={yScale(Math.max(...kidSlots))}
            stroke={branchColor.get(id)}
            strokeWidth={3}
          />
        );
      })}
      {stems.map((id) => (
        <line
          key={`stem-${id}`}
          x1={xScale(distance.get(byId.get(id)[PARENT]))}
          x2={xScale(distance.get(id))}
          y1={yScale(slot.get(id))}
          y2={yScale(slot.get(id))}
          stroke={branchColor.get(id)}
          strokeWidth={3}
        />
      ))}
      {tips.map((id) => (
        <text
          key={`label-${id}`}
          x={xScale(distance.get(id)) + 14}
          y={yScale(slot.get(id))}
          dominantBaseline="middle"
          fontSize={17}
          fill={t.ink}
        >
          {id}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "18px 36px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <ChartsDataProvider
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        series={tipSeries}
        margin={{ top: 24, right: 170, bottom: 24, left: 36 }}
        xAxis={[
          {
            id: "distance",
            scaleType: "linear",
            min: 0,
            max: maxDistance * (1 + DISTANCE_PAD),
            tickNumber: 6,
            label: BRANCH_LENGTH,
            height: 72,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          { id: "slot", scaleType: "linear", min: -SLOT_PAD, max: tips.length - 1 + SLOT_PAD, reverse: true, position: "none" },
        ]}
      >
        <ChartsWrapper legendPosition={{ horizontal: "start", vertical: "top" }} legendDirection="horizontal">
          <ChartsLegend sx={{ fontSize: 15, color: t.ink, px: "36px", height: LEGEND_H, alignItems: "center", gap: 3 }} />
          <ChartsSurface
            sx={{
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
              "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
            }}
          >
            <ChartsGrid vertical />
            <PhyloBranches />
            <ScatterPlot />
            <ChartsXAxis axisId="distance" />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
