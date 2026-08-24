// anyplot.ai
// bullet-basic: Basic Bullet Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-24
import { BarChart } from "@mui/x-charts/BarChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly KPI dashboard: actual performance vs. target, banded by
// poor / satisfactory / good qualitative ranges (Stephen Few's design).
const kpis = [
  { label: "Quarterly Revenue ($M)", actual: 82, target: 90, ranges: [50, 75, 100] },
  { label: "New Customers Acquired", actual: 145, target: 130, ranges: [80, 120, 160] },
  { label: "Support SLA Compliance (%)", actual: 96, target: 95, ranges: [85, 95, 100] },
  { label: "Project Milestones (%)", actual: 68, target: 80, ranges: [40, 70, 100] },
];

const hexToRgba = (hex, alpha) => {
  const int = parseInt(hex.slice(1), 16);
  const r = (int >> 16) & 255;
  const g = (int >> 8) & 255;
  const b = int & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

// Grayscale range-band shading (darkest = poor, lightest = good) per spec notes.
const BAND_COLORS = [hexToRgba(t.ink, 0.26), hexToRgba(t.ink, 0.15), hexToRgba(t.ink, 0.08)];
const BAR_COLOR = t.palette[0]; // brand green — the measure, identical across every bullet

// --- Layout constants (CSS px within the mount's coordinate space) ---------
const PADDING = 48;
const TITLE_HEIGHT = 44;
const ROW_GAP = 20;
const LABEL_WIDTH = 300;
const VALUE_WIDTH = 150;
const BAND_HEIGHT = 46;

const rowAreaHeight = SIZE.height - PADDING * 2 - TITLE_HEIGHT - ROW_GAP * kpis.length;
const rowHeight = rowAreaHeight / kpis.length;
const chartWidth = SIZE.width - PADDING * 2 - LABEL_WIDTH - VALUE_WIDTH;

function Bullet({ kpi }) {
  const maxRange = kpi.ranges[2];
  const bands = [kpi.ranges[0], kpi.ranges[1] - kpi.ranges[0], kpi.ranges[2] - kpi.ranges[1]];

  return (
    <div style={{ display: "flex", alignItems: "center", height: rowHeight, gap: 20 }}>
      <div
        style={{
          width: LABEL_WIDTH,
          textAlign: "right",
          color: t.ink,
          fontSize: 16,
          fontWeight: 500,
          paddingRight: 8,
        }}
      >
        {kpi.label}
      </div>
      <div style={{ position: "relative", width: chartWidth, height: BAND_HEIGHT }}>
        {/* Background: stacked qualitative range bands, grayscale, full band height */}
        <BarChart
          width={chartWidth}
          height={BAND_HEIGHT}
          layout="horizontal"
          series={bands.map((value, i) => ({ data: [value], stack: "range", color: BAND_COLORS[i] }))}
          xAxis={[{ scaleType: "linear", min: 0, max: maxRange }]}
          yAxis={[{ scaleType: "band", data: [""], categoryGapRatio: 0.08 }]}
          margin={{ top: 0, bottom: 0, left: 0, right: 0 }}
          bottomAxis={null}
          leftAxis={null}
          slotProps={{ legend: { hidden: true } }}
          tooltip={{ trigger: "none" }}
          skipAnimation
        />
        {/* Foreground: thin actual-value bar plus the target reference line */}
        <div style={{ position: "absolute", top: 0, left: 0 }}>
          <BarChart
            width={chartWidth}
            height={BAND_HEIGHT}
            layout="horizontal"
            series={[{ data: [kpi.actual], color: BAR_COLOR }]}
            xAxis={[{ scaleType: "linear", min: 0, max: maxRange }]}
            yAxis={[{ scaleType: "band", data: [""], categoryGapRatio: 0.6 }]}
            margin={{ top: 0, bottom: 0, left: 0, right: 0 }}
            bottomAxis={null}
            leftAxis={null}
            slotProps={{ legend: { hidden: true } }}
            tooltip={{ trigger: "none" }}
            skipAnimation
          >
            <ChartsReferenceLine x={kpi.target} lineStyle={{ stroke: t.ink, strokeWidth: 3 }} />
          </BarChart>
        </div>
      </div>
      <div style={{ width: VALUE_WIDTH, color: t.inkSoft, fontSize: 15 }}>
        {kpi.actual} / {kpi.target}
      </div>
    </div>
  );
}

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  return (
    <div
      style={{
        width: SIZE.width,
        height: SIZE.height,
        padding: PADDING,
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div style={{ height: TITLE_HEIGHT, color: t.ink, fontSize: 22, fontWeight: 500 }}>
        bullet-basic · javascript · muix · anyplot.ai
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: ROW_GAP, marginTop: ROW_GAP }}>
        {kpis.map((kpi) => (
          <Bullet key={kpi.label} kpi={kpi} />
        ))}
      </div>
    </div>
  );
}
