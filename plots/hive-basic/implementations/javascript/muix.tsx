// anyplot.ai
// hive-basic: Basic Hive Plot
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 85/100 | Updated: 2026-10-24
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = '"Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, sans-serif';
const MONO = '"JetBrains Mono", "SFMono-Regular", Menlo, monospace';
const START_ANGLE_DEG = 90;
const INNER_R = 18;
const OUTER_R = 100;
const CONTROL_R = 18;
const SPOKE_HUB_SHARE = 0.55;
const SPOKE_RIM_SHARE = 1.05;
const LABEL_R_SHARE = 1.16;
const DOMAIN_PAD_SHARE = 1.14;

// Columns: set these to your data's column names
const NODE = "Module"; // role: nodes
const LAYER = "Layer"; // role: axis_attribute
const SOURCE = "Source module"; // role: source
const TARGET = "Target module"; // role: target
const WEIGHT = "Dependency weight"; // role: weight

// Data: replace this block with your own records
const SEED_LAYERS = [
  { label: "Core", count: 12 },
  { label: "Utility", count: 10 },
  { label: "Interface", count: 10 },
];
const SEED_PAIRS: Array<[number, number]> = [
  [0, 1],
  [1, 2],
  [2, 0],
];
const EDGES_PER_PAIR = 24;

const nodes: Array<{
  [NODE]: string;
  [LAYER]: string;
}> = [];
for (let l = 0; l < SEED_LAYERS.length; l += 1) {
  const layer = SEED_LAYERS[l];
  for (let i = 0; i < layer.count; i += 1) {
    nodes.push({
      [NODE]: `${layer.label}-${i + 1}`,
      [LAYER]: layer.label,
    });
  }
}

let lcgState = 42 >>> 0;
const edgeKeys = new Set<string>();
const data: Array<{
  [SOURCE]: string;
  [TARGET]: string;
  [WEIGHT]: number;
}> = [];

for (let p = 0; p < SEED_PAIRS.length; p += 1) {
  const layerA = SEED_LAYERS[SEED_PAIRS[p][0]];
  const layerB = SEED_LAYERS[SEED_PAIRS[p][1]];
  let added = 0;
  let attempts = 0;
  while (added < EDGES_PER_PAIR && attempts < EDGES_PER_PAIR * 6) {
    attempts += 1;
    lcgState = (Math.imul(lcgState, 1664525) + 1013904223) >>> 0;
    const idxA = Math.floor((lcgState / 4294967296) * layerA.count);
    lcgState = (Math.imul(lcgState, 1664525) + 1013904223) >>> 0;
    const idxB = Math.floor((lcgState / 4294967296) * layerB.count);
    lcgState = (Math.imul(lcgState, 1664525) + 1013904223) >>> 0;
    const weight = 1 + Math.floor((lcgState / 4294967296) * 5);

    const srcId = `${layerA.label}-${idxA + 1}`;
    const tgtId = `${layerB.label}-${idxB + 1}`;
    const key = `${srcId}|${tgtId}`;
    if (edgeKeys.has(key)) continue;
    edgeKeys.add(key);

    data.push({
      [SOURCE]: srcId,
      [TARGET]: tgtId,
      [WEIGHT]: weight,
    });
    added += 1;
  }
}

// Plot: reads only data and the constants above
const axisLabels = Array.from(new Set(nodes.map((n) => n[LAYER])));

const AXES = axisLabels.map((label, idx) => {
  const angle = START_ANGLE_DEG + (idx * 360) / axisLabels.length;
  const rad = (angle * Math.PI) / 180;
  return {
    id: label,
    label,
    index: idx,
    angle,
    cos: Math.cos(rad),
    sin: Math.sin(rad),
    color: t.palette[idx],
  };
});
const axisById = Object.fromEntries(AXES.map((a) => [a.id, a]));

interface HiveNode {
  id: string;
  axis: string;
  degree: number;
  weightSum: number;
  r: number;
  x: number;
  y: number;
}

const nodeMap = new Map<string, HiveNode>();
for (let i = 0; i < nodes.length; i += 1) {
  const row = nodes[i];
  nodeMap.set(row[NODE], {
    id: row[NODE],
    axis: row[LAYER],
    degree: 0,
    weightSum: 0,
    r: INNER_R,
    x: 0,
    y: 0,
  });
}

