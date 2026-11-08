// anyplot.ai
// curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 97/100 | Created: 2026-08-24
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { LinePlot } from "@mui/x-charts/LineChart";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const ERROR_AXIS = "Prediction error"; // the y quantity of every bias-variance decomposition
const HEADROOM_SHARE = 0.08; // space above the highest total error, as a share of it
const LABEL_GAP = 20; // minimum vertical distance between two end-of-curve labels, in px

// Columns: set these to your data's column names
const COMPLEXITY = "Model complexity (low → high)"; // role: model_complexity
const BIAS_SQUARED = "Bias²"; // role: bias_squared
const VARIANCE = "Variance"; // role: variance
const IRREDUCIBLE = "Irreducible error"; // role: irreducible_error
const TOTAL = "Total error"; // role: total_error

// Data: replace this block with your own records, one object per complexity value
// Theoretical decomposition over 80 complexity values: bias² falls as 2.4 / (1 + 0.3c), variance rises
// as 0.005c², the noise floor stays at 0.15, and the total error is their sum
const data = Array.from({ length: 80 }, (_, i) => {
  const c = 1 + (i * 19) / 79;
  const biasSquared = 2.4 / (1 + 0.3 * c);
  const variance = 0.005 * c * c;
  const irreducible = 0.15;
  return {
    [COMPLEXITY]: c,
    [BIAS_SQUARED]: biasSquared,
    [VARIANCE]: variance,
    [IRREDUCIBLE]: irreducible,
    [TOTAL]: biasSquared + variance + irreducible,
  };
});

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[COMPLEXITY] - b[COMPLEXITY]);
const complexity = rows.map((d) => d[COMPLEXITY]);
const optimum = rows.reduce((best, d) => (d[TOTAL] < best[TOTAL] ? d : best), rows[0]);
const yMax = Math.max(...rows.map((d) => d[TOTAL])) * (1 + HEADROOM_SHARE);

// Total error carries the story, so it leads in palette order and line weight; the irreducible noise
// floor is a baseline and takes the neutral ink anchor
const curves = [
  { id: "total", column: TOTAL, color: t.palette[0], width: 4, dash: "none" },
  { id: "bias", column: BIAS_SQUARED, color: t.palette[1], width: 3, dash: "10 6" },
  { id: "variance", column: VARIANCE, color: t.palette[2], width: 3.5, dash: "2 6" },
  { id: "irreducible", column: IRREDUCIBLE, color: t.ink, width: 1.5, dash: "4 4" },
];
const series = curves.map((c) => ({
  type: "line" as const,
  id: c.id,
  label: c.column,
  data: rows.map((d) => d[c.column]),
  color: c.color,
  curve: "monotoneX" as const,
  showMark: false,
}));

const TITLE = "curve-bias-variance-tradeoff · javascript · muix · anyplot.ai";
const formula = `${TOTAL} = ${BIAS_SQUARED} + ${VARIANCE} + ${IRREDUCIBLE}`;
const HEADER_H = 88;

function Zones() {
  const xScale = useXScale();
  const { left, top, width, height } = useDrawingArea();
  const xOpt = xScale(optimum[COMPLEXITY])!;
  return (
    <g>
      <rect x={left} y={top} width={xOpt - left} height={height} fill={t.inkSoft} fillOpacity={0.07} />
      <rect x={xOpt} y={top} width={left + width - xOpt} height={height} fill={t.amber} fillOpacity={0.12} />
      <text x={(left + xOpt) / 2} y={top + 28} fill={t.inkSoft} fontSize={15} fontWeight={600} letterSpacing={1} textAnchor="middle">
        UNDERFITTING
      </text>
      <text x={(xOpt + left + width) / 2} y={top + 28} fill={t.inkSoft} fontSize={15} fontWeight={600} letterSpacing={1} textAnchor="middle">
        OVERFITTING
      </text>
    </g>
  );
}

function CurveLabels() {
  const yScale = useYScale();
  const { left, width } = useDrawingArea();
  const last = rows[rows.length - 1];
  // Labels sit at each curve's right end; only the labels move apart when two ends are close
  const labels = curves.map((c) => ({ ...c, y: yScale(last[c.column])! })).sort((a, b) => a.y - b.y);
  labels.forEach((l, i) => {
    if (i > 0 && l.y - labels[i - 1].y < LABEL_GAP) l.y = labels[i - 1].y + LABEL_GAP;
  });
  return (
    <g>
      {labels.map((l) => (
        <text key={l.id} x={left + width + 12} y={l.y} dominantBaseline="middle" fill={l.color} fontSize={16} fontWeight={500}>
          {l.column}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: HEADER_H, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "6px", pt: "8px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 16, color: t.inkSoft, lineHeight: 1.2 }}>{formula}</Typography>
      </Box>
      <ChartsContainer
        width={width}
        height={height - HEADER_H}
        series={series}
        skipAnimation
        margin={{ top: 16, right: 180, bottom: 16, left: 32 }}
        xAxis={[
          {
            scaleType: "linear",
            data: complexity,
            min: complexity[0],
            max: complexity[complexity.length - 1],
            label: COMPLEXITY,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: yMax,
            label: ERROR_AXIS,
            width: 76,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          ...Object.fromEntries(
            curves.map((c) => [
              `& .MuiLineChart-line[data-series="${c.id}"]`,
              { strokeWidth: c.width, strokeDasharray: c.dash, strokeLinecap: "round" },
            ]),
          ),
        }}
      >
        <Zones />
        <LinePlot />
        <ChartsReferenceLine
          x={optimum[COMPLEXITY]}
          label={`Optimum at ${optimum[COMPLEXITY].toFixed(1)} (minimum ${TOTAL.toLowerCase()} ${optimum[TOTAL].toFixed(2)})`}
          labelAlign="end"
          lineStyle={{ stroke: t.ink, strokeDasharray: "6 4", strokeWidth: 1.5 }}
          labelStyle={{ fill: t.ink, fontSize: 14, fontWeight: 600 }}
        />
        <CurveLabels />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </Box>
  );
}
