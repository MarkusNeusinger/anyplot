//# anyplot-orientation: landscape
// anyplot.ai
// errorbar-basic: Basic Error Bar Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-30

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Plant stress experiment: mean stem elongation (cm/week) ± 1 SD across 7 growth conditions
const CONDITIONS = ["Control", "Low Temp", "High Temp", "Low pH", "High pH", "Drought", "Flood"];
const MEANS      = [4.2,       2.8,         3.1,         2.4,      3.6,       1.9,       2.2];
const ERRORS     = [0.5,       0.7,         0.6,         0.8,      0.5,       0.6,       0.9];

// ErrorBars renders ±1 SD whiskers using the CartesianContext scale functions
function ErrorBars() {
  const xScale = useXScale("x");
  const yScale = useYScale("y");
  if (!xScale || !yScale) return null;

  const bw  = (xScale ).bandwidth();
  const cap = Math.round(bw * 0.14);

  return (
    <g>
      {CONDITIONS.map((cond, i) => {
        const cx   = (xScale )(cond) + bw / 2;
        const yTop = (yScale )(MEANS[i] + ERRORS[i]);
        const yBot = (yScale )(MEANS[i] - ERRORS[i]);
        return (
          <g key={cond}>
            {/* Vertical whisker */}
            <line x1={cx} y1={yTop} x2={cx} y2={yBot}
                  stroke={t.ink} strokeWidth={3} strokeOpacity={0.7} strokeLinecap="round" />
            {/* Top cap */}
            <line x1={cx - cap} y1={yTop} x2={cx + cap} y2={yTop}
                  stroke={t.ink} strokeWidth={3} strokeOpacity={0.7} strokeLinecap="round" />
            {/* Bottom cap */}
            <line x1={cx - cap} y1={yBot} x2={cx + cap} y2={yBot}
                  stroke={t.ink} strokeWidth={3} strokeOpacity={0.7} strokeLinecap="round" />
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  const title = "Seedling Growth Under Stress · errorbar-basic · javascript · muix · anyplot.ai";
  const titleSize = title.length > 67 ? Math.round(22 * 67 / title.length) : 22;

  return (
    <ChartContainer
      width={W}
      height={H}
      series={[{
        type: "bar",
        data: MEANS,
        id: "growth",
        label: "Mean Stem Elongation (cm/week)",
        xAxisId: "x",
        yAxisId: "y",
      }]}
      xAxis={[{
        id: "x",
        scaleType: "band",
        data: CONDITIONS,
      }]}
      yAxis={[{
        id: "y",
        min: 0,
        max: 6,
      }]}
      colors={[t.palette[0]]}
      margin={{ top: 72, bottom: 92, left: 100, right: 44 }}
    >
      <ChartsGrid horizontal />
      <BarPlot skipAnimation borderRadius={4} />
      <ErrorBars />
      <ChartsXAxis
        axisId="x"
        label="Growth Condition"
        labelStyle={{ fontSize: 16 }}
        tickLabelStyle={{ fontSize: 14 }}
      />
      <ChartsYAxis
        axisId="y"
        label="Mean Stem Elongation (cm / week)"
        labelStyle={{ fontSize: 16 }}
        tickLabelStyle={{ fontSize: 14 }}
      />
      <text
        x={W / 2}
        y={36}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={titleSize}
        fontWeight={600}
        fill={t.ink}
        fontFamily="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
      >
        {title}
      </text>
    </ChartContainer>
  );
}
