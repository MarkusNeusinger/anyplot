// anyplot.ai
// donut-basic: Basic Donut Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 89/100 | Updated: 2026-11-08
//# anyplot-orientation: square
import { PieChart } from "@mui/x-charts/PieChart";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const DARK_INK = "#1A1A17"; // fixed label inks: segment colours do not change with the theme
const LIGHT_INK = "#FAF8F1";
const INK_SPLIT = 0.194; // relative luminance at which both inks reach the same WCAG contrast
const TITLE = "donut-basic · javascript · muix · anyplot.ai";
const TITLE_H = 72;
const LEGEND_H = 56;

// Columns: set these to your data's column names
const ASSET_CLASS = "Asset class"; // role: category
const ALLOCATION = "Allocation (million USD)"; // role: value

// Data: replace this block with your own records, one object per row
// A 500 million USD portfolio by asset class
const data = [
  { [ASSET_CLASS]: "Equities", [ALLOCATION]: 210 },
  { [ASSET_CLASS]: "Fixed Income", [ALLOCATION]: 140 },
  { [ASSET_CLASS]: "Real Estate", [ALLOCATION]: 70 },
  { [ASSET_CLASS]: "Commodities", [ALLOCATION]: 45 },
  { [ASSET_CLASS]: "Cash & Equivalents", [ALLOCATION]: 35 },
];

// Plot: reads only data and the constants above
const total = data.reduce((sum, d) => sum + d[ALLOCATION], 0);
const slices = data.map((d, i) => {
  const color = t.palette[i];
  // WCAG relative luminance of the segment colour decides which fixed ink reads better on it
  const [r, g, b] = [1, 3, 5].map((k) => {
    const c = parseInt(color.slice(k, k + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return {
    id: String(i),
    label: d[ASSET_CLASS],
    value: d[ALLOCATION],
    color,
    ink: 0.2126 * r + 0.7152 * g + 0.0722 * b > INK_SPLIT ? DARK_INK : LIGHT_INK,
  };
});
const inkRules = Object.fromEntries(
  slices.map((s, i) => [`& .MuiPieChart-arcLabel:nth-of-type(${i + 1})`, { fill: s.ink }]),
);

function CenterTotal() {
  const { left, top, width, height } = useDrawingArea();
  const cx = left + width / 2;
  const cy = top + height / 2;
  return (
    <g textAnchor="middle">
      <text x={cx} y={cy - 58} fontSize={18} fontWeight={600} letterSpacing="0.12em" fill={t.inkSoft}>
        TOTAL
      </text>
      <text x={cx} y={cy + 18} fontSize={68} fontWeight={700} fill={t.ink}>
        {total.toLocaleString("en-US")}
      </text>
      <text x={cx} y={cy + 56} fontSize={18} fill={t.inkSoft}>
        {ALLOCATION}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, paddingTop: 26, boxSizing: "border-box", textAlign: "center" }}>
        <span style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</span>
      </div>
      <PieChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        margin={{ top: 16, right: 40, bottom: 16, left: 40 }}
        series={[
          {
            id: "allocation",
            data: slices,
            innerRadius: "52%",
            outerRadius: "96%",
            paddingAngle: 1.5,
            cornerRadius: 4,
            arcLabel: (item) => `${Math.round((item.value / total) * 100)}%`,
            arcLabelMinAngle: 12,
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 16, color: t.ink, gap: 3 },
          },
        }}
        sx={{
          "& .MuiPieChart-arc": { stroke: t.pageBg, strokeWidth: 2 },
          "& .MuiPieChart-arcLabel": { fontSize: 22, fontWeight: 700 },
          ...inkRules,
        }}
      >
        <CenterTotal />
      </PieChart>
    </div>
  );
}
