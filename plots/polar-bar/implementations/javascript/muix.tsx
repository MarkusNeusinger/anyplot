// anyplot.ai
// polar-bar: Polar Bar Chart (Wind Rose)
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-09-05
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;
const TITLE = "polar-bar · javascript · muix · anyplot.ai";

// Constants
const DIRECTION_COL = "Direction";
const SPEED_BIN_COL = "Wind Speed";
const COUNT_COL = "Observations (obs)";

const RING_COUNT = 4;
const WEDGE_GAP_RAD = 0.035;
const OUTER_PAD_PX = 64;
const LABEL_OFFSET_PX = 28;
const HEADER_HEIGHT = 64;
const FOOTER_HEIGHT = 56;

// Data — monthly wind observations by compass direction and speed range
const DATA = [
  { [DIRECTION_COL]: "N", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 18 },
  { [DIRECTION_COL]: "NNE", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 15 },
  { [DIRECTION_COL]: "NE", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 12 },
  { [DIRECTION_COL]: "ENE", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 10 },
  { [DIRECTION_COL]: "E", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 14 },
  { [DIRECTION_COL]: "ESE", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 20 },
  { [DIRECTION_COL]: "SE", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 25 },
  { [DIRECTION_COL]: "SSE", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 30 },
  { [DIRECTION_COL]: "S", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 35 },
  { [DIRECTION_COL]: "SSW", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 40 },
  { [DIRECTION_COL]: "SW", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 45 },
  { [DIRECTION_COL]: "WSW", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 42 },
  { [DIRECTION_COL]: "W", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 38 },
  { [DIRECTION_COL]: "WNW", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 30 },
  { [DIRECTION_COL]: "NW", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 24 },
  { [DIRECTION_COL]: "NNW", [SPEED_BIN_COL]: "Light (0–10 mph)", [COUNT_COL]: 20 },

  { [DIRECTION_COL]: "N", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 10 },
  { [DIRECTION_COL]: "NNE", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 8 },
  { [DIRECTION_COL]: "NE", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 6 },
  { [DIRECTION_COL]: "ENE", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 5 },
  { [DIRECTION_COL]: "E", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 8 },
  { [DIRECTION_COL]: "ESE", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 14 },
  { [DIRECTION_COL]: "SE", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 18 },
  { [DIRECTION_COL]: "SSE", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 24 },
  { [DIRECTION_COL]: "S", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 30 },
  { [DIRECTION_COL]: "SSW", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 38 },
  { [DIRECTION_COL]: "SW", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 46 },
  { [DIRECTION_COL]: "WSW", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 40 },
  { [DIRECTION_COL]: "W", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 32 },
  { [DIRECTION_COL]: "WNW", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 22 },
  { [DIRECTION_COL]: "NW", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 16 },
  { [DIRECTION_COL]: "NNW", [SPEED_BIN_COL]: "Moderate (10–20 mph)", [COUNT_COL]: 12 },

  { [DIRECTION_COL]: "N", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 2 },
  { [DIRECTION_COL]: "NNE", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 1 },
  { [DIRECTION_COL]: "NE", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 1 },
  { [DIRECTION_COL]: "ENE", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 1 },
  { [DIRECTION_COL]: "E", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 2 },
  { [DIRECTION_COL]: "ESE", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 4 },
  { [DIRECTION_COL]: "SE", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 6 },
  { [DIRECTION_COL]: "SSE", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 10 },
  { [DIRECTION_COL]: "S", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 14 },
  { [DIRECTION_COL]: "SSW", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 20 },
  { [DIRECTION_COL]: "SW", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 28 },
  { [DIRECTION_COL]: "WSW", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 22 },
  { [DIRECTION_COL]: "W", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 15 },
  { [DIRECTION_COL]: "WNW", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 8 },
  { [DIRECTION_COL]: "NW", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 4 },
  { [DIRECTION_COL]: "NNW", [SPEED_BIN_COL]: "Strong (20+ mph)", [COUNT_COL]: 3 },
];

// Derive directions and speed bins in order of first appearance
const directions = [];
const speedBinLabels = [];
for (const row of DATA) {
  const dir = String(row[DIRECTION_COL]);
  const bin = String(row[SPEED_BIN_COL]);
  if (!directions.includes(dir)) directions.push(dir);
  if (!speedBinLabels.includes(bin)) speedBinLabels.push(bin);
}

const speedBins = speedBinLabels.map((label, idx) => ({
  label,
  color: t.palette[idx],
}));

const countUnitMatch = COUNT_COL.match(/\(([^)]+)\)/);
const countUnit = countUnitMatch ? countUnitMatch[1] : "";

const dirCount = directions.length;
const sectorHalfWidth = Math.PI / dirCount;

// Group values by direction and compute radial domain
const directionStacks = directions.map((dir, i) => {
  const angle = (-90 + (i * 360) / dirCount) * (Math.PI / 180);
  let cumulative = 0;
  const segments = speedBins.map((bin) => {
    const match = DATA.find(
      (r) => String(r[DIRECTION_COL]) === dir && String(r[SPEED_BIN_COL]) === bin.label,
    );
    const val = match ? Number(match[COUNT_COL]) : 0;
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

const rawMaxTotal = Math.max(...directionStacks.map((d) => d.total), 1);
const ringStep = Math.ceil(rawMaxTotal / RING_COUNT / 10) * 10;
const maxValue = ringStep * RING_COUNT;
const rings = [];
for (let k = 1; k <= RING_COUNT; k += 1) {
  rings.push(k * ringStep);
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
      {/* Concentric frequency rings */}
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

      {/* Spokes and rim labels for all compass directions */}
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

      {/* Stacked wedges */}
      {directionStacks.map((item) => {
        const a0 = item.angle - sectorHalfWidth + WEDGE_GAP_RAD;
        const a1 = item.angle + sectorHalfWidth - WEDGE_GAP_RAD;
        const cos0 = Math.cos(a0);
        const sin0 = Math.sin(a0);
        const cos1 = Math.cos(a1);
        const sin1 = Math.sin(a1);

        return item.segments.map((seg) => {
          const r0 = seg.startVal * pxPerUnit;
          const r1 = seg.endVal * pxPerUnit;
          if (r1 <= r0) return null;
          const ox0 = cx + r1 * cos0;
          const oy0 = cy + r1 * sin0;
          const ox1 = cx + r1 * cos1;
          const oy1 = cy + r1 * sin1;
          let pathD = "";
          if (r0 < 0.5) {
            pathD = `M ${cx},${cy} L ${ox0},${oy0} A ${r1} ${r1} 0 0 1 ${ox1},${oy1} Z`;
          } else {
            const ix0 = cx + r0 * cos0;
            const iy0 = cy + r0 * sin0;
            const ix1 = cx + r0 * cos1;
            const iy1 = cy + r0 * sin1;
            pathD =
              `M ${ix0},${iy0} L ${ox0},${oy0} ` +
              `A ${r1} ${r1} 0 0 1 ${ox1},${oy1} L ${ix1},${iy1} ` +
              `A ${r0} ${r0} 0 0 0 ${ix0},${iy0} Z`;
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

      {/* Frequency tick labels along the top spoke with pageBg pill badges */}
      {rings.map((level) => {
        const ty = cy - (level / maxValue) * radius;
        const tickText = countUnit ? `${level} ${countUnit}` : `${level}`;
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
