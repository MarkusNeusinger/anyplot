// anyplot.ai
// network-hierarchical: Hierarchical Network Graph with Tree Layout
// Library: muix 9.x | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-02

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "network-hierarchical · javascript · muix · anyplot.ai";
const TITLE_FONT_SIZE = 22;
const TITLE_H = 44;
const LEGEND_H = 36;
const LEVEL_RADII = [22, 16, 12, 9];
const X_PAD_SHARE = 0.08;
const Y_TOP_PAD_SHARE = 0.22;
const Y_BOTTOM_PAD_SHARE = 0.34;
const ROOT_BRANCH = "Executive";

const NODE_ID_COL = "node_id";
const LABEL_COL = "label";
const PARENT_ID_COL = "parent_id";
const LEVEL_COL = "level";
const BRANCH_COL = "branch";

// Data: 4-level company org chart (flat scalar hierarchy records)
const DATA: Array<Record<string, string | number>> = [
  { node_id: "ceo", label: "CEO", parent_id: "", level: 0, branch: "Executive" },

  // Engineering branch
  { node_id: "vp-eng", label: "VP Engineering", parent_id: "ceo", level: 1, branch: "Engineering" },
  { node_id: "dir-plat", label: "Platform Eng", parent_id: "vp-eng", level: 2, branch: "Engineering" },
  { node_id: "dir-prod", label: "Product Eng", parent_id: "vp-eng", level: 2, branch: "Engineering" },
  { node_id: "rep-be1", label: "Backend Eng 1", parent_id: "dir-plat", level: 3, branch: "Engineering" },
  { node_id: "rep-be2", label: "Backend Eng 2", parent_id: "dir-plat", level: 3, branch: "Engineering" },
  { node_id: "rep-inf", label: "Infra Eng", parent_id: "dir-plat", level: 3, branch: "Engineering" },
  { node_id: "rep-fe1", label: "Frontend Eng 1", parent_id: "dir-prod", level: 3, branch: "Engineering" },
  { node_id: "rep-fe2", label: "Frontend Eng 2", parent_id: "dir-prod", level: 3, branch: "Engineering" },

  // Sales branch
  { node_id: "vp-sales", label: "VP Sales", parent_id: "ceo", level: 1, branch: "Sales" },
  { node_id: "dir-ent", label: "Enterprise Sales", parent_id: "vp-sales", level: 2, branch: "Sales" },
  { node_id: "dir-smb", label: "SMB Sales", parent_id: "vp-sales", level: 2, branch: "Sales" },
  { node_id: "rep-ae1", label: "Account Exec 1", parent_id: "dir-ent", level: 3, branch: "Sales" },
  { node_id: "rep-ae2", label: "Account Exec 2", parent_id: "dir-ent", level: 3, branch: "Sales" },
  { node_id: "rep-ae3", label: "Account Exec 3", parent_id: "dir-smb", level: 3, branch: "Sales" },
  { node_id: "rep-ae4", label: "Account Exec 4", parent_id: "dir-smb", level: 3, branch: "Sales" },

  // Marketing branch
  { node_id: "vp-mkt", label: "VP Marketing", parent_id: "ceo", level: 1, branch: "Marketing" },
  { node_id: "dir-brand", label: "Brand", parent_id: "vp-mkt", level: 2, branch: "Marketing" },
  { node_id: "dir-growth", label: "Growth", parent_id: "vp-mkt", level: 2, branch: "Marketing" },
  { node_id: "rep-bm", label: "Brand Manager", parent_id: "dir-brand", level: 3, branch: "Marketing" },
  { node_id: "rep-cl", label: "Content Lead", parent_id: "dir-brand", level: 3, branch: "Marketing" },
  { node_id: "rep-ga", label: "Growth Analyst", parent_id: "dir-growth", level: 3, branch: "Marketing" },
  { node_id: "rep-seo", label: "SEO Specialist", parent_id: "dir-growth", level: 3, branch: "Marketing" },

  // Operations branch
  { node_id: "vp-ops", label: "VP Operations", parent_id: "ceo", level: 1, branch: "Operations" },
  { node_id: "dir-fin", label: "Finance", parent_id: "vp-ops", level: 2, branch: "Operations" },
  { node_id: "dir-ppl", label: "People", parent_id: "vp-ops", level: 2, branch: "Operations" },
  { node_id: "rep-ctrl", label: "Controller", parent_id: "dir-fin", level: 3, branch: "Operations" },
  { node_id: "rep-fpa", label: "FP&A Analyst", parent_id: "dir-fin", level: 3, branch: "Operations" },
  { node_id: "rep-rec", label: "Recruiter", parent_id: "dir-ppl", level: 3, branch: "Operations" },
  { node_id: "rep-hr", label: "HR Partner", parent_id: "dir-ppl", level: 3, branch: "Operations" },
];

// Derive department branches in order of first appearance (excluding root Executive)
const branches: string[] = [];
for (const row of DATA) {
  const b = String(row[BRANCH_COL]);
  if (b !== ROOT_BRANCH && !branches.includes(b)) {
    branches.push(b);
  }
}

interface TreeNode {
  id: string;
  label: string;
  parentId: string;
  level: number;
  branchIndex: number;
  children: string[];
  radius: number;
  color: string;
  x: number;
  y: number;
}

const nodesById = new Map<string, TreeNode>();
const allNodes: TreeNode[] = [];