for (let i = 0; i < data.length; i += 1) {
  const row = data[i];
  const srcNode = nodeMap.get(row[SOURCE]);
  const tgtNode = nodeMap.get(row[TARGET]);
  const w = row[WEIGHT];
  if (srcNode) {
    srcNode.degree += 1;
    srcNode.weightSum += w;
  }
  if (tgtNode) {
    tgtNode.degree += 1;
    tgtNode.weightSum += w;
  }
}

const allNodes = Array.from(nodeMap.values());
const degrees = allNodes.map((n) => n.degree);
const MIN_DEGREE = Math.min(...degrees);
const MAX_DEGREE = Math.max(...degrees);
const weights = data.map((d) => d[WEIGHT]);
const MIN_WEIGHT = Math.min(...weights);
const MAX_WEIGHT = Math.max(...weights);

const nodesByAxis: Record<string, HiveNode[]> = {};
for (let a = 0; a < AXES.length; a += 1) {
  const axis = AXES[a];
  const ordered = allNodes
    .filter((n) => n.axis === axis.id)
    .sort((n1, n2) => n1.degree - n2.degree || n1.id.localeCompare(n2.id));
  for (let i = 0; i < ordered.length; i += 1) {
    const node = ordered[i];
    const r =
      ordered.length > 1
        ? INNER_R + (i / (ordered.length - 1)) * (OUTER_R - INNER_R)
        : OUTER_R;
    node.r = r;
    node.x = r * axis.cos;
    node.y = r * axis.sin;
  }
  nodesByAxis[axis.id] = ordered;
}

const LABEL_R = OUTER_R * LABEL_R_SHARE;
const axisTipXs = AXES.map((a) => LABEL_R * a.cos);
const axisTipYs = AXES.map((a) => LABEL_R * a.sin);
const minTipX = Math.min(...axisTipXs);
const maxTipX = Math.max(...axisTipXs);
const minTipY = Math.min(...axisTipYs);
const maxTipY = Math.max(...axisTipYs);

const contentXCenter = (minTipX + maxTipX) / 2;
const contentYCenter = (minTipY + maxTipY) / 2;
const X_HALF_SPAN = ((maxTipX - minTipX) / 2) * DOMAIN_PAD_SHARE;
const Y_HALF_SPAN = ((maxTipY - minTipY) / 2) * DOMAIN_PAD_SHARE;
const X_MIN = contentXCenter - X_HALF_SPAN;
const X_MAX = contentXCenter + X_HALF_SPAN;
const Y_MIN = contentYCenter - Y_HALF_SPAN;
const Y_MAX = contentYCenter + Y_HALF_SPAN;

const HEADER_HEIGHT = 112;
const MIN_MARGIN = 48;
const FRAME_W = window.ANYPLOT_SIZE.width;
const FRAME_H = window.ANYPLOT_SIZE.height - HEADER_HEIGHT;
const domainRatio = X_HALF_SPAN / Y_HALF_SPAN;
const innerW = FRAME_W - 2 * MIN_MARGIN;
const innerH = FRAME_H - 2 * MIN_MARGIN;
const plotW = innerW / innerH > domainRatio ? innerH * domainRatio : innerW;
const plotH = innerW / innerH > domainRatio ? innerH : innerW / domainRatio;
const MARGIN = {
  top: Math.round((FRAME_H - plotH) / 2),
  bottom: Math.round((FRAME_H - plotH) / 2),
  left: Math.round((FRAME_W - plotW) / 2),
  right: Math.round((FRAME_W - plotW) / 2),
};

