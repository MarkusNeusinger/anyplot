// anyplot.ai
// bar-spine: Spine Plot for Two-Variable Proportions
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "Customer Churn by Subscription Tier · bar-spine · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 40;
const FULL = 100; // every spine bar spans the whole, 0 to 100 %
const Y_TICKS = [0, 0.25, 0.5, 0.75, 1].map((f) => f * FULL);
const DECIMALS = 1;
const MIN_LABEL_W = 64; // px; a narrower segment keeps no percentage label
const MIN_LABEL_H = 24; // px; a shorter segment keeps no percentage label
// Outcome semantics: retained is good (green), downgraded a warning (amber), churned bad (red);
// an outcome outside the map takes the unused palette positions in order
const OUTCOME_COLORS = new Map([
  ["Retained", t.palette[0]],
  ["Downgraded", t.amber],
  ["Churned", t.palette[4]],
]);
// Fixed label inks: segment fills keep their hex in both themes, so the ink follows the fill
const DARK_INK = "#1A1A17";
const LIGHT_INK = "#FAF8F1";

// Columns: set these to your data's column names
const TIER = "Subscription tier"; // role: x_category
const OUTCOME = "Outcome"; // role: fill_category
const CUSTOMERS = "Customers"; // role: count

// Data: replace this block with your own records, one object per row
// Customers per subscription tier, split by what they did at renewal
const data = [
  { [TIER]: "Free", [OUTCOME]: "Retained", [CUSTOMERS]: 2636 },
  { [TIER]: "Free", [OUTCOME]: "Downgraded", [CUSTOMERS]: 900 },
  { [TIER]: "Free", [OUTCOME]: "Churned", [CUSTOMERS]: 1664 },
  { [TIER]: "Basic", [OUTCOME]: "Retained", [CUSTOMERS]: 1949 },
  { [TIER]: "Basic", [OUTCOME]: "Downgraded", [CUSTOMERS]: 500 },
  { [TIER]: "Basic", [OUTCOME]: "Churned", [CUSTOMERS]: 651 },
  { [TIER]: "Pro", [OUTCOME]: "Retained", [CUSTOMERS]: 1404 },
  { [TIER]: "Pro", [OUTCOME]: "Downgraded", [CUSTOMERS]: 180 },
  { [TIER]: "Pro", [OUTCOME]: "Churned", [CUSTOMERS]: 216 },
  { [TIER]: "Enterprise", [OUTCOME]: "Retained", [CUSTOMERS]: 638 },
  { [TIER]: "Enterprise", [OUTCOME]: "Downgraded", [CUSTOMERS]: 20 },
  { [TIER]: "Enterprise", [OUTCOME]: "Churned", [CUSTOMERS]: 42 },
];

// Plot: reads only data and the constants above
// Tiers left to right and outcomes bottom to top, both in order of first appearance
const tiers = [...new Set(data.map((d) => d[TIER]))];
const outcomes = [...new Set(data.map((d) => d[OUTCOME]))];
const rows = data.filter((d) => d[CUSTOMERS] != null);
const tierTotals = tiers.map((tier) => rows.filter((d) => d[TIER] === tier).reduce((a, d) => a + d[CUSTOMERS], 0));
const grandTotal = tierTotals.reduce((a, v) => a + v, 0);

// Bar edges on the count axis: each tier is as wide as its marginal count
const tierStarts = tierTotals.map((_, i) => tierTotals.slice(0, i).reduce((a, v) => a + v, 0));
const tierCenters = tierStarts.map((x0, i) => x0 + tierTotals[i] / 2);
const tickLabels = new Map(
  tierCenters.map((c, i) => [c, `${tiers[i]}\n${tierTotals[i].toLocaleString("en-US")}`]),
);

