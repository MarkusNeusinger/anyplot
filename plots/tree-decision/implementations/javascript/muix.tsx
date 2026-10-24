// anyplot.ai
// tree-decision: Decision Tree Visualization with Probabilities
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 95/100 | Created: 2026-08-26

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE_H = 66;
const MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";
const NODE_TITLES: Record<string, string> = {
  D0: "Launch Product?",
  C1: "Initial Demand",
  D1: "Expand Capacity?",
  D2: "Discount Price?",
  C2: "Sustained Demand",
};

// Columns: set these to your data's column names
const NODE_ID = "Node ID"; // role: node_id
const NODE_TYPE = "Node Type"; // role: node_type
const PARENT_ID = "Parent Node ID"; // role: parent_id
const BRANCH_LABEL = "Branch Label"; // role: branch_label
const PROBABILITY = "Branch Probability"; // role: probability
const PAYOFF = "Terminal Payoff ($K)"; // role: payoff

// Data: replace this block with your own records
const data: Array<Record<string, string | number | null>> = [
  { [NODE_ID]: "D0", [NODE_TYPE]: "decision", [PARENT_ID]: null, [BRANCH_LABEL]: "", [PROBABILITY]: null, [PAYOFF]: null },
  { [NODE_ID]: "C1", [NODE_TYPE]: "chance", [PARENT_ID]: "D0", [BRANCH_LABEL]: "Launch", [PROBABILITY]: null, [PAYOFF]: null },
  { [NODE_ID]: "T6", [NODE_TYPE]: "terminal", [PARENT_ID]: "D0", [BRANCH_LABEL]: "Don't Launch", [PROBABILITY]: null, [PAYOFF]: 0 },
  { [NODE_ID]: "D1", [NODE_TYPE]: "decision", [PARENT_ID]: "C1", [BRANCH_LABEL]: "High Demand", [PROBABILITY]: 0.6, [PAYOFF]: null },
  { [NODE_ID]: "D2", [NODE_TYPE]: "decision", [PARENT_ID]: "C1", [BRANCH_LABEL]: "Low Demand", [PROBABILITY]: 0.4, [PAYOFF]: null },
  { [NODE_ID]: "C2", [NODE_TYPE]: "chance", [PARENT_ID]: "D1", [BRANCH_LABEL]: "Expand", [PROBABILITY]: null, [PAYOFF]: null },
  { [NODE_ID]: "T3", [NODE_TYPE]: "terminal", [PARENT_ID]: "D1", [BRANCH_LABEL]: "Don't Expand", [PROBABILITY]: null, [PAYOFF]: 500 },
  { [NODE_ID]: "T4", [NODE_TYPE]: "terminal", [PARENT_ID]: "D2", [BRANCH_LABEL]: "Discount", [PROBABILITY]: null, [PAYOFF]: 150 },
  { [NODE_ID]: "T5", [NODE_TYPE]: "terminal", [PARENT_ID]: "D2", [BRANCH_LABEL]: "Hold Price", [PROBABILITY]: null, [PAYOFF]: 80 },
  { [NODE_ID]: "T1", [NODE_TYPE]: "terminal", [PARENT_ID]: "C2", [BRANCH_LABEL]: "High", [PROBABILITY]: 0.7, [PAYOFF]: 850 },
  { [NODE_ID]: "T2", [NODE_TYPE]: "terminal", [PARENT_ID]: "C2", [BRANCH_LABEL]: "Low", [PROBABILITY]: 0.3, [PAYOFF]: 200 },
];

// Plot: reads only data and the constants above
const treeNodes = data.map((row) => ({
  id: String(row[NODE_ID]),
  type: String(row[NODE_TYPE]) as "decision" | "chance" | "terminal",
  parent: row[PARENT_ID] ? String(row[PARENT_ID]) : null,
  title: NODE_TITLES[String(row[NODE_ID])] ?? String(row[NODE_ID]),
  branchLabel: String(row[BRANCH_LABEL] ?? ""),
  probability: row[PROBABILITY] != null ? Number(row[PROBABILITY]) : null,
  payoff: row[PAYOFF] != null ? Number(row[PAYOFF]) : 0,
  depth: 0,
  y: 0,
  emv: 0,
  pruned: false,
}));

