// anyplot.ai
// bode-basic: Bode Plot for Frequency Response
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-17

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data: G(s) = 20 / ((s/1+1)(s/10+1)(s/100+1)) — 3-pole open-loop TF ---
// Pole frequencies: ω₁=1, ω₂=10, ω₃=100 rad/s  (0.16 Hz, 1.59 Hz, 15.9 Hz)
const K = 20;
const w1 = 1;
const w2 = 10;
const w3 = 100;
const N = 250;

const freqs: number[] = [];
const mags: number[] = [];
const phases: number[] = [];

for (let i = 0; i < N; i++) {
  const f = Math.pow(10, -2 + (i / (N - 1)) * 4); // 0.01 to 100 Hz
  const omega = 2 * Math.PI * f;
  const gain =
    K /
    Math.sqrt(
      (1 + (omega / w1) ** 2) *
        (1 + (omega / w2) ** 2) *
        (1 + (omega / w3) ** 2)
    );
  freqs.push(f);
  mags.push(20 * Math.log10(gain));
  phases.push(
    -(
      Math.atan(omega / w1) +
      Math.atan(omega / w2) +
      Math.atan(omega / w3)
    ) *
      (180 / Math.PI)
  );
}

// Gain crossover: magnitude crosses 0 dB going downward
let gcFreq = freqs[0];
let phaseAtGC = phases[0];
for (let i = 1; i < N; i++) {
  if (mags[i - 1] > 0 && mags[i] <= 0) {
    gcFreq = freqs[i];
    phaseAtGC = phases[i];
    break;
  }
}
const phaseMargin = phaseAtGC + 180;

// Phase crossover: phase crosses -180° going downward
let pcFreq = freqs[N - 1];
let magAtPC = mags[N - 1];
let hasCrossover = false;
for (let i = 1; i < N; i++) {
  if (phases[i - 1] > -180 && phases[i] <= -180) {
    pcFreq = freqs[i];
    magAtPC = mags[i];
    hasCrossover = true;
    break;
  }
}
const gainMargin = hasCrossover ? -magAtPC : null;

// --- Chart component --------------------------------------------------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleH = 56;
  const panelH = Math.floor((height - titleH) / 2);

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          height: titleH,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Typography sx={{ fontSize: 20, fontWeight: 500, letterSpacing: 0.4 }}>
          bode-basic · javascript · muix · anyplot.ai
        </Typography>
      </Box>

      {/* Magnitude panel */}
      <LineChart
        width={width}
        height={panelH}
        colors={[t.palette[0]]}
        skipAnimation
        xAxis={[
          {
            data: freqs,
            scaleType: "log",
            tickLabelStyle: { fontSize: 12 },
          },
        ]}
        yAxis={[
          {
            label: "Magnitude (dB)",
            labelStyle: { fontSize: 15 },
            tickLabelStyle: { fontSize: 13 },
          },
        ]}
        series={[{ data: mags, showMark: false, label: "Magnitude" }]}
        slotProps={{ legend: { hidden: true } }}
        grid={{ horizontal: true, vertical: true }}
        margin={{ left: 80, right: 50, top: 20, bottom: 30 }}
      >
        <ChartsReferenceLine
          y={0}
          lineStyle={{
            stroke: t.inkSoft,
            strokeDasharray: "6 4",
            strokeWidth: 1.5,
          }}
          label="0 dB"
          labelStyle={{ fontSize: 12 }}
          labelAlign="end"
        />
        {hasCrossover && (
          <ChartsReferenceLine
            x={pcFreq}
            lineStyle={{
              stroke: t.palette[3],
              strokeDasharray: "6 4",
              strokeWidth: 1.5,
            }}
            label={`GM = ${gainMargin!.toFixed(1)} dB`}
            labelStyle={{ fontSize: 12, fill: t.palette[3] }}
            labelAlign="start"
          />
        )}
      </LineChart>

      {/* Phase panel */}
      <LineChart
        width={width}
        height={panelH}
        colors={[t.palette[1]]}
        skipAnimation
        xAxis={[
          {
            data: freqs,
            scaleType: "log",
            label: "Frequency (Hz)",
            labelStyle: { fontSize: 15 },
            tickLabelStyle: { fontSize: 13 },
          },
        ]}
        yAxis={[
          {
            label: "Phase (°)",
            labelStyle: { fontSize: 15 },
            tickLabelStyle: { fontSize: 13 },
          },
        ]}
        series={[{ data: phases, showMark: false, label: "Phase" }]}
        slotProps={{ legend: { hidden: true } }}
        grid={{ horizontal: true, vertical: true }}
        margin={{ left: 80, right: 50, top: 5, bottom: 60 }}
      >
        <ChartsReferenceLine
          y={-180}
          lineStyle={{
            stroke: t.inkSoft,
            strokeDasharray: "6 4",
            strokeWidth: 1.5,
          }}
          label="-180°"
          labelStyle={{ fontSize: 12 }}
          labelAlign="end"
        />
        <ChartsReferenceLine
          x={gcFreq}
          lineStyle={{
            stroke: t.palette[2],
            strokeDasharray: "6 4",
            strokeWidth: 1.5,
          }}
          label={`PM = ${phaseMargin.toFixed(1)}°`}
          labelStyle={{ fontSize: 12, fill: t.palette[2] }}
          labelAlign="start"
        />
      </LineChart>
    </Box>
  );
}
