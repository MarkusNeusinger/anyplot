// anyplot.ai
// radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-26
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Strategic technology planning: emerging tech mapped by adoption horizon
// (ring, inner→outer) across four thematic sectors (angular wedge).
const RINGS = [
  { key: "now", label: "Now (0–6 mo)" },
  { key: "near", label: "Near-Term (6–18 mo)" },
  { key: "mid", label: "Mid-Term (18–36 mo)" },
  { key: "future", label: "Future (3+ yr)" },
];

const SECTORS = [
  { key: "ai", label: "AI & ML" },
  { key: "cloud", label: "Cloud Infra" },
  { key: "security", label: "Security" },
  { key: "sustain", label: "Green Tech" },
];

// Exactly one item per (ring, sector) cell — every marker gets its own ray,
// so radial labels never compete with a same-cell sibling for space.
const ITEMS = [
  { name: "LLM Fine-Tuning", ring: 0, sector: 0 },
  { name: "Multimodal Agents", ring: 1, sector: 0 },
  { name: "On-Device Inference", ring: 2, sector: 0 },
  { name: "Neuromorphic Chips", ring: 3, sector: 0 },
  { name: "Serverless Functions", ring: 0, sector: 1 },
  { name: "Edge Computing", ring: 1, sector: 1 },
  { name: "WebAssembly Runtimes", ring: 2, sector: 1 },
  { name: "Quantum-Safe Networking", ring: 3, sector: 1 },
  { name: "Zero Trust Access", ring: 0, sector: 2 },
  { name: "Passwordless Auth", ring: 1, sector: 2 },
  { name: "Post-Quantum Crypto", ring: 2, sector: 2 },
  { name: "Homomorphic Encryption", ring: 3, sector: 2 },
  { name: "Carbon-Aware Scheduling", ring: 0, sector: 3 },
  { name: "Green Data Centers", ring: 1, sector: 3 },
  { name: "Circular Hardware", ring: 2, sector: 3 },
  { name: "Direct Air Capture", ring: 3, sector: 3 },
];

// --- Geometry (half-circle: rings sweep 180°→0°, sectors divide the arc) ----
// The data domain is asymmetric (tight below the baseline, generous above it)
// so the square-ish drawing area is spent on the semicircle + its legends
// instead of blank space — width/height below are derived from these lengths.
const R_MAX = 100;
const RING_BOUNDS = [0, 25, 50, 75, 100];
const SECTOR_SPAN = 180 / SECTORS.length;
// Outward reach of each item's label, per ring — smaller on the outer ring so
// it doesn't crowd the sector header just beyond R_MAX.
const LABEL_OFFSET = [14, 14, 13, 9];
const X_HALF = 142;
const Y_TOP = 136;
const Y_BOTTOM = -80;

const POINTS = ITEMS.map((item) => {
  const sectorStart = 180 - item.sector * SECTOR_SPAN;
  const angle = sectorStart - SECTOR_SPAN / 2; // dead center of the sector wedge
  const radius = (RING_BOUNDS[item.ring] + RING_BOUNDS[item.ring + 1]) / 2;
  return { ...item, angle, radius, labelOffset: LABEL_OFFSET[item.ring] };
});

