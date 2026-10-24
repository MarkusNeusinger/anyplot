// anyplot.ai
// network-force-directed: Force-Directed Graph
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 82/100 | Updated: 2026-10-24
//# anyplot-orientation: square

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "network-force-directed · javascript · muix · anyplot.ai";
const TITLE_FONT_SIZE = 22;
const TITLE_H = 46;
const LEGEND_H = 36;
const CAPTION_H = 32;
const SIM_AREA_SPAN = 1000;
const RING_RADIUS_SHARE = 0.26;
const SUBRING_RADIUS_SHARE = 0.07;
const JITTER_SHARE = 0.024;
const ITERATIONS = 300;
const INITIAL_TEMP_SHARE = 0.08;
const GRAVITY_FACTOR = 0.01;
const PAD_SHARE = 0.14;
const MIN_NODE_R = 7;
const MAX_NODE_R_SPAN = 16;
const HUB_HALO_OFFSET = 7;

// Columns: set these to your data's column names
const NODE = "Researcher"; // role: node
const GROUP = "Research field"; // role: group
const SOURCE = "Source researcher"; // role: source
const TARGET = "Target researcher"; // role: target
const WEIGHT = "Co-authored papers"; // role: weight

// Data: replace this block with your own records
const nodes: Array<Record<string, string>> = [
  // Machine Learning (8 researchers)
  { [NODE]: "ML-0", [GROUP]: "Machine Learning" },
  { [NODE]: "ML-1", [GROUP]: "Machine Learning" },
  { [NODE]: "ML-2", [GROUP]: "Machine Learning" },
  { [NODE]: "ML-3", [GROUP]: "Machine Learning" },
  { [NODE]: "ML-4", [GROUP]: "Machine Learning" },
  { [NODE]: "ML-5", [GROUP]: "Machine Learning" },
  { [NODE]: "ML-6", [GROUP]: "Machine Learning" },
  { [NODE]: "ML-7", [GROUP]: "Machine Learning" },

  // Robotics (6 researchers)
  { [NODE]: "RB-0", [GROUP]: "Robotics" },
  { [NODE]: "RB-1", [GROUP]: "Robotics" },
  { [NODE]: "RB-2", [GROUP]: "Robotics" },
  { [NODE]: "RB-3", [GROUP]: "Robotics" },
  { [NODE]: "RB-4", [GROUP]: "Robotics" },
  { [NODE]: "RB-5", [GROUP]: "Robotics" },

  // Bioinformatics (7 researchers)
  { [NODE]: "BI-0", [GROUP]: "Bioinformatics" },
  { [NODE]: "BI-1", [GROUP]: "Bioinformatics" },
  { [NODE]: "BI-2", [GROUP]: "Bioinformatics" },
  { [NODE]: "BI-3", [GROUP]: "Bioinformatics" },
  { [NODE]: "BI-4", [GROUP]: "Bioinformatics" },
  { [NODE]: "BI-5", [GROUP]: "Bioinformatics" },
  { [NODE]: "BI-6", [GROUP]: "Bioinformatics" },

  // Network Science (5 researchers)
  { [NODE]: "NS-0", [GROUP]: "Network Science" },
  { [NODE]: "NS-1", [GROUP]: "Network Science" },
  { [NODE]: "NS-2", [GROUP]: "Network Science" },
  { [NODE]: "NS-3", [GROUP]: "Network Science" },
  { [NODE]: "NS-4", [GROUP]: "Network Science" },

  // Cryptography (6 researchers)
  { [NODE]: "CR-0", [GROUP]: "Cryptography" },
  { [NODE]: "CR-1", [GROUP]: "Cryptography" },
  { [NODE]: "CR-2", [GROUP]: "Cryptography" },
  { [NODE]: "CR-3", [GROUP]: "Cryptography" },
  { [NODE]: "CR-4", [GROUP]: "Cryptography" },
  { [NODE]: "CR-5", [GROUP]: "Cryptography" },
];

