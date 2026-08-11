// anyplot.ai
// bland-altman-basic: Bland-Altman Agreement Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-11
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
// Systolic blood pressure (mmHg) for 70 patients, each measured once with a
// new oscillometric cuff and once with the mercury-column reference standard.
let seed = 42;
function nextRandom() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function gaussian() {
  const u1 = Math.max(nextRandom(), 1e-9);
  const u2 = nextRandom();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const PATIENT_COUNT = 70;
const reference = Array.from({ length: PATIENT_COUNT }, () => 122 + gaussian() * 15);
// The cuff reads slightly high on average, and its scatter widens a little
// for higher pressures — a realistic proportional-error pattern.
const cuff = reference.map((value) => value + 3.4 + gaussian() * (4 + value * 0.02));

const meanValues = reference.map((value, i) => (value + cuff[i]) / 2);
const diffValues = reference.map((value, i) => cuff[i] - value);

const bias = diffValues.reduce((sum, d) => sum + d, 0) / PATIENT_COUNT;
const variance =
  diffValues.reduce((sum, d) => sum + (d - bias) ** 2, 0) / (PATIENT_COUNT - 1);
const stdDev = Math.sqrt(variance);
const upperLimit = bias + 1.96 * stdDev;
const lowerLimit = bias - 1.96 * stdDev;

const points = meanValues.map((mean, i) => ({ x: mean, y: diffValues[i], id: i }));

const TITLE_HEIGHT = 60;

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box
      sx={{
        width,
        height,
        display: "flex",
        flexDirection: "column",
        paddingTop: "20px",
      }}
    >
      <Typography
        sx={{
          color: t.ink,
          fontSize: 22,
          fontWeight: 500,
          textAlign: "center",
          lineHeight: 1.2,
        }}
      >
        bland-altman-basic · javascript · muix · anyplot.ai
      </Typography>
      <ScatterChart
        width={width}
        height={height - TITLE_HEIGHT}
        skipAnimation
        series={[
          {
            data: points,
            label: "Patient reading",
            markerSize: 7,
            color: "rgba(0, 158, 115, 0.6)",
          },
        ]}
        xAxis={[
          {
            label: "Mean of Cuff & Reference (mmHg)",
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            label: "Difference: Cuff − Reference (mmHg)",
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        margin={{ left: 100, right: 140, top: 20, bottom: 90 }}
        grid={{ horizontal: true, vertical: true }}
        slotProps={{ legend: { hidden: true } }}
      >
        <ChartsReferenceLine
          y={bias}
          label={`Bias: ${bias.toFixed(1)} mmHg`}
          labelAlign="end"
          lineStyle={{ stroke: t.ink, strokeWidth: 2.5 }}
          labelStyle={{ fill: t.ink, fontSize: 14, fontWeight: 600 }}
        />
        <ChartsReferenceLine
          y={upperLimit}
          label={`+1.96 SD: ${upperLimit.toFixed(1)}`}
          labelAlign="end"
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "8 6", strokeWidth: 1.75 }}
          labelStyle={{ fill: t.inkSoft, fontSize: 13 }}
        />
        <ChartsReferenceLine
          y={lowerLimit}
          label={`−1.96 SD: ${lowerLimit.toFixed(1)}`}
          labelAlign="end"
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "8 6", strokeWidth: 1.75 }}
          labelStyle={{ fill: t.inkSoft, fontSize: 13 }}
        />
      </ScatterChart>
    </Box>
  );
}
