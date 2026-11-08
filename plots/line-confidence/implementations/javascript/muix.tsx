// anyplot.ai
// line-confidence: Line Plot with Confidence Interval
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-05
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { ChartsAxisHighlight } from "@mui/x-charts/ChartsAxisHighlight";
import { LinePlot } from "@mui/x-charts/LineChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const BAND_LABEL = "95 % prediction interval"; // what the band between the two bound columns represents
const BAND_OPACITY = 0.24;
const Y_PAD_SHARE = 0.06; // share of the value range added above the upper and below the lower bound

// Columns: set these to your data's column names
const DATE = "Date"; // role: x
const USERS = "Daily active users (forecast mean)"; // role: y
const LOWER = "Lower bound (users)"; // role: y_lower
const UPPER = "Upper bound (users)"; // role: y_upper

// Data: replace this block with your own records, one object per x value
// A 60-day forecast of daily active users from 1 Jan 2024: a rising trend with a two-week
// cycle, and a 95 % prediction interval whose standard error grows with the horizon.
const data = Array.from({ length: 60 }, (_, i) => {
  const mean = 12000 + 45 * i + 800 * Math.sin((2 * Math.PI * i) / 14);
  const half = 1.96 * (300 + 25 * i);
  return {
    [DATE]: new Date(Date.UTC(2024, 0, 1 + i)).toISOString().slice(0, 10),
    [USERS]: Math.round(mean),
    [LOWER]: Math.round(mean - half),
    [UPPER]: Math.round(mean + half),
  };
});

// Plot: reads only data and the constants above
// ISO dates are read as local midnight, the frame the time axis places its ticks in
const rows = [...data].sort((a, b) => Date.parse(a[DATE]) - Date.parse(b[DATE]));
const n = rows.length;
const dates = rows.map((d) => new Date(`${d[DATE]}T00:00:00`));
const centre = rows.map((d) => d[USERS] ?? null);
const lowers = rows.map((d) => d[LOWER] ?? null);
const uppers = rows.map((d) => d[UPPER] ?? null);

// The band is filled for each run of consecutive x values that has both bounds
const bandRuns: number[][] = [];
rows.forEach((_, i) => {
  if (lowers[i] == null || uppers[i] == null) return;
  const run = bandRuns[bandRuns.length - 1];
  if (run && run[run.length - 1] === i - 1) run.push(i);
  else bandRuns.push([i]);
});

const drawn = [...centre, ...lowers, ...uppers].filter((v) => v != null);
const yLow = Math.min(...drawn);
const yHigh = Math.max(...drawn);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;

const widths = rows.map((_, i) => (lowers[i] != null && uppers[i] != null ? uppers[i] - lowers[i] : null));
const firstWidth = widths.find((w) => w != null);
const lastWidth = [...widths].reverse().find((w) => w != null);

const dayFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" });
const fullFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" });
const numberFormat = new Intl.NumberFormat("en-US");
const boundUnit = LOWER.match(/\(([^)]+)\)/)?.[1];
const unitSuffix = boundUnit ? ` ${boundUnit}` : "";

const TITLE = "line-confidence · javascript · muix · anyplot.ai";
const SUBTITLE =
  `${n} days, ${fullFormat.format(dates[0])} – ${fullFormat.format(dates[n - 1])}` +
  (firstWidth != null
    ? ` · band width ${numberFormat.format(firstWidth)}${unitSuffix} at the start, ${numberFormat.format(lastWidth)}${unitSuffix} at the end`
    : "");
const HEADER_H = 84;
const LEGEND_H = 40;
const LINE_COLOR = t.palette[0];

function Band() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {bandRuns.map((run) => {
        const top = run.map((i) => `${xScale(dates[i])},${yScale(uppers[i])}`);
        const bottom = [...run].reverse().map((i) => `${xScale(dates[i])},${yScale(lowers[i])}`);
        return (
          <path
            key={run[0]}
            d={`M${top.join("L")}L${bottom.join("L")}Z`}
            fill={LINE_COLOR}
            fillOpacity={BAND_OPACITY}
            stroke="none"
          />
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "14px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.6 }}>{SUBTITLE}</Typography>
      </Box>
      <Box
        sx={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: "36px" }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Box sx={{ width: 28, height: 4, borderRadius: 2, bgcolor: LINE_COLOR }} />
          <Typography sx={{ fontSize: 15, color: t.ink }}>{USERS}</Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Box sx={{ width: 28, height: 16, borderRadius: "3px", bgcolor: LINE_COLOR, opacity: BAND_OPACITY }} />
          <Typography sx={{ fontSize: 15, color: t.ink }}>{BAND_LABEL}</Typography>
        </Box>
      </Box>
      <ChartsDataProvider
        width={width}
        height={height - HEADER_H - LEGEND_H}
        margin={{ top: 8, right: 48, bottom: 16, left: 20 }}
        skipAnimation
        series={[
          {
            type: "line",
            id: "centre",
            data: centre,
            label: USERS,
            color: LINE_COLOR,
            curve: "linear",
            showMark: false,
            valueFormatter: (v, { dataIndex }) =>
              v == null
                ? ""
                : `${numberFormat.format(v)} (${numberFormat.format(lowers[dataIndex])} – ${numberFormat.format(uppers[dataIndex])})`,
          },
        ]}
        xAxis={[
          {
            scaleType: "time",
            data: dates,
            domainLimit: "strict",
            tickNumber: 9,
            valueFormatter: (v: Date, context) =>
              context.location === "tick" ? dayFormat.format(v) : fullFormat.format(v),
            label: DATE,
            height: 64,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yLow - yPad,
            max: yHigh + yPad,
            width: 84,
            label: USERS,
            valueFormatter: (v: number) => numberFormat.format(v),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <ChartsWrapper>
          <ChartsSurface
            sx={{
              "& .MuiLineChart-line": { strokeWidth: 3.5 },
              "& .MuiChartsGrid-line": { stroke: t.grid },
            }}
          >
            <ChartsGrid horizontal />
            <Band />
            <LinePlot skipAnimation />
            <ChartsAxisHighlight x="line" />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
          <ChartsTooltip trigger="axis" />
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