const data: Array<Record<string, string | number>> = [
  // Machine Learning
  { [SOURCE]: "ML-0", [TARGET]: "ML-1", [WEIGHT]: 5 },
  { [SOURCE]: "ML-0", [TARGET]: "ML-2", [WEIGHT]: 4 },
  { [SOURCE]: "ML-0", [TARGET]: "ML-3", [WEIGHT]: 3 },
  { [SOURCE]: "ML-0", [TARGET]: "ML-4", [WEIGHT]: 4 },
  { [SOURCE]: "ML-0", [TARGET]: "ML-5", [WEIGHT]: 2 },
  { [SOURCE]: "ML-0", [TARGET]: "ML-6", [WEIGHT]: 3 },
  { [SOURCE]: "ML-0", [TARGET]: "ML-7", [WEIGHT]: 2 },
  { [SOURCE]: "ML-1", [TARGET]: "ML-2", [WEIGHT]: 3 },
  { [SOURCE]: "ML-1", [TARGET]: "ML-4", [WEIGHT]: 2 },
  { [SOURCE]: "ML-2", [TARGET]: "ML-3", [WEIGHT]: 1 },
  { [SOURCE]: "ML-4", [TARGET]: "ML-5", [WEIGHT]: 2 },
  { [SOURCE]: "ML-5", [TARGET]: "ML-6", [WEIGHT]: 3 },
  { [SOURCE]: "ML-6", [TARGET]: "ML-7", [WEIGHT]: 1 },

  // Robotics
  { [SOURCE]: "RB-0", [TARGET]: "RB-1", [WEIGHT]: 4 },
  { [SOURCE]: "RB-0", [TARGET]: "RB-2", [WEIGHT]: 3 },
  { [SOURCE]: "RB-0", [TARGET]: "RB-3", [WEIGHT]: 5 },
  { [SOURCE]: "RB-0", [TARGET]: "RB-4", [WEIGHT]: 2 },
  { [SOURCE]: "RB-0", [TARGET]: "RB-5", [WEIGHT]: 3 },
  { [SOURCE]: "RB-1", [TARGET]: "RB-2", [WEIGHT]: 2 },
  { [SOURCE]: "RB-2", [TARGET]: "RB-3", [WEIGHT]: 3 },
  { [SOURCE]: "RB-3", [TARGET]: "RB-4", [WEIGHT]: 1 },
  { [SOURCE]: "RB-4", [TARGET]: "RB-5", [WEIGHT]: 2 },

  // Bioinformatics
  { [SOURCE]: "BI-0", [TARGET]: "BI-1", [WEIGHT]: 3 },
  { [SOURCE]: "BI-0", [TARGET]: "BI-2", [WEIGHT]: 4 },
  { [SOURCE]: "BI-0", [TARGET]: "BI-3", [WEIGHT]: 5 },
  { [SOURCE]: "BI-0", [TARGET]: "BI-4", [WEIGHT]: 2 },
  { [SOURCE]: "BI-0", [TARGET]: "BI-5", [WEIGHT]: 3 },
  { [SOURCE]: "BI-0", [TARGET]: "BI-6", [WEIGHT]: 4 },
  { [SOURCE]: "BI-1", [TARGET]: "BI-2", [WEIGHT]: 2 },
  { [SOURCE]: "BI-2", [TARGET]: "BI-3", [WEIGHT]: 3 },
  { [SOURCE]: "BI-3", [TARGET]: "BI-5", [WEIGHT]: 2 },
  { [SOURCE]: "BI-4", [TARGET]: "BI-6", [WEIGHT]: 1 },
  { [SOURCE]: "BI-5", [TARGET]: "BI-6", [WEIGHT]: 2 },

  // Network Science
  { [SOURCE]: "NS-0", [TARGET]: "NS-1", [WEIGHT]: 4 },
  { [SOURCE]: "NS-0", [TARGET]: "NS-2", [WEIGHT]: 3 },
  { [SOURCE]: "NS-0", [TARGET]: "NS-3", [WEIGHT]: 5 },
  { [SOURCE]: "NS-0", [TARGET]: "NS-4", [WEIGHT]: 2 },
  { [SOURCE]: "NS-1", [TARGET]: "NS-2", [WEIGHT]: 2 },
  { [SOURCE]: "NS-2", [TARGET]: "NS-3", [WEIGHT]: 3 },
  { [SOURCE]: "NS-3", [TARGET]: "NS-4", [WEIGHT]: 1 },

  // Cryptography
  { [SOURCE]: "CR-0", [TARGET]: "CR-1", [WEIGHT]: 4 },
  { [SOURCE]: "CR-0", [TARGET]: "CR-2", [WEIGHT]: 3 },
  { [SOURCE]: "CR-0", [TARGET]: "CR-3", [WEIGHT]: 2 },
  { [SOURCE]: "CR-0", [TARGET]: "CR-4", [WEIGHT]: 5 },
  { [SOURCE]: "CR-0", [TARGET]: "CR-5", [WEIGHT]: 3 },
  { [SOURCE]: "CR-1", [TARGET]: "CR-2", [WEIGHT]: 1 },
  { [SOURCE]: "CR-2", [TARGET]: "CR-4", [WEIGHT]: 3 },
  { [SOURCE]: "CR-3", [TARGET]: "CR-4", [WEIGHT]: 2 },
  { [SOURCE]: "CR-4", [TARGET]: "CR-5", [WEIGHT]: 2 },

  // Cross-group bridges
  { [SOURCE]: "ML-0", [TARGET]: "RB-0", [WEIGHT]: 2 },
  { [SOURCE]: "ML-1", [TARGET]: "BI-0", [WEIGHT]: 1 },
  { [SOURCE]: "RB-0", [TARGET]: "BI-0", [WEIGHT]: 2 },
  { [SOURCE]: "BI-0", [TARGET]: "NS-0", [WEIGHT]: 1 },
  { [SOURCE]: "NS-0", [TARGET]: "CR-0", [WEIGHT]: 2 },
  { [SOURCE]: "CR-0", [TARGET]: "ML-0", [WEIGHT]: 1 },
  { [SOURCE]: "NS-2", [TARGET]: "ML-3", [WEIGHT]: 1 },
];

