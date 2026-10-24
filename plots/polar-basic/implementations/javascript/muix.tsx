// anyplot.ai
// polar-basic: Basic Polar Chart
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 91/100 | Updated: 2026-07-25
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "polar-basic · javascript · muix · anyplot.ai";
const CYCLE_HOURS = 24;
const RING_COUNT = 5;
const SPOKE_STEP_HOURS = 3;
const MARKER_RADIUS = 6.5;
const HEADER_HEIGHT = 68;
const CHART_MARGIN = 36;
const DOMAIN_PAD_FACTOR = 1.16;
const LABEL_RADIUS_FACTOR = 1.09;

// Columns: set these to your data's column names
const HOUR = "Hour of Day (h)"; // role: theta
const KWH = "Electricity Draw (kWh)"; // role: r

// Data: replace this block with your own records
const data: Array<Record<string, number>> = [
  { [HOUR]: 0, [KWH]: 1.2 },
  { [HOUR]: 1, [KWH]: 1.0 },
  { [HOUR]: 2, [KWH]: 0.9 },
  { [HOUR]: 3, [KWH]: 0.8 },
  { [HOUR]: 4, [KWH]: 0.9 },
  { [HOUR]: 5, [KWH]: 1.3 },
  { [HOUR]: 6, [KWH]: 2.1 },
  { [HOUR]: 7, [KWH]: 3.4 },
  { [HOUR]: 8, [KWH]: 3.8 },
  { [HOUR]: 9, [KWH]: 2.9 },
  { [HOUR]: 10, [KWH]: 2.2 },
  { [HOUR]: 11, [KWH]: 2.0 },
  { [HOUR]: 12, [KWH]: 2.3 },
  { [HOUR]: 13, [KWH]: 2.1 },
  { [HOUR]: 14, [KWH]: 2.0 },
  { [HOUR]: 15, [KWH]: 2.2 },
  { [HOUR]: 16, [KWH]: 2.6 },
  { [HOUR]: 17, [KWH]: 3.5 },
  { [HOUR]: 18, [KWH]: 4.6 },
  { [HOUR]: 19, [KWH]: 4.9 },
  { [HOUR]: 20, [KWH]: 4.2 },
  { [HOUR]: 21, [KWH]: 3.1 },
  { [HOUR]: 22, [KWH]: 2.0 },
  { [HOUR]: 23, [KWH]: 1.5 },
];

// Plot: reads only data and the constants above
const sortedRows = [...data].sort((a, b) => Number(a[HOUR]) - Number(b[HOUR]));
const rawMaxKwh = Math.max(...sortedRows.map((r) => Number(r[KWH])));
const rawStep = rawMaxKwh / RING_COUNT;
const stepMag = 10 ** Math.floor(Math.log10(rawStep));
const stepNorm = rawStep / stepMag;
const ringStep = (stepNorm <= 1 ? 1 : stepNorm <= 2 ? 2 : stepNorm <= 5 ? 5 : 10) * stepMag;
const ringDecimals = Math.max(0, -Math.floor(Math.log10(ringStep) + 1e-9));
const maxKwh = ringStep * RING_COUNT;
const rings: number[] = [];
for (let k = 1; k <= RING_COUNT; k += 1) {
  rings.push(Number((k * ringStep).toFixed(ringDecimals)));
}

const kwhUnitMatch = /\(([^)]+)\)/.exec(KWH);
const kwhUnit = kwhUnitMatch ? kwhUnitMatch[1] : "";

const points = sortedRows.map((row) => {
  const hour = Number(row[HOUR]);
  const val = Number(row[KWH]);
  const angle = (-90 + (hour / CYCLE_HOURS) * 360) * (Math.PI / 180);
  return {
    id: hour,
    hour,
    val,
    angle,
    x: val * Math.cos(angle),
    y: -val * Math.sin(angle),
  };
});

const spokePoints = Array.from({ length: CYCLE_HOURS / SPOKE_STEP_HOURS }, (_, i) => {
  const hour = i * SPOKE_STEP_HOURS;
  const angle = (-90 + (hour / CYCLE_HOURS) * 360) * (Math.PI / 180);
  const period = hour < 12 ? "AM" : "PM";
  const h12 = hour % 12 === 0 ? 12 : hour % 12;
  return {
    hour,
    angle,
    clockLabel: `${h12} ${period}`,
  };
});

const domainLimit = maxKwh * DOMAIN_PAD_FACTOR;
const labelRadiusVal = maxKwh * LABEL_RADIUS_FACTOR;

const series = [
  {
    type: "scatter" as const,
    data: points,
    color: t.palette[0],
    markerSize: MARKER_RADIUS,
    label: KWH,
  },
];

function PolarLayer() {
  const xScale = useXScale();
  const yScale = useYScale();

  const cx = Number(xScale(0));
  const cy = Number(yScale(0));
  const linePoints = points.map((p) => `${xScale(p.x)},${yScale(p.y)}`).join(" ");

  return (
    <g>
      {rings.map((level) => (
        <circle
          key={`ring-${level}`}
          cx={cx}
          cy={cy}
          r={Math.abs(Number(xScale(level)) - cx)}
          fill="none"
          stroke={t.grid}
          strokeWidth={level === maxKwh ? 2 : 1}
          strokeOpacity={level === maxKwh ? 1 : 0.65}
        />
      ))}

      {spokePoints.map((sp) => {
        const isQuarter = sp.hour % 6 === 0;
        const ox = Number(xScale(maxKwh * Math.cos(sp.angle)));
        const oy = Number(yScale(-maxKwh * Math.sin(sp.angle)));
        const lx = Number(xScale(labelRadiusVal * Math.cos(sp.angle)));
        const ly = Number(yScale(-labelRadiusVal * Math.sin(sp.angle)));
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

      <polygon
        points={linePoints}
        fill={t.palette[0]}
        fillOpacity={0.22}
        stroke={t.palette[0]}
        strokeWidth={3}
        strokeLinejoin="round"
      />

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

      {rings.map((level) => {
        const ty = Number(yScale(level));
        const levelStr = level.toFixed(ringDecimals);
        const tickText = kwhUnit ? `${levelStr} ${kwhUnit}` : levelStr;
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
  const size = window.ANYPLOT_SIZE;
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
        series={series}
        xAxis={[{ scaleType: "linear", min: -domainLimit, max: domainLimit, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: -domainLimit, max: domainLimit, position: "none" }]}
        margin={{
          top: CHART_MARGIN,
          bottom: CHART_MARGIN,
          left: CHART_MARGIN,
          right: CHART_MARGIN,
        }}
        skipAnimation
      >
        <PolarLayer />
        <ScatterPlot />
      </ChartsContainer>
    </div>
  );
}
