// anyplot.ai
// spectrum-basic: Frequency Spectrum Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-09
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot, AreaPlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const PEAK_PROMINENCE_DB = 15; // a local maximum counts as a dominant peak this far above the median level
const MAX_PEAK_LABELS = 5;
const Y_PAD_SHARE = 0.12; // headroom above the highest peak for its label
const LOG_TICK_MANTISSAS = [1, 2, 5];

// Columns: set these to your data's column names
const FREQUENCY = "Frequency (Hz)"; // role: frequency
const AMPLITUDE = "Amplitude (dB)"; // role: amplitude

// Data: replace this block with your own records, one object per row
// Magnitude spectrum of a plucked low-E guitar string (82.4 Hz) and its first four
// harmonics as narrow lines over a gently sloping noise floor, on 1024 log-spaced bins
// from 20 Hz to 8 kHz
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (Math.imul(seed, 1103515245) + 12345) | 0;
    return (seed >>> 0) / 4294967296;
  };
  const bins = 1024;
  const harmonics = [1, 2, 3, 4, 5].map((n) => ({
    freq: 82.4 * n,
    amplitudeDb: -6 - (n - 1) * 8,
    widthDecades: 0.005 + n * 0.001,
  }));
  return Array.from({ length: bins }, (_, i) => {
    const f = 10 ** (Math.log10(20) + (Math.log10(8000) - Math.log10(20)) * (i / (bins - 1)));
    const floorDb = -55 - 6 * Math.log10(f / 20) + (rand() - 0.5) * 4;
    const peakDb = Math.max(
      -100,
      ...harmonics.map((h) => h.amplitudeDb - 4 * ((Math.log10(f) - Math.log10(h.freq)) / h.widthDecades) ** 2),
    );
    const powerDb = 10 * Math.log10(10 ** (floorDb / 10) + 10 ** (peakDb / 10));
    return { [FREQUENCY]: Math.round(f * 10) / 10, [AMPLITUDE]: Math.round(powerDb * 10) / 10 };
  });
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[FREQUENCY] - b[FREQUENCY]);
const freqs = rows.map((d) => d[FREQUENCY]);
const amps = rows.map((d) => d[AMPLITUDE]);

const median = [...amps].sort((a, b) => a - b)[Math.floor(amps.length / 2)];
const peaks = rows
  .filter(
    (d, i) =>
      i > 0 &&
      i < rows.length - 1 &&
      d[AMPLITUDE] > amps[i - 1] &&
      d[AMPLITUDE] >= amps[i + 1] &&
      d[AMPLITUDE] - median >= PEAK_PROMINENCE_DB,
  )
  .sort((a, b) => b[AMPLITUDE] - a[AMPLITUDE])
  .slice(0, MAX_PEAK_LABELS);

const yLo = Math.min(...amps);
const yHi = Math.max(...amps);
const yMin = yLo - (yHi - yLo) * Y_PAD_SHARE * 0.5;
const yMax = yHi + (yHi - yLo) * Y_PAD_SHARE;
const xMin = Math.min(...freqs);
const xMax = Math.max(...freqs);
const xTicks = Array.from(
  { length: Math.ceil(Math.log10(xMax)) - Math.floor(Math.log10(xMin)) + 1 },
  (_, i) => 10 ** (Math.floor(Math.log10(xMin)) + i),
)
  .flatMap((decade) => LOG_TICK_MANTISSAS.map((m) => m * decade))
  .filter((v) => v >= xMin && v <= xMax);
const peakLabels = peaks.map((p) => `${p[FREQUENCY].toLocaleString("en-US", { maximumSignificantDigits: 3 })} Hz`);

const TITLE = "spectrum-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length.toLocaleString("en-US")} bins from ${xMin.toLocaleString("en-US")} to ${xMax.toLocaleString(
  "en-US",
)} Hz · ${peaks.length} peaks at least ${PEAK_PROMINENCE_DB} dB above the median level`;
const HEADER_H = 80;

function PeakMarkers() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {peaks.map((p, i) => (
        <g key={p[FREQUENCY]}>
          <circle
            cx={xScale(p[FREQUENCY])}
            cy={yScale(p[AMPLITUDE])}
            r={6}
            fill={t.palette[0]}
            stroke={t.pageBg}
            strokeWidth={2}
          />
          <text
            x={xScale(p[FREQUENCY])}
            y={yScale(p[AMPLITUDE]) - 14}
            textAnchor="middle"
            fontSize={14}
            fontWeight={600}
            fill={t.ink}
          >
            {peakLabels[i]}
          </text>
        </g>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 8,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={height - HEADER_H}
        margin={{ top: 12, right: 40, bottom: 12, left: 24 }}
        skipAnimation
        series={[
          {
            type: "line",
            id: "spectrum",
            data: amps,
            label: AMPLITUDE,
            color: t.palette[0],
            showMark: false,
            curve: "linear",
            area: true,
            baseline: "min",
          },
        ]}
        xAxis={[
          {
            data: freqs,
            scaleType: "log",
            min: xMin,
            max: xMax,
            tickInterval: xTicks,
            valueFormatter: (v) => (v >= 1000 ? `${v / 1000}k` : `${v}`),
            label: FREQUENCY,
            height: 62,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yMin,
            max: yMax,
            label: AMPLITUDE,
            width: 76,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 2.5 },
          "& .MuiLineChart-area": { fillOpacity: 0.12 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal vertical />
        <AreaPlot skipAnimation />
        <LinePlot skipAnimation />
        <PeakMarkers />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </div>
  );
}
