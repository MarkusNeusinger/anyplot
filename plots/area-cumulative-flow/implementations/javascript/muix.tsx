// anyplot.ai
// area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-18
import { LineChart } from "@mui/x-charts/LineChart";

const t = window.ANYPLOT_TOKENS;
const TITLE = "area-cumulative-flow · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;
const TITLE_FONT_SIZE = Math.max(15, Math.round(22 * Math.min(1, 67 / TITLE.length)));

// --- Data (in-memory, deterministic): software Kanban board, 90 days --------
// Workflow order, earliest stage first. `count[s][t]` is the cumulative number
// of items that have entered/passed through stage `s` by day `t`.
const STAGES = ["Backlog", "Analysis", "Development", "Testing", "Done"];
const N_DAYS = 90;
const START_DATE = new Date(2026, 0, 5);
const dates = Array.from(
  { length: N_DAYS },
  (_, i) => new Date(START_DATE.getTime() + i * 86400000),
);

// Fixed-seed 32-bit LCG (Numerical Recipes constants) — deterministic, no
// external RNG available in the browser.
let seed = 42;
function nextRand() {
  seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
  return seed / 4294967296;
}
function randInt(min, max) {
  return Math.floor(min + nextRand() * (max - min + 1));
}

// Backlog: cumulative arrivals into the pipeline.
const counts = STAGES.map(() => new Array(N_DAYS).fill(0));
for (let day = 0; day < N_DAYS; day += 1) {
  const arrivals = randInt(5, 9);
  counts[0][day] = (day === 0 ? 0 : counts[0][day - 1]) + arrivals;
}

// Downstream stages: each day, move as many items as capacity allows from the
// previous stage's pool into this one. Movement can never exceed what's
// actually waiting upstream, which guarantees count[s] <= count[s - 1] and
// count[s] stays monotonically non-decreasing over time.
// Testing's throughput cap is intentionally the tightest of the four —
// items enter Testing faster than QA can clear them, so the Testing band
// (WIP awaiting sign-off) widens steadily: a classic pipeline bottleneck.
const CAPACITY_RANGES = [
  [5, 9], // Backlog -> Analysis
  [5, 9], // Analysis -> Development
  [5, 9], // Development -> Testing
  [2, 5], // Testing -> Done (bottleneck)
];
for (let stage = 1; stage < STAGES.length; stage += 1) {
  const [capMin, capMax] = CAPACITY_RANGES[stage - 1];
  for (let day = 0; day < N_DAYS; day += 1) {
    const prevCumulative = day === 0 ? 0 : counts[stage][day - 1];
    const available = counts[stage - 1][day] - prevCumulative;
    const capacity = randInt(capMin, capMax);
    const moved = Math.max(0, Math.min(available, capacity));
    counts[stage][day] = prevCumulative + moved;
  }
}

// Distinct, non-adjacent Imprint hues — skip position 5 (matte red), the
// deferred semantic anchor for bad/error, since no stage here means "bad".
const STAGE_COLORS = [
  t.palette[0],
  t.palette[1],
  t.palette[2],
  t.palette[3],
  t.palette[5],
];

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
});

// Series are declared earliest-stage-first and NOT stacked (no `stack` id):
// each area fills independently from zero to its own raw cumulative count.
// Later series in the array paint on top, so Done (lowest values) fully
// occludes the stages beneath it, Testing shows only above the Done line,
// and so on up to Backlog, whose unoccluded sliver sits at the very top —
// exactly the "earliest stage on top" band order the spec calls for,
// without ever summing counts across stages.
const series = STAGES.map((stage, i) => ({
  id: stage,
  data: counts[i],
  label: stage,
  color: STAGE_COLORS[i],
  area: true,
  showMark: false,
  curve: "linear",
}));

export default function Chart() {
  const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT;

  return (
    <div
      style={{
        width: window.ANYPLOT_SIZE.width,
        height: window.ANYPLOT_SIZE.height,
        position: "relative",
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          lineHeight: `${TITLE_HEIGHT}px`,
          paddingLeft: 24,
          fontSize: TITLE_FONT_SIZE,
          fontWeight: 500,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      {/* MUI X's built-in yAxis label sits closer to the axis than 3-digit tick
          labels extend, so it renders directly on top of them. A custom
          absolutely-positioned label sidesteps that internal offset math. */}
      <div
        style={{
          position: "absolute",
          left: 4,
          top: TITLE_HEIGHT,
          width: 20,
          height: chartHeight,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          writingMode: "vertical-rl",
          transform: "rotate(180deg)",
          fontSize: 16,
          color: t.ink,
          whiteSpace: "nowrap",
        }}
      >
        Cumulative Items
      </div>
      <LineChart
        width={window.ANYPLOT_SIZE.width}
        height={chartHeight}
        skipAnimation
        series={series}
        xAxis={[
          {
            data: dates,
            scaleType: "time",
            label: "Date",
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
            valueFormatter: (date) => dateFormatter.format(date),
          },
        ]}
        yAxis={[
          {
            tickLabelStyle: { fontSize: 14 },
          },
        ]}
        grid={{ horizontal: true }}
        margin={{ top: 16, right: 32, bottom: 56, left: 84 }}
        slotProps={{
          legend: {
            direction: "row",
            position: { vertical: "top", horizontal: "middle" },
            labelStyle: { fontSize: 14 },
          },
        }}
      />
    </div>
  );
}
