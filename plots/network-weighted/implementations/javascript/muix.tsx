// anyplot.ai
// network-weighted: Weighted Network Graph with Edge Thickness
// Library: muix 9.x | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-02
//# anyplot-orientation: square

import * as React from "react";
import { useState } from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "network-weighted · javascript · muix · anyplot.ai";
const TITLE_H = 58;
const AREA = 4.5;
const ITERATIONS = 500;
const INITIAL_TEMP = 0.12;
const COOLING_FACTOR = 0.99;
const PAD_MULT = 1.25;
const NODE_MIN_R = 15;
const NODE_MAX_R = 40;
const EDGE_MIN_W = 2;
const EDGE_MAX_W = 13;

const SOURCE_ID_COL = "source_id";
const SOURCE_LABEL_COL = "source_label";
const SOURCE_DOMAIN_COL = "source_domain";
const TARGET_ID_COL = "target_id";
const TARGET_LABEL_COL = "target_label";
const TARGET_DOMAIN_COL = "target_domain";
const WEIGHT_COL = "coauthored_papers";

// Data: research-lab co-authorship network (flat scalar edge records)
const DATA: Array<Record<string, string | number>> = [
  { source_id: "GEN", source_label: "Genomics Lab", source_domain: "Life Sciences", target_id: "IMM", target_label: "Immunology Institute", target_domain: "Life Sciences", coauthored_papers: 42 },
  { source_id: "GEN", source_label: "Genomics Lab", source_domain: "Life Sciences", target_id: "NEU", target_label: "Neuroscience Institute", target_domain: "Life Sciences", coauthored_papers: 16 },
  { source_id: "GEN", source_label: "Genomics Lab", source_domain: "Life Sciences", target_id: "BIO", target_label: "Bioengineering Institute", target_domain: "Engineering", coauthored_papers: 22 },
  { source_id: "IMM", source_label: "Immunology Institute", source_domain: "Life Sciences", target_id: "BIO", target_label: "Bioengineering Institute", target_domain: "Engineering", coauthored_papers: 12 },
  { source_id: "IMM", source_label: "Immunology Institute", source_domain: "Life Sciences", target_id: "NEU", target_label: "Neuroscience Institute", target_domain: "Life Sciences", coauthored_papers: 6 },
  { source_id: "NEU", source_label: "Neuroscience Institute", source_domain: "Life Sciences", target_id: "AIR", target_label: "AI Research Center", target_domain: "Computer Science", coauthored_papers: 19 },
  { source_id: "MAR", source_label: "Marine Biology Station", source_domain: "Life Sciences", target_id: "ENV", target_label: "Environmental Engineering Lab", target_domain: "Engineering", coauthored_papers: 27 },
  { source_id: "MAR", source_label: "Marine Biology Station", source_domain: "Life Sciences", target_id: "CLI", target_label: "Climate Science Center", target_domain: "Physical Sciences", coauthored_papers: 31 },
  { source_id: "QPL", source_label: "Quantum Physics Lab", source_domain: "Physical Sciences", target_id: "MAT", target_label: "Materials Science Institute", target_domain: "Physical Sciences", coauthored_papers: 36 },
  { source_id: "QPL", source_label: "Quantum Physics Lab", source_domain: "Physical Sciences", target_id: "AST", target_label: "Astrophysics Observatory", target_domain: "Physical Sciences", coauthored_papers: 21 },
  { source_id: "MAT", source_label: "Materials Science Institute", source_domain: "Physical Sciences", target_id: "CHE", target_label: "Chemical Engineering Lab", target_domain: "Engineering", coauthored_papers: 33 },
  { source_id: "MAT", source_label: "Materials Science Institute", source_domain: "Physical Sciences", target_id: "ENV", target_label: "Environmental Engineering Lab", target_domain: "Engineering", coauthored_papers: 9 },
  { source_id: "AST", source_label: "Astrophysics Observatory", source_domain: "Physical Sciences", target_id: "CLI", target_label: "Climate Science Center", target_domain: "Physical Sciences", coauthored_papers: 8 },
  { source_id: "CLI", source_label: "Climate Science Center", source_domain: "Physical Sciences", target_id: "ENV", target_label: "Environmental Engineering Lab", target_domain: "Engineering", coauthored_papers: 24 },
  { source_id: "AIR", source_label: "AI Research Center", source_domain: "Computer Science", target_id: "DSI", target_label: "Data Science Institute", target_domain: "Computer Science", coauthored_papers: 45 },
  { source_id: "AIR", source_label: "AI Research Center", source_domain: "Computer Science", target_id: "ROB", target_label: "Robotics Lab", target_domain: "Computer Science", coauthored_papers: 29 },
  { source_id: "DSI", source_label: "Data Science Institute", source_domain: "Computer Science", target_id: "ROB", target_label: "Robotics Lab", target_domain: "Computer Science", coauthored_papers: 18 },
  { source_id: "DSI", source_label: "Data Science Institute", source_domain: "Computer Science", target_id: "GEN", target_label: "Genomics Lab", target_domain: "Life Sciences", coauthored_papers: 15 },
  { source_id: "DSI", source_label: "Data Science Institute", source_domain: "Computer Science", target_id: "CLI", target_label: "Climate Science Center", target_domain: "Physical Sciences", coauthored_papers: 12 },
  { source_id: "DSI", source_label: "Data Science Institute", source_domain: "Computer Science", target_id: "MAT", target_label: "Materials Science Institute", target_domain: "Physical Sciences", coauthored_papers: 7 },
  { source_id: "DSI", source_label: "Data Science Institute", source_domain: "Computer Science", target_id: "BIO", target_label: "Bioengineering Institute", target_domain: "Engineering", coauthored_papers: 10 },
  { source_id: "ROB", source_label: "Robotics Lab", source_domain: "Computer Science", target_id: "BIO", target_label: "Bioengineering Institute", target_domain: "Engineering", coauthored_papers: 14 },
  { source_id: "CHE", source_label: "Chemical Engineering Lab", source_domain: "Engineering", target_id: "BIO", target_label: "Bioengineering Institute", target_domain: "Engineering", coauthored_papers: 20 },
  { source_id: "CHE", source_label: "Chemical Engineering Lab", source_domain: "Engineering", target_id: "ENV", target_label: "Environmental Engineering Lab", target_domain: "Engineering", coauthored_papers: 17 },
];

