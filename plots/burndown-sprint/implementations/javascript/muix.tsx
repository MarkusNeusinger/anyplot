// anyplot.ai
// burndown-sprint: Agile Sprint Burndown Chart
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 91/100 | Created: 2026-06-14
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { LinePlot, MarkPlot } from "@mui/x-charts/LineChart";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const DAY_MS = 24 * 60 * 60 * 1000;
const Y_PAD_SHARE = 0.12; // headroom above the largest value, as a share of it
const BEHIND = t.palette[4]; // semantic: matte red where the actual line runs above the ideal
const AHEAD = t.palette[0]; // semantic: brand green where it runs below
const STATUS_OPACITY = 0.2;

// Columns: set these to your data's column names
const DAY = "Day"; // role: day
const REMAINING = "Remaining (story points)"; // role: remaining
const IDEAL = "Ideal remaining (story points)"; // role: ideal
const SCOPE_CHANGE = "Scope change (story points)"; // role: scope_change

// Data: replace this block with your own records, one object per row
// Two-week sprint: committed at planning on Friday, then 10 working days.
// On Thursday of week 1 the team finished 2 points and 8 points were added.
const data = [
  { [DAY]: new Date(2026, 4, 29), [REMAINING]: 40, [IDEAL]: 40, [SCOPE_CHANGE]: 0 },
  { [DAY]: new Date(2026, 5, 1), [REMAINING]: 37, [IDEAL]: 36, [SCOPE_CHANGE]: 0 },
  { [DAY]: new Date(2026, 5, 2), [REMAINING]: 34, [IDEAL]: 32, [SCOPE_CHANGE]: 0 },
  { [DAY]: new Date(2026, 5, 3), [REMAINING]: 32, [IDEAL]: 28, [SCOPE_CHANGE]: 0 },
  { [DAY]: new Date(2026, 5, 4), [REMAINING]: 38, [IDEAL]: 24, [SCOPE_CHANGE]: 8 },
  { [DAY]: new Date(2026, 5, 5), [REMAINING]: 34, [IDEAL]: 20, [SCOPE_CHANGE]: 0 },
  { [DAY]: new Date(2026, 5, 8), [REMAINING]: 28, [IDEAL]: 16, [SCOPE_CHANGE]: 0 },
  { [DAY]: new Date(2026, 5, 9), [REMAINING]: 21, [IDEAL]: 12, [SCOPE_CHANGE]: 0 },
  { [DAY]: new Date(2026, 5, 10), [REMAINING]: 14, [IDEAL]: 8, [SCOPE_CHANGE]: 0 },
  { [DAY]: new Date(2026, 5, 11), [REMAINING]: 7, [IDEAL]: 4, [SCOPE_CHANGE]: 0 },
  { [DAY]: new Date(2026, 5, 12), [REMAINING]: 2, [IDEAL]: 0, [SCOPE_CHANGE]: 0 },
];

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[DAY].getTime() - b[DAY].getTime());
const days = rows.map((d) => d[DAY]);
const remaining = rows.map((d) => d[REMAINING]);
const ideal = rows.map((d) => d[IDEAL]);
const formatDay = (d: Date) => d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });

// Non-working days: a gap of more than one calendar day between consecutive rows
const gaps = rows.slice(1).flatMap((row, i) => {
  const before = days[i];
  const skipped = Math.round((row[DAY].getTime() - before.getTime()) / DAY_MS) - 1;
  if (skipped < 1) return [];
  const first = new Date(before.getTime() + DAY_MS).toLocaleDateString("en-US", { weekday: "short" });
  const last = new Date(before.getTime() + skipped * DAY_MS).toLocaleDateString("en-US", { weekday: "short" });
  return [{ from: before, to: row[DAY], label: skipped > 1 ? `${first}–${last}` : first }];
});

const unit = REMAINING.match(/\(([^)]+)\)\s*$/)?.[1] ?? "";
const scopeName = SCOPE_CHANGE.replace(/\s*\([^)]*\)\s*$/, "");
const scopeEvents = rows
  .filter((d) => d[SCOPE_CHANGE])
  .map((d) => ({ day: d[DAY], label: `${scopeName} ${d[SCOPE_CHANGE] > 0 ? "+" : "−"}${Math.abs(d[SCOPE_CHANGE])} ${unit}` }));

const yMax = Math.max(...remaining, ...ideal) * (1 + Y_PAD_SHARE);
const totalAdded = rows.reduce((s, d) => s + (d[SCOPE_CHANGE] || 0), 0);
const TITLE = "burndown-sprint · javascript · muix · anyplot.ai";
const subtitle = `${remaining[0]} ${unit} committed · ${totalAdded >= 0 ? "+" : "−"}${Math.abs(totalAdded)} added during the sprint · ${remaining[remaining.length - 1]} left on ${formatDay(days[days.length - 1])} · red: behind the ideal line, green: ahead`;
const TITLE_H = 80;

