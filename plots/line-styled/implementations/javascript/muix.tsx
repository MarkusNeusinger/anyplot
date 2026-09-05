// anyplot.ai
// line-styled: Styled Line Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-05
import {
  LineChart,
  lineElementClasses,
  getLineElementUtilityClass,
} from "@mui/x-charts/LineChart";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic mulberry32 PRNG) ------------------------
function mulberry32(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let x = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(42);

const MINUTES = Array.from({ length: 60 }, (_, i) => i);

const p50: number[] = [];
const p90: number[] = [];
const p99: number[] = [];
const p999: number[] = [];
let baseline = 42;
for (let i = 0; i < MINUTES.length; i += 1) {
  baseline += (rand() - 0.5) * 4;
  baseline = Math.min(58, Math.max(32, baseline));
  const tailGap = 14 + rand() * 8;
  const deepTailGap = 30 + rand() * 14 + Math.sin(i / 6) * 6;
  const spike = i % 17 === 0 ? 55 + rand() * 35 : rand() * 10;
  p50.push(Math.round(baseline * 10) / 10);
  p90.push(Math.round((baseline + tailGap) * 10) / 10);
  p99.push(Math.round((baseline + tailGap + deepTailGap) * 10) / 10);
  p999.push(Math.round((baseline + tailGap + deepTailGap + spike) * 10) / 10);
}

// Standard line styles mapped to series, so the chart stays legible when
// printed in monochrome (spec: solid, dashed, dotted, dash-dot).
const SERIES = [
  { id: "p50", label: "p50 latency", dash: "none" },
  { id: "p90", label: "p90 latency", dash: "11 7" },
  { id: "p99", label: "p99 latency", dash: "2 6" },
  { id: "p999", label: "p99.9 latency", dash: "13 5 2 5" },
];

// Consistent line width across styles; strokeDasharray keyed per series id
// via the utility class MUI X attaches to each line's root element.
const lineSx = {
  [`.${lineElementClasses.root}`]: { strokeWidth: 3 },
  ...Object.fromEntries(
    SERIES.map((s) => [
      `.${getLineElementUtilityClass(`series-${s.id}`)}`,
      { strokeDasharray: s.dash },
    ]),
  ),
};

// Custom legend swatch: a short dashed line sample next to the series name.
// MUI X's built-in legend only draws color squares (no dash preview) and its
// bottom-anchored position ignores the chart's own margin, so a plain HTML
// row below the chart both fixes the layout and shows the actual line style.
function LegendRow({ topGap }: { topGap: number }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        gap: 32,
        paddingTop: topGap,
        fontFamily: "system-ui, sans-serif",
      }}
    >
      {SERIES.map((s, i) => (
        <div
          key={s.id}
          style={{ display: "flex", alignItems: "center", gap: 8 }}
        >
          <svg width={40} height={14}>
            <line
              x1={0}
              y1={7}
              x2={40}
              y2={7}
              stroke={t.palette[i]}
              strokeWidth={3}
              strokeDasharray={s.dash}
            />
          </svg>
          <span style={{ fontSize: 14, color: t.inkSoft }}>{s.label}</span>
        </div>
      ))}
    </div>
  );
}

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleHeight = 56;
  const axisCaptionHeight = 26;
  const legendHeight = 48;
  const chartHeight = height - titleHeight - axisCaptionHeight - legendHeight;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: titleHeight,
          display: "flex",
          alignItems: "center",
          paddingLeft: 8,
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
          fontFamily: "system-ui, sans-serif",
        }}
      >
        line-styled · javascript · muix · anyplot.ai
      </div>
      {/* Manual y-axis caption: MUI X's rotated axis `label` collides with
          3-digit tick numbers on this data range, so it is drawn here instead. */}
      <div
        style={{
          height: axisCaptionHeight,
          display: "flex",
          alignItems: "flex-end",
          paddingLeft: 16,
          fontSize: 16,
          color: t.ink,
          fontFamily: "system-ui, sans-serif",
        }}
      >
        Response Latency (ms)
      </div>
      <LineChart
        width={width}
        height={chartHeight}
        skipAnimation
        dataset={MINUTES.map((minute, i) => ({
          minute,
          p50: p50[i],
          p90: p90[i],
          p99: p99[i],
          p999: p999[i],
        }))}
        xAxis={[
          {
            dataKey: "minute",
            label: "Time (minutes)",
            scaleType: "linear",
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        series={SERIES.map((s, i) => ({
          id: s.id,
          dataKey: s.id,
          label: s.label,
          color: t.palette[i],
          curve: "monotoneX",
          showMark: false,
        }))}
        grid={{ horizontal: true }}
        margin={{ top: 20, right: 32, bottom: 64, left: 72 }}
        slots={{ legend: () => null }}
        sx={{
          ...lineSx,
          "& .MuiChartsAxisLine": { stroke: t.inkSoft },
          "& .MuiChartsAxisTick": { stroke: t.inkSoft },
        }}
      />
      <LegendRow topGap={legendHeight - 14 - 8} />
    </div>
  );
}
