// anyplot.ai
// bar-diverging-likert: Likert Scale Diverging Bar Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { BarChart } from "@mui/x-charts/BarChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "bar-diverging-likert · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 48;
const X_LABEL = "Share of responses (%)";
const PAD_SHARE = 0.06; // room beyond the longest half-bar
const MIN_LABEL_PX = 38; // a segment narrower than this keeps no percentage label
// The style guide's muted anchor (not among the tokens) for the neutral level
const MUTED = t.theme === "dark" ? "#A8A79F" : "#6B6A63";
const STEP_SHARE = 0.45; // the mild levels sit this far from their pole toward the ramp's midpoint
const DARK_INK = "#1A1A17";
const LIGHT_INK = "#FAF8F1";

// Columns: set these to your data's column names
const QUESTION = "Survey question"; // role: question
const STRONGLY_DISAGREE = "Strongly disagree"; // role: strongly_disagree
const DISAGREE = "Disagree"; // role: disagree
const NEUTRAL = "Neutral"; // role: neutral
const AGREE = "Agree"; // role: agree
const STRONGLY_AGREE = "Strongly agree"; // role: strongly_agree

// Data: replace this block with your own records, one object per row
// Employee engagement survey, 5-point Likert scale, percent of responses per level
const data = [
  { [QUESTION]: "I understand my role's impact", [STRONGLY_DISAGREE]: 2, [DISAGREE]: 5, [NEUTRAL]: 8, [AGREE]: 45, [STRONGLY_AGREE]: 40 },
  { [QUESTION]: "I receive regular recognition", [STRONGLY_DISAGREE]: 8, [DISAGREE]: 17, [NEUTRAL]: 20, [AGREE]: 35, [STRONGLY_AGREE]: 20 },
  { [QUESTION]: "I have growth opportunities", [STRONGLY_DISAGREE]: 10, [DISAGREE]: 22, [NEUTRAL]: 23, [AGREE]: 30, [STRONGLY_AGREE]: 15 },
  { [QUESTION]: "My manager gives useful feedback", [STRONGLY_DISAGREE]: 5, [DISAGREE]: 12, [NEUTRAL]: 18, [AGREE]: 40, [STRONGLY_AGREE]: 25 },
  { [QUESTION]: "I can share ideas openly", [STRONGLY_DISAGREE]: 4, [DISAGREE]: 11, [NEUTRAL]: 15, [AGREE]: 42, [STRONGLY_AGREE]: 28 },
  { [QUESTION]: "Changes are communicated well", [STRONGLY_DISAGREE]: 12, [DISAGREE]: 25, [NEUTRAL]: 20, [AGREE]: 28, [STRONGLY_AGREE]: 15 },
  { [QUESTION]: "My workload is manageable", [STRONGLY_DISAGREE]: 18, [DISAGREE]: 27, [NEUTRAL]: 15, [AGREE]: 28, [STRONGLY_AGREE]: 12 },
  { [QUESTION]: "I'd recommend this company", [STRONGLY_DISAGREE]: 3, [DISAGREE]: 7, [NEUTRAL]: 12, [AGREE]: 38, [STRONGLY_AGREE]: 40 },
];

// Plot: reads only data and the constants above
const LEVELS = [STRONGLY_DISAGREE, DISAGREE, NEUTRAL, AGREE, STRONGLY_AGREE]; // scale order

// Most net agreement first: (agree + strongly agree) minus (disagree + strongly disagree)
const ranked = data
  .map((d) => ({ row: d, net: d[AGREE] + d[STRONGLY_AGREE] - d[DISAGREE] - d[STRONGLY_DISAGREE] }))
  .sort((a, b) => b.net - a.net);
const rows = ranked.map((r) => r.row);
const nets = ranked.map((r) => r.net);
const questions = rows.map((d) => d[QUESTION]);

// Ordered levels take steps of the diverging Imprint ramp: the poles at its ends,
// the mild levels part-way toward its midpoint, neutral in the muted anchor
const levelRgb = [
  [t.div[0], t.div[0], 0],
  [t.div[0], t.div[1], STEP_SHARE],
  [MUTED, MUTED, 0],
  [t.div[2], t.div[1], STEP_SHARE],
  [t.div[2], t.div[2], 0],
].map(([from, to, share]) =>
  [1, 3, 5].map((i) =>
    Math.round(parseInt(String(from).slice(i, i + 2), 16) * (1 - Number(share)) + parseInt(String(to).slice(i, i + 2), 16) * Number(share)),
  ),
);
const LEVEL_COLORS = levelRgb.map(([r, g, b]) => `rgb(${r}, ${g}, ${b})`);

