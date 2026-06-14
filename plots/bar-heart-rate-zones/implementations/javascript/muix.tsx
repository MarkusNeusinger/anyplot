// anyplot.ai
// bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 91/100 | Created: 2026-06-14
//# anyplot-orientation: landscape
// anyplot.ai
// bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-14

import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

const zoneLabels = ["Z1 Recovery", "Z2 Endurance", "Z3 Aerobic", "Z4 Threshold", "Z5 Maximum"];
const hrRanges   = ["< 125 bpm", "126–145 bpm", "146–162 bpm", "163–174 bpm", "> 174 bpm"];
const minutes    = [8, 22, 15, 12, 3];

// Semantic zone colors: fitness-industry grey/blue/green/ochre/red → nearest Imprint members.
// Z2 Endurance dominates at 22/60 min (37%) — rendered full opacity.
// Remaining zones at 75% opacity (hex alpha BF) to direct the eye toward the dominant bar.
const zoneColors = [
  "#6B6A63BF",  // Z1 Recovery  — muted anchor, 75%
  "#4467A3",    // Z2 Endurance — position 3 blue, full opacity (dominant)
  "#009E73BF",  // Z3 Aerobic   — position 1 green, 75%
  "#BD8233BF",  // Z4 Threshold — position 4 ochre, 75%
  "#AE3030BF",  // Z5 Maximum   — position 5 matte red, 75%
];

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;   // 1600 CSS px (landscape mount)
  const H = window.ANYPLOT_SIZE.height;  // 900 CSS px
  const CHART_TOP = 84;

  return (
    <Box sx={{ position: "relative", width: W, height: H, bgcolor: t.pageBg }}>

      {/* Title + subtitle */}
      <Box sx={{ position: "absolute", top: 22, left: 56, right: 56 }}>
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 500, lineHeight: 1.25 }}>
          bar-heart-rate-zones · javascript · muix · anyplot.ai
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 14, mt: 0.5 }}>
          60-minute tempo run — time spent in each training intensity zone
        </Typography>
      </Box>

      {/* Bar chart */}
      <Box sx={{ position: "absolute", top: CHART_TOP, left: 0, right: 0, bottom: 0 }}>
        <BarChart
          width={W}
          height={H - CHART_TOP}
          skipAnimation
          xAxis={[{
            scaleType: "band",
            data: zoneLabels,
            colorMap: {
              type: "ordinal",
              values: zoneLabels,
              colors: zoneColors,
            },
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: { fontSize: 15, fill: t.ink, fontWeight: 500 },
            categoryGapRatio: 0.38,
          }]}
          yAxis={[{
            label: "Time (minutes)",
            labelStyle: { fontSize: 14, fill: t.inkSoft },
            tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
            disableTicks: true,
            max: 28,
          }]}
          series={[{
            data: minutes,
            label: "Time in zone",
            valueFormatter: (v, ctx) => {
              const i = ctx?.dataIndex ?? 0;
              return `${v} min | HR: ${hrRanges[i]}`;
            },
          }]}
          barLabel={(item) => (item.value !== null ? `${item.value} min` : null)}
          margin={{ top: 30, right: 60, bottom: 80, left: 76 }}
          grid={{ horizontal: true }}
          sx={{
            "& .MuiBarLabel-root": {
              fill: "#F0EFE8",  // warm white — readable on all zone colors in both themes
              fontSize: "16px",
              fontWeight: 700,
            },
            "& .MuiChartsAxis-line": { stroke: t.inkSoft },
            "& .MuiChartsGrid-line": { stroke: t.grid },
            "& .MuiChartsLegend-root": { display: "none" },
          }}
        />
      </Box>

      {/* HR boundary ranges below each zone (bottom strip) */}
      <Box
        sx={{
          position: "absolute",
          bottom: 12,
          left: 76 + 60,
          right: 60,
          display: "flex",
          justifyContent: "space-around",
          pointerEvents: "none",
        }}
      >
        {hrRanges.map((range, i) => (
          <Typography
            key={i}
            sx={{ color: t.inkSoft, fontSize: 12, textAlign: "center" }}
          >
            {range}
          </Typography>
        ))}
      </Box>
    </Box>
  );
}
