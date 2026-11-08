// anyplot.ai
// heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-25
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const MEAN = "Cycle mean, blade-root flapwise moment (kN·m)"; // role: mean
const AMPLITUDE = "Cycle amplitude, half-range (kN·m)"; // role: amplitude
const COUNT = "Cycle count"; // role: count

// Data: replace this block with your own records, one object per amplitude-mean bin
// Synthetic wind-turbine blade-root flapwise bending moment: a slow operating
// trend (gusts, pitch changes) carries fast turbulent fluctuations. Three-point
// rainflow counting (ASTM E1049; full cycles weigh 1, the residual half-cycles
// 0.5) reduces it to cycles, binned into a 20 x 20 amplitude-by-mean matrix.
const data = (() => {
  let state = 42 >>> 0;
  const rng = () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };

  const signal = Array.from({ length: 6000 }, (_, i) => {
    const trend = 620 + 180 * Math.sin((2 * Math.PI * i) / 900) + 90 * Math.sin((2 * Math.PI * i) / 2600 + 1.1);
    const turbulence =
      140 * Math.sin((2 * Math.PI * i) / 41) +
      70 * Math.sin((2 * Math.PI * i) / 17 + 0.6) +
      40 * Math.sin((2 * Math.PI * i) / 6.3 + 2.4) +
      50 * (rng() - 0.5);
    return trend + turbulence;
  });

  // Rainflow counting works on reversals only: keep the turning points
  const turningPoints = [signal[0]];
  for (let i = 1; i < signal.length - 1; i += 1) {
    if (signal[i] > signal[i - 1] !== signal[i + 1] > signal[i]) turningPoints.push(signal[i]);
  }
  turningPoints.push(signal[signal.length - 1]);

  const stack: number[] = [];
  const cycles: { amplitude: number; mean: number; weight: number }[] = [];
  for (const point of turningPoints) {
    stack.push(point);
    while (stack.length >= 3) {
      const n = stack.length;
      const innerRange = Math.abs(stack[n - 2] - stack[n - 3]);
      const outerRange = Math.abs(stack[n - 1] - stack[n - 2]);
      if (innerRange > outerRange) break;
      cycles.push({ amplitude: innerRange / 2, mean: (stack[n - 2] + stack[n - 3]) / 2, weight: 1 });
      stack.splice(n - 3, 2);
    }
  }
  for (let i = 0; i < stack.length - 1; i += 1) {
    cycles.push({ amplitude: Math.abs(stack[i + 1] - stack[i]) / 2, mean: (stack[i + 1] + stack[i]) / 2, weight: 0.5 });
  }

  const binCount = 20;
  const amplitudeMax = Math.max(...cycles.map((c) => c.amplitude));
  const meanMin = Math.min(...cycles.map((c) => c.mean));
  const meanMax = Math.max(...cycles.map((c) => c.mean));
  const amplitudeWidth = amplitudeMax / binCount;
  const meanWidth = (meanMax - meanMin) / binCount;
  const weights = new Array(binCount * binCount).fill(0);
  for (const c of cycles) {
    const a = Math.min(binCount - 1, Math.floor(c.amplitude / amplitudeWidth));
    const m = Math.min(binCount - 1, Math.floor((c.mean - meanMin) / meanWidth));
    weights[a * binCount + m] += c.weight;
  }
  return weights.map((w, k) => ({
    [MEAN]: Number((meanMin + ((k % binCount) + 0.5) * meanWidth).toFixed(1)),
    [AMPLITUDE]: Number(((Math.floor(k / binCount) + 0.5) * amplitudeWidth).toFixed(1)),
    [COUNT]: Math.round(w),
  }));
})();

// Plot: reads only data and the constants above
const meanCenters = [...new Set(data.map((d) => d[MEAN]))].sort((a, b) => a - b);
const amplitudeCenters = [...new Set(data.map((d) => d[AMPLITUDE]))].sort((a, b) => a - b);
// Bin width = the smallest step between neighbouring bin centres
const meanBin = Math.min(...meanCenters.slice(1).map((v, i) => v - meanCenters[i]));
const amplitudeBin = Math.min(...amplitudeCenters.slice(1).map((v, i) => v - amplitudeCenters[i]));

