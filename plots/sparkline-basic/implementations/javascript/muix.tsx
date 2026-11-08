// anyplot.ai
// sparkline-basic: Basic Sparkline
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-09
import { SparkLineChart } from "@mui/x-charts/SparkLineChart";

const t = window.ANYPLOT_TOKENS;

// Constants
const AREA_OPACITY = 0.18;
const LINE_WIDTH = 2.5;

// Columns: set these to your data's column names
const METRIC = "Metric"; // role: extra
const DAY = "Day"; // role: extra
const VALUE = "Value"; // role: values

// Data: replace this block with your own records, one object per row
// Four dashboard KPIs over 45 days, each a fixed-seed random walk
const data = (() => {
  const walks = [
    { name: "Daily revenue (k$)", seed: 7, start: 82, drift: 0.9, volatility: 6 },
    { name: "Active users", seed: 19, start: 3400, drift: 12, volatility: 220 },
    { name: "Avg response time (ms)", seed: 31, start: 260, drift: -1.1, volatility: 14 },
    { name: "Conversion rate (%)", seed: 53, start: 4.2, drift: 0.02, volatility: 0.35 },
  ];
  return walks.flatMap((w) => {
    let state = w.seed;
    let value = w.start;
    return Array.from({ length: 45 }, (_, i) => {
      if (i > 0) {
        state = (state * 1664525 + 1013904223) % 4294967296;
        value = Math.max(0, value + w.drift + (state / 4294967296 - 0.5) * w.volatility);
      }
      return { [METRIC]: w.name, [DAY]: i + 1, [VALUE]: Math.round(value * 100) / 100 };
    });
  });
})();

// Plot: reads only data and the constants above
const metrics = [...new Set(data.map((d) => d[METRIC]))].map((name) => {
  const values = data
    .filter((d) => d[METRIC] === name)
    .sort((a, b) => a[DAY] - b[DAY])
    .map((d) => d[VALUE]);
  const last = values[values.length - 1];
  return {
    name,
    values,
    min: Math.min(...values),
    max: Math.max(...values),
    lastText: last.toFixed(Math.abs(last) >= 100 ? 0 : Math.abs(last) >= 10 ? 1 : 2),
  };
});
const days = data.map((d) => d[DAY]);

const TITLE = "sparkline-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${DAY} ${Math.min(...days)}–${Math.max(...days)} · each line scaled to its own range · last value beside the name`;
const HEADER_H = 96;
const PAD = 40;
const ROW_GAP = 22;
const LABEL_W = 320;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const rowH = (height - HEADER_H - PAD - ROW_GAP * (metrics.length - 1)) / metrics.length;
  const sparkW = width - PAD * 2 - LABEL_W - 24 * 2 - 32;
  const sparkH = rowH - 16;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 8,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: ROW_GAP, padding: `0 ${PAD}px ${PAD}px` }}>
        {metrics.map((m) => (
          <div
            key={m.name}
            style={{
              height: rowH,
              background: t.elevatedBg,
              borderRadius: 10,
              padding: "0 24px",
              boxSizing: "border-box",
              display: "flex",
              alignItems: "center",
              gap: 32,
            }}
          >
            <div style={{ width: LABEL_W, flexShrink: 0 }}>
              <div style={{ fontSize: 16, color: t.inkSoft }}>{m.name}</div>
              <div style={{ fontSize: 30, fontWeight: 600, color: t.ink }}>{m.lastText}</div>
            </div>
            <SparkLineChart
              data={m.values}
              width={sparkW}
              height={sparkH}
              color={t.palette[0]}
              curve="linear"
              area
              baseline="min"
              yAxis={{ min: m.min, max: m.max }}
              skipAnimation
              margin={{ top: 10, bottom: 10, left: 4, right: 4 }}
              sx={{
                "& .MuiLineChart-line": { strokeWidth: LINE_WIDTH, strokeLinejoin: "round", strokeLinecap: "round" },
                "& .MuiLineChart-area": { fillOpacity: AREA_OPACITY },
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
