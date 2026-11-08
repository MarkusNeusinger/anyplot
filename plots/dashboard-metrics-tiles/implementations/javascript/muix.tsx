// anyplot.ai
// dashboard-metrics-tiles: Real-Time Dashboard Tiles
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 91/100 | Updated: 2026-11-08
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { SparkLineChart } from "@mui/x-charts/SparkLineChart";

const t = window.ANYPLOT_TOKENS;

// Constants
// Status colours as the Notes ask: green for good, amber for warning, red for critical
const STATUS_COLOR = { good: t.palette[0], warning: t.amber, critical: t.palette[4] };
// The most urgent status comes first in the dashboard's reading order
const SEVERITY_RANK = { critical: 0, warning: 1, good: 2 };
const FAVORABLE = t.palette[0];
const UNFAVORABLE = t.palette[4];
// One neutral colour for every sparkline: the status reads from the tile's stripe alone, and the
// amber warning hue is never needed as a thin line on the light page
const SPARK_COLOR = t.inkSoft;
const SPARK_PAD = 0.25; // share of a history's range left free above and below its sparkline
const SPARK_MIN_H = 130;
const TITLE = "dashboard-metrics-tiles · javascript · muix · anyplot.ai";

// Columns: set these to your data's column names
const METRIC = "Metric"; // role: metric_name
const TIME = "Sample time"; // role: extra
const VALUE = "Value"; // role: history
const CHANGE = "Change vs previous period (%)"; // role: change_percent
const STATUS = "Status"; // role: status
const UNIT = "Unit"; // role: extra
const HIGHER_IS_BETTER = "Higher is better"; // role: extra

// Data: replace this block with your own records, one object per row (one row per metric and sample;
// the latest sample of each metric is its current value)
const data = (() => {
  const samples = 16;
  const snapshot = new Date(2026, 9, 14, 14, 30);
  const metrics = [
    { name: "CPU Usage", unit: "%", end: 63, trend: -0.16, noise: 1.0, seed: 11, change: -3.7, status: "good", higherIsBetter: false },
    { name: "Memory", unit: "%", end: 58, trend: 0.17, noise: 1.0, seed: 22, change: 4.6, status: "warning", higherIsBetter: false },
    { name: "Response Time", unit: "ms", end: 187, trend: -1.28, noise: 4.0, seed: 33, change: -9.3, status: "good", higherIsBetter: false },
    { name: "Error Rate", unit: "%", end: 2.4, trend: 0.045, noise: 0.08, seed: 44, change: 12.3, status: "critical", higherIsBetter: false },
    { name: "Request Rate", unit: "req/s", end: 1834, trend: 11, noise: 35, seed: 55, change: 6.4, status: "good", higherIsBetter: true },
    { name: "Uptime", unit: "%", end: 99.95, trend: -0.001, noise: 0.015, seed: 66, change: -0.02, status: "warning", higherIsBetter: true },
  ];
  // History built backward from the current value with a fixed-seed LCG, so each sparkline ends on its headline number
  return metrics.flatMap((m) => {
    let state = m.seed;
    let value = m.end;
    const values = [m.end];
    for (let i = 1; i < samples; i += 1) {
      state = (state * 1664525 + 1013904223) % 4294967296;
      value -= m.trend + (state / 4294967296 - 0.5) * m.noise;
      values.unshift(Math.max(0, value));
    }
    return values.map((v, i) => ({
      [METRIC]: m.name,
      [TIME]: new Date(snapshot.getTime() - (samples - 1 - i) * 60000),
      [VALUE]: v,
      [CHANGE]: m.change,
      [STATUS]: m.status,
      [UNIT]: m.unit,
      [HIGHER_IS_BETTER]: m.higherIsBetter,
    }));
  });
})();

// Plot: reads only data and the constants above
const tiles = [...new Set(data.map((d) => d[METRIC]))]
  .map((name) => {
    const rows = data.filter((d) => d[METRIC] === name).sort((a, b) => a[TIME] - b[TIME]);
    const latest = rows[rows.length - 1];
    const values = rows.map((d) => d[VALUE]);
    const lo = Math.min(...values);
    const hi = Math.max(...values);
    const change = latest[CHANGE];
    const changeAbs = Math.abs(change);
    return {
      name,
      values,
      times: rows.map((d) => d[TIME]),
      yMin: lo - (hi - lo) * SPARK_PAD,
      yMax: hi + (hi - lo) * SPARK_PAD,
      status: latest[STATUS],
      accent: STATUS_COLOR[latest[STATUS]],
      current: latest[VALUE].toLocaleString("en-US", { maximumFractionDigits: 2 }),
      unit: latest[UNIT],
      up: change > 0,
      changeColor: change > 0 === latest[HIGHER_IS_BETTER] ? FAVORABLE : UNFAVORABLE,
      // Changes under one percent keep two decimals, so the arrow never sits beside a "0.0%"
      changeText: `${changeAbs.toFixed(changeAbs < 1 ? 2 : 1)}%`,
    };
  })
  .sort((a, b) => SEVERITY_RANK[a.status] - SEVERITY_RANK[b.status]);

