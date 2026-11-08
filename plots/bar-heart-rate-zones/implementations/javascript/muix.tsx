// anyplot.ai
// bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "Tempo Run · bar-heart-rate-zones · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const PAD_SHARE = 0.12; // headroom above the tallest bar for its duration label
// The style guide's muted anchor (not among the tokens) for the grey recovery zone
const MUTED = t.theme === "dark" ? "#A8A79F" : "#6B6A63";
// Conventional zone colours (grey, blue, green, orange, red) in their nearest Imprint hues,
// keyed by the zone code that opens each zone label
const ZONE_COLORS = new Map([
  ["Z1", MUTED],
  ["Z2", t.palette[2]],
  ["Z3", t.palette[0]],
  ["Z4", t.palette[3]],
  ["Z5", t.palette[4]],
]);

// Columns: set these to your data's column names
const ZONE = "Heart rate zone"; // role: zone
const MINUTES = "Time in zone (min)"; // role: minutes
const HR_LOW = "Zone floor (bpm)"; // role: hr_low
const HR_HIGH = "Zone ceiling (bpm)"; // role: hr_high

// Data: replace this block with your own records, one object per row
// Time per zone for a 60-minute tempo run; open-ended zones leave one bound empty
const data = [
  { [ZONE]: "Z1 Recovery", [MINUTES]: 8, [HR_LOW]: null, [HR_HIGH]: 125 },
  { [ZONE]: "Z2 Endurance", [MINUTES]: 22, [HR_LOW]: 126, [HR_HIGH]: 145 },
  { [ZONE]: "Z3 Aerobic", [MINUTES]: 15, [HR_LOW]: 146, [HR_HIGH]: 162 },
  { [ZONE]: "Z4 Threshold", [MINUTES]: 12, [HR_LOW]: 163, [HR_HIGH]: 174 },
  { [ZONE]: "Z5 Maximum", [MINUTES]: 3, [HR_LOW]: 175, [HR_HIGH]: null },
];

// Plot: reads only data and the constants above
// Zones keep the data's Z1 → Z5 order; they are never sorted by duration
const zones = data.map((d) => d[ZONE]);
const minutes = data.map((d) => d[MINUTES]);
const timeUnit = MINUTES.match(/\(([^)]*)\)/)?.[1] ?? "";
const hrUnit = HR_LOW.match(/\(([^)]*)\)/)?.[1] ?? "";

// HR boundary range per zone; an open bound reads as "up to" or "from"
const hrRanges = new Map(
  data.map((d) => [
    d[ZONE],
    d[HR_LOW] == null
      ? `≤ ${d[HR_HIGH]} ${hrUnit}`
      : d[HR_HIGH] == null
        ? `≥ ${d[HR_LOW]} ${hrUnit}`
        : `${d[HR_LOW]}–${d[HR_HIGH]} ${hrUnit}`,
  ]),
);

// Semantic colour by zone code; a zone outside the map takes the unused palette positions in order
const codes = zones.map((z) => String(z).split(/\s+/)[0]);
const spare = t.palette.filter((c) => ![...ZONE_COLORS.values()].includes(c));
const unmatched = codes.filter((c) => !ZONE_COLORS.has(c));
const zoneColors = codes.map((c) => ZONE_COLORS.get(c) ?? spare[unmatched.indexOf(c)]);

const total = minutes.reduce((a, v) => a + (v ?? 0), 0);
const top = minutes.indexOf(Math.max(...minutes));
const SUBTITLE = `${total} ${timeUnit} across ${zones.length} zones · most time in ${zones[top]}: ${minutes[top]} ${timeUnit} (${Math.round((minutes[top] / total) * 100)}%)`;

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
        skipAnimation
        hideLegend
        borderRadius={4}
        grid={{ horizontal: true }}
        series={[
          {
            id: "minutes",
            data: minutes,
            label: MINUTES,
            valueFormatter: (v: number | null, { dataIndex }: { dataIndex: number }) =>
              v == null ? null : `${v} ${timeUnit} · ${hrRanges.get(zones[dataIndex])}`,
            barLabel: (item: { value: number | null }) => (item.value == null ? null : `${item.value} ${timeUnit}`),
            barLabelPlacement: "outside",
          },
        ]}
        xAxis={[
          {
            scaleType: "band",
            data: zones,
            label: ZONE,
            height: 84,
            categoryGapRatio: 0.38,
            colorMap: { type: "ordinal", values: zones, colors: zoneColors },
            // Second tick line: the zone's heart rate boundaries
            valueFormatter: (z: string, ctx: { location: string }) =>
              ctx.location === "tick" ? `${z}\n${hrRanges.get(z)}` : z,
            disableTicks: true,
            tickLabelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: Math.max(...minutes) * (1 + PAD_SHARE),
            label: MINUTES,
            width: 84,
            disableTicks: true,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        margin={{ top: 16, right: 48, bottom: 8, left: 24 }}
        sx={{
          "& .MuiBarChart-label": { fill: t.ink, fontSize: 16, fontWeight: 700 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      />
    </Box>
  );
}
