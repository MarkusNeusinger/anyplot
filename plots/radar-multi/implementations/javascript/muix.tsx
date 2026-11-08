// anyplot.ai
// radar-multi: Multi-Series Radar Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-08-20
//# anyplot-orientation: square

import { RadarChart, RadarAxis } from "@mui/x-charts/RadarChart";
import { usePolarGeometry, useRadiusAxes } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SCALE_MAX = 100; // the 0–100 rating scale the spec recommends
const RINGS = 5; // gridlines at every fifth of the scale: 20, 40, 60, 80, 100
const CALLOUT_RADIUS = 1.12; // the callout box centre, as a share of the outer ring's radius
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

// Focal point: the feature where the leading model is furthest ahead of the runner-up
const leads = features.map((feature) => {
  const ranked = models
    .map((model) => ({ model, score: scores.get(`${model}\u0000${feature}`) }))
    .filter((r) => Number.isFinite(r.score))
    .sort((a, b) => b.score - a.score);
  return { feature, leader: ranked[0], runnerUp: ranked[1], margin: ranked.length > 1 ? ranked[0].score - ranked[1].score : -Infinity };
});
const widest = leads.reduce((a, b) => (b.margin > a.margin ? b : a));

const TITLE = "radar-multi · javascript · muix · anyplot.ai";
const SUBTITLE = `${models.length} series × ${features.length} axes · ${SCORE}`;

function WidestLead() {
  const polar = usePolarGeometry();
  const { radiusAxis } = useRadiusAxes();
  if (!Number.isFinite(widest.margin)) return null;
  const angle = polar.angleScale(widest.feature);
  const radius = radiusAxis[widest.feature].scale(widest.leader.score);
  const outer = radiusAxis[widest.feature].scale(SCALE_MAX);
  const [vx, vy] = polar.point(radius, angle);
  // The box sits outside the outer ring, half a spoke counter-clockwise, clear of every polygon
  const [bx, by] = polar.point(outer * CALLOUT_RADIUS, angle - Math.PI / features.length);
  const color = t.palette[models.indexOf(widest.leader.model)];
  const line1 = `Widest lead: ${widest.feature}`;
  const line2 = `${widest.leader.model} ${widest.leader.score} vs ${widest.runnerUp.model} ${widest.runnerUp.score}`;
  const boxW = Math.max(line1.length * 8.6, line2.length * 7.6) + 28;
  return (
    <g>
      <circle cx={polar.cx + vx} cy={polar.cy + vy} r={12} fill="none" stroke={color} strokeWidth={2.5} />
      <line
        x1={polar.cx + bx}
        y1={polar.cy + by + (vy < by ? -26 : 26)}
        x2={polar.cx + vx}
        y2={polar.cy + vy + (vy < by ? 12 : -12)}
        stroke={color}
        strokeWidth={1.5}
        strokeDasharray="5 4"
      />
      <rect
        x={polar.cx + bx - boxW / 2}
        y={polar.cy + by - 26}
        width={boxW}
        height={52}
        rx={8}
        fill={t.pageBg}
        fillOpacity={0.9}
        stroke={t.grid}
      />
      <text x={polar.cx + bx} y={polar.cy + by - 7} fontSize={15} fontWeight={700} fill={t.ink} textAnchor="middle">
        {line1}
      </text>
      <text x={polar.cx + bx} y={polar.cy + by + 15} fontSize={14} fill={t.inkSoft} textAnchor="middle">
        {line2}
      </text>
    </g>
  );
}

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
          "& .MuiRadarChart-seriesArea": { fillOpacity: 0.22, strokeWidth: 3, strokeLinejoin: "round" },
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
        <RadarAxis metric={features[0]} divisions={RINGS} labelOrientation="horizontal" textAnchor="start" />
        <WidestLead />
      </RadarChart>
    </div>
  );
}