// Plot: reads only data and the constants above
const groups: string[] = [];
for (const row of nodes) {
  const grp = String(row[GROUP]);
  if (!groups.includes(grp)) groups.push(grp);
}

interface ForceNode {
  id: string;
  groupIndex: number;
  groupName: string;
  isHub: boolean;
  withinIndex: number;
  degree: number;
  radius: number;
  x: number;
  y: number;
}

const nodeIndexById = new Map<string, number>();
const layoutNodes: ForceNode[] = [];
const groupCounts = new Array<number>(groups.length).fill(0);

for (const row of nodes) {
  const id = String(row[NODE]);
  const grp = String(row[GROUP]);
  const groupIndex = groups.indexOf(grp);
  const withinIndex = groupCounts[groupIndex];
  groupCounts[groupIndex] += 1;
  nodeIndexById.set(id, layoutNodes.length);
  layoutNodes.push({
    id,
    groupIndex,
    groupName: grp,
    isHub: false,
    withinIndex,
    degree: 0,
    radius: MIN_NODE_R,
    x: 0,
    y: 0,
  });
}

interface ForceEdge {
  sourceIdx: number;
  targetIdx: number;
  weight: number;
  wRatio: number;
  isBridge: boolean;
}

const edges: ForceEdge[] = [];
for (const row of data) {
  const a = nodeIndexById.get(String(row[SOURCE]))!;
  const b = nodeIndexById.get(String(row[TARGET]))!;
  const weight = Number(row[WEIGHT]);
  const isBridge = layoutNodes[a].groupIndex !== layoutNodes[b].groupIndex;
  edges.push({ sourceIdx: a, targetIdx: b, weight, wRatio: 0, isBridge });
  layoutNodes[a].degree += 1;
  layoutNodes[b].degree += 1;
}