// Derive domains in canonical order of first appearance across both columns
const domains: string[] = [];
for (const row of DATA) {
  const sd = String(row[SOURCE_DOMAIN_COL]);
  const td = String(row[TARGET_DOMAIN_COL]);
  if (!domains.includes(sd)) domains.push(sd);
}
for (const row of DATA) {
  const td = String(row[TARGET_DOMAIN_COL]);
  if (!domains.includes(td)) domains.push(td);
}

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

const nodeIndexById = new Map<string, number>();
const nodes: LabNode[] = [];

for (const row of DATA) {
  const sId = String(row[SOURCE_ID_COL]);
  if (!nodeIndexById.has(sId)) {
    const sDom = String(row[SOURCE_DOMAIN_COL]);
    nodeIndexById.set(sId, nodes.length);
    nodes.push({
      id: sId,
      label: String(row[SOURCE_LABEL_COL]),
      domainName: sDom,
      domainIndex: domains.indexOf(sDom),
      weightedDegree: 0,
      radius: NODE_MIN_R,
      x: 0,
      y: 0,
    });
  }
}
for (const row of DATA) {
  const tId = String(row[TARGET_ID_COL]);
  if (!nodeIndexById.has(tId)) {
    const tDom = String(row[TARGET_DOMAIN_COL]);
    nodeIndexById.set(tId, nodes.length);
    nodes.push({
      id: tId,
      label: String(row[TARGET_LABEL_COL]),
      domainName: tDom,
      domainIndex: domains.indexOf(tDom),
      weightedDegree: 0,
      radius: NODE_MIN_R,
      x: 0,
      y: 0,
    });
  }
}

