// anyplot.ai
// line-styled: Styled Line Plot
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 86/100 | Updated: 2026-10-23
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// Constants: the standard line styles, handed out in order (solid, dashed,
// dotted, dash-dot) so the chart stays legible when printed in monochrome.
// The dotted pattern is a touch dense so it keeps reading as dots at crossings.
const DASHES = ["none", "11 7", "3 5", "13 5 2 5", "18 6", "2 4 8 4"];
const LINE_WIDTH = 3;

// Columns: set these to your data's column names
const MINUTE = "Time (minutes)"; // role: x
const LATENCY = ["p50", "p90", "p99", "p99.9"]; // role: y
const Y_LABEL = "Response Latency (ms)";

// Data: replace this block with your own records, one object per row
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
const data: Record<string, number>[] = [];
let baseline = 42;
for (let i = 0; i < 60; i += 1) {
  baseline += (rand() - 0.5) * 4;
  baseline = Math.min(58, Math.max(32, baseline));
  const tailGap = 14 + rand() * 8;
  const deepTailGap = 30 + rand() * 14 + Math.sin(i / 6) * 6;
  const spike = i % 17 === 0 ? 55 + rand() * 35 : rand() * 10;
  const round = (v: number) => Math.round(v * 10) / 10;
  data.push({
    [MINUTE]: i,
    p50: round(baseline),
    p90: round(baseline + tailGap),
    p99: round(baseline + tailGap + deepTailGap),
    "p99.9": round(baseline + tailGap + deepTailGap + spike),
  });
}

// Plot: reads only data and the constants above
// Focal point: the single largest value of the deepest-tail (last) series.
const tail = LATENCY[LATENCY.length - 1];
const peak = data.reduce((best, d) => ((d[tail] ?? -Infinity) > (best[tail] ?? -Infinity) ? d : best));

// Legend swatch drawn by the native legend: a line sample in the series' own
// dash pattern, long enough to show the full pattern (MUI X's built-in "line"
// mark is solid only).
function dashMark(dash: string) {
  return function DashMark({ color }: { color?: string }) {
    return (
      <svg viewBox="0 0 44 14" width={44} height={14} style={{ display: "block" }}>
        <line x1={0} y1={7} x2={44} y2={7} stroke={color} strokeWidth={LINE_WIDTH} strokeDasharray={dash} />
      </svg>
    );
  };
}

// One stroke width for every style; the dash pattern is set per series via
// the v9 `data-series` attribute on each line path.
const lineSx = {
  "& .MuiLineChart-line": { strokeWidth: LINE_WIDTH },
  ...Object.fromEntries(
    LATENCY.map((key, i) => [`& .MuiLineChart-line[data-series="${key}"]`, { strokeDasharray: DASHES[i] }]),
  ),
};

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleHeight = 56;
  const legendHeight = 48;

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
      <LineChart
        width={width}
        height={height - titleHeight - legendHeight}
        skipAnimation
        dataset={data}
        xAxis={[
          {
            dataKey: MINUTE,
            label: MINUTE,
            scaleType: "linear",
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            label: Y_LABEL,
            width: 84,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        series={LATENCY.map((key, i) => ({
          id: key,
          dataKey: key,
          label: `${key} latency`,
          color: t.palette[i],
          curve: "monotoneX",
          showMark: false,
          labelMarkType: dashMark(DASHES[i]),
        }))}
        grid={{ horizontal: true }}
        margin={{ top: 20, right: 32, bottom: 8, left: 12 }}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
            sx: {
              fontSize: 14,
              color: t.inkSoft,
              gap: 4,
              columnGap: 4,
              pt: 1.5,
              // MUI X clamps legend marks to a 14 px square; widen it so the
              // swatch shows the whole dash pattern.
              "& .MuiChartsLegend-mark": { width: 44, height: 14 },
            },
          },
        }}
        sx={{
          ...lineSx,
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <ChartsReferenceLine
          x={peak[MINUTE]}
          label={`peak ${tail} · ${peak[tail]}ms`}
          labelAlign="start"
          spacing={{ x: -150, y: 10 }}
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "4 4" }}
          labelStyle={{ fontSize: 13, fill: t.inkSoft }}
        />
      </LineChart>
    </div>
  );
}
