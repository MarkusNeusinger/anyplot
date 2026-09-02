// anyplot.ai
// dashboard-metrics-tiles: Real-Time Dashboard Tiles
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02
//# anyplot-orientation: landscape
// anyplot.ai
// dashboard-metrics-tiles: Real-Time Dashboard Tiles
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-02
import { Box, Typography } from "@mui/material";
import { SparkLineChart } from "@mui/x-charts/SparkLineChart";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Tiny LCG so the sparkline noise is reproducible without a browser RNG.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}

// Builds history backward from the current value so the sparkline always
// ends exactly on the tile's headline number, trending in the direction
// implied by trendPerStep.
function buildHistory(end, trendPerStep, noiseScale, seed, points = 16) {
  const rand = lcg(seed);
  const values = [end];
  let value = end;
  for (let i = 1; i < points; i += 1) {
    value -= trendPerStep + (rand() - 0.5) * noiseScale;
    values.unshift(Math.max(0, value));
  }
  return values;
}

const STATUS_COLOR = {
  good: t.palette[0],
  warning: t.amber,
  critical: t.palette[4],
};

const metrics = [
  {
    name: "CPU Usage",
    status: "good",
    increaseIsGood: false,
    changePercent: -5.2,
    currentValue: 45,
    format: (v) => `${v.toFixed(0)}%`,
    history: buildHistory(45, -0.5, 1.2, 11),
  },
  {
    name: "Memory",
    status: "warning",
    increaseIsGood: false,
    changePercent: 8.1,
    currentValue: 72,
    format: (v) => `${v.toFixed(0)}%`,
    history: buildHistory(72, 0.55, 1.2, 22),
  },
  {
    name: "Response Time",
    status: "good",
    increaseIsGood: false,
    changePercent: -14.8,
    currentValue: 120,
    format: (v) => `${v.toFixed(0)}ms`,
    history: buildHistory(120, -1.9, 3.5, 33),
  },
  {
    name: "Error Rate",
    status: "critical",
    increaseIsGood: false,
    changePercent: 12.3,
    currentValue: 2.4,
    format: (v) => `${v.toFixed(1)}%`,
    history: buildHistory(2.4, 0.045, 0.08, 44),
  },
  {
    name: "Requests / sec",
    status: "good",
    increaseIsGood: true,
    changePercent: 6.4,
    currentValue: 1834,
    format: (v) => v.toLocaleString("en-US", { maximumFractionDigits: 0 }),
    history: buildHistory(1834, 11, 35, 55),
  },
  {
    name: "Uptime",
    status: "warning",
    increaseIsGood: true,
    changePercent: -0.02,
    currentValue: 99.95,
    format: (v) => `${v.toFixed(2)}%`,
    history: buildHistory(99.95, -0.001, 0.015, 66),
  },
];

function changeColor(metric) {
  const favorable = metric.changePercent > 0 === metric.increaseIsGood;
  return favorable ? t.palette[0] : t.palette[4];
}

// --- Tile --------------------------------------------------------------------

function MetricTile({ metric }) {
  const accent = STATUS_COLOR[metric.status];
  const arrow = metric.changePercent > 0 ? "▲" : "▼";
  const lo = Math.min(...metric.history);
  const hi = Math.max(...metric.history);
  const pad = (hi - lo) * 0.25 || hi * 0.05 || 1;

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        height: "100%",
        boxSizing: "border-box",
        borderRadius: "10px",
        border: `1px solid ${t.grid}`,
        borderLeft: `6px solid ${accent}`,
        backgroundColor: t.elevatedBg,
        padding: "18px 24px",
      }}
    >
      <Typography sx={{ fontSize: 15, fontWeight: 500, color: t.inkSoft, letterSpacing: "0.4px" }}>
        {metric.name.toUpperCase()}
      </Typography>

      <Box sx={{ display: "flex", alignItems: "baseline", gap: "12px", marginTop: "4px" }}>
        <Typography sx={{ fontSize: 42, fontWeight: 700, color: t.ink, lineHeight: 1 }}>
          {metric.format(metric.currentValue)}
        </Typography>
        <Typography sx={{ fontSize: 17, fontWeight: 600, color: changeColor(metric) }}>
          {arrow} {Math.abs(metric.changePercent).toFixed(1)}%
        </Typography>
      </Box>

      <Box sx={{ height: 60, marginTop: "8px" }}>
        <SparkLineChart
          data={metric.history}
          yAxis={{ min: lo - pad, max: hi + pad }}
          colors={[accent]}
          area
          curve="monotoneX"
          showHighlight
          skipAnimation
          resolveSizeBeforeRender
          height={60}
          margin={{ top: 8, bottom: 4, left: 4, right: 4 }}
        />
      </Box>
    </Box>
  );
}

// --- Dashboard (default-exported component — the harness mounts it) --------

export default function Chart() {
  return (
    <Box
      sx={{
        width: window.ANYPLOT_SIZE.width,
        height: window.ANYPLOT_SIZE.height,
        boxSizing: "border-box",
        backgroundColor: t.pageBg,
        padding: "28px 36px",
        display: "flex",
        flexDirection: "column",
        gap: "18px",
      }}
    >
      <Typography sx={{ fontSize: 22, fontWeight: 500, color: t.ink }}>
        dashboard-metrics-tiles · javascript · muix · anyplot.ai
      </Typography>

      <Box
        sx={{
          flex: 1,
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gridTemplateRows: "repeat(2, 1fr)",
          gap: "18px",
        }}
      >
        {metrics.map((metric) => (
          <MetricTile key={metric.name} metric={metric} />
        ))}
      </Box>
    </Box>
  );
}
