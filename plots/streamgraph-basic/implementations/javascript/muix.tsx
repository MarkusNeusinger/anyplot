// anyplot.ai
// streamgraph-basic: Basic Stream Graph
// Library: muix 9.17.0 | JavaScript 22.23.1
// Quality: 88/100 | Created: 2026-08-05
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const Y_PAD_SHARE = 0.04; // room above and below the stream

// Columns: set these to your data's column names
const MONTH = "Month"; // role: time
const GENRE = "Genre"; // role: category
const HOURS = "Streaming hours (thousands)"; // role: value

// Data: replace this block with your own records, one object per row
// Monthly streaming hours by music genre over two years: Electronic and Hip-Hop
// grow, Rock cools off, Jazz and Classical decline slowly, Pop stays flat
const data = (() => {
  let seed = 42;
  const genres = [
    { name: "Pop", base: 380, amp: 55, freq: 0.55, phase: 0.4, trend: 0.4 },
    { name: "Hip-Hop", base: 300, amp: 70, freq: 0.45, phase: 2.1, trend: 5.5 },
    { name: "Electronic", base: 190, amp: 60, freq: 0.65, phase: 4.0, trend: 8.5 },
    { name: "Rock", base: 260, amp: 45, freq: 0.35, phase: 1.2, trend: -3.5 },
    { name: "Jazz", base: 140, amp: 25, freq: 0.5, phase: 3.3, trend: -2.0 },
    { name: "Classical", base: 100, amp: 18, freq: 0.4, phase: 5.1, trend: -1.2 },
  ];
  const rows: { [k: string]: Date | string | number }[] = [];
  for (const g of genres) {
    for (let i = 0; i < 24; i += 1) {
      seed = (seed * 1103515245 + 12345) & 0x7fffffff;
      const wave = Math.sin(i * g.freq * 0.5 + g.phase) * g.amp;
      const noise = (seed / 0x7fffffff - 0.5) * g.amp * 0.3;
      rows.push({
        [MONTH]: new Date(2024, i, 1),
        [GENRE]: g.name,
        [HOURS]: Math.round(Math.max(30, g.base + g.trend * i + wave + noise)),
      });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
// Layers are stacked inside-out and mirrored about the middle axis (silhouette), so only their thickness carries a value
const months = [...new Set(data.map((d) => (d[MONTH] as Date).getTime()))].sort((a, b) => a - b).map((ms) => new Date(ms));
const genres = [...new Set(data.map((d) => d[GENRE] as string))];
const series = genres.map((genre, i) => ({
  id: `genre-${i}`,
  label: genre,
  color: t.palette[i],
  data: months.map(
    (m) => (data.find((d) => d[GENRE] === genre && (d[MONTH] as Date).getTime() === m.getTime())?.[HOURS] as number) ?? null,
  ),
  area: true,
  stack: "stream",
  stackOrder: "insideOut" as const,
  stackOffset: "silhouette" as const,
  curve: "catmullRom" as const,
  showMark: false,
  labelMarkType: "square" as const,
}));
const totals = months.map((_, k) => series.reduce((sum, s) => sum + (s.data[k] ?? 0), 0));
const streamHalf = (Math.max(...totals) / 2) * (1 + Y_PAD_SHARE);

const MONTH_FORMAT: Intl.DateTimeFormatOptions = { month: "short", year: "numeric" };
const TITLE = "streamgraph-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `Layer thickness: ${HOURS} · ${months.length} months, ${months[0].toLocaleDateString("en-US", MONTH_FORMAT)} to ${months[months.length - 1].toLocaleDateString("en-US", MONTH_FORMAT)}`;
const HEADER_H = 76;

export default function Chart() {
  const { width: W, height: H } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box
        sx={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "6px",
        }}
      >
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 15, lineHeight: 1.2 }}>{SUBTITLE}</Typography>
      </Box>
      <LineChart
        width={W}
        height={H - HEADER_H - 40}
        skipAnimation
        series={series}
        margin={{ top: 16, right: 48, bottom: 8, left: 48 }}
        xAxis={[
          {
            scaleType: "point",
            data: months,
            label: MONTH,
            height: 64,
            valueFormatter: (d: Date) => d.toLocaleDateString("en-US", MONTH_FORMAT),
            tickInterval: (d: Date) => d.getMonth() % 3 === 0,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            position: "none",
            min: -streamHalf,
            max: streamHalf,
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: { fontSize: 15, color: t.ink, gap: "20px" },
          },
        }}
        sx={{
          "& .MuiLineChart-area": { fillOpacity: 0.92, filter: "none" },
          "& .MuiLineChart-line": { strokeWidth: 1.5 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      />
    </Box>
  );
}
