// anyplot.ai
// bar-horizontal: Horizontal Bar Chart
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: pending | Created: 2026-08-05
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "Feature Requests by Customer Votes · bar-horizontal · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const PAD_SHARE = 0.08; // room beyond the longest bar for its value label
// The style guide's muted anchor (other / rest): the bars behind the accented leader
const MUTED = t.theme === "dark" ? "#A8A79F" : "#6B6A63";

// Columns: set these to your data's column names
const FEATURE_REQUEST = "Feature request"; // role: category
const VOTES = "Customer votes"; // role: value

// Data: replace this block with your own records, one object per row
// Product roadmap survey: feature requests and the votes each received
const data = [
  { [FEATURE_REQUEST]: "Dark mode support", [VOTES]: 842 },
  { [FEATURE_REQUEST]: "Offline data sync", [VOTES]: 715 },
  { [FEATURE_REQUEST]: "Advanced search filters", [VOTES]: 693 },
  { [FEATURE_REQUEST]: "Bulk CSV export", [VOTES]: 588 },
  { [FEATURE_REQUEST]: "Customizable dashboards", [VOTES]: 511 },
  { [FEATURE_REQUEST]: "Real-time collaboration", [VOTES]: 467 },
  { [FEATURE_REQUEST]: "Mobile app redesign", [VOTES]: 398 },
  { [FEATURE_REQUEST]: "API rate limit increase", [VOTES]: 312 },
];

// Plot: reads only data and the constants above
// A ranking: most votes first, so the leader sits at the top
const rows = data.filter((d) => d[VOTES] != null).sort((a, b) => b[VOTES] - a[VOTES]);
const requests = rows.map((d) => d[FEATURE_REQUEST]);
const votes = rows.map((d) => d[VOTES]);
const maxVotes = Math.max(...votes);

// Accent on the most-voted request; every other bar takes the muted anchor
const barColors = votes.map((v) => (v === maxVotes ? t.palette[0] : MUTED));

const SUBTITLE = [
  `${rows.length} requests ranked by ${VOTES.toLowerCase()}`,
  rows.length > 1
    ? `${requests[0]} leads with ${votes[0]}, ${votes[0] - votes[1]} ahead of ${requests[1]}`
    : null,
]
  .filter(Boolean)
  .join(" · ");

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
        height={height - TITLE_H}
        layout="horizontal"
        skipAnimation
        hideLegend
        borderRadius={4}
        grid={{ vertical: true }}
        series={[
          {
            id: "votes",
            label: VOTES,
            data: votes,
            barLabel: "value",
            barLabelPlacement: "outside",
          },
        ]}
        xAxis={[
          {
            min: 0,
            max: maxVotes * (1 + PAD_SHARE),
            label: VOTES,
            height: 64,
            tickNumber: 8,
            disableTicks: true,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: requests,
            colorMap: { type: "ordinal", values: requests, colors: barColors },
            width: 240,
            categoryGapRatio: 0.35,
            disableTicks: true,
            tickLabelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        margin={{ top: 16, right: 48, bottom: 8, left: 24 }}
        sx={{
          "& .MuiBarChart-label": { fill: t.ink, fontSize: 15, fontWeight: 600 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      />
    </Box>
  );
}
