// anyplot.ai
// forest-basic: Meta-Analysis Forest Plot
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 85/100 | Updated: 2026-10-24
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "Systolic BP Reduction · forest-basic · javascript · muix · anyplot.ai";
const POOLED_LABEL = "Pooled Effect (Random Effects)";
const NULL_LABEL = "No difference";
const NULL_EFFECT = 0;
const Z_95 = 1.95996;

const X_PAD_SHARE = 0.12;
const Y_PAD_TOP = 0.75;
const Y_PAD_BOTTOM = 0.95;
const POOLED_ROW_GAP = 1.6;
const MIN_MARKER_HALF = 5;
const MAX_MARKER_HALF = 11;

const TITLE_HEIGHT = 56;
const SUBTITLE_HEIGHT = 36;
const MARGIN = { top: 20, right: 256, bottom: 20, left: 16 };
const X_AXIS_HEIGHT = 56;
const Y_AXIS_WIDTH = 228;

// Columns: set these to your data's column names
const STUDY = "Study"; // role: study
const EFFECT = "Mean difference in SBP (mmHg)"; // role: effect_size
const CI_LOWER = "95% CI lower"; // role: ci_lower
const CI_UPPER = "95% CI upper"; // role: ci_upper
const WEIGHT = "Study weight"; // role: weight

// Data: replace this block with your own records
const data: Record<string, string | number>[] = [
  { [STUDY]: "Anderson et al. 2019", [EFFECT]: -4.2, [CI_LOWER]: -7.1, [CI_UPPER]: -1.3, [WEIGHT]: 11.9 },
  { [STUDY]: "Chen et al. 2020", [EFFECT]: -6.8, [CI_LOWER]: -9.5, [CI_UPPER]: -4.1, [WEIGHT]: 15.1 },
  { [STUDY]: "Dubois et al. 2020", [EFFECT]: -3.1, [CI_LOWER]: -6.9, [CI_UPPER]: 0.7, [WEIGHT]: 8.8 },
  { [STUDY]: "Fernandez et al. 2021", [EFFECT]: -8.5, [CI_LOWER]: -11.2, [CI_UPPER]: -5.8, [WEIGHT]: 16.0 },
  { [STUDY]: "Garcia et al. 2021", [EFFECT]: -5.0, [CI_LOWER]: -8.8, [CI_UPPER]: -1.2, [WEIGHT]: 10.5 },
  { [STUDY]: "Halvorsen et al. 2022", [EFFECT]: -7.3, [CI_LOWER]: -10.0, [CI_UPPER]: -4.6, [WEIGHT]: 15.7 },
  { [STUDY]: "Ivanova et al. 2022", [EFFECT]: -2.0, [CI_LOWER]: -5.5, [CI_UPPER]: 1.5, [WEIGHT]: 7.9 },
  { [STUDY]: "Kowalski et al. 2023", [EFFECT]: -6.1, [CI_LOWER]: -8.7, [CI_UPPER]: -3.5, [WEIGHT]: 14.1 },
];

// Plot: reads only data and the constants above
const nStudies = data.length;
const studyRecords = data.map((r, i) => {
  const name = String(r[STUDY]);
  const effect = Number(r[EFFECT]);
  const lower = Number(r[CI_LOWER]);
  const upper = Number(r[CI_UPPER]);
  const weight = Number(r[WEIGHT]);
  const se = (upper - lower) / (2 * Z_95);
  const invVar = 1 / (se * se);
  return { name, effect, lower, upper, weight, se, invVar, y: nStudies - i };
});

const sumInvVar = studyRecords.reduce((s, r) => s + r.invVar, 0);
const fixedMean = studyRecords.reduce((s, r) => s + r.invVar * r.effect, 0) / sumInvVar;
const qStat = studyRecords.reduce((s, r) => s + r.invVar * Math.pow(r.effect - fixedMean, 2), 0);
const df = nStudies - 1;
const cDenom = sumInvVar - studyRecords.reduce((s, r) => s + r.invVar * r.invVar, 0) / sumInvVar;
const tauSq = Math.max(0, (qStat - df) / cDenom);

const reWeights = studyRecords.map((r) => 1 / (r.se * r.se + tauSq));
const sumReWeights = reWeights.reduce((s, w) => s + w, 0);
const pooledEffect = studyRecords.reduce((s, r, idx) => s + reWeights[idx] * r.effect, 0) / sumReWeights;
const pooledSe = Math.sqrt(1 / sumReWeights);
const pooledLower = pooledEffect - Z_95 * pooledSe;
const pooledUpper = pooledEffect + Z_95 * pooledSe;
const iSquared = qStat > df ? ((qStat - df) / qStat) * 100 : 0;

const weights = studyRecords.map((s) => s.weight);
const minWeight = Math.min(...weights);
const maxWeight = Math.max(...weights);

const rows = studyRecords.map((s) => ({
  ...s,
  halfSize:
    MIN_MARKER_HALF +
    ((s.weight - minWeight) / (maxWeight - minWeight)) * (MAX_MARKER_HALF - MIN_MARKER_HALF),
}));

