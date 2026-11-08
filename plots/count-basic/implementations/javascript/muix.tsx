// anyplot.ai
// count-basic: Basic Count Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 95/100 | Created: 2026-08-11
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { BarChart } from "@mui/x-charts/BarChart";

const t = window.ANYPLOT_TOKENS;

// Constants
const HEADROOM_SHARE = 0.1; // space above the tallest bar for its count label, as a share of the top count

// Columns: set these to your data's column names
const CATEGORY = "Support ticket category"; // role: category

// Data: replace this block with your own records, one object per observation
// 620 raw support tickets, each tagged with one category; the plot counts them
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
  const ticketTypes = ["Technical", "Billing", "Shipping", "Account", "Feature Request", "Other"];
  const weights = [0.3, 0.24, 0.18, 0.14, 0.09, 0.05];
  return Array.from({ length: 620 }, () => {
    const r = rand();
    let cumulative = 0;
    const index = weights.findIndex((w) => {
      cumulative += w;
      return r < cumulative;
    });
    return { [CATEGORY]: ticketTypes[index === -1 ? ticketTypes.length - 1 : index] };
  });
})();

// Plot: reads only data and the constants above
// Count the observations per category, then order by descending count (ties keep first appearance)
const countByCategory = new Map<string, number>();
data
  .filter((d) => d[CATEGORY] != null)
  .forEach((d) => countByCategory.set(d[CATEGORY], (countByCategory.get(d[CATEGORY]) ?? 0) + 1));
const ranked = [...countByCategory.entries()]
  .map(([category, count]) => ({ category, count }))
  .sort((a, b) => b.count - a.count);
const total = ranked.reduce((sum, r) => sum + r.count, 0);
const topCount = ranked[0]?.count ?? 0;

const TITLE = "Support Tickets · count-basic · javascript · muix · anyplot.ai";
const subtitle = `n = ${total.toLocaleString("en-US")} observations in ${ranked.length} categories, sorted by count`;
const HEADER_H = 88;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: HEADER_H, display: "flex", flexDirection: "column", justifyContent: "center", gap: "6px", px: "56px", pt: "8px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2 }}>{subtitle}</Typography>
      </Box>
      <BarChart
        width={width}
        height={height - HEADER_H}
        dataset={ranked}
        colors={[t.palette[0]]}
        skipAnimation
        hideLegend
        borderRadius={4}
        grid={{ horizontal: true }}
        margin={{ top: 24, right: 48, bottom: 16, left: 32 }}
        xAxis={[
          {
            scaleType: "band",
            dataKey: "category",
            label: CATEGORY,
            height: 68,
            categoryGapRatio: 0.4,
            disableTicks: true,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            label: "Count",
            width: 76,
            min: 0,
            max: topCount * (1 + HEADROOM_SHARE),
            tickMinStep: 1, // counts are whole numbers
            tickNumber: 8,
            disableTicks: true,
            disableLine: true,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        series={[{ id: "count", dataKey: "count", label: "Count", barLabel: "value", barLabelPlacement: "outside" }]}
        sx={{
          "& .MuiBarChart-label": { fontSize: "16px", fontWeight: 600, fill: t.ink },
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
        }}
      />
    </Box>
  );
}
