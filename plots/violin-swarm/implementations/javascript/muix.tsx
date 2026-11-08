// anyplot.ai
// violin-swarm: Violin Plot with Overlaid Swarm Points
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const GRID_N = 140; // KDE evaluation points per violin
const TAIL_BANDWIDTHS = 2; // each violin ends this many bandwidths past its outermost value
const Y_PAD = 0.04; // share of the violins' value range added above and below them
const VIOLIN_SPAN = 0.8; // share of a category band the widest violin fills
const MARKER_R = 5; // swarm point radius, px
const PEAK_MIN_HEIGHT = 0.25; // a density peak below this share of the violin's maximum is noise
const PEAK_MIN_SEPARATION = 2; // two peaks closer than this many bandwidths are one mode
const PEAK_VALLEY_RATIO = 0.85; // a valley above this share of the lower peak does not split two modes
const TITLE = "violin-swarm · javascript · muix · anyplot.ai";
const TITLE_H = 80;

// Columns: set these to your data's column names
const CONDITION = "Condition"; // role: category
const REACTION_TIME = "Reaction time (ms)"; // role: value

// Data: replace this block with your own records, one object per row
// Reaction times across four experimental conditions, 50 trials each. Each
// condition has its own shape: sleep deprivation adds a cluster of attention
// lapses (a second mode), and the dual task skews into a long slow tail.
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
  const normal = (mean, sd) =>
    mean + sd * Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
  const clamp = (v) => Math.min(650, Math.max(300, v));
  const conditions = [
    ["Baseline", () => clamp(normal(420, 35))],
    ["Caffeine", () => clamp(normal(360, 28))],
    ["Sleep-deprived", () => clamp(rand() < 0.75 ? normal(470, 30) : normal(590, 25))],
    ["Dual-task", () => clamp(430 + 140 * Math.pow(rand(), 2.2) + 8 * normal(0, 1))],
  ];
  return conditions.flatMap(([name, sample]) =>
    Array.from({ length: 50 }, () => ({ [CONDITION]: name, [REACTION_TIME]: Math.round(sample() * 10) / 10 })),
  );
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[REACTION_TIME] != null);
const categories = [...new Set(rows.map((d) => d[CONDITION]))];

// Per category: sorted values, median and a Gaussian KDE (Silverman bandwidth)
// normalized to its own peak, so width encodes shape rather than sample count.
// The grid ends a few bandwidths past the data, so each violin tapers near its
// own range. Density modes are the local maxima that survive a valley test.
const violins = categories.map((cat) => {
  const values = rows
    .filter((d) => d[CONDITION] === cat)
    .map((d) => d[REACTION_TIME])
    .sort((a, b) => a - b);
  const n = values.length;
  const median = n % 2 === 0 ? (values[n / 2 - 1] + values[n / 2]) / 2 : values[(n - 1) / 2];
  const mean = values.reduce((a, b) => a + b, 0) / n;
  const sd = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(1, n - 1));
  const bandwidth = Math.max(0.9 * sd * Math.pow(n, -0.2), 1e-6);
  const lo = values[0] - TAIL_BANDWIDTHS * bandwidth;
  const hi = values[n - 1] + TAIL_BANDWIDTHS * bandwidth;
  const grid = Array.from({ length: GRID_N }, (_, k) => lo + (k * (hi - lo)) / (GRID_N - 1));
  const raw = grid.map((gy) => values.reduce((sum, v) => sum + Math.exp(-0.5 * ((gy - v) / bandwidth) ** 2), 0));
  const peak = Math.max(...raw);
  const density = raw.map((v) => v / peak);
  const valueDensity = values.map(
    (y) => values.reduce((sum, v) => sum + Math.exp(-0.5 * ((y - v) / bandwidth) ** 2), 0) / peak,
  );
  const medianDensity = values.reduce((sum, v) => sum + Math.exp(-0.5 * ((median - v) / bandwidth) ** 2), 0) / peak;

  const modes = [];
  for (let k = 1; k < GRID_N - 1; k += 1) {
    if (density[k] < PEAK_MIN_HEIGHT || density[k] < density[k - 1] || density[k] < density[k + 1]) continue;
    const close = modes.find((m) => Math.abs(m.value - grid[k]) < PEAK_MIN_SEPARATION * bandwidth);
    if (!close) modes.push({ idx: k, value: grid[k], height: density[k] });
    else if (density[k] > close.height) Object.assign(close, { idx: k, value: grid[k], height: density[k] });
  }
  modes.sort((a, b) => a.idx - b.idx);
  let merged = true;
  while (merged && modes.length > 1) {
    merged = false;
    for (let i = 0; i < modes.length - 1 && !merged; i += 1) {
      const valley = Math.min(...density.slice(modes[i].idx, modes[i + 1].idx + 1));
      if (valley / Math.min(modes[i].height, modes[i + 1].height) > PEAK_VALLEY_RATIO) {
        modes.splice(modes[i].height >= modes[i + 1].height ? i + 1 : i, 1);
        merged = true;
      }
    }
  }
  const minorMode = modes.length > 1 ? [...modes].sort((a, b) => a.height - b.height)[0] : null;

  return { values, valueDensity, median, medianDensity, grid, density, minorMode };
});
const gridMin = Math.min(...violins.map((v) => v.grid[0]));
const gridMax = Math.max(...violins.map((v) => v.grid[GRID_N - 1]));
const yMin = gridMin - (gridMax - gridMin) * Y_PAD;
const yMax = gridMax + (gridMax - gridMin) * Y_PAD;
const SUBTITLE = `${rows.length} observations in ${categories.length} groups · bar: median${violins.some((v) => v.minorMode) ? " · dashed leader: second density mode" : ""}`;

