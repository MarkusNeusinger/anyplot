// anyplot.ai
// shap-summary: SHAP Summary Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";

const t = window.ANYPLOT_TOKENS;

// Constants
const SHAP_BASELINE = 0; // no impact on the prediction
const MAX_FEATURES = 20; // show only the most important features beyond this count
const MARKER_R = 5; // px
const ROW_HALF_SPREAD = 0.4; // beeswarm spread as a share of the row height, each side
const X_PAD_SHARE = 0.06; // axis padding as a share of the SHAP range
const ROW_PAD = 0.62; // rows of headroom below the last and above the first feature

// Columns: set these to your data's column names
const FEATURE = "Feature"; // role: feature_names
const SHAP = "SHAP value (impact on churn risk)"; // role: shap_values
const FEATURE_VALUE = "Feature value"; // role: feature_values

// Data: replace this block with your own records, one object per row
// SHAP values from a tree explainer on a gradient-boosted churn model: one row per
// (customer, feature); feature values in their own units.
const features: [string, number, number, number, number, number][] = [
  // name, SHAP amplitude, direction, value low, value high, decimals
  ["Support tickets (30 d)", 0.48, 1, 0, 12, 0],
  ["Days since last login", 0.4, 1, 0, 60, 0],
  ["Monthly active hours", 0.34, -1, 0, 120, 1],
  ["NPS score", 0.27, -1, 0, 10, 0],
  ["Contract length (months)", 0.22, -1, 1, 36, 0],
  ["Discount applied (%)", 0.17, 1, 0, 30, 0],
  ["Integrations enabled", 0.13, -1, 0, 8, 0],
  ["Team size (seats)", 0.09, -1, 1, 50, 0],
  ["Onboarding sessions", 0.06, -1, 0, 6, 0],
];
let seed = 42;
const data: Record<string, number | string>[] = [];
for (const [name, amplitude, direction, lo, hi, decimals] of features) {
  for (let s = 0; s < 80; s += 1) {
    seed = (Math.imul(seed, 1103515245) + 12345) & 0x7fffffff;
    const level = seed / 0x7fffffff;
    seed = (Math.imul(seed, 1103515245) + 12345) & 0x7fffffff;
    const u1 = Math.max(seed / 0x7fffffff, 1e-9);
    seed = (Math.imul(seed, 1103515245) + 12345) & 0x7fffffff;
    const u2 = seed / 0x7fffffff;
    const noise = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    const noiseScale = Math.max(0.05 + (0.5 - amplitude) * 0.08, 0.02);
    data.push({
      [FEATURE]: name,
      [SHAP]: Number((direction * amplitude * (level - 0.5) * 2 + noise * noiseScale).toFixed(4)),
      [FEATURE_VALUE]: Number((lo + level * (hi - lo)).toFixed(decimals)),
    });
  }
}

// Plot: reads only data and the constants above
const { width: W, height: H } = window.ANYPLOT_SIZE;
const names = [...new Set(data.map((d) => String(d[FEATURE])))];
const ranked = names
  .map((name) => {
    const rows = data.filter((d) => d[FEATURE] === name);
    const meanAbs = rows.reduce((s, d) => s + Math.abs(Number(d[SHAP])), 0) / rows.length;
    return { name, rows, meanAbs };
  })
  .sort((a, b) => b.meanAbs - a.meanAbs)
  .slice(0, MAX_FEATURES);
const nRows = ranked.length;
const namesBottomUp = ranked.map((f) => f.name).reverse();

const shapAll = ranked.flatMap((f) => f.rows.map((d) => Number(d[SHAP])));
const shapMin = Math.min(...shapAll, SHAP_BASELINE);
const shapMax = Math.max(...shapAll, SHAP_BASELINE);
const xPad = (shapMax - shapMin) * X_PAD_SHARE;
const xLow = shapMin - xPad;
const xHigh = shapMax + xPad;
const rowLow = -ROW_PAD;
const rowHigh = nRows - 1 + ROW_PAD;

// Layout in px, so the beeswarm can resolve collisions on screen
const HEADER_H = 84;
const LEGEND_W = 150;
const MARGIN = { top: 16, right: 24, bottom: 16, left: 16 };
const X_AXIS_H = 64;
const Y_AXIS_W = 210;
const chartW = W - LEGEND_W;
const chartH = H - HEADER_H;
const pxPerShap = (chartW - MARGIN.left - MARGIN.right - Y_AXIS_W) / (xHigh - xLow);
const pxPerRow = (chartH - MARGIN.top - MARGIN.bottom - X_AXIS_H) / (rowHigh - rowLow);
const dotPx = MARKER_R * 2 + 1.5;
const maxOffsetPx = pxPerRow * ROW_HALF_SPREAD;

