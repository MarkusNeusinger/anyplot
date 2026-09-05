// anyplot.ai
// line-filled: Filled Line Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-05
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG PRNG — no fetch, no Math.random) ----
let seed = 11;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const DAYS = 60;
const startDate = new Date(2026, 0, 5); // Mon Jan 5, 2026
const dates: Date[] = [];
const visitors: number[] = [];
const baseVisitors = 3200; // pre-launch daily unique visitors
const dailyGrowth = 0.013; // sustained lift from a content-marketing push

for (let i = 0; i < DAYS; i++) {
  const date = new Date(startDate);
  date.setDate(startDate.getDate() + i);
  dates.push(date);

  const weekday = date.getDay();
  const weekendDip = weekday === 0 || weekday === 6 ? 0.7 : 1;
  const trend = 1 + i * dailyGrowth;
  const noise = 1 + (rand() - 0.5) * 0.16;
  visitors.push(Math.round(baseVisitors * trend * weekendDip * noise));
}

const TITLE = "Website Traffic Growth · line-filled · javascript · muix · anyplot.ai";

// --- Chart (default-exported component — the harness mounts it) -----------
export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const titleSize = TITLE.length > 67 ? Math.max(14, Math.round((22 * 67) / TITLE.length)) : 22;

  const TITLE_H = 64;
  const chartH = H - TITLE_H;
  // MUI X's y-axis `label` offsets itself from a hardcoded tickFontSize guess
  // rather than the tick labels' real measured width, so a 4-digit tick
  // ("3,000") collides with it. A hand-rotated label in its own flex column
  // sidesteps that and gives predictable, collision-free spacing.
  const yLabelWidth = 40;
  const chartW = W - yLabelWidth;

  return (
    <Box
      sx={{
        width: W,
        height: H,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "'Roboto', 'Helvetica Neue', Arial, sans-serif",
        boxSizing: "border-box",
      }}
    >
      <Box sx={{ height: TITLE_H, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Typography sx={{ color: t.ink, fontSize: titleSize, fontWeight: 600 }}>{TITLE}</Typography>
      </Box>

      <Box sx={{ display: "flex", flexDirection: "row", height: chartH }}>
        <Box sx={{ width: yLabelWidth, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Typography sx={{ fontSize: 15, color: t.ink, whiteSpace: "nowrap", transform: "rotate(-90deg)" }}>
            Unique Visitors
          </Typography>
        </Box>

        <LineChart
          width={chartW}
          height={chartH}
          skipAnimation
          series={[
            {
              id: "visitors",
              data: visitors,
              showMark: false,
              area: true,
              color: t.palette[0],
              curve: "monotoneX",
              valueFormatter: (v: number | null) => (v == null ? "" : `${v.toLocaleString("en-US")} visitors`),
            },
          ]}
          xAxis={[
            {
              data: dates,
              scaleType: "time",
              label: "Date",
              valueFormatter: (d: Date) => d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
              tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
              labelStyle: { fontSize: 15, fill: t.ink },
            },
          ]}
          yAxis={[
            {
              valueFormatter: (v: number) => v.toLocaleString("en-US"),
              tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
            },
          ]}
          grid={{ horizontal: true }}
          slotProps={{ legend: { hidden: true } }}
          margin={{ top: 24, right: 40, bottom: 64, left: 66 }}
          sx={{
            "& .MuiLineElement-root": { strokeWidth: 3 },
            "& .MuiAreaElement-root": { fill: t.palette[0], fillOpacity: 0.35 },
            "& .MuiChartsAxis-line": { stroke: t.inkSoft, strokeOpacity: 0.4 },
            "& .MuiChartsAxis-tick": { stroke: t.inkSoft, strokeOpacity: 0.4 },
            "& .MuiChartsGrid-line": { stroke: t.grid },
          }}
        />
      </Box>
    </Box>
  );
}
