// anyplot.ai
// bar-horizontal: Horizontal Bar Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-05
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// "muted" semantic anchor (other / rest) — not in ANYPLOT_TOKENS, so it's
// derived the same way the style guide defines it: theme-adaptive gray.
const MUTED = t.theme === "light" ? "#6B6A63" : "#A8A79F";

// Fixed (theme-independent) label colors — the bar fills below don't flip
// with theme, so label contrast is chosen per fill, not via t.ink/t.inkSoft.
const LABEL_ON_BRAND = "#1A1A17"; // dark ink — reads on the brand-green bar
const LABEL_ON_MUTED = t.pageBg; // page background — reads on the muted-gray bars (adapts per theme)

// --- Data (in-memory, deterministic) ----------------------------------------
// Product roadmap survey: feature requests ranked by customer votes, most
// requested first. Long descriptive labels are exactly why this ranking is
// horizontal rather than vertical — they'd collide or need rotation otherwise.
const FEATURES = [
  "Dark mode support",
  "Offline data sync",
  "Advanced search filters",
  "Bulk CSV export",
  "Customizable dashboards",
  "Real-time collaboration",
  "Mobile app redesign",
  "API rate limit increase",
];
const VOTES = [842, 715, 693, 588, 511, 467, 398, 312];

// Chart renders category index 0 at the top of the y-axis, so the array
// above (already sorted highest → lowest) reads as a top-to-bottom ranking.
// Only the top request is highlighted brand green; the rest use the "muted"
// semantic anchor (other / rest) so the eye lands on the leading request.
const BAR_COLORS = FEATURES.map((_, i) => (i === 0 ? t.palette[0] : MUTED));
const LABEL_COLORS = FEATURES.map((_, i) => (i === 0 ? LABEL_ON_BRAND : LABEL_ON_MUTED));

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width; // 1600 CSS px (landscape mount)
  const H = window.ANYPLOT_SIZE.height; // 900 CSS px
  const CHART_TOP = 84;

  const title = "Feature Requests by Customer Votes · bar-horizontal · javascript · muix · anyplot.ai";
  const titleSize = title.length > 67 ? Math.round(22 * 67 / title.length) : 22;

  return (
    <Box sx={{ position: "relative", width: W, height: H, bgcolor: t.pageBg }}>
      {/* Title + subtitle */}
      <Box sx={{ position: "absolute", top: 24, left: 56, right: 56 }}>
        <Typography sx={{ color: t.ink, fontSize: titleSize, fontWeight: 500 }}>{title}</Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 14, mt: 0.5 }}>
          Dark mode leads a 2026 product roadmap survey of 1,842 respondents
        </Typography>
      </Box>

      {/* Bar chart */}
      <Box sx={{ position: "absolute", top: CHART_TOP, left: 0, right: 0, bottom: 0 }}>
        <BarChart
          width={W}
          height={H - CHART_TOP}
          layout="horizontal"
          skipAnimation
          borderRadius={4}
          xAxis={[
            {
              label: "Customer Votes",
              labelStyle: { fontSize: 15, fill: t.ink },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              disableTicks: true,
              max: 950,
            },
          ]}
          yAxis={[
            {
              scaleType: "band",
              data: FEATURES,
              colorMap: { type: "ordinal", values: FEATURES, colors: BAR_COLORS },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              disableTicks: true,
              categoryGapRatio: 0.35,
            },
          ]}
          series={[
            {
              id: "votes",
              label: "Votes",
              data: VOTES,
              valueFormatter: (v) => `${v} votes`,
            },
          ]}
          barLabel="value"
          slotProps={{
            barLabel: (ownerState) => ({
              style: {
                fontSize: 13,
                fontWeight: 600,
                fill: LABEL_COLORS[ownerState.dataIndex],
              },
            }),
            legend: { hidden: true },
          }}
          margin={{ top: 14, right: 60, bottom: 60, left: 230 }}
          sx={{
            "& .MuiChartsAxis-line": { stroke: t.inkSoft },
            "& .MuiChartsGrid-line": { stroke: t.grid },
          }}
        />
      </Box>
    </Box>
  );
}
