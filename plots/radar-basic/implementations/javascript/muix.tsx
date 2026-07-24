// anyplot.ai
// radar-basic: Basic Radar Chart
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 89/100 | Created: 2026-07-24
//# anyplot-orientation: square
// anyplot.ai
// radar-basic: Basic Radar Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-07-24
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

// @mui/x-charts 7.x community has no RadarChart component (added in v8), so the
// radar is composed on MUI X's own charting surface: ChartContainer provides the
// sized <svg> + drawing area, and useDrawingArea() gives the plot rect we map the
// polar geometry onto. Everything is real data drawn to scale — no faked chrome.

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// Theme-adaptive chrome (ThemeProvider handles MUI text; these are for our SVG).
const INK = t.ink;
const INK_SOFT = t.inkSoft;
const GRID = t.grid;
const PAGE_BG = t.pageBg;

// --- Data (in-memory, deterministic) — basketball player scouting report ------
const axes = ["Speed", "Shooting", "Passing", "Defense", "Rebounding", "Stamina"];
const series = [
  { label: "Guard", color: t.palette[0], values: [90, 84, 92, 68, 52, 86] },
  { label: "Forward", color: t.palette[1], values: [70, 76, 62, 85, 90, 80] },
];
const MAX = 100;
const RINGS = [20, 40, 60, 80, 100];
const N = axes.length;

// Axis i points from the top (-90°) going clockwise; SVG y grows downward.
const angleOf = (i) => (-90 + (i * 360) / N) * (Math.PI / 180);

// --- Radar layer: rendered as children inside MUI X's ChartsSurface -----------
function RadarLayer() {
  const area = useDrawingArea();
  const cx = area.left + area.width / 2;
  const cy = area.top + area.height / 2;
  const half = Math.min(area.width, area.height) / 2;
  const R = half - 54; // data radius; the margin between R and half holds labels
  const labelR = half - 4;

  const point = (frac, i) => {
    const a = angleOf(i);
    return [cx + frac * R * Math.cos(a), cy + frac * R * Math.sin(a)];
  };
  const polygon = (frac) =>
    axes.map((_, i) => point(frac, i).join(",")).join(" ");

  return (
    <g>
      {/* Concentric grid rings at each value level */}
      {RINGS.map((level) => (
        <polygon
          key={`ring-${level}`}
          points={polygon(level / MAX)}
          fill="none"
          stroke={GRID}
          strokeWidth={level === MAX ? 2 : 1.25}
        />
      ))}

      {/* Radial spokes + outer axis labels */}
      {axes.map((label, i) => {
        const [ox, oy] = point(1, i);
        const a = angleOf(i);
        const lx = cx + labelR * Math.cos(a);
        const ly = cy + labelR * Math.sin(a);
        const cos = Math.cos(a);
        const anchor = cos > 0.15 ? "start" : cos < -0.15 ? "end" : "middle";
        const sin = Math.sin(a);
        const baseline = sin > 0.5 ? "hanging" : sin < -0.5 ? "auto" : "central";
        return (
          <g key={`axis-${label}`}>
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
              {label}
            </text>
          </g>
        );
      })}

      {/* Value tick labels along the top spoke */}
      {RINGS.map((level) => (
        <text
          key={`tick-${level}`}
          x={cx + 6}
          y={cy - (level / MAX) * R}
          fill={INK_SOFT}
          fontSize={13}
          textAnchor="start"
          dominantBaseline="central"
        >
          {level}
        </text>
      ))}

      {/* Series polygons: translucent fill + solid outline + vertex markers */}
      {series.map((s) => (
        <g key={`series-${s.label}`}>
          <polygon
            points={axes.map((_, i) => point(s.values[i] / MAX, i).join(",")).join(" ")}
            fill={s.color}
            fillOpacity={0.25}
            stroke={s.color}
            strokeWidth={3}
            strokeLinejoin="round"
          />
          {axes.map((_, i) => {
            const [px, py] = point(s.values[i] / MAX, i);
            return (
              <circle
                key={`pt-${s.label}-${i}`}
                cx={px}
                cy={py}
                r={6}
                fill={s.color}
                stroke={PAGE_BG}
                strokeWidth={2}
              />
            );
          })}
        </g>
      ))}
    </g>
  );
}

// --- Title + legend drawn on the surface, then the radar layer ----------------
function Chrome() {
  const legendGap = 240;
  const legendStart = size.width / 2 - ((series.length - 1) * legendGap) / 2;
  const legendY = size.height - 44;
  return (
    <g>
      <text
        x={size.width / 2}
        y={52}
        fill={INK}
        fontSize={28}
        fontWeight={700}
        textAnchor="middle"
      >
        radar-basic · javascript · muix · anyplot.ai
      </text>
      {series.map((s, i) => {
        const x = legendStart + i * legendGap;
        return (
          <g key={`legend-${s.label}`}>
            <rect x={x - 84} y={legendY - 13} width={26} height={26} rx={5} fill={s.color} />
            <text
              x={x - 50}
              y={legendY}
              fill={INK}
              fontSize={17}
              textAnchor="start"
              dominantBaseline="central"
            >
              {s.label}
            </text>
          </g>
        );
      })}
    </g>
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
      <RadarLayer />
    </ChartContainer>
  );
}
