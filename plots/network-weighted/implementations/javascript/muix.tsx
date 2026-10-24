// anyplot.ai
// network-weighted: Weighted Network Graph with Edge Thickness
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02
//# anyplot-orientation: square

import { useState } from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "network-weighted · javascript · muix · anyplot.ai";
const TITLE_H = 58;
const LEGEND_H = 112;
const AREA = 4.5;
const ITERATIONS = 500;
const INITIAL_TEMP = 0.12;
const COOLING_FACTOR = 0.99;
const PAD_MULT = 1.25;
const NODE_MIN_R = 15;
const NODE_MAX_R = 40;
const EDGE_MIN_W = 2;
const EDGE_MAX_W = 13;

// Columns: set these to your data's column names
const NODE_ID = "Lab code"; // role: node
const NODE_LABEL = "Research institute"; // role: label
const DOMAIN = "Research domain"; // role: group
const SOURCE = "Source lab"; // role: source
const TARGET = "Partner lab"; // role: target
const WEIGHT = "Co-authored papers"; // role: weight

// Data: replace this block with your own records
const nodes: Array<Record<string, string>> = [
  { [NODE_ID]: "GEN", [NODE_LABEL]: "Genomics Lab", [DOMAIN]: "Life Sciences" },
  { [NODE_ID]: "IMM", [NODE_LABEL]: "Immunology Institute", [DOMAIN]: "Life Sciences" },
  { [NODE_ID]: "NEU", [NODE_LABEL]: "Neuroscience Institute", [DOMAIN]: "Life Sciences" },
  { [NODE_ID]: "MAR", [NODE_LABEL]: "Marine Biology Station", [DOMAIN]: "Life Sciences" },
  { [NODE_ID]: "QPL", [NODE_LABEL]: "Quantum Physics Lab", [DOMAIN]: "Physical Sciences" },
  { [NODE_ID]: "MAT", [NODE_LABEL]: "Materials Science Institute", [DOMAIN]: "Physical Sciences" },
  { [NODE_ID]: "AST", [NODE_LABEL]: "Astrophysics Observatory", [DOMAIN]: "Physical Sciences" },
  { [NODE_ID]: "CLI", [NODE_LABEL]: "Climate Science Center", [DOMAIN]: "Physical Sciences" },
  { [NODE_ID]: "AIR", [NODE_LABEL]: "AI Research Center", [DOMAIN]: "Computer Science" },
  { [NODE_ID]: "DSI", [NODE_LABEL]: "Data Science Institute", [DOMAIN]: "Computer Science" },
  { [NODE_ID]: "ROB", [NODE_LABEL]: "Robotics Lab", [DOMAIN]: "Computer Science" },
  { [NODE_ID]: "CHE", [NODE_LABEL]: "Chemical Engineering Lab", [DOMAIN]: "Engineering" },
  { [NODE_ID]: "BIO", [NODE_LABEL]: "Bioengineering Institute", [DOMAIN]: "Engineering" },
  { [NODE_ID]: "ENV", [NODE_LABEL]: "Environmental Engineering Lab", [DOMAIN]: "Engineering" },
];

