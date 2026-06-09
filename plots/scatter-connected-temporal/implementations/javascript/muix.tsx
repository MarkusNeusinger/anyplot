// anyplot.ai
// scatter-connected-temporal: Connected Scatter Plot with Temporal Path
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-09

import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// US Phillips curve: unemployment rate (%) vs. inflation rate (%), 1970–2009
// Data is synthetic-realistic based on US macroeconomic trends
const unemployment = [
  4.9, 5.9, 5.6, 4.9, 5.6, 8.5, 7.7, 7.1, 6.1, 5.8, // 1970-1979
  7.1, 7.6, 9.7, 9.6, 7.5, 7.2, 7.0, 6.2, 5.5, 5.3, // 1980-1989
  5.6, 6.8, 7.5, 6.9, 6.1, 5.6, 5.4, 4.9, 4.5, 4.2, // 1990-1999
  4.0, 4.7, 5.8, 6.0, 5.5, 5.1, 4.6, 4.6, 5.8, 9.3, // 2000-2009
];

const inflation = [
   5.7,  4.4,  3.2,  6.2, 11.0,  9.1,  5.8,  6.5,  7.6, 11.3, // 1970-1979
  13.5, 10.3,  6.2,  3.2,  4.3,  3.6,  1.9,  3.6,  4.1,  4.8, // 1980-1989
   5.4,  4.2,  3.0,  3.0,  2.6,  2.8,  3.0,  2.3,  1.6,  2.2, // 1990-1999
   3.4,  2.8,  1.6,  2.3,  2.7,  3.4,  3.2,  2.9,  3.8, -0.4, // 2000-2009
];

// Decade segments — overlap at boundary indices for seamless path connection
const s1970s = inflation.map((v, i) => (i <= 9 ? v : null));
const s1980s = inflation.map((v, i) => (i >= 9 && i <= 19 ? v : null));
const s1990s = inflation.map((v, i) => (i >= 19 && i <= 29 ? v : null));
const s2000s = inflation.map((v, i) => (i >= 29 ? v : null));

// Title: "Phillips Curve · scatter-connected-temporal · javascript · muix · anyplot.ai" = 79 chars
// Scaled fontsize: round(22 × 67/79) = 19 px
const TITLE_H = 52;

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  return (
    <Box
      sx={{
        width: W,
        height: H,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Typography
        sx={{
          color: t.ink,
          fontSize: 19,
          fontWeight: 500,
          textAlign: "center",
          height: TITLE_H,
          lineHeight: `${TITLE_H}px`,
          flexShrink: 0,
        }}
      >
        Phillips Curve · scatter-connected-temporal · javascript · muix · anyplot.ai
      </Typography>
      <LineChart
        width={W}
        height={H - TITLE_H}
        skipAnimation
        grid={{ horizontal: true, vertical: true }}
        xAxis={[{
          data: unemployment,
          scaleType: "linear",
          label: "Unemployment Rate (%)",
          min: 3.5,
          max: 11.0,
          tickMinStep: 1,
          tickLabelStyle: { fontSize: 14 },
          labelStyle: { fontSize: 16 },
        }]}
        yAxis={[{
          label: "Inflation Rate (%)",
          min: -2,
          max: 15,
          tickMinStep: 2,
          tickLabelStyle: { fontSize: 14 },
          labelStyle: { fontSize: 16 },
        }]}
        series={[
          { data: s1970s, label: "1970s", color: t.palette[0], showMark: true, curve: "linear" },
          { data: s1980s, label: "1980s", color: t.palette[1], showMark: true, curve: "linear" },
          { data: s1990s, label: "1990s", color: t.palette[2], showMark: true, curve: "linear" },
          { data: s2000s, label: "2000s", color: t.palette[3], showMark: true, curve: "linear" },
        ]}
        slotProps={{
          legend: {
            direction: "row",
            position: { vertical: "top", horizontal: "right" },
            itemMarkWidth: 14,
            itemMarkHeight: 14,
            labelStyle: { fontSize: 14 },
          },
        }}
        sx={{
          "& .MuiLineElement-root": { strokeWidth: 2.5 },
        }}
      />
    </Box>
  );
}