function HiveGeometry() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;

  return (
    <g>
      {data.map((row, i) => {
        const source = nodeMap.get(row[SOURCE])!;
        const target = nodeMap.get(row[TARGET])!;
        const axisA = axisById[source.axis];
        const axisB = axisById[target.axis];
        const angleDiff = ((axisB.angle - axisA.angle + 540) % 360) - 180;
        const midAngleRad = ((axisA.angle + angleDiff / 2) * Math.PI) / 180;
        const ctrlX = xScale(CONTROL_R * Math.cos(midAngleRad));
        const ctrlY = yScale(CONTROL_R * Math.sin(midAngleRad));
        const p1x = xScale(source.x);
        const p1y = yScale(source.y);
        const p2x = xScale(target.x);
        const p2y = yScale(target.y);
        const wFrac =
          MAX_WEIGHT === MIN_WEIGHT
            ? 0.5
            : (row[WEIGHT] - MIN_WEIGHT) / (MAX_WEIGHT - MIN_WEIGHT);

        return (
          <path
            key={`edge-${i}`}
            d={`M ${p1x} ${p1y} Q ${ctrlX} ${ctrlY} ${p2x} ${p2y}`}
            fill="none"
            stroke={t.inkSoft}
            strokeOpacity={0.25 + wFrac * 0.22}
            strokeWidth={1.1 + wFrac * 1.1}
          />
        );
      })}
      {AXES.map((axis) => {
        const hubX = xScale(INNER_R * SPOKE_HUB_SHARE * axis.cos);
        const hubY = yScale(INNER_R * SPOKE_HUB_SHARE * axis.sin);
        const rimX = xScale(OUTER_R * SPOKE_RIM_SHARE * axis.cos);
        const rimY = yScale(OUTER_R * SPOKE_RIM_SHARE * axis.sin);
        const labelX = xScale(OUTER_R * LABEL_R_SHARE * axis.cos);
        const labelY = yScale(OUTER_R * LABEL_R_SHARE * axis.sin);
        const titleOffsetY = axis.sin < 0 ? 6 : -14;
        const subOffsetY = axis.sin < 0 ? 28 : 8;
        const nodesOnAxis = nodesByAxis[axis.id];

        return (
          <g key={axis.id}>
            <line
              x1={hubX}
              y1={hubY}
              x2={rimX}
              y2={rimY}
              stroke={t.inkSoft}
              strokeWidth={2.5}
            />
            <text
              x={labelX}
              y={labelY + titleOffsetY}
              fill={t.ink}
              fontSize={18}
              fontWeight={700}
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {axis.label} ({nodesOnAxis.length})
            </text>
            <text
              x={labelX}
              y={labelY + subOffsetY}
              fill={t.inkSoft}
              fontSize={14}
              fontFamily={MONO}
              textAnchor="middle"
              dominantBaseline="middle"
            >
              degree {nodesOnAxis[0].degree}→
              {nodesOnAxis[nodesOnAxis.length - 1].degree}
            </text>
          </g>
        );
      })}
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
        color: t.ink,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          height: HEADER_HEIGHT,
          padding: "18px 48px 6px 48px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            fontSize: 22,
            fontWeight: 700,
            color: t.ink,
            lineHeight: 1.2,
          }}
        >
          hive-basic · javascript · muix · anyplot.ai
        </div>
        <div
          style={{
            fontSize: 14,
            color: t.inkSoft,
            fontFamily: MONO,
          }}
        >
          {allNodes.length} nodes across {AXES.length} axes ({LAYER}) ·{" "}
          {data.length} edges · radial distance encodes node degree (
          {MIN_DEGREE} → {MAX_DEGREE})
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 24,
            fontSize: 14,
            color: t.ink,
          }}
        >
          {AXES.map((axis) => (
            <div
              key={axis.id}
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <span
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: "50%",
                  background: axis.color,
                  display: "inline-block",
                }}
              />
              <span style={{ fontWeight: 600 }}>{axis.label}</span>
            </div>
          ))}
        </div>
      </div>

      <ChartsContainer
        width={width}
        height={height - HEADER_HEIGHT}
        margin={MARGIN}
        skipAnimation
        xAxis={[{ scaleType: "linear", min: X_MIN, max: X_MAX, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: Y_MIN, max: Y_MAX, position: "none" }]}
        series={AXES.map((axis) => ({
          type: "scatter",
          id: axis.id,
          label: axis.label,
          color: axis.color,
          markerSize: 8,
          data: nodesByAxis[axis.id].map((n) => ({
            x: n.x,
            y: n.y,
            id: n.id,
          })),
        }))}
      >
        <HiveGeometry />
        <ScatterPlot />
      </ChartsContainer>
    </div>
  );
}
