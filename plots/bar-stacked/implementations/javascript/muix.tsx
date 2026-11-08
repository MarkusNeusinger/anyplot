// anyplot.ai
// bar-stacked: Stacked Bar Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { BarChart } from "@mui/x-charts/BarChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "Cloud Costs by Service · bar-stacked · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 44;
const PAD_SHARE = 0.1; // headroom above the tallest stack for its total label

// Columns: set these to your data's column names
const MONTH = "Month"; // role: category
const SERVICE = "Service"; // role: component
const SPEND = "Spend (thousand USD)"; // role: value

// Data: replace this block with your own records, one object per row
// Monthly cloud infrastructure spend by service, first half of the year
const data = [
  { [MONTH]: "Jan", [SERVICE]: "Compute", [SPEND]: 38 },
  { [MONTH]: "Feb", [SERVICE]: "Compute", [SPEND]: 41 },
  { [MONTH]: "Mar", [SERVICE]: "Compute", [SPEND]: 44 },
  { [MONTH]: "Apr", [SERVICE]: "Compute", [SPEND]: 47 },
  { [MONTH]: "May", [SERVICE]: "Compute", [SPEND]: 52 },
  { [MONTH]: "Jun", [SERVICE]: "Compute", [SPEND]: 58 },
  { [MONTH]: "Jan", [SERVICE]: "Database", [SPEND]: 21 },
  { [MONTH]: "Feb", [SERVICE]: "Database", [SPEND]: 22 },
  { [MONTH]: "Mar", [SERVICE]: "Database", [SPEND]: 24 },
  { [MONTH]: "Apr", [SERVICE]: "Database", [SPEND]: 25 },
  { [MONTH]: "May", [SERVICE]: "Database", [SPEND]: 27 },
  { [MONTH]: "Jun", [SERVICE]: "Database", [SPEND]: 29 },
  { [MONTH]: "Jan", [SERVICE]: "Storage", [SPEND]: 14 },
  { [MONTH]: "Feb", [SERVICE]: "Storage", [SPEND]: 15 },
  { [MONTH]: "Mar", [SERVICE]: "Storage", [SPEND]: 16 },
  { [MONTH]: "Apr", [SERVICE]: "Storage", [SPEND]: 17 },
  { [MONTH]: "May", [SERVICE]: "Storage", [SPEND]: 18 },
  { [MONTH]: "Jun", [SERVICE]: "Storage", [SPEND]: 20 },
  { [MONTH]: "Jan", [SERVICE]: "Networking", [SPEND]: 9 },
  { [MONTH]: "Feb", [SERVICE]: "Networking", [SPEND]: 10 },
  { [MONTH]: "Mar", [SERVICE]: "Networking", [SPEND]: 10 },
  { [MONTH]: "Apr", [SERVICE]: "Networking", [SPEND]: 11 },
  { [MONTH]: "May", [SERVICE]: "Networking", [SPEND]: 12 },
  { [MONTH]: "Jun", [SERVICE]: "Networking", [SPEND]: 13 },
];

// Plot: reads only data and the constants above
// Months keep their order of appearance; each service keeps its colour by first appearance
const months = [...new Set(data.map((d) => d[MONTH]))];
const services = [...new Set(data.map((d) => d[SERVICE]))];
const values = services.map((s) =>
  months.map((m) => data.find((d) => d[MONTH] === m && d[SERVICE] === s)?.[SPEND] ?? null),
);
const serviceTotals = values.map((vs) => vs.reduce((a, v) => a + (v ?? 0), 0));
// Same stack order in every bar: the largest service overall at the bottom
const stackOrder = services.map((_, i) => i).sort((a, b) => serviceTotals[b] - serviceTotals[a]);

const totals = months.map((_, mi) => values.reduce((a, vs) => a + (vs[mi] ?? 0), 0));
const maxTotal = Math.max(...totals);

const growth = values.map((vs) => {
  const known = vs.filter((v) => v != null);
  return known.length > 1 && known[0] ? known[known.length - 1] / known[0] - 1 : -Infinity;
});
const fastest = growth.indexOf(Math.max(...growth));
const pct = (r: number) => `${r >= 0 ? "+" : ""}${Math.round(r * 100)}%`;
const SUBTITLE = [
  `${services.length} services across ${months.length} months, largest at the bottom`,
  totals[0] ? `stack total ${totals[0]} → ${totals[totals.length - 1]} (${pct(totals[totals.length - 1] / totals[0] - 1)})` : null,
  Number.isFinite(growth[fastest]) ? `fastest growth: ${services[fastest]} (${pct(growth[fastest])})` : null,
]
  .filter(Boolean)
  .join(" · ");

// Custom layer: each stack's total, just above the top of the stack
function TotalLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {months.map((m, i) => (
        <text
          key={m}
          x={xScale(m) + xScale.bandwidth() / 2}
          y={yScale(totals[i]) - 10}
          textAnchor="middle"
          fontSize={16}
          fontWeight={600}
          fill={t.ink}
        >
          {totals[i].toLocaleString("en-US")}
        </text>
      ))}
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
      <BarChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        borderRadius={3}
        grid={{ horizontal: true }}
        series={stackOrder.map((i) => ({
          id: `s${i}`,
          label: services[i],
          stack: "total",
          color: t.palette[i],
          data: values[i],
        }))}
        xAxis={[
          {
            scaleType: "band",
            data: months,
            label: MONTH,
            height: 64,
            categoryGapRatio: 0.4,
            disableTicks: true,
            tickLabelStyle: { fontSize: 16, fill: t.ink },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: maxTotal * (1 + PAD_SHARE),
            label: SPEND,
            width: 84,
            disableTicks: true,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        margin={{ top: 16, right: 40, bottom: 8, left: 24 }}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: { fontSize: 15, color: t.ink },
          },
        }}
        sx={{
          "& .MuiBarChart-element": { stroke: t.elevatedBg, strokeWidth: 1 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <TotalLabels />
      </BarChart>
    </Box>
  );
}