function WeekendBands() {
  const xScale = useXScale();
  const area = useDrawingArea();
  const half = xScale.bandwidth() / 2;
  return (
    <g>
      {gaps.map((g) => (
        <g key={g.from.getTime()}>
          <rect x={xScale(g.from) + half} y={area.top} width={xScale(g.to) - xScale(g.from)} height={area.height} fill={t.inkSoft} fillOpacity={0.1} />
          <text x={xScale(g.from) + half + (xScale(g.to) - xScale(g.from)) / 2} y={area.top + area.height - 12} textAnchor="middle" fontSize={14} fill={t.inkSoft}>
            {g.label}
          </text>
        </g>
      ))}
    </g>
  );
}

// Between consecutive days the actual line holds its value while the ideal falls
// linearly; the gap is split where the two cross and colored by its sign
function ScheduleFill() {
  const xScale = useXScale();
  const yScale = useYScale();
  const half = xScale.bandwidth() / 2;
  const pieces: { points: number[][]; behind: boolean }[] = [];
  for (let i = 0; i < rows.length - 1; i += 1) {
    const x0 = xScale(days[i]) + half;
    const x1 = xScale(days[i + 1]) + half;
    const a = remaining[i] - ideal[i];
    const b = remaining[i] - ideal[i + 1];
    if (a * b < 0) {
      const xc = x0 + (a / (a - b)) * (x1 - x0);
      pieces.push({ points: [[x0, remaining[i]], [xc, remaining[i]], [x0, ideal[i]]], behind: a > 0 });
      pieces.push({ points: [[xc, remaining[i]], [x1, remaining[i]], [x1, ideal[i + 1]]], behind: b > 0 });
    } else {
      pieces.push({ points: [[x0, remaining[i]], [x1, remaining[i]], [x1, ideal[i + 1]], [x0, ideal[i]]], behind: a + b > 0 });
    }
  }
  return (
    <g>
      {pieces.map((p, i) => (
        <polygon
          key={i}
          points={p.points.map(([x, v]) => `${x},${yScale(v)}`).join(" ")}
          fill={p.behind ? BEHIND : AHEAD}
          fillOpacity={STATUS_OPACITY}
        />
      ))}
    </g>
  );
}

function ScopeMarkers() {
  const xScale = useXScale();
  const area = useDrawingArea();
  const half = xScale.bandwidth() / 2;
  return (
    <g>
      {scopeEvents.map((e) => (
        <g key={e.day.getTime()}>
          <line x1={xScale(e.day) + half} x2={xScale(e.day) + half} y1={area.top} y2={area.top + area.height} stroke={t.ink} strokeWidth={2} strokeDasharray="3 5" />
          <text x={xScale(e.day) + half + 10} y={area.top + 22} fontSize={15} fontWeight={600} fill={t.ink}>
            {e.label}
          </text>
        </g>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column", background: t.pageBg }}>
      <div style={{ height: TITLE_H, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, paddingTop: 10 }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <ChartsDataProvider
        width={width}
        height={height - TITLE_H - 44}
        margin={{ top: 8, bottom: 12, left: 24, right: 40 }}
        series={[
          { type: "line", id: "actual", label: REMAINING, data: remaining, color: t.palette[0], curve: "stepAfter", strictStepCurve: true, showMark: true, shape: "circle" },
          { type: "line", id: "ideal", label: IDEAL, data: ideal, color: t.inkSoft, curve: "linear", showMark: false },
        ]}
        xAxis={[
          {
            scaleType: "band",
            data: days,
            label: DAY,
            height: 64,
            tickPlacement: "middle",
            valueFormatter: formatDay,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: yMax,
            label: REMAINING,
            width: 80,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        skipAnimation
      >
        <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "end" }} legendDirection="horizontal">
          <ChartsLegend
            sx={{
              fontSize: 15,
              color: t.inkSoft,
              pr: 5,
              '& [data-series="ideal"] .MuiChartsLabelMark-root': { width: 28 },
              '& [data-series="ideal"] .MuiChartsLabelMark-fill': { strokeDasharray: "6 4", strokeLinecap: "butt" },
            }}
          />
          <ChartsSurface
            sx={{
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
              "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
              '& .MuiLineChart-line[data-series="actual"]': { strokeWidth: 3.5 },
              '& .MuiLineChart-line[data-series="ideal"]': { strokeWidth: 2.5, strokeDasharray: "10 7" },
              "& .MuiLineChart-mark": { r: 6, strokeWidth: 2.5 },
            }}
          >
            <WeekendBands />
            <ChartsGrid horizontal />
            <ScheduleFill />
            <LinePlot skipAnimation />
            <ScopeMarkers />
            <MarkPlot skipAnimation />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
