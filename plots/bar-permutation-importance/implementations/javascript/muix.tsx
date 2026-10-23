// anyplot.ai
// bar-permutation-importance: Permutation Feature Importance Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-08-26
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const ZERO_REF = 0;
const X_PAD_SHARE = 0.08;
const SEQ_MIN_MIX = 0.22;

// Columns: set these to your data's column names
const FEATURE = "Model feature"; // role: feature
const IMPORTANCE_MEAN = "Mean decrease in accuracy"; // role: importance_mean
const IMPORTANCE_STD = "Shuffle SD"; // role: importance_std

// Data: replace this block with your own records, one object per row
const data = [
  { [FEATURE]: "Contract Type", [IMPORTANCE_MEAN]: 0.182, [IMPORTANCE_STD]: 0.021 },
  { [FEATURE]: "Tenure (Months)", [IMPORTANCE_MEAN]: 0.146, [IMPORTANCE_STD]: 0.018 },
  { [FEATURE]: "Monthly Charges", [IMPORTANCE_MEAN]: 0.098, [IMPORTANCE_STD]: 0.015 },
  { [FEATURE]: "Total Charges", [IMPORTANCE_MEAN]: 0.071, [IMPORTANCE_STD]: 0.014 },
  { [FEATURE]: "Tech Support", [IMPORTANCE_MEAN]: 0.058, [IMPORTANCE_STD]: 0.012 },
  { [FEATURE]: "Online Security", [IMPORTANCE_MEAN]: 0.049, [IMPORTANCE_STD]: 0.011 },
  { [FEATURE]: "Support Calls", [IMPORTANCE_MEAN]: 0.041, [IMPORTANCE_STD]: 0.010 },
  { [FEATURE]: "Internet Service", [IMPORTANCE_MEAN]: 0.033, [IMPORTANCE_STD]: 0.009 },
  { [FEATURE]: "Payment Method", [IMPORTANCE_MEAN]: 0.026, [IMPORTANCE_STD]: 0.008 },
  { [FEATURE]: "Paperless Billing", [IMPORTANCE_MEAN]: 0.019, [IMPORTANCE_STD]: 0.007 },
  { [FEATURE]: "Dependents", [IMPORTANCE_MEAN]: 0.014, [IMPORTANCE_STD]: 0.006 },
  { [FEATURE]: "Streaming TV", [IMPORTANCE_MEAN]: 0.009, [IMPORTANCE_STD]: 0.006 },
  { [FEATURE]: "Partner", [IMPORTANCE_MEAN]: 0.006, [IMPORTANCE_STD]: 0.005 },
  { [FEATURE]: "Multiple Lines", [IMPORTANCE_MEAN]: 0.003, [IMPORTANCE_STD]: 0.005 },
  { [FEATURE]: "Senior Citizen", [IMPORTANCE_MEAN]: -0.004, [IMPORTANCE_STD]: 0.004 },
];

// Plot: reads only data and the constants above
const sorted = [...data].sort((a, b) => b[IMPORTANCE_MEAN] - a[IMPORTANCE_MEAN]);
const features = sorted.map((d) => d[FEATURE]);
const means = sorted.map((d) => d[IMPORTANCE_MEAN]);
const stds = sorted.map((d) => d[IMPORTANCE_STD]);

const minMean = Math.min(...means);
const maxMean = Math.max(...means);
const meanSpan = maxMean - minMean || 1;

const seqLowInt = parseInt(t.seq[0].slice(1), 16);
const seqHighInt = parseInt(t.seq[1].slice(1), 16);
const seqLowRgb = [(seqLowInt >> 16) & 255, (seqLowInt >> 8) & 255, seqLowInt & 255];
const seqHighRgb = [(seqHighInt >> 16) & 255, (seqHighInt >> 8) & 255, seqHighInt & 255];

const barColors = means.map((v) => {
  const norm = (v - minMean) / meanSpan;
  const ratio = SEQ_MIN_MIX + (1 - SEQ_MIN_MIX) * norm;
  const r = Math.round(seqLowRgb[0] + (seqHighRgb[0] - seqLowRgb[0]) * ratio);
  const g = Math.round(seqLowRgb[1] + (seqHighRgb[1] - seqLowRgb[1]) * ratio);
  const b = Math.round(seqLowRgb[2] + (seqHighRgb[2] - seqLowRgb[2]) * ratio);
  return `rgb(${r}, ${g}, ${b})`;
});

