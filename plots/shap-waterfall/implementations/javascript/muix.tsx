// anyplot.ai
// shap-waterfall: SHAP Waterfall Plot for Feature Attribution
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-09

import { BarChart } from "@mui/x-charts/BarChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const MAX_FEATURES = 15; // rows shown; any further features collapse into one row
const X_PAD_SHARE = 0.14; // axis padding as a share of the chain's span, room for the value labels

// Columns: set these to your data's column names
const FEATURE = "Feature"; // role: feature
const SHAP = "SHAP value"; // role: shap_value
const BASE = "Base value"; // role: base_value
const PREDICTION = "Predicted default probability"; // role: final_value

// Data: replace this block with your own records, one object per row
// One applicant's predicted probability of loan default from a credit-scoring model,
// decomposed into per-feature SHAP contributions; the base value is the mean predicted
// default probability over the model's training sample, balanced to equal numbers of
// defaulted and repaid loans.
const data = [
  { [FEATURE]: "Credit score", [SHAP]: -0.14, [BASE]: 0.55, [PREDICTION]: 0.135 },
  { [FEATURE]: "Payment history", [SHAP]: -0.09, [BASE]: 0.55, [PREDICTION]: 0.135 },
  { [FEATURE]: "Debt-to-income ratio", [SHAP]: -0.07, [BASE]: 0.55, [PREDICTION]: 0.135 },
  { [FEATURE]: "Credit utilization", [SHAP]: -0.05, [BASE]: 0.55, [PREDICTION]: 0.135 },
  { [FEATURE]: "Annual income", [SHAP]: -0.04, [BASE]: 0.55, [PREDICTION]: 0.135 },
  { [FEATURE]: "Account age", [SHAP]: -0.035, [BASE]: 0.55, [PREDICTION]: 0.135 },
  { [FEATURE]: "Employment length", [SHAP]: -0.03, [BASE]: 0.55, [PREDICTION]: 0.135 },
  { [FEATURE]: "Number of open accounts", [SHAP]: 0.025, [BASE]: 0.55, [PREDICTION]: 0.135 },
  { [FEATURE]: "Recent credit inquiries", [SHAP]: 0.02, [BASE]: 0.55, [PREDICTION]: 0.135 },
  { [FEATURE]: "Delinquencies (past 2 years)", [SHAP]: 0.015, [BASE]: 0.55, [PREDICTION]: 0.135 },
  { [FEATURE]: "Loan purpose", [SHAP]: -0.012, [BASE]: 0.55, [PREDICTION]: 0.135 },
  { [FEATURE]: "Home ownership", [SHAP]: -0.01, [BASE]: 0.55, [PREDICTION]: 0.135 },
  { [FEATURE]: "Public records", [SHAP]: 0.008, [BASE]: 0.55, [PREDICTION]: 0.135 },
  { [FEATURE]: "Existing loan count", [SHAP]: -0.006, [BASE]: 0.55, [PREDICTION]: 0.135 },
];

// Plot: reads only data and the constants above
const baseValue = Number(data[0][BASE]);
const prediction = Number(data[0][PREDICTION]);
const ranked = [...data].sort((a, b) => Math.abs(Number(b[SHAP])) - Math.abs(Number(a[SHAP])));
const kept = ranked.length > MAX_FEATURES ? ranked.slice(0, MAX_FEATURES - 1) : ranked;
const rest = ranked.slice(kept.length);
const contributions = [
  ...kept.map((d) => ({ label: String(d[FEATURE]), shap: Number(d[SHAP]) })),
  ...(rest.length > 0
    ? [{ label: `${rest.length} other features`, shap: rest.reduce((s, d) => s + Number(d[SHAP]), 0) }]
    : []),
];

// Chain from the base value, largest contribution first (top row)
let running = baseValue;
const rows = contributions.map((c) => {
  const start = running;
  running += c.shap;
  return { ...c, start, end: running };
});
const last = rows[rows.length - 1];