const byId: Record<string, (typeof treeNodes)[number]> = {};
for (const n of treeNodes) {
  byId[n.id] = n;
}

for (const n of treeNodes) {
  let d = 0;
  let cur = n;
  while (cur.parent) {
    d += 1;
    cur = byId[cur.parent];
  }
  n.depth = d;
}

// Compute post-order traversal from root by DFS stack
const rootNode = treeNodes.find((n) => n.parent === null)!;
const preOrder: Array<(typeof treeNodes)[number]> = [];
const dfsStack = [rootNode];
while (dfsStack.length > 0) {
  const cur = dfsStack.pop()!;
  preOrder.push(cur);
  const kids = treeNodes.filter((n) => n.parent === cur.id);
  for (let i = kids.length - 1; i >= 0; i--) {
    dfsStack.push(kids[i]);
  }
}

// Assign sequential y to leaves in pre-order, then bottom-up average y and EMV rollback
let nextLeafY = 0;
for (const n of preOrder) {
  const kids = treeNodes.filter((k) => k.parent === n.id);
  if (kids.length === 0) {
    n.y = nextLeafY;
    nextLeafY += 1;
  }
}

for (let idx = preOrder.length - 1; idx >= 0; idx--) {
  const node = preOrder[idx];
  const kids = treeNodes.filter((k) => k.parent === node.id);
  if (kids.length === 0) {
    node.emv = node.payoff;
    continue;
  }
  const ys = kids.map((k) => k.y);
  node.y = (Math.min(...ys) + Math.max(...ys)) / 2;

  if (node.type === "chance") {
    node.emv = kids.reduce(
      (sum, k) => sum + (k.probability ?? 0) * k.emv,
      0,
    );
    for (const k of kids) k.pruned = false;
  } else {
    let bestIdx = 0;
    kids.forEach((k, i) => {
      if (k.emv > kids[bestIdx].emv) bestIdx = i;
    });
    node.emv = kids[bestIdx].emv;
    kids.forEach((k, i) => {
      k.pruned = i !== bestIdx;
    });
  }
}

const maxDepth = Math.max(...treeNodes.map((n) => n.depth));
const minY = Math.min(...treeNodes.map((n) => n.y));
const maxY = Math.max(...treeNodes.map((n) => n.y));
const xDomain = [-0.35, maxDepth + 0.85];
const yDomain = [minY - 0.65, maxY + 0.65];

function TreeEdges() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  return (
    <g>
      {treeNodes
        .filter((n) => n.parent !== null)
        .map((n) => {
          const parent = byId[n.parent!];
          const x1 = xs(parent.depth);
          const y1 = ys(parent.y);
          const x2 = xs(n.depth);
          const y2 = ys(n.y);
          const mx = (x1 + x2) / 2;
          const my = (y1 + y2) / 2;
          const angle = Math.atan2(y2 - y1, x2 - x1);
          const nx = -Math.sin(angle);
          const ny = Math.cos(angle);
          const lx = mx + nx * 16;
          const ly = my + ny * 16;
          const labelText =
            n.probability != null
              ? `${n.branchLabel} · p=${n.probability.toFixed(2)}`
              : n.branchLabel;
          return (
            <g key={n.id}>
              <line
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={n.pruned ? MUTED : t.inkSoft}
                strokeWidth={n.pruned ? 1.8 : 2.4}
                strokeDasharray={n.pruned ? "7 5" : undefined}
                strokeOpacity={n.pruned ? 0.55 : 0.9}
              />
              {n.pruned && (
                <g stroke={MUTED} strokeWidth={2} strokeOpacity={0.85}>
                  <line x1={mx - 7} y1={my - 7} x2={mx + 7} y2={my + 7} />
                  <line x1={mx - 7} y1={my + 7} x2={mx + 7} y2={my - 7} />
                </g>
              )}
              <text
                x={lx}
                y={ly}
                fontSize={14}
                fill={n.pruned ? MUTED : t.inkSoft}
                textAnchor="middle"
                dominantBaseline="middle"
              >
                {labelText}
              </text>
            </g>
          );
        })}
    </g>
  );
}