// Label ink per level: whichever fixed ink contrasts more with the segment's fill
const LEVEL_INKS = levelRgb.map((rgb) => {
  const [R, G, B] = rgb.map((v) => (v / 255 <= 0.03928 ? v / 255 / 12.92 : ((v / 255 + 0.055) / 1.055) ** 2.4));
  const lum = 0.2126 * R + 0.7152 * G + 0.0722 * B;
  return (lum + 0.05) / 0.0603 >= 0.985 / (lum + 0.05) ? DARK_INK : LIGHT_INK;
});

// Diverging stack: neutral split evenly across zero, disagreement stacked left and
// agreement right; within each sign the first series sits next to the midline
const SEGMENTS = [
  { id: "neutral-left", level: 2, sign: -1, share: 0.5 },
  { id: "disagree", level: 1, sign: -1, share: 1 },
  { id: "strongly-disagree", level: 0, sign: -1, share: 1 },
  { id: "neutral-right", level: 2, sign: 1, share: 0.5 },
  { id: "agree", level: 3, sign: 1, share: 1 },
  { id: "strongly-agree", level: 4, sign: 1, share: 1 },
];

const reach =
  Math.max(
    ...rows.map((d) => d[STRONGLY_DISAGREE] + d[DISAGREE] + d[NEUTRAL] / 2),
    ...rows.map((d) => d[AGREE] + d[STRONGLY_AGREE] + d[NEUTRAL] / 2),
  ) *
    (1 + PAD_SHARE) || 1;
const halfStep = 10 ** Math.floor(Math.log10(reach)) / 2;
const limit = Math.ceil(reach / halfStep) * halfStep;

const fmtSigned = (v: number) => `${v > 0 ? "+" : ""}${v}`;
const SUBTITLE = `${rows.length} questions, sorted by net agreement (${fmtSigned(Math.max(...nets))} to ${fmtSigned(Math.min(...nets))} points) · neutral split across the midline`;

// The neutral share is labelled once, in full, on the midline it straddles; a halo
// in the segment's own fill breaks the midline behind the text
function NeutralLabels() {
  const xScale = useXScale("share");
  const yScale = useYScale();
  const bw = yScale.bandwidth();
  return (
    <g>
      {rows.map((d) => {
        const share = d[NEUTRAL];
        if (share == null || Math.abs(xScale(share / 2) - xScale(-share / 2)) < MIN_LABEL_PX) return null;
        return (
          <text
            key={d[QUESTION]}
            x={xScale(0)}
            y={yScale(d[QUESTION]) + bw / 2}
            textAnchor="middle"
            dominantBaseline="central"
            fontSize={15}
            fontWeight={600}
            fill={LEVEL_INKS[2]}
            stroke={LEVEL_COLORS[2]}
            strokeWidth={5}
            paintOrder="stroke"
          >
            {`${share}%`}
          </text>
        );
      })}
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
        layout="horizontal"
        skipAnimation
        hideLegend
        grid={{ vertical: true }}
        series={SEGMENTS.map((seg) => ({
          id: seg.id,
          stack: "likert",
          label: LEVELS[seg.level],
          color: LEVEL_COLORS[seg.level],
          data: rows.map((d) => seg.sign * d[LEVELS[seg.level]] * seg.share),
          valueFormatter: (_v: number | null, { dataIndex }: { dataIndex: number }) =>
            `${rows[dataIndex][LEVELS[seg.level]]}%`,
          // the neutral halves carry no label of their own: NeutralLabels draws it on the midline
          barLabel: (item: { dataIndex: number }, ctx: { bar: { width: number } }) =>
            seg.level === 2 || ctx.bar.width < MIN_LABEL_PX ? null : `${rows[item.dataIndex][LEVELS[seg.level]]}%`,
        }))}
        xAxis={[
          {
            id: "share",
            min: -limit,
            max: limit,
            label: X_LABEL,
            height: 64,
            valueFormatter: (v: number) => `${Math.abs(v)}`,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: questions,
            width: 290,
            categoryGapRatio: 0.3,
            disableTicks: true,
            tickLabelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        margin={{ top: 16, right: 48, bottom: 8, left: 24 }}
        sx={{
          "& .MuiBarChart-label": { fontSize: 15, fontWeight: 600 },
          ...Object.fromEntries(
            SEGMENTS.map((seg) => [`& [data-series="${seg.id}"] .MuiBarChart-label`, { fill: LEVEL_INKS[seg.level] }]),
          ),
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <ChartsReferenceLine x={0} axisId="share" lineStyle={{ stroke: t.ink, strokeWidth: 2 }} />
        <NeutralLabels />
      </BarChart>
      <Box sx={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: "28px" }}>
        {LEVELS.map((level, i) => (
          <Box key={level} sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Box sx={{ width: 16, height: 16, borderRadius: "3px", bgcolor: LEVEL_COLORS[i] }} />
            <Typography sx={{ fontSize: 15, color: t.ink }}>{level}</Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
