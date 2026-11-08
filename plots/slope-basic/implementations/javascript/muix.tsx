// anyplot.ai
// slope-basic: Basic Slope Chart (Slopegraph)
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 89/100 | Updated: 2026-11-08

import { LineChart } from "@mui/x-charts/LineChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const Y_PAD_SHARE = 0.08; // value-axis padding as a share of the value range
const LABEL_GAP_PX = 20; // minimum vertical distance between two end labels
const LABEL_FONT = 15; // px
const DIRECTIONS = [
  { key: "up", label: "Increase", color: t.palette[0] },
  { key: "down", label: "Decrease", color: t.palette[4] },
  { key: "flat", label: "No change", color: t.palette[1] },
];

// Columns: set these to your data's column names
const ENTITY = "Department"; // role: entity
const START = "Satisfaction 2023"; // role: value_start
const END = "Satisfaction 2025"; // role: value_end

// Data: replace this block with your own records, one object per row
// Employee satisfaction score (0-100) by department in two survey waves.
const data = [
  { [ENTITY]: "Customer Support", [START]: 52, [END]: 46 },
  { [ENTITY]: "Sales", [START]: 57, [END]: 51 },
  { [ENTITY]: "Design", [START]: 47, [END]: 55 },
  { [ENTITY]: "Marketing", [START]: 65, [END]: 60 },
  { [ENTITY]: "Finance", [START]: 61, [END]: 68 },
  { [ENTITY]: "Product", [START]: 79, [END]: 72 },
  { [ENTITY]: "HR", [START]: 70, [END]: 77 },
  { [ENTITY]: "Operations", [START]: 74, [END]: 82 },
  { [ENTITY]: "Engineering", [START]: 83, [END]: 90 },
];

// Plot: reads only data and the constants above
const rows = data.map((d) => {
  const delta = Number(d[END]) - Number(d[START]);
  const dir = DIRECTIONS.find((k) => k.key === (delta > 0 ? "up" : delta < 0 ? "down" : "flat"));
  return { name: String(d[ENTITY]), start: Number(d[START]), end: Number(d[END]), color: dir?.color as string, dir: dir?.key };
});
const shownDirections = DIRECTIONS.filter((k) => rows.some((r) => r.dir === k.key));

const values = rows.flatMap((r) => [r.start, r.end]);
const vMin = Math.min(...values);
const vMax = Math.max(...values);
const yPad = (vMax - vMin) * Y_PAD_SHARE;
const sideMargin = Math.max(...rows.map((r) => `${r.name} · ${Math.max(r.start, r.end)}`.length)) * LABEL_FONT * 0.55 + 36;

const title = "slope-basic · javascript · muix · anyplot.ai";
const subtitle = `n = ${rows.length} · ${START} → ${END} · ${shownDirections
  .map((k) => `${k.label}: ${rows.filter((r) => r.dir === k.key).length}`)
  .join(", ")}`;
const HEADER_H = 96;

function EndLabels() {
  const xScale = useXScale() as (v: string) => number;
  const yScale = useYScale() as (v: number) => number;
  // Labels keep their line end's value; only crowded labels shift apart along their axis
  const sides = [
    { x: xScale(START) - 16, anchor: "end", key: "start" as const },
    { x: xScale(END) + 16, anchor: "start", key: "end" as const },
  ].map((side) => {
    const placed = rows
      .map((r) => ({ r, y: yScale(r[side.key]) }))
      .sort((a, b) => a.y - b.y);
    for (let i = 1; i < placed.length; i += 1) {
      placed[i].y = Math.max(placed[i].y, placed[i - 1].y + LABEL_GAP_PX);
    }
    return { ...side, placed };
  });
  return (
    <g fontSize={LABEL_FONT} fill={t.ink}>
      {sides.map((side) =>
        side.placed.map(({ r, y }) => (
          <text
            key={`${side.key}-${r.name}`}
            x={side.x}
            y={y}
            textAnchor={side.anchor}
            dominantBaseline="middle"
          >
            {side.key === "start" ? `${r.name} · ${r.start}` : `${r.end} · ${r.name}`}
          </text>
        )),
      )}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 10,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{title}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 28, fontSize: 15, color: t.inkSoft }}>
          <span>{subtitle}</span>
          {shownDirections.map((k) => (
            <span key={k.key} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 16, color: t.ink }}>
              <svg width={28} height={12}>
                <line x1={2} y1={6} x2={26} y2={6} stroke={k.color} strokeWidth={3} strokeLinecap="round" />
                <circle cx={14} cy={6} r={4} fill={t.pageBg} stroke={k.color} strokeWidth={2.5} />
              </svg>
              {k.label}
            </span>
          ))}
        </div>
      </div>
      <LineChart
        width={width}
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        margin={{ left: sideMargin, right: sideMargin, top: 8, bottom: 24 }}
        xAxis={[
          {
            scaleType: "point",
            data: [START, END],
            position: "top",
            height: 40,
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: { fontSize: 16, fontWeight: 600, fill: t.ink },
          },
        ]}
        yAxis={[{ min: vMin - yPad, max: vMax + yPad, position: "none" }]}
        series={rows.map((r, i) => ({
          id: `entity-${i}`,
          label: r.name,
          data: [r.start, r.end],
          color: r.color,
          curve: "linear",
          showMark: true,
          shape: "circle",
        }))}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiLineChart-mark": { strokeWidth: 2.5 },
        }}
      >
        <EndLabels />
      </LineChart>
    </div>
  );
}
