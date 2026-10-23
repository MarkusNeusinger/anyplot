// anyplot.ai
// alluvial-basic: Basic Alluvial Diagram
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 84/100 | Updated: 2026-10-23
import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const NODE_W = 18;
const MID_LABEL_FONT = 13;
const MID_LABEL_MIN_HEIGHT = MID_LABEL_FONT + 6;

// Columns: set these to your data's column names
const TIME_POINT = "Quarter"; // role: time_point
const NEXT_TIME_POINT = "Next quarter"; // role: extra
const CATEGORY = "Subscription tier"; // role: category
const TO_CATEGORY = "Next tier"; // role: extra
const VALUE = "Customers"; // role: value
const FLOW = "Transition count"; // role: flow

// Data: replace this block with your own records, one object per row
const data = (() => {
  const stackOrder = ["Enterprise", "Pro", "Basic", "Free", "Churned"];
  const timePoints = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"];
  const transition = {
    Free: { Free: 0.7, Basic: 0.22, Pro: 0, Enterprise: 0, Churned: 0.08 },
    Basic: { Free: 0.1, Basic: 0.55, Pro: 0.28, Enterprise: 0, Churned: 0.07 },
    Pro: { Free: 0, Basic: 0.1, Pro: 0.65, Enterprise: 0.2, Churned: 0.05 },
    Enterprise: { Free: 0, Basic: 0, Pro: 0.08, Enterprise: 0.9, Churned: 0.02 },
    Churned: { Free: 0.03, Basic: 0, Pro: 0, Enterprise: 0, Churned: 0.97 },
  };
  const populations = [
    { Free: 500, Basic: 300, Pro: 150, Enterprise: 50, Churned: 0 },
  ];
  for (let i = 1; i < timePoints.length; i += 1) {
    const prev = populations[i - 1];
    const next = {};
    stackOrder.forEach((to) => {
      next[to] = stackOrder.reduce(
        (sum, from) => sum + prev[from] * transition[from][to],
        0,
      );
    });
    populations.push(next);
  }

  const rows = [];
  for (let step = 0; step < timePoints.length - 1; step += 1) {
    const pop = populations[step];
    stackOrder.forEach((from) => {
      stackOrder.forEach((to) => {
        const rate = transition[from][to];
        rows.push({
          [TIME_POINT]: timePoints[step],
          [NEXT_TIME_POINT]: timePoints[step + 1],
          [CATEGORY]: from,
          [TO_CATEGORY]: to,
          [VALUE]: pop[from],
          [FLOW]: pop[from] * rate,
        });
      });
    });
  }
  return rows;
})();

// Plot: reads only data and the constants above
const categories = [...new Set(data.map((d) => d[CATEGORY]))];
const timePoints = [
  ...new Set([
    ...data.map((d) => d[TIME_POINT]),
    ...data.map((d) => d[NEXT_TIME_POINT]),
  ]),
];
const categoryColor = Object.fromEntries(
  categories.map((cat, i) => [cat, t.palette[i]]),
);

const populations = timePoints.map((tp, idx) => {
  const pop = {};
  categories.forEach((cat) => {
    if (idx < timePoints.length - 1) {
      pop[cat] = data
        .filter((d) => d[TIME_POINT] === tp && d[CATEGORY] === cat)
        .reduce((sum, d) => sum + d[FLOW], 0);
    } else {
      const prevTp = timePoints[idx - 1];
      pop[cat] = data
        .filter((d) => d[TIME_POINT] === prevTp && d[TO_CATEGORY] === cat)
        .reduce((sum, d) => sum + d[FLOW], 0);
    }
  });
  return pop;
});

const total = categories.reduce((sum, cat) => sum + populations[0][cat], 0);

const nodeExtents = populations.map((pop) => {
  let cursor = total;
  const extents = {};
  categories.forEach((cat) => {
    const bottom = cursor - pop[cat];
    extents[cat] = { top: cursor, bottom };
    cursor = bottom;
  });
  return extents;
});

