// anyplot.ai
// polar-scatter: Polar Scatter Plot
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-05
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const TITLE = "polar-scatter · javascript · muix · anyplot.ai";

// Constants
const CATEGORY_COL = "Time of Day";
const BEARING_COL = "Wind Bearing (°)";
const SPEED_COL = "Wind Speed (m/s)";

const POINTS_PER_GROUP = 30;
const MIN_SPEED_FLOOR = 0.5;
const SPEED_CEIL_CAP = 20;
const RING_COUNT = 4;
const SPOKE_STEP_DEG = 45;
const FULL_CIRCLE_DEG = 360;
const FILL_OPACITY = 0.72;
const MARKER_SIZE = 8;
const TITLE_HEIGHT = 70;
const LEGEND_HEIGHT = 54;
const CHART_MARGIN = { top: 36, bottom: 36, left: 36, right: 36 };
const LABEL_RADIUS_FACTOR = 1.13;
const DOMAIN_PAD_FACTOR = 1.26;
const TICK_SPOKE_DEG = 245;

const GROUP_SEEDS = [
  { name: "Morning", meanBearing: 15, meanSpeed: 7, spread: 85 },
  { name: "Afternoon", meanBearing: 105, meanSpeed: 13, spread: 90 },
  { name: "Evening", meanBearing: 195, meanSpeed: 10, spread: 80 },
  { name: "Night", meanBearing: 285, meanSpeed: 4, spread: 75 },
];

// Data — deterministic diurnal wind observations (flat scalar records)
const DATA = [];
let lcgState = 42;
for (const cfg of GROUP_SEEDS) {
  for (let idx = 0; idx < POINTS_PER_GROUP; idx += 1) {
    lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
    const u1 = lcgState / 4294967296;
    lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
    const u2 = lcgState / 4294967296;
    const bearing = (((cfg.meanBearing + (u1 - 0.5) * cfg.spread) % FULL_CIRCLE_DEG) + FULL_CIRCLE_DEG) % FULL_CIRCLE_DEG;
    const speed = Math.min(
      SPEED_CEIL_CAP,
      Math.max(MIN_SPEED_FLOOR, cfg.meanSpeed + (u2 - 0.5) * cfg.meanSpeed),
    );
    DATA.push({
      [CATEGORY_COL]: cfg.name,
      [BEARING_COL]: Math.round(bearing * 100) / 100,
      [SPEED_COL]: Math.round(speed * 100) / 100,
    });
  }
}

// Derive categories in order of first appearance and radial domain from DATA
const categories = [];
for (const row of DATA) {
  const cat = String(row[CATEGORY_COL]);
  if (!categories.includes(cat)) categories.push(cat);
}

const rawMaxSpeed = Math.max(...DATA.map((r) => Number(r[SPEED_COL])), 1);
const ringStep = Math.ceil(rawMaxSpeed / RING_COUNT / 5) * 5;
const maxRadius = ringStep * RING_COUNT;
const rings = [];
for (let k = 1; k <= RING_COUNT; k += 1) {
  rings.push(k * ringStep);
}

const spokeDegrees = [];
for (let deg = 0; deg < FULL_CIRCLE_DEG; deg += SPOKE_STEP_DEG) {
  spokeDegrees.push(deg);
}

const bearingUnitMatch = BEARING_COL.match(/\(([^)]+)\)/);
const bearingUnit = bearingUnitMatch ? bearingUnitMatch[1] : "°";
const speedUnitMatch = SPEED_COL.match(/\(([^)]+)\)/);
const speedUnit = speedUnitMatch ? speedUnitMatch[1] : "m/s";

const labelRadius = maxRadius * LABEL_RADIUS_FACTOR;
const domainLimit = maxRadius * DOMAIN_PAD_FACTOR;
const tickSpokeRad = (TICK_SPOKE_DEG * Math.PI) / 180;