const data: Array<Record<string, string | number>> = [
  { [SOURCE]: "GEN", [TARGET]: "IMM", [WEIGHT]: 42 },
  { [SOURCE]: "GEN", [TARGET]: "NEU", [WEIGHT]: 16 },
  { [SOURCE]: "GEN", [TARGET]: "BIO", [WEIGHT]: 22 },
  { [SOURCE]: "IMM", [TARGET]: "BIO", [WEIGHT]: 12 },
  { [SOURCE]: "IMM", [TARGET]: "NEU", [WEIGHT]: 6 },
  { [SOURCE]: "NEU", [TARGET]: "AIR", [WEIGHT]: 19 },
  { [SOURCE]: "MAR", [TARGET]: "ENV", [WEIGHT]: 27 },
  { [SOURCE]: "MAR", [TARGET]: "CLI", [WEIGHT]: 31 },
  { [SOURCE]: "QPL", [TARGET]: "MAT", [WEIGHT]: 36 },
  { [SOURCE]: "QPL", [TARGET]: "AST", [WEIGHT]: 21 },
  { [SOURCE]: "MAT", [TARGET]: "CHE", [WEIGHT]: 33 },
  { [SOURCE]: "MAT", [TARGET]: "ENV", [WEIGHT]: 9 },
  { [SOURCE]: "AST", [TARGET]: "CLI", [WEIGHT]: 8 },
  { [SOURCE]: "CLI", [TARGET]: "ENV", [WEIGHT]: 24 },
  { [SOURCE]: "AIR", [TARGET]: "DSI", [WEIGHT]: 45 },
  { [SOURCE]: "AIR", [TARGET]: "ROB", [WEIGHT]: 29 },
  { [SOURCE]: "DSI", [TARGET]: "ROB", [WEIGHT]: 18 },
  { [SOURCE]: "DSI", [TARGET]: "GEN", [WEIGHT]: 15 },
  { [SOURCE]: "DSI", [TARGET]: "CLI", [WEIGHT]: 12 },
  { [SOURCE]: "DSI", [TARGET]: "MAT", [WEIGHT]: 7 },
  { [SOURCE]: "DSI", [TARGET]: "BIO", [WEIGHT]: 10 },
  { [SOURCE]: "ROB", [TARGET]: "BIO", [WEIGHT]: 14 },
  { [SOURCE]: "CHE", [TARGET]: "BIO", [WEIGHT]: 20 },
  { [SOURCE]: "CHE", [TARGET]: "ENV", [WEIGHT]: 17 },
];

// Plot: reads only data and the constants above
interface LabNode {
  id: string;
  label: string;
  domainName: string;
  domainIndex: number;
  weightedDegree: number;
  radius: number;
  x: number;
  y: number;
}

const domains: string[] = [];
const nodeIndexById = new Map<string, number>();
const layoutNodes: LabNode[] = [];

for (const row of nodes) {
  const id = String(row[NODE_ID]);
  const dom = String(row[DOMAIN]);
  if (!domains.includes(dom)) domains.push(dom);
  nodeIndexById.set(id, layoutNodes.length);
  layoutNodes.push({
    id,
    label: String(row[NODE_LABEL]),
    domainName: dom,
    domainIndex: domains.indexOf(dom),
    weightedDegree: 0,
    radius: NODE_MIN_R,
    x: 0,
    y: 0,
  });
}

interface LabEdge {
  sourceIdx: number;
  targetIdx: number;
  weight: number;
  strokeWidth: number;
  ratio: number;
}

const edges: LabEdge[] = [];
for (const row of data) {
  const sIdx = nodeIndexById.get(String(row[SOURCE]))!;
  const tIdx = nodeIndexById.get(String(row[TARGET]))!;
  const weight = Number(row[WEIGHT]);
  layoutNodes[sIdx].weightedDegree += weight;
  layoutNodes[tIdx].weightedDegree += weight;
  edges.push({ sourceIdx: sIdx, targetIdx: tIdx, weight, strokeWidth: EDGE_MIN_W, ratio: 0 });
}

const edgeWeights = edges.map((e) => e.weight);
const minWeight = Math.min(...edgeWeights);
const maxWeight = Math.max(...edgeWeights);
const weightSpan = maxWeight - minWeight;

for (const edge of edges) {
  edge.ratio = (edge.weight - minWeight) / weightSpan;
  edge.strokeWidth = EDGE_MIN_W + edge.ratio * (EDGE_MAX_W - EDGE_MIN_W);
}

const degrees = layoutNodes.map((n) => n.weightedDegree);
const minDegree = Math.min(...degrees);
const maxDegree = Math.max(...degrees);
const degreeSpan = maxDegree - minDegree;

for (const node of layoutNodes) {
  const ratio = (node.weightedDegree - minDegree) / degreeSpan;
  node.radius = NODE_MIN_R + ratio * (NODE_MAX_R - NODE_MIN_R);
}

let lcgState = 42;
const nCount = layoutNodes.length;
const kForce = Math.sqrt(AREA / nCount);

for (let i = 0; i < nCount; i += 1) {
  lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
  const rx = (lcgState / 4294967296) * 2 - 1;
  lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
  const ry = (lcgState / 4294967296) * 2 - 1;
  layoutNodes[i].x = rx;
  layoutNodes[i].y = ry;
}

