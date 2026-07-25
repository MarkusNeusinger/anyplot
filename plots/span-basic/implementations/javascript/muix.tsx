// anyplot.ai
// span-basic: Basic Span Plot (Highlighted Region)
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-07-25
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useDrawingArea, useXScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const TITLE = "span-basic · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;

// --- Data (in-memory, deterministic): hourly API latency over one day -------
const hours = Array.from({ length: 24 }, (_, i) => i);
const latencyMs = [
  118, 112, 295, 338, 261, 124, 119, 127, 141, 155, 168, 176, 182, 179, 171,
  163, 154, 146, 138, 131, 126, 122, 119, 115,
];

// Overnight maintenance window: reduced capacity drives up response times.
const MAINTENANCE_START = 2;
const MAINTENANCE_END = 5;

// --- Vertical span highlighting the maintenance window -----------------------
// No ChartsReferenceArea ships in the community package (7.29.1) — a rect
// positioned via the chart's own scale/drawing-area hooks reproduces it while
// staying entirely within the @mui/x-charts community surface.
function MaintenanceSpan() {
  const xScale = useXScale();
  const { top, height } = useDrawingArea();
  const x0 = xScale(MAINTENANCE_START);
  const x1 = xScale(MAINTENANCE_END);

  return (
    <rect
      x={Math.min(x0, x1)}
      y={top}
      width={Math.abs(x1 - x0)}
      height={height}
      fill={t.amber}
      fillOpacity={0.25}
    />
  );
}

export default function Chart() {
  const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT;

  return (
    <div
      style={{
        width: window.ANYPLOT_SIZE.width,
        height: window.ANYPLOT_SIZE.height,
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          lineHeight: `${TITLE_HEIGHT}px`,
          paddingLeft: 24,
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <LineChart
        width={window.ANYPLOT_SIZE.width}
        height={chartHeight}
        skipAnimation
        series={[
          {
            data: latencyMs,
            label: "API latency",
            color: t.palette[0],
            showMark: false,
            curve: "monotoneX",
          },
        ]}
        xAxis={[
          {
            data: hours,
            scaleType: "linear",
            label: "Hour of Day (UTC)",
            valueFormatter: (v) => `${v}:00`,
            tickMinStep: 2,
          },
        ]}
        yAxis={[{ label: "Latency (ms)" }]}
        grid={{ horizontal: true }}
        slotProps={{ legend: { hidden: true } }}
      >
        <MaintenanceSpan />
        <ChartsReferenceLine
          x={MAINTENANCE_START}
          lineStyle={{ stroke: t.amber, strokeDasharray: "4 4" }}
        />
        <ChartsReferenceLine
          x={MAINTENANCE_END}
          lineStyle={{ stroke: t.amber, strokeDasharray: "4 4" }}
          label="Maintenance window"
          labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
          spacing={{ x: 10, y: 0 }}
        />
      </LineChart>
    </div>
  );
}
