// anyplot.ai
// polar-bar: Polar Bar Chart (Wind Rose)
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "polar-bar · javascript · muix · anyplot.ai";
const RING_COUNT = 4;
const WEDGE_GAP_RAD = 0.035;
const OUTER_PAD_PX = 64;
const LABEL_OFFSET_PX = 28;
const HEADER_HEIGHT = 64;
const FOOTER_HEIGHT = 56;

// Columns: set these to your data's column names
const DIRECTION = "Direction"; // role: theta
const SPEED_BIN = "Wind Speed"; // role: group
const COUNT = "Observations (obs)"; // role: r

// Data: replace this block with your own records
const data: Array<Record<string, string | number>> = [
  { [DIRECTION]: "N", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 18 },
  { [DIRECTION]: "NNE", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 15 },
  { [DIRECTION]: "NE", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 12 },
  { [DIRECTION]: "ENE", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 10 },
  { [DIRECTION]: "E", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 14 },
  { [DIRECTION]: "ESE", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 20 },
  { [DIRECTION]: "SE", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 25 },
  { [DIRECTION]: "SSE", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 30 },
  { [DIRECTION]: "S", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 35 },
  { [DIRECTION]: "SSW", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 40 },
  { [DIRECTION]: "SW", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 45 },
  { [DIRECTION]: "WSW", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 42 },
  { [DIRECTION]: "W", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 38 },
  { [DIRECTION]: "WNW", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 30 },
  { [DIRECTION]: "NW", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 24 },
  { [DIRECTION]: "NNW", [SPEED_BIN]: "Light (0–10 mph)", [COUNT]: 20 },

  { [DIRECTION]: "N", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 10 },
  { [DIRECTION]: "NNE", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 8 },
  { [DIRECTION]: "NE", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 6 },
  { [DIRECTION]: "ENE", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 5 },
  { [DIRECTION]: "E", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 8 },
  { [DIRECTION]: "ESE", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 14 },
  { [DIRECTION]: "SE", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 18 },
  { [DIRECTION]: "SSE", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 24 },
  { [DIRECTION]: "S", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 30 },
  { [DIRECTION]: "SSW", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 38 },
  { [DIRECTION]: "SW", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 46 },
  { [DIRECTION]: "WSW", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 40 },
  { [DIRECTION]: "W", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 32 },
  { [DIRECTION]: "WNW", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 22 },
  { [DIRECTION]: "NW", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 16 },
  { [DIRECTION]: "NNW", [SPEED_BIN]: "Moderate (10–20 mph)", [COUNT]: 12 },

  { [DIRECTION]: "N", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 2 },
  { [DIRECTION]: "NNE", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 1 },
  { [DIRECTION]: "NE", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 1 },
  { [DIRECTION]: "ENE", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 1 },
  { [DIRECTION]: "E", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 2 },
  { [DIRECTION]: "ESE", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 4 },
  { [DIRECTION]: "SE", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 6 },
  { [DIRECTION]: "SSE", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 10 },
  { [DIRECTION]: "S", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 14 },
  { [DIRECTION]: "SSW", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 20 },
  { [DIRECTION]: "SW", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 28 },
  { [DIRECTION]: "WSW", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 22 },
  { [DIRECTION]: "W", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 15 },
  { [DIRECTION]: "WNW", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 8 },
  { [DIRECTION]: "NW", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 4 },
  { [DIRECTION]: "NNW", [SPEED_BIN]: "Strong (20+ mph)", [COUNT]: 3 },
];

// Plot: reads only data and the constants above
const directions: string[] = [];
const speedBinLabels: string[] = [];
for (const row of data) {
  const dir = String(row[DIRECTION]);
  const bin = String(row[SPEED_BIN]);
  if (!directions.includes(dir)) directions.push(dir);
  if (!speedBinLabels.includes(bin)) speedBinLabels.push(bin);
}

