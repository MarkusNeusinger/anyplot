// anyplot.ai
// line-markers: Line Plot with Markers
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-05
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const LINE_WIDTH = 2.5;
const MARK_R = 9; // marker radius in px, about 3.5 line widths
// One marker per series in order: a distinct shape, filled and hollow in turn, and a line dash.
// Paths are centred on (0, 0) and moved onto each data point.
const MARKERS = [
  { d: `M ${-MARK_R} 0 A ${MARK_R} ${MARK_R} 0 1 0 ${MARK_R} 0 A ${MARK_R} ${MARK_R} 0 1 0 ${-MARK_R} 0 Z`, filled: true, dash: "none" },
  { d: `M 0 ${-MARK_R * 1.2} L ${MARK_R * 1.2} 0 L 0 ${MARK_R * 1.2} L ${-MARK_R * 1.2} 0 Z`, filled: false, dash: "9 6" },
  { d: `M ${-MARK_R * 0.85} ${-MARK_R * 0.85} H ${MARK_R * 0.85} V ${MARK_R * 0.85} H ${-MARK_R * 0.85} Z`, filled: true, dash: "3 5" },
  { d: `M 0 ${-MARK_R * 1.1} L ${MARK_R * 1.05} ${MARK_R * 0.75} L ${-MARK_R * 1.05} ${MARK_R * 0.75} Z`, filled: false, dash: "13 5 2 5" },
  { d: `M 0 ${MARK_R * 1.1} L ${MARK_R * 1.05} ${-MARK_R * 0.75} L ${-MARK_R * 1.05} ${-MARK_R * 0.75} Z`, filled: true, dash: "18 6" },
  { d: `M ${-MARK_R} ${-MARK_R * 0.35} H ${-MARK_R * 0.35} V ${-MARK_R} H ${MARK_R * 0.35} V ${-MARK_R * 0.35} H ${MARK_R} V ${MARK_R * 0.35} H ${MARK_R * 0.35} V ${MARK_R} H ${-MARK_R * 0.35} V ${MARK_R * 0.35} H ${-MARK_R} Z`, filled: false, dash: "2 4 8 4" },
];
const X_PAD_SHARE = 0.03; // share of the x range added on both sides so the outer markers stay whole
const Y_PAD_SHARE = 0.15; // share of the y range added below and above the data

// Columns: set these to your data's column names
const CHECKPOINT = "QC checkpoint (sequential reading)"; // role: x
const STATION = "Assembly station"; // role: series
const TORQUE = "Torque (N·m)"; // role: y
const TARGET = "Target torque (N·m)"; // role: extra

// Data: replace this block with your own records, one object per row
// Torque-wrench readings at 14 sequential fastener checkpoints on two assembly stations.
const data = Object.entries({
  "Station A": [42.6, 42.3, 42.7, 42.4, 42.8, 42.2, 42.5, 42.6, 42.3, 42.7, 42.4, 42.5, 42.6, 42.3],
  "Station B": [41.9, 42.0, 41.7, 42.1, 41.8, 41.6, 41.9, 41.5, 41.8, 41.7, 41.9, 41.6, 41.8, 41.7],
}).flatMap(([station, readings]) =>
  readings.map((torque, i) => ({ [CHECKPOINT]: i + 1, [STATION]: station, [TORQUE]: torque, [TARGET]: 42.5 })),
);

// Plot: reads only data and the constants above
const stations = [...new Set(data.map((d) => d[STATION]))];
const checkpoints = [...new Set(data.map((d) => d[CHECKPOINT]))].sort((a, b) => a - b);
const lines = stations.map((station, i) => ({
  id: `series-${i}`,
  label: station,
  color: t.palette[i],
  marker: MARKERS[i],
  values: checkpoints.map(
    (c) => data.find((d) => d[STATION] === station && d[CHECKPOINT] === c)?.[TORQUE] ?? null,
  ),
}));
const target = data.find((d) => d[TARGET] != null)?.[TARGET];

