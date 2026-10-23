// anyplot.ai
// campbell-basic: Campbell Diagram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 94/100 | Created: 2026-08-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const ENGINE_ORDERS = [
  { order: 1, dash: "12 6", opacity: 0.9 },
  { order: 2, dash: "7 5", opacity: 0.75 },
  { order: 3, dash: "3 4", opacity: 0.65 },
];
const RPM_PER_HZ = 60;
const Y_PAD_SHARE = 0.08;
const HEADER_H = 122;

// Columns: set these to your data's column names
const SPEED = "Rotational speed (RPM)"; // role: x
const MODE = "Mode shape"; // role: series
const FREQ = "Natural frequency (Hz)"; // role: y

// Data: replace this block with your own records, one object per row
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
const speedMin = Math.min(...speeds);
const speedMax = Math.max(...speeds);

const modeSeries = modeNames.map((name, idx) => {
  const modeRows = data
    .filter((d) => String(d[MODE]) === name)
    .sort((a, b) => Number(a[SPEED]) - Number(b[SPEED]));
  const bySpeed = new Map(
    modeRows.map((r) => [Number(r[SPEED]), Number(r[FREQ])]),
  );
  return {
    id: `mode-${idx}`,
    label: name,
    color: t.palette[idx],
    values: speeds.map((s) => bySpeed.get(s) ?? null),
  };
});

const orderCurves = ENGINE_ORDERS.map((o) => ({
  ...o,
  label: `${o.order}x EO`,
  shortLabel: `${o.order}x`,
  values: speeds.map((s) => (o.order * s) / RPM_PER_HZ),
}));

const criticalSpeeds: {
  id: string;
  speed: number;
  freq: number;
  modeLabel: string;
  orderLabel: string;
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
        const critSpeed = speeds[i] + frac * (speeds[i + 1] - speeds[i]);
        const critFreq = mA + frac * (mB - mA);
        criticalSpeeds.push({
          id: `${mode.id}-eo-${order.order}-${i}`,
          speed: critSpeed,
          freq: critFreq,
          modeLabel: mode.label,
          orderLabel: order.shortLabel,
        });
      }
    }
  }
}

const allFreqs = [
  ...data.map((d) => Number(d[FREQ])),
  ...orderCurves.flatMap((o) => o.values),
];
const freqMaxRaw = Math.max(...allFreqs);
const freqMax = freqMaxRaw * (1 + Y_PAD_SHARE);
const criticalColor = t.palette[modeNames.length];

const TITLE = "campbell-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${modeSeries.length} rotor modes · ${ENGINE_ORDERS.length} engine orders (${ENGINE_ORDERS.map((o) => `${o.order}x`).join(", ")}) · ${criticalSpeeds.length} critical-speed intersections`;

function CampbellOverlay() {
  const xScale = useXScale("speed");
  const yScale = useYScale("freq");
  const { left, top, width, height } = useDrawingArea();
  if (!xScale || !yScale) return null;

  return (
    <g>
      {orderCurves.map((o) => {
        const x0 = xScale(speedMin);
        const y0 = yScale((o.order * speedMin) / RPM_PER_HZ);
        const x1 = xScale(speedMax);
        const y1 = yScale((o.order * speedMax) / RPM_PER_HZ);
        if (
          x0 === undefined ||
          y0 === undefined ||
          x1 === undefined ||
          y1 === undefined
        ) {
          return null;
        }
        const labelSpeed = speedMax * 0.94;
        const lx = xScale(labelSpeed) ?? x1;
        const ly = (yScale((o.order * labelSpeed) / RPM_PER_HZ) ?? y1) - 10;

        return (
          <g key={o.label}>
            <line
              x1={x0}
              y1={y0}
              x2={x1}
              y2={y1}
              stroke={t.inkSoft}
              strokeWidth={2}
              strokeDasharray={o.dash}
              opacity={o.opacity}
            />
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
        const pts = speeds
          .map((s, idx) => {
            const val = m.values[idx];
            if (val === null) return null;
            const px = xScale(s);
            const py = yScale(val);
            return px !== undefined && py !== undefined ? `${px},${py}` : null;
          })
          .filter(Boolean)
          .join(" ");
        const endVal = m.values[m.values.length - 1];
        if (endVal === null) return null;
        const lx = left + width + 10;
        const ly = yScale(endVal);
        if (ly === undefined) return null;
        return (
          <g key={m.id}>
            <polyline
              points={pts}
              fill="none"
              stroke={m.color}
              strokeWidth={3.2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <text
              x={lx}
              y={ly}
              dominantBaseline="central"
              fontSize={14}
              fontWeight={600}
              fill={m.color}
            >
              {m.label}
            </text>
          </g>
        );
      })}

      {criticalSpeeds.map((cs) => {
        const cx = xScale(cs.speed);
        const cy = yScale(cs.freq);
        if (cx === undefined || cy === undefined) return null;
        if (cy < top || cy > top + height) return null;
        const r = 8.5;
        return (
          <g key={cs.id}>
            <polygon
              points={`${cx},${cy - r} ${cx + r},${cy} ${cx},${cy + r} ${cx - r},${cy}`}
              fill={criticalColor}
              stroke={t.pageBg}
              strokeWidth={2.2}
            />
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
              key={o.label}
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
            <svg width={18} height={18}>
              <polygon
                points="9,1 17,9 9,17 1,9"
                fill={criticalColor}
                stroke={t.pageBg}
                strokeWidth={1.5}
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
        margin={{ top: 20, right: 145, bottom: 20, left: 40 }}
        series={[]}
        xAxis={[
          {
            id: "speed",
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
        }}
      >
        <ChartsGrid horizontal vertical />
        <CampbellOverlay />
        <ChartsXAxis axisId="speed" />
        <ChartsYAxis axisId="freq" />
      </ChartsContainer>
    </div>
  );
}
