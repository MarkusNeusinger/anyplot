// anyplot.ai
// bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-08-20
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "NPV Sensitivity Analysis · bar-tornado-sensitivity · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 40;
const PAD_SHARE = 0.12; // room beyond the outermost bar ends for their value labels
// The two scenarios of a one-way sensitivity analysis, coloured by scenario on every bar
const LOW_LABEL = "Low input";
const HIGH_LABEL = "High input";
const BASE_LABEL = "Base case";
const LOW_COLOR = t.palette[0];
const HIGH_COLOR = t.palette[1];

// Columns: set these to your data's column names
const PARAMETER = "Input parameter"; // role: parameter
const LOW_VALUE = "NPV at low input (USD)"; // role: low_value
const HIGH_VALUE = "NPV at high input (USD)"; // role: high_value
const BASE_VALUE = "Net present value (USD)"; // role: base_value

// Data: replace this block with your own records, one object per row
// One-way sensitivity of a project's NPV: each assumption moves between its low and
// high scenario while every other one stays at the base case
const data = [
  { [PARAMETER]: "Revenue Growth Rate", [LOW_VALUE]: 1750000, [HIGH_VALUE]: 3150000, [BASE_VALUE]: 2400000 },
  { [PARAMETER]: "Discount Rate", [LOW_VALUE]: 1900000, [HIGH_VALUE]: 3000000, [BASE_VALUE]: 2400000 },
  { [PARAMETER]: "Terminal Growth Rate", [LOW_VALUE]: 2050000, [HIGH_VALUE]: 2900000, [BASE_VALUE]: 2400000 },
  { [PARAMETER]: "Operating Margin", [LOW_VALUE]: 2000000, [HIGH_VALUE]: 2750000, [BASE_VALUE]: 2400000 },
  { [PARAMETER]: "Exit Multiple", [LOW_VALUE]: 2100000, [HIGH_VALUE]: 2700000, [BASE_VALUE]: 2400000 },
  { [PARAMETER]: "Capital Expenditure", [LOW_VALUE]: 2650000, [HIGH_VALUE]: 2150000, [BASE_VALUE]: 2400000 },
  { [PARAMETER]: "Tax Rate", [LOW_VALUE]: 2550000, [HIGH_VALUE]: 2200000, [BASE_VALUE]: 2400000 },
  { [PARAMETER]: "Working Capital Change", [LOW_VALUE]: 2300000, [HIGH_VALUE]: 2500000, [BASE_VALUE]: 2400000 },
];

// Plot: reads only data and the constants above
const base = data.find((d) => d[BASE_VALUE] != null)?.[BASE_VALUE] ?? 0;
// Widest swing first, so the bars taper into the tornado shape; a missing end counts as the base case
const rows = data
  .filter((d) => d[LOW_VALUE] != null || d[HIGH_VALUE] != null)
  .sort(
    (a, b) =>
      Math.abs((b[HIGH_VALUE] ?? base) - (b[LOW_VALUE] ?? base)) -
      Math.abs((a[HIGH_VALUE] ?? base) - (a[LOW_VALUE] ?? base)),
  );
const parameters = rows.map((d) => d[PARAMETER]);

const fmt = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format;

// Value axis spans every bar end and the base case, padded for the end labels
const ends = rows.flatMap((d) => [d[LOW_VALUE], d[HIGH_VALUE]]).filter((v) => v != null);
const lo = Math.min(base, ...ends);
const hi = Math.max(base, ...ends);
const pad = (hi - lo || Math.abs(base) || 1) * PAD_SHARE;

const widest = rows[0];
const SUBTITLE = `${rows.length} parameters varied one at a time around a ${BASE_LABEL.toLowerCase()} of ${fmt(base)} · widest swing: ${widest[PARAMETER]}, ${fmt(widest[LOW_VALUE] ?? base)} to ${fmt(widest[HIGH_VALUE] ?? base)}`;

// Custom layer: each bar runs from the base case to its scenario result; when both
// results fall on one side, the longer bar is drawn first so the shorter stays visible
function TornadoBars() {
  const xScale = useXScale("npv");
  const yScale = useYScale("parameter");
  const bw = yScale.bandwidth();
  const x0 = xScale(base);

  return (
    <g>
      {rows.map((d) => {
        const y = yScale(d[PARAMETER]);
        const scenarios = [
          { key: "low", value: d[LOW_VALUE], color: LOW_COLOR },
          { key: "high", value: d[HIGH_VALUE], color: HIGH_COLOR },
        ]
          .filter((s) => s.value != null)
          .sort((a, b) => Math.abs(b.value - base) - Math.abs(a.value - base));
        return (
          <g key={d[PARAMETER]}>
            {scenarios.map((s) => {
              const xe = xScale(s.value);
              const left = s.value < base;
              return (
                <g key={s.key}>
                  <rect x={Math.min(x0, xe)} y={y} width={Math.abs(xe - x0)} height={bw} rx={3} fill={s.color} />
                  <text
                    x={xe + (left ? -8 : 8)}
                    y={y + bw / 2}
                    textAnchor={left ? "end" : "start"}
                    dominantBaseline="central"
                    fontSize={15}
                    fontWeight={500}
                    fill={t.ink}
                  >
                    {fmt(s.value)}
                  </text>
                </g>
              );
            })}
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
        {[
          { label: LOW_LABEL, color: LOW_COLOR },
          { label: HIGH_LABEL, color: HIGH_COLOR },
        ].map((s) => (
          <Box key={s.label} sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Box sx={{ width: 16, height: 16, borderRadius: "3px", bgcolor: s.color }} />
            <Typography sx={{ fontSize: 15, color: t.ink }}>{s.label}</Typography>
          </Box>
        ))}
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Box sx={{ width: 24, height: 0, borderTop: `2px dashed ${t.ink}` }} />
          <Typography sx={{ fontSize: 15, color: t.ink }}>{`${BASE_LABEL}: ${fmt(base)}`}</Typography>
        </Box>
      </Box>
      <ChartsContainer
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        series={[]}
        xAxis={[
          {
            id: "npv",
            scaleType: "linear",
            min: lo - pad,
            max: hi + pad,
            label: BASE_VALUE,
            height: 64,
            tickNumber: 8,
            valueFormatter: fmt,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "parameter",
            scaleType: "band",
            data: parameters,
            label: PARAMETER,
            width: 250,
            categoryGapRatio: 0.3,
            disableTicks: true,
            tickLabelStyle: { fontSize: 15, fill: t.ink },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        margin={{ top: 12, right: 48, bottom: 8, left: 24 }}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <ChartsGrid vertical />
        <TornadoBars />
        <ChartsReferenceLine
          x={base}
          axisId="npv"
          lineStyle={{ stroke: t.ink, strokeWidth: 2, strokeDasharray: "6 4" }}
        />
        <ChartsXAxis axisId="npv" />
        <ChartsYAxis axisId="parameter" />
      </ChartsContainer>
    </Box>
  );
}