const torques = data.map((d) => d[TORQUE]);
const yLow = Math.min(...torques, target ?? Infinity);
const yHigh = Math.max(...torques, target ?? -Infinity);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;
const xPad = (checkpoints[checkpoints.length - 1] - checkpoints[0]) * X_PAD_SHARE;
const unit = TORQUE.match(/\(([^)]+)\)/)?.[1] ?? "";
const targetName = TARGET.replace(/\s*\(.*\)\s*$/, "");

const TITLE = "Fastener Torque QC · line-markers · javascript · muix · anyplot.ai";
const SUBTITLE = `${torques.length} readings at ${checkpoints.length} checkpoints from ${stations.length} stations · range ${Math.min(...torques).toFixed(1)}–${Math.max(...torques).toFixed(1)} ${unit}`;
const HEADER_H = 84;

// Markers drawn at the exact (x, y) of every reading
function MarkerLayer() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  return (
    <g>
      {lines.map((line) =>
        line.values.map((v, j) =>
          v == null ? null : (
            <path
              key={`${line.id}-${checkpoints[j]}`}
              d={line.marker.d}
              transform={`translate(${xScale(checkpoints[j])}, ${yScale(v)})`}
              fill={line.marker.filled ? line.color : t.pageBg}
              stroke={line.marker.filled ? t.pageBg : line.color}
              strokeWidth={line.marker.filled ? 2 : 2.5}
            />
          ),
        ),
      )}
    </g>
  );
}

// The target's name and value in the right margin, beside the end of its line, clear of the data
function TargetLabel() {
  const yScale = useYScale() as (v: number) => number;
  const { left, width } = useDrawingArea();
  if (target == null) return null;
  return (
    <text x={left + width + 12} y={yScale(target)} fontSize={15} fill={t.inkSoft} dominantBaseline="central">
      <tspan x={left + width + 12} dy="-0.6em">
        {targetName}
      </tspan>
      <tspan x={left + width + 12} dy="1.2em">
        {target.toFixed(1)} {unit}
      </tspan>
    </text>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          padding: "16px 48px 0 104px",
          boxSizing: "border-box",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
        }}
      >
        <div>
          <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
          <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
        </div>
        <div style={{ display: "flex", gap: 28, paddingTop: 30 }}>
          {lines.map((line) => (
            <div key={line.id} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 16, color: t.ink }}>
              <svg width={56} height={24} viewBox="-28 -12 56 24">
                <line x1={-26} y1={0} x2={26} y2={0} stroke={line.color} strokeWidth={LINE_WIDTH} strokeDasharray={line.marker.dash} />
                <path
                  d={line.marker.d}
                  fill={line.marker.filled ? line.color : t.pageBg}
                  stroke={line.marker.filled ? t.pageBg : line.color}
                  strokeWidth={line.marker.filled ? 2 : 2.5}
                />
              </svg>
              {line.label}
            </div>
          ))}
        </div>
      </div>
      <LineChart
        width={width}
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        margin={{ top: 16, right: 132, bottom: 16, left: 24 }}
        xAxis={[
          {
            data: checkpoints,
            scaleType: "linear",
            min: checkpoints[0] - xPad,
            max: checkpoints[checkpoints.length - 1] + xPad,
            tickNumber: checkpoints.length,
            tickMinStep: 1,
            label: CHECKPOINT,
            height: 64,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yLow - yPad,
            max: yHigh + yPad,
            label: TORQUE,
            width: 76,
            valueFormatter: (v: number) => v.toFixed(1),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={lines.map((line) => ({
          id: line.id,
          data: line.values,
          label: line.label,
          color: line.color,
          curve: "linear",
          showMark: false,
          valueFormatter: (v: number | null) => (v == null ? "" : `${v.toFixed(1)} ${unit}`),
        }))}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: LINE_WIDTH },
          ...Object.fromEntries(
            lines.map((line) => [`& .MuiLineChart-line[data-series="${line.id}"]`, { strokeDasharray: line.marker.dash }]),
          ),
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        {target != null && (
          <ChartsReferenceLine
            y={target}
            lineStyle={{ stroke: t.inkSoft, strokeDasharray: "5 4", strokeWidth: 1.5 }}
          />
        )}
        <TargetLabel />
        <MarkerLayer />
      </LineChart>
    </div>
  );
}