const seq0Num = parseInt(t.seq[0].replace("#", ""), 16);
const seq1Num = parseInt(t.seq[1].replace("#", ""), 16);
const r0 = (seq0Num >> 16) & 255;
const g0 = (seq0Num >> 8) & 255;
const b0 = seq0Num & 255;
const r1 = (seq1Num >> 16) & 255;
const g1 = (seq1Num >> 8) & 255;
const b1 = seq1Num & 255;

const speedBins = speedBinLabels.map((label, idx) => {
  const ratio = speedBinLabels.length > 1 ? idx / (speedBinLabels.length - 1) : 1;
  const r = Math.round(r0 + (r1 - r0) * ratio);
  const g = Math.round(g0 + (g1 - g0) * ratio);
  const b = Math.round(b0 + (b1 - b0) * ratio);
  return {
    label,
    color: `rgb(${r}, ${g}, ${b})`,
  };
});

const countUnitMatch = /\(([^)]+)\)/.exec(COUNT);
const countUnit = countUnitMatch ? countUnitMatch[1] : "";

const dirCount = directions.length;
const sectorHalfWidth = Math.PI / dirCount;

const directionStacks = directions.map((dir, i) => {
  const angle = (-90 + (i * 360) / dirCount) * (Math.PI / 180);
  let cumulative = 0;
  const segments = speedBins.map((bin) => {
    const match = data.find(
      (r) => String(r[DIRECTION]) === dir && String(r[SPEED_BIN]) === bin.label,
    );
    const val = match ? Number(match[COUNT]) : 0;
    const startVal = cumulative;
    cumulative += val;
    return {
      binLabel: bin.label,
      color: bin.color,
      startVal,
      endVal: cumulative,
    };
  });
  return { dir, index: i, angle, total: cumulative, segments };
});

const rawMaxTotal = Math.max(...directionStacks.map((d) => d.total));
const rawStep = rawMaxTotal / RING_COUNT;
const stepMag = 10 ** Math.floor(Math.log10(rawStep));
const stepNorm = rawStep / stepMag;
const ringStep = (stepNorm <= 1 ? 1 : stepNorm <= 2 ? 2 : stepNorm <= 5 ? 5 : 10) * stepMag;
const ringDecimals = Math.max(0, -Math.floor(Math.log10(ringStep) + 1e-9));
const maxValue = ringStep * RING_COUNT;
const rings: number[] = [];
for (let k = 1; k <= RING_COUNT; k += 1) {
  rings.push(Number((k * ringStep).toFixed(ringDecimals)));
}

