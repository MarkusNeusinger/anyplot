// anyplot.ai
// timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { LinePlot } from "@mui/x-charts/LineChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const LEVEL_80 = 80; // confidence levels of the two bands (%)
const LEVEL_95 = 95;
const OPACITY_80 = 0.38; // the narrower band is darker
const OPACITY_95 = 0.18;
const PAD_SHARE = 0.06; // room above and below the outermost values and bounds
const UNIT_SUFFIX = /\s*\([^)]*\)\s*$/; // a trailing "(unit)" in a column name
const HEADER_H = 112;
const MARGIN = { top: 16, right: 40, bottom: 8, left: 16 };

// Columns: set these to your data's column names
const DATE = "Month"; // role: date
const ACTUAL = "Demand (units)"; // role: actual
const FORECAST = "Forecast (units)"; // role: forecast
const LOWER_80 = "80% lower bound (units)"; // role: lower_80
const UPPER_80 = "80% upper bound (units)"; // role: upper_80
const LOWER_95 = "95% lower bound (units)"; // role: lower_95
const UPPER_95 = "95% upper bound (units)"; // role: upper_95

// Data: replace this block with your own records, one object per row
// Monthly product demand: 42 months of history and a 12-month forecast whose first
// month repeats the last observation, with normal intervals that widen with the horizon
const data = (() => {
  let state = 42;
  const random = () => {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
  const history = 42;
  const start = history - 1;
  const centre = (i: number) => 3200 + 9 * i + 260 * Math.sin((2 * Math.PI * i) / 12);
  return Array.from({ length: history + 12 }, (_, i) => {
    const actual = i <= start ? Math.round(centre(i) + (random() - 0.5) * 180) : null;
    const forecast = i < start ? null : i === start ? actual : Math.round(centre(i));
    const sigma = 70 + 26 * (i - start);
    return {
      [DATE]: new Date(2023, i, 1),
      [ACTUAL]: actual,
      [FORECAST]: forecast,
      [LOWER_80]: forecast == null ? null : Math.round(forecast - 1.2816 * sigma),
      [UPPER_80]: forecast == null ? null : Math.round(forecast + 1.2816 * sigma),
      [LOWER_95]: forecast == null ? null : Math.round(forecast - 1.96 * sigma),
      [UPPER_95]: forecast == null ? null : Math.round(forecast + 1.96 * sigma),
    };
  });
})();

// Plot: reads only data and the constants above
const rows = data
  .filter((d) => d[DATE] instanceof Date && !Number.isNaN(d[DATE].getTime()))
  .sort((a, b) => a[DATE].getTime() - b[DATE].getTime());
const dates = rows.map((d) => d[DATE]);
const forecastRows = rows.filter((d) => Number.isFinite(d[FORECAST]));
const forecastStart = forecastRows[0][DATE];
const historyRows = rows.filter((d) => Number.isFinite(d[ACTUAL]));
const horizon = forecastRows.filter((d) => !Number.isFinite(d[ACTUAL])).length;
const values = rows
  .flatMap((d) => [ACTUAL, FORECAST, LOWER_80, UPPER_80, LOWER_95, UPPER_95].map((k) => d[k]))
  .filter((v) => Number.isFinite(v));
const vMin = Math.min(...values);
const vMax = Math.max(...values);
// the wider band is drawn first, so the narrower one lies on top of it
const bands = [
  { id: "ci95", level: LEVEL_95, lower: LOWER_95, upper: UPPER_95, opacity: OPACITY_95 },
  { id: "ci80", level: LEVEL_80, lower: LOWER_80, upper: UPPER_80, opacity: OPACITY_80 },
].map((b) => ({ ...b, rows: rows.filter((d) => Number.isFinite(d[b.lower]) && Number.isFinite(d[b.upper])) }));
const formatMonth = (d: Date) => d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
const legend = [
  { key: "actual", label: ACTUAL.replace(UNIT_SUFFIX, ""), dash: false, opacity: 0 },
  { key: "forecast", label: FORECAST.replace(UNIT_SUFFIX, ""), dash: true, opacity: 0 },
  { key: "ci80", label: `${LEVEL_80}% interval`, dash: false, opacity: 1 - (1 - OPACITY_80) * (1 - OPACITY_95) },
  { key: "ci95", label: `${LEVEL_95}% interval`, dash: false, opacity: OPACITY_95 },
];

const TITLE = "Monthly Demand Forecast · timeseries-forecast-uncertainty · javascript · muix · anyplot.ai";
const SUBTITLE = `${historyRows.length} ${DATE.toLowerCase()}s of history to ${formatMonth(historyRows[historyRows.length - 1][DATE])} · ${horizon}-${DATE.toLowerCase()} forecast with ${LEVEL_80}% and ${LEVEL_95}% intervals`;
const axisText = { tickLabelStyle: { fontSize: 14, fill: t.inkSoft }, labelStyle: { fontSize: 16, fill: t.ink } };

function BandLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {bands.map((b) => (
        <path
          key={b.id}
          d={`M ${b.rows.map((d) => `${xScale(d[DATE])} ${yScale(d[b.upper])}`).join(" L ")} L ${[...b.rows]
            .reverse()
            .map((d) => `${xScale(d[DATE])} ${yScale(d[b.lower])}`)
            .join(" L ")} Z`}
          fill={t.palette[0]}
          fillOpacity={b.opacity}
          stroke="none"
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: HEADER_H, px: "56px", pt: "14px", boxSizing: "border-box" }}>
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600, lineHeight: 1.25 }}>{TITLE}</Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 15, mt: "4px" }}>{SUBTITLE}</Typography>
        <Box sx={{ display: "flex", gap: "26px", mt: "12px", alignItems: "center" }}>
          {legend.map((item) => (
            <Box key={item.key} sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
              {item.opacity > 0 ? (
                <Box sx={{ width: 20, height: 14, bgcolor: t.palette[0], opacity: item.opacity }} />
              ) : (
                <Box sx={{ width: 26, height: 0, borderTop: `3px ${item.dash ? "dashed" : "solid"} ${t.palette[0]}` }} />
              )}
              <Typography sx={{ color: t.inkSoft, fontSize: 15 }}>{item.label}</Typography>
            </Box>
          ))}
        </Box>
      </Box>
      <ChartsDataProvider
        width={width}
        height={height - HEADER_H}
        skipAnimation
        margin={MARGIN}
        xAxis={[
          {
            data: dates,
            scaleType: "time",
            min: dates[0],
            max: dates[dates.length - 1],
            tickNumber: 10,
            valueFormatter: formatMonth,
            label: DATE,
            height: 60,
            ...axisText,
          },
        ]}
        yAxis={[
          {
            min: vMin - (vMax - vMin) * PAD_SHARE,
            max: vMax + (vMax - vMin) * PAD_SHARE,
            label: ACTUAL,
            width: 84,
            valueFormatter: (v: number) => v.toLocaleString("en-US"),
            ...axisText,
          },
        ]}
        series={[
          { type: "line", id: "actual", label: legend[0].label, data: rows.map((d) => d[ACTUAL]), color: t.palette[0], showMark: false, curve: "monotoneX" },
          { type: "line", id: "forecast", label: legend[1].label, data: rows.map((d) => d[FORECAST]), color: t.palette[0], showMark: false, curve: "linear" },
        ]}
      >
        <ChartsWrapper>
          <ChartsSurface
            sx={{
              "& .MuiLineChart-line": { strokeWidth: 3 },
              '& .MuiLineChart-line[data-series="forecast"]': { strokeDasharray: "10 6" },
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
              "& .MuiChartsGrid-line": { stroke: t.grid },
            }}
          >
            <ChartsGrid horizontal />
            <BandLayer />
            <LinePlot />
            <ChartsReferenceLine
              x={forecastStart}
              label="Forecast start"
              labelAlign="start"
              lineStyle={{ stroke: t.inkSoft, strokeDasharray: "4 4", strokeWidth: 1.5 }}
              labelStyle={{ fontSize: 14, fill: t.inkSoft }}
            />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
          <ChartsTooltip trigger="axis" />
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
