// anyplot.ai
// rug-basic: Basic Rug Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-07-25

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const FONT = "Inter, system-ui, -apple-system, sans-serif";

// Seeded LCG for deterministic data generation (no seeded RNG in browser)
let seed = 42;
function rand() {
  seed = (Math.imul(1664525, seed) + 1013904223) | 0;
  return (seed >>> 0) / 4294967296;
}
function randn() {
  const u = Math.max(rand(), 1e-10);
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rand());
}

// Reaction times (ms) in a visual cognitive task, two testing sessions
const morning = Array.from({ length: 140 }, () => 420 + 55 * randn());
const evening = Array.from({ length: 140 }, () => 458 + 70 * randn());
// A few slow trials at the tail — attention lapses, visible as outlier ticks
morning.push(636);
evening.push(688, 706, 727);

const LANES = [
  { label: "Morning session", values: morning, color: t.palette[0] },
  { label: "Evening session", values: evening, color: t.palette[1] },
];

const allValues = LANES.flatMap((lane) => lane.values);
const X_MIN = Math.floor(Math.min(...allValues) / 20) * 20 - 20;
const X_MAX = Math.ceil(Math.max(...allValues) / 20) * 20 + 20;

const TICK_HEIGHT = 250; // px, consistent height for every observation tick
const TITLE_H = 60;

// One rug lane: an optional baseline rule plus one semi-transparent tick per
// observation. Overlapping trials (frequent near the distribution centre)
// darken naturally.
function RugLane({ values, color, baselineY, showRule }) {
  const xs = useXScale();
  const { left, width } = useDrawingArea();
  if (!xs) return null;
  return (
    <g>
      {showRule && (
        <line x1={left} x2={left + width} y1={baselineY} y2={baselineY} stroke={t.grid} strokeWidth={1} />
      )}
      {values.map((v, i) => (
        <line
          key={i}
          x1={xs(v)}
          x2={xs(v)}
          y1={baselineY}
          y2={baselineY - TICK_HEIGHT}
          stroke={color}
          strokeWidth={2}
          strokeOpacity={0.42}
          strokeLinecap="round"
        />
      ))}
    </g>
  );
}

function LaneLabel({ text, baselineY, color }) {
  const { left } = useDrawingArea();
  return (
    <text x={left} y={baselineY - TICK_HEIGHT - 16} fontSize={16} fontFamily={FONT} fontWeight={600} fill={color}>
      {text}
    </text>
  );
}

// Two rug lanes sharing one x-axis, vertically split within the drawing area.
// The second lane sits flush on the axis line; the first gets its own rule.
function RugPlot() {
  const { top, height } = useDrawingArea();
  const baselines = [top + height * 0.48, top + height];
  return (
    <g>
      {LANES.map((lane, i) => (
        <RugLane
          key={lane.label}
          values={lane.values}
          color={lane.color}
          baselineY={baselines[i]}
          showRule={i === 0}
        />
      ))}
      {LANES.map((lane, i) => (
        <LaneLabel key={lane.label} text={lane.label} baselineY={baselines[i]} color={lane.color} />
      ))}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  return (
    <div
      style={{
        width: W,
        height: H,
        display: "flex",
        flexDirection: "column",
        backgroundColor: t.pageBg,
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          padding: "18px 36px 0",
          fontSize: 21,
          fontWeight: 600,
          color: t.ink,
          height: TITLE_H,
          boxSizing: "border-box",
          letterSpacing: "-0.3px",
        }}
      >
        Reaction Times by Session · rug-basic · javascript · muix · anyplot.ai
      </div>
      <ChartContainer
        width={W}
        height={H - TITLE_H}
        skipAnimation
        series={[]}
        margin={{ top: 24, right: 60, bottom: 100, left: 60 }}
        xAxis={[
          {
            min: X_MIN,
            max: X_MAX,
            scaleType: "linear",
            label: "Reaction Time (ms)",
            tickMinStep: 40,
            valueFormatter: (v) => String(Math.round(v)),
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { strokeOpacity: 0.15 },
        }}
      >
        <ChartsGrid vertical />
        <RugPlot />
        <ChartsXAxis />
      </ChartContainer>
    </div>
  );
}
