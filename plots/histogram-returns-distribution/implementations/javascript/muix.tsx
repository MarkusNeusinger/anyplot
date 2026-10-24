// anyplot.ai
// histogram-returns-distribution: Returns Distribution Histogram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-09-02

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useDrawingArea, useXScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = '"Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, sans-serif';
const MONO = '"JetBrains Mono", "SFMono-Regular", Menlo, monospace';
const Y_AXIS_LABEL = "Probability density";
const CORE_SERIES_LABEL = "Within ±2σ";
const TAIL_SERIES_LABEL = "Beyond ±2σ (tail)";
const NORMAL_SERIES_LABEL = "Normal fit";

const BIN_COUNT = 26;
const TAIL_SIGMA_MULT = 2.0;
const Y_TOP_PAD_SHARE = 0.14;

// Columns: set these to your data's column names
const DATE = "Trading date"; // role: date
const RETURNS = "Daily return (%)"; // role: returns

// Data: replace this block with your own records
const N_DAYS = 252;
const DAILY_VOL = 1.15;
const DRIFT = 0.04;

let seed = 42;
const data: Array<{
  [DATE]: string;
  [RETURNS]: number;
}> = [];

const baseMs = Date.UTC(2025, 0, 2);
for (let i = 0; i < N_DAYS; i += 1) {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  const u1 = Math.max(seed / 0x7fffffff, 1e-12);
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  const u2 = seed / 0x7fffffff;
  const z1 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);

  let r = DRIFT + z1 * DAILY_VOL;

  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  const shockRoll = seed / 0x7fffffff;
  if (shockRoll < 0.06) {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    const su1 = Math.max(seed / 0x7fffffff, 1e-12);
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    const su2 = seed / 0x7fffffff;
    const sz = Math.sqrt(-2 * Math.log(su1)) * Math.cos(2 * Math.PI * su2);
    r -= Math.abs(sz) * DAILY_VOL * 2.2;
  }

  const weekIdx = Math.floor(i / 5);
  const dayInWeek = i % 5;
  const dateStr = new Date(baseMs + (weekIdx * 7 + dayInWeek) * 86400000)
    .toISOString()
    .slice(0, 10);

  data.push({
    [DATE]: dateStr,
    [RETURNS]: r,
  });
}

// Plot: reads only data and the constants above
const unitMatch = RETURNS.match(/\(([^)]+)\)/);
const returnUnit = unitMatch ? unitMatch[1] : "";

const periodReturns = data.map((row) => row[RETURNS]);
const periodDates = data.map((row) => row[DATE]);
const startDate = periodDates[0];
const endDate = periodDates[periodDates.length - 1];

const n = periodReturns.length;
const mean = periodReturns.reduce((a, b) => a + b, 0) / n;
const variance = periodReturns.reduce((a, b) => a + (b - mean) ** 2, 0) / n;
const std = Math.sqrt(variance);
const skewness =
  periodReturns.reduce((a, b) => a + ((b - mean) / std) ** 3, 0) / n;
const excessKurtosis =
  periodReturns.reduce((a, b) => a + ((b - mean) / std) ** 4, 0) / n - 3;

const minReturn = Math.min(...periodReturns);
const maxReturn = Math.max(...periodReturns);
const binWidth = (maxReturn - minReturn) / BIN_COUNT;
const binCounts = new Array<number>(BIN_COUNT).fill(0);
for (let i = 0; i < n; i += 1) {
  const r = periodReturns[i];
  const idx = Math.min(
    BIN_COUNT - 1,
    Math.max(0, Math.floor((r - minReturn) / binWidth)),
  );
  binCounts[idx] += 1;
}

const binCenters = binCounts.map((_, i) => minReturn + binWidth * (i + 0.5));
const density = binCounts.map((c) => c / (n * binWidth));
const normalCurve = binCenters.map(
  (c) =>
    Math.exp(-0.5 * ((c - mean) / std) ** 2) / (std * Math.sqrt(2 * Math.PI)),
);

const lowerTail = mean - TAIL_SIGMA_MULT * std;
const upperTail = mean + TAIL_SIGMA_MULT * std;
const coreDensity = density.map((d, i) =>
  binCenters[i] < lowerTail || binCenters[i] > upperTail ? 0 : d,
);
const tailDensity = density.map((d, i) =>
  binCenters[i] < lowerTail || binCenters[i] > upperTail ? d : 0,
);
const tailPeriodCount = periodReturns.filter(
  (r) => r < lowerTail || r > upperTail,
).length;

const maxDensity = Math.max(...density, ...normalCurve);
const yMax = maxDensity * (1 + Y_TOP_PAD_SHARE);

const CORE_COLOR = t.palette[0];
const TAIL_COLOR = t.palette[1];
const NORMAL_COLOR = t.ink;

