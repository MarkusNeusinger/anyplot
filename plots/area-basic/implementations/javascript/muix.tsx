// anyplot.ai
// area-basic: Basic Area Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-08-20

import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const X = "Date"; // role: x
const Y = "Daily Visitors"; // role: y

// Data: replace this block with your own records, one object per row
const data = (() => {
  let s = 42 >>> 0;
  const rand = () => {
    s = (Math.imul(1664525, s) + 1013904223) >>> 0;
    return s / 4294967295;
  };

  const dayCount = 60;
  const startDate = new Date(2026, 0, 5);
  return Array.from({ length: dayCount }, (_, i) => {
    const d = new Date(startDate);
    d.setDate(d.getDate() + i);
    const trend = 4100 + i * 34;
    const isWeekend = d.getDay() === 0 || d.getDay() === 6;
    const seasonality = isWeekend ? -950 : 180;
    const noise = (rand() - 0.5) * 600;
    return {
      [X]: d,
      [Y]: Math.max(0, Math.round(trend + seasonality + noise)),
    };
  });
})();

// Plot: reads only data and the constants above
const dates = data.map((d) => d[X]);
const visitors = data.map((d) => d[Y]);

const TITLE = "Website Visitors · area-basic · javascript · muix · anyplot.ai";
const TITLE_H = 58;
const AREA_GRADIENT_ID = "areaBasicFillGradient";

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          px: "40px",
          pt: "10px",
        }}
      >
        <Typography
          sx={{
            color: t.ink,
            fontSize: "25px",
            fontWeight: 600,
            lineHeight: 1,
          }}
        >
          {TITLE}
        </Typography>
      </Box>

      <LineChart
        width={width}
        height={height - TITLE_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        xAxis={[
          {
            data: dates,
            scaleType: "time",
            valueFormatter: (v: Date) =>
              v.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            tickNumber: 8,
            height: 68,
            label: X,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            width: 84,
            label: Y,
            valueFormatter: (v: number) => `${(v / 1000).toFixed(1)}k`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "visitors",
            data: visitors,
            label: Y,
            color: t.palette[0],
            area: true,
            showMark: false,
            curve: "linear",
            baseline: 0,
          },
        ]}
        margin={{ top: 20, bottom: 20, left: 24, right: 40 }}
        sx={{
          "& .MuiLineChart-area": { fill: `url(#${AREA_GRADIENT_ID})` },
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <defs>
          <linearGradient id={AREA_GRADIENT_ID} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={t.palette[0]} stopOpacity={0.55} />
            <stop offset="100%" stopColor={t.palette[0]} stopOpacity={0.04} />
          </linearGradient>
        </defs>
      </LineChart>
    </Box>
  );
}