interface LabEdge {
  sourceIdx: number;
  targetIdx: number;
  weight: number;
  strokeWidth: number;
  ratio: number;
}

const edges: LabEdge[] = [];
for (const row of DATA) {
  const sIdx = nodeIndexById.get(String(row[SOURCE_ID_COL]))!;
  const tIdx = nodeIndexById.get(String(row[TARGET_ID_COL]))!;
  const weight = Number(row[WEIGHT_COL]);
  nodes[sIdx].weightedDegree += weight;
  nodes[tIdx].weightedDegree += weight;
  edges.push({ sourceIdx: sIdx, targetIdx: tIdx, weight, strokeWidth: EDGE_MIN_W, ratio: 0 });
}

const edgeWeights = edges.map((e) => e.weight);
const MIN_WEIGHT = Math.min(...edgeWeights);
const MAX_WEIGHT = Math.max(...edgeWeights);
const weightSpan = MAX_WEIGHT - MIN_WEIGHT || 1;

for (const edge of edges) {
  edge.ratio = (edge.weight - MIN_WEIGHT) / weightSpan;
  edge.strokeWidth = EDGE_MIN_W + edge.ratio * (EDGE_MAX_W - EDGE_MIN_W);
}

const degrees = nodes.map((n) => n.weightedDegree);
const MIN_DEGREE = Math.min(...degrees);
const MAX_DEGREE = Math.max(...degrees);
const degreeSpan = MAX_DEGREE - MIN_DEGREE || 1;

for (const node of nodes) {
  const ratio = (node.weightedDegree - MIN_DEGREE) / degreeSpan;
  node.radius = NODE_MIN_R + ratio * (NODE_MAX_R - NODE_MIN_R);
}

// Fruchterman-Reingold force-directed layout with weighted attraction
let lcgState = 42;
const N = nodes.length;
const K = Math.sqrt(AREA / N);

for (let i = 0; i < N; i += 1) {
  lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
  const rx = (lcgState / 4294967296) * 2 - 1;
  lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
  const ry = (lcgState / 4294967296) * 2 - 1;
  nodes[i].x = rx;
  nodes[i].y = ry;
}