function MeanReferenceLineLayer() {
  const { top, height } = useDrawingArea();
  const xScale = useXScale() as unknown as ((v: number) => number) & {
    bandwidth: () => number;
  };
  const bw = xScale.bandwidth();
  const leftBinIdx = Math.max(
    0,
    Math.min(BIN_COUNT - 2, Math.floor((mean - binCenters[0]) / binWidth)),
  );
  const cLeft = binCenters[leftBinIdx];
  const cRight = binCenters[leftBinIdx + 1];
  const xLeft = xScale(cLeft) + bw / 2;
  const xRight = xScale(cRight) + bw / 2;
  const frac = (mean - cLeft) / binWidth;
  const meanX = xLeft + frac * (xRight - xLeft);

  return (
    <g>
      <line
        x1={meanX}
        y1={top}
        x2={meanX}
        y2={top + height}
        stroke={t.ink}
        strokeDasharray="6 4"
        strokeWidth={1.75}
      />
      <text
        x={meanX + 8}
        y={top + 18}
        fill={t.ink}
        fontSize={14}
        fontWeight={600}
        fontFamily={MONO}
      >
        Mean ({mean >= 0 ? "+" : ""}
        {mean.toFixed(2)}
        {returnUnit})
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const headerHeight = 84;
  const chartHeight = height - headerHeight;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        color: t.ink,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          height: headerHeight,
          padding: "14px 44px 4px 104px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          boxSizing: "border-box",
        }}
      >
        <div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: t.ink,
              lineHeight: 1.2,
            }}
          >
            histogram-returns-distribution · javascript · muix · anyplot.ai
          </div>
          <div
            style={{
              fontSize: 14,
              color: t.inkSoft,
              marginTop: 4,
              fontFamily: MONO,
            }}
          >
            {n} periods ({startDate} to {endDate}) · {tailPeriodCount} tail
            periods beyond ±{TAIL_SIGMA_MULT.toFixed(0)}σ (
            {lowerTail.toFixed(2)}
            {returnUnit} / +{upperTail.toFixed(2)}
            {returnUnit})
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 24,
            fontSize: 15,
            color: t.ink,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 16,
                height: 14,
                borderRadius: 3,
                background: CORE_COLOR,
                display: "inline-block",
              }}
            />
            <span>{CORE_SERIES_LABEL}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 16,
                height: 14,
                borderRadius: 3,
                background: TAIL_COLOR,
                display: "inline-block",
              }}
            />
            <span>{TAIL_SERIES_LABEL}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 24,
                height: 3,
                borderRadius: 2,
                background: NORMAL_COLOR,
                display: "inline-block",
              }}
            />
            <span>{NORMAL_SERIES_LABEL}</span>
          </div>
        </div>
      </div>

      <div style={{ position: "relative", width, height: chartHeight }}>
        <ChartsContainer
          width={width}
          height={chartHeight}
          skipAnimation
          margin={{ top: 20, right: 40, bottom: 20, left: 20 }}
          series={[
            {
              type: "bar",
              data: coreDensity,
              stack: "bins",
              color: CORE_COLOR,
              label: CORE_SERIES_LABEL,
              valueFormatter: (v: number | null) =>
                v ? v.toFixed(3) : null,
            },
            {
              type: "bar",
              data: tailDensity,
              stack: "bins",
              color: TAIL_COLOR,
              label: TAIL_SERIES_LABEL,
              valueFormatter: (v: number | null) =>
                v ? v.toFixed(3) : null,
            },
            {
              type: "line",
              data: normalCurve,
              color: NORMAL_COLOR,
              label: NORMAL_SERIES_LABEL,
              showMark: false,
              curve: "natural",
              valueFormatter: (v: number | null) =>
                v !== null ? v.toFixed(3) : "",
            },
          ]}
          xAxis={[
            {
              scaleType: "band",
              data: binCenters,
              height: 60,
              categoryGapRatio: 0.04,
              valueFormatter: (v: number) =>
                Math.abs(v) < 0.05
                  ? `0.0${returnUnit}`
                  : `${v.toFixed(1)}${returnUnit}`,
              label: RETURNS,
              labelStyle: { fill: t.ink, fontSize: 16, fontWeight: 600 },
              tickLabelStyle: {
                fill: t.inkSoft,
                fontSize: 14,
                fontFamily: MONO,
              },
              tickLabelInterval: (_: unknown, i: number) => i % 3 === 0,
            },
          ]}
          yAxis={[
            {
              min: 0,
              max: yMax,
              width: 84,
              label: Y_AXIS_LABEL,
              labelStyle: { fill: t.ink, fontSize: 16, fontWeight: 600 },
              tickLabelStyle: {
                fill: t.inkSoft,
                fontSize: 14,
                fontFamily: MONO,
              },
              valueFormatter: (v: number) => v.toFixed(2),
            },
          ]}
        >
          <ChartsGrid horizontal />
          <BarPlot skipAnimation borderRadius={2} />
          <LinePlot skipAnimation />
          <MeanReferenceLineLayer />
          <ChartsXAxis />
          <ChartsYAxis />
        </ChartsContainer>

        <div
          style={{
            position: "absolute",
            top: 28,
            left: 124,
            background: t.elevatedBg,
            border: `1px solid ${t.grid}`,
            borderRadius: 8,
            padding: "12px 18px",
            fontSize: 15,
            lineHeight: 1.65,
            color: t.ink,
            minWidth: 210,
            fontFamily: MONO,
          }}
        >
          <div
            style={{
              fontWeight: 700,
              marginBottom: 4,
              fontFamily: FONT,
              fontSize: 15,
            }}
          >
            Return statistics
          </div>
          <div style={{ color: t.inkSoft }}>
            Mean: {mean.toFixed(2)}
            {returnUnit}
          </div>
          <div style={{ color: t.inkSoft }}>
            Std dev: {std.toFixed(2)}
            {returnUnit}
          </div>
          <div style={{ color: t.inkSoft }}>
            Skewness: {skewness.toFixed(2)}
          </div>
          <div style={{ color: t.inkSoft }}>
            Excess kurtosis: {excessKurtosis.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}