const minW = Math.min(...edges.map((e) => e.weight));
const maxW = Math.max(...edges.map((e) => e.weight));
const wSpan = maxW - minW;
for (const edge of edges) {
  edge.wRatio = (edge.weight - minW) / wSpan;
}

// Identify the primary hub in each group by highest degree
for (let g = 0; g < groups.length; g += 1) {
  let bestIdx = -1;
  let bestDeg = -1;
  for (let i = 0; i < layoutNodes.length; i += 1) {
    if (layoutNodes[i].groupIndex === g && layoutNodes[i].degree > bestDeg) {
      bestDeg = layoutNodes[i].degree;
      bestIdx = i;
    }
  }
  if (bestIdx >= 0) {
    layoutNodes[bestIdx].isHub = true;
  }
}

const maxDegree = Math.max(...layoutNodes.map((n) => n.degree));
for (const node of layoutNodes) {
  node.radius = MIN_NODE_R + (node.degree / maxDegree) * MAX_NODE_R_SPAN;
}

let lcgState = 104729;
const ringRadius = SIM_AREA_SPAN * RING_RADIUS_SHARE;
const subringRadius = SIM_AREA_SPAN * SUBRING_RADIUS_SHARE;
const jitterSpan = SIM_AREA_SPAN * JITTER_SHARE;

for (const node of layoutNodes) {
  const groupAngle = (node.groupIndex / groups.length) * Math.PI * 2;
  const centerX = Math.cos(groupAngle) * ringRadius;
  const centerY = Math.sin(groupAngle) * ringRadius;
  const groupCount = groupCounts[node.groupIndex];
  const withinAngle = (node.withinIndex / groupCount) * Math.PI * 2;
  lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
  const jx = (lcgState / 4294967296 - 0.5) * jitterSpan;
  lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
  const jy = (lcgState / 4294967296 - 0.5) * jitterSpan;
  node.x = centerX + Math.cos(withinAngle) * subringRadius + jx;
  node.y = centerY + Math.sin(withinAngle) * subringRadius + jy;
}

const idealDistance = Math.sqrt((SIM_AREA_SPAN * SIM_AREA_SPAN) / layoutNodes.length);
let temperature = SIM_AREA_SPAN * INITIAL_TEMP_SHARE;
const cooling = temperature / ITERATIONS;

