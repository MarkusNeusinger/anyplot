// anyplot.ai
// violin-split: Split Violin Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const GRID_N = 160; // KDE evaluation points per half
const TAIL_BANDWIDTHS = 1.5; // the density falls below ~4 % of its peak this far past the data
const SCORE_MIN = 0; // the test's fixed score range: no density is drawn and no tick is set outside it
const SCORE_MAX = 100;
const Y_PAD = 0.04; // share of the value range added below the data
const Y_HEADROOM = 0.08; // share of the value range added above the data, room for the callout
const Y_TICK_COUNT = 15; // about this many value ticks
const NICE_STEPS = [1, 2, 2.5, 5, 10]; // round tick step multipliers
const TITLE = "violin-split · javascript · muix · anyplot.ai";
const TITLE_H = 80;
const LEGEND_H = 40;

// Columns: set these to your data's column names
const SUBJECT = "Subject"; // role: category
const GROUP = "Study arm"; // role: split_group
const SCORE = "Test score (points)"; // role: value

// Data: replace this block with your own records, one object per row
// End-of-term test scores of 140 students per subject and study arm; the
// experimental arm used a new tutoring program. Scores outside 0-100 are redrawn.
const data = (() => {
  let state = 20260909 >>> 0;
  const rng = () => {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state / 4294967296;
  };
  const gaussian = (mean, sd) => {
    let u1 = rng();
    while (u1 <= 1e-12) u1 = rng();
    return mean + sd * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * rng());
  };
  const subjects = [
    ["Mathematics", 68, 11, 74, 9],
    ["Science", 74, 9, 80, 7],
    ["Language Arts", 76, 8, 81, 7],
    ["History", 70, 10, 76, 8],
  ];
  return subjects.flatMap(([subject, cMean, cSd, eMean, eSd]) =>
    [
      ["Control", cMean, cSd],
      ["Experimental", eMean, eSd],
    ].flatMap(([arm, mean, sd]) =>
      Array.from({ length: 140 }, () => {
        let v = gaussian(mean, sd);
        while (v < 0 || v > 100) v = gaussian(mean, sd);
        return { [SUBJECT]: subject, [GROUP]: arm, [SCORE]: Math.round(v * 10) / 10 };
      }),
    ),
  );
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[SCORE] != null);
const categories = [...new Set(rows.map((d) => d[SUBJECT]))];
// A split violin has two halves: the first two split groups in order of
// appearance take the left and the right side in every category
const halvesOrder = [...new Set(rows.map((d) => d[GROUP]))].slice(0, 2);

// Per category and half: quartiles and a Gaussian KDE (Silverman bandwidth)
// normalized to its own peak, on a grid that ends a short way past the data,
// so each half tapers to the centre line just beyond its values; the grid is
// cut at the score range, where a half then ends flat
const halves = categories.map((cat) =>
  halvesOrder.map((group) => {
    const values = rows
      .filter((d) => d[SUBJECT] === cat && d[GROUP] === group)
      .map((d) => d[SCORE])
      .sort((a, b) => a - b);
    const n = values.length;
    if (n === 0) return null;
    const [q1, median, q3] = [0.25, 0.5, 0.75].map((q) => {
      const pos = (n - 1) * q;
      const base = Math.floor(pos);
      return values[base] + (pos - base) * ((values[base + 1] ?? values[base]) - values[base]);
    });
    const mean = values.reduce((a, b) => a + b, 0) / n;
    const sd = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(1, n - 1));
    const bandwidth = Math.max(0.9 * sd * Math.pow(n, -0.2), 1e-6);
    const lo = Math.max(SCORE_MIN, values[0] - TAIL_BANDWIDTHS * bandwidth);
    const hi = Math.min(SCORE_MAX, values[n - 1] + TAIL_BANDWIDTHS * bandwidth);
    const grid = Array.from({ length: GRID_N }, (_, k) => lo + (k * (hi - lo)) / (GRID_N - 1));
    const raw = grid.map((gy) => values.reduce((sum, v) => sum + Math.exp(-0.5 * ((gy - v) / bandwidth) ** 2), 0));
    const peak = Math.max(...raw);
    return { q1, median, q3, grid, density: raw.map((v) => v / peak) };
  }),
);