// --- Radar diagram (custom marks composed on the MUI X cartesian scales) ----
function RadarDiagram() {
  const xScale = useXScale();
  const yScale = useYScale();

  const toPx = (radius, angleDeg) => {
    const rad = (angleDeg * Math.PI) / 180;
    return [xScale(radius * Math.cos(rad)), yScale(radius * Math.sin(rad))];
  };
  const arcPoints = (radius, steps = 48) =>
    Array.from({ length: steps + 1 }, (_, i) => toPx(radius, 180 - (180 * i) / steps));
  const toPath = (pts) => pts.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x},${y}`).join(" ");

  const dividerAngles = Array.from({ length: SECTORS.length + 1 }, (_, i) => 180 - i * SECTOR_SPAN);

  return (
    <g>
      {/* Subtle alternating fill per ring — separates the time horizons */}
      {RINGS.map((ring, i) => {
        const rInner = RING_BOUNDS[i];
        const rOuter = RING_BOUNDS[i + 1];
        const outerArc = arcPoints(rOuter);
        const innerArc = rInner === 0 ? [toPx(0, 90)] : arcPoints(rInner).reverse();
        const d = `${toPath(outerArc)} L${innerArc.map(([x, y]) => `${x},${y}`).join(" L")} Z`;
        return <path key={ring.key} d={d} fill={t.ink} opacity={i % 2 === 0 ? 0.035 : 0.07} stroke="none" />;
      })}

      {/* Ring boundary lines (outer ring gets a bolder frame) */}
      {RING_BOUNDS.slice(1).map((r, i) => (
        <path
          key={`ring-line-${r}`}
          d={toPath(arcPoints(r))}
          fill="none"
          stroke={i === RING_BOUNDS.length - 2 ? t.inkSoft : t.grid}
          strokeWidth={i === RING_BOUNDS.length - 2 ? 2.5 : 1.5}
        />
      ))}

      {/* Baseline diameter */}
      <path d={toPath([toPx(R_MAX, 180), toPx(R_MAX, 0)])} stroke={t.inkSoft} strokeWidth={2.5} />

      {/* Sector divider spokes */}
      {dividerAngles.map((angle) => (
        <path key={`div-${angle}`} d={toPath([toPx(0, angle), toPx(R_MAX, angle)])} stroke={t.grid} strokeWidth={1.5} />
      ))}

      {/* Ring name row, just below the baseline — kept clear of the data area */}
      {RINGS.map((ring, i) => {
        const rowHalf = X_HALF * 0.8;
        const slot = (2 * rowHalf) / RINGS.length;
        const x = xScale(-rowHalf + slot * (i + 0.5));
        const y = yScale(-16);
        return (
          <text key={`ring-label-${ring.key}`} x={x} y={y} fontSize={13} fontWeight={600} fill={t.inkSoft} textAnchor="middle" dominantBaseline="middle">
            {ring.label}
          </text>
        );
      })}

      {/* Sector headers along the outer edge */}
      {SECTORS.map((sector, i) => {
        const sectorStart = 180 - i * SECTOR_SPAN;
        const mid = sectorStart - SECTOR_SPAN / 2;
        const [x, y] = toPx(R_MAX + 24, mid);
        const cos = Math.cos((mid * Math.PI) / 180);
        const anchor = cos > 0.25 ? "start" : cos < -0.25 ? "end" : "middle";
        return (
          <text key={`sector-label-${sector.key}`} x={x} y={y} fontSize={16} fontWeight={700} fill={t.ink} textAnchor={anchor} dominantBaseline="middle">
            {sector.label}
          </text>
        );
      })}

      {/* Sector color legend, laid out below the ring row */}
      <text x={xScale(0)} y={yScale(-42)} fontSize={14} fontWeight={600} fill={t.inkSoft} textAnchor="middle">
        Sector
      </text>
      {SECTORS.map((sector, i) => {
        const slot = (2 * X_HALF) / SECTORS.length;
        const cx = xScale(-X_HALF + slot * (i + 0.5));
        const cy = yScale(-68);
        return (
          <g key={`legend-${sector.key}`}>
            <circle cx={cx - 48} cy={cy} r={8} fill={t.palette[i]} stroke={t.pageBg} strokeWidth={2} />
            <text x={cx - 34} y={cy} fontSize={14} fill={t.ink} textAnchor="start" dominantBaseline="middle">
              {sector.label}
            </text>
          </g>
        );
      })}

      {/* Items — marker + outward radial label, colored by sector */}
      {POINTS.map((p) => {
        const [mx, my] = toPx(p.radius, p.angle);
        const [lx, ly] = toPx(p.radius + p.labelOffset, p.angle);
        const cos = Math.cos((p.angle * Math.PI) / 180);
        const anchor = cos > 0.2 ? "start" : cos < -0.2 ? "end" : "middle";
        return (
          <g key={p.name}>
            <circle cx={mx} cy={my} r={9} fill={t.palette[p.sector]} stroke={t.pageBg} strokeWidth={2.2} />
            <text x={lx} y={ly} fontSize={13} fill={t.ink} textAnchor={anchor} dominantBaseline="middle">
              {p.name}
            </text>
          </g>
        );
      })}
    </g>
  );
}

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const titleHeight = 64;
  // Derive the drawing area's aspect ratio from the data domain so the
  // semicircle renders as true circular arcs (equal px-per-unit on both axes)
  // without wasting canvas on a forced square container.
  const xDomainLen = 2 * X_HALF;
  const yDomainLen = Y_TOP - Y_BOTTOM;
  const chartHeight = size.height - titleHeight - 20;
  const chartWidth = Math.min(size.width - 40, chartHeight * (xDomainLen / yDomainLen));

  return (
    <Box sx={{ width: size.width, height: size.height, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
      <Box sx={{ height: titleHeight, display: "flex", alignItems: "center" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          radar-innovation-timeline · javascript · muix · anyplot.ai
        </Typography>
      </Box>
      <ChartContainer
        width={chartWidth}
        height={chartHeight}
        series={[]}
        xAxis={[{ min: -X_HALF, max: X_HALF, scaleType: "linear", domainLimit: "strict" }]}
        yAxis={[{ min: Y_BOTTOM, max: Y_TOP, scaleType: "linear", domainLimit: "strict" }]}
        margin={{ top: 10, bottom: 10, left: 10, right: 10 }}
        skipAnimation
      >
        <RadarDiagram />
      </ChartContainer>
    </Box>
  );
}
