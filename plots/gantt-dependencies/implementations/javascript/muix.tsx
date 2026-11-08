// anyplot.ai
// gantt-dependencies: Gantt Chart with Dependencies
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-08-25
import { BarChart } from "@mui/x-charts/BarChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const DAY_MS = 86400000;
const TICK_DAYS = 7; // one date tick per week from the first start
const X_PAD_SHARE = 0.02; // time padding on both sides, as a share of the schedule span
const ARROW_STUB = 12; // px an arrow runs straight out of a bar end before it turns
const DEPENDENCY_SEPARATOR = ";"; // separates several predecessors in one cell
const TASK_PREFIX = "↳ "; // marks a task row below its group header row
const GROUP_SPAN_LABEL = "Group span (earliest start to latest end)";
const DATE_LABEL = "Date";
const TITLE = "gantt-dependencies · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 44;

// Columns: set these to your data's column names
const TASK = "Task"; // role: task
const START = "Start"; // role: start
const END = "End"; // role: end
const PHASE = "Phase"; // role: group
const DEPENDS_ON = "Depends on"; // role: depends_on

// Data: replace this block with your own records, one object per row
// Software release plan, four phases of dependent tasks; all links are finish-to-start
const data = [
  { [TASK]: "Gather requirements", [PHASE]: "Requirements", [START]: "2026-01-01", [END]: "2026-01-05", [DEPENDS_ON]: "" },
  { [TASK]: "Stakeholder review", [PHASE]: "Requirements", [START]: "2026-01-05", [END]: "2026-01-08", [DEPENDS_ON]: "Gather requirements" },
  { [TASK]: "Finalize scope", [PHASE]: "Requirements", [START]: "2026-01-08", [END]: "2026-01-10", [DEPENDS_ON]: "Stakeholder review" },
  { [TASK]: "UI wireframes", [PHASE]: "Design", [START]: "2026-01-10", [END]: "2026-01-15", [DEPENDS_ON]: "Finalize scope" },
  { [TASK]: "Database schema", [PHASE]: "Design", [START]: "2026-01-10", [END]: "2026-01-16", [DEPENDS_ON]: "Finalize scope" },
  { [TASK]: "Architecture review", [PHASE]: "Design", [START]: "2026-01-16", [END]: "2026-01-18", [DEPENDS_ON]: "UI wireframes; Database schema" },
  { [TASK]: "Backend API", [PHASE]: "Development", [START]: "2026-01-18", [END]: "2026-01-28", [DEPENDS_ON]: "Architecture review" },
  { [TASK]: "Frontend UI", [PHASE]: "Development", [START]: "2026-01-18", [END]: "2026-01-30", [DEPENDS_ON]: "Architecture review" },
  { [TASK]: "Integration", [PHASE]: "Development", [START]: "2026-01-30", [END]: "2026-02-03", [DEPENDS_ON]: "Backend API; Frontend UI" },
  { [TASK]: "Unit testing", [PHASE]: "Testing", [START]: "2026-02-03", [END]: "2026-02-06", [DEPENDS_ON]: "Integration" },
  { [TASK]: "QA testing", [PHASE]: "Testing", [START]: "2026-02-06", [END]: "2026-02-10", [DEPENDS_ON]: "Unit testing" },
  { [TASK]: "UAT sign-off", [PHASE]: "Testing", [START]: "2026-02-10", [END]: "2026-02-13", [DEPENDS_ON]: "QA testing" },
  { [TASK]: "Deployment", [PHASE]: "Testing", [START]: "2026-02-13", [END]: "2026-02-14", [DEPENDS_ON]: "UAT sign-off" },
];

// Plot: reads only data and the constants above
const tasks = data
  .map((d) => ({
    name: d[TASK],
    phase: d[PHASE],
    start: Date.parse(d[START]),
    end: Date.parse(d[END]),
    predecessors: String(d[DEPENDS_ON] ?? "")
      .split(DEPENDENCY_SEPARATOR)
      .map((s) => s.trim())
      .filter((s) => s.length > 0),
  }))
  .filter((d) => Number.isFinite(d.start) && Number.isFinite(d.end));
const phases = [...new Set(tasks.map((d) => d.phase))];

// Rows top to bottom: each group header, then its tasks by start date
const rows = phases.flatMap((phase, phaseIndex) => {
  const members = tasks.filter((d) => d.phase === phase).sort((a, b) => a.start - b.start);
  return [
    {
      label: phase,
      kind: "group",
      phaseIndex,
      start: Math.min(...members.map((d) => d.start)),
      end: Math.max(...members.map((d) => d.end)),
    },
    ...members.map((d) => ({ label: `${TASK_PREFIX}${d.name}`, kind: "task", phaseIndex, start: d.start, end: d.end })),
  ];
});
const rowByTask = new Map(tasks.map((d) => [d.name, rows.find((r) => r.label === `${TASK_PREFIX}${d.name}`)]));

