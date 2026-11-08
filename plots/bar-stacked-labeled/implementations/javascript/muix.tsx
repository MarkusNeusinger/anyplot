// anyplot.ai
// bar-stacked-labeled: Stacked Bar Chart with Total Labels
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-26
import { BarChart } from "@mui/x-charts/BarChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "Project Budget by Phase · bar-stacked-labeled · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 44;
const PAD_SHARE = 0.12; // headroom above the tallest stack for its total label
const MIN_LABEL_PX = 30; // a segment shorter than this keeps no segment label
// Fixed label inks: segment fills keep their hex in both themes, so the ink follows the fill
const DARK_INK = "#1A1A17";
const LIGHT_INK = "#FAF8F1";

// Columns: set these to your data's column names
const PHASE = "Project phase"; // role: category
const COST_TYPE = "Cost type"; // role: component
const COST = "Cost (thousand USD)"; // role: value

// Data: replace this block with your own records, one object per row
// Software project budget, three cost types per delivery phase
const data = [
  { [PHASE]: "Planning", [COST_TYPE]: "Labor", [COST]: 18 },
  { [PHASE]: "Design", [COST_TYPE]: "Labor", [COST]: 32 },
  { [PHASE]: "Development", [COST_TYPE]: "Labor", [COST]: 58 },
  { [PHASE]: "Testing", [COST_TYPE]: "Labor", [COST]: 34 },
  { [PHASE]: "Deployment", [COST_TYPE]: "Labor", [COST]: 22 },
  { [PHASE]: "Planning", [COST_TYPE]: "Materials", [COST]: 6 },
  { [PHASE]: "Design", [COST_TYPE]: "Materials", [COST]: 14 },
  { [PHASE]: "Development", [COST_TYPE]: "Materials", [COST]: 20 },
  { [PHASE]: "Testing", [COST_TYPE]: "Materials", [COST]: 10 },
  { [PHASE]: "Deployment", [COST_TYPE]: "Materials", [COST]: 8 },
  { [PHASE]: "Planning", [COST_TYPE]: "Equipment", [COST]: 4 },
  { [PHASE]: "Design", [COST_TYPE]: "Equipment", [COST]: 10 },
  { [PHASE]: "Development", [COST_TYPE]: "Equipment", [COST]: 16 },
  { [PHASE]: "Testing", [COST_TYPE]: "Equipment", [COST]: 6 },
  { [PHASE]: "Deployment", [COST_TYPE]: "Equipment", [COST]: 12 },
];

// Plot: reads only data and the constants above
// Phases keep their delivery order; cost types stack bottom to top in order of first appearance
const phases = [...new Set(data.map((d) => d[PHASE]))];
const costTypes = [...new Set(data.map((d) => d[COST_TYPE]))];
const values = costTypes.map((c) =>
  phases.map((p) => data.find((d) => d[PHASE] === p && d[COST_TYPE] === c)?.[COST] ?? null),
);
const totals = phases.map((_, pi) => values.reduce((a, vs) => a + (vs[pi] ?? 0), 0));
const maxTotal = Math.max(...totals);
const grandTotal = totals.reduce((a, v) => a + v, 0);
const largest = totals.indexOf(maxTotal);

// Segment label ink per cost type: whichever fixed ink contrasts more with the fill
const labelInks = costTypes.map((_, i) => {
  const [R, G, B] = [1, 3, 5].map((k) => {
    const c = parseInt(t.palette[i].slice(k, k + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  const lum = 0.2126 * R + 0.7152 * G + 0.0722 * B;
  return (lum + 0.05) / 0.0603 >= 0.985 / (lum + 0.05) ? DARK_INK : LIGHT_INK;
});

const SUBTITLE = `${phases.length} phases, ${costTypes.length} cost types · budget total ${grandTotal.toLocaleString("en-US")} · largest phase: ${phases[largest]} (${Math.round((maxTotal / grandTotal) * 100)}% of the total)`;

// Custom layer: each stack's total, directly above the top of the stack
function TotalLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {phases.map((p, i) => (
        <text
          key={p}
          x={xScale(p) + xScale.bandwidth() / 2}
          y={yScale(totals[i]) - 12}
          textAnchor="middle"
          fontSize={20}
          fontWeight={700}
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
        colors={t.palette}
        skipAnimation
        borderRadius={4}
        grid={{ horizontal: true }}
        series={costTypes.map((c, i) => ({
          id: `c${i}`,
          label: c,
          stack: "total",
          data: values[i],
          barLabel: (item: { value: number | null }, ctx: { bar: { height: number } }) =>
            item.value == null || ctx.bar.height < MIN_LABEL_PX ? null : item.value.toLocaleString("en-US"),
        }))}
        xAxis={[
          {
            scaleType: "band",
            data: phases,
            label: PHASE,
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
            label: COST,
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
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 15, color: t.ink },
          },
        }}
        sx={{
          "& .MuiBarChart-element": { stroke: t.elevatedBg, strokeWidth: 1.5 },
          "& .MuiBarChart-label": { fontSize: 15, fontWeight: 500 },
          ...Object.fromEntries(costTypes.map((_, i) => [`& [data-series="c${i}"] .MuiBarChart-label`, { fill: labelInks[i] }])),
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <TotalLabels />
      </BarChart>
    </Box>
  );
}