function WindRoseOverlay() {
  const area = useDrawingArea();
  const cx = area.left + area.width / 2;
  const cy = area.top + area.height / 2;
  const half = Math.min(area.width, area.height) / 2;
  const radius = half - OUTER_PAD_PX;
  const labelRadius = radius + LABEL_OFFSET_PX;
  const pxPerUnit = radius / maxValue;

  return (
    <g>
      {rings.map((level) => (
        <circle
          key={`ring-${level}`}
          cx={cx}
          cy={cy}
          r={(level / maxValue) * radius}
          fill="none"
          stroke={t.grid}
          strokeWidth={level === maxValue ? 2 : 1}
          strokeOpacity={level === maxValue ? 1 : 0.65}
        />
      ))}

      {directionStacks.map((item) => {
        const isPrimary = item.index % 2 === 0;
        const ox = cx + radius * Math.cos(item.angle);
        const oy = cy + radius * Math.sin(item.angle);
        const lx = cx + labelRadius * Math.cos(item.angle);
        const ly = cy + labelRadius * Math.sin(item.angle);
        const cos = Math.cos(item.angle);
        const sin = Math.sin(item.angle);
        const anchor = cos > 0.25 ? "start" : cos < -0.25 ? "end" : "middle";
        const baseline = sin > 0.4 ? "hanging" : sin < -0.4 ? "auto" : "central";
        return (
          <g key={`spoke-${item.dir}`}>
            <line
              x1={cx}
              y1={cy}
              x2={ox}
              y2={oy}
              stroke={t.grid}
              strokeWidth={isPrimary ? 1.25 : 0.85}
              strokeOpacity={isPrimary ? 0.9 : 0.5}
            />
            <text
              x={lx}
              y={ly}
              fill={isPrimary ? t.ink : t.inkSoft}
              fontSize={isPrimary ? 16 : 14}
              fontWeight={isPrimary ? 600 : 500}
              textAnchor={anchor}
              dominantBaseline={baseline}
            >
              {item.dir}
            </text>
          </g>
        );
      })}

      {directionStacks.map((item) => {
        const a0 = item.angle - sectorHalfWidth + WEDGE_GAP_RAD;
        const a1 = item.angle + sectorHalfWidth - WEDGE_GAP_RAD;
        const cos0 = Math.cos(a0);
        const sin0 = Math.sin(a0);
        const cos1 = Math.cos(a1);
        const sin1 = Math.sin(a1);

        return item.segments.map((seg) => {
          const r0Px = seg.startVal * pxPerUnit;
          const r1Px = seg.endVal * pxPerUnit;
          if (r1Px <= r0Px) return null;
          const ox0 = cx + r1Px * cos0;
          const oy0 = cy + r1Px * sin0;
          const ox1 = cx + r1Px * cos1;
          const oy1 = cy + r1Px * sin1;
          let pathD = "";
          if (r0Px < 0.5) {
            pathD = `M ${cx},${cy} L ${ox0},${oy0} A ${r1Px} ${r1Px} 0 0 1 ${ox1},${oy1} Z`;
          } else {
            const ix0 = cx + r0Px * cos0;
            const iy0 = cy + r0Px * sin0;
            const ix1 = cx + r0Px * cos1;
            const iy1 = cy + r0Px * sin1;
            pathD =
              `M ${ix0},${iy0} L ${ox0},${oy0} ` +
              `A ${r1Px} ${r1Px} 0 0 1 ${ox1},${oy1} L ${ix1},${iy1} ` +
              `A ${r0Px} ${r0Px} 0 0 0 ${ix0},${iy0} Z`;
          }
          return (
            <path
              key={`wedge-${item.dir}-${seg.binLabel}`}
              d={pathD}
              fill={seg.color}
              stroke={t.pageBg}
              strokeWidth={2}
            />
          );
        });
      })}

      {rings.map((level) => {
        const ty = cy - (level / maxValue) * radius;
        const levelStr = level.toFixed(ringDecimals);
        const tickText = countUnit ? `${levelStr} ${countUnit}` : levelStr;
        const pillWidth = tickText.length * 8.5 + 14;
        return (
          <g key={`tick-${level}`}>
            <rect x={cx + 6} y={ty - 11} width={pillWidth} height={22} rx={4} fill={t.pageBg} />
            <text
              x={cx + 12}
              y={ty}
              fill={t.inkSoft}
              fontSize={14}
              textAnchor="start"
              dominantBaseline="central"
            >
              {tickText}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const chartHeight = size.height - HEADER_HEIGHT - FOOTER_HEIGHT;

  return (
    <div
      style={{
        width: size.width,
        height: size.height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          height: HEADER_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 700,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartsContainer
        width={size.width}
        height={chartHeight}
        series={[]}
        xAxis={[{ position: "none" }]}
        yAxis={[{ position: "none" }]}
        margin={{ top: 16, bottom: 16, left: 24, right: 24 }}
        skipAnimation
      >
        <WindRoseOverlay />
      </ChartsContainer>
      <div
        style={{
          height: FOOTER_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 36,
        }}
      >
        {speedBins.map((bin) => (
          <div
            key={`legend-${bin.label}`}
            style={{ display: "flex", alignItems: "center", gap: 10 }}
          >
            <span
              style={{
                width: 20,
                height: 20,
                borderRadius: 4,
                backgroundColor: bin.color,
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: 15, color: t.ink, fontWeight: 500 }}>{bin.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