let temperature = INITIAL_TEMP;
for (let iter = 0; iter < ITERATIONS; iter += 1) {
  const dispX = new Array<number>(nCount).fill(0);
  const dispY = new Array<number>(nCount).fill(0);

  for (let i = 0; i < nCount; i += 1) {
    for (let j = i + 1; j < nCount; j += 1) {
      const dx = layoutNodes[i].x - layoutNodes[j].x;
      const dy = layoutNodes[i].y - layoutNodes[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
      const force = (kForce * kForce) / dist;
      const ux = dx / dist;
      const uy = dy / dist;
      dispX[i] += ux * force;
      dispY[i] += uy * force;
      dispX[j] -= ux * force;
      dispY[j] -= uy * force;
    }
  }

  for (const edge of edges) {
    const i = edge.sourceIdx;
    const j = edge.targetIdx;
    const dx = layoutNodes[i].x - layoutNodes[j].x;
    const dy = layoutNodes[i].y - layoutNodes[j].y;
    const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
    const idealDist = kForce * (1.5 - 1.0 * edge.ratio);
    const force = (dist * dist) / idealDist;
    const ux = dx / dist;
    const uy = dy / dist;
    dispX[i] -= ux * force;
    dispY[i] -= uy * force;
    dispX[j] += ux * force;
    dispY[j] += uy * force;
  }

  for (let i = 0; i < nCount; i += 1) {
    const dx = dispX[i];
    const dy = dispY[i];
    const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
    const limited = Math.min(dist, temperature);
    layoutNodes[i].x += (dx / dist) * limited;
    layoutNodes[i].y += (dy / dist) * limited;
  }
  temperature *= COOLING_FACTOR;
}

const centroidX = layoutNodes.reduce((s, n) => s + n.x, 0) / nCount;
const centroidY = layoutNodes.reduce((s, n) => s + n.y, 0) / nCount;
for (const node of layoutNodes) {
  node.x -= centroidX;
  node.y -= centroidY;
}

const rangeX = Math.max(...layoutNodes.map((n) => Math.abs(n.x)));
const rangeY = Math.max(...layoutNodes.map((n) => Math.abs(n.y)));
const xHalf = rangeX * PAD_MULT;
const yHalf = rangeY * PAD_MULT;

const sortedEdges = [...edges].sort((a, b) => a.weight - b.weight);
const midWeight = Math.round((minWeight + maxWeight) / 2);
const weightSamples = [
  { weight: minWeight, strokeWidth: EDGE_MIN_W },
  {
    weight: midWeight,
    strokeWidth: EDGE_MIN_W + ((midWeight - minWeight) / weightSpan) * (EDGE_MAX_W - EDGE_MIN_W),
  },
  { weight: maxWeight, strokeWidth: EDGE_MAX_W },
];

interface HoverInfo {
  label: string;
  detail: string;
  x: number;
  y: number;
}

function WeightedNetworkOverlay({
  hover,
  onHoverChange,
}: {
  hover: HoverInfo | null;
  onHoverChange: (info: HoverInfo | null) => void;
}) {
  const xScale = useXScale();
  const yScale = useYScale();
  const drawingArea = useDrawingArea();

  return (
    <g>
      {sortedEdges.map((edge, i) => {
        const s = layoutNodes[edge.sourceIdx];
        const d = layoutNodes[edge.targetIdx];
        const x1 = Number(xScale(s.x));
        const y1 = Number(yScale(s.y));
        const x2 = Number(xScale(d.x));
        const y2 = Number(yScale(d.y));
        const tooltip: HoverInfo = {
          label: `${s.label} ↔ ${d.label}`,
          detail: `${edge.weight} (${WEIGHT})`,
          x: (x1 + x2) / 2,
          y: (y1 + y2) / 2,
        };
        return (
          <g key={`${s.id}-${d.id}-${i}`}>
            <line
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={t.ink}
              strokeOpacity={0.22 + edge.ratio * 0.4}
              strokeWidth={edge.strokeWidth}
              strokeLinecap="round"
            />
            <line
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="transparent"
              strokeWidth={Math.max(edge.strokeWidth, 18)}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => onHoverChange(tooltip)}
              onMouseLeave={() => onHoverChange(null)}
            />
          </g>
        );
      })}
      {layoutNodes.map((node) => {
        const cx = Number(xScale(node.x));
        const cy = Number(yScale(node.y));
        const radius = node.radius;
        const tooltip: HoverInfo = {
          label: node.label,
          detail: `${node.domainName} · weighted degree ${node.weightedDegree}`,
          x: cx,
          y: cy - radius - 10,
        };
        return (
          <g key={node.id}>
            <circle
              cx={cx}
              cy={cy}
              r={radius}
              fill={t.palette[node.domainIndex]}
              stroke={t.pageBg}
              strokeWidth={3}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => onHoverChange(tooltip)}
              onMouseLeave={() => onHoverChange(null)}
            />
            <rect
              x={cx - 21}
              y={cy - radius - 26}
              width={42}
              height={20}
              rx={4}
              fill={t.pageBg}
              fillOpacity={0.86}
              style={{ pointerEvents: "none" }}
            />
            <text
              x={cx}
              y={cy - radius - 11}
              textAnchor="middle"
              fontSize={16}
              fontWeight={600}
              fill={t.ink}
              style={{ pointerEvents: "none" }}
            >
              {node.id}
            </text>
          </g>
        );
      })}

      {hover && (
        <g style={{ pointerEvents: "none" }}>
          <rect
            x={Math.min(
              Math.max(
                hover.x - (Math.max(hover.label.length, hover.detail.length) * 8 + 24) / 2,
                8,
              ),
              drawingArea.left +
                drawingArea.width -
                (Math.max(hover.label.length, hover.detail.length) * 8 + 24) -
                8,
            )}
            y={Math.max(hover.y - 52 - 12, 8)}
            width={Math.max(hover.label.length, hover.detail.length) * 8 + 24}
            height={52}
            rx={6}
            fill={t.elevatedBg}
            stroke={t.inkSoft}
            strokeOpacity={0.4}
          />
          <text
            x={hover.x}
            y={Math.max(hover.y - 52 - 12, 8) + 21}
            textAnchor="middle"
            fontSize={14}
            fontWeight={600}
            fill={t.ink}
          >
            {hover.label}
          </text>
          <text
            x={hover.x}
            y={Math.max(hover.y - 52 - 12, 8) + 40}
            textAnchor="middle"
            fontSize={14}
            fill={t.inkSoft}
          >
            {hover.detail}
          </text>
        </g>
      )}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const [hover, setHover] = useState<HoverInfo | null>(null);
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
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</span>
      </div>
      <ChartsContainer
        width={width}
        height={chartHeight}
        margin={{ top: 28, right: 60, bottom: 28, left: 60 }}
        series={[]}
        skipAnimation
        disableAxisListener
        xAxis={[{ scaleType: "linear", min: -xHalf, max: xHalf, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: -yHalf, max: yHalf, position: "none" }]}
      >
        <WeightedNetworkOverlay hover={hover} onHoverChange={setHover} />
      </ChartsContainer>
      <div
        style={{
          minHeight: LEGEND_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 12,
          padding: "8px 40px 14px",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            justifyContent: "center",
            gap: 28,
          }}
        >
          {domains.map((name, i) => (
            <span
              key={name}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                fontSize: 15,
                color: t.inkSoft,
              }}
            >
              <span
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: "50%",
                  backgroundColor: t.palette[i],
                  display: "inline-block",
                }}
              />
              <span>{name}</span>
            </span>
          ))}
        </div>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            justifyContent: "center",
            gap: 24,
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          <span>{`Edge width = ${WEIGHT} · node size = weighted degree:`}</span>
          {weightSamples.map((sample) => (
            <span
              key={sample.weight}
              style={{ display: "inline-flex", alignItems: "center", gap: 8 }}
            >
              <svg width={52} height={16}>
                <line
                  x1={4}
                  y1={8}
                  x2={48}
                  y2={8}
                  stroke={t.ink}
                  strokeOpacity={0.55}
                  strokeWidth={sample.strokeWidth}
                  strokeLinecap="round"
                />
              </svg>
              <span>{sample.weight}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