let temperature = INITIAL_TEMP;
for (let iter = 0; iter < ITERATIONS; iter += 1) {
  const dispX = new Array(N).fill(0);
  const dispY = new Array(N).fill(0);

  for (let i = 0; i < N; i += 1) {
    for (let j = i + 1; j < N; j += 1) {
      const dx = nodes[i].x - nodes[j].x;
      const dy = nodes[i].y - nodes[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
      const force = (K * K) / dist;
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
    const dx = nodes[i].x - nodes[j].x;
    const dy = nodes[i].y - nodes[j].y;
    const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
    const idealDist = K * (1.5 - 1.0 * edge.ratio);
    const force = (dist * dist) / idealDist;
    const ux = dx / dist;
    const uy = dy / dist;
    dispX[i] -= ux * force;
    dispY[i] -= uy * force;
    dispX[j] += ux * force;
    dispY[j] += uy * force;
  }

  for (let i = 0; i < N; i += 1) {
    const dx = dispX[i];
    const dy = dispY[i];
    const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
    const limited = Math.min(dist, temperature);
    nodes[i].x += (dx / dist) * limited;
    nodes[i].y += (dy / dist) * limited;
  }
  temperature *= COOLING_FACTOR;
}

const centroidX = nodes.reduce((s, n) => s + n.x, 0) / N;
const centroidY = nodes.reduce((s, n) => s + n.y, 0) / N;
for (const node of nodes) {
  node.x -= centroidX;
  node.y -= centroidY;
}

const rangeX = Math.max(...nodes.map((n) => Math.abs(n.x))) || 1;
const rangeY = Math.max(...nodes.map((n) => Math.abs(n.y))) || 1;
const X_HALF = rangeX * PAD_MULT;
const Y_HALF = rangeY * PAD_MULT;

// Draw heaviest edges last so the strongest collaborations stay legible on top
const sortedEdges = [...edges].sort((a, b) => a.weight - b.weight);
const weightSamples = [
  { weight: MIN_WEIGHT, strokeWidth: EDGE_MIN_W },
  {
    weight: Math.round((MIN_WEIGHT + MAX_WEIGHT) / 2),
    strokeWidth: EDGE_MIN_W + ((Math.round((MIN_WEIGHT + MAX_WEIGHT) / 2) - MIN_WEIGHT) / weightSpan) * (EDGE_MAX_W - EDGE_MIN_W),
  },
  { weight: MAX_WEIGHT, strokeWidth: EDGE_MAX_W },
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

  const rowY = drawingArea.top + drawingArea.height + 42;
  const swatchR = 9;
  const groupGap = 225;
  const weightRowY = rowY + 52;
  const weightStartX = drawingArea.left;

  return (
    <g>
      {sortedEdges.map((edge, i) => {
        const s = nodes[edge.sourceIdx];
        const d = nodes[edge.targetIdx];
        const x1 = xScale(s.x);
        const y1 = yScale(s.y);
        const x2 = xScale(d.x);
        const y2 = yScale(d.y);
        const tooltip: HoverInfo = {
          label: `${s.label} ↔ ${d.label}`,
          detail: `${edge.weight} co-authored papers`,
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
      {nodes.map((node) => {
        const cx = xScale(node.x);
        const cy = yScale(node.y);
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

      {/* Domain legend + edge weight scale */}
      <g>
        {domains.map((name, i) => {
          const x = drawingArea.left + i * groupGap;
          return (
            <g key={name}>
              <circle cx={x} cy={rowY} r={swatchR} fill={t.palette[i]} />
              <text x={x + swatchR + 8} y={rowY + 5} fontSize={16} fill={t.inkSoft}>
                {name}
              </text>
            </g>
          );
        })}
        <text x={weightStartX} y={weightRowY - 14} fontSize={14} fill={t.inkSoft}>
          Edge width = co-authored papers · node size = weighted degree
        </text>
        {weightSamples.map((sample, i) => {
          const x = weightStartX + i * 140;
          const lineY = weightRowY + 12;
          return (
            <g key={sample.weight}>
              <line
                x1={x}
                y1={lineY}
                x2={x + 60}
                y2={lineY}
                stroke={t.ink}
                strokeOpacity={0.55}
                strokeWidth={sample.strokeWidth}
                strokeLinecap="round"
              />
              <text x={x + 30} y={lineY + 22} textAnchor="middle" fontSize={14} fill={t.inkSoft}>
                {sample.weight}
              </text>
            </g>
          );
        })}
      </g>

      {/* Hover tooltip */}
      {hover && (
        <g style={{ pointerEvents: "none" }}>
          <rect
            x={Math.min(
              Math.max(hover.x - (Math.max(hover.label.length, hover.detail.length) * 8 + 24) / 2, 8),
              drawingArea.left + drawingArea.width - (Math.max(hover.label.length, hover.detail.length) * 8 + 24) - 8,
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
        height={height - TITLE_H}
        margin={{ top: 28, right: 60, bottom: 155, left: 60 }}
        series={[]}
        skipAnimation
        disableAxisListener
        xAxis={[{ scaleType: "linear", min: -X_HALF, max: X_HALF, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: -Y_HALF, max: Y_HALF, position: "none" }]}
      >
        <WeightedNetworkOverlay hover={hover} onHoverChange={setHover} />
      </ChartsContainer>
    </div>
  );
}
