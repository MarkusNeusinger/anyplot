// anyplot.ai
// polar-line: Polar Line Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "polar-line · javascript · muix · anyplot.ai";
const FULL_CIRCLE_DEG = 360;
const SPOKE_STEP_DEG = 45;
const DEG_SYMBOL = "°";
const RING_COUNT = 5;
const MARKER_SIZE = 7;
const HEADER_HEIGHT = 64;
const FOOTER_HEIGHT = 56;
const CHART_MARGIN = 36;
const DOMAIN_PAD_FACTOR = 1.18;
const LABEL_RADIUS_FACTOR = 1.09;

// Columns: set these to your data's column names
const SERIES_NAME = "Antenna Type"; // role: group
const AZIMUTH = "Azimuth (°)"; // role: theta
const GAIN = "Normalized gain"; // role: r

// Data: replace this block with your own records
const ANGLE_STEP_DEG = 15;

const data: Array<Record<string, string | number>> = [];
for (let deg = 0; deg < FULL_CIRCLE_DEG; deg += ANGLE_STEP_DEG) {
  const rad = (deg * Math.PI) / 180;
  const omniVal =
    Math.round((0.78 + 0.05 * Math.cos(3 * rad) + 0.03 * Math.cos(7 * rad)) * 1000) / 1000;
  data.push({
    [SERIES_NAME]: "Omnidirectional dipole",
    [AZIMUTH]: deg,
    [GAIN]: omniVal,
  });
}
for (let deg = 0; deg < FULL_CIRCLE_DEG; deg += ANGLE_STEP_DEG) {
  const rad = (deg * Math.PI) / 180;
  const cosVal = Math.cos(rad);
  const mainLobe = Math.pow(Math.max(0, cosVal), 6);
  const backLobe = 0.18 * Math.pow(Math.max(0, -cosVal), 10);
  const yagiVal = Math.round(Math.min(1, 0.06 + 0.94 * mainLobe + backLobe) * 1000) / 1000;
  data.push({
    [SERIES_NAME]: "Directional Yagi",
    [AZIMUTH]: deg,
    [GAIN]: yagiVal,
  });
}

// Plot: reads only data and the constants above
const seriesNames: string[] = [];
for (const row of data) {
  const sName = String(row[SERIES_NAME]);
  if (!seriesNames.includes(sName)) seriesNames.push(sName);
}

const rawMaxGain = Math.max(...data.map((r) => Number(r[GAIN])));
const rawStep = rawMaxGain / RING_COUNT;
const stepMag = 10 ** Math.floor(Math.log10(rawStep));
const stepNorm = rawStep / stepMag;
const ringStep = (stepNorm <= 1 ? 1 : stepNorm <= 2 ? 2 : stepNorm <= 5 ? 5 : 10) * stepMag;
const ringDecimals = Math.max(0, -Math.floor(Math.log10(ringStep) + 1e-9));
const gainMax = ringStep * RING_COUNT;
const rings: number[] = [];
for (let k = 1; k <= RING_COUNT; k += 1) {
  rings.push(Number((k * ringStep).toFixed(ringDecimals)));
}

const degreeTicks: number[] = [];
for (let deg = 0; deg < FULL_CIRCLE_DEG; deg += SPOKE_STEP_DEG) {
  degreeTicks.push(deg);
}

const seriesGroups = seriesNames.map((name, idx) => {
  const groupRows = data
    .filter((r) => String(r[SERIES_NAME]) === name)
    .sort((a, b) => Number(a[AZIMUTH]) - Number(b[AZIMUTH]));
  const color = t.palette[idx];
  const points = groupRows.map((row) => {
    const deg = Number(row[AZIMUTH]);
    const gain = Number(row[GAIN]);
    const angle = ((deg - 90) * Math.PI) / 180;
    return {
      id: `${name}-${deg}`,
      deg,
      gain,
      angle,
      x: gain * Math.cos(angle),
      y: -gain * Math.sin(angle),
    };
  });
  return { label: name, color, points };
});

