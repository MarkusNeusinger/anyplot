// anyplot.ai
// residual-plot: Residual Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05

import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// Constants
const OUTLIER_SD = 2; // residuals beyond this many standard deviations count as outliers
const OUTLIER_COLOR = t.palette[4]; // alert red for the outliers; the bulk keeps the brand green
const PAD_SHARE = 0.04; // axis padding beyond the outermost points and bands, share of the span
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 44;

// Columns: set these to your data's column names
const OBSERVED = "Observed price (USD)"; // role: y_true
const PREDICTED = "Predicted price (USD)"; // role: y_pred

// Data: replace this block with your own records, one object per row
// 220 home sales: price regressed on floor area (600–3500 sq ft) by ordinary least squares, with
// noise that widens for larger homes; fixed-seed LCG with Box-Muller normals
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  const sqft = Array.from({ length: 220 }, () => 600 + rand() * 2900);
  const price = sqft.map((s) => {
    const z = Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
    return 42000 + s * 118 + z * (8000 + s * 18);
  });
  const mx = sqft.reduce((a, b) => a + b, 0) / sqft.length;
  const my = price.reduce((a, b) => a + b, 0) / price.length;
  const slope =
    sqft.reduce((a, s, i) => a + (s - mx) * (price[i] - my), 0) / sqft.reduce((a, s) => a + (s - mx) ** 2, 0);
  return sqft.map((s, i) => ({
    [OBSERVED]: Math.round(price[i]),
    [PREDICTED]: Math.round(my + slope * (s - mx)),
  }));
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => Number.isFinite(d[OBSERVED]) && Number.isFinite(d[PREDICTED]));
const points = rows.map((d, i) => ({ x: d[PREDICTED], y: d[OBSERVED] - d[PREDICTED], id: i }));
const meanResidual = points.reduce((s, p) => s + p.y, 0) / points.length;
const sd = Math.sqrt(points.reduce((s, p) => s + (p.y - meanResidual) ** 2, 0) / (points.length - 1));
const limit = OUTLIER_SD * sd;
const inliers = points.filter((p) => Math.abs(p.y) <= limit);
const outliers = points.filter((p) => Math.abs(p.y) > limit);
const xs = points.map((p) => p.x);
const ys = [...points.map((p) => p.y), limit, -limit];
const xPad = (Math.max(...xs) - Math.min(...xs)) * PAD_SHARE;
const yPad = (Math.max(...ys) - Math.min(...ys)) * PAD_SHARE;

const unit = OBSERVED.match(/\(([^)]+)\)/)?.[1] ?? "";
const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const TITLE = "residual-plot · javascript · muix · anyplot.ai";
const SUBTITLE = `${points.length} observations · residual = observed − predicted · SD ${fmt.format(sd)} ${unit} · ${outliers.length} beyond ±${OUTLIER_SD}σ`;

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
      <ScatterChart
        width={width}
        height={height - TITLE_H - SUBTITLE_H - LEGEND_H}
        skipAnimation
        margin={{ top: 12, right: 40, bottom: 8, left: 16 }}
        grid={{ horizontal: true, vertical: true }}
        series={[
          { id: "residuals", data: inliers, label: `Residuals within ±${OUTLIER_SD}σ`, markerSize: 6, color: t.palette[0] },
          { id: "outliers", data: outliers, label: `Outliers beyond ±${OUTLIER_SD}σ`, markerSize: 8, color: OUTLIER_COLOR },
        ]}
        xAxis={[
          {
            label: PREDICTED,
            min: Math.min(...xs) - xPad,
            max: Math.max(...xs) + xPad,
            tickNumber: 9,
            height: 64,
            valueFormatter: (v) => fmt.format(v),
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            label: `Residual (${unit})`,
            min: Math.min(...ys) - yPad,
            max: Math.max(...ys) + yPad,
            width: 92,
            valueFormatter: (v) => fmt.format(v),
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: { fontSize: 15, color: t.ink },
          },
        }}
        sx={{
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiScatterChart-marker": { stroke: t.pageBg, strokeWidth: 1 },
          '& [data-series="residuals"] .MuiScatterChart-marker': { fillOpacity: 0.6 },
        }}
      >
        <ChartsReferenceLine
          y={0}
          label="Perfect prediction: residual = 0"
          labelAlign="end"
          spacing={{ x: 8, y: 8 }}
          lineStyle={{ stroke: t.ink, strokeWidth: 2 }}
          labelStyle={{ fill: t.ink, fontSize: 14, fontWeight: 600, stroke: t.pageBg, strokeWidth: 4, paintOrder: "stroke" }}
        />
        {[1, -1].map((side) => (
          <ChartsReferenceLine
            key={side}
            y={side * limit}
            label={`${side > 0 ? "+" : "−"}${OUTLIER_SD}σ = ${side > 0 ? "" : "−"}${fmt.format(limit)}`}
            labelAlign="end"
            spacing={{ x: 8, y: 8 }}
            lineStyle={{ stroke: t.inkSoft, strokeDasharray: "8 6", strokeWidth: 1.5 }}
            labelStyle={{ fill: t.inkSoft, fontSize: 14, stroke: t.pageBg, strokeWidth: 4, paintOrder: "stroke" }}
          />
        ))}
      </ScatterChart>
    </div>
  );
}