const filled = halves.flat().filter((h) => h != null);
const gridMin = Math.min(...filled.map((h) => h.grid[0]));
const gridMax = Math.max(...filled.map((h) => h.grid[GRID_N - 1]));
const yMin = gridMin - (gridMax - gridMin) * Y_PAD;
const yMax = gridMax + (gridMax - gridMin) * Y_HEADROOM;
// Round ticks inside the axis and the score range: the headroom above the
// test maximum holds the callout, never a score tick
const tickRaw = (yMax - yMin) / Y_TICK_COUNT;
const tickMagnitude = 10 ** Math.floor(Math.log10(tickRaw));
const tickStep = NICE_STEPS.map((m) => m * tickMagnitude).find((s) => s >= tickRaw);
const tickLo = Math.max(SCORE_MIN, Math.ceil(yMin / tickStep - 1e-9) * tickStep);
const tickHi = Math.min(SCORE_MAX, yMax);
const yTicks = Array.from({ length: Math.floor((tickHi - tickLo) / tickStep + 1e-9) + 1 }, (_, i) => tickLo + i * tickStep);

// Focal callout: the category with the largest gap between the two halves' medians
const UNIT = SCORE.match(/\(([^)]+)\)\s*$/)?.[1] ?? "";
const gaps = halves.map((pair) => (pair[0] && pair[1] ? pair[1].median - pair[0].median : null));
const gapIndex = gaps.reduce((best, g, i) => (g != null && (best < 0 || Math.abs(g) > Math.abs(gaps[best])) ? i : best), -1);
const CALLOUT =
  gapIndex >= 0
    ? `Largest median gap: ${halvesOrder[1]} ${gaps[gapIndex] >= 0 ? "+" : "−"}${Math.abs(gaps[gapIndex]).toFixed(1)} ${UNIT}`
    : null;
const SUBTITLE = `${rows.length.toLocaleString("en-US")} ${SCORE.replace(/\s*\([^)]*\)\s*$/, "").toLowerCase()}s across ${categories.length} ${SUBJECT.toLowerCase()}s · bar: Q1–Q3 of each half, dot: its median`;

// The community package has no violin component: a custom layer draws each
// half through the chart's band and linear scales, both meeting at the
// category's centre line.
function SplitViolins() {
  const xScale = useXScale();
  const yScale = useYScale();
  const band = xScale.bandwidth();
  const halfWidthMax = band * 0.42;

  return (
    <g>
      {categories.map((cat, ci) => {
        const cx = xScale(cat) + band / 2;
        const present = halves[ci].filter((h) => h != null);
        const spineTop = Math.min(...present.map((h) => yScale(h.grid[GRID_N - 1])));
        const spineBottom = Math.max(...present.map((h) => yScale(h.grid[0])));
        return (
          <g key={cat}>
            <line x1={cx} x2={cx} y1={spineTop} y2={spineBottom} stroke={t.inkSoft} strokeWidth={1} />
            {halves[ci].map((half, gi) => {
              if (half == null) return null;
              const side = gi === 0 ? -1 : 1;
              const color = t.palette[gi];
              const outline = half.grid.map((gy, k) => `L ${cx + side * half.density[k] * halfWidthMax} ${yScale(gy)}`).join(" ");
              const d = `M ${cx} ${yScale(half.grid[0])} ${outline} L ${cx} ${yScale(half.grid[GRID_N - 1])} Z`;
              const markerX = cx + side * 8;
              return (
                <g key={`${cat}-${gi}`}>
                  <path d={d} fill={color} fillOpacity={0.7} stroke={color} strokeWidth={1.5} strokeLinejoin="round" />
                  <line x1={markerX} x2={markerX} y1={yScale(half.q1)} y2={yScale(half.q3)} stroke={t.pageBg} strokeWidth={5} strokeLinecap="round" />
                  <circle cx={markerX} cy={yScale(half.median)} r={4.5} fill={t.pageBg} stroke={color} strokeWidth={1.75} />
                </g>
              );
            })}
            {ci === gapIndex && (
              <text x={cx} y={spineTop - 14} textAnchor="middle" fontSize={15} fontWeight={600} fill={t.ink}>
                {CALLOUT}
              </text>
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
        {halvesOrder.map((group, i) => (
          <div key={group} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 16, height: 16, borderRadius: 3, background: t.palette[i], opacity: 0.85, display: "inline-block" }} />
            <span style={{ fontSize: 15, color: t.ink }}>{`${group} (${i === 0 ? "left" : "right"} half)`}</span>
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
            disableTicks: true,
            height: 72,
            label: SUBJECT,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "value",
            scaleType: "linear",
            min: yMin,
            max: yMax,
            tickInterval: yTicks,
            width: 84,
            label: SCORE,
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
        <SplitViolins />
        <ChartsXAxis axisId="category" />
        <ChartsYAxis axisId="value" />
      </ChartsContainer>
    </div>
  );
}
