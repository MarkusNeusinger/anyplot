// anyplot.ai
// radar-basic: Basic Radar Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
//# anyplot-orientation: square

import { RadarChart, RadarAxis, RadarSeriesArea, RadarSeriesMarks } from "@mui/x-charts/RadarChart";

const t = window.ANYPLOT_TOKENS;

// Constants
const SCALE_MAX = 100; // the 0–100 rating scale the spec recommends
const RINGS = 5; // gridlines at every fifth of the scale: 20, 40, 60, 80, 100
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 48;

// Columns: set these to your data's column names
const ATTRIBUTE = "Attribute"; // role: category
const PLAYERS = ["Guard", "Forward"]; // role: value

// Data: replace this block with your own records, one object per row
// Basketball scouting report: two player profiles rated 0–100 on six attributes
const data = [
  { [ATTRIBUTE]: "Speed", [PLAYERS[0]]: 90, [PLAYERS[1]]: 70 },
  { [ATTRIBUTE]: "Shooting", [PLAYERS[0]]: 84, [PLAYERS[1]]: 76 },
  { [ATTRIBUTE]: "Passing", [PLAYERS[0]]: 92, [PLAYERS[1]]: 62 },
  { [ATTRIBUTE]: "Defense", [PLAYERS[0]]: 68, [PLAYERS[1]]: 85 },
  { [ATTRIBUTE]: "Rebounding", [PLAYERS[0]]: 52, [PLAYERS[1]]: 90 },
  { [ATTRIBUTE]: "Stamina", [PLAYERS[0]]: 86, [PLAYERS[1]]: 80 },
];

// Plot: reads only data and the constants above
const attributes = [...new Set(data.map((d) => d[ATTRIBUTE]))];
const series = PLAYERS.map((player, i) => ({
  id: `player-${i}`,
  label: player,
  data: attributes.map((a) => data.find((d) => d[ATTRIBUTE] === a)?.[player] ?? null),
  fillArea: true,
}));

const TITLE = "radar-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${PLAYERS.length} series on ${attributes.length} axes · shared scale 0–${SCALE_MAX}`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <RadarChart
        width={width}
        height={height - TITLE_H - SUBTITLE_H - LEGEND_H}
        skipAnimation
        colors={t.palette}
        margin={{ top: 64, right: 120, bottom: 64, left: 120 }}
        radar={{ metrics: attributes, max: SCALE_MAX, labelGap: 22 }}
        divisions={RINGS}
        shape="sharp"
        stripeColor={null}
        series={series}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 16, color: t.ink },
          },
        }}
        sx={{
          "& .MuiRadarChart-gridRadial, & .MuiRadarChart-gridDivider": { stroke: t.grid, strokeOpacity: 1, strokeWidth: 1.5 },
          // The chart's own areas carry only the fills; the outlines are drawn in a second pass
          // above every fill, so no series' fill tints another series' outline
          "& .MuiRadarChart-seriesArea": { fillOpacity: 0.25, strokeWidth: 0 },
          "& .MuiRadarChart-seriesMark": { r: 6, stroke: t.pageBg, strokeWidth: 2 },
          "& .MuiRadarChart-axisLine": { stroke: "none" },
          "& .MuiRadarChart-axisLabel": { fontSize: 15, fill: t.inkSoft, transform: "translateX(8px)" },
          // The metric labels carry an inline 12 px caption style, which only an !important rule outranks
          "& .MuiChartsSvgLayer-root > text": { fontSize: "18px !important", fontWeight: "600 !important" },
        }}
      >
        <RadarSeriesArea className="radar-outline" fill="none" strokeWidth={3} strokeLinejoin="round" />
        <RadarSeriesMarks />
        <RadarAxis metric={attributes[0]} divisions={RINGS} labelOrientation="horizontal" textAnchor="start" />
      </RadarChart>
    </div>
  );
}