const spare = t.palette.filter((c) => ![...OUTCOME_COLORS.values()].includes(c));
const unmatched = outcomes.filter((o) => !OUTCOME_COLORS.has(o));
const outcomeColors = outcomes.map((o) => OUTCOME_COLORS.get(o) ?? spare[unmatched.indexOf(o)]);
// Label ink per outcome: whichever fixed ink contrasts more with the outcome's fill
const outcomeInks = outcomeColors.map((hex) => {
  const [R, G, B] = [1, 3, 5].map((k) => {
    const c = parseInt(hex.slice(k, k + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  const lum = 0.2126 * R + 0.7152 * G + 0.0722 * B;
  return (lum + 0.05) / 0.0603 >= 0.985 / (lum + 0.05) ? DARK_INK : LIGHT_INK;
});

// Segments: conditional share of each outcome within its tier, stacked from zero to FULL
const segments = tiers.flatMap((tier, ti) => {
  let base = 0;
  return outcomes.flatMap((outcome, oi) => {
    const row = rows.find((d) => d[TIER] === tier && d[OUTCOME] === outcome);
    if (!row || !tierTotals[ti]) return [];
    const share = (row[CUSTOMERS] / tierTotals[ti]) * FULL;
    const seg = {
      key: `${ti}-${oi}`,
      x0: tierStarts[ti],
      x1: tierStarts[ti] + tierTotals[ti],
      y0: base,
      y1: base + share,
      fill: outcomeColors[oi],
      ink: outcomeInks[oi],
      label: `${share.toFixed(DECIMALS)}%`,
    };
    base += share;
    return [seg];
  });
});

const SUBTITLE = `Bar width ∝ ${CUSTOMERS.toLowerCase()} per ${TIER.toLowerCase()} (n = ${grandTotal.toLocaleString("en-US")}) · segment height = ${OUTCOME.toLowerCase()} share within the bar`;

// Custom layer: the variable-width stacked bars, drawn in data coordinates
function SpineSegments() {
  const xScale = useXScale("count");
  const yScale = useYScale("share");

  return (
    <g>
      {segments.map((s) => {
        const x = xScale(s.x0);
        const w = xScale(s.x1) - x;
        const y = yScale(s.y1);
        const h = yScale(s.y0) - y;
        return (
          <g key={s.key}>
            <rect x={x} y={y} width={w} height={h} fill={s.fill} stroke={t.elevatedBg} strokeWidth={1} />
            {w >= MIN_LABEL_W && h >= MIN_LABEL_H && (
              <text
                x={x + w / 2}
                y={y + h / 2}
                textAnchor="middle"
                dominantBaseline="central"
                fill={s.ink}
                fontSize={15}
                fontWeight={600}
              >
                {s.label}
              </text>
            )}
          </g>
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
      <Box sx={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: "28px" }}>
        {outcomes.map((outcome, i) => (
          <Box key={outcome} sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Box sx={{ width: 16, height: 16, borderRadius: "3px", bgcolor: outcomeColors[i] }} />
            <Typography sx={{ fontSize: 15, color: t.ink }}>{outcome}</Typography>
          </Box>
        ))}
      </Box>
      <ChartsContainer
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        series={[]}
        xAxis={[
          {
            id: "count",
            scaleType: "linear",
            min: 0,
            max: grandTotal,
            label: TIER,
            height: 84,
            // One tick under the centre of each bar, named by its tier and its count
            tickInterval: tierCenters,
            valueFormatter: (v: number) => tickLabels.get(v) ?? "",
            disableTicks: true,
            tickLabelStyle: { fontSize: 15, fill: t.ink },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "share",
            scaleType: "linear",
            min: 0,
            max: FULL,
            tickInterval: Y_TICKS,
            label: `Share of ${CUSTOMERS.toLowerCase()} (%)`,
            width: 72,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        margin={{ top: 12, right: 48, bottom: 8, left: 24 }}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <SpineSegments />
        <ChartsXAxis axisId="count" />
        <ChartsYAxis axisId="share" />
      </ChartsContainer>
    </Box>
  );
}