const flows = (() => {
  const result = [];
  for (let step = 0; step < timePoints.length - 1; step += 1) {
    const tp = timePoints[step];
    const outCursor = {};
    const inCursor = {};
    categories.forEach((cat) => {
      outCursor[cat] = nodeExtents[step][cat].top;
      inCursor[cat] = nodeExtents[step + 1][cat].top;
    });
    categories.forEach((from) => {
      categories.forEach((to) => {
        const row = data.find(
          (d) =>
            d[TIME_POINT] === tp &&
            d[CATEGORY] === from &&
            d[TO_CATEGORY] === to,
        );
        const val = row ? row[FLOW] : 0;
        if (val < 0.5) return;
        const srcTop = outCursor[from];
        const srcBottom = srcTop - val;
        outCursor[from] = srcBottom;
        const dstTop = inCursor[to];
        const dstBottom = dstTop - val;
        inCursor[to] = dstBottom;
        result.push({
          step,
          from,
          to,
          value: val,
          srcTop,
          srcBottom,
          dstTop,
          dstBottom,
        });
      });
    });
  }
  return result;
})();

function AlluvialFlows() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g data-drawing-container>
      {flows.map((f, i) => {
        const x1 = xScale(timePoints[f.step]) + NODE_W / 2;
        const x2 = xScale(timePoints[f.step + 1]) - NODE_W / 2;
        const midX = (x1 + x2) / 2;
        const ySrcTop = yScale(f.srcTop);
        const ySrcBottom = yScale(f.srcBottom);
        const yDstTop = yScale(f.dstTop);
        const yDstBottom = yScale(f.dstBottom);
        return (
          <path
            key={`flow-${i}`}
            d={`M ${x1} ${ySrcTop} C ${midX} ${ySrcTop}, ${midX} ${yDstTop}, ${x2} ${yDstTop} L ${x2} ${yDstBottom} C ${midX} ${yDstBottom}, ${midX} ${ySrcBottom}, ${x1} ${ySrcBottom} Z`}
            fill={categoryColor[f.from]}
            fillOpacity={0.55}
            stroke={categoryColor[f.from]}
            strokeOpacity={0.55}
            strokeWidth={1}
          />
        );
      })}
    </g>
  );
}

function AlluvialNodes() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g data-drawing-container>
      {timePoints.map((timePoint, colIndex) => {
        const cx = xScale(timePoint);
        const isFirst = colIndex === 0;
        const isLast = colIndex === timePoints.length - 1;
        return categories.map((cat) => {
          const value = populations[colIndex][cat];
          if (value < 0.5) return null;
          const { top, bottom } = nodeExtents[colIndex][cat];
          const yTop = yScale(top);
          const yBottom = yScale(bottom);
          const midY = (yTop + yBottom) / 2;
          const segmentH = yBottom - yTop;
          const showMidLabel =
            !isFirst && !isLast && segmentH >= MID_LABEL_MIN_HEIGHT;
          const midPillW = cat.length * MID_LABEL_FONT * 0.6 + 14;
          const midPillH = MID_LABEL_FONT + 8;
          return (
            <React.Fragment key={`${timePoint}-${cat}`}>
              <rect
                x={cx - NODE_W / 2}
                y={yTop}
                width={NODE_W}
                height={segmentH}
                fill={categoryColor[cat]}
                stroke={t.pageBg}
                strokeWidth={1.5}
              />
              {(isFirst || isLast) && (
                <text
                  x={isFirst ? cx - NODE_W / 2 - 10 : cx + NODE_W / 2 + 10}
                  y={midY + 4}
                  textAnchor={isFirst ? "end" : "start"}
                  fontSize={13}
                  fill={t.inkSoft}
                >
                  {`${cat} · ${Math.round(value)}`}
                </text>
              )}
              {showMidLabel && (
                <>
                  <rect
                    x={cx - midPillW / 2}
                    y={midY - midPillH / 2}
                    width={midPillW}
                    height={midPillH}
                    rx={midPillH / 2}
                    fill={t.pageBg}
                    opacity={0.92}
                  />
                  <text
                    x={cx}
                    y={midY + MID_LABEL_FONT / 2 - 1}
                    textAnchor="middle"
                    fontSize={MID_LABEL_FONT}
                    fill={t.inkSoft}
                  >
                    {cat}
                  </text>
                </>
              )}
            </React.Fragment>
          );
        });
      })}
    </g>
  );
}