// Beeswarm: every dot keeps its exact SHAP value on x; only its offset inside the row
// moves, to the nearest free slot alternating above and below the row line.
const points: { id: string; x: number; y: number; z: number }[] = [];
ranked.forEach((feature, idx) => {
  const row = nRows - 1 - idx;
  const values = feature.rows.map((d) => Number(d[FEATURE_VALUE]));
  const vMin = Math.min(...values);
  const vSpan = Math.max(...values) - vMin || 1;
  const placed: { x: number; off: number }[] = [];
  [...feature.rows]
    .sort((a, b) => Number(a[SHAP]) - Number(b[SHAP]))
    .forEach((d, i) => {
      const x = Number(d[SHAP]);
      const near = placed.filter((p) => Math.abs((x - p.x) * pxPerShap) < dotPx);
      let off = 0;
      for (let k = 0; k < 2 * Math.ceil(maxOffsetPx / (dotPx * 0.9)) + 1; k += 1) {
        const raw = (k % 2 === 1 ? 1 : -1) * Math.ceil(k / 2) * dotPx * 0.9;
        const cand = Math.max(-maxOffsetPx, Math.min(maxOffsetPx, raw));
        off = cand;
        if (near.every((p) => Math.hypot(cand - p.off, (x - p.x) * pxPerShap) >= dotPx * 0.95)) break;
      }
      placed.push({ x, off });
      points.push({
        id: `${row}-${i}`,
        x,
        y: row + off / pxPerRow,
        z: (Number(d[FEATURE_VALUE]) - vMin) / vSpan,
      });
    });
});

const title = "shap-summary · javascript · muix · anyplot.ai";
const samplesPerFeature = Math.max(...ranked.map((f) => f.rows.length));
const subtitle = `${samplesPerFeature} samples × ${nRows} features · rows ranked by mean |SHAP value| · dot color: ${FEATURE_VALUE.toLowerCase()}, scaled per feature`;

export default function Chart() {
  return (
    <div style={{ width: W, height: H, background: t.pageBg, display: "flex", flexDirection: "column" }}>
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
      <ChartsDataProvider
        width={chartW}
        height={chartH}
        margin={MARGIN}
        skipAnimation
        series={[
          {
            type: "scatter",
            id: "shap",
            label: SHAP,
            data: points,
            markerSize: MARKER_R,
            zAxisId: "feature-value",
          },
        ]}
        xAxis={[
          {
            scaleType: "linear",
            min: xLow,
            max: xHigh,
            label: SHAP,
            height: X_AXIS_H,
            valueFormatter: (v: number) => `${v > 0 ? "+" : ""}${v.toFixed(2)}`,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
            sx: { "& .MuiChartsAxis-line, & .MuiChartsAxis-tick": { stroke: t.inkSoft } },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: rowLow,
            max: rowHigh,
            width: Y_AXIS_W,
            tickInterval: namesBottomUp.map((_, i) => i),
            valueFormatter: (v: number) => namesBottomUp[Math.round(v)] ?? "",
            disableTicks: true,
            tickLabelStyle: { fontSize: 15, fill: t.ink },
            sx: { "& .MuiChartsAxis-line": { stroke: t.inkSoft } },
          },
        ]}
        zAxis={[
          {
            id: "feature-value",
            min: 0,
            max: 1,
            colorMap: { type: "continuous", min: 0, max: 1, color: [t.div[2], t.div[0]] },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "middle", horizontal: "end" }} legendDirection="vertical">
          <div
            style={{
              gridArea: "legend",
              width: LEGEND_W,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 10,
              color: t.inkSoft,
              fontSize: 15,
            }}
          >
            <span style={{ color: t.ink, fontSize: 16 }}>{FEATURE_VALUE}</span>
            <ContinuousColorLegend
              axisDirection="z"
              axisId="feature-value"
              direction="vertical"
              labelPosition="extremes"
              minLabel="Low"
              maxLabel="High"
              thickness={18}
              sx={{ height: 420, fontSize: 15, color: t.inkSoft }}
            />
          </div>
          <ChartsSurface>
            <ChartsGrid vertical />
            <ChartsReferenceLine
              x={SHAP_BASELINE}
              lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 4", strokeWidth: 1.5 }}
            />
            <ScatterPlot />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
