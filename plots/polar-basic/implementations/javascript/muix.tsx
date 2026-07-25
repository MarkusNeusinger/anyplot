// anyplot.ai
// polar-basic: Basic Polar Chart
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 89/100 | Updated: 2026-07-25
//# anyplot-orientation: square
// anyplot.ai
// polar-basic: Basic Polar Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-07-24
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

// @mui/x-charts 7.x community has no polar/radial chart component (a PolarProvider
// exists internally but isn't part of the public export surface), so the polar
// plot is composed on MUI X's own charting surface: ChartContainer sizes the
// <svg> + theme, and useDrawingArea() gives the plot rect the polar geometry is
// mapped onto. Every ring, spoke and data point below is computed from real
// values — nothing is faked chrome.

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// Theme-adaptive chrome (ThemeProvider handles MUI text; these are for our SVG).
const INK = t.ink;
const INK_SOFT = t.inkSoft;
const GRID = t.grid;
const PAGE_BG = t.pageBg;
const BRAND = t.palette[0]; // Imprint palette position 1 — always first series

// --- Data (in-memory, deterministic) -------------------------------------------
// Smart-home electricity draw across a 24h cycle: a commuter-hours morning peak
// and a larger evening peak, low overnight — the cyclical pattern polar coords
// are meant to reveal, invisible as a simple bump in a cartesian line chart.
const HOURS = 24;
const kwh = [
  1.2, 1.0, 0.9, 0.8, 0.9, 1.3, 2.1, 3.4, 3.8, 2.9, 2.2, 2.0, 2.3, 2.1, 2.0, 2.2,
  2.6, 3.5, 4.6, 4.9, 4.2, 3.1, 2.0, 1.5,
];
const MAX_KWH = 5;
const RINGS = [1, 2, 3, 4, 5];
const LABELED_HOURS = [0, 6, 12, 18];
const HOUR_LABELS = { 0: "12 AM", 6: "6 AM", 12: "12 PM", 18: "6 PM" };

// Hour 0 points to the top (-90°); angle grows clockwise as the day progresses.
const angleOf = (hour) => (-90 + (hour / HOURS) * 360) * (Math.PI / 180);

// --- Polar layer: rendered as children inside MUI X's ChartsSurface ------------
function PolarLayer() {
  const area = useDrawingArea();
  const cx = area.left + area.width / 2;
  const cy = area.top + area.height / 2;
  const half = Math.min(area.width, area.height) / 2;
  const R = half - 60; // data radius; margin between R and half holds labels
  const labelR = half - 6;

  const point = (frac, hour) => {
    const a = angleOf(hour);
    return [cx + frac * R * Math.cos(a), cy + frac * R * Math.sin(a)];
  };

  const linePoints = kwh
    .map((v, hour) => point(v / MAX_KWH, hour).join(","))
    .join(" ");

  return (
    <g>
      {/* Concentric radius gridlines, one per kWh ring — outer ring solid,
          inner rings lighter so the nested grid stays subtle near the center */}
      {RINGS.map((level) => (
        <circle
          key={`ring-${level}`}
          cx={cx}
          cy={cy}
          r={(level / MAX_KWH) * R}
          fill="none"
          stroke={GRID}
          strokeWidth={level === MAX_KWH ? 2 : 1}
          strokeOpacity={level === MAX_KWH ? 1 : 0.6}
        />
      ))}

      {/* Angular spokes + labels at the four standard clock positions */}
      {LABELED_HOURS.map((hour) => {
        const [ox, oy] = point(1, hour);
        const a = angleOf(hour);
        const lx = cx + labelR * Math.cos(a);
        const ly = cy + labelR * Math.sin(a);
        const cos = Math.cos(a);
        const anchor = cos > 0.3 ? "start" : cos < -0.3 ? "end" : "middle";
        const sin = Math.sin(a);
        const baseline = sin > 0.5 ? "hanging" : sin < -0.5 ? "auto" : "central";
        return (
          <g key={`spoke-${hour}`}>
            <line x1={cx} y1={cy} x2={ox} y2={oy} stroke={GRID} strokeWidth={1.25} />
            <text
              x={lx}
              y={ly}
              fill={INK}
              fontSize={18}
              fontWeight={600}
              textAnchor={anchor}
              dominantBaseline={baseline}
            >
              {HOUR_LABELS[hour]}
            </text>
          </g>
        );
      })}

      {/* Closed polygon: translucent fill + solid outline + hourly markers */}
      <polygon
        points={linePoints}
        fill={BRAND}
        fillOpacity={0.22}
        stroke={BRAND}
        strokeWidth={3}
        strokeLinejoin="round"
      />
      {kwh.map((v, hour) => {
        const [px, py] = point(v / MAX_KWH, hour);
        return (
          <circle
            key={`pt-${hour}`}
            cx={px}
            cy={py}
            r={5}
            fill={BRAND}
            stroke={PAGE_BG}
            strokeWidth={1.5}
          />
        );
      })}

      {/* Radius (kWh) tick labels, offset off the top spoke, drawn LAST so they
          sit above the data polygon. Theta is continuous here (unlike a radar
          chart's fixed high-value axis), so the polygon crosses this spoke too
          at low-value hours — each label gets an opaque backing chip to stay
          legible regardless of what's underneath. */}
      {RINGS.map((level) => {
        const ty = cy - (level / MAX_KWH) * R;
        return (
          <g key={`tick-${level}`}>
            <rect x={cx + 6} y={ty - 11} width={62} height={22} rx={4} fill={PAGE_BG} />
            <text
              x={cx + 12}
              y={ty}
              fill={INK_SOFT}
              fontSize={15}
              textAnchor="start"
              dominantBaseline="central"
            >
              {`${level} kWh`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

// --- Title drawn on the surface, then the polar layer ---------------------------
function Chrome() {
  return (
    <text
      x={size.width / 2}
      y={52}
      fill={INK}
      fontSize={28}
      fontWeight={700}
      textAnchor="middle"
    >
      polar-basic · javascript · muix · anyplot.ai
    </text>
  );
}

// --- Chart (default-exported component — the harness mounts it) ----------------
export default function Chart() {
  return (
    <ChartContainer
      width={size.width}
      height={size.height}
      series={[]}
      margin={{ top: 84, bottom: 84, left: 96, right: 96 }}
      skipAnimation
    >
      <Chrome />
      <PolarLayer />
    </ChartContainer>
  );
}
