// anyplot.ai
// drawdown-basic: Drawdown Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 89/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const LOSS = t.palette[4]; // drawdown in the loss red, as the Notes ask
const VALUE_COLOR = t.palette[0]; // first palette position not taken by the loss colour
const RECOVERY_MARK_SHARE = 0.1; // recoveries are marked for drawdowns at least this share as deep as the maximum
const Y_PAD = 0.05; // share of each axis span left free beyond the outermost values
const ZERO_PAD = 0.08; // share of the deepest drawdown left free above the zero line, where the period is named
const DATE_TICKS = 8; // target count of date ticks; the time scale rounds the step to whole calendar units
// The value series gets its own panel above the drawdown on the same date axis, so the two lines never cross
const VALUE_PANEL_SHARE = 0.3; // share of the chart height for the value panel
const Y_AXIS_W = 84; // both panels share this axis width and the margins, so their dates line up
const PANEL_MARGIN_X = 24;
const DAY_MS = 86400000;
const TITLE = "drawdown-basic · javascript · muix · anyplot.ai";
const HEADER_H = 84;
const FOOT_H = 16;

// Columns: set these to your data's column names
const DATE = "Date"; // role: date
const NAV = "NAV per share (USD)"; // role: value

// Data: replace this block with your own records, one object per row
// Simulated daily NAV of a fund over 500 trading days: a mild correction, a sharp bear-market crash,
// a strong recovery and a calm finish
const data = (() => {
  const dates = [];
  const cursor = new Date(2024, 0, 2);
  while (dates.length < 500) {
    if (cursor.getDay() !== 0 && cursor.getDay() !== 6) dates.push(new Date(cursor));
    cursor.setDate(cursor.getDate() + 1);
  }
  let state = 42;
  let nav = 100;
  return dates.map((date, i) => {
    state = (state * 1103515245 + 12345) % 2147483648;
    const drift = i < 120 ? 0.0004 : i < 150 ? -0.0045 : i < 260 ? 0.0006 : i < 300 ? -0.0105 : i < 410 ? 0.0068 : 0.0004;
    nav *= 1 + drift + (state / 2147483648 - 0.5) * 0.018;
    return { [DATE]: date, [NAV]: Math.round(nav * 100) / 100 };
  });
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => Number.isFinite(d[NAV])).sort((a, b) => a[DATE] - b[DATE]);
const dates = rows.map((d) => d[DATE]);
const values = rows.map((d) => d[NAV]);

// Drawdown from the running maximum, in percent: 0 at every new high
let runningMax = -Infinity;
const drawdown = values.map((v) => {
  runningMax = Math.max(runningMax, v);
  return ((v - runningMax) / runningMax) * 100;
});

// Drawdown episodes: from the last high before the curve leaves zero to the first return to zero
const episodes = [];
let open = null;
drawdown.forEach((dd, i) => {
  if (dd < 0 && open === null) open = { peak: Math.max(0, i - 1), trough: i, recovery: -1 };
  if (open !== null && dd < drawdown[open.trough]) open.trough = i;
  if (dd === 0 && open !== null) {
    open.recovery = i;
    episodes.push(open);
    open = null;
  }
});
if (open !== null) episodes.push(open);

const worst = episodes.reduce((a, b) => (drawdown[b.trough] < drawdown[a.trough] ? b : a));
const maxDrawdown = drawdown[worst.trough];
// The marking threshold is rounded once, so the legend states exactly the rule the marks follow
const markDepth = Math.round(-maxDrawdown * RECOVERY_MARK_SHARE * 10) / 10;
const marked = episodes.filter((e) => e.recovery > -1 && -drawdown[e.trough] >= markDepth);

const fmtDate = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" }).format;
const declineDays = Math.round((dates[worst.trough] - dates[worst.peak]) / DAY_MS);
const recoveryText =
  worst.recovery > -1
    ? `recovery ${Math.round((dates[worst.recovery] - dates[worst.trough]) / DAY_MS)} days (to ${fmtDate(dates[worst.recovery])})`
    : "not yet recovered";
const stats = `Max drawdown ${maxDrawdown.toFixed(1)}% · decline ${declineDays} days (${fmtDate(dates[worst.peak])} → ${fmtDate(dates[worst.trough])}) · ${recoveryText}`;

const yMin = maxDrawdown * (1 + Y_PAD);
const yMax = -maxDrawdown * ZERO_PAD;
const valueLow = Math.min(...values);
const valueHigh = Math.max(...values);
const valueMin = valueLow - (valueHigh - valueLow) * Y_PAD;
const valueMax = valueHigh + (valueHigh - valueLow) * Y_PAD;

// Marker-only series: a value at the trough and at each marked recovery, null elsewhere
const recoveryIdx = new Set(marked.map((e) => e.recovery));
const troughSeries = drawdown.map((dd, i) => (i === worst.trough ? dd : null));
const recoverySeries = drawdown.map((dd, i) => (recoveryIdx.has(i) ? dd : null));

// The maximum drawdown period, shaded in both panels; the drawdown panel also names it and labels the trough
function MaxDrawdownPeriod({ annotate }: { annotate: boolean }) {
  const xScale = useXScale();
  const yScale = useYScale();
  const { left, top, width, height } = useDrawingArea();
  const x0 = xScale(dates[worst.peak]);
  const x1 = xScale(dates[worst.recovery > -1 ? worst.recovery : dates.length - 1]);
  const tx = xScale(dates[worst.trough]);
  const ty = yScale(maxDrawdown);
  const troughRight = tx < left + width * 0.7;
  return (
    <g>
      <rect x={x0} y={top} width={x1 - x0} height={height} fill={t.inkSoft} fillOpacity={0.08} />
      {annotate && (
        <g>
          <text x={x0 + 10} y={top + 18} fontSize={14} fill={t.inkSoft}>
            Max drawdown period
          </text>
          <text x={troughRight ? tx + 16 : tx - 16} y={ty + 5} textAnchor={troughRight ? "start" : "end"} fontSize={15} fontWeight={600} fill={t.ink}>
            {`${maxDrawdown.toFixed(1)}% on ${fmtDate(dates[worst.trough])}`}
          </text>
        </g>
      )}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const valuePanelH = Math.round((height - HEADER_H - FOOT_H) * VALUE_PANEL_SHARE);
  const drawdownPanelH = height - HEADER_H - FOOT_H - valuePanelH;
  const axisStyle = {
    "& .MuiChartsAxis-line": { stroke: t.inkSoft },
    "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
    "& .MuiChartsGrid-line": { stroke: t.grid },
  };
  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "22px 40px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{stats}</div>
      </div>
      <LineChart
        width={width}
        height={valuePanelH}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        margin={{ top: 12, right: PANEL_MARGIN_X, bottom: 4, left: PANEL_MARGIN_X }}
        xAxis={[{ data: dates, scaleType: "time", position: "none" }]}
        yAxis={[
          {
            id: "value",
            label: NAV,
            min: valueMin,
            max: valueMax,
            tickNumber: 4,
            width: Y_AXIS_W,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "value",
            data: values,
            label: NAV,
            color: VALUE_COLOR,
            showMark: false,
          },
        ]}
        sx={{ '& .MuiLineChart-line[data-series="value"]': { strokeWidth: 2.5 }, ...axisStyle }}
      >
        <MaxDrawdownPeriod annotate={false} />
      </LineChart>
      <LineChart
        width={width}
        height={drawdownPanelH}
        skipAnimation
        grid={{ horizontal: true }}
        margin={{ top: 8, right: PANEL_MARGIN_X, bottom: 8, left: PANEL_MARGIN_X }}
        xAxis={[
          {
            data: dates,
            scaleType: "time",
            label: DATE,
            height: 64,
            tickNumber: DATE_TICKS,
            valueFormatter: (d) => d.toLocaleDateString("en-US", { month: "short", year: "numeric" }),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "drawdown",
            min: yMin,
            max: yMax,
            label: "Drawdown from running peak (%)",
            width: Y_AXIS_W,
            valueFormatter: (v) => `${v.toFixed(0)}%`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "drawdown",
            yAxisId: "drawdown",
            data: drawdown,
            label: "Drawdown (%)",
            color: LOSS,
            area: true,
            showMark: false,
            valueFormatter: (v) => `${v.toFixed(1)}%`,
          },
          {
            id: "trough",
            yAxisId: "drawdown",
            data: troughSeries,
            label: "Maximum drawdown",
            color: LOSS,
            showMark: true,
            shape: "circle",
            labelMarkType: "circle",
          },
          {
            id: "recovery",
            yAxisId: "drawdown",
            data: recoverySeries,
            label: `Recovery from a drawdown of ${markDepth.toFixed(1)}% or more`,
            color: t.ink,
            showMark: true,
            shape: "circle",
            labelMarkType: "circle",
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "end" },
            sx: { fontSize: 15, color: t.inkSoft, pr: 4 },
          },
        }}
        sx={{
          '& .MuiLineChart-area[data-series="drawdown"]': { fillOpacity: 0.35 },
          '& .MuiLineChart-line[data-series="drawdown"]': { strokeWidth: 2.5 },
          '& .MuiLineChart-mark[data-series="trough"]': { r: 8, fill: LOSS, stroke: t.pageBg, strokeWidth: 2.5 },
          '& .MuiLineChart-mark[data-series="recovery"]': { r: 7, fill: t.ink, stroke: t.pageBg, strokeWidth: 2.5 },
          ...axisStyle,
        }}
      >
        <ChartsReferenceLine y={0} axisId="drawdown" lineStyle={{ stroke: t.ink, strokeWidth: 1.5 }} />
        <MaxDrawdownPeriod annotate />
      </LineChart>
    </div>
  );
}