function ValueAxisTitle() {
  const { top, height } = useDrawingArea();
  const cy = top + height / 2;
  return (
    <text
      x={16}
      y={cy}
      textAnchor="middle"
      fontSize={13}
      fill={t.inkSoft}
      transform={`rotate(-90, 16, ${cy})`}
    >
      {VALUE}
    </text>
  );
}

const TITLE = "alluvial-basic · javascript · muix · anyplot.ai";
const TITLE_FONT_DEFAULT = 28;
const titleFontSize =
  TITLE.length > 67
    ? Math.round(TITLE_FONT_DEFAULT * (67 / TITLE.length))
    : TITLE_FONT_DEFAULT;
const SUBTITLE = `Simulated SaaS subscription-tier migration · ${Math.round(total).toLocaleString("en-US")} ${VALUE.toLowerCase()} across ${timePoints.length} ${TIME_POINT.toLowerCase()}s`;
const TITLE_H = 44;
const SUBTITLE_H = 26;
const LEGEND_H = 34;

function Legend() {
  return (
    <div
      style={{
        height: LEGEND_H,
        display: "flex",
        alignItems: "center",
        gap: "16px",
        flexWrap: "wrap",
      }}
    >
      {categories.map((cat) => (
        <div
          key={cat}
          style={{ display: "flex", alignItems: "center", gap: "7px" }}
        >
          <span
            style={{
              width: "13px",
              height: "13px",
              borderRadius: "3px",
              backgroundColor: categoryColor[cat],
              display: "inline-block",
            }}
          />
          <span style={{ fontSize: "14px", color: t.inkSoft }}>{cat}</span>
        </div>
      ))}
      <span style={{ fontSize: "14px", color: t.inkSoft, fontStyle: "italic" }}>
        Band width ∝ {FLOW.toLowerCase()}
      </span>
    </div>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - TITLE_H - SUBTITLE_H - LEGEND_H;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ paddingLeft: "20px" }}>
        <div
          style={{
            height: `${TITLE_H}px`,
            lineHeight: `${TITLE_H}px`,
            fontSize: `${titleFontSize}px`,
            fontWeight: 500,
            color: t.ink,
          }}
        >
          {TITLE}
        </div>
        <div
          style={{
            height: `${SUBTITLE_H}px`,
            lineHeight: `${SUBTITLE_H}px`,
            fontSize: "15px",
            fontStyle: "italic",
            color: t.inkSoft,
          }}
        >
          {SUBTITLE}
        </div>
        <Legend />
      </div>
      <ChartsContainer
        width={width}
        height={chartHeight}
        series={[]}
        margin={{ top: 20, bottom: 20, left: 150, right: 150 }}
        xAxis={[
          {
            id: "time",
            scaleType: "point",
            data: timePoints,
            position: "top",
            disableLine: true,
            disableTicks: true,
            height: 40,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft, fontWeight: 600 },
          },
        ]}
        yAxis={[
          {
            id: "value",
            scaleType: "linear",
            min: 0,
            max: total,
            position: "none",
          },
        ]}
        skipAnimation
      >
        <ChartsXAxis axisId="time" />
        <ValueAxisTitle />
        <AlluvialFlows />
        <AlluvialNodes />
      </ChartsContainer>
    </div>
  );
}
