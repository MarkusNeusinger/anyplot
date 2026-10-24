// anyplot.ai
// parallel-categories-basic: Basic Parallel Categories Plot
// Library: muix 9.x | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-09-05

import * as React from "react";
import { useState } from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "parallel-categories-basic · javascript · muix · anyplot.ai";
const TITLE_FONT_SIZE = 22;
const HEADER_H = 118;
const PAD = 40;
const GAP = 34;
const NODE_HALF = 13;
const MIN_SEG = 8;

const CLASS_COL = "passenger_class";
const SEX_COL = "sex";
const OUTCOME_COL = "outcome";
const COUNT_COL = "passenger_count";

// Data: Titanic passengers by class, sex, and outcome (flat scalar records)
const DATA: Array<Record<string, string | number>> = [
  { passenger_class: "1st", sex: "Female", outcome: "Survived", passenger_count: 91 },
  { passenger_class: "1st", sex: "Female", outcome: "Did not survive", passenger_count: 3 },
  { passenger_class: "1st", sex: "Male", outcome: "Survived", passenger_count: 45 },
  { passenger_class: "1st", sex: "Male", outcome: "Did not survive", passenger_count: 77 },
  { passenger_class: "2nd", sex: "Female", outcome: "Survived", passenger_count: 70 },
  { passenger_class: "2nd", sex: "Female", outcome: "Did not survive", passenger_count: 6 },
  { passenger_class: "2nd", sex: "Male", outcome: "Survived", passenger_count: 17 },
  { passenger_class: "2nd", sex: "Male", outcome: "Did not survive", passenger_count: 91 },
  { passenger_class: "3rd", sex: "Female", outcome: "Survived", passenger_count: 72 },
  { passenger_class: "3rd", sex: "Female", outcome: "Did not survive", passenger_count: 72 },
  { passenger_class: "3rd", sex: "Male", outcome: "Survived", passenger_count: 47 },
  { passenger_class: "3rd", sex: "Male", outcome: "Did not survive", passenger_count: 300 },
];

// Derive category orders in order of first appearance
const classOrder: string[] = [];
const sexOrder: string[] = [];
const outcomeOrder: string[] = [];
let totalCount = 0;

const classTotals = new Map<string, number>();
const sexTotals = new Map<string, number>();
const outcomeTotals = new Map<string, number>();

for (const row of DATA) {
  const cls = String(row[CLASS_COL]);
  const sex = String(row[SEX_COL]);
  const out = String(row[OUTCOME_COL]);
  const cnt = Number(row[COUNT_COL]);
  if (!classOrder.includes(cls)) classOrder.push(cls);
  if (!sexOrder.includes(sex)) sexOrder.push(sex);
  if (!outcomeOrder.includes(out)) outcomeOrder.push(out);
  totalCount += cnt;
  classTotals.set(cls, (classTotals.get(cls) ?? 0) + cnt);
  sexTotals.set(sex, (sexTotals.get(sex) ?? 0) + cnt);
  outcomeTotals.set(out, (outcomeTotals.get(out) ?? 0) + cnt);
}

// Semantic outcome colors: first outcome (Survived) -> brand green, second (Did not survive) -> matte red
const outcomeColorMap: Record<string, string> = {};
for (let i = 0; i < outcomeOrder.length; i += 1) {
  outcomeColorMap[outcomeOrder[i]] = i === 0 ? t.palette[0] : t.palette[4];
}

const columnDefs = [
  { col: CLASS_COL, header: "Class", order: classOrder, totals: classTotals },
  { col: SEX_COL, header: "Sex", order: sexOrder, totals: sexTotals },
  { col: OUTCOME_COL, header: "Outcome", order: outcomeOrder, totals: outcomeTotals },
];

const maxNodes = Math.max(classOrder.length, sexOrder.length, outcomeOrder.length);

