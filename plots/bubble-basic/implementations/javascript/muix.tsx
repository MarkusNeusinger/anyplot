// anyplot.ai
// bubble-basic: Basic Bubble Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-08-24
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const TITLE = "bubble-basic · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;

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
// instead of a formless blob. The community package has no bubble/z-size
// scatter mode (ZAxisConfig only maps z to colour), so bubbles are drawn as
// a custom SVG layer positioned via the chart's own scale hooks.
const ARCHETYPES = [
  { growth: 24, margin: 19, share: 62, count: 15 },
  { growth: 12, margin: 10, share: 34, count: 20 },
  { growth: 4, margin: 3, share: 14, count: 15 },
];

const rand = lcg(42);

const companies = ARCHETYPES.flatMap((a, groupIndex) =>
  Array.from({ length: a.count }, (_, i) => ({
    id: `${groupIndex}-${i}`,
    x: Math.round(randomNormal(rand, a.growth, 7) * 10) / 10,
    y: Math.round(randomNormal(rand, a.margin, 6) * 10) / 10,
    size: Math.min(100, Math.max(10, Math.round(randomNormal(rand, a.share, 18)))),
  })),
);

const xValues = companies.map((d) => d.x);
const yValues = companies.map((d) => d.y);
const sizeValues = companies.map((d) => d.size);
const xDomain = [Math.min(...xValues) - 4, Math.max(...xValues) + 4];
const yDomain = [Math.min(...yValues) - 4, Math.max(...yValues) + 4];
const sizeMin = Math.min(...sizeValues);
const sizeMax = Math.max(...sizeValues);

// Scale bubbles by AREA, not radius — otherwise size differences read as
// far more extreme than the underlying data actually is.
const MIN_RADIUS = 7;
const MAX_RADIUS = 52;
function radiusForSize(value) {
  const ratio = (value - sizeMin) / (sizeMax - sizeMin);
  return MIN_RADIUS + (MAX_RADIUS - MIN_RADIUS) * Math.sqrt(Math.max(0, ratio));
}

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
          fill={t.palette[0]}
          fillOpacity={0.6}
          stroke={t.pageBg}
          strokeWidth={1}
        />
      ))}
    </g>
  );
}

// --- Size legend — three reference bubbles explain the size scaling --------
function SizeLegend({ left, top }) {
  const legendValues = [
    Math.round(sizeMax / 10) * 10,
    Math.round((sizeMin + sizeMax) / 2 / 10) * 10,
    Math.round(sizeMin / 10) * 10,
  ];
  let cursorY = top;

  return (
    <g>
      <text x={left} y={top - 20} fontSize={13} fontWeight={600} fill={t.inkSoft}>
        Market share index
      </text>
      {legendValues.map((value) => {
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
              fontSize={13}
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
  const margin = { top: 24, right: 210, bottom: 70, left: 90 };

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
        <ChartsGrid horizontal vertical />
        <Bubbles />
        <ChartsXAxis axisId="growth" />
        <ChartsYAxis axisId="margin" />
        <SizeLegend left={width - margin.right + 24} top={70} />
      </ChartContainer>
    </div>
  );
}
