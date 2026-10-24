// anyplot.ai
// network-force-directed: Force-Directed Graph
// Library: muix 9.x | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-08-24
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

const SOURCE_ID_COL = "source_id";
const SOURCE_GROUP_COL = "source_group";
const SOURCE_HUB_COL = "source_is_hub";
const TARGET_ID_COL = "target_id";
const TARGET_GROUP_COL = "target_group";
const TARGET_HUB_COL = "target_is_hub";
const WEIGHT_COL = "weight";
const BRIDGE_COL = "is_bridge";

// Data: research co-authorship network (flat scalar edge records)
const DATA: Array<Record<string, string | number | boolean>> = [
  // Machine Learning (ML-0 hub, ML-1..ML-6 peers)
  { source_id: "ML-0", source_group: "Machine Learning", source_is_hub: true, target_id: "ML-1", target_group: "Machine Learning", target_is_hub: false, weight: 3, is_bridge: false },
  { source_id: "ML-0", source_group: "Machine Learning", source_is_hub: true, target_id: "ML-2", target_group: "Machine Learning", target_is_hub: false, weight: 3, is_bridge: false },
  { source_id: "ML-0", source_group: "Machine Learning", source_is_hub: true, target_id: "ML-3", target_group: "Machine Learning", target_is_hub: false, weight: 3, is_bridge: false },
  { source_id: "ML-0", source_group: "Machine Learning", source_is_hub: true, target_id: "ML-4", target_group: "Machine Learning", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "ML-0", source_group: "Machine Learning", source_is_hub: true, target_id: "ML-5", target_group: "Machine Learning", target_is_hub: false, weight: 3, is_bridge: false },
  { source_id: "ML-0", source_group: "Machine Learning", source_is_hub: true, target_id: "ML-6", target_group: "Machine Learning", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "ML-1", source_group: "Machine Learning", source_is_hub: false, target_id: "ML-2", target_group: "Machine Learning", target_is_hub: false, weight: 1, is_bridge: false },
  { source_id: "ML-2", source_group: "Machine Learning", source_is_hub: false, target_id: "ML-3", target_group: "Machine Learning", target_is_hub: false, weight: 1, is_bridge: false },
  { source_id: "ML-3", source_group: "Machine Learning", source_is_hub: false, target_id: "ML-4", target_group: "Machine Learning", target_is_hub: false, weight: 1, is_bridge: false },
  { source_id: "ML-4", source_group: "Machine Learning", source_is_hub: false, target_id: "ML-5", target_group: "Machine Learning", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "ML-5", source_group: "Machine Learning", source_is_hub: false, target_id: "ML-6", target_group: "Machine Learning", target_is_hub: false, weight: 2, is_bridge: false },

  // Robotics (RB-0 hub, RB-1..RB-6 peers)
  { source_id: "RB-0", source_group: "Robotics", source_is_hub: true, target_id: "RB-1", target_group: "Robotics", target_is_hub: false, weight: 3, is_bridge: false },
  { source_id: "RB-0", source_group: "Robotics", source_is_hub: true, target_id: "RB-2", target_group: "Robotics", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "RB-0", source_group: "Robotics", source_is_hub: true, target_id: "RB-3", target_group: "Robotics", target_is_hub: false, weight: 3, is_bridge: false },
  { source_id: "RB-0", source_group: "Robotics", source_is_hub: true, target_id: "RB-4", target_group: "Robotics", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "RB-0", source_group: "Robotics", source_is_hub: true, target_id: "RB-5", target_group: "Robotics", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "RB-0", source_group: "Robotics", source_is_hub: true, target_id: "RB-6", target_group: "Robotics", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "RB-1", source_group: "Robotics", source_is_hub: false, target_id: "RB-2", target_group: "Robotics", target_is_hub: false, weight: 1, is_bridge: false },
  { source_id: "RB-2", source_group: "Robotics", source_is_hub: false, target_id: "RB-3", target_group: "Robotics", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "RB-3", source_group: "Robotics", source_is_hub: false, target_id: "RB-4", target_group: "Robotics", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "RB-4", source_group: "Robotics", source_is_hub: false, target_id: "RB-5", target_group: "Robotics", target_is_hub: false, weight: 1, is_bridge: false },
  { source_id: "RB-5", source_group: "Robotics", source_is_hub: false, target_id: "RB-6", target_group: "Robotics", target_is_hub: false, weight: 1, is_bridge: false },

  // Bioinformatics (BI-0 hub, BI-1..BI-6 peers)
  { source_id: "BI-0", source_group: "Bioinformatics", source_is_hub: true, target_id: "BI-1", target_group: "Bioinformatics", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "BI-0", source_group: "Bioinformatics", source_is_hub: true, target_id: "BI-2", target_group: "Bioinformatics", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "BI-0", source_group: "Bioinformatics", source_is_hub: true, target_id: "BI-3", target_group: "Bioinformatics", target_is_hub: false, weight: 3, is_bridge: false },
  { source_id: "BI-0", source_group: "Bioinformatics", source_is_hub: true, target_id: "BI-4", target_group: "Bioinformatics", target_is_hub: false, weight: 3, is_bridge: false },
  { source_id: "BI-0", source_group: "Bioinformatics", source_is_hub: true, target_id: "BI-5", target_group: "Bioinformatics", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "BI-0", source_group: "Bioinformatics", source_is_hub: true, target_id: "BI-6", target_group: "Bioinformatics", target_is_hub: false, weight: 3, is_bridge: false },
  { source_id: "BI-1", source_group: "Bioinformatics", source_is_hub: false, target_id: "BI-2", target_group: "Bioinformatics", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "BI-2", source_group: "Bioinformatics", source_is_hub: false, target_id: "BI-3", target_group: "Bioinformatics", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "BI-3", source_group: "Bioinformatics", source_is_hub: false, target_id: "BI-4", target_group: "Bioinformatics", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "BI-4", source_group: "Bioinformatics", source_is_hub: false, target_id: "BI-5", target_group: "Bioinformatics", target_is_hub: false, weight: 1, is_bridge: false },
  { source_id: "BI-5", source_group: "Bioinformatics", source_is_hub: false, target_id: "BI-6", target_group: "Bioinformatics", target_is_hub: false, weight: 1, is_bridge: false },

  // Network Science (NS-0 hub, NS-1..NS-6 peers)
  { source_id: "NS-0", source_group: "Network Science", source_is_hub: true, target_id: "NS-1", target_group: "Network Science", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "NS-0", source_group: "Network Science", source_is_hub: true, target_id: "NS-2", target_group: "Network Science", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "NS-0", source_group: "Network Science", source_is_hub: true, target_id: "NS-3", target_group: "Network Science", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "NS-0", source_group: "Network Science", source_is_hub: true, target_id: "NS-4", target_group: "Network Science", target_is_hub: false, weight: 3, is_bridge: false },
  { source_id: "NS-0", source_group: "Network Science", source_is_hub: true, target_id: "NS-5", target_group: "Network Science", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "NS-0", source_group: "Network Science", source_is_hub: true, target_id: "NS-6", target_group: "Network Science", target_is_hub: false, weight: 3, is_bridge: false },
  { source_id: "NS-1", source_group: "Network Science", source_is_hub: false, target_id: "NS-2", target_group: "Network Science", target_is_hub: false, weight: 1, is_bridge: false },
  { source_id: "NS-2", source_group: "Network Science", source_is_hub: false, target_id: "NS-3", target_group: "Network Science", target_is_hub: false, weight: 1, is_bridge: false },
  { source_id: "NS-3", source_group: "Network Science", source_is_hub: false, target_id: "NS-4", target_group: "Network Science", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "NS-4", source_group: "Network Science", source_is_hub: false, target_id: "NS-5", target_group: "Network Science", target_is_hub: false, weight: 1, is_bridge: false },
  { source_id: "NS-5", source_group: "Network Science", source_is_hub: false, target_id: "NS-6", target_group: "Network Science", target_is_hub: false, weight: 2, is_bridge: false },

  // Cryptography (CR-0 hub, CR-1..CR-6 peers)
  { source_id: "CR-0", source_group: "Cryptography", source_is_hub: true, target_id: "CR-1", target_group: "Cryptography", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "CR-0", source_group: "Cryptography", source_is_hub: true, target_id: "CR-2", target_group: "Cryptography", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "CR-0", source_group: "Cryptography", source_is_hub: true, target_id: "CR-3", target_group: "Cryptography", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "CR-0", source_group: "Cryptography", source_is_hub: true, target_id: "CR-4", target_group: "Cryptography", target_is_hub: false, weight: 3, is_bridge: false },
  { source_id: "CR-0", source_group: "Cryptography", source_is_hub: true, target_id: "CR-5", target_group: "Cryptography", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "CR-0", source_group: "Cryptography", source_is_hub: true, target_id: "CR-6", target_group: "Cryptography", target_is_hub: false, weight: 3, is_bridge: false },
  { source_id: "CR-1", source_group: "Cryptography", source_is_hub: false, target_id: "CR-2", target_group: "Cryptography", target_is_hub: false, weight: 1, is_bridge: false },
  { source_id: "CR-2", source_group: "Cryptography", source_is_hub: false, target_id: "CR-3", target_group: "Cryptography", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "CR-3", source_group: "Cryptography", source_is_hub: false, target_id: "CR-4", target_group: "Cryptography", target_is_hub: false, weight: 2, is_bridge: false },
  { source_id: "CR-4", source_group: "Cryptography", source_is_hub: false, target_id: "CR-5", target_group: "Cryptography", target_is_hub: false, weight: 1, is_bridge: false },
  { source_id: "CR-5", source_group: "Cryptography", source_is_hub: false, target_id: "CR-6", target_group: "Cryptography", target_is_hub: false, weight: 1, is_bridge: false },

  // Inter-group hub bridges
  { source_id: "ML-0", source_group: "Machine Learning", source_is_hub: true, target_id: "RB-0", target_group: "Robotics", target_is_hub: true, weight: 1, is_bridge: true },
  { source_id: "RB-0", source_group: "Robotics", source_is_hub: true, target_id: "BI-0", target_group: "Bioinformatics", target_is_hub: true, weight: 1, is_bridge: true },
  { source_id: "BI-0", source_group: "Bioinformatics", source_is_hub: true, target_id: "NS-0", target_group: "Network Science", target_is_hub: true, weight: 1, is_bridge: true },
  { source_id: "NS-0", source_group: "Network Science", source_is_hub: true, target_id: "CR-0", target_group: "Cryptography", target_is_hub: true, weight: 1, is_bridge: true },
  { source_id: "CR-0", source_group: "Cryptography", source_is_hub: true, target_id: "ML-0", target_group: "Machine Learning", target_is_hub: true, weight: 1, is_bridge: true },
];

