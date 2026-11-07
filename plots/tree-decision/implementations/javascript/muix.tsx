// anyplot.ai
// tree-decision: Decision Tree Visualization with Probabilities
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 95/100 | Created: 2026-08-26

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const DECISION = "decision"; // the three node types of the spec, each drawn as its own shape
const CHANCE = "chance";
const TERMINAL = "terminal";
const DEPTH_PAD_LEFT = 0.3; // in depth steps: room left of the root for its question
const DEPTH_PAD_RIGHT = 0.7; // in depth steps: room right of the deepest terminals for their payoffs
const SLOT_PAD = 0.6; // in leaf slots: room above the first and below the last leaf
const NODE_R = 18; // half the side of a node mark, px
const EDGE_FONT = 15; // branch label size, px
const TITLE = "tree-decision · javascript · muix · anyplot.ai";
const TITLE_H = 76;
const LEGEND_H = 44;

// Columns: set these to your data's column names
const NODE_ID = "Node"; // role: node_id
const NODE_TYPE = "Node type"; // role: node_type
const PARENT_ID = "Parent"; // role: parent_id
const BRANCH_LABEL = "Branch"; // role: branch_label
const PROBABILITY = "Probability"; // role: probability
const PAYOFF = "Payoff (USD thousand)"; // role: payoff
const QUESTION = "Question"; // role: extra

// Data: replace this block with your own records, one object per row
// A two-stage product-launch decision: launch or not, then react to the
// demand that materialises. The parent of the root is null; probabilities
// sit on chance branches only and payoffs on terminal nodes only.
const data = [
  { [NODE_ID]: "D0", [NODE_TYPE]: "decision", [PARENT_ID]: null, [BRANCH_LABEL]: null, [PROBABILITY]: null, [PAYOFF]: null, [QUESTION]: "Launch product?" },
  { [NODE_ID]: "C1", [NODE_TYPE]: "chance", [PARENT_ID]: "D0", [BRANCH_LABEL]: "Launch", [PROBABILITY]: null, [PAYOFF]: null, [QUESTION]: "Initial demand" },
  { [NODE_ID]: "T6", [NODE_TYPE]: "terminal", [PARENT_ID]: "D0", [BRANCH_LABEL]: "Don't launch", [PROBABILITY]: null, [PAYOFF]: 0, [QUESTION]: null },
  { [NODE_ID]: "D1", [NODE_TYPE]: "decision", [PARENT_ID]: "C1", [BRANCH_LABEL]: "High demand", [PROBABILITY]: 0.6, [PAYOFF]: null, [QUESTION]: "Expand capacity?" },
  { [NODE_ID]: "D2", [NODE_TYPE]: "decision", [PARENT_ID]: "C1", [BRANCH_LABEL]: "Low demand", [PROBABILITY]: 0.4, [PAYOFF]: null, [QUESTION]: "Discount price?" },
  { [NODE_ID]: "C2", [NODE_TYPE]: "chance", [PARENT_ID]: "D1", [BRANCH_LABEL]: "Expand", [PROBABILITY]: null, [PAYOFF]: null, [QUESTION]: "Sustained demand" },
  { [NODE_ID]: "T3", [NODE_TYPE]: "terminal", [PARENT_ID]: "D1", [BRANCH_LABEL]: "Don't expand", [PROBABILITY]: null, [PAYOFF]: 500, [QUESTION]: null },
  { [NODE_ID]: "T4", [NODE_TYPE]: "terminal", [PARENT_ID]: "D2", [BRANCH_LABEL]: "Discount", [PROBABILITY]: null, [PAYOFF]: 150, [QUESTION]: null },
  { [NODE_ID]: "T5", [NODE_TYPE]: "terminal", [PARENT_ID]: "D2", [BRANCH_LABEL]: "Hold price", [PROBABILITY]: null, [PAYOFF]: 80, [QUESTION]: null },
  { [NODE_ID]: "T1", [NODE_TYPE]: "terminal", [PARENT_ID]: "C2", [BRANCH_LABEL]: "Demand holds", [PROBABILITY]: 0.7, [PAYOFF]: 850, [QUESTION]: null },
  { [NODE_ID]: "T2", [NODE_TYPE]: "terminal", [PARENT_ID]: "C2", [BRANCH_LABEL]: "Demand fades", [PROBABILITY]: 0.3, [PAYOFF]: 200, [QUESTION]: null },
];

// Plot: reads only data and the constants above
const byId = new Map(data.map((d) => [d[NODE_ID], d]));
const children = new Map(data.map((d) => [d[NODE_ID], []]));
data.forEach((d) => {
  if (d[PARENT_ID] != null) children.get(d[PARENT_ID])?.push(d[NODE_ID]);
});
const roots = data.filter((d) => d[PARENT_ID] == null).map((d) => d[NODE_ID]);