const counted = data.filter((d) => d[COUNT] > 0);
const empty = data.filter((d) => !(d[COUNT] > 0));
const countMin = Math.min(...counted.map((d) => d[COUNT]));
const countMax = Math.max(...counted.map((d) => d[COUNT]));
const totalCycles = counted.reduce((s, d) => s + d[COUNT], 0);
const peak = counted.filter((d) => d[COUNT] === countMax).slice(0, 1);
// Draw order: empty bins as faint outlines, counted bins filled, the peak bin outlined on top
const cellLayers = [
  ...empty.map((d) => ({ d, filled: false, stroke: t.grid, strokeWidth: 1 })),
  ...counted.map((d) => ({ d, filled: true, stroke: "none", strokeWidth: 0 })),
  ...peak.map((d) => ({ d, filled: false, stroke: t.ink, strokeWidth: 3 })),
];

const TITLE = "heatmap-rainflow · javascript · muix · anyplot.ai";
const SUBTITLE = `${totalCycles.toLocaleString("en-US")} counted cycles in ${meanCenters.length} × ${amplitudeCenters.length} bins · empty bins left unfilled · outlined: peak bin, ${countMax.toLocaleString("en-US")} cycles`;
const HEADER_H = 82;
const LEGEND_W = 170;
const CELL_GAP = 2; // px between neighbouring cells

// Cells in data coordinates: each bin spans its centre ± half a bin width
function RainflowCells() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const colorScale = useZColorScale() as (v: number) => string;
  return (
    <g>
      {cellLayers.map(({ d, filled, stroke, strokeWidth }, i) => {
        const x0 = xScale(d[MEAN] - meanBin / 2);
        const x1 = xScale(d[MEAN] + meanBin / 2);
        const y0 = yScale(d[AMPLITUDE] + amplitudeBin / 2);
        const y1 = yScale(d[AMPLITUDE] - amplitudeBin / 2);
        return (
          <rect
            key={i}
            x={x0 + CELL_GAP / 2}
            y={y0 + CELL_GAP / 2}
            width={Math.max(x1 - x0 - CELL_GAP, 0)}
            height={Math.max(y1 - y0 - CELL_GAP, 0)}
            fill={filled ? colorScale(Math.log(d[COUNT])) : "none"}
            stroke={stroke}
            strokeWidth={strokeWidth}
          />
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartH = height - HEADER_H;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "16px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.5 }}>{SUBTITLE}</Typography>
      </Box>
      <ChartsDataProvider
        width={width - LEGEND_W}
        height={chartH}
        series={[]}
        skipAnimation
        margin={{ top: 16, right: 24, bottom: 16, left: 24 }}
        xAxis={[
          {
            scaleType: "linear",
            min: meanCenters[0] - meanBin / 2,
            max: meanCenters[meanCenters.length - 1] + meanBin / 2,
            height: 64,
            label: MEAN,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: amplitudeCenters[0] - amplitudeBin / 2,
            max: amplitudeCenters[amplitudeCenters.length - 1] + amplitudeBin / 2,
            width: 84,
            label: AMPLITUDE,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        // Log colour scale: rainflow matrices are heavily right-skewed
        zAxis={[
          {
            colorMap: {
              type: "continuous",
              min: Math.log(countMin),
              max: Math.log(countMax),
              color: [t.seq[0], t.seq[1]],
            },
          },
        ]}
      >
        <ChartsWrapper
          legendPosition={{ vertical: "middle", horizontal: "end" }}
          legendDirection="vertical"
          sx={{ width, height: chartH }}
        >
          <Box
            sx={{
              gridArea: "legend",
              width: LEGEND_W,
              height: chartH * 0.6,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <Typography sx={{ color: t.ink, fontSize: 15, mb: "8px", textAlign: "center", lineHeight: 1.3 }}>
              {COUNT}
              <br />
              (log scale)
            </Typography>
            <ContinuousColorLegend
              direction="vertical"
              thickness={20}
              labelPosition="end"
              minLabel={({ value }) => Math.round(Math.exp(Number(value))).toLocaleString("en-US")}
              maxLabel={({ value }) => Math.round(Math.exp(Number(value))).toLocaleString("en-US")}
              sx={{ flex: 1, color: t.inkSoft, fontSize: 14 }}
            />
          </Box>
          <ChartsSurface>
            <RainflowCells />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