const overallY = 1 - POOLED_ROW_GAP;
const yTicks = [...rows.map((r) => r.y), overallY];
const yLabels = new Map<number, string>(
  yTicks.map((y) => [y, y === overallY ? POOLED_LABEL : rows.find((r) => r.y === y)!.name]),
);

const rawXMin = Math.min(...rows.map((s) => s.lower), pooledLower, NULL_EFFECT);
const rawXMax = Math.max(...rows.map((s) => s.upper), pooledUpper, NULL_EFFECT);
const rawXSpan = rawXMax - rawXMin;
const xMin = rawXMin - rawXSpan * X_PAD_SHARE;
const xMax = rawXMax + rawXSpan * X_PAD_SHARE;

function ForestMarks() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const drawingArea = useDrawingArea();

  const dividerY = yScale((rows[rows.length - 1].y + overallY) / 2);
  const textX = drawingArea.left + drawingArea.width + 18;
  const capHalf = 6;

  const cyOverall = yScale(overallY);
  const xL = xScale(pooledLower);
  const xC = xScale(pooledEffect);
  const xU = xScale(pooledUpper);
  const halfH = 13;

  return (
    <g>
      <line
        x1={drawingArea.left}
        x2={drawingArea.left + drawingArea.width}
        y1={dividerY}
        y2={dividerY}
        stroke={t.grid}
        strokeWidth={1}
      />

      {rows.map((r) => {
        const cx = xScale(r.effect);
        const cy = yScale(r.y);
        const x1 = xScale(r.lower);
        const x2 = xScale(r.upper);
        const half = r.halfSize;
        return (
          <g key={r.name}>
            <line x1={x1} x2={x2} y1={cy} y2={cy} stroke={t.palette[0]} strokeWidth={2.2} />
            <line x1={x1} x2={x1} y1={cy - capHalf} y2={cy + capHalf} stroke={t.palette[0]} strokeWidth={2.2} />
            <line x1={x2} x2={x2} y1={cy - capHalf} y2={cy + capHalf} stroke={t.palette[0]} strokeWidth={2.2} />
            <rect x={cx - half} y={cy - half} width={half * 2} height={half * 2} fill={t.palette[0]} />
            <text x={textX} y={cy + 5} fontSize={14} fill={t.inkSoft} fontFamily="sans-serif">
              {`${r.effect.toFixed(1)} [${r.lower.toFixed(1)}, ${r.upper.toFixed(1)}]  ·  w = ${r.weight.toFixed(1)}`}
            </text>
          </g>
        );
      })}

      <g>
        <polygon
          points={`${xL},${cyOverall} ${xC},${cyOverall - halfH} ${xU},${cyOverall} ${xC},${cyOverall + halfH}`}
          fill={t.ink}
          stroke={t.pageBg}
          strokeWidth={1}
        />
        <text x={textX} y={cyOverall + 5} fontSize={14} fontWeight={700} fill={t.ink} fontFamily="sans-serif">
          {`${pooledEffect.toFixed(1)} [${pooledLower.toFixed(1)}, ${pooledUpper.toFixed(1)}]`}
        </text>
      </g>
    </g>
  );
}

export default function Chart() {
  const chartWidth = window.ANYPLOT_SIZE.width;
  const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT - SUBTITLE_HEIGHT;
  const subtitle = `${EFFECT} · squares sized by ${WEIGHT} · diamond = pooled effect (k = ${nStudies}, I² = ${iSquared.toFixed(0)}%)`;

  return (
    <Box
      sx={{
        width: chartWidth,
        height: window.ANYPLOT_SIZE.height,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600 }}>{TITLE}</Typography>
      </Box>
      <Box
        sx={{
          height: SUBTITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <Typography sx={{ color: t.inkSoft, fontSize: 15 }}>{subtitle}</Typography>
      </Box>

      <ChartsContainer
        skipAnimation
        width={chartWidth}
        height={chartHeight}
        margin={MARGIN}
        series={[]}
        xAxis={[
          {
            scaleType: "linear",
            min: xMin,
            max: xMax,
            height: X_AXIS_HEIGHT,
            label: EFFECT,
            labelStyle: { fontSize: 15, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: overallY - Y_PAD_BOTTOM,
            max: nStudies + Y_PAD_TOP,
            width: Y_AXIS_WIDTH,
            tickInterval: yTicks,
            valueFormatter: (v: number) => yLabels.get(v) ?? "",
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            tickSize: 4,
            disableLine: true,
          },
        ]}
        sx={{ "& .MuiChartsGrid-line": { stroke: t.grid, strokeOpacity: 0.5 } }}
      >
        <ChartsGrid vertical />
        <ChartsReferenceLine
          x={NULL_EFFECT}
          label={NULL_LABEL}
          labelAlign="end"
          labelStyle={{ fontSize: 14, fill: t.inkSoft }}
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 4", strokeWidth: 1.5 }}
        />
        <ForestMarks />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </Box>
  );
}
