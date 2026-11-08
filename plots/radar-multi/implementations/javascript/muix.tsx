// anyplot.ai
// radar-multi: Multi-Series Radar Chart
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
const FEATURE = "Feature"; // role: category
const SCORE = "Score (0–100)"; // role: value
const MODEL = "Headphones"; // role: series

// Data: replace this block with your own records, one object per row
// Noise-cancelling headphone review: three models scored 0–100 on seven features
const data = [
  ["Sound Quality", 92, 78, 65],
  ["Noise Cancelling", 88, 95, 60],
  ["Battery Life", 75, 90, 82],
  ["Comfort", 80, 85, 70],
  ["Build Quality", 85, 70, 60],
  ["Value", 60, 55, 92],
  ["Connectivity", 90, 82, 75],
].flatMap(([feature, ...scores]) =>
  ["AudioMax Pro", "SoundWave Elite", "EchoBudget"].map((model, i) => ({
    [FEATURE]: feature,
    [MODEL]: model,
    [SCORE]: scores[i],
  })),
);

// Plot: reads only data and the constants above
const features = [...new Set(data.map((d) => d[FEATURE]))];
const models = [...new Set(data.map((d) => d[MODEL]))];
const scores = new Map(data.map((d) => [`${d[MODEL]}\u0000${d[FEATURE]}`, d[SCORE]]));
const series = models.map((model, i) => ({
  id: `model-${i}`,
  label: model,
  data: features.map((f) => scores.get(`${model}\u0000${f}`) ?? null),
  fillArea: true,
}));

const TITLE = "radar-multi · javascript · muix · anyplot.ai";
const SUBTITLE = `${models.length} series × ${features.length} axes · ${SCORE}`;

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
        margin={{ top: 64, right: 150, bottom: 64, left: 150 }}
        radar={{ metrics: features, max: SCALE_MAX, labelGap: 22 }}
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
          "& .MuiRadarChart-seriesArea": { fillOpacity: 0.22, strokeWidth: 0 },
          "& .MuiRadarChart-seriesMark": { r: 5.5, stroke: t.pageBg, strokeWidth: 2 },
          "& .MuiRadarChart-axisLine": { stroke: "none" },
          "& .MuiRadarChart-axisLabel": {
            fontSize: 15,
            fill: t.inkSoft,
            transform: "translateX(8px)",
            stroke: t.pageBg,
            strokeWidth: 4,
            paintOrder: "stroke",
          },
          // The metric labels carry an inline 12 px caption style, which only an !important rule outranks
          "& .MuiChartsSvgLayer-root > text": { fontSize: "17px !important", fontWeight: "600 !important" },
        }}
      >
        <RadarSeriesArea className="radar-outline" fill="none" strokeWidth={3} strokeLinejoin="round" />
        <RadarSeriesMarks />
        <RadarAxis metric={features[0]} divisions={RINGS} labelOrientation="horizontal" textAnchor="start" />
      </RadarChart>
    </div>
  );
}
