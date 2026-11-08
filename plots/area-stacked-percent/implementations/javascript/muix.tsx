// anyplot.ai
// area-stacked-percent: 100% Stacked Area Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-09-02
import { LineChart } from "@mui/x-charts/LineChart";
import { useDrawingArea, useXScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "area-stacked-percent · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 44;
const Y_LABEL = "Share of total (%)";
const MAJORITY = 0.5; // a share below this ends a category's majority of the total

// Columns: set these to your data's column names
const YEAR = "Year"; // role: time
const SOURCE = "Source"; // role: category
const GENERATION = "Generation (TWh)"; // role: value

// Data: replace this block with your own records, one object per row
// Illustrative electricity generation mix, 2010 to 2024: solar and wind grow
// quadratically along a falling cost curve, hydro and nuclear stay roughly flat,
// fossil declines linearly
const data = Array.from({ length: 15 }, (_, i) => [
  { [YEAR]: 2010 + i, [SOURCE]: "Solar", [GENERATION]: 4 + Math.round(i * i * 1.6) },
  { [YEAR]: 2010 + i, [SOURCE]: "Wind", [GENERATION]: 15 + Math.round(i * i * 0.9) },
  { [YEAR]: 2010 + i, [SOURCE]: "Hydro", [GENERATION]: 150 + i * 3 },
  { [YEAR]: 2010 + i, [SOURCE]: "Nuclear", [GENERATION]: 260 - i * 2 },
  { [YEAR]: 2010 + i, [SOURCE]: "Fossil", [GENERATION]: 680 - i * 18 },
]).flat();

// Plot: reads only data and the constants above
const years = [...new Set(data.map((d) => d[YEAR]))].sort((a, b) => a - b);
const sources = [...new Set(data.map((d) => d[SOURCE]))];
const valueByKey = new Map(data.map((d) => [`${d[SOURCE]}|${d[YEAR]}`, d[GENERATION]]));
const values = sources.map((s) => years.map((y) => valueByKey.get(`${s}|${y}`) ?? null));
const totals = years.map((_, k) => values.reduce((sum, row) => sum + (row[k] ?? 0), 0));
const shares = values.map((row) => row.map((v, k) => (v == null || !totals[k] ? null : v / totals[k])));
const UNIT = GENERATION.match(/\(([^)]+)\)/)?.[1] ?? "";

// Focal point: the first year in which the category leading the first year loses
// its majority, drawn only when it starts with a majority and later loses it
const leader = shares.reduce((best, row, g) => ((row[0] ?? 0) > (shares[best][0] ?? 0) ? g : best), 0);
const lossIdx = (shares[leader][0] ?? 0) >= MAJORITY ? shares[leader].findIndex((v) => v != null && v < MAJORITY) : -1;
const milestone =
  lossIdx > 0
    ? { year: years[lossIdx], text: `${years[lossIdx]}: ${sources[leader]} falls below ${Math.round(MAJORITY * 100)}% of the total` }
    : null;

const SUBTITLE = `${years.length} years, ${years[0]}–${years[years.length - 1]} · ${sources.length} categories · each year's total = 100%`;

// Dashed marker at the milestone year, labelled above the drawing area on the page
function MilestoneMarker() {
  const xScale = useXScale();
  const { top, height } = useDrawingArea();
  if (!milestone) return null;
  const x = xScale(milestone.year);
  return (
    <g>
      <line x1={x} x2={x} y1={top - 6} y2={top + height} stroke={t.ink} strokeWidth={1.75} strokeDasharray="6 4" />
      <text x={x} y={top - 14} textAnchor="middle" fontSize={15} fontWeight={600} fill={t.ink}>
        {milestone.text}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, px: "40px", pt: "18px", boxSizing: "border-box" }}>
        <Typography sx={{ color: t.ink, fontSize: "22px", fontWeight: 600, lineHeight: 1.2 }}>
          {TITLE}
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: "15px", lineHeight: 1.2, mt: "8px" }}>
          {SUBTITLE}
        </Typography>
      </Box>
      <LineChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true }}
        xAxis={[
          {
            data: years,
            scaleType: "point",
            label: YEAR,
            valueFormatter: (v: number) => `${v}`,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: 1,
            label: Y_LABEL,
            width: 76,
            valueFormatter: (v: number) => `${Math.round(v * 100)}%`,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={sources.map((source, g) => ({
          id: `source-${g}`,
          label: source,
          data: values[g],
          color: t.palette[g],
          stack: "total",
          stackOffset: "expand" as const,
          area: true,
          showMark: false,
          labelMarkType: "square" as const,
          valueFormatter: (v: number | null, { dataIndex }: { dataIndex: number }) =>
            v == null ? "" : `${Math.round((shares[g][dataIndex] ?? 0) * 100)}% · ${v.toLocaleString("en-US")} ${UNIT}`.trim(),
        }))}
        margin={{ top: 40, right: 48, bottom: 8, left: 24 }}
        slotProps={{
          legend: {
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 15, color: t.ink },
          },
        }}
        sx={{
          "& .MuiLineChart-area": { fillOpacity: 0.9, filter: "none" },
          "& .MuiLineChart-line": { strokeWidth: 2 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <MilestoneMarker />
      </LineChart>
    </Box>
  );
}
