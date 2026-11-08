// anyplot.ai
// heatmap-adjacency: Network Adjacency Matrix Heatmap
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05
//# anyplot-orientation: square
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "heatmap-adjacency · javascript · muix · anyplot.ai";
const TITLE_H = 96;
const LEGEND_W = 150;
const X_AXIS_H = 34;
const Y_AXIS_W = 64;
const TEAM_LABEL_H = 44;

// Columns: set these to your data's column names
const SOURCE = "Source"; // role: source
const TARGET = "Target"; // role: target
const WEIGHT = "Shared threads per month"; // role: weight
const SOURCE_TEAM = "Source team"; // role: extra
const TARGET_TEAM = "Target team"; // role: extra

// Data: replace this block with your own records, one object per row
// Undirected collaboration network of 20 people in four teams: same-team pairs link often and
// strongly, cross-team pairs rarely and weakly; one row per linked pair
const data = (() => {
  let s = 42 >>> 0;
  const random = () => {
    s = (Math.imul(1664525, s) + 1013904223) >>> 0;
    return s / 4294967295;
  };
  const teams = [
    { name: "Engineering", members: ["Ava", "Noah", "Mia", "Liam", "Zoe"] },
    { name: "Design", members: ["Ivy", "Theo", "Nora", "Omar", "Luca"] },
    { name: "Product", members: ["Maya", "Eli", "Ruby", "Finn", "Sara"] },
    { name: "Marketing", members: ["Nina", "Cole", "Ana", "Drew", "Wes"] },
  ];
  const people = teams.flatMap((team) => team.members.map((name) => ({ name, team: team.name })));
  const rows: Record<string, string | number>[] = [];
  people.forEach((a, i) => {
    people.slice(i + 1).forEach((b) => {
      const sameTeam = a.team === b.team;
      const linkRoll = random();
      let weight = 0;
      if (sameTeam && linkRoll < 0.85) weight = Math.round(35 + random() * 65);
      else if (!sameTeam && linkRoll < 0.22) weight = Math.round(5 + random() * 30);
      if (weight > 0) {
        rows.push({ [SOURCE]: a.name, [TARGET]: b.name, [WEIGHT]: weight, [SOURCE_TEAM]: a.team, [TARGET_TEAM]: b.team });
      }
    });
  });
  return rows;
})();

// Plot: reads only data and the constants above
const edges = data.filter((d) => Number.isFinite(Number(d[WEIGHT])));

// Nodes from both endpoint columns (first appearance in the source column, then the target column),
// grouped by team to expose the blocks along the diagonal
const teamOf = new Map<string, string>();
edges.forEach((d) => teamOf.set(String(d[SOURCE]), String(d[SOURCE_TEAM])));
edges.forEach((d) => teamOf.set(String(d[TARGET]), String(d[TARGET_TEAM])));
const teams = [...new Set([...teamOf.values()])];
const nodes = teams.flatMap((team) => [...teamOf.keys()].filter((name) => teamOf.get(name) === team));

// Undirected graph: each pair fills both triangles; an absent pair keeps no entry
const weightOf = new Map<string, number>();
edges.forEach((d) => {
  weightOf.set(`${d[SOURCE]}|${d[TARGET]}`, Number(d[WEIGHT]));
  weightOf.set(`${d[TARGET]}|${d[SOURCE]}`, Number(d[WEIGHT]));
});
const cells = nodes.flatMap((row) =>
  nodes.map((col) => ({ key: `${row}|${col}`, row, col, weight: weightOf.get(`${row}|${col}`) })),
);
const minWeight = Math.min(...weightOf.values());
const maxWeight = Math.max(...weightOf.values());

// Team blocks along the diagonal: first and last node of each team
const blocks = teams.map((team) => {
  const members = nodes.filter((name) => teamOf.get(name) === team);
  return { team, first: members[0], last: members[members.length - 1] };
});
const strongest = edges.filter((d) => Number(d[WEIGHT]) === maxWeight);
const subtitle = `${nodes.length} nodes in ${teams.length} teams · ${edges.length} undirected links, both triangles filled · outlined: strongest link (${maxWeight}), ${strongest.map((d) => `${d[SOURCE]}–${d[TARGET]}`).join(", ")}`;

