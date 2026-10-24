// anyplot.ai
// campbell-basic: Campbell Diagram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 94/100 | Created: 2026-08-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const ORDER_DASHES = ["12 6", "7 5", "3 4"]; // one step per engine order, in order
const ORDER_OPACITIES = [0.9, 0.75, 0.65];
const RPM_PER_HZ = 60;
const CRITICAL_PALETTE_IDX = 4; // red marks the critical speeds; the modes take the other positions
const Y_PAD_SHARE = 0.08;
const ORDER_LABEL_SHARE = 0.94; // order labels sit at this share of the speed range
const END_LABEL_CHAR_PX = 8.4; // width of one 14 px semibold character
const HEADER_H = 122;

// Columns: set these to your data's column names
const SPEED = "Rotational speed (RPM)"; // role: speed
const MODE = "Mode shape"; // role: extra
const FREQ = "Natural frequency (Hz)"; // role: frequency_mode

// Data: replace this block with your own records, one object per row
const engineOrders = [1, 2, 3];
const data = (() => {
  const modeSpecs = [
    { name: "1st Bending", base: 42, slope: 0.0027 },
    { name: "1st Torsional", base: 88, slope: 0.0008 },
    { name: "2nd Bending", base: 125, slope: -0.0025 },
    { name: "Axial", base: 152, slope: -0.0012 },
  ];
  const rows: { [key: string]: string | number }[] = [];
  for (const m of modeSpecs) {
    for (let s = 0; s <= 6000; s += 100) {
      rows.push({
        [SPEED]: s,
        [MODE]: m.name,
        [FREQ]: Math.round((m.base + m.slope * s) * 100) / 100,
      });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const modeNames = Array.from(new Set(data.map((d) => String(d[MODE]))));
const speeds = Array.from(new Set(data.map((d) => Number(d[SPEED])))).sort(
  (a, b) => a - b,
);
const speedMin = speeds[0];
const speedMax = speeds[speeds.length - 1];
const modePalette = t.palette.filter((_, i) => i !== CRITICAL_PALETTE_IDX);
const criticalColor = t.palette[CRITICAL_PALETTE_IDX];

const modeSeries = modeNames.map((name, idx) => {
  const bySpeed = new Map(
    data
      .filter((d) => String(d[MODE]) === name)
      .map((r) => [Number(r[SPEED]), Number(r[FREQ])]),
  );
  return {
    id: `mode-${idx}`,
    label: name,
    color: modePalette[idx],
    values: speeds.map((s) => bySpeed.get(s) ?? null),
  };
});

const orderCurves = engineOrders.map((order, idx) => ({
  id: `eo-${idx}`,
  order,
  label: `${order}x EO`,
  shortLabel: `${order}x`,
  dash: ORDER_DASHES[idx],
  opacity: ORDER_OPACITIES[idx],
  values: speeds.map((s) => (order * s) / RPM_PER_HZ),
}));

const criticalSpeeds: {
  id: string;
  speed: number;
  freq: number;
}[] = [];

for (const mode of modeSeries) {
  for (const order of orderCurves) {
    for (let i = 0; i < speeds.length - 1; i += 1) {
      const mA = mode.values[i];
      const mB = mode.values[i + 1];
      if (mA === null || mB === null) continue;
      const diffA = mA - order.values[i];
      const diffB = mB - order.values[i + 1];
      if (diffA === 0 || diffA * diffB < 0) {
        const frac = diffA / (diffA - diffB);
        criticalSpeeds.push({
          id: `${mode.id}-${order.id}-${i}`,
          speed: speeds[i] + frac * (speeds[i + 1] - speeds[i]),
          freq: mA + frac * (mB - mA),
        });
      }
    }
  }
}

const allFreqs = [
  ...data.map((d) => Number(d[FREQ])),
  ...orderCurves.flatMap((o) => o.values),
];
const freqMax = Math.max(...allFreqs) * (1 + Y_PAD_SHARE);
const endLabelWidth =
  Math.max(...modeNames.map((name) => name.length)) * END_LABEL_CHAR_PX + 32;

const TITLE = "campbell-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${modeSeries.length} rotor modes · ${engineOrders.length} engine orders (${orderCurves.map((o) => o.shortLabel).join(", ")}) · ${criticalSpeeds.length} critical-speed intersections`;

function CampbellLabels() {
  const xScale = useXScale("speed");
  const yScale = useYScale("freq");
  const { left, width } = useDrawingArea();
  const labelSpeed = speedMin + (speedMax - speedMin) * ORDER_LABEL_SHARE;
  const lineEnd = left + width;

  return (
    <g>
      {orderCurves.map((o) => {
        const lx = xScale(labelSpeed);
        const ly = yScale((o.order * labelSpeed) / RPM_PER_HZ) - 10;
        return (
          <g key={o.id}>
            <rect
              x={lx - 18}
              y={ly - 11}
              width={36}
              height={20}
              rx={4}
              fill={t.pageBg}
              fillOpacity={0.88}
            />
            <text
              x={lx}
              y={ly}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={14}
              fontWeight={600}
              fill={t.inkSoft}
            >
              {o.shortLabel}
            </text>
          </g>
        );
      })}

      {modeSeries.map((m) => {
        const endVal = m.values[m.values.length - 1];
        if (endVal === null) return null;
        const ly = yScale(endVal);
        return (
          <g key={m.id}>
            <line
              x1={lineEnd + 6}
              x2={lineEnd + 18}
              y1={ly}
              y2={ly}
              stroke={m.color}
              strokeWidth={3.2}
              strokeLinecap="round"
            />
            <text
              x={lineEnd + 24}
              y={ly}
              dominantBaseline="central"
              fontSize={14}
              fontWeight={600}
              fill={t.ink}
            >
              {m.label}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - HEADER_H;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        fontFamily: "Inter, system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          paddingTop: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 22,
            alignItems: "center",
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          {modeSeries.map((m) => (
            <div
              key={m.id}
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <span
                style={{
                  width: 24,
                  height: 3.5,
                  background: m.color,
                  borderRadius: 2,
                  display: "inline-block",
                }}
              />
              <span style={{ color: t.ink, fontWeight: 500 }}>{m.label}</span>
            </div>
          ))}
          {orderCurves.map((o) => (
            <div
              key={o.id}
              style={{ display: "flex", alignItems: "center", gap: 6 }}
            >
              <svg width={28} height={10}>
                <line
                  x1={0}
                  y1={5}
                  x2={28}
                  y2={5}
                  stroke={t.inkSoft}
                  strokeWidth={2}
                  strokeDasharray={o.dash}
                  opacity={o.opacity}
                />
              </svg>
              <span>{o.label}</span>
            </div>
          ))}
          <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <svg width={20} height={20}>
              <circle
                cx={10}
                cy={10}
                r={8.5}
                fill={criticalColor}
                stroke={t.pageBg}
                strokeWidth={2}
              />
            </svg>
            <span style={{ color: t.ink, fontWeight: 500 }}>
              Critical Speeds ({criticalSpeeds.length})
            </span>
          </div>
        </div>
      </div>

      <ChartsContainer
        width={width}
        height={chartHeight}
        skipAnimation
        margin={{ top: 20, right: endLabelWidth, bottom: 20, left: 40 }}
        series={[
          ...orderCurves.map((o) => ({
            type: "line",
            id: o.id,
            label: o.label,
            data: o.values,
            color: t.inkSoft,
            showMark: false,
            curve: "linear",
          })),
          ...modeSeries.map((m) => ({
            type: "line",
            id: m.id,
            label: m.label,
            data: m.values,
            color: m.color,
            showMark: false,
            curve: "linear",
          })),
          {
            type: "scatter",
            id: "critical",
            label: "Critical Speeds",
            data: criticalSpeeds.map((cs) => ({
              id: cs.id,
              x: cs.speed,
              y: cs.freq,
            })),
            color: criticalColor,
            markerSize: 8.5,
          },
        ]}
        xAxis={[
          {
            id: "speed",
            scaleType: "linear",
            data: speeds,
            min: speedMin,
            max: speedMax,
            tickNumber: 7,
            height: 64,
            label: SPEED,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "freq",
            min: 0,
            max: freqMax,
            tickNumber: 8,
            width: 88,
            label: FREQ,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": {
            stroke: t.grid,
            opacity: 0.65,
            strokeDasharray: "3 4",
          },
          "& .MuiLineChart-line": {
            strokeWidth: 3.2,
            strokeLinecap: "round",
            strokeLinejoin: "round",
          },
          ...Object.fromEntries(
            orderCurves.map((o) => [
              `& .MuiLineChart-line[data-series="${o.id}"]`,
              {
                strokeWidth: 2,
                strokeDasharray: o.dash,
                strokeLinecap: "butt",
                opacity: o.opacity,
              },
            ]),
          ),
          "& .MuiScatterChart-marker": { stroke: t.pageBg, strokeWidth: 2.2 },
        }}
      >
        <ChartsGrid horizontal vertical />
        <LinePlot />
        <ScatterPlot />
        <CampbellLabels />
        <ChartsXAxis axisId="speed" />
        <ChartsYAxis axisId="freq" />
      </ChartsContainer>
    </div>
  );
}