const seriesGroups = categories.map((cat, i) => {
  const catRows = DATA.filter((r) => String(r[CATEGORY_COL]) === cat);
  const label = String(catRows[0]?.[CATEGORY_COL] ?? cat);
  const baseHex = t.palette[i];
  const cleanHex = baseHex.replace("#", "");
  const rVal = parseInt(cleanHex.substring(0, 2), 16);
  const gVal = parseInt(cleanHex.substring(2, 4), 16);
  const bVal = parseInt(cleanHex.substring(4, 6), 16);
  const rgbaColor = `rgba(${rVal}, ${gVal}, ${bVal}, ${FILL_OPACITY})`;

  const points = catRows.map((row, idx) => {
    const bearingDeg = Number(row[BEARING_COL]);
    const radiusVal = Number(row[SPEED_COL]);
    const rad = (bearingDeg * Math.PI) / 180;
    return {
      id: `${label}-${idx}`,
      x: radiusVal * Math.sin(rad),
      y: radiusVal * Math.cos(rad),
    };
  });

  return {
    type: "scatter",
    id: label,
    label,
    baseColor: baseHex,
    color: rgbaColor,
    markerSize: MARKER_SIZE,
    data: points,
  };
});

function PolarGrid() {
  const xScale = useXScale();
  const yScale = useYScale();
  if (!xScale || !yScale) return null;

  const cx = xScale(0);
  const cy = yScale(0);

  return (
    <g>
      {rings.map((r) => (
        <circle
          key={`ring-${r}`}
          cx={cx}
          cy={cy}
          r={Math.abs(xScale(r) - cx)}
          fill="none"
          stroke={t.grid}
          strokeWidth={r === maxRadius ? 1.5 : 1}
        />
      ))}
      {spokeDegrees.map((deg) => {
        const rad = (deg * Math.PI) / 180;
        const sx = maxRadius * Math.sin(rad);
        const sy = maxRadius * Math.cos(rad);
        const lx = labelRadius * Math.sin(rad);
        const ly = labelRadius * Math.cos(rad);
        return (
          <g key={`spoke-${deg}`}>
            <line
              x1={cx}
              y1={cy}
              x2={xScale(sx)}
              y2={yScale(sy)}
              stroke={t.grid}
              strokeWidth={1}
            />
            <text
              x={xScale(lx)}
              y={yScale(ly)}
              fill={t.inkSoft}
              fontSize={14}
              fontWeight={deg % 90 === 0 ? 600 : 400}
              textAnchor="middle"
              dominantBaseline="central"
            >
              {`${deg}${bearingUnit}`}
            </text>
          </g>
        );
      })}
      {rings.map((r) => {
        const tx = xScale(r * Math.sin(tickSpokeRad));
        const ty = yScale(r * Math.cos(tickSpokeRad));
        const tickText = `${r} ${speedUnit}`;
        const pillWidth = tickText.length * 8.2 + 12;
        return (
          <g key={`ring-label-${r}`}>
            <rect
              x={tx - pillWidth / 2}
              y={ty - 11}
              width={pillWidth}
              height={22}
              rx={4}
              fill={t.pageBg}
            />
            <text
              x={tx}
              y={ty}
              fill={t.inkSoft}
              fontSize={14}
              textAnchor="middle"
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
  const { width, height } = window.ANYPLOT_SIZE;
  const chartSize = height - TITLE_HEIGHT - LEGEND_HEIGHT;

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartsContainer
        width={chartSize}
        height={chartSize}
        margin={CHART_MARGIN}
        skipAnimation
        xAxis={[{ scaleType: "linear", min: -domainLimit, max: domainLimit, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: -domainLimit, max: domainLimit, position: "none" }]}
        series={seriesGroups}
      >
        <PolarGrid />
        <ScatterPlot />
      </ChartsContainer>
      <div
        style={{
          height: LEGEND_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 28,
        }}
      >
        {seriesGroups.map((group) => (
          <div key={group.id} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                backgroundColor: group.baseColor,
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: 15, color: t.inkSoft, fontWeight: 500 }}>{group.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