for (let iter = 0; iter < ITERATIONS; iter += 1) {
  const dispX = new Array<number>(layoutNodes.length).fill(0);
  const dispY = new Array<number>(layoutNodes.length).fill(0);

  for (let i = 0; i < layoutNodes.length; i += 1) {
    for (let j = i + 1; j < layoutNodes.length; j += 1) {
      const dx = layoutNodes[i].x - layoutNodes[j].x;
      const dy = layoutNodes[i].y - layoutNodes[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
      const force = (idealDistance * idealDistance) / dist;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      dispX[i] += fx;
      dispY[i] += fy;
      dispX[j] -= fx;
      dispY[j] -= fy;
    }
  }

  for (const edge of edges) {
    const a = edge.sourceIdx;
    const b = edge.targetIdx;
    const dx = layoutNodes[a].x - layoutNodes[b].x;
    const dy = layoutNodes[a].y - layoutNodes[b].y;
    const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
    const force = ((dist * dist) / idealDistance) * (0.6 + edge.wRatio * 0.6);
    const fx = (dx / dist) * force;
    const fy = (dy / dist) * force;
    dispX[a] -= fx;
    dispY[a] -= fy;
    dispX[b] += fx;
    dispY[b] += fy;
  }

  for (let i = 0; i < layoutNodes.length; i += 1) {
    dispX[i] -= layoutNodes[i].x * GRAVITY_FACTOR;
    dispY[i] -= layoutNodes[i].y * GRAVITY_FACTOR;
    const dist = Math.sqrt(dispX[i] * dispX[i] + dispY[i] * dispY[i]) || 0.01;
    const capped = Math.min(dist, temperature);
    layoutNodes[i].x += (dispX[i] / dist) * capped;
    layoutNodes[i].y += (dispY[i] / dist) * capped;
  }

  temperature = Math.max(temperature - cooling, 1);
}

const xs = layoutNodes.map((n) => n.x);
const ys = layoutNodes.map((n) => n.y);
const rawXMin = Math.min(...xs);
const rawXMax = Math.max(...xs);
const rawYMin = Math.min(...ys);
const rawYMax = Math.max(...ys);
const rawSpan = Math.max(rawXMax - rawXMin, rawYMax - rawYMin);
const pad = rawSpan * PAD_SHARE;
const xMid = (rawXMin + rawXMax) / 2;
const yMid = (rawYMin + rawYMax) / 2;
const span = rawSpan + pad * 2;
const domain = {
  xMin: xMid - span / 2,
  xMax: xMid + span / 2,
  yMin: yMid - span / 2,
  yMax: yMid + span / 2,
};

function ForceNetworkOverlay() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g data-drawing-container>
      {edges.map((edge, i) => (
        <line
          key={`edge-${i}`}
          x1={xScale(layoutNodes[edge.sourceIdx].x)}
          y1={yScale(layoutNodes[edge.sourceIdx].y)}
          x2={xScale(layoutNodes[edge.targetIdx].x)}
          y2={yScale(layoutNodes[edge.targetIdx].y)}
          stroke={t.inkSoft}
          strokeOpacity={edge.isBridge ? 0.25 : 0.42}
          strokeWidth={edge.isBridge ? 1.2 : 1.1 + edge.wRatio * 2.2}
          strokeDasharray={edge.isBridge ? "5,4" : undefined}
        />
      ))}
      {layoutNodes.map((node) => (
        <React.Fragment key={node.id}>
          {node.isHub && (
            <circle
              cx={xScale(node.x)}
              cy={yScale(node.y)}
              r={node.radius + HUB_HALO_OFFSET}
              fill={t.palette[node.groupIndex]}
              opacity={0.2}
            />
          )}
          <circle
            cx={xScale(node.x)}
            cy={yScale(node.y)}
            r={node.radius}
            fill={t.palette[node.groupIndex]}
            stroke={t.pageBg}
            strokeWidth={1.5}
          />
          {node.isHub && (
            <g>
              <rect
                x={Number(xScale(node.x)) - (node.groupName.length * 4.4 + 8)}
                y={Number(yScale(node.y)) - node.radius - 24}
                width={node.groupName.length * 8.8 + 16}
                height={20}
                rx={4}
                fill={t.pageBg}
                fillOpacity={0.88}
              />
              <text
                x={xScale(node.x)}
                y={Number(yScale(node.y)) - node.radius - 10}
                textAnchor="middle"
                fontSize={15}
                fontWeight={500}
                fill={t.ink}
              >
                {node.groupName}
              </text>
            </g>
          )}
        </React.Fragment>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - TITLE_H - LEGEND_H - CAPTION_H;

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
        {groups.map((groupName, i) => (
          <div key={groupName} style={{ display: "flex", alignItems: "center", gap: "7px" }}>
            <span
              style={{
                width: "12px",
                height: "12px",
                borderRadius: "50%",
                backgroundColor: t.palette[i],
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: "14px", color: t.inkSoft }}>{groupName}</span>
          </div>
        ))}
      </div>
      <ChartsContainer
        width={width}
        height={chartHeight}
        series={[]}
        margin={{ top: 8, bottom: 8, left: 8, right: 8 }}
        xAxis={[{ id: "x", scaleType: "linear", min: domain.xMin, max: domain.xMax, position: "none" }]}
        yAxis={[{ id: "y", scaleType: "linear", min: domain.yMin, max: domain.yMax, position: "none" }]}
        skipAnimation
      >
        <ForceNetworkOverlay />
      </ChartsContainer>
      <div
        style={{
          height: CAPTION_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 13,
          color: t.inkSoft,
        }}
      >
        {`Node size = degree · Halo & label = highest-degree hub per ${GROUP} · Edge width = ${WEIGHT} · Dashed line = cross-group link`}
      </div>
    </div>
  );
}
