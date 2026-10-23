// anyplot.ai
// bubble-basic: Basic Bubble Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 83/100 | Updated: 2026-09-27
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const BUBBLE_OPACITY = 0.58;
const MAX_RADIUS = 34;
const X_PAD_SHARE = 0.1;
const Y_PAD_SHARE = 0.12;
const HEADER_H = 148;

// Columns: set these to your data's column names
const X = "Revenue growth rate (%)"; // role: x
const Y = "Operating profit margin (%)"; // role: y
const SIZE = "Market share index"; // role: size

// Data: replace this block with your own records, one object per row
const data = (() => {
  let state = 42;
  const clusters = [
    { growth: 24, margin: 19, share: 64, count: 16, xSpread: 8.5, ySpread: 6.5 },
    { growth: 13, margin: 11, share: 36, count: 20, xSpread: 6.5, ySpread: 5.5 },
    { growth: 4, margin: 3.5, share: 16, count: 16, xSpread: 6.5, ySpread: 5.5 },
  ];
  const rows: { [key: string]: number }[] = [];

  for (const c of clusters) {
    for (let i = 0; i < c.count; i += 1) {
      const normals: number[] = [];
      for (let g = 0; g < 3; g += 1) {
        state = (state * 1664525 + 1013904223) % 4294967296;
        const u1 = Math.max(state / 4294967296, 1e-9);
        state = (state * 1664525 + 1013904223) % 4294967296;
        const u2 = state / 4294967296;
        normals.push(Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2));
      }
      const xVal = Math.round((c.growth + normals[0] * c.xSpread) * 10) / 10;
      const yVal = Math.round((c.margin + normals[1] * c.ySpread) * 10) / 10;
      const sVal = Math.min(100, Math.max(10, Math.round(c.share + normals[2] * 16)));
      rows.push({
        [X]: xVal,
        [Y]: yVal,
        [SIZE]: sVal,
      });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const xValues = data.map((d) => d[X]);
const yValues = data.map((d) => d[Y]);
const sizeValues = data.map((d) => d[SIZE]);

const sizeMin = Math.min(...sizeValues);
const sizeMax = Math.max(...sizeValues) || 1;

const bubbles = data.map((d, i) => ({
  id: i,
  x: d[X],
  y: d[Y],
  size: d[SIZE],
  r: MAX_RADIUS * Math.sqrt(Math.max(0, d[SIZE]) / sizeMax),
}));

const xMinRaw = Math.min(...xValues);
const xMaxRaw = Math.max(...xValues);
const xSpan = xMaxRaw - xMinRaw || 1;
const xMin = xMinRaw - xSpan * X_PAD_SHARE;
const xMax = xMaxRaw + xSpan * X_PAD_SHARE;

const yMinRaw = Math.min(...yValues);
const yMaxRaw = Math.max(...yValues);
const ySpan = yMaxRaw - yMinRaw || 1;
const yMin = yMinRaw - ySpan * Y_PAD_SHARE;
const yMax = yMaxRaw + ySpan * Y_PAD_SHARE;

const legendSizes = [
  Math.round(sizeMin),
  Math.round((sizeMin + sizeMax) / 2),
  Math.round(sizeMax),
].map((val) => ({
  val,
  r: MAX_RADIUS * Math.sqrt(Math.max(0, val) / sizeMax),
}));

const TITLE = "bubble-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} observations · Bubble area proportional to ${SIZE.toLowerCase()} (${sizeMin}–${sizeMax})`;

function Bubbles() {
  const xScale = useXScale("growth");
  const yScale = useYScale("margin");
  if (!xScale || !yScale) return null;

  return (
    <g>
      {bubbles.map((d) => {
        const cx = xScale(d.x);
        const cy = yScale(d.y);
        if (cx === undefined || cy === undefined) return null;
        return (
          <circle
            key={d.id}
            cx={cx}
            cy={cy}
            r={d.r}
            fill={t.palette[0]}
            fillOpacity={BUBBLE_OPACITY}
            stroke={t.pageBg}
            strokeWidth={2}
          />
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - HEADER_H;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        fontFamily: "Inter, system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 24,
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          <span style={{ fontWeight: 600, color: t.ink }}>{SIZE}:</span>
          {legendSizes.map((item) => (
            <div
              key={item.val}
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <svg
                width={item.r * 2 + 4}
                height={item.r * 2 + 4}
                style={{ overflow: "visible" }}
              >
                <circle
                  cx={item.r + 2}
                  cy={item.r + 2}
                  r={item.r}
                  fill={t.palette[0]}
                  fillOpacity={BUBBLE_OPACITY}
                  stroke={t.pageBg}
                  strokeWidth={1.5}
                />
              </svg>
              <span>{item.val}</span>
            </div>
          ))}
        </div>
      </div>

      <ChartsContainer
        width={width}
        height={chartHeight}
        series={[]}
        skipAnimation
        margin={{ top: 20, right: 48, bottom: 20, left: 40 }}
        xAxis={[
          {
            id: "growth",
            min: xMin,
            max: xMax,
            tickNumber: 9,
            height: 64,
            label: X,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "margin",
            min: yMin,
            max: yMax,
            tickNumber: 8,
            width: 84,
            label: Y,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": {
            stroke: t.grid,
            opacity: 0.65,
            strokeDasharray: "3 4",
          },
        }}
      >
        <ChartsGrid horizontal vertical />
        <Bubbles />
        <ChartsXAxis axisId="growth" />
        <ChartsYAxis axisId="margin" />
      </ChartsContainer>
    </div>
  );
}