// Grid as the Notes ask: 2x2 for 4 tiles, 3x2 for 6, 3x3 or 4x3 for more
const cols = Math.ceil(Math.sqrt(tiles.length));
const gridRows = Math.ceil(tiles.length / cols);

const allTimes = data.map((d) => d[TIME].getTime());
const spanMinutes = Math.round((Math.max(...allTimes) - Math.min(...allTimes)) / 60000);
const snapshotLabel = new Date(Math.max(...allTimes)).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
const subtitle = `Snapshot at ${snapshotLabel} · ${tiles.length} metrics · sparklines cover the last ${spanMinutes} minutes`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <Box
      sx={{
        width,
        height,
        boxSizing: "border-box",
        backgroundColor: t.pageBg,
        padding: "26px 36px 28px",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
      }}
    >
      <Box>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, marginTop: "4px" }}>{subtitle}</Typography>
      </Box>

      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          display: "grid",
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
          gridTemplateRows: `repeat(${gridRows}, 1fr)`,
          gap: "18px",
        }}
      >
        {tiles.map((tile, i) => {
          const isCritical = tile.status === "critical";
          return (
            <Box
              key={tile.name}
              sx={{
                display: "flex",
                flexDirection: "column",
                minWidth: 0,
                minHeight: 0,
                boxSizing: "border-box",
                borderRadius: "10px",
                border: `1px solid ${t.grid}`,
                borderLeft: `${isCritical ? 8 : 6}px solid ${tile.accent}`,
                background: t.elevatedBg,
                padding: "18px 24px",
              }}
            >
              <Typography sx={{ fontSize: 15, fontWeight: 500, color: t.inkSoft, letterSpacing: "0.4px" }}>
                {tile.name.toUpperCase()}
              </Typography>

              <Box sx={{ display: "flex", alignItems: "baseline", gap: "14px", marginTop: "12px" }}>
                <Typography sx={{ fontSize: 54, fontWeight: 700, color: t.ink, lineHeight: 1 }}>
                  {tile.current}
                  <Box component="span" sx={{ fontSize: 24, fontWeight: 500, color: t.inkSoft, marginLeft: "6px" }}>
                    {tile.unit}
                  </Box>
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <svg width="16" height="16" viewBox="0 0 10 10" style={{ display: "block", flexShrink: 0 }} aria-hidden="true">
                    <path d={tile.up ? "M5 1 L9 8 L1 8 Z" : "M5 9 L9 2 L1 2 Z"} fill={tile.changeColor} />
                  </svg>
                  <Typography sx={{ fontSize: 20, fontWeight: 600, color: tile.changeColor }}>{tile.changeText}</Typography>
                </Box>
              </Box>

              {/* The sparkline takes all the height the label and value leave free, so no dead band opens up */}
              <Box sx={{ flex: 1, minHeight: SPARK_MIN_H, marginTop: "16px" }}>
                <SparkLineChart
                  data={tile.values}
                  xAxis={{ data: tile.times, scaleType: "time" }}
                  yAxis={{ min: tile.yMin, max: tile.yMax }}
                  color={SPARK_COLOR}
                  area
                  baseline="min"
                  curve="monotoneX"
                  skipAnimation
                  margin={{ top: 8, bottom: 4, left: 4, right: 4 }}
                  sx={{
                    "& .MuiLineChart-area": { fill: `url(#spark-fill-${i})` },
                    "& .MuiLineChart-line": { strokeWidth: 2.5 },
                  }}
                >
                  <defs>
                    <linearGradient id={`spark-fill-${i}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={SPARK_COLOR} stopOpacity={0.3} />
                      <stop offset="100%" stopColor={SPARK_COLOR} stopOpacity={0.03} />
                    </linearGradient>
                  </defs>
                </SparkLineChart>
              </Box>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}
