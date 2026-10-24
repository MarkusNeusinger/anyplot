// anyplot.ai
// polar-scatter: Polar Scatter Plot
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 83/100 | Updated: 2026-10-24
//# anyplot-orientation: square

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "polar-scatter · javascript · muix · anyplot.ai";
const RING_COUNT = 4;
const SPOKE_STEP_DEG = 45;
const FULL_CIRCLE_DEG = 360;
const DEG_SYMBOL = "°";
const FILL_OPACITY = 0.72;
const MARKER_SIZE = 8;
const TITLE_HEIGHT = 74;
const LEGEND_HEIGHT = 40;
const CHART_MARGIN = { top: 14, bottom: 14, left: 14, right: 14 };
const LABEL_RADIUS_FACTOR = 1.065;
const DOMAIN_PAD_FACTOR = 1.11;

// Columns: set these to your data's column names
const CATEGORY = "Time of Day"; // role: group
const BEARING = "Wind Bearing (°)"; // role: theta
const SPEED = "Wind Speed (m/s)"; // role: r

// Data: replace this block with your own records
const POINTS_PER_GROUP = 30;
const MIN_SPEED_FLOOR = 0.5;
const SPEED_CEIL_CAP = 20;
const GROUP_SEEDS = [
  { name: "Morning", meanBearing: 15, meanSpeed: 7, spread: 85 },
  { name: "Afternoon", meanBearing: 105, meanSpeed: 13, spread: 90 },
  { name: "Evening", meanBearing: 195, meanSpeed: 10, spread: 80 },
  { name: "Night", meanBearing: 285, meanSpeed: 4, spread: 75 },
];

const data: Array<Record<string, string | number>> = [];
let lcgState = 42;
for (const cfg of GROUP_SEEDS) {
  for (let idx = 0; idx < POINTS_PER_GROUP; idx += 1) {
    lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
    const u1 = lcgState / 4294967296;
    lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
    const u2 = lcgState / 4294967296;
    const bearing =
      (((cfg.meanBearing + (u1 - 0.5) * cfg.spread) % FULL_CIRCLE_DEG) + FULL_CIRCLE_DEG) %
      FULL_CIRCLE_DEG;
    const speed = Math.min(
      SPEED_CEIL_CAP,
      Math.max(MIN_SPEED_FLOOR, cfg.meanSpeed + (u2 - 0.5) * cfg.meanSpeed),
    );
    data.push({
      [CATEGORY]: cfg.name,
      [BEARING]: Math.round(bearing * 100) / 100,
      [SPEED]: Math.round(speed * 100) / 100,
    });
  }
}

// Plot: reads only data and the constants above
const categories: string[] = [];
for (const row of data) {
  const cat = String(row[CATEGORY]);
  if (!categories.includes(cat)) categories.push(cat);
}

const rawMaxSpeed = Math.max(...data.map((r) => Number(r[SPEED])));
const rawStep = rawMaxSpeed / RING_COUNT;
const stepMag = 10 ** Math.floor(Math.log10(rawStep));
const stepNorm = rawStep / stepMag;
const ringStep = (stepNorm <= 1 ? 1 : stepNorm <= 2 ? 2 : stepNorm <= 5 ? 5 : 10) * stepMag;
const ringDecimals = Math.max(0, -Math.floor(Math.log10(ringStep) + 1e-9));
const maxRadius = ringStep * RING_COUNT;
const rings: number[] = [];
for (let k = 1; k <= RING_COUNT; k += 1) {
  rings.push(Number((k * ringStep).toFixed(ringDecimals)));
}

const spokeDegrees: number[] = [];
for (let deg = 0; deg < FULL_CIRCLE_DEG; deg += SPOKE_STEP_DEG) {
  spokeDegrees.push(deg);
}

// Choose ring-label bearing at the centre of the 45° sector with fewest points
const sectorCount = FULL_CIRCLE_DEG / SPOKE_STEP_DEG;
const sectorCounts = new Array<number>(sectorCount).fill(0);
for (const row of data) {
  const b = (((Number(row[BEARING]) % FULL_CIRCLE_DEG) + FULL_CIRCLE_DEG) % FULL_CIRCLE_DEG);
  const sIdx = Math.min(sectorCount - 1, Math.floor(b / SPOKE_STEP_DEG));
  sectorCounts[sIdx] += 1;
}
let minSectorIdx = 0;
for (let s = 1; s < sectorCount; s += 1) {
  if (sectorCounts[s] < sectorCounts[minSectorIdx]) {
    minSectorIdx = s;
  }
}
const tickSpokeDeg = minSectorIdx * SPOKE_STEP_DEG + SPOKE_STEP_DEG / 2;
const tickSpokeRad = (tickSpokeDeg * Math.PI) / 180;

const speedUnitMatch = /\(([^)]+)\)/.exec(SPEED);
const speedUnit = speedUnitMatch ? speedUnitMatch[1] : "";

const labelRadius = maxRadius * LABEL_RADIUS_FACTOR;
const domainLimit = maxRadius * DOMAIN_PAD_FACTOR;

const seriesGroups = categories.map((cat, i) => {
  const catRows = data.filter((r) => String(r[CATEGORY]) === cat);
  const points = catRows.map((row, idx) => {
    const bearingDeg = Number(row[BEARING]);
    const radiusVal = Number(row[SPEED]);
    const rad = (bearingDeg * Math.PI) / 180;
    return {
      id: `${cat}-${idx}`,
      x: radiusVal * Math.sin(rad),
      y: radiusVal * Math.cos(rad),
    };
  });

  return {
    type: "scatter" as const,
    id: cat,
    label: cat,
    color: t.palette[i],
    markerSize: MARKER_SIZE,
    data: points,
  };
});

function PolarGrid() {
  const xScale = useXScale();
  const yScale = useYScale();

  const cx = Number(xScale(0));
  const cy = Number(yScale(0));

  return (
    <g>
      {rings.map((r) => (
        <circle
          key={`ring-${r}`}
          cx={cx}
          cy={cy}
          r={Math.abs(Number(xScale(r)) - cx)}
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
              {`${deg}${DEG_SYMBOL}`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

// Drawn after <ScatterPlot /> so the ring labels stay readable above the markers
function RingLabels() {
  const xScale = useXScale();
  const yScale = useYScale();

  return (
    <g>
      {rings.map((r) => {
        const tx = Number(xScale(r * Math.sin(tickSpokeRad)));
        const ty = Number(yScale(r * Math.cos(tickSpokeRad)));
        const rStr = r.toFixed(ringDecimals);
        const tickText = speedUnit ? `${rStr} ${speedUnit}` : rStr;
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
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>
          {`Angle: ${BEARING}, clockwise from 0${DEG_SYMBOL} at top  ·  Radius: ${SPEED}`}
        </div>
      </div>
      <ChartsDataProvider
        width={chartSize}
        height={chartSize}
        margin={CHART_MARGIN}
        skipAnimation
        xAxis={[{ scaleType: "linear", min: -domainLimit, max: domainLimit, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: -domainLimit, max: domainLimit, position: "none" }]}
        series={seriesGroups}
      >
        <ChartsWrapper
          legendPosition={{ vertical: "bottom", horizontal: "center" }}
          sx={{ "& .MuiScatterChart-marker": { fillOpacity: FILL_OPACITY } }}
        >
          <ChartsLegend sx={{ fontSize: 15, color: t.inkSoft, gap: 3.5 }} />
          <ChartsSurface>
            <PolarGrid />
            <ScatterPlot />
            <RingLabels />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
