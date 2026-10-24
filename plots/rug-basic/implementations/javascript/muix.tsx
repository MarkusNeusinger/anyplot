// anyplot.ai
// rug-basic: Basic Rug Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 91/100 | Created: 2026-07-25

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "Reaction Times by Session · rug-basic · javascript · muix · anyplot.ai";
const TITLE_H = 60;
const TICK_FRAC = 0.72;
const NICE_STEP = 20;

// Columns: set these to your data's column names
const SESSION = "Testing session"; // role: group
const VALUES = "Reaction Time (ms)"; // role: values

// Data: replace this block with your own records
const SESSION_SPECS = [
  { name: "Morning session", count: 140, mean: 420, std: 55, tail: [636] },
  { name: "Evening session", count: 140, mean: 458, std: 70, tail: [688, 706, 727] },
];

let seed = 42;
const data = [];
for (const spec of SESSION_SPECS) {
  for (let i = 0; i < spec.count; i += 1) {
    seed = (Math.imul(1664525, seed) + 1013904223) | 0;
    const u1 = Math.max((seed >>> 0) / 4294967296, 1e-10);
    seed = (Math.imul(1664525, seed) + 1013904223) | 0;
    const u2 = (seed >>> 0) / 4294967296;
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    data.push({ [SESSION]: spec.name, [VALUES]: spec.mean + spec.std * z });
  }
  for (const tailVal of spec.tail) {
    data.push({ [SESSION]: spec.name, [VALUES]: tailVal });
  }
}

// Plot: reads only data and the constants above
const sessionNames = Array.from(new Set(data.map((row) => String(row[SESSION]))));
const lanes = sessionNames.map((label, idx) => ({
  label,
  values: data.filter((row) => String(row[SESSION]) === label).map((row) => Number(row[VALUES])),
  color: t.palette[idx % t.palette.length],
  strokeLabel: idx === 1,
}));

const allValues = lanes.flatMap((lane) => lane.values);
const xMin = Math.floor(Math.min(...allValues) / NICE_STEP) * NICE_STEP - NICE_STEP;
const xMax = Math.ceil(Math.max(...allValues) / NICE_STEP) * NICE_STEP + NICE_STEP;

function RugPlot() {
  const xs = useXScale();
  const { left, top, width, height } = useDrawingArea();
  const laneHeight = height / lanes.length;
  const tickHeight = laneHeight * TICK_FRAC;

  return (
    <g>
      {lanes.map((lane, i) => {
        const laneTop = top + i * laneHeight;
        const baselineY = laneTop + laneHeight;
        return (
          <g key={lane.label}>
            <rect x={left} y={laneTop} width={width} height={laneHeight} fill={lane.color} opacity={0.05} />
            {lane.values.map((v, j) => (
              <line
                key={j}
                x1={xs(v)}
                x2={xs(v)}
                y1={baselineY}
                y2={baselineY - tickHeight}
                stroke={lane.color}
                strokeWidth={2}
                strokeOpacity={0.45}
                strokeLinecap="round"
              />
            ))}
            <text
              x={left}
              y={laneTop + 20}
              fontSize={16}
              fontWeight={600}
              fill={lane.color}
              stroke={lane.strokeLabel ? t.ink : "none"}
              strokeWidth={lane.strokeLabel ? 0.75 : 0}
              paintOrder="stroke"
            >
              {lane.label}
            </text>
          </g>
        );
      })}
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
        {TITLE}
      </div>
      <ChartsContainer
        width={W}
        height={H - TITLE_H}
        skipAnimation
        series={[]}
        margin={{ top: 24, right: 60, bottom: 32, left: 60 }}
        xAxis={[
          {
            min: xMin,
            max: xMax,
            scaleType: "linear",
            height: 68,
            label: VALUES,
            tickMinStep: NICE_STEP * 2,
            valueFormatter: (v) => String(Math.round(v)),
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16 },
          },
        ]}
        yAxis={[{ min: 0, max: 1, scaleType: "linear", position: "none" }]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { strokeOpacity: 0.15 },
        }}
      >
        <ChartsGrid vertical />
        <RugPlot />
        <ChartsXAxis />
      </ChartsContainer>
    </div>
  );
}
