// anyplot.ai
// parallel-categories-basic: Basic Parallel Categories Plot
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 84/100 | Updated: 2026-10-24

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
const OUTCOME_SEMANTICS: Record<string, { color: string; hatched: boolean }> = {
  Survived: { color: t.palette[0], hatched: false },
  "Did not survive": { color: t.palette[4], hatched: true },
};
const UNUSED_PALETTE = [t.palette[1], t.palette[2], t.palette[3], t.palette[5]];

// Columns: set these to your data's column names
const DIMENSIONS = ["Passenger class", "Sex", "Outcome"]; // role: dimension
const COUNT = "Passengers"; // role: value

// Data: replace this block with your own records
const data: Array<Record<string, string | number>> = [
  { [DIMENSIONS[0]]: "1st", [DIMENSIONS[1]]: "Female", [DIMENSIONS[2]]: "Survived", [COUNT]: 91 },
  { [DIMENSIONS[0]]: "1st", [DIMENSIONS[1]]: "Female", [DIMENSIONS[2]]: "Did not survive", [COUNT]: 3 },
  { [DIMENSIONS[0]]: "1st", [DIMENSIONS[1]]: "Male", [DIMENSIONS[2]]: "Survived", [COUNT]: 45 },
  { [DIMENSIONS[0]]: "1st", [DIMENSIONS[1]]: "Male", [DIMENSIONS[2]]: "Did not survive", [COUNT]: 77 },
  { [DIMENSIONS[0]]: "2nd", [DIMENSIONS[1]]: "Female", [DIMENSIONS[2]]: "Survived", [COUNT]: 70 },
  { [DIMENSIONS[0]]: "2nd", [DIMENSIONS[1]]: "Female", [DIMENSIONS[2]]: "Did not survive", [COUNT]: 6 },
  { [DIMENSIONS[0]]: "2nd", [DIMENSIONS[1]]: "Male", [DIMENSIONS[2]]: "Survived", [COUNT]: 17 },
  { [DIMENSIONS[0]]: "2nd", [DIMENSIONS[1]]: "Male", [DIMENSIONS[2]]: "Did not survive", [COUNT]: 91 },
  { [DIMENSIONS[0]]: "3rd", [DIMENSIONS[1]]: "Female", [DIMENSIONS[2]]: "Survived", [COUNT]: 72 },
  { [DIMENSIONS[0]]: "3rd", [DIMENSIONS[1]]: "Female", [DIMENSIONS[2]]: "Did not survive", [COUNT]: 72 },
  { [DIMENSIONS[0]]: "3rd", [DIMENSIONS[1]]: "Male", [DIMENSIONS[2]]: "Survived", [COUNT]: 47 },
  { [DIMENSIONS[0]]: "3rd", [DIMENSIONS[1]]: "Male", [DIMENSIONS[2]]: "Did not survive", [COUNT]: 300 },
];

// Plot: reads only data and the constants above
const totalCount = data.reduce((sum, row) => sum + Number(row[COUNT]), 0);

const columnDefs = DIMENSIONS.map((col) => {
  const order: string[] = [];
  const totals = new Map<string, number>();
  for (const row of data) {
    const val = String(row[col]);
    const cnt = Number(row[COUNT]);
    if (!order.includes(val)) order.push(val);
    totals.set(val, (totals.get(val) ?? 0) + cnt);
  }
  return { col, order, totals };
});

const outcomeDim = DIMENSIONS[DIMENSIONS.length - 1];
const outcomeOrder = columnDefs[columnDefs.length - 1].order;
const outcomeStyles: Record<string, { color: string; hatched: boolean }> = {};
let fallbackIdx = 0;
for (const name of outcomeOrder) {
  if (OUTCOME_SEMANTICS[name]) {
    outcomeStyles[name] = OUTCOME_SEMANTICS[name];
  } else {
    outcomeStyles[name] = {
      color: UNUSED_PALETTE[fallbackIdx % UNUSED_PALETTE.length],
      hatched: false,
    };
    fallbackIdx += 1;
  }
}

const maxNodes = Math.max(...columnDefs.map((d) => d.order.length));

