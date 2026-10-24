// anyplot.ai
// histogram-capability: Process Capability Plot with Specification Limits
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: pending | Created: 2026-06-20
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useDrawingArea } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = "system-ui, -apple-system, sans-serif";
const TITLE = "histogram-capability · javascript · muix · anyplot.ai";

const N_BINS = 15;
const CURVE_STEPS = 120;
const X_PAD_RATIO = 0.25;
const Y_PAD_RATIO = 0.14;
const CAPABLE_MIN = 1.33;
const MARGINAL_MIN = 1.0;

const BRAND = t.palette[0];
const TARGET_COLOR = t.palette[1];
const BLUE = t.palette[2];
const RED = t.palette[4];

// Columns: set these to your data's column names
const DIAMETER = "Shaft diameter (mm)"; // role: measurement
const LSL = "LSL"; // role: lsl
const USL = "USL"; // role: usl
const TARGET = "Target"; // role: target

// Data: replace this block with your own records
type CapabilityRow = {
  [DIAMETER]: number;
  [LSL]: number;
  [USL]: number;
  [TARGET]: number;
};

const data: CapabilityRow[] = [];
let seed = 42 >>> 0;
const sampleSize = 200;

for (let i = 0; i < sampleSize; i++) {
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const u1 = Math.max(seed / 0x100000000, 1e-10);
  seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
  const u2 = seed / 0x100000000;
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  data.push({
    [DIAMETER]: Number((10.005 + z * 0.015).toFixed(5)),
    [LSL]: 9.95,
    [USL]: 10.05,
    [TARGET]: 10.0,
  });
}

// Plot: reads only data and the constants above
const n = data.length;
const lsl = data[0][LSL];
const usl = data[0][USL];
const target = data[0][TARGET];
const measurements = data.map((r) => r[DIAMETER]);

const sampleMean = measurements.reduce((s, v) => s + v, 0) / n;
const sampleSigma = Math.sqrt(
  measurements.reduce((s, v) => s + (v - sampleMean) ** 2, 0) / (n - 1),
);

const Cp = (usl - lsl) / (6 * sampleSigma);
const Cpk = Math.min(
  (usl - sampleMean) / (3 * sampleSigma),
  (sampleMean - lsl) / (3 * sampleSigma),
);

const dataMin = Math.min(...measurements);
const dataMax = Math.max(...measurements);
const binWidth = (dataMax - dataMin) / N_BINS;

const histCounts = new Array(N_BINS).fill(0);
for (const v of measurements) {
  const idx = Math.min(N_BINS - 1, Math.floor((v - dataMin) / binWidth));
  histCounts[idx]++;
}

const specSpan = usl - lsl;
const xMin = Math.min(dataMin, lsl - specSpan * X_PAD_RATIO);
const xMax = Math.max(dataMax, usl + specSpan * X_PAD_RATIO);

const curveX = Array.from(
  { length: CURVE_STEPS },
  (_, i) => xMin + (i / (CURVE_STEPS - 1)) * (xMax - xMin),
);
const normalValues = curveX.map((x) => {
  const z = (x - sampleMean) / sampleSigma;
  return (
    (Math.exp(-0.5 * z * z) / (sampleSigma * Math.sqrt(2 * Math.PI))) *
    n *
    binWidth
  );
});

const yMax = Math.max(...histCounts, ...normalValues) * (1 + Y_PAD_RATIO);

const capStatus =
  Cpk >= CAPABLE_MIN
    ? "Status: Capable"
    : Cpk >= MARGINAL_MIN
      ? "Status: Marginal"
      : "Status: Not Capable";

const unitMatch = DIAMETER.match(/\(([^)]+)\)/);
const unit = unitMatch ? ` ${unitMatch[1]}` : "";
const SUBTITLE = `${DIAMETER} (n = ${n}) · μ = ${sampleMean.toFixed(4)}${unit}, σ = ${sampleSigma.toFixed(4)}${unit} · ${LSL} = ${lsl.toFixed(2)}, ${TARGET} = ${target.toFixed(2)}, ${USL} = ${usl.toFixed(2)}${unit}`;

