// anyplot.ai
// bar-error: Bar Chart with Error Bars
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-02
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const X_PAD_SHARE = 0.08;
const CAP_WIDTH_SHARE = 0.24;

// Columns: set these to your data's column names
const CATEGORY = "Support channel"; // role: category
const VALUE = "Mean satisfaction score (0–10)"; // role: value
const ERROR = "Standard deviation (±1 SD)"; // role: error
const SAMPLE_SIZE = "Respondents per channel"; // role: extra

// Data: replace this block with your own records, one object per row
const data = [
  { [CATEGORY]: "Live Chat", [VALUE]: 8.4, [ERROR]: 0.6, [SAMPLE_SIZE]: 150 },
  { [CATEGORY]: "Phone", [VALUE]: 7.8, [ERROR]: 0.7, [SAMPLE_SIZE]: 150 },
  { [CATEGORY]: "Email", [VALUE]: 7.2, [ERROR]: 0.9, [SAMPLE_SIZE]: 150 },
  { [CATEGORY]: "Social Media", [VALUE]: 6.9, [ERROR]: 0.95, [SAMPLE_SIZE]: 150 },
  { [CATEGORY]: "Self-Service", [VALUE]: 6.5, [ERROR]: 1.1, [SAMPLE_SIZE]: 150 },
];

// Plot: reads only data and the constants above
const channels = data.map((d) => d[CATEGORY]);
const scores = data.map((d) => d[VALUE]);
const maxUpper = Math.max(...data.map((d) => d[VALUE] + d[ERROR]));
const minLower = Math.min(...data.map((d) => d[VALUE] - d[ERROR]));
const xMax = maxUpper * (1 + X_PAD_SHARE);
const xMin = Math.min(0, minLower * (1 + X_PAD_SHARE));
const formatValue = (v: number) => v.toLocaleString("en-US");
const minSample = Math.min(...data.map((d) => d[SAMPLE_SIZE]));
const maxSample = Math.max(...data.map((d) => d[SAMPLE_SIZE]));
const sampleText =
  minSample === maxSample
    ? minSample.toLocaleString("en-US")
    : `${minSample.toLocaleString("en-US")}–${maxSample.toLocaleString("en-US")}`;

function ErrorBars() {
  const xScale = useXScale("x") as any;
  const yScale = useYScale("y") as any;
  const bw = yScale.bandwidth();
  const cap = bw * CAP_WIDTH_SHARE;

  return (
    <g data-drawing-container>
      {data.map((row) => {
        const channel = row[CATEGORY];
        const cy = yScale(channel) + bw / 2;
        const xLow = xScale(row[VALUE] - row[ERROR]);
        const xHigh = xScale(row[VALUE] + row[ERROR]);
        return (
          <g key={channel}>
            <line
              x1={xLow}
              y1={cy}
              x2={xHigh}
              y2={cy}
              stroke={t.ink}
              strokeWidth={3}
              strokeLinecap="round"
            />
            <line
              x1={xLow}
              y1={cy - cap / 2}
              x2={xLow}
              y2={cy + cap / 2}
              stroke={t.ink}
              strokeWidth={3}
              strokeLinecap="round"
            />
            <line
              x1={xHigh}
              y1={cy - cap / 2}
              x2={xHigh}
              y2={cy + cap / 2}
              stroke={t.ink}
              strokeWidth={3}
              strokeLinecap="round"
            />
            <text
              x={xHigh + 12}
              y={cy + 5}
              fontSize={14}
              fontWeight={600}
              fill={t.inkSoft}
            >
              {`${formatValue(row[VALUE])} ± ${formatValue(row[ERROR])}`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

const TITLE = "bar-error · javascript · muix · anyplot.ai";
const SUBTITLE = `${CATEGORY}: ${channels.length} · ${SAMPLE_SIZE}: ${sampleText}`;
const HEADER_H = 100;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      }}
    >
      <div
        style={{
          height: HEADER_H,
          padding: "14px 48px 0 48px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            fontSize: 22,
            fontWeight: 600,
            color: t.ink,
            lineHeight: 1.25,
          }}
        >
          {TITLE}
        </div>
        <div
          style={{
            fontSize: 15,
            color: t.inkSoft,
            marginTop: 4,
          }}
        >
          {SUBTITLE}
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 20,
            marginTop: 6,
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <span
              style={{
                width: 14,
                height: 12,
                borderRadius: 3,
                backgroundColor: t.palette[0],
                display: "inline-block",
              }}
            />
            <span>{VALUE}</span>
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <svg width="20" height="12" style={{ display: "inline-block" }}>
              <line x1="2" y1="6" x2="18" y2="6" stroke={t.ink} strokeWidth="2.5" />
              <line x1="2" y1="2" x2="2" y2="10" stroke={t.ink} strokeWidth="2.5" />
              <line x1="18" y1="2" x2="18" y2="10" stroke={t.ink} strokeWidth="2.5" />
            </svg>
            <span>{ERROR}</span>
          </span>
        </div>
      </div>
      <ChartsContainer
        width={width}
        height={height - HEADER_H}
        skipAnimation
        series={[
          {
            type: "bar",
            data: scores,
            id: "satisfaction",
            label: VALUE,
            layout: "horizontal",
            color: t.palette[0],
            xAxisId: "x",
            yAxisId: "y",
          },
        ]}
        xAxis={[
          {
            id: "x",
            scaleType: "linear",
            min: xMin,
            max: xMax,
            valueFormatter: formatValue,
            height: 68,
            label: VALUE,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "y",
            scaleType: "band",
            data: channels,
            width: 140,
            label: CATEGORY,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        margin={{ top: 20, bottom: 24, left: 40, right: 90 }}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <ChartsGrid vertical />
        <BarPlot borderRadius={4} skipAnimation />
        <ErrorBars />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId="y" />
      </ChartsContainer>
    </div>
  );
}
