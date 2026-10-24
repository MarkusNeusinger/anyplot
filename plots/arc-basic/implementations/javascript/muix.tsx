// anyplot.ai
// arc-basic: Basic Arc Diagram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-24
import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const NODE_RADIUS = 8;
const X_PAD_SHARE = 0.04;
const Y_DOMAIN_MAX = 1.05;
const MIN_ARC_HEIGHT = 0.12;
const MAX_ARC_SPAN = 0.88;
const STROKE_MIN_PX = 1.6;
const STROKE_MAX_PX = 3.4;
const STROKE_ALPHA_MIN = 0.52;
const STROKE_ALPHA_MAX = 0.82;
const SEMANTIC_COLORS: Record<string, string> = {
  Activates: t.palette[0],
  Represses: t.palette[4],
};

// Columns: set these to your data's column names
const SOURCE = "Source gene"; // role: nodes
const TARGET = "Target gene"; // role: edges
const WEIGHT = "Interaction strength"; // role: weights
const INTERACTION_TYPE = "Regulation type"; // role: extra

// Data: replace this block with your own records, one object per row
const data = [
  { [SOURCE]: "FOXP2", [TARGET]: "GATA3", [WEIGHT]: 2, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "GATA3", [TARGET]: "MYC", [WEIGHT]: 3, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "MYC", [TARGET]: "KRAS", [WEIGHT]: 2, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "KRAS", [TARGET]: "EGFR", [WEIGHT]: 3, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "EGFR", [TARGET]: "PIK3CA", [WEIGHT]: 2, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "PIK3CA", [TARGET]: "PTEN", [WEIGHT]: 4, [INTERACTION_TYPE]: "Represses" },
  { [SOURCE]: "PTEN", [TARGET]: "TP53", [WEIGHT]: 3, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "TP53", [TARGET]: "ATM", [WEIGHT]: 2, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "ATM", [TARGET]: "BRCA1", [WEIGHT]: 3, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "BRCA1", [TARGET]: "BRCA2", [WEIGHT]: 4, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "BRCA2", [TARGET]: "CDK4", [WEIGHT]: 1, [INTERACTION_TYPE]: "Represses" },
  { [SOURCE]: "CDK4", [TARGET]: "ESR1", [WEIGHT]: 2, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "ESR1", [TARGET]: "NOTCH1", [WEIGHT]: 2, [INTERACTION_TYPE]: "Represses" },
  { [SOURCE]: "NOTCH1", [TARGET]: "AKT1", [WEIGHT]: 3, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "AKT1", [TARGET]: "VEGFA", [WEIGHT]: 2, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "VEGFA", [TARGET]: "APOE", [WEIGHT]: 1, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "APOE", [TARGET]: "ACE2", [WEIGHT]: 2, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "MYC", [TARGET]: "TP53", [WEIGHT]: 3, [INTERACTION_TYPE]: "Represses" },
  { [SOURCE]: "PIK3CA", [TARGET]: "AKT1", [WEIGHT]: 4, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "TP53", [TARGET]: "BRCA1", [WEIGHT]: 3, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "BRCA1", [TARGET]: "ACE2", [WEIGHT]: 1, [INTERACTION_TYPE]: "Represses" },
  { [SOURCE]: "FOXP2", [TARGET]: "ACE2", [WEIGHT]: 1, [INTERACTION_TYPE]: "Activates" },
  { [SOURCE]: "KRAS", [TARGET]: "BRCA2", [WEIGHT]: 2, [INTERACTION_TYPE]: "Represses" },
];

// Plot: reads only data and the constants above
const nodes = [
  ...new Set([...data.map((d) => d[SOURCE]), ...data.map((d) => d[TARGET])]),
];
const nodeIndex = Object.fromEntries(nodes.map((n, i) => [n, i]));
const maxDistance = nodes.length - 1;

const types = [...new Set(data.map((d) => d[INTERACTION_TYPE]))];
const usedColors = new Set(
  types.map((k) => SEMANTIC_COLORS[k]).filter(Boolean),
);
const unusedPalette = t.palette.filter((c) => !usedColors.has(c));
let unusedIdx = 0;
const typeColor: Record<string, string> = {};
const typeDash: Record<string, string | undefined> = {};
types.forEach((k, i) => {
  typeColor[k] = SEMANTIC_COLORS[k] ?? unusedPalette[unusedIdx++];
  typeDash[k] = i % 2 === 1 ? "6 4" : undefined;
});

