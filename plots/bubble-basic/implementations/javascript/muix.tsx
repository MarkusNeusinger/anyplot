// anyplot.ai
// bubble-basic: Basic Bubble Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Updated: 2026-09-27
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const TITLE = "bubble-basic · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;
const MARGIN = { top: 24, right: 210, bottom: 70, left: 90 };
// Semi-transparent fill composites differently over the two page backgrounds:
// the same alpha reads visibly darker/more saturated over #1A1A17 than over
// #FAF8F1, even though the underlying Imprint hex values never change. A
// small theme-aware opacity bump keeps the perceived hue closer across themes.
const BUBBLE_OPACITY = window.ANYPLOT_THEME === "dark" ? 0.6 : 0.48;

// --- Data (in-memory, deterministic LCG — no seeded RNG in the browser) -----
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}

function randomNormal(rand, mean, stdDev) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * stdDev;
}

// Three loose company archetypes — fast-growing leaders, steady mid-market
// challengers, and small niche players — so the cloud has real structure
// instead of a formless blob. Each archetype gets its own hue so the
// pattern reads immediately instead of hiding in a single-color cloud.
// Abstract group labels (no semantic color cue), so Imprint positions are
// used in canonical order 1->3, not cherry-picked.
// The community package has no bubble/z-size scatter mode (ZAxisConfig
// only maps z to colour), so bubbles are drawn as a custom SVG layer
// positioned via the chart's own scale hooks.
// "Growth leaders" gets a wider (xSpread, ySpread) than the other two
// archetypes — the previous review flagged that its 15 bubbles packed so
// tightly around x=20-22, y=17-21 that individual boundaries were hard to
// distinguish even with the pageBg stroke separation.
const ARCHETYPES = [
  { name: "Growth leaders", growth: 24, margin: 19, share: 62, count: 15, xSpread: 9, ySpread: 7.5, color: t.palette[0] },
  { name: "Mid-market", growth: 12, margin: 10, share: 34, count: 20, xSpread: 7, ySpread: 6, color: t.palette[1] },
  { name: "Niche players", growth: 4, margin: 3, share: 14, count: 15, xSpread: 7, ySpread: 6, color: t.palette[2] },
];

const rand = lcg(42);

const companies = ARCHETYPES.flatMap((a, groupIndex) =>
  Array.from({ length: a.count }, (_, i) => ({
    id: `${groupIndex}-${i}`,
    x: Math.round(randomNormal(rand, a.growth, a.xSpread) * 10) / 10,
    y: Math.round(randomNormal(rand, a.margin, a.ySpread) * 10) / 10,
    size: Math.min(100, Math.max(10, Math.round(randomNormal(rand, a.share, 18)))),
    color: a.color,
  })),
);

const sizeValues = companies.map((d) => d.size);
const sizeMin = Math.min(...sizeValues);
const sizeMax = Math.max(...sizeValues);

// Scale bubbles by AREA, not radius — otherwise size differences read as
// far more extreme than the underlying data actually is. Capped tighter
// than the raw 10-100 domain would suggest so the densest cluster
// (growth ~20-30%, margin ~15-25%) stays legible instead of fusing together.
const MIN_RADIUS = 7;
const MAX_RADIUS = 38;
function radiusForSize(value) {
  const ratio = (value - sizeMin) / (sizeMax - sizeMin);
  return MIN_RADIUS + (MAX_RADIUS - MIN_RADIUS) * Math.sqrt(Math.max(0, ratio));
}

// Legend geometry, computed once so the two legend blocks can be vertically
// centered against the chart instead of pinned at fixed heights that leave a
// visible gap of unused whitespace beneath them on tall canvases.
const LEGEND_GAP = 56;
const SIZE_LEGEND_VALUES = [
  Math.round(sizeMax / 10) * 10,
  Math.round((sizeMin + sizeMax) / 2 / 10) * 10,
  Math.round(sizeMin / 10) * 10,
];
const COLOR_LEGEND_HEIGHT = 20 + (ARCHETYPES.length - 1) * 24 + 12;
const SIZE_LEGEND_HEIGHT =
  20 + SIZE_LEGEND_VALUES.reduce((height, value) => height + radiusForSize(value) * 2 + 16, 0);

// Declutter pass: per-archetype spread tuning (see above) can't fully
// prevent a chance pocket where several bubbles from different archetypes
// land on top of each other. x and y need different px-per-unit factors
// since the axes don't share a domain width, so distances are computed in
// approximate pixel space — mirroring ChartContainer's linear min/max
// mapping, since the real xScale/yScale hooks aren't available until the
// chart mounts — and converted back to data units. The scale used here is
// only an approximation (built from the pre-repulsion spread); the real
// axis domain is recomputed below from the settled positions, so a bubble
// can never end up padded outside its own axis range. Bubbles closer than
// 92% of their summed radii are pushed apart — tight enough to still read
// as an organic cloud, strong enough that no two bubbles fuse into an
// undifferentiated blob.
const rawXValues = companies.map((d) => d.x);
const rawYValues = companies.map((d) => d.y);
const rawXDomain = [Math.min(...rawXValues) - 4, Math.max(...rawXValues) + 4];
const rawYDomain = [Math.min(...rawYValues) - 4, Math.max(...rawYValues) + 4];
const { width: CANVAS_WIDTH, height: CANVAS_HEIGHT } = window.ANYPLOT_SIZE;
const PLOT_WIDTH = CANVAS_WIDTH - MARGIN.left - MARGIN.right;
const PLOT_HEIGHT = CANVAS_HEIGHT - TITLE_HEIGHT - MARGIN.top - MARGIN.bottom;
const PX_PER_X = PLOT_WIDTH / (rawXDomain[1] - rawXDomain[0]);
const PX_PER_Y = PLOT_HEIGHT / (rawYDomain[1] - rawYDomain[0]);