function AdjacencyLayer() {
  const xScale = useXScale() as unknown as ((v: string) => number) & { bandwidth: () => number; step: () => number };
  const yScale = useYScale() as unknown as ((v: string) => number) & { bandwidth: () => number; step: () => number };
  const colorScale = useZColorScale() as unknown as (v: number) => string;
  const { left, top, width, height } = useDrawingArea();
  const cellW = xScale.bandwidth();
  const cellH = yScale.bandwidth();
  const halfGap = (xScale.step() - cellW) / 2;
  return (
    <g>
      {cells.map((c) => (
        <rect
          key={c.key}
          x={xScale(c.col)}
          y={yScale(c.row)}
          width={cellW}
          height={cellH}
          fill={c.weight === undefined ? t.elevatedBg : colorScale(c.weight)}
          stroke={c.weight === maxWeight ? t.ink : "none"}
          strokeWidth={c.weight === maxWeight ? 2.5 : 0}
        />
      ))}
      {blocks.slice(1).map((b) => (
        <g key={b.team}>
          <line
            x1={xScale(b.first) - halfGap}
            x2={xScale(b.first) - halfGap}
            y1={top}
            y2={top + height}
            stroke={t.inkSoft}
            strokeWidth={2}
          />
          <line
            x1={left}
            x2={left + width}
            y1={yScale(b.first) - halfGap}
            y2={yScale(b.first) - halfGap}
            stroke={t.inkSoft}
            strokeWidth={2}
          />
        </g>
      ))}
      {blocks.map((b) => (
        <text
          key={`label-${b.team}`}
          x={(xScale(b.first) + xScale(b.last) + cellW) / 2}
          y={top + height + 28}
          textAnchor="middle"
          fontSize={15}
          fontWeight={600}
          fill={t.inkSoft}
        >
          {b.team}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartW = width - LEGEND_W;
  const chartH = height - TITLE_H;
  // Equal px per node on both axes: the matrix is a square of the smaller available side
  const availW = chartW - 16 - Y_AXIS_W - 12;
  const availH = chartH - 8 - X_AXIS_H - TEAM_LABEL_H;
  const side = Math.min(availW, availH);
  return (
    <Box sx={{ width, height, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, pt: "20px", px: "24px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, mt: "6px", lineHeight: 1.35 }}>{subtitle}</Typography>
      </Box>
      <ChartsDataProvider
        width={chartW}
        height={chartH}
        series={[]}
        skipAnimation
        margin={{ top: 8, left: 16, right: 12 + availW - side, bottom: TEAM_LABEL_H + availH - side }}
        xAxis={[
          {
            scaleType: "band",
            data: nodes,
            position: "top",
            height: X_AXIS_H,
            categoryGapRatio: 0.06,
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: nodes,
            width: Y_AXIS_W,
            categoryGapRatio: 0.06,
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        zAxis={[{ colorMap: { type: "continuous", min: minWeight, max: maxWeight, color: [t.seq[0], t.seq[1]] } }]}
      >
        <ChartsWrapper
          legendPosition={{ vertical: "middle", horizontal: "end" }}
          legendDirection="vertical"
          sx={{ width, height: chartH }}
        >
          <Box
            sx={{
              gridArea: "legend",
              width: LEGEND_W,
              height: 520,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <Typography sx={{ fontSize: 15, color: t.ink, textAlign: "center", lineHeight: 1.3, maxWidth: 130, mb: "10px" }}>
              {WEIGHT}
            </Typography>
            <ContinuousColorLegend
              direction="vertical"
              thickness={20}
              labelPosition="end"
              sx={{ flex: 1, color: t.inkSoft, fontSize: 14 }}
            />
          </Box>
          <ChartsSurface>
            <AdjacencyLayer />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
