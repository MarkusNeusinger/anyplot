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
const CAPTION_H = 38;
const CHART_MARGIN = 8;
const SIM_AREA_SPAN = 1000;
const RING_RADIUS_SHARE = 0.26;
const SUBRING_RADIUS_SHARE = 0.07;
const JITTER_SHARE = 0.024;
const ITERATIONS = 300;
const INITIAL_TEMP_SHARE = 0.08;
const GRAVITY_FACTOR = 0.01;
const ROTATION_STEPS = 180;
const PAD_X_PX = 80;
const PAD_Y_PX = 56;
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
  { [NODE]: "Okafor", [GROUP]: "Machine Learning" },
  { [NODE]: "Lindqvist", [GROUP]: "Machine Learning" },
  { [NODE]: "Tanaka", [GROUP]: "Machine Learning" },
  { [NODE]: "Moreau", [GROUP]: "Machine Learning" },
  { [NODE]: "Haddad", [GROUP]: "Machine Learning" },
  { [NODE]: "Silva", [GROUP]: "Machine Learning" },
  { [NODE]: "Kowalski", [GROUP]: "Machine Learning" },
  { [NODE]: "Brennan", [GROUP]: "Machine Learning" },

  // Robotics (6 researchers)
  { [NODE]: "Nakamura", [GROUP]: "Robotics" },
  { [NODE]: "Fischer", [GROUP]: "Robotics" },
  { [NODE]: "Adeyemi", [GROUP]: "Robotics" },
  { [NODE]: "Rossi", [GROUP]: "Robotics" },
  { [NODE]: "Petrov", [GROUP]: "Robotics" },
  { [NODE]: "Chen", [GROUP]: "Robotics" },

  // Bioinformatics (7 researchers)
  { [NODE]: "Iyer", [GROUP]: "Bioinformatics" },
  { [NODE]: "Novak", [GROUP]: "Bioinformatics" },
  { [NODE]: "Garcia", [GROUP]: "Bioinformatics" },
  { [NODE]: "Holm", [GROUP]: "Bioinformatics" },
  { [NODE]: "Abiodun", [GROUP]: "Bioinformatics" },
  { [NODE]: "Larsen", [GROUP]: "Bioinformatics" },
  { [NODE]: "Wojcik", [GROUP]: "Bioinformatics" },

  // Network Science (5 researchers)
  { [NODE]: "Varga", [GROUP]: "Network Science" },
  { [NODE]: "Duarte", [GROUP]: "Network Science" },
  { [NODE]: "Sato", [GROUP]: "Network Science" },
  { [NODE]: "Keller", [GROUP]: "Network Science" },
  { [NODE]: "Amari", [GROUP]: "Network Science" },

  // Cryptography (6 researchers)
  { [NODE]: "Ivanova", [GROUP]: "Cryptography" },
  { [NODE]: "Osei", [GROUP]: "Cryptography" },
  { [NODE]: "Bauer", [GROUP]: "Cryptography" },
  { [NODE]: "Mendez", [GROUP]: "Cryptography" },
  { [NODE]: "Park", [GROUP]: "Cryptography" },
  { [NODE]: "Quinn", [GROUP]: "Cryptography" },
];

