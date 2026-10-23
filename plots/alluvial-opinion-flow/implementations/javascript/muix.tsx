// anyplot.ai
// alluvial-opinion-flow: Opinion Flow Diagram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-26
import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const INK_MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

// Constants
const NODE_W = 24;
const GAP_SHARE = 0.08; // vertical gap between category blocks as a share of total wave count

// Columns: set these to your data's column names
const WAVE = "Survey wave"; // role: wave
const NEXT_WAVE = "Next wave"; // role: extra
const SOURCE_CATEGORY = "Source opinion"; // role: source_category
const TARGET_CATEGORY = "Target opinion"; // role: target_category
const FLOW_COUNT = "Respondents"; // role: flow_count

// Data: replace this block with your own records, one object per row
const data = [
  // Q1 2025 -> Q2 2025
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Very Satisfied", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 110 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Very Satisfied", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 30 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Very Satisfied", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 10 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 60 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 180 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 40 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Dissatisfied", [FLOW_COUNT]: 15 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Very Dissatisfied", [FLOW_COUNT]: 5 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 25 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 35 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 140 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Dissatisfied", [FLOW_COUNT]: 70 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Very Dissatisfied", [FLOW_COUNT]: 30 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 3 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 3 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 20 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Dissatisfied", [FLOW_COUNT]: 80 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Very Dissatisfied", [FLOW_COUNT]: 44 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 2 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 2 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 10 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Dissatisfied", [FLOW_COUNT]: 15 },
  { [WAVE]: "Q1 2025", [NEXT_WAVE]: "Q2 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Very Dissatisfied", [FLOW_COUNT]: 71 },
  // Q2 2025 -> Q3 2025
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Very Satisfied", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 160 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Very Satisfied", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 30 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Very Satisfied", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 10 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 70 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 150 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 20 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Dissatisfied", [FLOW_COUNT]: 8 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Very Dissatisfied", [FLOW_COUNT]: 2 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 25 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 15 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 100 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Dissatisfied", [FLOW_COUNT]: 60 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Very Dissatisfied", [FLOW_COUNT]: 20 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 3 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 3 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 20 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Dissatisfied", [FLOW_COUNT]: 110 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Very Dissatisfied", [FLOW_COUNT]: 44 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 2 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 2 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 10 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Dissatisfied", [FLOW_COUNT]: 22 },
  { [WAVE]: "Q2 2025", [NEXT_WAVE]: "Q3 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Very Dissatisfied", [FLOW_COUNT]: 114 },
  // Q3 2025 -> Q4 2025
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Very Satisfied", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 220 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Very Satisfied", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 30 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Very Satisfied", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 10 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 90 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 90 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 12 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Dissatisfied", [FLOW_COUNT]: 6 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Satisfied", [TARGET_CATEGORY]: "Very Dissatisfied", [FLOW_COUNT]: 2 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 8 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 20 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 80 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Dissatisfied", [FLOW_COUNT]: 40 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Neutral", [TARGET_CATEGORY]: "Very Dissatisfied", [FLOW_COUNT]: 12 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Very Satisfied", [FLOW_COUNT]: 2 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 8 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 15 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Dissatisfied", [FLOW_COUNT]: 125 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Dissatisfied", [TARGET_CATEGORY]: "Very Dissatisfied", [FLOW_COUNT]: 50 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Satisfied", [FLOW_COUNT]: 2 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Neutral", [FLOW_COUNT]: 3 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Dissatisfied", [FLOW_COUNT]: 19 },
  { [WAVE]: "Q3 2025", [NEXT_WAVE]: "Q4 2025", [SOURCE_CATEGORY]: "Very Dissatisfied", [TARGET_CATEGORY]: "Very Dissatisfied", [FLOW_COUNT]: 156 },
];

// Plot: reads only data and the constants above
const categories = [
  ...new Set([
    ...data.map((d) => d[SOURCE_CATEGORY]),
    ...data.map((d) => d[TARGET_CATEGORY]),
  ]),
];
const waves = [
  ...new Set([
    ...data.map((d) => d[WAVE]),
    ...data.map((d) => d[NEXT_WAVE]),
  ]),
];

