// anyplot.ai
// forest-basic: Meta-Analysis Forest Plot
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-05
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
const STUDY_COL = "study";
const EFFECT_COL = "effect_size";
const CI_LOWER = "ci_lower";
const CI_UPPER = "ci_upper";
const WEIGHT_COL = "weight";

const TITLE = "Systolic BP Reduction · forest-basic · javascript · muix · anyplot.ai";
const SUBTITLE_PREFIX = "Mean difference vs. placebo (mmHg) · squares sized by study weight · diamond = pooled effect";
const X_AXIS_LABEL = "Mean Difference in Systolic Blood Pressure (mmHg)";
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

// Data — randomized controlled trials comparing antihypertensive therapy vs. placebo (mmHg SBP change)
const data: Record<string, string | number>[] = [
  { [STUDY_COL]: "Anderson et al. 2019", [EFFECT_COL]: -4.2, [CI_LOWER]: -7.1, [CI_UPPER]: -1.3, [WEIGHT_COL]: 11.9 },
  { [STUDY_COL]: "Chen et al. 2020", [EFFECT_COL]: -6.8, [CI_LOWER]: -9.5, [CI_UPPER]: -4.1, [WEIGHT_COL]: 15.1 },
  { [STUDY_COL]: "Dubois et al. 2020", [EFFECT_COL]: -3.1, [CI_LOWER]: -6.9, [CI_UPPER]: 0.7, [WEIGHT_COL]: 8.8 },
  { [STUDY_COL]: "Fernandez et al. 2021", [EFFECT_COL]: -8.5, [CI_LOWER]: -11.2, [CI_UPPER]: -5.8, [WEIGHT_COL]: 16.0 },
  { [STUDY_COL]: "Garcia et al. 2021", [EFFECT_COL]: -5.0, [CI_LOWER]: -8.8, [CI_UPPER]: -1.2, [WEIGHT_COL]: 10.5 },
  { [STUDY_COL]: "Halvorsen et al. 2022", [EFFECT_COL]: -7.3, [CI_LOWER]: -10.0, [CI_UPPER]: -4.6, [WEIGHT_COL]: 15.7 },
  { [STUDY_COL]: "Ivanova et al. 2022", [EFFECT_COL]: -2.0, [CI_LOWER]: -5.5, [CI_UPPER]: 1.5, [WEIGHT_COL]: 7.9 },
  { [STUDY_COL]: "Kowalski et al. 2023", [EFFECT_COL]: -6.1, [CI_LOWER]: -8.7, [CI_UPPER]: -3.5, [WEIGHT_COL]: 14.1 },
];

// DerSimonian-Laird random-effects pooled estimate computed from the study rows
const nStudies = data.length;
const studyRecords = data.map((r, i) => {
  const name = String(r[STUDY_COL]);
  const effect = Number(r[EFFECT_COL]);
  const lower = Number(r[CI_LOWER]);
  const upper = Number(r[CI_UPPER]);
  const weight = Number(r[WEIGHT_COL]);
  const se = (upper - lower) / (2 * Z_95);
  const invVar = 1 / (se * se || 1);
  return { name, effect, lower, upper, weight, se, invVar, y: nStudies - i };
});

const sumInvVar = studyRecords.reduce((s, r) => s + r.invVar, 0);
const fixedMean = studyRecords.reduce((s, r) => s + r.invVar * r.effect, 0) / (sumInvVar || 1);
const qStat = studyRecords.reduce((s, r) => s + r.invVar * Math.pow(r.effect - fixedMean, 2), 0);
const df = Math.max(1, nStudies - 1);
const cDenom = sumInvVar - studyRecords.reduce((s, r) => s + r.invVar * r.invVar, 0) / (sumInvVar || 1);
const tauSq = Math.max(0, (qStat - df) / (cDenom || 1));

const reWeights = studyRecords.map((r) => 1 / (r.se * r.se + tauSq));
const sumReWeights = reWeights.reduce((s, w) => s + w, 0);
const pooledEffect = studyRecords.reduce((s, r, idx) => s + reWeights[idx] * r.effect, 0) / (sumReWeights || 1);
const pooledSe = Math.sqrt(1 / (sumReWeights || 1));
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
    ((s.weight - minWeight) / (maxWeight - minWeight || 1)) * (MAX_MARKER_HALF - MIN_MARKER_HALF),
}));

const overallY = 1 - POOLED_ROW_GAP;
const yTicks = [...rows.map((r) => r.y), overallY];
const yLabels = new Map<number, string>(
  yTicks.map((y) => [y, y === overallY ? POOLED_LABEL : rows.find((r) => r.y === y)!.name]),
);

const rawXMin = Math.min(...rows.map((s) => s.lower), pooledLower, NULL_EFFECT);
const rawXMax = Math.max(...rows.map((s) => s.upper), pooledUpper, NULL_EFFECT);
const rawXSpan = rawXMax - rawXMin || 1;
const xMin = Number((rawXMin - rawXSpan * X_PAD_SHARE).toFixed(1));
const xMax = Number((rawXMax + rawXSpan * X_PAD_SHARE).toFixed(1));

function ForestMarks() {
  const xScale = useXScale();
  const yScale = useYScale();
  const drawingArea = useDrawingArea();

  const dividerY = yScale((rows[rows.length - 1].y + overallY) / 2) ?? 0;
  const textX = drawingArea.left + drawingArea.width + 18;
  const capHalf = 6;

  const cyOverall = yScale(overallY) ?? 0;
  const xL = xScale(pooledLower) ?? 0;
  const xC = xScale(pooledEffect) ?? 0;
  const xU = xScale(pooledUpper) ?? 0;
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
        const cx = xScale(r.effect) ?? 0;
        const cy = yScale(r.y) ?? 0;
        const x1 = xScale(r.lower) ?? 0;
        const x2 = xScale(r.upper) ?? 0;
        const half = r.halfSize;
        return (
          <g key={r.name}>
            <line x1={x1} x2={x2} y1={cy} y2={cy} stroke={t.palette[0]} strokeWidth={2.2} />
            <line x1={x1} x2={x1} y1={cy - capHalf} y2={cy + capHalf} stroke={t.palette[0]} strokeWidth={2.2} />
            <line x1={x2} x2={x2} y1={cy - capHalf} y2={cy + capHalf} stroke={t.palette[0]} strokeWidth={2.2} />
            <rect x={cx - half} y={cy - half} width={half * 2} height={half * 2} fill={t.palette[0]} />
            <text x={textX} y={cy + 5} fontSize={14} fill={t.inkSoft} fontFamily="sans-serif">
              {`${r.effect.toFixed(1)} [${r.lower.toFixed(1)}, ${r.upper.toFixed(1)}]  ·  ${r.weight.toFixed(1)}%`}
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
  const subtitle = `${SUBTITLE_PREFIX} (k = ${nStudies}, I² = ${iSquared.toFixed(0)}%)`;

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
            label: X_AXIS_LABEL,
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
