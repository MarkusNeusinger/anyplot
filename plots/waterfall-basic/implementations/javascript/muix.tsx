// anyplot.ai
// waterfall-basic: Basic Waterfall Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: pending | Updated: 2026-11-08

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
// Semantic colors: gains green, losses matte red, and the start and end totals
// blue, the third color the spec names for them.
const ROLE_COLORS = { increase: t.palette[0], decrease: t.palette[4], total: t.palette[2] };
const ROLE_NAMES = { increase: "Increase", decrease: "Decrease", total: "Total" };
const TITLE = "waterfall-basic · javascript · muix · anyplot.ai";
const TITLE_H = 80;
const LEGEND_H = 40;

// Columns: set these to your data's column names
const STEP = "Step"; // role: category
const AMOUNT = "Cash (USD)"; // role: value

// Data: replace this block with your own records, one object per row
// Quarterly cash bridge: the opening balance, then signed inflows and outflows,
// then the closing balance. The first row is the start total and the last row
// names the end total.
const data = [
  { [STEP]: "Opening Balance", [AMOUNT]: 120000 },
  { [STEP]: "Product Sales", [AMOUNT]: 85000 },
  { [STEP]: "Service Revenue", [AMOUNT]: 42000 },
  { [STEP]: "Refunds", [AMOUNT]: -18000 },
  { [STEP]: "Operating Costs", [AMOUNT]: -65000 },
  { [STEP]: "Taxes", [AMOUNT]: -21000 },
  { [STEP]: "Closing Balance", [AMOUNT]: 143000 },
];

// Plot: reads only data and the constants above
const steps = data.map((d) => d[STEP]);
const last = data.length - 1;
// Running total after each step. The end bar is the start plus every change,
// so it always closes the bridge; a change left empty draws no bar.
const running = [];
data.forEach((d, i) => {
  if (i === 0) running.push(d[AMOUNT]);
  else if (i === last || d[AMOUNT] == null) running.push(running[i - 1]);
  else running.push(running[i - 1] + d[AMOUNT]);
});
const isTotal = data.map((_, i) => i === 0 || i === last);
const change = data.map((d, i) => (isTotal[i] ? null : d[AMOUNT]));

// Floating bars: an invisible base segment lifts each change off the axis, and
// the visible segment on top spans the change, all in one stack.
const baseData = change.map((c, i) => (c == null ? null : c >= 0 ? running[i - 1] : running[i]));
const roleData = {
  increase: change.map((c) => (c != null && c >= 0 ? c : null)),
  decrease: change.map((c) => (c != null && c < 0 ? -c : null)),
  total: running.map((v, i) => (isTotal[i] ? v : null)),
};

// Label ink chosen by each fill's relative luminance, fixed across themes
const labelInk = Object.fromEntries(
  Object.entries(ROLE_COLORS).map(([role, hex]) => {
    const [r, g, b] = [1, 3, 5]
      .map((k) => parseInt(hex.slice(k, k + 2), 16) / 255)
      .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
    return [role, 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.179 ? "#1A1A17" : "#FAF8F1"];
  }),
);
const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });
const yMin = Math.min(0, ...running);
const SUBTITLE = `${change.filter((c) => c != null).length} changes from ${steps[0]} to ${steps[last]} · bar labels: running total`;

// Dashed connectors from the end of each bar to the start of the next, at the
// running total they share, drawn in data coordinates.
function Connectors() {
  const xScale = useXScale();
  const yScale = useYScale();
  const band = xScale.bandwidth();

  return (
    <g>
      {steps.slice(0, last).map((step, i) => (
        <line
          key={step}
          x1={xScale(step) + band}
          x2={xScale(steps[i + 1])}
          y1={yScale(running[i])}
          y2={yScale(running[i])}
          stroke={t.inkSoft}
          strokeWidth={1.75}
          strokeDasharray="6 5"
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "18px 36px 0", boxSizing: "border-box", textAlign: "center" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <div style={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: 28 }}>
        {Object.keys(ROLE_COLORS).map((role) => (
          <div key={role} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 16, height: 16, borderRadius: 3, background: ROLE_COLORS[role], display: "inline-block" }} />
            <span style={{ fontSize: 16, color: t.ink }}>{ROLE_NAMES[role]}</span>
          </div>
        ))}
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        margin={{ top: 12, right: 48, bottom: 12, left: 24 }}
        series={[
          { type: "bar", id: "base", stack: "waterfall", data: baseData, color: "transparent" },
          ...Object.keys(ROLE_COLORS).map((role) => ({
            type: "bar",
            id: role,
            stack: "waterfall",
            data: roleData[role],
            color: ROLE_COLORS[role],
            label: ROLE_NAMES[role],
            barLabel: (item) => (item.value == null ? null : compact.format(running[item.dataIndex])),
          })),
        ]}
        xAxis={[
          {
            id: "step",
            scaleType: "band",
            data: steps,
            categoryGapRatio: 0.35,
            height: 48,
            tickLabelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "amount",
            min: yMin,
            width: 88,
            label: AMOUNT,
            valueFormatter: (v) => compact.format(v),
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal />
        <BarPlot
          skipAnimation
          borderRadius={3}
          slotProps={{
            barLabel: (ownerState) => ({
              style: { fontSize: 16, fontWeight: 700, fill: labelInk[ownerState.seriesId] },
            }),
          }}
        />
        <Connectors />
        <ChartsXAxis axisId="step" />
        <ChartsYAxis axisId="amount" />
      </ChartsContainer>
    </div>
  );
}
