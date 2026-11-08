// anyplot.ai
// violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const GRID_N = 120; // KDE evaluation points per violin
const TAIL_BANDWIDTHS = 1.5; // the density falls below ~4 % of its peak this far past the data
const Y_PAD = 0.06; // share of the value range added below the data
const Y_HEADROOM = 0.12; // share of the value range added above the data, room for the callout
const GROUP_SPAN = 0.84; // share of a category band the violins of its groups fill
const MARKER_R = 4; // swarm point radius, px
const TITLE = "violin-grouped-swarm · javascript · muix · anyplot.ai";
const TITLE_H = 80;
const LEGEND_H = 40;

// Columns: set these to your data's column names
const TASK = "Task type"; // role: category
const LEVEL = "Agent level"; // role: group
const TIME = "Resolution time (s)"; // role: value

// Data: replace this block with your own records, one object per row
// Support-ticket resolution times, 40 tickets per task type and agent level.
// Junior agents run slower and more variably than seniors, except on code
// review, where both lean on the same checklist and the gap nearly closes.
const data = (() => {
  let state = 42 >>> 0;
  const rand = () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
  const gaussian = () => Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
  const cells = [
    ["Bug Triage", "Junior", 95, 24],
    ["Bug Triage", "Senior", 52, 12],
    ["Data Entry", "Junior", 60, 16],
    ["Data Entry", "Senior", 38, 9],
    ["Code Review", "Junior", 130, 22],
    ["Code Review", "Senior", 118, 20],
  ];
  return cells.flatMap(([task, level, mean, sd]) =>
    Array.from({ length: 40 }, () => ({
      [TASK]: task,
      [LEVEL]: level,
      [TIME]: Math.round(Math.min(220, Math.max(10, mean + sd * gaussian())) * 10) / 10,
    })),
  );
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[TIME] != null);
const categories = [...new Set(rows.map((d) => d[TASK]))];
const groups = [...new Set(rows.map((d) => d[LEVEL]))];

// Per category and group: sorted values, median and a Gaussian KDE (Silverman
// bandwidth) normalized to its own peak on a grid that ends a short way past
// the data, so each violin tapers just beyond its values. Empty cells stay null.
const cells = categories.map((cat) =>
  groups.map((group) => {
    const values = rows
      .filter((d) => d[TASK] === cat && d[LEVEL] === group)
      .map((d) => d[TIME])
      .sort((a, b) => a - b);
    const n = values.length;
    if (n === 0) return null;
    const median = n % 2 === 0 ? (values[n / 2 - 1] + values[n / 2]) / 2 : values[(n - 1) / 2];
    const mean = values.reduce((a, b) => a + b, 0) / n;
    const sd = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(1, n - 1));
    const bandwidth = Math.max(0.9 * sd * Math.pow(n, -0.2), 1e-6);
    const lo = values[0] - TAIL_BANDWIDTHS * bandwidth;
    const hi = values[n - 1] + TAIL_BANDWIDTHS * bandwidth;
    const grid = Array.from({ length: GRID_N }, (_, k) => lo + (k * (hi - lo)) / (GRID_N - 1));
    const raw = grid.map((gy) => values.reduce((sum, v) => sum + Math.exp(-0.5 * ((gy - v) / bandwidth) ** 2), 0));
    const peak = Math.max(...raw);
    return { values, median, grid, density: raw.map((v) => v / peak) };
  }),
);

const filled = cells.flat().filter((c) => c != null);
const gridMin = Math.min(...filled.map((c) => c.grid[0]));
const gridMax = Math.max(...filled.map((c) => c.grid[GRID_N - 1]));
const yMin = gridMin - (gridMax - gridMin) * Y_PAD;
const yMax = gridMax + (gridMax - gridMin) * Y_HEADROOM;

// Focal callout: the category whose group medians lie closest together
const UNIT = TIME.match(/\(([^)]+)\)\s*$/)?.[1] ?? "";
const medianSpread = cells.map((row) => {
  const medians = row.filter((c) => c != null).map((c) => c.median);
  return medians.length > 1 ? Math.max(...medians) - Math.min(...medians) : null;
});
const closestIndex = groups.length > 1
  ? medianSpread.reduce((best, s, i) => (s != null && (best < 0 || s < medianSpread[best]) ? i : best), -1)
  : -1;
const CALLOUT = closestIndex >= 0 ? `Closest medians: ${medianSpread[closestIndex].toFixed(1)} ${UNIT} apart` : null;
const SUBTITLE = `${rows.length} observations, ${categories.length} ${TASK.toLowerCase()}s × ${groups.length} ${LEVEL.toLowerCase()}s · line: median`;

