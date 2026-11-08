// anyplot.ai
// scatter-marginal: Scatter Plot with Marginal Distributions
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 83/100 | Updated: 2026-11-08
//# anyplot-orientation: square
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { BarChart } from "@mui/x-charts/BarChart";

const t = window.ANYPLOT_TOKENS;

// Constants
const BIN_COUNT = 22; // histogram bins per marginal, spanning the shared axis domain
const EXTENT_PAD_SHARE = 0.06; // room beyond the extreme values, as a share of each variable's span
const COUNT_HEADROOM_SHARE = 0.08; // room above the tallest marginal bar
const POINT_OPACITY = 0.62;
const MARGINAL_OPACITY = 0.34; // quieter than the points, so the scatter stays the main panel

// Columns: set these to your data's column names
const RAINFALL = "Annual rainfall (mm)"; // role: x
const YIELD = "Crop yield (t/ha)"; // role: y

// Data: replace this block with your own records, one object per row
// Field trial: seasonal rainfall against crop yield across 400 plots, with a
// moderate positive correlation plus agronomic noise.
const data = (() => {
  let seed = 42;
  const uniform = () => {
    seed = (Math.imul(seed, 1103515245) + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  const gaussian = () => Math.sqrt(-2 * Math.log(Math.max(uniform(), 1e-9))) * Math.cos(2 * Math.PI * uniform());
  return Array.from({ length: 400 }, () => {
    const rainfall = 800 + 150 * gaussian();
    const cropYield = Math.max(0.6, 1.6 + 0.0046 * rainfall + 0.7 * gaussian());
    return { [RAINFALL]: Number(rainfall.toFixed(1)), [YIELD]: Number(cropYield.toFixed(2)) };
  });
})();

// Plot: reads only data and the constants above
const points = data.map((d, i) => ({ id: i, x: d[RAINFALL], y: d[YIELD] }));
const xs = data.map((d) => d[RAINFALL]);
const ys = data.map((d) => d[YIELD]);

// One padded domain per variable drives both the scatter axis and its marginal's bins
const xPad = (Math.max(...xs) - Math.min(...xs)) * EXTENT_PAD_SHARE;
const yPad = (Math.max(...ys) - Math.min(...ys)) * EXTENT_PAD_SHARE;
const xMin = Math.min(...xs) - xPad;
const xMax = Math.max(...xs) + xPad;
const yMin = Math.min(...ys) - yPad;
const yMax = Math.max(...ys) + yPad;

const xBinWidth = (xMax - xMin) / BIN_COUNT;
const yBinWidth = (yMax - yMin) / BIN_COUNT;
const xCounts = new Array(BIN_COUNT).fill(0);
const yCounts = new Array(BIN_COUNT).fill(0);
xs.forEach((v) => {
  xCounts[Math.min(BIN_COUNT - 1, Math.floor((v - xMin) / xBinWidth))] += 1;
});
ys.forEach((v) => {
  yCounts[Math.min(BIN_COUNT - 1, Math.floor((v - yMin) / yBinWidth))] += 1;
});
const xCentres = xCounts.map((_, i) => xMin + (i + 0.5) * xBinWidth);
const yCentres = yCounts.map((_, i) => yMin + (i + 0.5) * yBinWidth);

const n = data.length;
const xMean = xs.reduce((s, v) => s + v, 0) / n;
const yMean = ys.reduce((s, v) => s + v, 0) / n;
const cov = data.reduce((s, d) => s + (d[RAINFALL] - xMean) * (d[YIELD] - yMean), 0);
const sx = Math.sqrt(xs.reduce((s, v) => s + (v - xMean) ** 2, 0));
const sy = Math.sqrt(ys.reduce((s, v) => s + (v - yMean) ** 2, 0));
const pearsonR = cov / (sx * sy);

// Layout: scatter lower left, marginals on top and right. The marginals hide their
// axes and copy the scatter's margins plus axis bands, so all drawing areas align.
const TITLE = "scatter-marginal · javascript · muix · anyplot.ai";
const SUBTITLE = `n = ${n} · Pearson r = ${pearsonR.toFixed(2)} · marginal histograms with ${BIN_COUNT} bins`;
const HEADER_HEIGHT = 76;
const GAP = 12;
const MARGINAL_SIZE = 200;
const X_AXIS_HEIGHT = 64;
const Y_AXIS_WIDTH = 76;
const MAIN_MARGIN = { left: 24, right: 8, top: 8, bottom: 16 };
const { width, height } = window.ANYPLOT_SIZE;
const plotAreaHeight = height - HEADER_HEIGHT;
const mainWidth = width - GAP - MARGINAL_SIZE;
const mainHeight = plotAreaHeight - GAP - MARGINAL_SIZE;

const markerSx = {
  "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
  "& .MuiChartsAxis-line": { stroke: t.inkSoft },
  "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
  "& .MuiScatterChart-marker": { fillOpacity: POINT_OPACITY, stroke: t.pageBg, strokeWidth: 1 },
};
const barSx = { "& .MuiBarChart-element": { fillOpacity: MARGINAL_OPACITY, stroke: t.pageBg, strokeWidth: 1 } };

export default function Chart() {
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_HEIGHT,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <div
        style={{
          width,
          height: plotAreaHeight,
          display: "grid",
          gridTemplateColumns: `${mainWidth}px ${GAP}px ${MARGINAL_SIZE}px`,
          gridTemplateRows: `${MARGINAL_SIZE}px ${GAP}px ${mainHeight}px`,
        }}
      >
        <div style={{ gridColumn: 1, gridRow: 1 }}>
          <BarChart
            width={mainWidth}
            height={MARGINAL_SIZE}
            skipAnimation
            hideLegend
            margin={{ left: MAIN_MARGIN.left + Y_AXIS_WIDTH, right: MAIN_MARGIN.right, top: 8, bottom: 0 }}
            xAxis={[{ scaleType: "band", data: xCentres, categoryGapRatio: 0, position: "none" }]}
            yAxis={[{ min: 0, max: Math.max(...xCounts) * (1 + COUNT_HEADROOM_SHARE), position: "none" }]}
            series={[{ id: "x-marginal", data: xCounts, color: t.palette[0] }]}
            sx={barSx}
          />
        </div>
        <div style={{ gridColumn: 1, gridRow: 3 }}>
          <ScatterChart
            width={mainWidth}
            height={mainHeight}
            skipAnimation
            hideLegend
            grid={{ horizontal: true, vertical: true }}
            margin={MAIN_MARGIN}
            xAxis={[
              {
                min: xMin,
                max: xMax,
                label: RAINFALL,
                height: X_AXIS_HEIGHT,
                labelStyle: { fontSize: 16, fill: t.ink },
                tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              },
            ]}
            yAxis={[
              {
                min: yMin,
                max: yMax,
                label: YIELD,
                width: Y_AXIS_WIDTH,
                labelStyle: { fontSize: 16, fill: t.ink },
                tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              },
            ]}
            series={[{ id: "plots", data: points, markerSize: 6, color: t.palette[0] }]}
            sx={markerSx}
          />
        </div>
        <div style={{ gridColumn: 3, gridRow: 3 }}>
          <BarChart
            layout="horizontal"
            width={MARGINAL_SIZE}
            height={mainHeight}
            skipAnimation
            hideLegend
            margin={{ top: MAIN_MARGIN.top, bottom: MAIN_MARGIN.bottom + X_AXIS_HEIGHT, left: 0, right: 8 }}
            yAxis={[{ scaleType: "band", data: yCentres, categoryGapRatio: 0, position: "none", reverse: true }]}
            xAxis={[{ min: 0, max: Math.max(...yCounts) * (1 + COUNT_HEADROOM_SHARE), position: "none" }]}
            series={[{ id: "y-marginal", data: yCounts, color: t.palette[0] }]}
            sx={barSx}
          />
        </div>
      </div>
    </div>
  );
}