// Depth: the number of ancestors above a node
const depth = new Map(
  data.map((d) => {
    let steps = 0;
    let parent = d[PARENT_ID];
    while (parent != null && steps < data.length) {
      steps += 1;
      parent = byId.get(parent)?.[PARENT_ID] ?? null;
    }
    return [d[NODE_ID], steps];
  }),
);

// Leaves take one slot each in depth-first order; a parent sits midway between
// its first and last child, so subtrees never overlap.
const preorder = [];
const stack = [...roots].reverse();
while (stack.length > 0) {
  const id = stack.pop();
  preorder.push(id);
  stack.push(...[...children.get(id)].reverse());
}
const slot = new Map();
preorder
  .filter((id) => children.get(id).length === 0)
  .forEach((id, i) => slot.set(id, i));
const bottomUp = [...preorder].sort((a, b) => depth.get(b) - depth.get(a));

// EMV rollback, deepest nodes first: a terminal is worth its payoff, a chance
// node the probability-weighted mean of its branches, a decision node its best
// branch; every other branch of a decision is pruned. Pruning stays local to
// the decision that rejected the branch.
const emv = new Map();
const pruned = new Set();
bottomUp.forEach((id) => {
  const node = byId.get(id);
  const kids = children.get(id);
  if (kids.length > 0) {
    const kidSlots = kids.map((k) => slot.get(k));
    slot.set(id, (Math.min(...kidSlots) + Math.max(...kidSlots)) / 2);
  }
  if (kids.length === 0) {
    emv.set(id, node[PAYOFF]);
  } else if (node[NODE_TYPE] === CHANCE) {
    emv.set(id, kids.reduce((sum, k) => sum + byId.get(k)[PROBABILITY] * emv.get(k), 0));
  } else {
    const best = kids.reduce((b, k) => (emv.get(k) > emv.get(b) ? k : b), kids[0]);
    emv.set(id, emv.get(best));
    kids.filter((k) => k !== best).forEach((k) => pruned.add(k));
  }
});

const maxDepth = Math.max(...depth.values());
const slotCount = Math.max(...slot.values());
const formatValue = (v) => Math.round(v).toLocaleString("en-US");
const nodeTypes = [...new Set(data.map((d) => d[NODE_TYPE]))];
const typeColor = { [DECISION]: t.palette[0], [CHANCE]: t.palette[1] };
const PAYOFF_UNIT = PAYOFF.match(/\(([^)]+)\)\s*$/)?.[1] ?? "";
const terminalCount = data.filter((d) => children.get(d[NODE_ID]).length === 0).length;
const SUBTITLE = `${data.length} nodes, ${terminalCount} terminal payoffs · payoffs and EMV in ${PAYOFF_UNIT}, rolled back from the terminals · root EMV ${formatValue(emv.get(roots[0]))}`;