const rawMin = Math.min(
  ZERO_REF,
  ...sorted.map((d) => d[IMPORTANCE_MEAN] - d[IMPORTANCE_STD]),
);
const rawMax = Math.max(
  ZERO_REF,
  ...sorted.map((d) => d[IMPORTANCE_MEAN] + d[IMPORTANCE_STD]),
);
const xSpan = rawMax - rawMin || 1;
const xMin = rawMin - xSpan * X_PAD_SHARE;
const xMax = rawMax + xSpan * X_PAD_SHARE;

const TITLE = "Churn Prediction Model · bar-permutation-importance · javascript · muix · anyplot.ai";
const SUBTITLE = `${FEATURE}: ${features.length} · Whiskers: ±1 ${IMPORTANCE_STD} · Top: ${features[0]}, ${means[0].toFixed(3)} ± ${stds[0].toFixed(3)}`;

function ErrorBars() {
  const xScale = useXScale("x");
  const yScale = useYScale("y");
  const bw = yScale.bandwidth();
  const cap = bw * 0.34;

  return (
    <g>
      {features.map((feature, i) => {
        const cy = yScale(feature) + bw / 2;
        const xLo = xScale(means[i] - stds[i]);
        const xHi = xScale(means[i] + stds[i]);
        return (
          <g
            key={feature}
            stroke={t.ink}
            strokeWidth={2.5}
            strokeOpacity={0.85}
            strokeLinecap="round"
          >
            <line x1={xLo} y1={cy} x2={xHi} y2={cy} />
            <line x1={xLo} y1={cy - cap} x2={xLo} y2={cy + cap} />
            <line x1={xHi} y1={cy - cap} x2={xHi} y2={cy + cap} />
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const CHART_TOP = 84;

  return (
    <Box sx={{ position: "relative", width: W, height: H, bgcolor: t.pageBg }}>
      <Box sx={{ position: "absolute", top: 20, left: 56, right: 56 }}>
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600, lineHeight: 1.25 }}>
          {TITLE}
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 15, mt: 0.5 }}>
          {SUBTITLE}
        </Typography>
      </Box>

      <Box sx={{ position: "absolute", top: CHART_TOP, left: 0, right: 0, bottom: 0 }}>
        <ChartsContainer
          width={W}
          height={H - CHART_TOP}
          series={[
            {
              type: "bar",
              id: "importance",
              data: means,
              layout: "horizontal",
              xAxisId: "x",
              yAxisId: "y",
              label: IMPORTANCE_MEAN,
              valueFormatter: (v: number, { dataIndex }: { dataIndex: number }) =>
                `${v.toFixed(3)} ± ${stds[dataIndex].toFixed(3)}`,
            },
          ]}
          xAxis={[
            {
              id: "x",
              scaleType: "linear",
              min: xMin,
              max: xMax,
              tickNumber: 8,
              height: 64,
              label: IMPORTANCE_MEAN,
              labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            },
          ]}
          yAxis={[
            {
              id: "y",
              scaleType: "band",
              data: features,
              width: 175,
              colorMap: { type: "ordinal", values: features, colors: barColors },
              categoryGapRatio: 0.3,
              label: FEATURE,
              labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              disableTicks: true,
            },
          ]}
          margin={{ top: 14, right: 48, bottom: 20, left: 36 }}
          skipAnimation
          sx={{
            "& .MuiChartsAxis-line": { stroke: t.inkSoft },
            "& .MuiChartsGrid-line": { stroke: t.grid },
            "& .MuiBarChart-element": { stroke: t.inkSoft, strokeOpacity: 0.25, strokeWidth: 1 },
          }}
        >
          <ChartsGrid vertical />
          <BarPlot skipAnimation borderRadius={3} />
          <ErrorBars />
          <ChartsReferenceLine
            x={ZERO_REF}
            axisId="x"
            lineStyle={{ stroke: t.ink, strokeWidth: 2, strokeOpacity: 0.6 }}
          />
          <ChartsXAxis axisId="x" />
          <ChartsYAxis axisId="y" />
        </ChartsContainer>
      </Box>
    </Box>
  );
}
