// anyplot.ai
// gantt-basic: Basic Gantt Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-05
import { BarChart } from "@mui/x-charts/BarChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const DAY_MS = 86400000;
const TICK_DAYS = 14; // one date tick every two weeks from the first start
const X_PAD_SHARE = 0.02; // time padding on both sides, as a share of the schedule span
const DATE_LABEL = "Date";
const TITLE = "gantt-basic · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 44;

// Columns: set these to your data's column names
const TASK = "Task"; // role: task
const START = "Start"; // role: start
const END = "End"; // role: end
const PHASE = "Phase"; // role: category

// Data: replace this block with your own records, one object per row, and the status date of the schedule
// Website redesign project: 11 tasks across 4 phases, reported as of 20 February 2026
const AS_OF = "2026-02-20";
const data = [
  { [TASK]: "Requirements gathering", [PHASE]: "Design", [START]: "2026-01-05", [END]: "2026-01-12" },
  { [TASK]: "Wireframing", [PHASE]: "Design", [START]: "2026-01-10", [END]: "2026-01-20" },
  { [TASK]: "Visual design", [PHASE]: "Design", [START]: "2026-01-18", [END]: "2026-01-30" },
  { [TASK]: "Backend development", [PHASE]: "Development", [START]: "2026-01-26", [END]: "2026-02-20" },
  { [TASK]: "Frontend development", [PHASE]: "Development", [START]: "2026-01-29", [END]: "2026-02-24" },
  { [TASK]: "API integration", [PHASE]: "Development", [START]: "2026-02-16", [END]: "2026-02-27" },
  { [TASK]: "Unit testing", [PHASE]: "Testing", [START]: "2026-02-21", [END]: "2026-03-01" },
  { [TASK]: "QA and bug fixes", [PHASE]: "Testing", [START]: "2026-02-27", [END]: "2026-03-10" },
  { [TASK]: "User acceptance testing", [PHASE]: "Testing", [START]: "2026-03-06", [END]: "2026-03-14" },
  { [TASK]: "Deployment", [PHASE]: "Launch", [START]: "2026-03-12", [END]: "2026-03-16" },
  { [TASK]: "Post-launch monitoring", [PHASE]: "Launch", [START]: "2026-03-14", [END]: "2026-03-25" },
];

// Plot: reads only data and the constants above
const tasks = data
  .map((d) => ({ name: d[TASK], phase: d[PHASE], start: Date.parse(d[START]), end: Date.parse(d[END]) }))
  .filter((d) => Number.isFinite(d.start) && Number.isFinite(d.end))
  .sort((a, b) => a.start - b.start);
const phases = [...new Set(tasks.map((d) => d.phase))];

const firstStart = Math.min(...tasks.map((d) => d.start));
const lastEnd = Math.max(...tasks.map((d) => d.end));
const xPad = (lastEnd - firstStart) * X_PAD_SHARE;
const ticks = Array.from(
  { length: Math.floor((lastEnd - firstStart) / (TICK_DAYS * DAY_MS)) + 1 },
  (_, i) => firstStart + i * TICK_DAYS * DAY_MS,
);
const asOf = Date.parse(AS_OF);
const showAsOf = asOf >= firstStart && asOf <= lastEnd;

const dayFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
const fullDateFormat = new Intl.DateTimeFormat("en-US", { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
const subtitle = `${tasks.length} tasks colored by ${PHASE} · ${fullDateFormat.format(firstStart)} – ${fullDateFormat.format(lastEnd)} (${Math.round((lastEnd - firstStart) / DAY_MS)} days)`;

// Each task is a floating bar: a transparent segment up to its start, stacked with its phase's duration segment
const series = [
  {
    id: "offset",
    stack: "schedule",
    color: "transparent",
    data: tasks.map((d) => d.start),
    valueFormatter: () => null,
  },
  ...phases.map((phase, i) => ({
    id: `phase-${i}`,
    label: phase,
    stack: "schedule",
    color: t.palette[i],
    data: tasks.map((d) => (d.phase === phase ? d.end - d.start : null)),
    valueFormatter: (value: number | null, { dataIndex }: { dataIndex: number }) =>
      value === null ? null : `${dayFormat.format(tasks[dataIndex].start)} – ${dayFormat.format(tasks[dataIndex].end)}`,
  })),
];

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
        borderRadius={3}
        series={series}
        grid={{ vertical: true }}
        margin={{ top: 16, right: 56, bottom: 16, left: 24 }}
        xAxis={[
          {
            min: firstStart - xPad,
            max: lastEnd + xPad,
            tickInterval: ticks,
            valueFormatter: (v: number) => dayFormat.format(v),
            label: DATE_LABEL,
            height: 68,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: tasks.map((d) => d.name),
            width: 220,
            categoryGapRatio: 0.35,
            disableTicks: true,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
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
        {showAsOf && (
          <ChartsReferenceLine
            x={asOf}
            label={`As of ${dayFormat.format(asOf)}`}
            labelAlign="start"
            lineStyle={{ stroke: t.ink, strokeDasharray: "6 4", strokeWidth: 2 }}
            labelStyle={{ fontSize: 14, fill: t.ink, fontWeight: 600 }}
          />
        )}
      </BarChart>
    </Box>
  );
}