// Derive groups in order of first appearance across both columns
const groups: string[] = [];
for (const row of DATA) {
  const sg = String(row[SOURCE_GROUP_COL]);
  const tg = String(row[TARGET_GROUP_COL]);
  if (!groups.includes(sg)) groups.push(sg);
  if (!groups.includes(tg)) groups.push(tg);
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
const nodes: ForceNode[] = [];
const groupCounts = new Array(groups.length).fill(0);

for (const row of DATA) {
  const endpoints = [
    { id: String(row[SOURCE_ID_COL]), group: String(row[SOURCE_GROUP_COL]), isHub: Boolean(row[SOURCE_HUB_COL]) },
    { id: String(row[TARGET_ID_COL]), group: String(row[TARGET_GROUP_COL]), isHub: Boolean(row[TARGET_HUB_COL]) },
  ];
  for (const ep of endpoints) {
    if (!nodeIndexById.has(ep.id)) {
      const groupIndex = groups.indexOf(ep.group);
      const withinIndex = groupCounts[groupIndex];
      groupCounts[groupIndex] += 1;
      nodeIndexById.set(ep.id, nodes.length);
      nodes.push({
        id: ep.id,
        groupIndex,
        groupName: ep.group,
        isHub: ep.isHub,
        withinIndex,
        degree: 0,
        radius: MIN_NODE_R,
        x: 0,
        y: 0,
      });
    }
  }
}

interface ForceEdge {
  sourceIdx: number;
  targetIdx: number;
  weight: number;
  isBridge: boolean;
}

const edges: ForceEdge[] = [];
for (const row of DATA) {
  const a = nodeIndexById.get(String(row[SOURCE_ID_COL]))!;
  const b = nodeIndexById.get(String(row[TARGET_ID_COL]))!;
  const weight = Number(row[WEIGHT_COL]);
  const isBridge = Boolean(row[BRIDGE_COL]);
  edges.push({ sourceIdx: a, targetIdx: b, weight, isBridge });
  nodes[a].degree += 1;
  nodes[b].degree += 1;
}

const maxDegree = Math.max(1, ...nodes.map((n) => n.degree));
for (const node of nodes) {
  node.radius = MIN_NODE_R + (node.degree / maxDegree) * MAX_NODE_R_SPAN;
}

// Deterministic initial positions on a ring of group centers
let lcgState = 104729;
const ringRadius = SIM_AREA_SPAN * RING_RADIUS_SHARE;
const subringRadius = SIM_AREA_SPAN * SUBRING_RADIUS_SHARE;
const jitterSpan = SIM_AREA_SPAN * JITTER_SHARE;

for (const node of nodes) {
  const groupAngle = (node.groupIndex / groups.length) * Math.PI * 2;
  const centerX = Math.cos(groupAngle) * ringRadius;
  const centerY = Math.sin(groupAngle) * ringRadius;
  const groupCount = Math.max(1, groupCounts[node.groupIndex]);
  const withinAngle = (node.withinIndex / groupCount) * Math.PI * 2;
  lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
  const jx = (lcgState / 4294967296 - 0.5) * jitterSpan;
  lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
  const jy = (lcgState / 4294967296 - 0.5) * jitterSpan;
  node.x = centerX + Math.cos(withinAngle) * subringRadius + jx;
  node.y = centerY + Math.sin(withinAngle) * subringRadius + jy;
}

// Fruchterman-Reingold force-directed simulation (flat module-level statements)
const idealDistance = Math.sqrt((SIM_AREA_SPAN * SIM_AREA_SPAN) / nodes.length);
let temperature = SIM_AREA_SPAN * INITIAL_TEMP_SHARE;
const cooling = temperature / ITERATIONS;

for (let iter = 0; iter < ITERATIONS; iter += 1) {
  const dispX = new Array(nodes.length).fill(0);
  const dispY = new Array(nodes.length).fill(0);

  for (let i = 0; i < nodes.length; i += 1) {
    for (let j = i + 1; j < nodes.length; j += 1) {
      const dx = nodes[i].x - nodes[j].x;
      const dy = nodes[i].y - nodes[j].y;
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
    const dx = nodes[a].x - nodes[b].x;
    const dy = nodes[a].y - nodes[b].y;
    const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
    const force = ((dist * dist) / idealDistance) * (0.6 + edge.weight * 0.2);
    const fx = (dx / dist) * force;
    const fy = (dy / dist) * force;
    dispX[a] -= fx;
    dispY[a] -= fy;
    dispX[b] += fx;
    dispY[b] += fy;
  }

  for (let i = 0; i < nodes.length; i += 1) {
    dispX[i] -= nodes[i].x * GRAVITY_FACTOR;
    dispY[i] -= nodes[i].y * GRAVITY_FACTOR;
    const dist = Math.sqrt(dispX[i] * dispX[i] + dispY[i] * dispY[i]) || 0.01;
    const capped = Math.min(dist, temperature);
    nodes[i].x += (dispX[i] / dist) * capped;
    nodes[i].y += (dispY[i] / dist) * capped;
  }

  temperature = Math.max(temperature - cooling, 1);
}

// Square, padded domain derived from simulated node extent
const xs = nodes.map((n) => n.x);
const ys = nodes.map((n) => n.y);
const rawXMin = Math.min(...xs);
const rawXMax = Math.max(...xs);
const rawYMin = Math.min(...ys);
const rawYMax = Math.max(...ys);
const rawSpan = Math.max(rawXMax - rawXMin, rawYMax - rawYMin) || 1;
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
          x1={xScale(nodes[edge.sourceIdx].x)}
          y1={yScale(nodes[edge.sourceIdx].y)}
          x2={xScale(nodes[edge.targetIdx].x)}
          y2={yScale(nodes[edge.targetIdx].y)}
          stroke={t.inkSoft}
          strokeOpacity={edge.isBridge ? 0.22 : 0.4}
          strokeWidth={edge.isBridge ? 1.1 : 0.8 + edge.weight * 0.7}
          strokeDasharray={edge.isBridge ? "5,4" : undefined}
        />
      ))}
      {nodes.map((node) => (
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
                x={xScale(node.x) - (node.groupName.length * 4.4 + 8)}
                y={yScale(node.y) - node.radius - 24}
                width={node.groupName.length * 8.8 + 16}
                height={20}
                rx={4}
                fill={t.pageBg}
                fillOpacity={0.88}
              />
              <text
                x={xScale(node.x)}
                y={yScale(node.y) - node.radius - 10}
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
    </div>
  );
}
