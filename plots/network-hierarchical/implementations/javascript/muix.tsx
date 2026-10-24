// anyplot.ai
// network-hierarchical: Hierarchical Network Graph with Tree Layout
// Library: muix 7.29.1 | JavaScript 22.23.2
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

// Columns: set these to your data's column names
const NODE_ID = "Node ID"; // role: id
const LABEL = "Role"; // role: label
const PARENT_ID = "Reports to"; // role: parent

// Data: replace this block with your own records
const data: Array<Record<string, string | null>> = [
  { [NODE_ID]: "ceo", [LABEL]: "CEO", [PARENT_ID]: null },

  // Engineering branch
  { [NODE_ID]: "vp-eng", [LABEL]: "VP Engineering", [PARENT_ID]: "ceo" },
  { [NODE_ID]: "dir-plat", [LABEL]: "Platform Eng", [PARENT_ID]: "vp-eng" },
  { [NODE_ID]: "dir-prod", [LABEL]: "Product Eng", [PARENT_ID]: "vp-eng" },
  { [NODE_ID]: "rep-be1", [LABEL]: "Backend Eng 1", [PARENT_ID]: "dir-plat" },
  { [NODE_ID]: "rep-be2", [LABEL]: "Backend Eng 2", [PARENT_ID]: "dir-plat" },
  { [NODE_ID]: "rep-inf", [LABEL]: "Infra Eng", [PARENT_ID]: "dir-plat" },
  { [NODE_ID]: "rep-fe1", [LABEL]: "Frontend Eng 1", [PARENT_ID]: "dir-prod" },
  { [NODE_ID]: "rep-fe2", [LABEL]: "Frontend Eng 2", [PARENT_ID]: "dir-prod" },

  // Sales branch
  { [NODE_ID]: "vp-sales", [LABEL]: "VP Sales", [PARENT_ID]: "ceo" },
  { [NODE_ID]: "dir-ent", [LABEL]: "Enterprise Sales", [PARENT_ID]: "vp-sales" },
  { [NODE_ID]: "dir-smb", [LABEL]: "SMB Sales", [PARENT_ID]: "vp-sales" },
  { [NODE_ID]: "rep-ae1", [LABEL]: "Account Exec 1", [PARENT_ID]: "dir-ent" },
  { [NODE_ID]: "rep-ae2", [LABEL]: "Account Exec 2", [PARENT_ID]: "dir-ent" },
  { [NODE_ID]: "rep-ae3", [LABEL]: "Account Exec 3", [PARENT_ID]: "dir-smb" },
  { [NODE_ID]: "rep-ae4", [LABEL]: "Account Exec 4", [PARENT_ID]: "dir-smb" },

  // Marketing branch
  { [NODE_ID]: "vp-mkt", [LABEL]: "VP Marketing", [PARENT_ID]: "ceo" },
  { [NODE_ID]: "dir-brand", [LABEL]: "Brand", [PARENT_ID]: "vp-mkt" },
  { [NODE_ID]: "dir-growth", [LABEL]: "Growth", [PARENT_ID]: "vp-mkt" },
  { [NODE_ID]: "rep-bm", [LABEL]: "Brand Manager", [PARENT_ID]: "dir-brand" },
  { [NODE_ID]: "rep-cl", [LABEL]: "Content Lead", [PARENT_ID]: "dir-brand" },
  { [NODE_ID]: "rep-ga", [LABEL]: "Growth Analyst", [PARENT_ID]: "dir-growth" },
  { [NODE_ID]: "rep-seo", [LABEL]: "SEO Specialist", [PARENT_ID]: "dir-growth" },

  // Operations branch
  { [NODE_ID]: "vp-ops", [LABEL]: "VP Operations", [PARENT_ID]: "ceo" },
  { [NODE_ID]: "dir-fin", [LABEL]: "Finance", [PARENT_ID]: "vp-ops" },
  { [NODE_ID]: "dir-ppl", [LABEL]: "People", [PARENT_ID]: "vp-ops" },
  { [NODE_ID]: "rep-ctrl", [LABEL]: "Controller", [PARENT_ID]: "dir-fin" },
  { [NODE_ID]: "rep-fpa", [LABEL]: "FP&A Analyst", [PARENT_ID]: "dir-fin" },
  { [NODE_ID]: "rep-rec", [LABEL]: "Recruiter", [PARENT_ID]: "dir-ppl" },
  { [NODE_ID]: "rep-hr", [LABEL]: "HR Partner", [PARENT_ID]: "dir-ppl" },
];

// Plot: reads only data and the constants above
interface TreeNode {
  id: string;
  label: string;
  parentId: string | null;
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

for (const row of data) {
  const id = String(row[NODE_ID]);
  const label = String(row[LABEL]);
  const parentVal = row[PARENT_ID];
  const parentId = parentVal !== null && parentVal !== undefined && String(parentVal) !== "" ? String(parentVal) : null;
  const node: TreeNode = {
    id,
    label,
    parentId,
    level: 0,
    branchIndex: -1,
    children: [],
    radius: LEVEL_RADII[0],
    color: t.ink,
    x: 0,
    y: 0,
  };
  nodesById.set(id, node);
  allNodes.push(node);
}

for (const node of allNodes) {
  if (node.parentId !== null) {
    nodesById.get(node.parentId)!.children.push(node.id);
  }
}

const rootNode = allNodes.find((n) => n.parentId === null)!;
const branchRootIds = rootNode.children;
const branches = branchRootIds.map((id) => nodesById.get(id)!.label);

const dfsOrder: TreeNode[] = [];
const stack: TreeNode[] = [rootNode];
while (stack.length > 0) {
  const curr = stack.pop()!;
  dfsOrder.push(curr);
  for (let i = curr.children.length - 1; i >= 0; i -= 1) {
    const child = nodesById.get(curr.children[i])!;
    child.level = curr.level + 1;
    child.branchIndex = curr.id === rootNode.id ? branchRootIds.indexOf(child.id) : curr.branchIndex;
    child.radius = LEVEL_RADII[Math.min(child.level, LEVEL_RADII.length - 1)];
    child.color = t.palette[child.branchIndex];
    stack.push(child);
  }
}

const maxLevel = Math.max(...allNodes.map((n) => n.level));

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
  if (node.parentId !== null) {
    edges.push({ parent: nodesById.get(node.parentId)!, child: node });
  }
}

const xSpan = nextLeafX - 1;
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
        const cx = Number(xScale(node.x));
        const cy = Number(yScale(node.y));
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
