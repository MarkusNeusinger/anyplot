// anyplot.ai
// step-basic: Basic Step Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 85/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const BASELINE = 0; // stock counts start from an empty warehouse
const X_PAD_SHARE = 0.02;
const Y_PAD_SHARE = 0.08;

// Columns: set these to your data's column names
const DAY = "Day of month"; // role: x
const UNITS = "Units in stock"; // role: y

// Data: replace this block with your own records, one object per row
// Daily warehouse inventory: stock holds between restocks and shipments, so each
// reading applies from its day until the next one ("post" steps)
const data = [
  500, 500, 460, 460, 460, 410, 410, 410, 680, 680, 680, 630,
  630, 580, 580, 580, 820, 820, 760, 760, 760, 700, 700, 650,
].map((units, i) => ({ [DAY]: i + 1, [UNITS]: units }));

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[DAY] != null).sort((a, b) => a[DAY] - b[DAY]);
const days = rows.map((d) => d[DAY]);
const units = rows.map((d) => d[UNITS]);
const values = units.filter((v) => v != null);

const xSpan = days[days.length - 1] - days[0];
const yLow = Math.min(BASELINE, ...values);
const yHigh = Math.max(...values);
const xMin = days[0] - xSpan * X_PAD_SHARE;
const xMax = days[days.length - 1] + xSpan * X_PAD_SHARE;
const yMax = yHigh + (yHigh - yLow) * Y_PAD_SHARE;

const TITLE = "step-basic · javascript · muix · anyplot.ai";
const TITLE_H = 64;

export default function Chart() {
  const { width: W, height: H } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600 }}>{TITLE}</Typography>
      </Box>
      <LineChart
        width={W}
        height={H - TITLE_H}
        skipAnimation
        hideLegend
        margin={{ top: 16, right: 48, bottom: 16, left: 24 }}
        grid={{ horizontal: true }}
        xAxis={[
          {
            data: days,
            scaleType: "linear",
            min: xMin,
            max: xMax,
            label: DAY,
            tickNumber: 12,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            min: yLow,
            max: yMax,
            label: UNITS,
            tickNumber: 9,
            width: 80,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        series={[
          {
            id: "stock",
            data: units,
            label: UNITS,
            color: t.palette[0],
            curve: "stepAfter",
            showMark: true,
            shape: "circle",
          },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiLineChart-mark": { strokeWidth: 2.5 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      />
    </Box>
  );
}