const weights = data.map((d) => d[WEIGHT]);
const minWeight = Math.min(...weights);
const maxWeight = Math.max(...weights);
const weightSpan = Math.max(1e-9, maxWeight - minWeight);
const xPad = maxDistance * X_PAD_SHARE;

function ArcLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const baselineY = yScale(0);
  return (
    <g data-drawing-container>
      {data.map((row, i) => {
        const a = nodeIndex[row[SOURCE]];
        const b = nodeIndex[row[TARGET]];
        const strength = (row[WEIGHT] - minWeight) / weightSpan;
        const kind = row[INTERACTION_TYPE];
        const x1 = xScale(a);
        const x2 = xScale(b);
        const archH =
          MIN_ARC_HEIGHT + MAX_ARC_SPAN * (Math.abs(b - a) / maxDistance);
        const apexY = yScale(archH);
        const controlY = baselineY - 2 * (baselineY - apexY);
        return (
          <path
            key={`edge-${i}`}
            d={`M ${x1} ${baselineY} Q ${(x1 + x2) / 2} ${controlY} ${x2} ${baselineY}`}
            fill="none"
            stroke={typeColor[kind]}
            strokeWidth={STROKE_MIN_PX + strength * (STROKE_MAX_PX - STROKE_MIN_PX)}
            strokeOpacity={
              STROKE_ALPHA_MIN + strength * (STROKE_ALPHA_MAX - STROKE_ALPHA_MIN)
            }
            strokeDasharray={typeDash[kind]}
          />
        );
      })}
      {nodes.map((name, i) => {
        const x = xScale(i);
        const labelX = x - 4;
        const labelY = baselineY + NODE_RADIUS + 18;
        return (
          <React.Fragment key={name}>
            <circle
              cx={x}
              cy={baselineY}
              r={NODE_RADIUS}
              fill={t.palette[0]}
              stroke={t.pageBg}
              strokeWidth={1.5}
            />
            <text
              x={labelX}
              y={labelY}
              textAnchor="end"
              fontSize={14}
              fontWeight={500}
              fill={t.inkSoft}
              transform={`rotate(-40 ${labelX} ${labelY})`}
            >
              {name}
            </text>
          </React.Fragment>
        );
      })}
    </g>
  );
}

const TITLE = "arc-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${nodes.length} nodes · ${data.length} arcs · ${WEIGHT}: ${minWeight}–${maxWeight}`;
const HEADER_H = 100;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      }}
    >
      <div
        style={{
          height: HEADER_H,
          padding: "14px 50px 0 50px",
          display: "flex",
          flexDirection: "column",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            fontSize: 22,
            fontWeight: 600,
            color: t.ink,
            lineHeight: 1.25,
          }}
        >
          {TITLE}
        </div>
        <div
          style={{
            fontSize: 15,
            color: t.inkSoft,
            marginTop: 4,
          }}
        >
          {SUBTITLE}
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 22,
            marginTop: 6,
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          {types.map((kind) => (
            <span
              key={kind}
              style={{ display: "inline-flex", alignItems: "center", gap: 7 }}
            >
              <svg width="20" height="4" style={{ display: "inline-block" }}>
                <line
                  x1="0"
                  y1="2"
                  x2="20"
                  y2="2"
                  stroke={typeColor[kind]}
                  strokeWidth="3"
                  strokeDasharray={typeDash[kind]}
                />
              </svg>
              <span>{kind}</span>
            </span>
          ))}
          <span>· Arc height ∝ sequence distance · Stroke width ∝ {WEIGHT}</span>
        </div>
      </div>
      <ChartsContainer
        width={width}
        height={height - HEADER_H}
        series={[]}
        margin={{ top: 20, bottom: 110, left: 60, right: 50 }}
        xAxis={[
          {
            id: "x",
            scaleType: "linear",
            min: -xPad,
            max: maxDistance + xPad,
            position: "none",
          },
        ]}
        yAxis={[
          {
            id: "y",
            scaleType: "linear",
            min: 0,
            max: Y_DOMAIN_MAX,
            position: "none",
          },
        ]}
        skipAnimation
      >
        <ArcLayer />
      </ChartsContainer>
    </div>
  );
}