// The community package has no violin or swarm component: a custom layer
// draws both through the chart's band and linear scales.
function ViolinSwarm() {
  const xScale = useXScale();
  const yScale = useYScale();
  const band = xScale.bandwidth();
  const halfWidth = (band * VIOLIN_SPAN) / 2;
  const diameter = MARKER_R * 2 + 1.5;
  const step = diameter * 0.92;

  return (
    <g>
      {categories.map((cat, i) => {
        const v = violins[i];
        const color = t.palette[i];
        const center = xScale(cat) + band / 2;
        const leftSide = v.grid.map((gy, k) => `${center - v.density[k] * halfWidth},${yScale(gy)}`);
        const rightSide = v.grid.map((gy, k) => `${center + v.density[k] * halfWidth},${yScale(gy)}`).reverse();
        const violinPath = `M${leftSide.join(" L")} L${rightSide.join(" L")} Z`;

        // Beeswarm: each point keeps its value and moves sideways only as far
        // as needed to clear the points placed near it, never past the violin's
        // own outline at that value.
        const swarm = [];
        v.values.forEach((value, j) => {
          const y = yScale(value);
          const maxOffset = Math.max(0, v.valueDensity[j] * halfWidth - MARKER_R);
          const nearby = swarm.filter((p) => Math.abs(y - p.y) < diameter);
          let offset = 0;
          for (let k = 0; k <= 2 * Math.floor(maxOffset / step); k += 1) {
            const candidate = (k % 2 === 1 ? 1 : -1) * Math.ceil(k / 2) * step;
            if (nearby.every((p) => Math.hypot(candidate - p.offset, y - p.y) >= diameter * 0.95)) {
              offset = candidate;
              break;
            }
          }
          swarm.push({ y, offset });
        });

        const medianHalf = v.medianDensity * halfWidth * 0.85;
        const modeY = v.minorMode ? yScale(v.minorMode.value) : 0;

        return (
          <g key={cat}>
            <path d={violinPath} fill={color} fillOpacity={0.38} stroke={color} strokeWidth={1.75} strokeLinejoin="round" />
            {swarm.map((p, k) => (
              <circle
                key={k}
                cx={center + p.offset}
                cy={p.y}
                r={MARKER_R}
                fill={t.ink}
                fillOpacity={0.85}
                stroke={t.pageBg}
                strokeWidth={0.75}
              />
            ))}
            <line
              x1={center - medianHalf}
              x2={center + medianHalf}
              y1={yScale(v.median)}
              y2={yScale(v.median)}
              stroke={t.pageBg}
              strokeWidth={3}
              strokeLinecap="round"
            />
            {v.minorMode && (
              <g>
                <line
                  x1={center + halfWidth * v.minorMode.height + 3}
                  x2={center + halfWidth + 16}
                  y1={modeY}
                  y2={modeY}
                  stroke={t.inkSoft}
                  strokeWidth={1.25}
                  strokeDasharray="3,3"
                />
                <text x={center + halfWidth + 20} y={modeY} dy="0.32em" fontSize={15} fill={t.inkSoft}>
                  second mode
                </text>
              </g>
            )}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "18px 36px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H}
        series={[]}
        skipAnimation
        margin={{ top: 16, right: 48, bottom: 12, left: 24 }}
        xAxis={[
          {
            id: "category",
            scaleType: "band",
            data: categories,
            disableTicks: true,
            height: 72,
            label: CONDITION,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "value",
            min: yMin,
            max: yMax,
            width: 84,
            label: REACTION_TIME,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <ChartsGrid horizontal />
        <ViolinSwarm />
        <ChartsXAxis axisId="category" />
        <ChartsYAxis axisId="value" />
      </ChartsContainer>
    </div>
  );
}
