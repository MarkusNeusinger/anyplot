// anyplot.ai
// timeline-basic: Event Timeline
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const PAD_SHARE = 0.06; // room before the first and after the last event, as a share of the span
const MARKER_R = 11; // event marker radius (px)
const LABEL_CLEARANCE = 64; // px kept beyond a stem's end for its two label lines
const TITLE_H = 64;
const LEGEND_H = 44;
const MARGIN = { top: 16, right: 48, bottom: 8, left: 48 };
const X_AXIS_H = 44;

// Columns: set these to your data's column names
const DATE = "Date"; // role: date
const EVENT = "Milestone"; // role: event
const CATEGORY = "Mission phase"; // role: category

// Data: replace this block with your own records, one object per row
// Milestones of NASA's Perseverance rover mission, dates from NASA/JPL releases
const data = [
  { [DATE]: new Date(2020, 6, 30), [EVENT]: "Launch on Atlas V", [CATEGORY]: "Launch" },
  { [DATE]: new Date(2021, 1, 18), [EVENT]: "Landing in Jezero Crater", [CATEGORY]: "Landing" },
  { [DATE]: new Date(2021, 3, 19), [EVENT]: "Ingenuity's First Flight", [CATEGORY]: "Exploration" },
  { [DATE]: new Date(2021, 8, 1), [EVENT]: "First Rock Sample", [CATEGORY]: "Science" },
  { [DATE]: new Date(2022, 3, 13), [EVENT]: "Arrival at the Delta Front", [CATEGORY]: "Exploration" },
  { [DATE]: new Date(2023, 0, 28), [EVENT]: "Sample Depot Completed", [CATEGORY]: "Science" },
  { [DATE]: new Date(2024, 0, 18), [EVENT]: "Ingenuity's Final Flight", [CATEGORY]: "Exploration" },
];

// Plot: reads only data and the constants above
// Events in date order; labels alternate above and below the spine in that order,
// and the earliest and latest labels open inward so they stay on the canvas
const events = data
  .filter((d) => d[DATE] instanceof Date && !Number.isNaN(d[DATE].getTime()))
  .sort((a, b) => a[DATE].getTime() - b[DATE].getTime())
  .map((d, i, all) => ({
    id: `event-${i}`,
    time: d[DATE].getTime(),
    name: d[EVENT],
    category: d[CATEGORY],
    dateText: d[DATE].toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
    above: i % 2 === 0,
    anchor: i === 0 ? "start" : i === all.length - 1 ? "end" : "middle",
  }));
const categories = [...new Set(events.map((e) => e.category))];
const categoryColor = Object.fromEntries(categories.map((c, i) => [c, t.palette[i]]));
const tFirst = events[0].time;
const tLast = events[events.length - 1].time;
const tPad = (tLast - tFirst) * PAD_SHARE;
const spanYears = (tLast - tFirst) / (365.25 * 24 * 3600 * 1000);

const TITLE = "Perseverance Rover Mission · timeline-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${events.length} ${EVENT.toLowerCase()}s over ${spanYears.toFixed(1)} years · color = ${CATEGORY.toLowerCase()}`;

function EventLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  const spineY = yScale(0);
  const [plotTop, plotBottom] = [yScale(1), yScale(-1)];
  const stem = (plotBottom - plotTop) / 2 - LABEL_CLEARANCE;

  return (
    <g>
      {events.map((e) => {
        const x = xScale(e.time);
        const end = e.above ? spineY - stem : spineY + stem;
        return (
          <g key={e.id}>
            <line x1={x} y1={spineY} x2={x} y2={end} stroke={categoryColor[e.category]} strokeWidth={2} />
            <text
              x={x}
              y={e.above ? end - 46 : end + 10}
              textAnchor={e.anchor}
              dominantBaseline="hanging"
              fontSize={16}
              fontWeight={600}
              fill={t.ink}
            >
              {e.name}
            </text>
            <text
              x={x}
              y={e.above ? end - 24 : end + 32}
              textAnchor={e.anchor}
              dominantBaseline="hanging"
              fontSize={14}
              fill={t.inkSoft}
            >
              {e.dateText}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width: W, height: H } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "4px", pt: "6px" }}>
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 15, lineHeight: 1.2 }}>{SUBTITLE}</Typography>
      </Box>
      <ChartsDataProvider
        width={W}
        height={H - TITLE_H - LEGEND_H}
        skipAnimation
        margin={MARGIN}
        series={categories.map((c, i) => ({
          type: "scatter" as const,
          id: `category-${i}`,
          label: c,
          color: categoryColor[c],
          markerSize: MARKER_R,
          data: events.filter((e) => e.category === c).map((e) => ({ id: e.id, x: e.time, y: 0 })),
          valueFormatter: (_v, { dataIndex }) => {
            const e = events.filter((ev) => ev.category === c)[dataIndex];
            return `${e.name} · ${e.dateText}`;
          },
        }))}
        xAxis={[
          {
            scaleType: "time",
            min: new Date(tFirst - tPad),
            max: new Date(tLast + tPad),
            height: X_AXIS_H,
            tickNumber: 8,
            valueFormatter: (v: Date) => v.toLocaleDateString("en-US", { month: "short", year: "numeric" }),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[{ min: -1, max: 1, position: "none" }]}
      >
        <ChartsWrapper legendPosition={{ vertical: "bottom", horizontal: "center" }} legendDirection="horizontal">
          <ChartsLegend direction="horizontal" sx={{ fontSize: 15, color: t.inkSoft, height: LEGEND_H, justifyContent: "center" }} />
          <ChartsSurface
            sx={{
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
              "& .MuiScatterChart-marker": { stroke: t.pageBg, strokeWidth: 2 },
            }}
          >
            <ChartsXAxis />
            <ChartsReferenceLine y={0} lineStyle={{ stroke: t.inkSoft, strokeWidth: 2 }} />
            <EventLabels />
            <ScatterPlot />
          </ChartsSurface>
          <ChartsTooltip trigger="item" />
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
