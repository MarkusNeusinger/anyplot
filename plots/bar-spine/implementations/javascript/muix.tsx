// anyplot.ai
// bar-spine: Spine Plot for Two-Variable Proportions
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-02
import { BarChart } from "@mui/x-charts/BarChart";

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;
const INK_MUTED = window.ANYPLOT_THEME === "light" ? "#6B6A63" : "#A8A79F";

// --- Data (in-memory, deterministic) ----------------------------------------
// Customer counts per subscription tier, split into churned vs. retained.
// Bar WIDTH encodes each tier's marginal share of the customer base; segment
// HEIGHT encodes the conditional churn/retention split within that tier.
const tiers = [
  { name: "Free", churned: 1664, retained: 3536 },
  { name: "Basic", churned: 651, retained: 2449 },
  { name: "Pro", churned: 216, retained: 1584 },
  { name: "Enterprise", churned: 42, retained: 658 },
];

const totals = tiers.map((d) => d.churned + d.retained);
const grandTotal = totals.reduce((sum, v) => sum + v, 0);
const churnPct = tiers.map((d, i) => Math.round((d.churned / totals[i]) * 1000) / 10);
const retainPct = churnPct.map((pct) => Math.round((100 - pct) * 10) / 10);

// --- Layout: variable-width columns, each a single 100%-stacked bar --------
const PAD_H = 32;
const PAD_V = 28;
const GAP = 10;
const AXIS_LABEL_W = 26; // rotated "Share of customers" caption, drawn outside the chart SVGs
const TICK_W = 52; // reserved for the shared y-axis tick numbers, drawn only on the first column
const TITLE_H = 34;
const LEGEND_H = 28;
const CAPTION_H = 24;

const rowWidth = size.width - PAD_H * 2;
const barAreaWidth = rowWidth - AXIS_LABEL_W - TICK_W;
const barWidths = totals.map((total) => Math.round((barAreaWidth * total) / grandTotal));
barWidths[barWidths.length - 1] += barAreaWidth - barWidths.reduce((sum, w) => sum + w, 0);
const chartWidths = barWidths.map((w, i) => (i === 0 ? TICK_W + w : w));
const chartHeight = size.height - PAD_V * 2 - TITLE_H - LEGEND_H - CAPTION_H - GAP * 3;

const title = "Customer Churn by Subscription Tier · bar-spine · javascript · muix · anyplot.ai";
const titleFontSize = Math.round(18 * (title.length > 67 ? 67 / title.length : 1));

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  return (
    <div
      style={{
        width: size.width,
        height: size.height,
        padding: `${PAD_V}px ${PAD_H}px`,
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        gap: GAP,
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <div style={{ height: TITLE_H, fontSize: titleFontSize, fontWeight: 600, color: t.ink }}>
        {title}
      </div>

      <div
        style={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          gap: 20,
          fontSize: 13,
          color: t.inkSoft,
        }}
      >
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 11, height: 11, background: t.palette[0], display: "inline-block" }} />
          Retained
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 11, height: 11, background: t.palette[4], display: "inline-block" }} />
          Churned
        </span>
        <span style={{ marginLeft: "auto" }}>n = {grandTotal.toLocaleString("en-US")} customers</span>
      </div>

      <div style={{ display: "flex", height: chartHeight }}>
        <div
          style={{
            width: AXIS_LABEL_W,
            height: chartHeight,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <span
            style={{
              display: "inline-block",
              transform: "rotate(-90deg)",
              whiteSpace: "nowrap",
              fontSize: 13,
              color: t.inkSoft,
            }}
          >
            Share of customers
          </span>
        </div>
        {tiers.map((tier, i) => (
          <BarChart
            key={tier.name}
            width={chartWidths[i]}
            height={chartHeight}
            skipAnimation
            margin={{ top: 8, right: 0, bottom: 26, left: i === 0 ? TICK_W : 0 }}
            xAxis={[
              {
                scaleType: "band",
                data: [tier.name],
                categoryGapRatio: 0,
                tickLabelStyle: { fontSize: 13 },
              },
            ]}
            yAxis={[
              {
                min: 0,
                max: 100,
                disableTicks: i !== 0,
                disableLine: i !== 0,
                valueFormatter: i === 0 ? (v) => `${v}%` : () => "",
                tickLabelStyle: { fontSize: 12 },
              },
            ]}
            series={[
              { data: [retainPct[i]], label: "Retained", stack: "total", color: t.palette[0] },
              { data: [churnPct[i]], label: "Churned", stack: "total", color: t.palette[4] },
            ]}
            slotProps={{ legend: { hidden: true } }}
          />
        ))}
      </div>

      <div style={{ height: CAPTION_H, fontSize: 12, fontStyle: "italic", color: INK_MUTED }}>
        Bar width ∝ tier size · segment height = conditional churn/retention rate within tier
      </div>
    </div>
  );
}