function TreeNodesAndLegend() {
  const { left, top } = useDrawingArea();
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  const legendItems = [
    { label: "Decision node", shape: "square", color: t.palette[0] },
    { label: "Chance node", shape: "circle", color: t.palette[1] },
    { label: "Terminal payoff", shape: "triangle", color: t.ink },
  ];

  return (
    <g>
      {treeNodes.map((n) => {
        const cx = xs(n.depth);
        const cy = ys(n.y);
        const dimmed = n.pruned;
        const s = 17;
        const w = 15;
        const h = 15;
        return (
          <g key={n.id} opacity={dimmed ? 0.5 : 1}>
            {n.type === "decision" && (
              <rect
                x={cx - s}
                y={cy - s}
                width={s * 2}
                height={s * 2}
                fill={t.palette[0]}
                stroke={t.pageBg}
                strokeWidth={2.5}
              />
            )}
            {n.type === "chance" && (
              <circle
                cx={cx}
                cy={cy}
                r={19}
                fill={t.palette[1]}
                stroke={t.pageBg}
                strokeWidth={2.5}
              />
            )}
            {n.type === "terminal" && (
              <polygon
                points={`${cx - w},${cy - h} ${cx - w},${cy + h} ${cx + w * 1.15},${cy}`}
                fill={t.elevatedBg}
                stroke={t.ink}
                strokeWidth={2}
              />
            )}

            {n.type !== "terminal" && (
              <>
                <text
                  x={cx}
                  y={cy - 32}
                  fontSize={15}
                  fontWeight={600}
                  fill={t.ink}
                  textAnchor="middle"
                >
                  {n.title}
                </text>
                <text
                  x={cx}
                  y={cy + 36}
                  fontSize={14}
                  fontWeight={600}
                  fill={t.inkSoft}
                  textAnchor="middle"
                >
                  {`EMV $${Math.round(n.emv)}K`}
                </text>
              </>
            )}
            {n.type === "terminal" && (
              <text
                x={cx + 26}
                y={cy}
                fontSize={15}
                fontWeight={600}
                fill={t.ink}
                dominantBaseline="middle"
              >
                {`$${Math.round(n.payoff)}K`}
              </text>
            )}
          </g>
        );
      })}

      <g transform={`translate(${left - 34}, ${top - 16})`}>
        {legendItems.map((item, i) => (
          <g key={item.label} transform={`translate(0, ${i * 28})`}>
            {item.shape === "square" && (
              <rect x={0} y={0} width={16} height={16} fill={item.color} />
            )}
            {item.shape === "circle" && (
              <circle cx={8} cy={8} r={8} fill={item.color} />
            )}
            {item.shape === "triangle" && (
              <polygon
                points="0,0 0,16 15,8"
                fill={t.elevatedBg}
                stroke={item.color}
                strokeWidth={2}
              />
            )}
            <text x={26} y={13} fontSize={14} fill={t.ink}>
              {item.label}
            </text>
          </g>
        ))}
        <g transform={`translate(0, ${legendItems.length * 28 + 6})`}>
          <line
            x1={0}
            y1={8}
            x2={16}
            y2={8}
            stroke={MUTED}
            strokeWidth={2}
            strokeDasharray="5 4"
          />
          <text x={26} y={13} fontSize={14} fill={t.ink}>
            Pruned branch
          </text>
        </g>
      </g>
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
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          Product Launch EMV Analysis · tree-decision · javascript · muix · anyplot.ai
        </span>
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H}
        series={[]}
        margin={{ top: 40, right: 110, bottom: 40, left: 60 }}
        xAxis={[
          {
            min: xDomain[0],
            max: xDomain[1],
            scaleType: "linear",
            position: "none",
          },
        ]}
        yAxis={[
          {
            min: yDomain[0],
            max: yDomain[1],
            scaleType: "linear",
            position: "none",
          },
        ]}
      >
        <TreeEdges />
        <TreeNodesAndLegend />
      </ChartsContainer>
    </div>
  );
}
