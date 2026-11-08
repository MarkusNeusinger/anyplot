// anyplot.ai
// line-annotated-events: Annotated Line Plot with Event Markers
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: 96/100 | Created: 2026-09-05
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const Y_PAD_SHARE = 0.05; // share of the value range added below the lowest value
const Y_HEADROOM_SHARE = 0.18; // room above the highest value for two rows of event labels
const LABEL_ROW_PX = 26; // vertical offset between the two alternating label rows

// Columns: set these to your data's column names
const DATE = "Date"; // role: date
const VALUE = "Daily active users (thousands)"; // role: value
const EVENT_DATE = "Event date"; // role: event_date
const EVENT_LABEL = "Event"; // role: event_label

// Data: replace this block with your own records: one object per day of the series
// (date and value) and one per event (event date and label); other cells stay null
// Daily active users of a SaaS product from 1 Jan to 27 Sep 2025: a slow upward drift with
// daily noise, a lasting step up on each launch, and a sharp dip on the outage day that
// halves every day after as users come back.
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  const isoDay = (i: number) => new Date(Date.UTC(2025, 0, 1 + i)).toISOString().slice(0, 10);
  const events = [
    { day: 34, label: "Beta launch", step: 6, dip: 0 },
    { day: 96, label: "Mobile app release", step: 13, dip: 0 },
    { day: 130, label: "Service outage", step: 0, dip: -15 },
    { day: 162, label: "API v2 launch", step: 9, dip: 0 },
    { day: 228, label: "Enterprise tier", step: 17, dip: 0 },
  ];
  const series = [];
  let level = 42;
  let dip = 0;
  for (let i = 0; i < 270; i += 1) {
    const event = events.find((e) => e.day === i);
    level = Math.max(5, level + 0.11 + (rand() - 0.5) * 1.6 + (event?.step ?? 0));
    dip = dip / 2 + (event?.dip ?? 0);
    const users = Math.max(5, level + dip);
    series.push({ [DATE]: isoDay(i), [VALUE]: Math.round(users * 10) / 10, [EVENT_DATE]: null, [EVENT_LABEL]: null });
  }
  const marks = events.map((e) => ({ [DATE]: null, [VALUE]: null, [EVENT_DATE]: isoDay(e.day), [EVENT_LABEL]: e.label }));
  return [...series, ...marks];
})();

// Plot: reads only data and the constants above
// ISO dates are read as local midnight, the frame the time axis places its ticks in
const points = data
  .filter((d) => d[DATE] != null && d[VALUE] != null)
  .sort((a, b) => Date.parse(a[DATE]) - Date.parse(b[DATE]));
const events = data
  .filter((d) => d[EVENT_DATE] != null && d[EVENT_LABEL] != null)
  .sort((a, b) => Date.parse(a[EVENT_DATE]) - Date.parse(b[EVENT_DATE]));
const dates = points.map((d) => new Date(`${d[DATE]}T00:00:00`));
const values = points.map((d) => d[VALUE]);
const eventDates = events.map((e) => new Date(`${e[EVENT_DATE]}T00:00:00`));
const n = points.length;

const yLow = Math.min(...values);
const yHigh = Math.max(...values);
const yRange = yHigh - yLow;

// One tick at the start of every month the series spans
const monthTicks: Date[] = [];
const monthCursor = new Date(dates[0].getFullYear(), dates[0].getMonth() + (dates[0].getDate() > 1 ? 1 : 0), 1);
while (monthCursor <= dates[n - 1]) {
  monthTicks.push(new Date(monthCursor));
  monthCursor.setMonth(monthCursor.getMonth() + 1);
}

const monthFormat = new Intl.DateTimeFormat("en-US", { month: "short" });
const fullFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" });

const TITLE = "line-annotated-events · javascript · muix · anyplot.ai";
const SUBTITLE =
  `${n} days, ${fullFormat.format(dates[0])} – ${fullFormat.format(dates[n - 1])} · ` +
  `${events.length} events, each a dashed line at its date`;
const HEADER_H = 84;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "14px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.6 }}>{SUBTITLE}</Typography>
      </Box>
      <LineChart
        width={width}
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        margin={{ top: 12, right: 40, bottom: 16, left: 20 }}
        series={[
          {
            id: "value",
            data: values,
            label: VALUE,
            color: t.palette[0],
            curve: "linear",
            showMark: false,
          },
        ]}
        xAxis={[
          {
            data: dates,
            scaleType: "time",
            domainLimit: "strict",
            tickInterval: monthTicks,
            valueFormatter: (v: Date, context) =>
              context.location === "tick" ? monthFormat.format(v) : fullFormat.format(v),
            label: DATE,
            height: 64,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yLow - yRange * Y_PAD_SHARE,
            max: yHigh + yRange * Y_HEADROOM_SHARE,
            width: 72,
            label: VALUE,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        {/* Consecutive events alternate between two label rows so close neighbours never collide */}
        {events.map((e, i) => (
          <ChartsReferenceLine
            key={`${e[EVENT_DATE]}-${e[EVENT_LABEL]}`}
            x={eventDates[i]}
            label={e[EVENT_LABEL]}
            labelAlign="start"
            spacing={{ x: 8, y: 8 + (i % 2) * LABEL_ROW_PX }}
            labelStyle={{ fontSize: 15, fontWeight: 600, fill: t.ink }}
            lineStyle={{ stroke: t.inkSoft, strokeWidth: 1.75, strokeDasharray: "6 4" }}
          />
        ))}
      </LineChart>
    </Box>
  );
}
