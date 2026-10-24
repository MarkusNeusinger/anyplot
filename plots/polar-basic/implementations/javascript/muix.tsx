// anyplot.ai
// polar-basic: Basic Polar Chart
// Library: muix 9.2.1 | JavaScript 22.23.1
// Quality: 91/100 | Updated: 2026-07-25
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;
const TITLE = "polar-basic · javascript · muix · anyplot.ai";

// Constants
const HOUR_COL = "Hour of Day (h)";
const KWH_COL = "Electricity Draw (kWh)";

const CYCLE_HOURS = 24;
const RING_COUNT = 5;
const SPOKE_STEP_HOURS = 3;
const MARKER_RADIUS = 6.5;
const HEADER_HEIGHT = 68;
const CHART_MARGIN = 36;
const DOMAIN_PAD_FACTOR = 1.16;
const LABEL_RADIUS_FACTOR = 1.09;

// Data — hourly smart-home electricity draw across a 24-hour cycle
const DATA = [
  { [HOUR_COL]: 0, [KWH_COL]: 1.2 },
  { [HOUR_COL]: 1, [KWH_COL]: 1.0 },
  { [HOUR_COL]: 2, [KWH_COL]: 0.9 },
  { [HOUR_COL]: 3, [KWH_COL]: 0.8 },
  { [HOUR_COL]: 4, [KWH_COL]: 0.9 },
  { [HOUR_COL]: 5, [KWH_COL]: 1.3 },
  { [HOUR_COL]: 6, [KWH_COL]: 2.1 },
  { [HOUR_COL]: 7, [KWH_COL]: 3.4 },
  { [HOUR_COL]: 8, [KWH_COL]: 3.8 },
  { [HOUR_COL]: 9, [KWH_COL]: 2.9 },
  { [HOUR_COL]: 10, [KWH_COL]: 2.2 },
  { [HOUR_COL]: 11, [KWH_COL]: 2.0 },
  { [HOUR_COL]: 12, [KWH_COL]: 2.3 },
  { [HOUR_COL]: 13, [KWH_COL]: 2.1 },
  { [HOUR_COL]: 14, [KWH_COL]: 2.0 },
  { [HOUR_COL]: 15, [KWH_COL]: 2.2 },
  { [HOUR_COL]: 16, [KWH_COL]: 2.6 },
  { [HOUR_COL]: 17, [KWH_COL]: 3.5 },
  { [HOUR_COL]: 18, [KWH_COL]: 4.6 },
  { [HOUR_COL]: 19, [KWH_COL]: 4.9 },
  { [HOUR_COL]: 20, [KWH_COL]: 4.2 },
  { [HOUR_COL]: 21, [KWH_COL]: 3.1 },
  { [HOUR_COL]: 22, [KWH_COL]: 2.0 },
  { [HOUR_COL]: 23, [KWH_COL]: 1.5 },
];

// Sort observations by hour and derive radial domain
const sortedRows = [...DATA].sort((a, b) => Number(a[HOUR_COL]) - Number(b[HOUR_COL]));
const rawMaxKwh = Math.max(...sortedRows.map((r) => Number(r[KWH_COL])), 1);
const ringStep = Math.ceil(rawMaxKwh / RING_COUNT);
const maxKwh = ringStep * RING_COUNT;
const rings = [];
for (let k = 1; k <= RING_COUNT; k += 1) {
  rings.push(k * ringStep);
}

const kwhUnitMatch = KWH_COL.match(/\(([^)]+)\)/);
const kwhUnit = kwhUnitMatch ? kwhUnitMatch[1] : "";
const seriesLabel = KWH_COL.replace(/\s*\([^)]*\)/, "");

// Precompute polar points and spoke labels (0h at top, clockwise)
const points = sortedRows.map((row) => {
  const hour = Number(row[HOUR_COL]);
  const val = Number(row[KWH_COL]);
  const angle = (-90 + (hour / CYCLE_HOURS) * 360) * (Math.PI / 180);
  const period = hour < 12 ? "AM" : "PM";
  const h12 = hour % 12 === 0 ? 12 : hour % 12;
  return {
    id: hour,
    hour,
    val,
    angle,
    x: val * Math.cos(angle),
    y: -val * Math.sin(angle),
    clockLabel: `${h12} ${period}`,
  };
});

