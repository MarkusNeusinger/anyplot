// anyplot.ai
// area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-19
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "area-cumulative-flow · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 44;

// Columns: set these to your data's column names
const DATE = "Date"; // role: date
const STAGE = "Stage"; // role: stage
const COUNT = "Cumulative tickets"; // role: count

// Data: replace this block with your own records, one object per row
// A support-ticket board over 70 days from 1 Apr 2026, stages in workflow order.
// Each stage is a queue that moves at most its daily capacity out of the backlog
// the previous stage hands it, so every cumulative count is non-decreasing and an
// earlier stage never falls below a later one. Development capacity drops for
// three weeks, then a staffing boost drains the backlog.
const data = (() => {
  const stageNames = ["New", "Triaged", "In Progress", "Resolved"];
  const start = new Date(2026, 3, 1);
  const totals = stageNames.map(() => 0);
  const rows: { [DATE]: Date; [STAGE]: string; [COUNT]: number }[] = [];
  for (let day = 0; day < 70; day += 1) {
    const date = new Date(start);
    date.setDate(date.getDate() + day);
    totals[0] += 9 + Math.round(2 * Math.sin(day / 8)) + (day >= 45 ? 4 : 0);
    const capacity = [14, day < 20 ? 9 : day < 42 ? 4 : 12, 8];
    for (let s = 1; s < stageNames.length; s += 1) {
      totals[s] += Math.min(capacity[s - 1], totals[s - 1] - totals[s]);
    }
    stageNames.forEach((stage, s) => rows.push({ [DATE]: date, [STAGE]: stage, [COUNT]: totals[s] }));
  }
  return rows;
})();

// Plot: reads only data and the constants above
const stages = [...new Set(data.map((d) => d[STAGE]))];
const dates = [...new Map(data.map((d) => [d[DATE].getTime(), d[DATE]])).values()].sort(
  (a, b) => a.getTime() - b.getTime(),
);
const countByKey = new Map(data.map((d) => [`${d[STAGE]}|${d[DATE].getTime()}`, d[COUNT]]));
const cumulative = stages.map((stage) => dates.map((dt) => countByKey.get(`${stage}|${dt.getTime()}`) ?? null));

// Band thickness: items currently in a stage, its cumulative count minus the next
// stage's; the last stage's band is its whole cumulative count
const bands = cumulative.map((row, i) =>
  row.map((v, k) => {
    if (i === stages.length - 1 || v == null) return v;
    const next = cumulative[i + 1][k];
    return next == null ? null : v - next;
  }),
);

// Largest work-in-progress band of any stage but the last, named in the subtitle
let peak = { stage: -1, day: -1, wip: -Infinity };
bands.slice(0, -1).forEach((row, i) =>
  row.forEach((v, k) => {
    if (v != null && v > peak.wip) peak = { stage: i, day: k, wip: v };
  }),
);
const fmtDay = (v: Date) => v.toLocaleDateString("en-US", { month: "short", day: "numeric" });
const SUBTITLE = [
  `${dates.length} days · ${stages.length} stages, earliest on top`,
  peak.stage >= 0 ? `widest band: ${stages[peak.stage]}, ${peak.wip} on ${fmtDay(dates[peak.day])}` : null,
]
  .filter(Boolean)
  .join(" · ");

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, px: "40px", pt: "18px", boxSizing: "border-box" }}>
        <Typography sx={{ color: t.ink, fontSize: "22px", fontWeight: 600, lineHeight: 1.2 }}>
          {TITLE}
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: "15px", lineHeight: 1.2, mt: "8px" }}>
          {SUBTITLE}
        </Typography>
      </Box>
      <LineChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true }}
        xAxis={[
          {
            data: dates,
            scaleType: "time",
            label: DATE,
            valueFormatter: fmtDay,
            tickNumber: 10,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            label: COUNT,
            width: 84,
            valueFormatter: (v: number) => v.toLocaleString("en-US"),
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={stages.map((stage, i) => ({
          id: `stage-${i}`,
          label: stage,
          data: bands[i],
          color: t.palette[i],
          stack: "flow",
          stackOrder: "reverse" as const,
          area: true,
          showMark: false,
          labelMarkType: "square" as const,
        }))}
        margin={{ top: 12, right: 40, bottom: 8, left: 24 }}
        slotProps={{
          legend: {
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 15, color: t.ink },
          },
        }}
        sx={{
          "& .MuiLineChart-area": { fillOpacity: 0.85, filter: "none" },
          "& .MuiLineChart-line": { strokeWidth: 2.5 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      />
    </Box>
  );
}
