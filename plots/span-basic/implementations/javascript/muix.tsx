// anyplot.ai
// span-basic: Basic Span Plot (Highlighted Region)
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot, MarkPlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const VERTICAL = "vertical"; // a vertical span covers a range of x; any other direction a range of y
const SPAN_OPACITY = 0.28;
const X_PAD_SHARE = 0.02;
const Y_PAD_SHARE = 0.08;
const LABEL_FONT = 15;

// Columns: set these to your data's column names
const START = "Start"; // role: start
const END = "End"; // role: end
const DIRECTION = "Direction"; // role: direction
const SPAN_LABEL = "Label"; // role: extra
const HOUR = "Hour of day (UTC)"; // role: extra
const LATENCY = "Latency (ms)"; // role: extra

// Data: replace this block with your own records, one object per row
// The underlying series: hourly API latency over one day
const series = [
  118, 112, 295, 338, 261, 124, 119, 127, 141, 155, 168, 176, 182, 179, 171, 163, 154, 146, 138, 131, 126, 122,
  119, 115,
].map((latency, hour) => ({ [HOUR]: hour, [LATENCY]: latency }));
// The spans: the overnight maintenance window (hours) and the degraded-latency zone (ms)
const data = [
  { [START]: 2, [END]: 5, [DIRECTION]: "vertical", [SPAN_LABEL]: "Maintenance window" },
  { [START]: 200, [END]: 350, [DIRECTION]: "horizontal", [SPAN_LABEL]: "Degraded latency" },
];

// Plot: reads only data and the constants above
const points = [...series].sort((a, b) => a[HOUR] - b[HOUR]);
const spans = data.map((d, i) => ({
  id: `span-${i}`,
  lo: Math.min(d[START], d[END]),
  hi: Math.max(d[START], d[END]),
  vertical: d[DIRECTION] === VERTICAL,
  label: d[SPAN_LABEL],
  color: t.palette[i + 1],
}));

const xValues = [...points.map((p) => p[HOUR]), ...spans.filter((s) => s.vertical).flatMap((s) => [s.lo, s.hi])];
const yValues = [...points.map((p) => p[LATENCY]), ...spans.filter((s) => !s.vertical).flatMap((s) => [s.lo, s.hi])];
const xSpan = Math.max(...xValues) - Math.min(...xValues);
const ySpan = Math.max(...yValues) - Math.min(...yValues);
const xMin = Math.min(...xValues) - xSpan * X_PAD_SHARE;
const xMax = Math.max(...xValues) + xSpan * X_PAD_SHARE;
const yMin = Math.min(...yValues) - ySpan * Y_PAD_SHARE;
const yMax = Math.max(...yValues) + ySpan * Y_PAD_SHARE;

const TITLE = "span-basic · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;

function SpanLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { left, top, width, height } = useDrawingArea();
  return (
    <g>
      {spans.map((s) => {
        const box = s.vertical
          ? { x: xScale(s.lo), y: top, w: xScale(s.hi) - xScale(s.lo), h: height }
          : { x: left, y: yScale(s.hi), w: width, h: yScale(s.lo) - yScale(s.hi) };
        const edges = s.vertical
          ? [box.x, box.x + box.w].map((x) => ({ x1: x, x2: x, y1: top, y2: top + height }))
          : [box.y, box.y + box.h].map((y) => ({ x1: left, x2: left + width, y1: y, y2: y }));
        return (
          <g key={s.id}>
            <rect x={box.x} y={box.y} width={box.w} height={box.h} fill={s.color} fillOpacity={SPAN_OPACITY} />
            {edges.map((e, j) => (
              <line key={j} {...e} stroke={s.color} strokeWidth={1.5} strokeDasharray="6 4" />
            ))}
            <text
              x={box.x + 12}
              y={s.vertical ? box.y + box.h - 14 : box.y + 22}
              fontSize={LABEL_FONT}
              fontWeight={600}
              fill={t.ink}
            >
              {s.label}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: TITLE_HEIGHT,
          lineHeight: `${TITLE_HEIGHT}px`,
          paddingLeft: 24,
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_HEIGHT}
        margin={{ top: 16, right: 40, bottom: 16, left: 24 }}
        skipAnimation
        series={[
          {
            type: "line",
            id: "latency",
            data: points.map((p) => p[LATENCY]),
            label: LATENCY,
            color: t.palette[0],
            showMark: true,
            shape: "circle",
            curve: "monotoneX",
          },
        ]}
        xAxis={[
          {
            data: points.map((p) => p[HOUR]),
            scaleType: "linear",
            min: xMin,
            max: xMax,
            label: HOUR,
            height: 64,
            tickMinStep: 2,
            valueFormatter: (v) => `${v}:00`,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            min: yMin,
            max: yMax,
            label: LATENCY,
            width: 76,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiLineChart-mark": { strokeWidth: 2 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal />
        <SpanLayer />
        <LinePlot skipAnimation />
        <MarkPlot skipAnimation />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </div>
  );
}