const spokePoints = points.filter((p) => p.hour % SPOKE_STEP_HOURS === 0);
const domainLimit = maxKwh * DOMAIN_PAD_FACTOR;
const labelRadiusVal = maxKwh * LABEL_RADIUS_FACTOR;

const SERIES = [
  {
    type: "scatter",
    data: points,
    color: t.palette[0],
    markerSize: MARKER_RADIUS,
    label: seriesLabel,
  },
];

function PolarLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  if (!xScale || !yScale) return null;

  const cx = xScale(0);
  const cy = yScale(0);
  const linePoints = points.map((p) => `${xScale(p.x)},${yScale(p.y)}`).join(" ");

  return (
    <g>
      {/* Concentric radial gridlines */}
      {rings.map((level) => (
        <circle
          key={`ring-${level}`}
          cx={cx}
          cy={cy}
          r={Math.abs(xScale(level) - cx)}
          fill="none"
          stroke={t.grid}
          strokeWidth={level === maxKwh ? 2 : 1}
          strokeOpacity={level === maxKwh ? 1 : 0.65}
        />
      ))}

      {/* Angular spokes and clock labels at regular 3-hour intervals */}
      {spokePoints.map((sp) => {
        const isQuarter = sp.hour % 6 === 0;
        const ox = xScale(maxKwh * Math.cos(sp.angle));
        const oy = yScale(-maxKwh * Math.sin(sp.angle));
        const lx = xScale(labelRadiusVal * Math.cos(sp.angle));
        const ly = yScale(-labelRadiusVal * Math.sin(sp.angle));
        const cos = Math.cos(sp.angle);
        const sin = Math.sin(sp.angle);
        const anchor = cos > 0.25 ? "start" : cos < -0.25 ? "end" : "middle";
        const baseline = sin > 0.4 ? "hanging" : sin < -0.4 ? "auto" : "central";
        return (
          <g key={`spoke-${sp.hour}`}>
            <line
              x1={cx}
              y1={cy}
              x2={ox}
              y2={oy}
              stroke={t.grid}
              strokeWidth={isQuarter ? 1.25 : 0.9}
              strokeOpacity={isQuarter ? 0.9 : 0.55}
            />
            <text
              x={lx}
              y={ly}
              fill={isQuarter ? t.ink : t.inkSoft}
              fontSize={isQuarter ? 17 : 14}
              fontWeight={isQuarter ? 600 : 500}
              textAnchor={anchor}
              dominantBaseline={baseline}
            >
              {sp.clockLabel}
            </text>
          </g>
        );
      })}

      {/* Closed polar polygon */}
      <polygon
        points={linePoints}
        fill={t.palette[0]}
        fillOpacity={0.22}
        stroke={t.palette[0]}
        strokeWidth={3}
        strokeLinejoin="round"
      />

      {/* Uniform pageBg halo rings around hourly points */}
      {points.map((p) => (
        <circle
          key={`halo-${p.hour}`}
          cx={xScale(p.x)}
          cy={yScale(p.y)}
          r={MARKER_RADIUS + 1.5}
          fill="none"
          stroke={t.pageBg}
          strokeWidth={2}
        />
      ))}

      {/* Radius tick labels to the left of the top spoke with pageBg pill badges */}
      {rings.map((level) => {
        const ty = yScale(level);
        const tickText = kwhUnit ? `${level} ${kwhUnit}` : `${level}`;
        const pillWidth = tickText.length * 8.5 + 14;
        return (
          <g key={`tick-${level}`}>
            <rect
              x={cx - pillWidth - 6}
              y={ty - 11}
              width={pillWidth}
              height={22}
              rx={4}
              fill={t.pageBg}
            />
            <text
              x={cx - 12}
              y={ty}
              fill={t.inkSoft}
              fontSize={14}
              textAnchor="end"
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
  const chartSize = size.height - HEADER_HEIGHT;

  return (
    <div
      style={{
        width: size.width,
        height: size.height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
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
        width={chartSize}
        height={chartSize}
        series={SERIES}
        xAxis={[{ scaleType: "linear", min: -domainLimit, max: domainLimit, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: -domainLimit, max: domainLimit, position: "none" }]}
        margin={{ top: CHART_MARGIN, bottom: CHART_MARGIN, left: CHART_MARGIN, right: CHART_MARGIN }}
        skipAnimation
      >
        <PolarLayer />
        <ScatterPlot />
      </ChartsContainer>
    </div>
  );
}
