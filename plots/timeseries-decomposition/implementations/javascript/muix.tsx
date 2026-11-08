// anyplot.ai
// timeseries-decomposition: Time Series Decomposition Plot
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-09
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const PERIOD = 12; // observations per seasonal cycle (12 for monthly data with a yearly cycle)
// The four panels of an additive decomposition, top to bottom; the seasonal and
// residual components are deviations, so their panels carry a zero line
const COMPONENTS = [
  { key: "original", name: "Original", zeroLine: false },
  { key: "trend", name: "Trend", zeroLine: false },
  { key: "seasonal", name: "Seasonal", zeroLine: true },
  { key: "residual", name: "Residual", zeroLine: true },
];
const HEADER_H = 72;
const PANEL_GAP = 6;
const X_AXIS_H = 44;
const Y_AXIS_W = 72;
const MARGIN = { top: 30, right: 32, bottom: 6, left: 16 };

// Columns: set these to your data's column names
const DATE = "Month"; // role: date
const VALUE = "Retail sales (thousand USD)"; // role: value

// Data: replace this block with your own records, one object per row
// Monthly retail sales over ten years: a rising trend, a holiday peak each
// November and December, and noise
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) % 2147483648;
    return seed / 2147483648;
  };
  const monthEffect = [-22, -18, -10, -4, 2, 6, 8, 4, -2, -6, 14, 28];
  return Array.from({ length: 120 }, (_, i) => ({
    [DATE]: new Date(2015, i, 1),
    [VALUE]: Number((240 + 1.9 * i + 0.006 * i * i + monthEffect[i % 12] + (rand() - 0.5) * 24).toFixed(1)),
  }));
})();

// Plot: reads only data and the constants above
// Classical additive decomposition: a centred moving average over one cycle gives the
// trend (half weight on both ends for an even period), the mean detrended value per
// position in the cycle gives the seasonal component, and the rest is the residual
const rows = data
  .filter((d) => d[DATE] instanceof Date && Number.isFinite(d[VALUE]))
  .sort((a, b) => a[DATE].getTime() - b[DATE].getTime());
const dates = rows.map((d) => d[DATE]);
const values = rows.map((d) => d[VALUE]);
const half = Math.floor(PERIOD / 2);
const trend = values.map((_, i) =>
  i < half || i >= values.length - half
    ? null
    : Array.from({ length: 2 * half + 1 }, (_, j) => j - half).reduce(
        (sum, k) => sum + values[i + k] * (Math.abs(k) * 2 === PERIOD ? 0.5 : 1),
        0,
      ) / PERIOD,
);
const rawIndex = Array.from({ length: PERIOD }, (_, p) => {
  const detrended = values.flatMap((v, i) => (i % PERIOD === p && trend[i] != null ? [v - trend[i]] : []));
  return detrended.reduce((sum, v) => sum + v, 0) / detrended.length;
});
const indexMean = rawIndex.reduce((sum, v) => sum + v, 0) / PERIOD;
const seasonal = values.map((_, i) => rawIndex[i % PERIOD] - indexMean);
const residual = values.map((v, i) => (trend[i] == null ? null : v - trend[i] - seasonal[i]));
const series = { original: values, trend, seasonal, residual };

const unit = VALUE.match(/\(([^)]+)\)/)?.[1] ?? VALUE;
const formatMonth = (d: Date) => d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
const TITLE = "timeseries-decomposition · javascript · muix · anyplot.ai";
const SUBTITLE = `${VALUE} · ${rows.length} observations, ${formatMonth(dates[0])} – ${formatMonth(dates[dates.length - 1])} · additive, period ${PERIOD}`;
const axisText = { tickLabelStyle: { fontSize: 14, fill: t.inkSoft }, labelStyle: { fontSize: 14, fill: t.inkSoft } };

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const panelH = (height - HEADER_H - X_AXIS_H - PANEL_GAP * (COMPONENTS.length - 1)) / COMPONENTS.length;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", gap: `${PANEL_GAP}px` }}>
      <Box sx={{ height: HEADER_H - PANEL_GAP, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "4px", pt: "6px" }}>
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 15, lineHeight: 1.2 }}>{SUBTITLE}</Typography>
      </Box>
      {COMPONENTS.map((c, i) => {
        const isLast = i === COMPONENTS.length - 1;
        return (
          <Box key={c.key} sx={{ position: "relative" }}>
            <Typography
              sx={{
                position: "absolute",
                top: 4,
                left: MARGIN.left + Y_AXIS_W + 8,
                fontSize: 16,
                fontWeight: 600,
                color: t.ink,
                pointerEvents: "none",
              }}
            >
              {c.name}
            </Typography>
            <LineChart
              width={width}
              height={panelH + (isLast ? X_AXIS_H : 0)}
              skipAnimation
              hideLegend
              grid={{ horizontal: true, vertical: true }}
              margin={MARGIN}
              xAxis={[
                {
                  data: dates,
                  scaleType: "time",
                  min: dates[0],
                  max: dates[dates.length - 1],
                  tickNumber: 10,
                  valueFormatter: formatMonth,
                  position: isLast ? "bottom" : "none",
                  height: X_AXIS_H,
                  ...axisText,
                },
              ]}
              yAxis={[{ label: unit, width: Y_AXIS_W, tickNumber: 4, ...axisText }]}
              series={[
                {
                  id: c.key,
                  data: series[c.key],
                  label: `${c.name} · ${VALUE}`,
                  color: t.palette[i],
                  showMark: false,
                  curve: "linear",
                  connectNulls: false,
                },
              ]}
              sx={{
                "& .MuiLineChart-line": { strokeWidth: 2.5 },
                "& .MuiChartsAxis-line": { stroke: t.inkSoft },
                "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
                "& .MuiChartsGrid-line": { stroke: t.grid },
              }}
            >
              {c.zeroLine && <ChartsReferenceLine y={0} lineStyle={{ stroke: t.inkSoft, strokeDasharray: "4 4" }} />}
            </LineChart>
          </Box>
        );
      })}
    </Box>
  );
}
