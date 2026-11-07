// anyplot.ai
// bar-grouped: Grouped Bar Chart
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 92/100 | Created: 2026-08-05
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "Quarterly Revenue by Product Line · bar-grouped · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 44;
const DECIMALS = 1;
// Fixed label inks: bar fills keep their hex in both themes, so the ink follows the fill
const DARK_INK = "#1A1A17";
const LIGHT_INK = "#FAF8F1";

// Columns: set these to your data's column names
const QUARTER = "Fiscal quarter"; // role: category
const PRODUCT_LINE = "Product line"; // role: group
const REVENUE = "Revenue (million USD)"; // role: value

// Data: replace this block with your own records, one object per row
// Hardware peaks in Q2 while the recurring lines keep growing
const data = [
  { [QUARTER]: "Q1", [PRODUCT_LINE]: "Hardware", [REVENUE]: 4.2 },
  { [QUARTER]: "Q2", [PRODUCT_LINE]: "Hardware", [REVENUE]: 4.8 },
  { [QUARTER]: "Q3", [PRODUCT_LINE]: "Hardware", [REVENUE]: 4.5 },
  { [QUARTER]: "Q4", [PRODUCT_LINE]: "Hardware", [REVENUE]: 4.2 },
  { [QUARTER]: "Q1", [PRODUCT_LINE]: "Software", [REVENUE]: 3.1 },
  { [QUARTER]: "Q2", [PRODUCT_LINE]: "Software", [REVENUE]: 3.9 },
  { [QUARTER]: "Q3", [PRODUCT_LINE]: "Software", [REVENUE]: 4.7 },
  { [QUARTER]: "Q4", [PRODUCT_LINE]: "Software", [REVENUE]: 5.6 },
  { [QUARTER]: "Q1", [PRODUCT_LINE]: "Services", [REVENUE]: 2.0 },
  { [QUARTER]: "Q2", [PRODUCT_LINE]: "Services", [REVENUE]: 2.6 },
  { [QUARTER]: "Q3", [PRODUCT_LINE]: "Services", [REVENUE]: 3.2 },
  { [QUARTER]: "Q4", [PRODUCT_LINE]: "Services", [REVENUE]: 4.4 },
];

// Plot: reads only data and the constants above
// Categories and groups keep their order of first appearance
const quarters = [...new Set(data.map((d) => d[QUARTER]))];
const lines = [...new Set(data.map((d) => d[PRODUCT_LINE]))];
const values = lines.map((line) =>
  quarters.map((q) => data.find((d) => d[QUARTER] === q && d[PRODUCT_LINE] === line)?.[REVENUE] ?? null),
);
const fmt = (v: number) => v.toFixed(DECIMALS);

// In-bar label ink per group: whichever fixed ink contrasts more with the group's fill
const labelInks = lines.map((_, i) => {
  const [R, G, B] = [1, 3, 5].map((k) => {
    const c = parseInt(t.palette[i].slice(k, k + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  const lum = 0.2126 * R + 0.7152 * G + 0.0722 * B;
  return (lum + 0.05) / 0.0603 >= 0.985 / (lum + 0.05) ? DARK_INK : LIGHT_INK;
});

// Leading group per category; the subtitle names the first and the last
const leaders = quarters.map((_, qi) => {
  const column = values.map((v) => v[qi] ?? -Infinity);
  return lines[column.indexOf(Math.max(...column))];
});
const firstLeader = leaders[0];
const lastLeader = leaders[leaders.length - 1];
const SUBTITLE = [
  `${lines.length} product lines across ${quarters.length} quarters`,
  firstLeader === lastLeader
    ? `${firstLeader} leads ${quarters[0]} and ${quarters[quarters.length - 1]}`
    : `${firstLeader} leads ${quarters[0]}, ${lastLeader} leads ${quarters[quarters.length - 1]}`,
].join(" · ");

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
        colors={t.palette}
        skipAnimation
        borderRadius={4}
        grid={{ horizontal: true }}
        series={lines.map((line, i) => ({
          id: `g${i}`,
          label: line,
          data: values[i],
          valueFormatter: (v: number | null) => (v == null ? null : fmt(v)),
          barLabel: (item: { value: number | null }) => (item.value == null ? null : fmt(item.value)),
        }))}
        xAxis={[
          {
            scaleType: "band",
            data: quarters,
            label: QUARTER,
            height: 64,
            categoryGapRatio: 0.35,
            barGapRatio: 0.12,
            disableTicks: true,
            tickLabelStyle: { fontSize: 16, fill: t.ink },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            label: REVENUE,
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
          "& .MuiBarChart-label": { fontSize: 15, fontWeight: 600 },
          ...Object.fromEntries(lines.map((_, i) => [`& [data-series="g${i}"] .MuiBarChart-label`, { fill: labelInks[i] }])),
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      />
    </Box>
  );
}