// Ordered sentiment ramp: good pole (t.seq[0] = #009E73) -> neutral midpoint (INK_MUTED) -> bad pole (t.div[0] = #AE3030)
const posPole = parseInt(t.seq[0].slice(1), 16);
const midPole = parseInt(INK_MUTED.slice(1), 16);
const negPole = parseInt(t.div[0].slice(1), 16);
const categoryColor: Record<string, string> = {};
categories.forEach((cat, i) => {
  const u = categories.length > 1 ? i / (categories.length - 1) : 0;
  const fromHex = u <= 0.5 ? posPole : midPole;
  const toHex = u <= 0.5 ? midPole : negPole;
  const mix = u <= 0.5 ? u * 2 : (u - 0.5) * 2;
  const hex = [16, 8, 0]
    .map((shift) => {
      const a = (fromHex >> shift) & 255;
      const b = (toHex >> shift) & 255;
      return Math.round(a + (b - a) * mix)
        .toString(16)
        .padStart(2, "0");
    })
    .join("");
  categoryColor[cat] = `#${hex}`;
});

const populations = waves.map((wave, idx) => {
  const pop: Record<string, number> = {};
  categories.forEach((cat) => {
    if (idx < waves.length - 1) {
      pop[cat] = data
        .filter((d) => d[WAVE] === wave && d[SOURCE_CATEGORY] === cat)
        .reduce((sum, d) => sum + d[FLOW_COUNT], 0);
    } else {
      const prevWave = waves[idx - 1];
      pop[cat] = data
        .filter((d) => d[WAVE] === prevWave && d[TARGET_CATEGORY] === cat)
        .reduce((sum, d) => sum + d[FLOW_COUNT], 0);
    }
  });
  return pop;
});

const waveTotals = waves.map((wave) =>
  Math.max(
    data.filter((d) => d[WAVE] === wave).reduce((sum, d) => sum + d[FLOW_COUNT], 0),
    data.filter((d) => d[NEXT_WAVE] === wave).reduce((sum, d) => sum + d[FLOW_COUNT], 0),
  ),
);
const stackTotal = Math.max(...waveTotals);
const minWaveTotal = Math.min(...waveTotals);
const gapUnits =
  categories.length > 1
    ? (stackTotal * GAP_SHARE) / (categories.length - 1)
    : 0;
const domainMax = stackTotal + gapUnits * (categories.length - 1);

const nodeExtents = populations.map((pop) => {
  let cursor = domainMax;
  const extents: Record<string, { top: number; bottom: number; value: number }> = {};
  categories.forEach((cat) => {
    const val = pop[cat];
    const bottom = cursor - val;
    extents[cat] = { top: cursor, bottom, value: val };
    cursor = bottom - gapUnits;
  });
  return extents;
});

const flows: {
  step: number;
  source: string;
  target: string;
  count: number;
  stable: boolean;
  srcTop: number;
  srcBottom: number;
  dstTop: number;
  dstBottom: number;
}[] = [];

for (let step = 0; step < waves.length - 1; step += 1) {
  const w = waves[step];
  const outCursor: Record<string, number> = {};
  const inCursor: Record<string, number> = {};
  categories.forEach((cat) => {
    outCursor[cat] = nodeExtents[step][cat].top;
    inCursor[cat] = nodeExtents[step + 1][cat].top;
  });
  categories.forEach((from) => {
    categories.forEach((to) => {
      const count = data
        .filter(
          (d) =>
            d[WAVE] === w &&
            d[SOURCE_CATEGORY] === from &&
            d[TARGET_CATEGORY] === to,
        )
        .reduce((s, d) => s + d[FLOW_COUNT], 0);
      if (count <= 0) return;
      const srcTop = outCursor[from];
      const srcBottom = srcTop - count;
      outCursor[from] = srcBottom;
      const dstTop = inCursor[to];
      const dstBottom = dstTop - count;
      inCursor[to] = dstBottom;
      flows.push({
        step,
        source: from,
        target: to,
        count,
        stable: from === to,
        srcTop,
        srcBottom,
        dstTop,
        dstBottom,
      });
    });
  });
}

function OpinionFlowLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g data-drawing-container>
      {flows.map((f, i) => {
        const x1 = xScale(waves[f.step]) + NODE_W / 2;
        const x2 = xScale(waves[f.step + 1]) - NODE_W / 2;
        const midX = (x1 + x2) / 2;
        const ySrcTop = yScale(f.srcTop);
        const ySrcBottom = yScale(f.srcBottom);
        const yDstTop = yScale(f.dstTop);
        const yDstBottom = yScale(f.dstBottom);
        return (
          <path
            key={`flow-${i}`}
            d={`M ${x1} ${ySrcTop} C ${midX} ${ySrcTop}, ${midX} ${yDstTop}, ${x2} ${yDstTop} L ${x2} ${yDstBottom} C ${midX} ${yDstBottom}, ${midX} ${ySrcBottom}, ${x1} ${ySrcBottom} Z`}
            fill={categoryColor[f.source]}
            fillOpacity={f.stable ? 0.58 : 0.18}
          />
        );
      })}
      {waves.map((wave, wIdx) => {
        const cx = xScale(wave);
        const isLast = wIdx === waves.length - 1;
        return categories.map((cat) => {
          const ext = nodeExtents[wIdx][cat];
          if (ext.value <= 0) return null;
          const yTop = yScale(ext.top);
          const yBottom = yScale(ext.bottom);
          const midY = (yTop + yBottom) / 2;
          const delta = isLast ? ext.value - populations[0][cat] : 0;
          const lx = cx + NODE_W / 2 + 10;
          const labelText = `${cat} (${ext.value})`;
          const pillW = labelText.length * 8.2 + 14;
          return (
            <React.Fragment key={`${wave}-${cat}`}>
              <rect
                x={cx - NODE_W / 2}
                y={yTop}
                width={NODE_W}
                height={Math.max(2, yBottom - yTop)}
                fill={categoryColor[cat]}
                rx={3}
              />
              {!isLast && (
                <rect
                  x={lx - 6}
                  y={midY - 12}
                  width={pillW}
                  height={22}
                  rx={4}
                  fill={t.pageBg}
                  fillOpacity={0.86}
                />
              )}
              <text
                x={lx}
                y={isLast ? midY - 4 : midY + 4}
                textAnchor="start"
                fontSize={14}
                fontWeight={600}
                fill={t.ink}
              >
                {labelText}
              </text>
              {isLast && (
                <text
                  x={lx}
                  y={midY + 15}
                  textAnchor="start"
                  fontSize={14}
                  fontWeight={600}
                  fill={t.inkSoft}
                >
                  <tspan fill={categoryColor[cat]}>{delta >= 0 ? "▲" : "▼"}</tspan>
                  {delta >= 0 ? ` +${delta} vs ${waves[0]}` : ` ${delta} vs ${waves[0]}`}
                </text>
              )}
            </React.Fragment>
          );
        });
      })}
    </g>
  );
}

const TITLE = "alluvial-opinion-flow · javascript · muix · anyplot.ai";
const countText =
  minWaveTotal === stackTotal
    ? stackTotal.toLocaleString("en-US")
    : `${minWaveTotal.toLocaleString("en-US")}–${stackTotal.toLocaleString("en-US")}`;
const SUBTITLE = `${FLOW_COUNT}: ${countText} · ${WAVE}: ${waves[0]}–${waves[waves.length - 1]}`;
const HEADER_H = 104;

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
          padding: "14px 40px 0 40px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
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
            gap: 18,
            marginTop: 6,
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          {categories.map((cat) => (
            <span
              key={cat}
              style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
            >
              <span
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: 3,
                  backgroundColor: categoryColor[cat],
                  display: "inline-block",
                }}
              />
              <span>{cat}</span>
            </span>
          ))}
          <span style={{ color: INK_MUTED }}>
            · Bold ribbon = stable · Faint ribbon = changed · ▲▼ = net shift
          </span>
        </div>
      </div>
      <ChartsContainer
        width={width}
        height={height - HEADER_H}
        series={[]}
        margin={{ top: 10, right: 230, bottom: 24, left: 60 }}
        xAxis={[
          {
            id: "wave",
            scaleType: "point",
            data: waves,
            position: "top",
            disableLine: true,
            disableTicks: true,
            height: 44,
            tickLabelStyle: { fontSize: 15, fontWeight: 600, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "count",
            scaleType: "linear",
            min: 0,
            max: domainMax,
            position: "none",
          },
        ]}
        skipAnimation
      >
        <ChartsXAxis />
        <OpinionFlowLayer />
      </ChartsContainer>
    </div>
  );
}
