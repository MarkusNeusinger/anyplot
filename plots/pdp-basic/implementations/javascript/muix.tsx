// anyplot.ai
// pdp-basic: Partial Dependence Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 97/100 | Created: 2026-09-05
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// Constants
const CI_LEVEL = 95; // percent, the confidence level of the interval columns
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 40;

// Columns: set these to your data's column names
const SPEND = "Weekly marketing spend ($1,000s)"; // role: feature_values
const PD = "Partial dependence (units sold/week)"; // role: partial_dependence
const CI_LOW = "CI lower (units sold/week)"; // role: confidence_interval
const CI_HIGH = "CI upper (units sold/week)"; // role: confidence_interval
const ICE = ["Store 1041", "Store 1187", "Store 1203", "Store 1316", "Store 1422", "Store 1509", "Store 1675", "Store 1738"]; // role: ice_curves

// Data: replace this block with your own records, one object per row
// PartialDependenceDisplay-style output of a GradientBoostingRegressor that predicts weekly
// units sold from marketing spend: the average prediction, its confidence interval and the
// ICE curves of eight sampled stores on a 61-point grid (fixed-seed LCG, no browser RNG)
let lcgState = 20260905 >>> 0;
const draws = Array.from({ length: 61 + ICE.length * 63 }, () => {
  lcgState = (Math.imul(lcgState, 1664525) + 1013904223) >>> 0;
  return lcgState / 4294967296;
});
let drawIndex = 0;
const spendGrid = Array.from({ length: 61 }, (_, i) => 5 + i);
const averagePrediction = spendGrid.map((x) => 620 / (1 + Math.exp(-(x - 32) / 7)) + (draws[drawIndex++] - 0.5) * 16);
const iceByStore = ICE.map(() => {
  const midpointShift = (draws[drawIndex++] - 0.5) * 16;
  const amplitude = 0.82 + draws[drawIndex++] * 0.36;
  return spendGrid.map((x) => (620 * amplitude) / (1 + Math.exp(-(x - (32 + midpointShift)) / 7)) + (draws[drawIndex++] - 0.5) * 12);
});
const data = spendGrid.map((x, i) => {
  const halfWidth = 9 + 0.5 * Math.abs(x - 32);
  return {
    [SPEND]: x,
    [PD]: Math.round(averagePrediction[i] * 10) / 10,
    [CI_LOW]: Math.round((averagePrediction[i] - halfWidth) * 10) / 10,
    [CI_HIGH]: Math.round((averagePrediction[i] + halfWidth) * 10) / 10,
    ...Object.fromEntries(ICE.map((store, j) => [store, Math.round(iceByStore[j][i] * 10) / 10])),
  };
});

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[SPEND] - b[SPEND]);
const spend = rows.map((d) => d[SPEND]);

// Centre every curve on the mean of the partial dependence, as the spec allows
const pdValues = rows.map((d) => d[PD]).filter((v) => Number.isFinite(v));
const centre = pdValues.reduce((a, b) => a + b, 0) / pdValues.length;
const centred = Object.fromEntries(
  [PD, CI_LOW, ...ICE].map((column) => [column, rows.map((d) => (Number.isFinite(d[column]) ? d[column] - centre : null))]),
);
const ciWidth = rows.map((d) => (Number.isFinite(d[CI_LOW]) && Number.isFinite(d[CI_HIGH]) ? d[CI_HIGH] - d[CI_LOW] : null));

const unitMatch = PD.match(/\(([^)]+)\)/);
const unit = unitMatch ? unitMatch[1] : "";

const TITLE = "pdp-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length}-point feature grid · curves centred on the mean partial dependence of ${centre.toFixed(0)} ${unit}`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <LineChart
        width={width}
        height={height - TITLE_H - SUBTITLE_H - LEGEND_H}
        skipAnimation
        margin={{ top: 16, right: 48, bottom: 8, left: 16 }}
        grid={{ horizontal: true }}
        series={[
          {
            id: "ci-lower",
            data: centred[CI_LOW],
            stack: "ci",
            area: true,
            showMark: false,
            curve: "linear",
            color: t.inkSoft,
            valueFormatter: () => null,
          },
          {
            id: "ci-band",
            data: ciWidth,
            stack: "ci",
            area: true,
            showMark: false,
            curve: "linear",
            color: t.inkSoft,
            label: `${CI_LEVEL}% confidence interval`,
            valueFormatter: (v) => (v === null ? null : `± ${(v / 2).toFixed(0)} ${unit}`),
          },
          ...ICE.map((store, j) => ({
            id: `ice-${j}`,
            data: centred[store],
            showMark: false,
            curve: "linear",
            color: t.palette[0],
            label: j === 0 ? `ICE curves (${ICE.length} observations)` : undefined,
          })),
          {
            id: "pd",
            data: centred[PD],
            showMark: false,
            curve: "linear",
            color: t.palette[0],
            label: PD,
          },
        ]}
        xAxis={[
          {
            data: spend,
            scaleType: "linear",
            label: SPEND,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            label: `${PD}, centred`,
            width: 84,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: { fontSize: 15, color: t.inkSoft },
          },
        }}
        sx={{
          "& .MuiLineChart-area[data-series='ci-lower']": { fill: "none" },
          "& .MuiLineChart-area[data-series='ci-band']": { fillOpacity: 0.2 },
          "& .MuiLineChart-line[data-series='ci-lower'], & .MuiLineChart-line[data-series='ci-band']": { strokeWidth: 0 },
          "& .MuiLineChart-line[data-series^='ice-']": { strokeWidth: 1.25, strokeOpacity: 0.3 },
          "& .MuiLineChart-line[data-series='pd']": { strokeWidth: 3.5 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <ChartsReferenceLine
          y={0}
          label="mean partial dependence"
          labelAlign="end"
          labelStyle={{ fontSize: 14, fill: t.inkSoft }}
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 4" }}
        />
      </LineChart>
    </div>
  );
}