// The community package has no tree component: a custom layer draws edges,
// labels and node marks in the container's linear scales (depth by leaf slot).
function DecisionTree() {
  const xScale = useXScale();
  const yScale = useYScale();
  const edges = data.filter((d) => d[PARENT_ID] != null && byId.has(d[PARENT_ID]));

  return (
    <g>
      {edges.map((d) => {
        const id = d[NODE_ID];
        const x1 = xScale(depth.get(d[PARENT_ID]));
        const y1 = yScale(slot.get(d[PARENT_ID]));
        const x2 = xScale(depth.get(id));
        const y2 = yScale(slot.get(id));
        const mx = (x1 + x2) / 2;
        const my = (y1 + y2) / 2;
        const angle = Math.atan2(y2 - y1, x2 - x1);
        const [cos, sin] = [Math.cos(angle), Math.sin(angle)];
        const isPruned = pruned.has(id);
        const probability = d[PROBABILITY];
        const label = probability != null ? `${d[BRANCH_LABEL]} · p = ${probability.toFixed(2)}` : d[BRANCH_LABEL];
        // The label sits above a rising branch and below a falling one, pushed
        // out along the normal far enough that its horizontal box clears the line.
        const halfW = String(label).length * EDGE_FONT * 0.28;
        const offset = halfW * Math.abs(sin) + (EDGE_FONT / 2) * Math.abs(cos) + 8;
        const [nx, ny] = y2 <= y1 ? [sin, -cos] : [-sin, cos];
        return (
          <g key={`edge-${id}`}>
            <g opacity={isPruned ? 0.55 : 1}>
              <line
                x1={x1 + cos * NODE_R}
                y1={y1 + sin * NODE_R}
                x2={x2 - cos * NODE_R}
                y2={y2 - sin * NODE_R}
                stroke={t.inkSoft}
                strokeWidth={isPruned ? 1.8 : 2.6}
                strokeDasharray={isPruned ? "7 5" : undefined}
              />
              {isPruned && (
                <g stroke={t.ink} strokeWidth={2} transform={`rotate(25 ${mx} ${my})`}>
                  <line x1={mx - 4} y1={my - 9} x2={mx - 4} y2={my + 9} />
                  <line x1={mx + 4} y1={my - 9} x2={mx + 4} y2={my + 9} />
                </g>
              )}
            </g>
            <text
              x={mx + nx * offset}
              y={my + ny * offset}
              fontSize={EDGE_FONT}
              fill={isPruned ? t.inkSoft : t.ink}
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {label}
            </text>
          </g>
        );
      })}
      {data.map((d) => {
        const id = d[NODE_ID];
        const cx = xScale(depth.get(id));
        const cy = yScale(slot.get(id));
        const type = d[NODE_TYPE];
        const isLeaf = children.get(id).length === 0;
        return (
          <g key={`node-${id}`}>
            <g opacity={pruned.has(id) ? 0.55 : 1}>
              {type === DECISION && (
                <rect x={cx - NODE_R} y={cy - NODE_R} width={NODE_R * 2} height={NODE_R * 2} fill={typeColor[DECISION]} stroke={t.pageBg} strokeWidth={2.5} />
              )}
              {type === CHANCE && <circle cx={cx} cy={cy} r={NODE_R + 2} fill={typeColor[CHANCE]} stroke={t.pageBg} strokeWidth={2.5} />}
              {type === TERMINAL && (
                <polygon
                  points={`${cx - NODE_R * 0.85},${cy - NODE_R * 0.85} ${cx - NODE_R * 0.85},${cy + NODE_R * 0.85} ${cx + NODE_R},${cy}`}
                  fill={t.elevatedBg}
                  stroke={t.ink}
                  strokeWidth={2}
                />
              )}
            </g>
            {!isLeaf && d[QUESTION] != null && (
              <text x={cx} y={cy - NODE_R - 14} fontSize={16} fontWeight={600} fill={t.ink} textAnchor="middle">
                {d[QUESTION]}
              </text>
            )}
            {!isLeaf && (
              <text x={cx} y={cy + NODE_R + 24} fontSize={15} fontWeight={600} fill={t.inkSoft} textAnchor="middle">
                EMV {formatValue(emv.get(id))}
              </text>
            )}
            {isLeaf && (
              <text x={cx + NODE_R + 12} y={cy} fontSize={16} fontWeight={600} fill={pruned.has(id) ? t.inkSoft : t.ink} dominantBaseline="middle">
                {formatValue(d[PAYOFF])}
              </text>
            )}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const legendItems = [
    { key: DECISION, label: "Decision node", mark: <rect x={1} y={1} width={16} height={16} fill={typeColor[DECISION]} /> },
    { key: CHANCE, label: "Chance node", mark: <circle cx={9} cy={9} r={8.5} fill={typeColor[CHANCE]} /> },
    { key: TERMINAL, label: "Terminal payoff", mark: <polygon points="2,2 2,16 17,9" fill={t.elevatedBg} stroke={t.ink} strokeWidth={1.6} /> },
  ].filter((item) => nodeTypes.includes(item.key));

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "16px 40px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <div style={{ height: LEGEND_H, display: "flex", alignItems: "center", gap: 32, padding: "0 40px" }}>
        {legendItems.map((item) => (
          <div key={item.key} style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <svg width={18} height={18}>{item.mark}</svg>
            <span style={{ fontSize: 15, color: t.ink }}>{item.label}</span>
          </div>
        ))}
        {pruned.size > 0 && (
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <svg width={34} height={18}>
              <line x1={0} y1={9} x2={34} y2={9} stroke={t.inkSoft} strokeWidth={1.8} strokeDasharray="6 4" opacity={0.55} />
              <line x1={13} y1={2} x2={13} y2={16} stroke={t.ink} strokeWidth={2} transform="rotate(25 15 9)" opacity={0.55} />
              <line x1={19} y1={2} x2={19} y2={16} stroke={t.ink} strokeWidth={2} transform="rotate(25 17 9)" opacity={0.55} />
            </svg>
            <span style={{ fontSize: 15, color: t.ink }}>Pruned branch</span>
          </div>
        )}
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H - LEGEND_H}
        series={[]}
        skipAnimation
        margin={{ top: 24, right: 40, bottom: 24, left: 40 }}
        xAxis={[{ id: "depth", scaleType: "linear", min: -DEPTH_PAD_LEFT, max: maxDepth + DEPTH_PAD_RIGHT, position: "none" }]}
        yAxis={[{ id: "slot", scaleType: "linear", min: -SLOT_PAD, max: slotCount + SLOT_PAD, reverse: true, position: "none" }]}
      >
        <DecisionTree />
      </ChartsContainer>
    </div>
  );
}
