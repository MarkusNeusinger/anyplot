//# anyplot-orientation: square
// anyplot.ai
// pie-basic: Basic Pie Chart
// Library: MUI X Charts | React | Node
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-20
import { PieChart, PieArcLabel } from "@mui/x-charts/PieChart";

const t = window.ANYPLOT_TOKENS;

// Constants
const EXPLODE_OFFSET = 30; // px the largest slice is pulled out along its bisector
const TITLE = "pie-basic · javascript · muix · anyplot.ai";
const MARGIN = { top: 100, right: 60, bottom: 40, left: 60 };
const LEGEND_BAND = 60;

// Columns: set these to your data's column names
const SOURCE = "Traffic source"; // role: category
const SHARE = "Share of visits (%)"; // role: value

// Data: replace this block with your own records, one object per row
// Website traffic sources for a mid-size e-commerce site (share of visits, sums to 100)
const data = [
  { [SOURCE]: "Organic Search", [SHARE]: 38 },
  { [SOURCE]: "Direct", [SHARE]: 22 },
  { [SOURCE]: "Social Media", [SHARE]: 16 },
  { [SOURCE]: "Referral", [SHARE]: 12 },
  { [SOURCE]: "Paid Search", [SHARE]: 8 },
  { [SOURCE]: "Email", [SHARE]: 4 },
];

// Plot: reads only data and the constants above
const total = data.reduce((sum, d) => sum + d[SHARE], 0);
const slices = data.map((d, i) => ({
  id: String(i),
  label: d[SOURCE],
  value: d[SHARE],
  color: t.palette[i],
}));
const explodedIndex = slices.reduce((best, s, i) => (s.value > slices[best].value ? i : best), 0);
const percent = (value) => `${Math.round((value / total) * 100)}%`;

// Arc-label ink: whichever of dark ink / white has the higher WCAG contrast
// against the slice's own fill, so every label stays legible on any Imprint color.
const luminance = (hex) => {
  const [r, g, b] = [1, 3, 5].map((k) => {
    const c = parseInt(hex.slice(k, k + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const DARK_INK = "#1A1A17";
const labelInk = (hex) => {
  const l = luminance(hex);
  return (l + 0.05) / (luminance(DARK_INK) + 0.05) > 1.05 / (l + 0.05) ? DARK_INK : "#FFFFFF";
};
const ContrastArcLabel = (props) => <PieArcLabel {...props} style={{ fill: labelInk(props.color) }} />;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - LEGEND_BAND;
  const drawingWidth = width - MARGIN.left - MARGIN.right;
  const drawingHeight = chartHeight - MARGIN.top - MARGIN.bottom;
  const outerRadius = Math.round((Math.min(drawingWidth, drawingHeight) / 2) * 0.86);

  // Cumulative angle bounds (deg) of the exploded slice, mirroring MUI X's pie
  // layout (0 = 12 o'clock, clockwise, data order).
  const before = slices.slice(0, explodedIndex).reduce((sum, s) => sum + s.value, 0);
  const startAngle = (before / total) * 360;
  const endAngle = ((before + slices[explodedIndex].value) / total) * 360;
  const mid = ((startAngle + endAngle) / 2) * (Math.PI / 180);

  // The main series keeps every slice (and drives the legend in data order); its
  // copy of the exploded slice is hidden, and an unlabelled one-item overlay
  // series redraws that slice offset outward along its bisector.
  return (
    <div style={{ position: "relative", width, height }}>
      <div
        style={{
          position: "absolute",
          top: 28,
          left: 0,
          right: 0,
          textAlign: "center",
          fontSize: 26,
          fontWeight: 600,
          color: t.ink,
          fontFamily: "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        }}
      >
        {TITLE}
      </div>
      <PieChart
        width={width}
        height={chartHeight}
        skipAnimation
        margin={MARGIN}
        slots={{ pieArcLabel: ContrastArcLabel }}
        series={[
          {
            id: "main",
            data: slices,
            cornerRadius: 2,
            outerRadius,
            arcLabel: (item) => (item.id === slices[explodedIndex].id ? "" : percent(item.value)),
            arcLabelMinAngle: 6,
          },
          {
            id: "exploded",
            data: [{ ...slices[explodedIndex], id: "exploded", label: undefined }],
            cornerRadius: 2,
            outerRadius,
            startAngle,
            endAngle,
            cx: drawingWidth / 2 + Math.sin(mid) * EXPLODE_OFFSET,
            cy: drawingHeight / 2 - Math.cos(mid) * EXPLODE_OFFSET,
            arcLabel: (item) => percent(item.value),
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 18, color: t.ink, gap: 3 },
          },
        }}
        sx={{
          "& .MuiPieChart-arc": { stroke: t.pageBg, strokeWidth: 3 },
          [`& [data-series="main"] .MuiPieChart-arc[data-index="${explodedIndex}"]`]: {
            opacity: 0,
            pointerEvents: "none",
          },
          "& .MuiPieChart-arcLabel": { fontSize: 22, fontWeight: 700 },
        }}
      />
    </div>
  );
}
