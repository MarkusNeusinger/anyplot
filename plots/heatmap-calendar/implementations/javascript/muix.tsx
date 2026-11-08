// anyplot.ai
// heatmap-calendar: Basic Calendar Heatmap
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const DAY_MS = 86400000;
const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const NO_DATA_LABEL = "No data";
const TITLE = "heatmap-calendar · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 64;
const MONTH_LABEL_H = 40;
const Y_AXIS_W = 56;
const MAX_CELL_ASPECT = 2.8; // a day cell is at most this many times taller than wide

// Columns: set these to your data's column names
const DATE = "Date"; // role: date
const COMMITS = "Commits per day"; // role: value

// Data: replace this block with your own records, one object per row
// One year of daily commit counts for a developer (GitHub-style): busier weekdays, a release-day
// spike every 37 days, and a 9-day trip in August with no rows at all
const data = (() => {
  let s = 42 >>> 0;
  const rng = () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
  const rows: { [DATE]: string; [COMMITS]: number }[] = [];
  for (let i = 0; i < 365; i += 1) {
    const day = new Date(Date.UTC(2023, 0, 1 + i));
    if (i >= 215 && i < 224) continue;
    const weekend = day.getUTCDay() === 0 || day.getUTCDay() === 6;
    let commits = weekend ? 1 + rng() * 3 : 3 + rng() * 7;
    if (i % 37 === 17) commits += 4 + rng() * 4;
    rows.push({ [DATE]: day.toISOString().slice(0, 10), [COMMITS]: Math.round(commits) });
  }
  return rows;
})();

// Plot: reads only data and the constants above
const valueByDay = new Map<number, number>();
data.forEach((d) => {
  const ms = Date.parse(d[DATE]);
  if (Number.isFinite(ms) && Number.isFinite(d[COMMITS])) valueByDay.set(Math.floor(ms / DAY_MS), d[COMMITS]);
});
const dayNumbers = [...valueByDay.keys()].sort((a, b) => a - b);
const firstDay = dayNumbers[0];
const lastDay = dayNumbers[dayNumbers.length - 1];

// Calendar grid: one column per week starting on the Monday on or before the first day, one row per weekday
const firstMonday = firstDay - ((new Date(firstDay * DAY_MS).getUTCDay() + 6) % 7);
const days = Array.from({ length: lastDay - firstDay + 1 }, (_, i) => {
  const dayNumber = firstDay + i;
  const date = new Date(dayNumber * DAY_MS);
  return {
    dayNumber,
    week: Math.floor((dayNumber - firstMonday) / 7),
    weekday: WEEKDAYS[(dayNumber - firstMonday) % 7],
    value: valueByDay.get(dayNumber),
    monthStart: date.getUTCDate() === 1 || i === 0,
    newYear: date.getUTCMonth() === 0 || i === 0,
  };
});
const weeks = Array.from({ length: days[days.length - 1].week + 1 }, (_, i) => i);
const values = [...valueByDay.values()];
const valueMin = Math.min(...values);
const valueMax = Math.max(...values);

const monthFormat = new Intl.DateTimeFormat("en-US", { month: "short", timeZone: "UTC" });
const yearFormat = new Intl.DateTimeFormat("en-US", { year: "numeric", timeZone: "UTC" });
const fullDateFormat = new Intl.DateTimeFormat("en-US", { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
const missingDays = days.filter((d) => d.value === undefined).length;
const subtitle = `${fullDateFormat.format(firstDay * DAY_MS)} – ${fullDateFormat.format(lastDay * DAY_MS)} · ${values.length} days with data, ${missingDays} without (empty cells) · ${values.reduce((a, b) => a + b, 0)} in total`;

function CalendarCells() {
  const xScale = useXScale() as unknown as ((v: number) => number) & { bandwidth: () => number };
  const yScale = useYScale() as unknown as ((v: string) => number) & { bandwidth: () => number };
  const colorScale = useZColorScale() as unknown as (v: number) => string;
  const cellW = xScale.bandwidth();
  const cellH = yScale.bandwidth();
  const gridTop = yScale(WEEKDAYS[0]);
  return (
    <g>
      {days.map((d) => (
        <rect
          key={d.dayNumber}
          x={xScale(d.week)}
          y={yScale(d.weekday)}
          width={cellW}
          height={cellH}
          rx={3}
          fill={d.value === undefined ? "none" : colorScale(d.value)}
          stroke={d.value === undefined ? t.inkSoft : "none"}
          strokeWidth={1.25}
          strokeDasharray={d.value === undefined ? "3 3" : undefined}
        />
      ))}
      {days
        .filter((d) => d.monthStart)
        .map((d) => (
          <text key={`m-${d.dayNumber}`} x={xScale(d.week)} y={gridTop - 14} fontSize={15} fill={t.inkSoft}>
            {d.newYear
              ? `${monthFormat.format(d.dayNumber * DAY_MS)} ${yearFormat.format(d.dayNumber * DAY_MS)}`
              : monthFormat.format(d.dayNumber * DAY_MS)}
          </text>
        ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  // Rows fill the free height up to a cap on the cell's height-to-width ratio; the block is centred vertically
  const weekStep = (width - 16 - Y_AXIS_W - 32) / weeks.length;
  const gridH = Math.min(height - TITLE_H - LEGEND_H - MONTH_LABEL_H - 8, WEEKDAYS.length * weekStep * MAX_CELL_ASPECT);
  const chartH = gridH + MONTH_LABEL_H + 8;
  return (
    <Box sx={{ width, height, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, pt: "20px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, mt: "6px" }}>{subtitle}</Typography>
      </Box>
      <Box sx={{ flex: 1, display: "flex", alignItems: "center" }}>
        <ChartsDataProvider
          width={width}
          height={chartH}
          series={[]}
          skipAnimation
          margin={{ top: MONTH_LABEL_H, right: 32, bottom: 8, left: 16 }}
          xAxis={[{ scaleType: "band", data: weeks, position: "none", categoryGapRatio: 0.14 }]}
          yAxis={[
            {
              scaleType: "band",
              data: WEEKDAYS,
              width: Y_AXIS_W,
              categoryGapRatio: 0.14,
              disableLine: true,
              disableTicks: true,
              tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            },
          ]}
          zAxis={[{ colorMap: { type: "continuous", min: valueMin, max: valueMax, color: [t.seq[0], t.seq[1]] } }]}
        >
          <ChartsWrapper
            legendPosition={{ vertical: "bottom", horizontal: "end" }}
            legendDirection="horizontal"
            sx={{ width, height: chartH + LEGEND_H }}
          >
            <Box
              sx={{
                gridArea: "legend",
                height: LEGEND_H,
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-end",
                gap: "16px",
                pr: "32px",
              }}
            >
              <Typography sx={{ fontSize: 15, color: t.ink }}>{COMMITS}</Typography>
              <ContinuousColorLegend
                direction="horizontal"
                thickness={16}
                labelPosition="end"
                sx={{ width: 320, color: t.inkSoft, fontSize: 14 }}
              />
              <Box
                sx={{
                  width: 22,
                  height: 22,
                  ml: "20px",
                  borderRadius: "3px",
                  border: `1.5px dashed ${t.inkSoft}`,
                  boxSizing: "border-box",
                }}
              />
              <Typography sx={{ fontSize: 15, color: t.inkSoft }}>{NO_DATA_LABEL}</Typography>
            </Box>
            <ChartsSurface>
              <CalendarCells />
              <ChartsYAxis />
            </ChartsSurface>
          </ChartsWrapper>
        </ChartsDataProvider>
      </Box>
    </Box>
  );
}