for (let iter = 0; iter < 40; iter++) {
  for (let i = 0; i < companies.length; i++) {
    for (let j = i + 1; j < companies.length; j++) {
      const a = companies[i];
      const b = companies[j];
      const dxPx = (b.x - a.x) * PX_PER_X;
      const dyPx = (b.y - a.y) * PX_PER_Y;
      const dist = Math.hypot(dxPx, dyPx) || 0.001;
      const minDist = (radiusForSize(a.size) + radiusForSize(b.size)) * 0.92;
      if (dist < minDist) {
        const push = (minDist - dist) / 2;
        const ux = dxPx / dist;
        const uy = dyPx / dist;
        a.x -= (ux * push) / PX_PER_X;
        a.y -= (uy * push) / PX_PER_Y;
        b.x += (ux * push) / PX_PER_X;
        b.y += (uy * push) / PX_PER_Y;
      }
    }
  }
}
companies.forEach((d) => {
  d.x = Math.round(d.x * 10) / 10;
  d.y = Math.round(d.y * 10) / 10;
});

const xValues = companies.map((d) => d.x);
const yValues = companies.map((d) => d.y);
const xDomain = [Math.min(...xValues) - 4, Math.max(...xValues) + 4];
const yDomain = [Math.min(...yValues) - 4, Math.max(...yValues) + 4];

// --- Bubbles (reads the chart's live x/y scales via context hooks) ---------
function Bubbles() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {companies.map((d) => (
        <circle
          key={d.id}
          cx={xScale(d.x)}
          cy={yScale(d.y)}
          r={radiusForSize(d.size)}
          fill={d.color}
          fillOpacity={BUBBLE_OPACITY}
          stroke={t.pageBg}
          strokeWidth={2}
        />
      ))}
    </g>
  );
}

// --- Color legend — names the three archetypes so the clustering reads as
// an insight instead of something the viewer has to discover unaided -------
function ColorLegend({ left, top }) {
  return (
    <g>
      <text x={left} y={top - 20} fontSize={14} fontWeight={600} fill={t.inkSoft}>
        Company archetype
      </text>
      {ARCHETYPES.map((a, i) => {
        const cy = top + i * 24;
        return (
          <g key={a.name}>
            <circle cx={left + 6} cy={cy} r={6} fill={a.color} fillOpacity={BUBBLE_OPACITY} stroke={a.color} strokeWidth={1.5} />
            <text x={left + 20} y={cy} dominantBaseline="middle" fontSize={14} fill={t.inkSoft}>
              {a.name}
            </text>
          </g>
        );
      })}
    </g>
  );
}

// --- Size legend — three reference bubbles explain the size scaling --------
function SizeLegend({ left, top }) {
  let cursorY = top;

  return (
    <g>
      <text x={left} y={top - 20} fontSize={14} fontWeight={600} fill={t.inkSoft}>
        Market share index
      </text>
      {SIZE_LEGEND_VALUES.map((value) => {
        const r = radiusForSize(value);
        cursorY += r + 10;
        const cy = cursorY;
        cursorY += r + 16;
        return (
          <g key={value}>
            <circle
              cx={left + MAX_RADIUS}
              cy={cy}
              r={r}
              fill="none"
              stroke={t.inkSoft}
              strokeWidth={1.5}
            />
            <text
              x={left + MAX_RADIUS * 2 + 14}
              y={cy}
              dominantBaseline="middle"
              fontSize={14}
              fill={t.inkSoft}
            >
              {value}
            </text>
          </g>
        );
      })}
    </g>
  );
}

// --- Chart (default-exported component — the harness mounts it) -----------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - TITLE_HEIGHT;
  const margin = MARGIN;

  // Center the two-part legend against the chart height instead of pinning
  // it near the top, so it no longer leaves a tall unused gap underneath.
  const legendBlockHeight = COLOR_LEGEND_HEIGHT + LEGEND_GAP + SIZE_LEGEND_HEIGHT;
  const legendBlockTop = Math.max(44, (chartHeight - legendBlockHeight) / 2);
  const colorLegendTop = legendBlockTop + 20;
  const sizeLegendTop = legendBlockTop + COLOR_LEGEND_HEIGHT + LEGEND_GAP + 20;

  return (
    <div style={{ width, height }}>
      <div
        style={{
          height: TITLE_HEIGHT,
          lineHeight: `${TITLE_HEIGHT}px`,
          paddingLeft: 24,
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartContainer
        width={width}
        height={chartHeight}
        series={[]}
        skipAnimation
        margin={margin}
        xAxis={[
          {
            id: "growth",
            min: xDomain[0],
            max: xDomain[1],
            label: "Revenue growth rate (%)",
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
          },
        ]}
        yAxis={[
          {
            id: "margin",
            min: yDomain[0],
            max: yDomain[1],
            label: "Profit margin (%)",
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
          },
        ]}
      >
        <ChartsGrid horizontal />
        <Bubbles />
        <ChartsXAxis axisId="growth" />
        <ChartsYAxis axisId="margin" />
        <ColorLegend left={width - margin.right + 24} top={colorLegendTop} />
        <SizeLegend left={width - margin.right + 24} top={sizeLegendTop} />
      </ChartContainer>
    </div>
  );
}