function ParallelCategories() {
  const area = useDrawingArea();
  const [hoveredRow, setHoveredRow] = useState<number | null>(null);

  const k = (area.height - GAP * (maxNodes - 1)) / totalCount;
  const colCount = columnDefs.length;
  const colX = columnDefs.map((_, ci) => area.left + (ci * area.width) / (colCount - 1));

  const colNodes: Array<Record<string, { y0: number; y1: number; total: number }>> = [];
  const colSegs: Array<Array<{ y0: number; y1: number }>> = [];

  for (const def of columnDefs) {
    const heights = new Map<string, number>();
    for (const row of data) {
      const name = String(row[def.col]);
      const h = Number(row[COUNT]) * k;
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
    for (const row of data) {
      const name = String(row[def.col]);
      const y0 = segCursor[name];
      const y1 = y0 + Number(row[COUNT]) * k;
      segCursor[name] = y1;
      segsForCol.push({ y0, y1 });
    }
    colSegs.push(segsForCol);
  }

  return (
    <g>
      <defs>
        <pattern
          id="outcome-hatch"
          patternUnits="userSpaceOnUse"
          width={6}
          height={6}
          patternTransform="rotate(45)"
        >
          <line x1={0} y1={0} x2={0} y2={6} stroke={t.ink} strokeOpacity={0.45} strokeWidth={1.5} />
        </pattern>
      </defs>

      {columnDefs.map((def, i) => (
        <text
          key={def.col}
          x={colX[i]}
          y={area.top - 22}
          textAnchor="middle"
          fontSize={15}
          fontWeight={600}
          fill={t.inkSoft}
        >
          {def.col}
        </text>
      ))}

      {data.map((row, i) => {
        const outcome = String(row[outcomeDim]);
        const style = outcomeStyles[outcome];
        const isHovered = hoveredRow === i;
        const isDimmed = hoveredRow !== null && !isHovered;
        const fillOpacity = isDimmed ? 0.12 : isHovered ? 0.92 : 0.78;
        const strokeOpacity = isDimmed ? 0.06 : isHovered ? 0.35 : 0.12;
        const strokeWidth = isHovered ? 1.5 : 1;

        return (
          <g key={`flow-${i}`}>
            {Array.from({ length: colCount - 1 }, (_, ci) => {
              const xStart = colX[ci] + NODE_HALF;
              const xEnd = colX[ci + 1] - NODE_HALF;
              const xMid = (xStart + xEnd) / 2;
              const segA = colSegs[ci][i];
              const segB = colSegs[ci + 1][i];
              const d = `M${xStart},${segA.y0} C${xMid},${segA.y0} ${xMid},${segB.y0} ${xEnd},${segB.y0} L${xEnd},${segB.y1} C${xMid},${segB.y1} ${xMid},${segA.y1} ${xStart},${segA.y1} Z`;

              return (
                <g key={`seg-${ci}`}>
                  <path
                    d={d}
                    fill={style.color}
                    stroke={t.ink}
                    cursor="pointer"
                    fillOpacity={fillOpacity}
                    strokeOpacity={strokeOpacity}
                    strokeWidth={strokeWidth}
                    onMouseEnter={() => setHoveredRow(i)}
                    onMouseLeave={() => setHoveredRow(null)}
                  />
                  {style.hatched && (
                    <path
                      d={d}
                      fill="url(#outcome-hatch)"
                      fillOpacity={fillOpacity}
                      pointerEvents="none"
                    />
                  )}
                </g>
              );
            })}
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

      {colNodes.map((nodes, ci) => {
        const isFirst = ci === 0;
        const isLast = ci === colCount - 1;
        const xPos = isFirst
          ? colX[ci] - NODE_HALF - 12
          : isLast
            ? colX[ci] + NODE_HALF + 12
            : colX[ci];
        const textAnchor = isFirst ? "end" : isLast ? "start" : "middle";
        return Object.entries(nodes).map(([name, node]) => {
          const yPos = isFirst || isLast ? (node.y0 + node.y1) / 2 : node.y0 - 12;
          return (
            <text
              key={`label-${ci}-${name}`}
              x={xPos}
              y={yPos}
              textAnchor={textAnchor}
              dominantBaseline={isFirst || isLast ? "middle" : "auto"}
              fontSize={14}
              fill={t.ink}
            >
              {`${name} · ${node.total}`}
            </text>
          );
        });
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
        backgroundColor: t.pageBg,
        position: "relative",
        fontFamily: '"Helvetica Neue", Arial, sans-serif',
        boxSizing: "border-box",
      }}
    >
      <div style={{ position: "absolute", top: 26, left: PAD, right: PAD }}>
        <div style={{ color: t.ink, fontSize: TITLE_FONT_SIZE, fontWeight: 600 }}>{TITLE}</div>
        <div style={{ color: t.inkSoft, fontSize: 15, marginTop: 6 }}>
          {`${DIMENSIONS.join(" → ")} across ${totalCount} (${COUNT}) — ribbon width is proportional to ${COUNT}.`}
        </div>
        <div style={{ display: "flex", gap: 24, marginTop: 12, alignItems: "center" }}>
          {outcomeOrder.map((name) => {
            const style = outcomeStyles[name];
            return (
              <div key={name} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span
                  style={{
                    width: 14,
                    height: 14,
                    borderRadius: 3,
                    backgroundColor: style.color,
                    backgroundImage: style.hatched
                      ? "repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(0,0,0,0.4) 2px, rgba(0,0,0,0.4) 3px)"
                      : undefined,
                    display: "inline-block",
                  }}
                />
                <span style={{ color: t.inkSoft, fontSize: 14 }}>{name}</span>
              </div>
            );
          })}
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
