// anyplot.ai
// spectrum-basic: Frequency Spectrum Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-09
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Synthetic FFT magnitude spectrum of a plucked low-E guitar string (82.4 Hz)
// and its first four harmonics, riding on a gently sloping noise floor.
let seed = 42;
function lcg() {
  seed = (Math.imul(seed, 1103515245) + 12345) | 0;
  return (seed >>> 0) / 4294967296;
}

const FUNDAMENTAL_HZ = 82.4;
const HARMONICS = [1, 2, 3, 4, 5].map((n) => ({
  freq: FUNDAMENTAL_HZ * n,
  amplitudeDb: -6 - (n - 1) * 8,
  widthDecades: 0.04 + n * 0.008,
}));

const POINTS = 400;
const MIN_FREQ = 20;
const MAX_FREQ = 8000;
const logMin = Math.log10(MIN_FREQ);
const logMax = Math.log10(MAX_FREQ);

const frequency = [];
const amplitude = [];
for (let i = 0; i < POINTS; i++) {
  const f = Math.pow(10, logMin + (logMax - logMin) * (i / (POINTS - 1)));
  frequency.push(Math.round(f * 10) / 10);

  // Pink-noise-like floor: drops with frequency, plus small fixed jitter
  const noiseFloorDb = -55 - 6 * Math.log10(f / MIN_FREQ) + (lcg() - 0.5) * 4;

  // Each harmonic contributes a narrow Gaussian bump in log-frequency space
  let peakDb = -100;
  for (const h of HARMONICS) {
    const distance = (Math.log10(f) - Math.log10(h.freq)) / h.widthDecades;
    peakDb = Math.max(peakDb, h.amplitudeDb - 4 * distance * distance);
  }

  // Combine floor and harmonics in the power domain, then back to dB
  const powerSum = Math.pow(10, noiseFloorDb / 10) + Math.pow(10, peakDb / 10);
  amplitude.push(Math.round(10 * Math.log10(powerSum) * 10) / 10);
}

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleHeight = 56;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <Typography
        color="text.primary"
        sx={{
          fontSize: 22,
          fontWeight: 500,
          height: titleHeight,
          boxSizing: "border-box",
          display: "flex",
          alignItems: "center",
          pl: 1,
        }}
      >
        spectrum-basic · javascript · muix · anyplot.ai
      </Typography>
      <LineChart
        width={width}
        height={height - titleHeight}
        skipAnimation
        series={[
          {
            data: amplitude,
            label: "Amplitude",
            color: t.palette[0],
            showMark: false,
            curve: "linear",
            area: true,
          },
        ]}
        sx={{
          "& .MuiLineElement-root": { strokeWidth: 2.5 },
          "& .MuiAreaElement-root": { fillOpacity: 0.12 },
        }}
        xAxis={[
          {
            data: frequency,
            scaleType: "log",
            label: "Frequency (Hz)",
            valueFormatter: (v) => (v >= 1000 ? `${Math.round(v / 100) / 10}k` : `${Math.round(v)}`),
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
          },
        ]}
        yAxis={[
          {
            label: "Amplitude (dB)",
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
            tickFontSize: 26,
          },
        ]}
        grid={{ horizontal: true }}
        margin={{ left: 130, right: 40, top: 20, bottom: 70 }}
        slotProps={{ legend: { hidden: true } }}
      >
        <ChartsReferenceLine
          x={FUNDAMENTAL_HZ}
          label={`Fundamental · ${FUNDAMENTAL_HZ} Hz`}
          labelAlign="end"
          lineStyle={{ stroke: t.amber, strokeDasharray: "6 4", strokeWidth: 1.5 }}
          labelStyle={{ fill: t.amber, fontSize: 13 }}
        />
      </LineChart>
    </div>
  );
}