const lo = Math.min(baseValue, prediction, ...rows.map((r) => r.end));
const hi = Math.max(baseValue, prediction, ...rows.map((r) => r.end));
const xPad = (hi - lo) * X_PAD_SHARE;
const offset = rows.map((r) => Math.min(r.start, r.end));
const increase = rows.map((r) => (r.shap > 0 ? r.shap : null));
const decrease = rows.map((r) => (r.shap < 0 ? -r.shap : null));
const risingColor = t.palette[4]; // red: pushes the prediction up
const fallingColor = t.palette[2]; // blue: pushes the prediction down

const title = "shap-waterfall · javascript · muix · anyplot.ai";
const subtitle = `${BASE} ${baseValue.toFixed(3)} → ${PREDICTION} ${prediction.toFixed(3)} · ${data.length} features ordered by |${SHAP}|, largest at the top`;
const HEADER_H = 84;
const LEGEND_H = 44;

function ChainLayer() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as ((v: string) => number) & { bandwidth: () => number };
  const half = yScale.bandwidth() / 2;
  // The prediction label sits on the last row, the chain's end, on the side its value label leaves free
  const lastRises = last.shap > 0;
  return (
    <g>
      {rows.slice(0, -1).map((r, i) => (
        <line
          key={`link-${r.label}`}
          x1={xScale(r.end)}
          x2={xScale(r.end)}
          y1={yScale(r.label) + half}
          y2={yScale(rows[i + 1].label) + half}
          stroke={t.inkSoft}
          strokeWidth={1.25}
          strokeDasharray="3 3"
        />
      ))}
      {rows.map((r) => (
        <text
          key={`value-${r.label}`}
          x={xScale(r.end) + (r.shap > 0 ? 8 : -8)}
          y={yScale(r.label) + half}
          textAnchor={r.shap > 0 ? "start" : "end"}
          dominantBaseline="central"
          fontSize={14}
          fontWeight={600}
          fill={t.ink}
          paintOrder="stroke"
          stroke={t.pageBg}
          strokeWidth={5}
          strokeLinejoin="round"
        >
          {`${r.shap > 0 ? "+" : "−"}${Math.abs(r.shap).toFixed(3)}`}
        </text>
      ))}
      <text
        x={lastRises ? xScale(Math.min(last.start, last.end)) - 12 : xScale(Math.max(last.start, last.end)) + 12}
        y={yScale(last.label) + half}
        textAnchor={lastRises ? "end" : "start"}
        dominantBaseline="central"
        fontSize={14}
        fontWeight={600}
        fill={t.ink}
        paintOrder="stroke"
        stroke={t.pageBg}
        strokeWidth={5}
        strokeLinejoin="round"
      >
        {`${PREDICTION} ${prediction.toFixed(3)}`}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{title}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <BarChart
        width={width}
        height={height - HEADER_H - LEGEND_H}
        layout="horizontal"
        skipAnimation
        margin={{ top: 36, right: 48, bottom: 8, left: 16 }}
        series={[
          { id: "offset", data: offset, stack: "chain", color: "transparent" },
          { id: "up", label: "Pushes the prediction up", data: increase, stack: "chain", color: risingColor },
          { id: "down", label: "Pushes the prediction down", data: decrease, stack: "chain", color: fallingColor },
        ]}
        xAxis={[
          {
            min: lo - xPad,
            max: hi + xPad,
            label: `${PREDICTION} (base value + cumulative SHAP)`,
            height: 64,
            valueFormatter: (v: number) => v.toFixed(2),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
            sx: { "& .MuiChartsAxis-line, & .MuiChartsAxis-tick": { stroke: t.inkSoft } },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: rows.map((r) => r.label),
            width: 220,
            disableTicks: true,
            tickLabelStyle: { fontSize: 15, fill: t.ink },
            sx: { "& .MuiChartsAxis-line": { stroke: t.inkSoft } },
          },
        ]}
        grid={{ vertical: true }}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 16, color: t.ink, pt: "12px" },
          },
        }}
      >
        <ChartsReferenceLine
          x={baseValue}
          label={`${BASE} ${baseValue.toFixed(3)}`}
          labelAlign="start"
          spacing={{ x: 8, y: -26 }}
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 4", strokeWidth: 1.5 }}
          labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
        />
        <ChartsReferenceLine
          x={prediction}
          lineStyle={{ stroke: t.ink, strokeDasharray: "6 4", strokeWidth: 1.5 }}
        />
        <ChainLayer />
      </BarChart>
    </div>
  );
}