for (const row of DATA) {
  const id = String(row[NODE_ID_COL]);
  const label = String(row[LABEL_COL]);
  const parentId = String(row[PARENT_ID_COL]);
  const level = Number(row[LEVEL_COL]);
  const branch = String(row[BRANCH_COL]);
  const branchIndex = branch === ROOT_BRANCH ? -1 : branches.indexOf(branch);
  const radius = LEVEL_RADII[Math.min(level, LEVEL_RADII.length - 1)];
  const color = branchIndex === -1 ? t.ink : t.palette[branchIndex];
  const node: TreeNode = {
    id,
    label,
    parentId,
    level,
    branchIndex,
    children: [],
    radius,
    color,
    x: 0,
    y: 0,
  };
  nodesById.set(id, node);
  allNodes.push(node);
}

for (const node of allNodes) {
  if (node.parentId && nodesById.has(node.parentId)) {
    nodesById.get(node.parentId)!.children.push(node.id);
  }
}

const maxLevel = Math.max(1, ...allNodes.map((n) => n.level));

// Iterative bottom-up tidy tree layout: leaves get sequential x in DFS order, parents average children
const rootNode = allNodes.find((n) => !n.parentId) ?? allNodes[0];
const dfsOrder: TreeNode[] = [];
const stack: TreeNode[] = [rootNode];
while (stack.length > 0) {
  const curr = stack.pop()!;
  dfsOrder.push(curr);
  for (let i = curr.children.length - 1; i >= 0; i -= 1) {
    const child = nodesById.get(curr.children[i]);
    if (child) stack.push(child);
  }
}

let nextLeafX = 0;
for (let i = 0; i < dfsOrder.length; i += 1) {
  const node = dfsOrder[i];
  if (node.children.length === 0) {
    node.x = nextLeafX;
    nextLeafX += 1;
  }
}
for (let i = dfsOrder.length - 1; i >= 0; i -= 1) {
  const node = dfsOrder[i];
  if (node.children.length > 0) {
    let sumX = 0;
    for (const childId of node.children) {
      sumX += nodesById.get(childId)!.x;
    }
    node.x = sumX / node.children.length;
  }
  node.y = maxLevel - node.level;
}

const edges: Array<{ parent: TreeNode; child: TreeNode }> = [];
for (const node of allNodes) {
  if (node.parentId && nodesById.has(node.parentId)) {
    edges.push({ parent: nodesById.get(node.parentId)!, child: node });
  }
}

const xSpan = Math.max(1, nextLeafX - 1);
const xPad = xSpan * X_PAD_SHARE;
const domain = {
  xMin: -xPad,
  xMax: xSpan + xPad,
  yMin: -maxLevel * Y_BOTTOM_PAD_SHARE,
  yMax: maxLevel * (1 + Y_TOP_PAD_SHARE),
};

function HierarchicalTreeOverlay() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g data-drawing-container>
      {edges.map(({ parent, child }, i) => (
        <line
          key={`edge-${i}`}
          x1={xScale(parent.x)}
          y1={yScale(parent.y)}
          x2={xScale(child.x)}
          y2={yScale(child.y)}
          stroke={child.color}
          strokeOpacity={0.38}
          strokeWidth={1.6}
        />
      ))}
      {allNodes.map((node) => {
        const cx = xScale(node.x);
        const cy = yScale(node.y);
        const isLeaf = node.children.length === 0;
        return (
          <React.Fragment key={node.id}>
            <circle
              cx={cx}
              cy={cy}
              r={node.radius}
              fill={node.color}
              stroke={t.pageBg}
              strokeWidth={1.5}
            />
            {!isLeaf ? (
              <g>
                <rect
                  x={cx - (node.label.length * 4.1 + 6)}
                  y={cy - node.radius - 24}
                  width={node.label.length * 8.2 + 12}
                  height={19}
                  rx={4}
                  fill={t.pageBg}
                  fillOpacity={0.86}
                />
                <text
                  x={cx}
                  y={cy - node.radius - 10}
                  textAnchor="middle"
                  fontSize={node.level === 0 ? 15 : 14}
                  fontWeight={node.level === 0 ? 600 : 500}
                  fill={t.ink}
                >
                  {node.label}
                </text>
              </g>
            ) : (
              <text
                x={cx}
                y={cy + node.radius + 12}
                textAnchor="end"
                fontSize={14}
                fontWeight={400}
                fill={t.inkSoft}
                transform={`rotate(-36, ${cx}, ${cy + node.radius + 12})`}
              >
                {node.label}
              </text>
            )}
          </React.Fragment>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - TITLE_H - LEGEND_H;

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <div
        style={{
          height: `${TITLE_H}px`,
          lineHeight: `${TITLE_H}px`,
          fontSize: `${TITLE_FONT_SIZE}px`,
          fontWeight: 600,
          color: t.ink,
          paddingLeft: "16px",
        }}
      >
        {TITLE}
      </div>
      <div
        style={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          gap: "20px",
          flexWrap: "wrap",
          paddingLeft: "16px",
        }}
      >
        {branches.map((branchName, i) => (
          <div key={branchName} style={{ display: "flex", alignItems: "center", gap: "7px" }}>
            <span
              style={{
                width: "12px",
                height: "12px",
                borderRadius: "50%",
                backgroundColor: t.palette[i],
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: "14px", color: t.inkSoft }}>{branchName}</span>
          </div>
        ))}
      </div>
      <ChartsContainer
        width={width}
        height={chartHeight}
        series={[]}
        margin={{ top: 8, bottom: 8, left: 16, right: 16 }}
        xAxis={[{ id: "x", scaleType: "linear", min: domain.xMin, max: domain.xMax, position: "none" }]}
        yAxis={[{ id: "y", scaleType: "linear", min: domain.yMin, max: domain.yMax, position: "none" }]}
        skipAnimation
      >
        <HierarchicalTreeOverlay />
      </ChartsContainer>
    </div>
  );
}