function ParallelCategories() {
  const area = useDrawingArea();
  const [hoveredRow, setHoveredRow] = useState<number | null>(null);

  const k = (area.height - GAP * (maxNodes - 1)) / totalCount;
  const colX = [area.left, area.left + area.width / 2, area.left + area.width];

  // Compute node boxes and stacked row segments per column
  const colNodes: Array<Record<string, { y0: number; y1: number; total: number }>> = [];
  const colSegs: Array<Array<{ y0: number; y1: number }>> = [];

  for (const def of columnDefs) {
    const heights = new Map<string, number>();
    for (const row of DATA) {
      const name = String(row[def.col]);
      const h = Math.max(Number(row[COUNT_COL]) * k, MIN_SEG);
      heights.set(name, (heights.get(name) ?? 0) + h);
    }

    let contentHeight = GAP * (def.order.length - 1);
    for (const name of def.order) {
      contentHeight += heights.get(name) ?? 0;
    }

    let yCursor = area.top + (area.height - contentHeight) / 2;
    const nodesMap: Record<string, { y0: number; y1: number; total: number }> = {};
    const segCursor: Record<string, number> = {};

    for (const name of def.order) {
      const h = heights.get(name) ?? 0;
      nodesMap[name] = { y0: yCursor, y1: yCursor + h, total: def.totals.get(name) ?? 0 };
      segCursor[name] = yCursor;
      yCursor += h + GAP;
    }
    colNodes.push(nodesMap);

    const segsForCol: Array<{ y0: number; y1: number }> = [];
    for (const row of DATA) {
      const name = String(row[def.col]);
      const y0 = segCursor[name];
      const y1 = y0 + Math.max(Number(row[COUNT_COL]) * k, MIN_SEG);
      segCursor[name] = y1;
      segsForCol.push({ y0, y1 });
    }
    colSegs.push(segsForCol);
  }

  const [clsNodes, sexNodes, outcomeNodes] = colNodes;
  const [clsSegs, sexSegs, outcomeSegs] = colSegs;
  const xm01 = (colX[0] + NODE_HALF + (colX[1] - NODE_HALF)) / 2;
  const xm12 = (colX[1] + NODE_HALF + (colX[2] - NODE_HALF)) / 2;

  return (
    <g>
      <defs>
        <pattern id="outcome-hatch" patternUnits="userSpaceOnUse" width={6} height={6} patternTransform="rotate(45)">
          <line x1={0} y1={0} x2={0} y2={6} stroke={t.ink} strokeOpacity={0.45} strokeWidth={1.5} />
        </pattern>
      </defs>

      {columnDefs.map((def, i) => (
        <text
          key={def.header}
          x={colX[i]}
          y={area.top - 22}
          textAnchor="middle"
          fontSize={15}
          fontWeight={600}
          fill={t.inkSoft}
        >
          {def.header}
        </text>
      ))}

      {DATA.map((row, i) => {
        const outcome = String(row[OUTCOME_COL]);
        const isSecondOutcome = outcome === outcomeOrder[1];
        const isHovered = hoveredRow === i;
        const isDimmed = hoveredRow !== null && !isHovered;
        const fillOpacity = isDimmed ? 0.12 : isHovered ? 0.92 : 0.78;
        const strokeOpacity = isDimmed ? 0.06 : isHovered ? 0.35 : 0.12;
        const strokeWidth = isHovered ? 1.5 : 1;

        const x0 = colX[0] + NODE_HALF;
        const x1 = colX[1] - NODE_HALF;
        const d01 = `M${x0},${clsSegs[i].y0} C${xm01},${clsSegs[i].y0} ${xm01},${sexSegs[i].y0} ${x1},${sexSegs[i].y0} L${x1},${sexSegs[i].y1} C${xm01},${sexSegs[i].y1} ${xm01},${clsSegs[i].y1} ${x0},${clsSegs[i].y1} Z`;

        const x2 = colX[1] + NODE_HALF;
        const x3 = colX[2] - NODE_HALF;
        const d12 = `M${x2},${sexSegs[i].y0} C${xm12},${sexSegs[i].y0} ${xm12},${outcomeSegs[i].y0} ${x3},${outcomeSegs[i].y0} L${x3},${outcomeSegs[i].y1} C${xm12},${outcomeSegs[i].y1} ${xm12},${sexSegs[i].y1} ${x2},${sexSegs[i].y1} Z`;

        return (
          <g key={`flow-${i}`}>
            <path
              d={d01}
              fill={outcomeColorMap[outcome]}
              stroke={t.ink}
              cursor="pointer"
              fillOpacity={fillOpacity}
              strokeOpacity={strokeOpacity}
              strokeWidth={strokeWidth}
              onMouseEnter={() => setHoveredRow(i)}
              onMouseLeave={() => setHoveredRow(null)}
            />
            {isSecondOutcome && (
              <path d={d01} fill="url(#outcome-hatch)" fillOpacity={fillOpacity} pointerEvents="none" />
            )}
            <path
              d={d12}
              fill={outcomeColorMap[outcome]}
              stroke={t.ink}
              cursor="pointer"
              fillOpacity={fillOpacity}
              strokeOpacity={strokeOpacity}
              strokeWidth={strokeWidth}
              onMouseEnter={() => setHoveredRow(i)}
              onMouseLeave={() => setHoveredRow(null)}
            />
            {isSecondOutcome && (
              <path d={d12} fill="url(#outcome-hatch)" fillOpacity={fillOpacity} pointerEvents="none" />
            )}
          </g>
        );
      })}

      {colNodes.map((nodes, ci) =>
        Object.entries(nodes).map(([name, node]) => (
          <rect
            key={`node-${ci}-${name}`}
            x={colX[ci] - NODE_HALF}
            y={node.y0}
            width={NODE_HALF * 2}
            height={node.y1 - node.y0}
            rx={2}
            fill={t.ink}
            fillOpacity={0.88}
          />
        )),
      )}

      {Object.entries(clsNodes).map(([name, node]) => (
        <text
          key={`label-cls-${name}`}
          x={colX[0] - NODE_HALF - 12}
          y={(node.y0 + node.y1) / 2}
          textAnchor="end"
          dominantBaseline="middle"
          fontSize={14}
          fill={t.ink}
        >
          {`${name} · ${node.total}`}
        </text>
      ))}
      {Object.entries(sexNodes).map(([name, node]) => (
        <text
          key={`label-sex-${name}`}
          x={colX[1]}
          y={node.y0 - 12}
          textAnchor="middle"
          fontSize={14}
          fill={t.ink}
        >
          {`${name} · ${node.total}`}
        </text>
      ))}
      {Object.entries(outcomeNodes).map(([name, node]) => (
        <text
          key={`label-outcome-${name}`}
          x={colX[2] + NODE_HALF + 12}
          y={(node.y0 + node.y1) / 2}
          textAnchor="start"
          dominantBaseline="middle"
          fontSize={14}
          fill={t.ink}
        >
          {`${name} · ${node.total}`}
        </text>
      ))}
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
        backgroundColor: t.pageBg,
        position: "relative",
        fontFamily: '"Helvetica Neue", Arial, sans-serif',
        boxSizing: "border-box",
      }}
    >
      <div style={{ position: "absolute", top: 26, left: PAD, right: PAD }}>
        <div style={{ color: t.ink, fontSize: TITLE_FONT_SIZE, fontWeight: 600 }}>{TITLE}</div>
        <div style={{ color: t.inkSoft, fontSize: 15, marginTop: 6 }}>
          {`Class, sex and survival outcome for ${totalCount} Titanic passengers — ribbon width is proportional to passenger count.`}
        </div>
        <div style={{ display: "flex", gap: 24, marginTop: 12, alignItems: "center" }}>
          {outcomeOrder.map((name, idx) => (
            <div key={name} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: 3,
                  backgroundColor: outcomeColorMap[name],
                  backgroundImage:
                    idx === 1
                      ? "repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(0,0,0,0.4) 2px, rgba(0,0,0,0.4) 3px)"
                      : undefined,
                  display: "inline-block",
                }}
              />
              <span style={{ color: t.inkSoft, fontSize: 14 }}>{name}</span>
            </div>
          ))}
        </div>
      </div>
      <div style={{ position: "absolute", top: HEADER_H, left: PAD }}>
        <ChartsContainer
          width={width - PAD * 2}
          height={height - HEADER_H - PAD / 2}
          series={[]}
          xAxis={[{ scaleType: "linear", min: 0, max: 1, position: "none" }]}
          yAxis={[{ scaleType: "linear", min: 0, max: 1, position: "none" }]}
          margin={{ top: 46, bottom: 12, left: 120, right: 170 }}
          skipAnimation
        >
          <ParallelCategories />
        </ChartsContainer>
      </div>
    </div>
  );
}