function CapabilityLayer() {
  const { left, top, width, height } = useDrawingArea();
  const binPx = (binWidth / (xMax - xMin)) * width;
  const px = left + width + 22;
  const py = top + 16;
  const lh = 28;

  return (
    <g fontFamily={FONT}>
      {histCounts.map((c, i) => {
        const bx = left + ((dataMin + i * binWidth - xMin) / (xMax - xMin)) * width;
        const by = top + (1 - c / yMax) * height;
        const bh = top + height - by;
        return (
          <rect
            key={i}
            x={bx + 0.5}
            y={by}
            width={binPx - 1}
            height={bh}
            fill={BRAND}
            fillOpacity={0.82}
          />
        );
      })}

      <rect
        x={px - 14}
        y={py - 16}
        width={216}
        height={264}
        fill={t.elevatedBg}
        stroke={t.grid}
        strokeWidth={1}
        rx={6}
      />
      <text
        x={px}
        y={py + 6}
        fontSize={14}
        fontWeight="700"
        fill={t.inkSoft}
        letterSpacing={1.2}
      >
        CAPABILITY
      </text>
      <text
        x={px}
        y={py + lh + 8}
        fontSize={16}
        fill={t.ink}
        fontFamily="monospace"
        fontWeight="600"
      >
        {`Cp  = ${Cp.toFixed(3)}`}
      </text>
      <text
        x={px}
        y={py + 2 * lh + 8}
        fontSize={16}
        fill={t.ink}
        fontFamily="monospace"
        fontWeight="600"
      >
        {`Cpk = ${Cpk.toFixed(3)}`}
      </text>
      <line
        x1={px}
        y1={py + 2 * lh + 22}
        x2={px + 188}
        y2={py + 2 * lh + 22}
        stroke={t.inkSoft}
        strokeWidth={1}
        strokeOpacity={0.35}
      />
      <text
        x={px}
        y={py + 3 * lh + 22}
        fontSize={14}
        fontWeight="700"
        fill={t.ink}
      >
        {capStatus}
      </text>

      <rect
        x={px}
        y={py + 4 * lh + 26}
        width={22}
        height={14}
        fill={BRAND}
        fillOpacity={0.82}
        rx={2}
      />
      <text x={px + 30} y={py + 4 * lh + 38} fontSize={14} fill={t.ink}>
        Observations
      </text>

      <line
        x1={px}
        y1={py + 5 * lh + 32}
        x2={px + 22}
        y2={py + 5 * lh + 32}
        stroke={BLUE}
        strokeWidth={3}
      />
      <text x={px + 30} y={py + 5 * lh + 37} fontSize={14} fill={t.ink}>
        Normal fit
      </text>

      <line
        x1={px}
        y1={py + 6 * lh + 32}
        x2={px + 22}
        y2={py + 6 * lh + 32}
        stroke={RED}
        strokeWidth={2.5}
        strokeDasharray="6 3"
      />
      <text x={px + 30} y={py + 6 * lh + 37} fontSize={14} fill={t.ink}>
        {`${LSL} / ${USL}`}
      </text>

      <line
        x1={px}
        y1={py + 7 * lh + 32}
        x2={px + 22}
        y2={py + 7 * lh + 32}
        stroke={TARGET_COLOR}
        strokeWidth={2.5}
        strokeDasharray="8 4"
      />
      <text x={px + 30} y={py + 7 * lh + 37} fontSize={14} fill={t.ink}>
        {TARGET}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const TITLE_H = 78;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <Typography
        sx={{
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
          pt: "16px",
          px: "40px",
          pb: 0,
          lineHeight: 1.2,
          fontFamily: FONT,
        }}
      >
        {TITLE}
      </Typography>
      <Typography
        sx={{
          fontSize: 15,
          fontWeight: 400,
          color: t.inkSoft,
          px: "40px",
          pt: "4px",
          pb: 0,
          lineHeight: 1.2,
          fontFamily: FONT,
        }}
      >
        {SUBTITLE}
      </Typography>

      <ChartsContainer
        width={width}
        height={height - TITLE_H}
        series={[
          {
            type: "line",
            id: "normal",
            data: normalValues,
            label: "Normal fit",
            color: BLUE,
            showMark: false,
            curve: "catmullRom",
          },
        ]}
        xAxis={[
          {
            id: "diameter-axis",
            data: curveX,
            scaleType: "linear",
            min: xMin,
            max: xMax,
            height: 60,
            label: DIAMETER,
            valueFormatter: (v: number) => v.toFixed(3),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
          },
        ]}
        yAxis={[
          {
            id: "count-axis",
            min: 0,
            max: yMax,
            width: 76,
            label: "Count",
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
          },
        ]}
        margin={{ top: 24, right: 244, bottom: 20, left: 20 }}
        skipAnimation
      >
        <ChartsGrid
          horizontal
          sx={{ "& line": { stroke: t.grid, strokeWidth: 0.8 } }}
        />
        <CapabilityLayer />
        <LinePlot skipAnimation />
        <ChartsReferenceLine
          x={lsl}
          label={LSL}
          labelAlign="start"
          lineStyle={{ stroke: RED, strokeDasharray: "6 3", strokeWidth: 2.5 }}
          labelStyle={{
            fill: RED,
            fontSize: 14,
            fontWeight: "bold",
            fontFamily: FONT,
          }}
        />
        <ChartsReferenceLine
          x={usl}
          label={USL}
          labelAlign="start"
          lineStyle={{ stroke: RED, strokeDasharray: "6 3", strokeWidth: 2.5 }}
          labelStyle={{
            fill: RED,
            fontSize: 14,
            fontWeight: "bold",
            fontFamily: FONT,
          }}
        />
        <ChartsReferenceLine
          x={target}
          label={TARGET}
          labelAlign="start"
          lineStyle={{ stroke: TARGET_COLOR, strokeDasharray: "8 4", strokeWidth: 2.5 }}
          labelStyle={{
            fill: TARGET_COLOR,
            fontSize: 14,
            fontWeight: "bold",
            fontFamily: FONT,
          }}
        />
        <ChartsXAxis axisId="diameter-axis" />
        <ChartsYAxis axisId="count-axis" />
      </ChartsContainer>
    </Box>
  );
}
