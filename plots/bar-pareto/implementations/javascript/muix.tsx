// anyplot.ai
// bar-pareto: Pareto Chart with Cumulative Line
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 86/100 | Updated: 2026-10-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { LinePlot, MarkPlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const PARETO_THRESHOLD = 80;
const PERCENT_MAX = 100;
const COUNT_PAD_SHARE = 0.18;

// Columns: set these to your data's column names
const CATEGORY = "Defect type"; // role: category
const COUNT = "Defect count"; // role: count

// Data: replace this block with your own records, one object per row
const data = [
  { [CATEGORY]: "Scratches", [COUNT]: 412 },
  { [CATEGORY]: "Dents", [COUNT]: 298 },
  { [CATEGORY]: "Cracks", [COUNT]: 187 },
  { [CATEGORY]: "Warping", [COUNT]: 143 },
  { [CATEGORY]: "Discoloration", [COUNT]: 98 },
  { [CATEGORY]: "Missing Part", [COUNT]: 76 },
  { [CATEGORY]: "Wrong Size", [COUNT]: 54 },
  { [CATEGORY]: "Surface Flaw", [COUNT]: 32 },
];

// Plot: reads only data and the constants above
const sorted = [...data].sort((a, b) => b[COUNT] - a[COUNT]);
const categories = sorted.map((d) => d[CATEGORY]);
const counts = sorted.map((d) => d[COUNT]);
const total = counts.reduce((a, b) => a + b, 0);

let running = 0;
const cumPercent = counts.map((c) => {
  running += c;
  return Number(((running / total) * PERCENT_MAX).toFixed(1));
});

const countMax = Math.ceil(counts[0] * (1 + COUNT_PAD_SHARE));
const vitalCount = cumPercent.findIndex((p) => p >= PARETO_THRESHOLD) + 1;
const cumLabel = "Cumulative share (%)";
const TITLE = "bar-pareto · javascript · muix · anyplot.ai";
const SUBTITLE = `${COUNT}: ${total.toLocaleString("en-US")} · ${CATEGORY}: ${categories.length} · Top ${vitalCount} reach ${cumPercent[vitalCount - 1]}%`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const HEADER_H = 104;
  const chartH = height - HEADER_H;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        boxSizing: "border-box",
      }}
    >
      <Box
        sx={{
          height: HEADER_H,
          pt: "14px",
          px: "48px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          boxSizing: "border-box",
        }}
      >
        <Typography
          sx={{ color: t.ink, fontSize: 22, fontWeight: 600, lineHeight: 1.25 }}
        >
          {TITLE}
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 15, mt: "4px" }}>
          {SUBTITLE}
        </Typography>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "28px",
            mt: "6px",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Box
              sx={{
                width: 18,
                height: 12,
                bgcolor: t.palette[0],
                borderRadius: "2px",
              }}
            />
            <Typography sx={{ color: t.inkSoft, fontSize: 14 }}>
              {COUNT}
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Box
              sx={{
                width: 22,
                height: 3,
                bgcolor: t.palette[1],
                borderRadius: "2px",
              }}
            />
            <Typography sx={{ color: t.inkSoft, fontSize: 14 }}>
              {cumLabel}
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Box
              sx={{
                width: 22,
                height: 0,
                borderTop: `2.5px dashed ${t.amber}`,
              }}
            />
            <Typography sx={{ color: t.inkSoft, fontSize: 14 }}>
              {`${PARETO_THRESHOLD}% threshold`}
            </Typography>
          </Box>
        </Box>
      </Box>

      <ChartsContainer
        width={width}
        height={chartH}
        series={[
          {
            type: "bar",
            id: "defect-counts",
            yAxisId: "counts",
            data: counts,
            label: COUNT,
            color: t.palette[0],
          },
          {
            type: "line",
            id: "cum-line",
            yAxisId: "percent",
            data: cumPercent,
            label: cumLabel,
            color: t.palette[1],
            showMark: true,
            shape: "circle",
            curve: "linear",
          },
        ]}
        xAxis={[
          {
            id: "x",
            scaleType: "band",
            data: categories,
            categoryGapRatio: 0.35,
            height: 68,
            label: CATEGORY,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "counts",
            position: "left",
            min: 0,
            max: countMax,
            width: 84,
            label: COUNT,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
          {
            id: "percent",
            position: "right",
            min: 0,
            max: PERCENT_MAX,
            width: 88,
            valueFormatter: (v: number) => `${v}%`,
            label: cumLabel,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        margin={{ top: 20, right: 36, bottom: 24, left: 36 }}
        skipAnimation
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
          "& .MuiLineChart-line": { strokeWidth: 3 },
        }}
      >
        <ChartsGrid horizontal />
        <BarPlot borderRadius={3} skipAnimation />
        <LinePlot skipAnimation />
        <MarkPlot skipAnimation />
        <ChartsReferenceLine
          y={PARETO_THRESHOLD}
          axisId="percent"
          lineStyle={{
            stroke: t.amber,
            strokeDasharray: "8 5",
            strokeWidth: 2.5,
          }}
        />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId="counts" />
        <ChartsYAxis axisId="percent" />
      </ChartsContainer>
    </Box>
  );
}
