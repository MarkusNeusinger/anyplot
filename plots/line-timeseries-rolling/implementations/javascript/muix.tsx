// anyplot.ai
// line-timeseries-rolling: Time Series with Rolling Average Overlay
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05
import { LineChart } from "@mui/x-charts/LineChart";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG PRNG — no fetch, no Math.random) ----
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const NUM_DAYS = 120;
const WINDOW = 7;
const START_DATE = new Date(2026, 0, 1);

const dates = Array.from({ length: NUM_DAYS }, (_, day) => {
  const d = new Date(START_DATE);
  d.setDate(d.getDate() + day);
  return d;
});

// Daily unique visitors to a blog: weekday/weekend seasonality, a slow
// baseline climb, a two-week traffic surge around a viral post (day 58-74),
// plus day-to-day noise — exactly the volatility a rolling average smooths.
const rawVisitors = dates.map((date, day) => {
  const weekday = date.getDay();
  const weekendDip = weekday === 0 || weekday === 6 ? 0.62 : 1;
  const trend = 1 + day * 0.004;
  const surge = day >= 58 && day <= 74 ? 1 + 0.5 * Math.sin(((day - 58) / 16) * Math.PI) : 1;
  const noise = 1 + (rand() - 0.5) * 0.22;
  const baseline = 2200;
  return Math.max(300, Math.round(baseline * weekendDip * trend * surge * noise));
});

// Trailing WINDOW-day rolling average — null until a full window of raw data
// is available, so the smoothed line starts WINDOW-1 days after the raw one.
const rollingAvg = rawVisitors.map((_, i) => {
  if (i < WINDOW - 1) return null;
  let sum = 0;
  for (let k = i - WINDOW + 1; k <= i; k += 1) sum += rawVisitors[k];
  return Math.round(sum / WINDOW);
});

const TITLE = "Daily Unique Visitors · line-timeseries-rolling · javascript · muix · anyplot.ai";

// --- Chart (default-exported component — the harness mounts it) -----------
export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const titleSize = TITLE.length > 67 ? Math.max(14, Math.round((22 * 67) / TITLE.length)) : 22;
  const padding = { top: 28, right: 40, bottom: 24, left: 40 };
  const titleBlockHeight = 56;
  // MUI X's y-axis `label` offsets itself from a hardcoded tickFontSize guess
  // rather than the tick labels' real measured width, so a 4-digit visitor
  // count collides with it. A hand-rotated label in its own flex column
  // sidesteps that and gives predictable, collision-free spacing.
  const yLabelWidth = 34;
  const chartWidth = size.width - padding.left - padding.right - yLabelWidth;
  const chartHeight = size.height - padding.top - padding.bottom - titleBlockHeight;

  return (
    <Box
      sx={{
        width: size.width,
        height: size.height,
        boxSizing: "border-box",
        padding: `${padding.top}px ${padding.right}px ${padding.bottom}px ${padding.left}px`,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Typography sx={{ fontSize: titleSize, fontWeight: 600, color: "text.primary", mb: "20px", lineHeight: 1 }}>
        {TITLE}
      </Typography>
      <Box sx={{ display: "flex", flexDirection: "row", height: chartHeight }}>
        <Box sx={{ width: yLabelWidth, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Typography sx={{ fontSize: 16, color: "text.secondary", whiteSpace: "nowrap", transform: "rotate(-90deg)" }}>
            Unique Visitors
          </Typography>
        </Box>
        <LineChart
          width={chartWidth}
          height={chartHeight}
          skipAnimation
          series={[
            {
              id: "raw",
              label: "Raw Data",
              data: rawVisitors,
              showMark: false,
              color: t.palette[0],
              valueFormatter: (v) => (v == null ? "" : `${v.toLocaleString("en-US")} visitors`),
            },
            {
              id: "rolling",
              label: `Rolling Average (${WINDOW}-Day)`,
              data: rollingAvg,
              showMark: false,
              color: t.palette[1],
              valueFormatter: (v) => (v == null ? "" : `${v.toLocaleString("en-US")} visitors`),
            },
          ]}
          xAxis={[
            {
              data: dates,
              scaleType: "time",
              label: "Date",
              valueFormatter: (date) => date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
              tickLabelStyle: { fontSize: 14 },
              labelStyle: { fontSize: 16 },
            },
          ]}
          yAxis={[
            {
              valueFormatter: (value) => value.toLocaleString("en-US"),
              tickLabelStyle: { fontSize: 14 },
            },
          ]}
          grid={{ vertical: true, horizontal: true }}
          slotProps={{
            legend: {
              direction: "row",
              labelStyle: { fontSize: 14 },
              itemMarkWidth: 18,
              itemMarkHeight: 10,
              markGap: 8,
            },
          }}
          sx={{
            "& .MuiLineElement-series-raw": { strokeWidth: 1.5, strokeOpacity: 0.5 },
            "& .MuiLineElement-series-rolling": { strokeWidth: 3.5 },
            "& .MuiChartsGrid-line": { strokeDasharray: "4 3" },
          }}
        />
      </Box>
    </Box>
  );
}
