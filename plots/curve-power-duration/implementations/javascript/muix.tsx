// anyplot.ai
// curve-power-duration: Mean-Maximal Power Duration Curve
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: pending | Created: 2026-06-13
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { LineChart } from "@mui/x-charts/LineChart";

const t = window.ANYPLOT_TOKENS;

// Constants
// Reference efforts of power profiling, in seconds
const REFERENCE_DURATIONS = [
  { seconds: 5, name: "5 s sprint" },
  { seconds: 60, name: "1 min" },
  { seconds: 300, name: "5 min" },
  { seconds: 1200, name: "20 min (FTP proxy)" },
];
// Human-readable tick ladder for a log time axis, in seconds (1 s up to 5 h)
const DURATION_TICKS = [1, 5, 30, 60, 300, 1200, 3600, 7200, 18000];
const WATT = "W"; // W′ is power × seconds: for a power column in watts that is joules, shown in kilojoules
const KILOJOULE = "kJ";
const HEADROOM_SHARE = 0.08; // space above the 1-second peak, as a share of it

// Columns: set these to your data's column names
const DURATION = "Effort duration"; // role: duration_s
const POWER = "Mean-maximal power (W)"; // role: power_w
const MODEL = "Critical power model (W)"; // role: model_power_w

// Data: replace this block with your own records, one object per duration in seconds
// Synthetic well-trained cyclist: 55 log-spaced durations from 1 s to 5 h; a neuromuscular plateau
// (1,100 W peak) blends below 30 s into the hyperbolic model P = CP + W′/t with CP = 280 W and
// W′ = 20 kJ, plus 3 % measurement noise; the model applies from 30 s on
const data = (() => {
  const cp = 280;
  const wPrime = 20000;
  const peak = 1100;
  const blend = 30;
  let seed = 42;
  const rand = () => {
    seed = (seed * 1664525 + 1013904223) & 0xffffffff;
    return (seed >>> 0) / 0xffffffff;
  };
  let best = Infinity;
  return Array.from({ length: 55 }, (_, i) => {
    const d = 10 ** ((i / 54) * Math.log10(18000));
    const base = d >= blend ? cp + wPrime / d : peak + (cp + wPrime / blend - peak) * (Math.log10(d) / Math.log10(blend));
    // a mean-maximal curve never rises: each best effort is capped by the shorter ones
    best = Math.min(best, base * (1 + (rand() - 0.5) * 0.03));
    return {
      [DURATION]: d,
      [POWER]: Math.round(best),
      [MODEL]: d >= blend ? Math.round(cp + wPrime / d) : null,
    };
  });
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[DURATION] - b[DURATION]);
const durations = rows.map((d) => d[DURATION]);

// CP and W′ recovered from the model column: least squares of model power on 1 / duration
const modelRows = rows.filter((d) => d[MODEL] !== null && Number.isFinite(d[MODEL]));
const inverse = modelRows.map((d) => 1 / d[DURATION]);
const modelPower = modelRows.map((d) => d[MODEL] as number);
const meanInverse = inverse.reduce((a, b) => a + b, 0) / inverse.length;
const meanPower = modelPower.reduce((a, b) => a + b, 0) / modelPower.length;
const wPrimeFit =
  inverse.reduce((s, x, i) => s + (x - meanInverse) * (modelPower[i] - meanPower), 0) /
  inverse.reduce((s, x) => s + (x - meanInverse) ** 2, 0);
const cpFit = meanPower - wPrimeFit * meanInverse;
// Units come from the power column's "(unit)" suffix; W′ carries that unit times seconds
const powerUnit = POWER.match(/\(([^)]+)\)\s*$/)?.[1] ?? "";
const wPrimeText = powerUnit === WATT ? `${(wPrimeFit / 1000).toFixed(1)} ${KILOJOULE}` : `${wPrimeFit.toFixed(0)} ${powerUnit}·s`;

const xMin = durations[0];
const xMax = durations[durations.length - 1];
const ticks = DURATION_TICKS.filter((s) => s >= xMin && s <= xMax);
const references = REFERENCE_DURATIONS.filter((r) => r.seconds >= xMin && r.seconds <= xMax);
const yMax = Math.max(...rows.map((d) => d[POWER])) * (1 + HEADROOM_SHARE);
const formatDuration = (seconds: number) => {
  const s = Math.round(seconds);
  if (s < 60) return `${s} s`;
  if (s < 3600) return `${Math.round(s / 60)} min`;
  return `${Math.round(s / 3600)} h`;
};

const TITLE = "Cyclist Power Profile · curve-power-duration · javascript · muix · anyplot.ai";
const subtitle = `${rows.length} durations from ${formatDuration(xMin)} to ${formatDuration(xMax)} · model fit CP = ${cpFit.toFixed(0)} ${powerUnit}, W′ = ${wPrimeText}`;
const HEADER_H = 88;
const LEGEND_H = 44;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: HEADER_H, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "6px", pt: "8px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2 }}>{subtitle}</Typography>
      </Box>
      <LineChart
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        margin={{ top: 16, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            id: "duration",
            data: durations,
            scaleType: "log",
            min: xMin,
            max: xMax,
            tickInterval: ticks,
            valueFormatter: formatDuration,
            label: DURATION,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "power",
            min: 0,
            max: yMax,
            label: POWER,
            width: 84,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        series={[
          { id: "empirical", label: POWER, data: rows.map((d) => d[POWER]), color: t.palette[0], showMark: false, curve: "monotoneX" },
          { id: "model", label: MODEL, data: rows.map((d) => d[MODEL]), color: t.palette[1], showMark: false, curve: "monotoneX", connectNulls: false },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: {
              fontSize: 15,
              color: t.ink,
              gap: "28px",
              '& [data-series="model"] .MuiChartsLabelMark-root': { width: 28 },
              '& [data-series="model"] .MuiChartsLabelMark-fill': { strokeDasharray: "6 4", strokeLinecap: "butt" },
            },
          },
        }}
        sx={{
          '& .MuiLineChart-line[data-series="empirical"]': { strokeWidth: 3.5 },
          '& .MuiLineChart-line[data-series="model"]': { strokeWidth: 3, strokeDasharray: "10 8" },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        {references.map((r) => (
          <ChartsReferenceLine
            key={r.name}
            x={r.seconds}
            label={r.name}
            labelAlign="start"
            lineStyle={{ stroke: t.inkSoft, strokeDasharray: "4 3", strokeWidth: 1 }}
            labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
          />
        ))}
        <ChartsReferenceLine
          y={cpFit}
          label={`Critical power ${cpFit.toFixed(0)} ${powerUnit}`}
          labelAlign="start"
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "4 3", strokeWidth: 1 }}
          labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
        />
      </LineChart>
    </Box>
  );
}