const domainLimit = gainMax * DOMAIN_PAD_FACTOR;
const labelRadiusVal = gainMax * LABEL_RADIUS_FACTOR;

const series = seriesGroups.map((group) => ({
  type: "scatter" as const,
  id: group.label,
  label: group.label,
  color: group.color,
  markerSize: MARKER_SIZE,
  data: group.points,
}));

function PolarLayer() {
  const xScale = useXScale();
  const yScale = useYScale();

  const cx = Number(xScale(0));
  const cy = Number(yScale(0));
  const midRingY = Number(yScale(rings[Math.floor(rings.length / 2)]));

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
          strokeWidth={level === gainMax ? 2 : 1}
          strokeOpacity={level === gainMax ? 1 : 0.65}
        />
      ))}

      {degreeTicks.map((deg) => {
        const angle = ((deg - 90) * Math.PI) / 180;
        const ox = Number(xScale(gainMax * Math.cos(angle)));
        const oy = Number(yScale(-gainMax * Math.sin(angle)));
        const lx = Number(xScale(labelRadiusVal * Math.cos(angle)));
        const ly = Number(yScale(-labelRadiusVal * Math.sin(angle)));
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        const anchor = cos > 0.3 ? "start" : cos < -0.3 ? "end" : "middle";
        const baseline = sin > 0.5 ? "hanging" : sin < -0.5 ? "auto" : "central";
        const isCardinal = deg % 90 === 0;
        return (
          <g key={`spoke-${deg}`}>
            <line x1={cx} y1={cy} x2={ox} y2={oy} stroke={t.grid} strokeWidth={1} />
            <text
              x={lx}
              y={ly}
              fill={isCardinal ? t.ink : t.inkSoft}
              fontSize={isCardinal ? 17 : 14}
              fontWeight={isCardinal ? 700 : 500}
              textAnchor={anchor}
              dominantBaseline={baseline}
            >
              {`${deg}${DEG_SYMBOL}`}
            </text>
          </g>
        );
      })}

      {seriesGroups.map((group) => {
        const polyPoints = group.points.map((p) => `${xScale(p.x)},${yScale(p.y)}`).join(" ");
        return (
          <polygon
            key={`poly-${group.label}`}
            points={polyPoints}
            fill="none"
            stroke={group.color}
            strokeWidth={3}
            strokeLinejoin="round"
          />
        );
      })}

      {rings.map((level) => {
        const ty = Number(yScale(level));
        const label = level.toFixed(ringDecimals);
        const pillWidth = label.length * 8.5 + 12;
        return (
          <g key={`tick-${level}`}>
            <rect x={cx + 8} y={ty - 11} width={pillWidth} height={22} rx={4} fill={t.pageBg} />
            <text
              x={cx + 14}
              y={ty}
              fill={t.inkSoft}
              fontSize={14}
              textAnchor="start"
              dominantBaseline="central"
            >
              {label}
            </text>
          </g>
        );
      })}

      <g transform={`translate(${cx + 58}, ${midRingY}) rotate(-90)`}>
        <rect x={-62} y={-11} width={124} height={22} rx={4} fill={t.pageBg} />
        <text
          x={0}
          y={0}
          fill={t.inkSoft}
          fontSize={14}
          fontWeight={600}
          textAnchor="middle"
          dominantBaseline="central"
        >
          {GAIN}
        </text>
      </g>
    </g>
  );
}

export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const chartSize = size.height - HEADER_HEIGHT - FOOTER_HEIGHT;

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
      <div
        style={{
          height: FOOTER_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 36,
        }}
      >
        {seriesGroups.map((group) => (
          <div
            key={`legend-${group.label}`}
            style={{ display: "flex", alignItems: "center", gap: 10 }}
          >
            <span
              style={{
                width: 18,
                height: 18,
                borderRadius: "50%",
                backgroundColor: group.color,
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: 15, color: t.ink, fontWeight: 500 }}>{group.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
