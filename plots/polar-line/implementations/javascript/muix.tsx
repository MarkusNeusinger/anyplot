// anyplot.ai
// polar-line: Polar Line Plot
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;
const TITLE = "polar-line · javascript · muix · anyplot.ai";

// Constants
const SERIES_COL = "Antenna Type";
const AZIMUTH_COL = "Azimuth (°)";
const GAIN_COL = "Normalized gain";

const ANGLE_STEP_DEG = 15;
const FULL_CIRCLE_DEG = 360;
const SPOKE_STEP_DEG = 45;
const RING_COUNT = 5;
const MARKER_SIZE = 7;
const HEADER_HEIGHT = 64;
const FOOTER_HEIGHT = 56;
const CHART_MARGIN = 36;
const DOMAIN_PAD_FACTOR = 1.18;
const LABEL_RADIUS_FACTOR = 1.09;

// Data — simulated far-field antenna radiation patterns sampled every 15° of azimuth
const DATA = [];
for (let deg = 0; deg < FULL_CIRCLE_DEG; deg += ANGLE_STEP_DEG) {
  const rad = (deg * Math.PI) / 180;
  const omniVal = Math.round((0.78 + 0.05 * Math.cos(3 * rad) + 0.03 * Math.cos(7 * rad)) * 1000) / 1000;
  DATA.push({
    [SERIES_COL]: "Omnidirectional dipole",
    [AZIMUTH_COL]: deg,
    [GAIN_COL]: omniVal,
  });
}
for (let deg = 0; deg < FULL_CIRCLE_DEG; deg += ANGLE_STEP_DEG) {
  const rad = (deg * Math.PI) / 180;
  const cosVal = Math.cos(rad);
  const mainLobe = Math.pow(Math.max(0, cosVal), 6);
  const backLobe = 0.18 * Math.pow(Math.max(0, -cosVal), 10);
  const yagiVal = Math.round(Math.min(1, 0.06 + 0.94 * mainLobe + backLobe) * 1000) / 1000;
  DATA.push({
    [SERIES_COL]: "Directional Yagi",
    [AZIMUTH_COL]: deg,
    [GAIN_COL]: yagiVal,
  });
}

// Derive series names in order of first appearance and radial domain from DATA
const seriesNames = [];
for (const row of DATA) {
  const sName = String(row[SERIES_COL]);
  if (!seriesNames.includes(sName)) seriesNames.push(sName);
}

const rawMaxGain = Math.max(...DATA.map((r) => Number(r[GAIN_COL])), 0.1);
const gainMax = Math.ceil(rawMaxGain * 10) / 10;
const ringStep = gainMax / RING_COUNT;
const rings = [];
for (let k = 1; k <= RING_COUNT; k += 1) {
  rings.push(Math.round(k * ringStep * 100) / 100);
}

const degreeTicks = [];
for (let deg = 0; deg < FULL_CIRCLE_DEG; deg += SPOKE_STEP_DEG) {
  degreeTicks.push(deg);
}

const azUnitMatch = AZIMUTH_COL.match(/\(([^)]+)\)/);
const azUnit = azUnitMatch ? azUnitMatch[1] : "°";

// Group and sort rows by azimuth for each series (0° at top, clockwise)
const seriesGroups = seriesNames.map((name, idx) => {
  const groupRows = DATA.filter((r) => String(r[SERIES_COL]) === name).sort(
    (a, b) => Number(a[AZIMUTH_COL]) - Number(b[AZIMUTH_COL]),
  );
  const label = String(groupRows[0]?.[SERIES_COL] ?? name);
  const color = t.palette[idx];
  const points = groupRows.map((row) => {
    const deg = Number(row[AZIMUTH_COL]);
    const gain = Number(row[GAIN_COL]);
    const angle = ((deg - 90) * Math.PI) / 180;
    return {
      id: `${label}-${deg}`,
      deg,
      gain,
      angle,
      x: gain * Math.cos(angle),
      y: -gain * Math.sin(angle),
    };
  });
  return { label, color, points };
});

const domainLimit = gainMax * DOMAIN_PAD_FACTOR;
const labelRadiusVal = gainMax * LABEL_RADIUS_FACTOR;

const SERIES = seriesGroups.map((group) => ({
  type: "scatter",
  id: group.label,
  label: group.label,
  color: group.color,
  markerSize: MARKER_SIZE,
  data: group.points,
}));

function PolarLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  if (!xScale || !yScale) return null;

  const cx = xScale(0);
  const cy = yScale(0);
  const midRingY = yScale(rings[Math.floor(rings.length / 2)]);

  return (
    <g>
      {/* Concentric gain rings */}
      {rings.map((level) => (
        <circle
          key={`ring-${level}`}
          cx={cx}
          cy={cy}
          r={Math.abs(xScale(level) - cx)}
          fill="none"
          stroke={t.grid}
          strokeWidth={level === gainMax ? 2 : 1}
          strokeOpacity={level === gainMax ? 1 : 0.65}
        />
      ))}

      {/* Radial spokes at every 45° of azimuth */}
      {degreeTicks.map((deg) => {
        const angle = ((deg - 90) * Math.PI) / 180;
        const ox = xScale(gainMax * Math.cos(angle));
        const oy = yScale(-gainMax * Math.sin(angle));
        const lx = xScale(labelRadiusVal * Math.cos(angle));
        const ly = yScale(-labelRadiusVal * Math.sin(angle));
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
              {`${deg}${azUnit}`}
            </text>
          </g>
        );
      })}

      {/* Radiation-pattern closed loops */}
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

      {/* Gain tick labels along the top spoke with pageBg pill badges */}
      {rings.map((level) => {
        const ty = yScale(level);
        const label = level.toFixed(1);
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

      {/* Radial axis title alongside the gain ticks */}
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
          {GAIN_COL}
        </text>
      </g>
    </g>
  );
}

export default function Chart() {
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
        series={SERIES}
        xAxis={[{ scaleType: "linear", min: -domainLimit, max: domainLimit, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: -domainLimit, max: domainLimit, position: "none" }]}
        margin={{ top: CHART_MARGIN, bottom: CHART_MARGIN, left: CHART_MARGIN, right: CHART_MARGIN }}
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