// Finish-to-start links: predecessor end (right edge) to successor start (left edge)
const edges = tasks.flatMap((d) =>
  d.predecessors
    .filter((p) => rowByTask.has(p))
    .map((p) => ({ from: rowByTask.get(p), to: rowByTask.get(d.name) })),
);

const firstStart = Math.min(...rows.map((r) => r.start));
const lastEnd = Math.max(...rows.map((r) => r.end));
const xPad = (lastEnd - firstStart) * X_PAD_SHARE;
const ticks = Array.from(
  { length: Math.floor((lastEnd - firstStart) / (TICK_DAYS * DAY_MS)) + 1 },
  (_, i) => firstStart + i * TICK_DAYS * DAY_MS,
);
const dayFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
const fullDateFormat = new Intl.DateTimeFormat("en-US", { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
const subtitle = `${tasks.length} tasks in ${phases.length} groups · ${edges.length} finish-to-start dependencies, arrow from predecessor end to successor start · ${fullDateFormat.format(firstStart)} – ${fullDateFormat.format(lastEnd)}`;

// Floating bars: a transparent segment up to each row's start, stacked with the span of a group or a task
const spanLabels = rows.map((r) => `${dayFormat.format(r.start)} – ${dayFormat.format(r.end)}`);
const series = [
  { id: "offset", stack: "schedule", color: "transparent", data: rows.map((r) => r.start), valueFormatter: () => null },
  {
    id: "group-span",
    label: GROUP_SPAN_LABEL,
    stack: "schedule",
    color: t.inkSoft,
    data: rows.map((r) => (r.kind === "group" ? r.end - r.start : null)),
    valueFormatter: (v: number | null, { dataIndex }: { dataIndex: number }) => (v === null ? null : spanLabels[dataIndex]),
  },
  ...phases.map((phase, i) => ({
    id: `phase-${i}`,
    label: phase,
    stack: "schedule",
    color: t.palette[i],
    data: rows.map((r) => (r.kind === "task" && r.phaseIndex === i ? r.end - r.start : null)),
    valueFormatter: (v: number | null, { dataIndex }: { dataIndex: number }) => (v === null ? null : spanLabels[dataIndex]),
  })),
];

function DependencyArrows() {
  const xScale = useXScale() as unknown as (v: number) => number;
  const yScale = useYScale() as unknown as ((v: string) => number) & { bandwidth: () => number; step: () => number };
  const band = yScale.bandwidth();
  const gap = yScale.step() - band;
  return (
    <g>
      <defs>
        <marker id="dependency-arrowhead" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
          <path d="M0,0 L10,5 L0,10 Z" fill={t.ink} />
        </marker>
      </defs>
      {edges.map((edge) => {
        const fromX = xScale(edge.from.end);
        const fromY = yScale(edge.from.label) + band / 2;
        const toX = xScale(edge.to.start);
        const toY = yScale(edge.to.label) + band / 2;
        // Out of the predecessor's end into the gap below its row, across to just left of the
        // successor's start, then down and into its left edge, clear of bars that start with it
        const gapY = yScale(edge.from.label) + band + gap / 2;
        const d = `M ${fromX} ${fromY} H ${fromX + ARROW_STUB} V ${gapY} H ${toX - ARROW_STUB} V ${toY} H ${toX}`;
        return (
          <path
            key={`${edge.from.label}->${edge.to.label}`}
            d={d}
            stroke={t.ink}
            strokeWidth={1.75}
            strokeLinejoin="round"
            fill="none"
            markerEnd="url(#dependency-arrowhead)"
          />
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <Box sx={{ width, height, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, pt: "20px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, mt: "6px" }}>{subtitle}</Typography>
      </Box>
      <BarChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        layout="horizontal"
        skipAnimation
        series={series}
        grid={{ vertical: true }}
        margin={{ top: 12, right: 56, bottom: 12, left: 24 }}
        xAxis={[
          {
            min: firstStart - xPad,
            max: lastEnd + xPad,
            tickInterval: ticks,
            valueFormatter: (v: number) => dayFormat.format(v),
            label: DATE_LABEL,
            height: 64,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: rows.map((r) => r.label),
            width: 230,
            categoryGapRatio: 0.32,
            disableTicks: true,
            tickLabelStyle: { fontSize: 14, fill: t.ink },
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: { fontSize: 15, color: t.inkSoft, mb: "8px" },
          },
        }}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <DependencyArrows />
      </BarChart>
    </Box>
  );
}