// The community package has no violin or swarm component: a custom layer
// draws them through the chart's band and linear scales, the groups dodged
// side by side inside each category band.
function GroupedViolinSwarm() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { top } = useDrawingArea();
  const band = xScale.bandwidth();
  const slot = (band * GROUP_SPAN) / groups.length;
  const violinHalfWidth = slot * 0.44;
  const swarmHalfWidth = slot * 0.4;
  const diameter = MARKER_R * 2 + 1;
  const step = diameter * 0.92;
  const maxK = Math.max(1, Math.floor(swarmHalfWidth / step));

  return (
    <g>
      {categories.map((cat, ci) => {
        const start = xScale(cat) + (band * (1 - GROUP_SPAN)) / 2;
        const centersX = groups.map((_, gi) => start + slot * (gi + 0.5));
        const tops = cells[ci].filter((c) => c != null).map((c) => yScale(c.grid[GRID_N - 1]));
        return (
          <g key={cat}>
            {groups.map((group, gi) => {
              const cell = cells[ci][gi];
              if (cell == null) return null;
              const color = t.palette[gi];
              const cx = centersX[gi];
              const leftSide = cell.grid.map((gy, k) => `${cx - cell.density[k] * violinHalfWidth},${yScale(gy)}`);
              const rightSide = cell.grid.map((gy, k) => `${cx + cell.density[k] * violinHalfWidth},${yScale(gy)}`).reverse();
              const violinPath = `M${cx},${yScale(cell.grid[0])} L${leftSide.join(" L")} L${cx},${yScale(cell.grid[GRID_N - 1])} L${rightSide.join(" L")} Z`;

              // Beeswarm: each point keeps its value; it moves sideways only as
              // far as needed to clear the points already placed near it, or,
              // where the row is full, to the offset that overlaps them least.
              const swarm = [];
              cell.values.forEach((v) => {
                const y = yScale(v);
                const nearby = swarm.filter((p) => Math.abs(y - p.y) < diameter);
                let offset = null;
                let fallback = { offset: 0, gap: -Infinity };
                for (let k = 0; k <= 2 * maxK && offset == null; k += 1) {
                  const candidate = (k % 2 === 1 ? 1 : -1) * Math.ceil(k / 2) * step;
                  const gap = Math.min(Infinity, ...nearby.map((p) => Math.hypot(candidate - p.offset, y - p.y)));
                  if (gap >= diameter * 0.95) offset = candidate;
                  else if (gap > fallback.gap) fallback = { offset: candidate, gap };
                }
                swarm.push({ y, offset: offset ?? fallback.offset });
              });

              return (
                <g key={`${cat}-${group}`}>
                  <path d={violinPath} fill={color} fillOpacity={0.4} stroke={color} strokeWidth={1.75} strokeLinejoin="round" />
                  {swarm.map((p, i) => (
                    <circle key={i} cx={cx + p.offset} cy={p.y} r={MARKER_R} fill={color} fillOpacity={0.9} stroke={t.pageBg} strokeWidth={0.75} />
                  ))}
                  <line
                    x1={cx - violinHalfWidth * 0.8}
                    x2={cx + violinHalfWidth * 0.8}
                    y1={yScale(cell.median)}
                    y2={yScale(cell.median)}
                    stroke={t.ink}
                    strokeWidth={2.5}
                  />
                </g>
              );
            })}
            {ci === closestIndex && (
              <g>
                <line x1={centersX[0]} x2={centersX[groups.length - 1]} y1={Math.min(...tops) - 18} y2={Math.min(...tops) - 18} stroke={t.inkSoft} strokeWidth={1.25} />
                {[centersX[0], centersX[groups.length - 1]].map((x) => (
                  <line key={x} x1={x} x2={x} y1={Math.min(...tops) - 18} y2={Math.min(...tops) - 10} stroke={t.inkSoft} strokeWidth={1.25} />
                ))}
                <text
                  x={(centersX[0] + centersX[groups.length - 1]) / 2}
                  y={Math.max(top + 16, Math.min(...tops) - 28)}
                  textAnchor="middle"
                  fontSize={15}
                  fontStyle="italic"
                  fill={t.inkSoft}
                >
                  {CALLOUT}
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
      <div style={{ height: LEGEND_H, display: "flex", alignItems: "center", gap: 28, padding: "0 36px" }}>
        <span style={{ fontSize: 15, color: t.ink }}>{LEVEL}</span>
        {groups.map((group, i) => (
          <div key={group} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 14, height: 14, borderRadius: 7, background: t.palette[i], display: "inline-block" }} />
            <span style={{ fontSize: 15, color: t.ink }}>{group}</span>
          </div>
        ))}
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H - LEGEND_H}
        series={[]}
        skipAnimation
        margin={{ top: 8, right: 48, bottom: 12, left: 24 }}
        xAxis={[
          {
            id: "category",
            scaleType: "band",
            data: categories,
            categoryGapRatio: 0.3,
            disableTicks: true,
            height: 72,
            label: TASK,
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
            label: TIME,
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
        <GroupedViolinSwarm />
        <ChartsXAxis axisId="category" />
        <ChartsYAxis axisId="value" />
      </ChartsContainer>
    </div>
  );
}