const data: Array<Record<string, string | number>> = [
  // Machine Learning: a lab lead with a dense core and two sub-teams
  { [SOURCE]: "Okafor", [TARGET]: "Lindqvist", [WEIGHT]: 6 },
  { [SOURCE]: "Okafor", [TARGET]: "Tanaka", [WEIGHT]: 4 },
  { [SOURCE]: "Okafor", [TARGET]: "Moreau", [WEIGHT]: 3 },
  { [SOURCE]: "Okafor", [TARGET]: "Haddad", [WEIGHT]: 2 },
  { [SOURCE]: "Lindqvist", [TARGET]: "Tanaka", [WEIGHT]: 3 },
  { [SOURCE]: "Lindqvist", [TARGET]: "Silva", [WEIGHT]: 2 },
  { [SOURCE]: "Tanaka", [TARGET]: "Kowalski", [WEIGHT]: 1 },
  { [SOURCE]: "Silva", [TARGET]: "Kowalski", [WEIGHT]: 4 },
  { [SOURCE]: "Silva", [TARGET]: "Haddad", [WEIGHT]: 1 },
  { [SOURCE]: "Haddad", [TARGET]: "Brennan", [WEIGHT]: 2 },
  { [SOURCE]: "Moreau", [TARGET]: "Brennan", [WEIGHT]: 1 },

  // Robotics: two close collaborators carry the group
  { [SOURCE]: "Nakamura", [TARGET]: "Fischer", [WEIGHT]: 5 },
  { [SOURCE]: "Nakamura", [TARGET]: "Adeyemi", [WEIGHT]: 2 },
  { [SOURCE]: "Fischer", [TARGET]: "Rossi", [WEIGHT]: 3 },
  { [SOURCE]: "Fischer", [TARGET]: "Petrov", [WEIGHT]: 2 },
  { [SOURCE]: "Rossi", [TARGET]: "Petrov", [WEIGHT]: 4 },
  { [SOURCE]: "Adeyemi", [TARGET]: "Chen", [WEIGHT]: 1 },
  { [SOURCE]: "Petrov", [TARGET]: "Chen", [WEIGHT]: 2 },

  // Bioinformatics: a star around one core-facility head
  { [SOURCE]: "Iyer", [TARGET]: "Novak", [WEIGHT]: 4 },
  { [SOURCE]: "Iyer", [TARGET]: "Garcia", [WEIGHT]: 5 },
  { [SOURCE]: "Iyer", [TARGET]: "Holm", [WEIGHT]: 3 },
  { [SOURCE]: "Iyer", [TARGET]: "Abiodun", [WEIGHT]: 2 },
  { [SOURCE]: "Iyer", [TARGET]: "Larsen", [WEIGHT]: 3 },
  { [SOURCE]: "Iyer", [TARGET]: "Wojcik", [WEIGHT]: 1 },
  { [SOURCE]: "Novak", [TARGET]: "Garcia", [WEIGHT]: 2 },
  { [SOURCE]: "Holm", [TARGET]: "Larsen", [WEIGHT]: 2 },
  { [SOURCE]: "Abiodun", [TARGET]: "Wojcik", [WEIGHT]: 3 },

  // Network Science: a small loop with one outlier
  { [SOURCE]: "Varga", [TARGET]: "Duarte", [WEIGHT]: 3 },
  { [SOURCE]: "Duarte", [TARGET]: "Sato", [WEIGHT]: 2 },
  { [SOURCE]: "Sato", [TARGET]: "Keller", [WEIGHT]: 4 },
  { [SOURCE]: "Keller", [TARGET]: "Varga", [WEIGHT]: 1 },
  { [SOURCE]: "Duarte", [TARGET]: "Amari", [WEIGHT]: 2 },

  // Cryptography: a tight trio trailing into a chain
  { [SOURCE]: "Ivanova", [TARGET]: "Osei", [WEIGHT]: 5 },
  { [SOURCE]: "Ivanova", [TARGET]: "Bauer", [WEIGHT]: 4 },
  { [SOURCE]: "Osei", [TARGET]: "Bauer", [WEIGHT]: 3 },
  { [SOURCE]: "Bauer", [TARGET]: "Mendez", [WEIGHT]: 2 },
  { [SOURCE]: "Mendez", [TARGET]: "Park", [WEIGHT]: 3 },
  { [SOURCE]: "Park", [TARGET]: "Quinn", [WEIGHT]: 1 },

  // Cross-field collaborations
  { [SOURCE]: "Okafor", [TARGET]: "Nakamura", [WEIGHT]: 3 },
  { [SOURCE]: "Tanaka", [TARGET]: "Iyer", [WEIGHT]: 2 },
  { [SOURCE]: "Kowalski", [TARGET]: "Fischer", [WEIGHT]: 1 },
  { [SOURCE]: "Garcia", [TARGET]: "Duarte", [WEIGHT]: 2 },
  { [SOURCE]: "Sato", [TARGET]: "Silva", [WEIGHT]: 1 },
  { [SOURCE]: "Keller", [TARGET]: "Mendez", [WEIGHT]: 1 },
  { [SOURCE]: "Moreau", [TARGET]: "Osei", [WEIGHT]: 2 },
  { [SOURCE]: "Chen", [TARGET]: "Holm", [WEIGHT]: 1 },
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
const wSpan = maxW - minW || 1;
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

// A force layout has no meaningful orientation: rotate it to the angle that
// lets it fill the drawing area best, then fit the domain to the pixel aspect
const plotW = window.ANYPLOT_SIZE.width - CHART_MARGIN * 2;
const plotH = window.ANYPLOT_SIZE.height - TITLE_H - LEGEND_H - CAPTION_H - CHART_MARGIN * 2;
const fitW = plotW - PAD_X_PX * 2;
const fitH = plotH - PAD_Y_PX * 2;

let bestAngle = 0;
let bestScale = 0;
for (let step = 0; step < ROTATION_STEPS; step += 1) {
  const angle = (step / ROTATION_STEPS) * Math.PI;
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const rx = layoutNodes.map((n) => n.x * cos - n.y * sin);
  const ry = layoutNodes.map((n) => n.x * sin + n.y * cos);
  const scale = Math.min(
    fitW / (Math.max(...rx) - Math.min(...rx)),
    fitH / (Math.max(...ry) - Math.min(...ry)),
  );
  if (scale > bestScale) {
    bestScale = scale;
    bestAngle = angle;
  }
}

for (const node of layoutNodes) {
  const x = node.x * Math.cos(bestAngle) - node.y * Math.sin(bestAngle);
  const y = node.x * Math.sin(bestAngle) + node.y * Math.cos(bestAngle);
  node.x = x;
  node.y = y;
}

const xs = layoutNodes.map((n) => n.x);
const ys = layoutNodes.map((n) => n.y);
const xMid = (Math.min(...xs) + Math.max(...xs)) / 2;
const yMid = (Math.min(...ys) + Math.max(...ys)) / 2;
const halfSpanX = plotW / 2 / bestScale;
const halfSpanY = plotH / 2 / bestScale;
const domain = {
  xMin: xMid - halfSpanX,
  xMax: xMid + halfSpanX,
  yMin: yMid - halfSpanY,
  yMax: yMid + halfSpanY,
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
          strokeOpacity={edge.isBridge ? 0.32 : 0.42}
          strokeWidth={1.1 + edge.wRatio * 2.2}
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
        margin={{ top: CHART_MARGIN, bottom: CHART_MARGIN, left: CHART_MARGIN, right: CHART_MARGIN }}
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
          fontSize: 15,
          color: t.inkSoft,
        }}
      >
        {`Node size = degree · Halo & label = top hub per ${GROUP} · Edge width = ${WEIGHT} · Dashed = cross-field link`}
      </div>
    </div>
  );
}
