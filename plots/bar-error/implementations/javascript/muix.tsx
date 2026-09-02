//# anyplot-orientation: landscape
// anyplot.ai
// bar-error: Bar Chart with Error Bars
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-02
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Customer-support survey: mean satisfaction score (0-10) ± 1 SD across ~150
// respondents per channel. Horizontal layout keeps the longer channel labels
// ("Self-Service", "Social Media") on a single, unrotated line.
const CHANNELS = [
  "Email",
  "Live Chat",
  "Phone",
  "Self-Service",
  "Social Media",
];
const SCORES = [7.2, 8.4, 7.8, 6.5, 6.9];
const ERRORS = [0.9, 0.6, 0.7, 1.1, 0.95];

// ErrorBars draws ±1 SD whiskers from the chart's own scale functions —
// horizontal layout means the whisker runs along x, its caps run along y.
function ErrorBars() {
  const xScale = useXScale("x");
  const yScale = useYScale("y");
  if (!xScale || !yScale) return null;

  const bw = (yScale as any).bandwidth();
  const cap = bw * 0.22;

  return (
    <g>
      {CHANNELS.map((channel, i) => {
        const cy = (yScale as any)(channel) + bw / 2;
        const xLow = (xScale as any)(SCORES[i] - ERRORS[i]);
        const xHigh = (xScale as any)(SCORES[i] + ERRORS[i]);
        return (
          <g key={channel}>
            <line
              x1={xLow}
              y1={cy}
              x2={xHigh}
              y2={cy}
              stroke={t.ink}
              strokeWidth={3}
              strokeOpacity={0.75}
              strokeLinecap="round"
            />
            <line
              x1={xLow}
              y1={cy - cap / 2}
              x2={xLow}
              y2={cy + cap / 2}
              stroke={t.ink}
              strokeWidth={3}
              strokeOpacity={0.75}
              strokeLinecap="round"
            />
            <line
              x1={xHigh}
              y1={cy - cap / 2}
              x2={xHigh}
              y2={cy + cap / 2}
              stroke={t.ink}
              strokeWidth={3}
              strokeOpacity={0.75}
              strokeLinecap="round"
            />
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  const title =
    "Customer Satisfaction by Support Channel · bar-error · javascript · muix · anyplot.ai";
  const titleSize =
    title.length > 67 ? Math.round(22 * (67 / title.length)) : 22;
  const subtitle = "Error bars show ±1 SD across ~150 respondents per channel";

  return (
    <ChartContainer
      width={W}
      height={H}
      series={[
        {
          type: "bar",
          data: SCORES,
          id: "satisfaction",
          label: "Mean satisfaction score (0–10)",
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
          min: 0,
          max: 10,
          label: "Mean Satisfaction Score (0–10)",
          labelStyle: { fontSize: 16, fill: t.inkSoft },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        },
      ]}
      yAxis={[
        {
          id: "y",
          scaleType: "band",
          data: CHANNELS,
          tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
        },
      ]}
      margin={{ top: 110, bottom: 90, left: 190, right: 90 }}
    >
      <ChartsGrid vertical />
      <BarPlot borderRadius={4} skipAnimation />
      <ErrorBars />
      <ChartsXAxis axisId="x" />
      <ChartsYAxis axisId="y" />
      <text
        x={W / 2}
        y={44}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={titleSize}
        fontWeight={600}
        fill={t.ink}
        fontFamily="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
      >
        {title}
      </text>
      <text
        x={W / 2}
        y={78}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={16}
        fontStyle="italic"
        fill={t.inkSoft}
        fontFamily="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
      >
        {subtitle}
      </text>
    </ChartContainer>
  );
}
