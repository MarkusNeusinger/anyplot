// anyplot.ai
// donut-nested: Nested Donut Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-18
//# anyplot-orientation: square
import { PieChart } from "@mui/x-charts/PieChart";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TINT_FIRST = 0.12; // share of white mixed into a parent's first child
const TINT_LAST = 0.6; // share of white mixed into its last child, still clear of the page in both themes
const DARK_INK = "#1A1A17"; // fixed label inks: segment colours do not change with the theme
const LIGHT_INK = "#FAF8F1";
const INK_SPLIT = 0.194; // relative luminance at which both inks reach the same WCAG contrast
const OUTER_LABEL_MIN_ANGLE = 22; // degrees; narrower outer segments are named in the legend only
const TITLE = "donut-nested · javascript · muix · anyplot.ai";
const TITLE_H = 72;
const LEGEND_H = 124; // two legend rows plus the 28 px bottom padding of the page

// Columns: set these to your data's column names
const BUSINESS_UNIT = "Business unit"; // role: level_1
const CUSTOMER_SEGMENT = "Customer segment"; // role: level_2
const REVENUE = "Revenue (million USD)"; // role: value

// Data: replace this block with your own records, one object per row
// Annual revenue of a technology company by business unit and customer segment
const data = [
  { [BUSINESS_UNIT]: "Software", [CUSTOMER_SEGMENT]: "Enterprise SaaS", [REVENUE]: 380 },
  { [BUSINESS_UNIT]: "Software", [CUSTOMER_SEGMENT]: "SMB Subscriptions", [REVENUE]: 210 },
  { [BUSINESS_UNIT]: "Software", [CUSTOMER_SEGMENT]: "Developer Tools", [REVENUE]: 120 },
  { [BUSINESS_UNIT]: "Hardware", [CUSTOMER_SEGMENT]: "Enterprise Devices", [REVENUE]: 260 },
  { [BUSINESS_UNIT]: "Hardware", [CUSTOMER_SEGMENT]: "Consumer Devices", [REVENUE]: 180 },
  { [BUSINESS_UNIT]: "Services", [CUSTOMER_SEGMENT]: "Managed Support", [REVENUE]: 150 },
  { [BUSINESS_UNIT]: "Services", [CUSTOMER_SEGMENT]: "Professional Services", [REVENUE]: 130 },
  { [BUSINESS_UNIT]: "Services", [CUSTOMER_SEGMENT]: "Training", [REVENUE]: 70 },
  { [BUSINESS_UNIT]: "Consulting", [CUSTOMER_SEGMENT]: "Strategy Advisory", [REVENUE]: 140 },
  { [BUSINESS_UNIT]: "Consulting", [CUSTOMER_SEGMENT]: "Implementation", [REVENUE]: 100 },
];

// Plot: reads only data and the constants above
const units = [...new Set(data.map((d) => d[BUSINESS_UNIT]))];
const total = data.reduce((sum, d) => sum + d[REVENUE], 0);
const revenueUnit = REVENUE.match(/\(([^)]+)\)/)?.[1] ?? "";

// Inner ring: one segment per business unit, its value aggregated from its children
const inner = units.map((unit, i) => ({
  id: `unit-${i}`,
  // Units carry their own arc label, so the legend lists only the customer segments
  label: (location) => (location === "legend" ? undefined : unit),
  value: data.filter((d) => d[BUSINESS_UNIT] === unit).reduce((sum, d) => sum + d[REVENUE], 0),
  color: t.palette[i],
}));

// Outer ring: children grouped under their unit in the inner ring's order, so every child
// sits inside its parent's arc; children mix the parent's hue with white, lighter in order
const outer = units.flatMap((unit, i) => {
  const children = data.filter((d) => d[BUSINESS_UNIT] === unit);
  const rgb = [1, 3, 5].map((k) => parseInt(t.palette[i].slice(k, k + 2), 16));
  return children.map((d, j) => {
    const tint = TINT_FIRST + ((TINT_LAST - TINT_FIRST) * j) / Math.max(1, children.length - 1);
    const mixed = rgb.map((c) => Math.round(c + (255 - c) * tint));
    return {
      id: `segment-${i}-${j}`,
      label: d[CUSTOMER_SEGMENT],
      value: d[REVENUE],
      color: `rgb(${mixed.join(", ")})`,
      rgb: mixed,
    };
  });
});

// Label ink on each segment from its colour's WCAG relative luminance
const inkRules = Object.fromEntries(
  [
    ...inner.map((s, i) => ["units", i, [1, 3, 5].map((k) => parseInt(s.color.slice(k, k + 2), 16))]),
    ...outer.map((s, i) => ["segments", i, s.rgb]),
  ].map(([series, i, rgb]) => {
    const [r, g, b] = rgb.map((c) => (c / 255 <= 0.03928 ? c / 255 / 12.92 : ((c / 255 + 0.055) / 1.055) ** 2.4));
    const ink = 0.2126 * r + 0.7152 * g + 0.0722 * b > INK_SPLIT ? DARK_INK : LIGHT_INK;
    return [`& .MuiPieChart-seriesLabels[data-series="${series}"] .MuiPieChart-arcLabel:nth-of-type(${i + 1})`, { fill: ink }];
  }),
);

function CenterTotal() {
  const { left, top, width, height } = useDrawingArea();
  const cx = left + width / 2;
  const cy = top + height / 2;
  return (
    <g textAnchor="middle">
      <text x={cx} y={cy - 34} fontSize={15} fontWeight={600} letterSpacing="0.12em" fill={t.inkSoft}>
        TOTAL
      </text>
      <text x={cx} y={cy + 14} fontSize={42} fontWeight={700} fill={t.ink}>
        {total.toLocaleString("en-US")}
      </text>
      <text x={cx} y={cy + 40} fontSize={15} fill={t.inkSoft}>
        {revenueUnit}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, display: "flex", flexDirection: "column", paddingBottom: 28, boxSizing: "border-box" }}>
      <div style={{ height: TITLE_H, paddingTop: 26, boxSizing: "border-box", textAlign: "center" }}>
        <span style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</span>
      </div>
      <PieChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        margin={{ top: 8, right: 40, bottom: 16, left: 40 }}
        series={[
          {
            id: "units",
            data: inner,
            innerRadius: "22%",
            outerRadius: "50%",
            cornerRadius: 3,
            arcLabel: "label",
            valueFormatter: (item) => `${item.value.toLocaleString("en-US")} ${revenueUnit}`,
          },
          {
            id: "segments",
            data: outer,
            innerRadius: "54%",
            outerRadius: "100%",
            cornerRadius: 3,
            arcLabel: "label",
            arcLabelMinAngle: OUTER_LABEL_MIN_ANGLE,
            valueFormatter: (item) => `${item.value.toLocaleString("en-US")} ${revenueUnit}`,
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 16, color: t.ink, columnGap: 3, rowGap: 1.5, px: 6, justifyContent: "center" },
          },
        }}
        sx={{
          "& .MuiPieChart-arc": { stroke: t.pageBg, strokeWidth: 3 },
          '& .MuiPieChart-seriesLabels[data-series="units"] .MuiPieChart-arcLabel': { fontSize: 18, fontWeight: 700 },
          '& .MuiPieChart-seriesLabels[data-series="segments"] .MuiPieChart-arcLabel': { fontSize: 15, fontWeight: 600 },
          ...inkRules,
        }}
      >
        <CenterTotal />
      </PieChart>
    </div>
  );
}
