// anyplot.ai
// bode-basic: Bode Plot for Frequency Response
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 84/100 | Created: 2026-06-17
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const GAIN_REF_DB = 0; // unity gain: the gain crossover and the gain margin are read against it
const PHASE_REF_DEG = -180; // the phase crossover and the phase margin are read against it
const Y_PAD_SHARE = 0.06; // y padding as a share of each panel's span

// Columns: set these to your data's column names
const FREQUENCY = "Frequency (Hz)"; // role: frequency_hz
const MAGNITUDE = "Magnitude (dB)"; // role: magnitude_db
const PHASE = "Phase (°)"; // role: phase_deg

// Data: replace this block with your own records, one object per row
// Open-loop response of G(s) = 20 / ((s/1 + 1)(s/10 + 1)(s/100 + 1)), three real
// poles at 1, 10 and 100 rad/s, sampled at 250 log-spaced frequencies.
const data = (() => {
  const gainK = 20;
  const poles = [1, 10, 100];
  const count = 250;
  return Array.from({ length: count }, (_, i) => {
    const f = 10 ** (-2 + (4 * i) / (count - 1));
    const omega = 2 * Math.PI * f;
    const gain = gainK / Math.sqrt(poles.reduce((p, w) => p * (1 + (omega / w) ** 2), 1));
    const phase = -poles.reduce((s, w) => s + Math.atan(omega / w), 0) * (180 / Math.PI);
    return { [FREQUENCY]: f, [MAGNITUDE]: 20 * Math.log10(gain), [PHASE]: phase };
  });
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[FREQUENCY] - b[FREQUENCY]);
const freqs = rows.map((d) => d[FREQUENCY]);
const mags = rows.map((d) => d[MAGNITUDE]);
const phases = rows.map((d) => d[PHASE]);

// Crossovers, interpolated in log frequency between the two samples that straddle the
// reference; each keeps the local slope of the other panel's curve for label placement
let gainCross: { f: number; phase: number; slope: number } | null = null;
for (let i = 1; i < rows.length && !gainCross; i += 1) {
  if (mags[i - 1] > GAIN_REF_DB && mags[i] <= GAIN_REF_DB) {
    const s = (mags[i - 1] - GAIN_REF_DB) / (mags[i - 1] - mags[i]);
    const f = 10 ** (Math.log10(freqs[i - 1]) + s * (Math.log10(freqs[i]) - Math.log10(freqs[i - 1])));
    gainCross = { f, phase: phases[i - 1] + s * (phases[i] - phases[i - 1]), slope: phases[i] - phases[i - 1] };
  }
}
let phaseCross: { f: number; mag: number; slope: number } | null = null;
for (let i = 1; i < rows.length && !phaseCross; i += 1) {
  if (phases[i - 1] > PHASE_REF_DEG && phases[i] <= PHASE_REF_DEG) {
    const s = (phases[i - 1] - PHASE_REF_DEG) / (phases[i - 1] - phases[i]);
    const f = 10 ** (Math.log10(freqs[i - 1]) + s * (Math.log10(freqs[i]) - Math.log10(freqs[i - 1])));
    phaseCross = { f, mag: mags[i - 1] + s * (mags[i] - mags[i - 1]), slope: mags[i] - mags[i - 1] };
  }
}

// Units come from the column names; a degree sign attaches without a space
const magUnit = MAGNITUDE.match(/\(([^)]+)\)\s*$/)?.[1] ?? "";
const phaseUnit = PHASE.match(/\(([^)]+)\)\s*$/)?.[1] ?? "";
const freqUnit = FREQUENCY.match(/\(([^)]+)\)\s*$/)?.[1] ?? "";
const magSuffix = magUnit.startsWith("°") ? magUnit : ` ${magUnit}`;
const phaseSuffix = phaseUnit.startsWith("°") ? phaseUnit : ` ${phaseUnit}`;

// A margin label sits on the side of its marker that the curve leaves: the curve runs
// toward the reference line on the other side, where the label would cross it
const gainMarker = phaseCross && {
  x: phaseCross.f,
  from: phaseCross.mag,
  to: GAIN_REF_DB,
  side: (GAIN_REF_DB - phaseCross.mag) * phaseCross.slope < 0 ? 1 : -1,
  label: `GM ${(GAIN_REF_DB - phaseCross.mag).toFixed(1)}${magSuffix} at ${phaseCross.f.toFixed(2)} ${freqUnit}`,
};
const phaseMarker = gainCross && {
  x: gainCross.f,
  from: gainCross.phase,
  to: PHASE_REF_DEG,
  side: (PHASE_REF_DEG - gainCross.phase) * gainCross.slope < 0 ? 1 : -1,
  label: `PM ${(gainCross.phase - PHASE_REF_DEG).toFixed(1)}${phaseSuffix} at ${gainCross.f.toFixed(2)} ${freqUnit}`,
};

// Shared log axis: one tick per decade over the data's frequency range
const firstDecade = Math.floor(Math.log10(freqs[0]));
const lastDecade = Math.ceil(Math.log10(freqs[freqs.length - 1]));
const decades = Array.from({ length: lastDecade - firstDecade + 1 }, (_, i) => 10 ** (firstDecade + i));
const formatFreq = (v: number) => (v >= 1 ? v.toFixed(0) : v.toPrecision(1));

const magLo = Math.min(...mags, GAIN_REF_DB);
const magHi = Math.max(...mags, GAIN_REF_DB);
const phaseLo = Math.min(...phases, PHASE_REF_DEG);
const phaseHi = Math.max(...phases, PHASE_REF_DEG);
const magPad = (magHi - magLo) * Y_PAD_SHARE;
const phasePad = (phaseHi - phaseLo) * Y_PAD_SHARE;

const TITLE = "bode-basic · javascript · muix · anyplot.ai";
const subtitle = `Open-loop frequency response · ${rows.length} log-spaced points from ${formatFreq(freqs[0])} to ${formatFreq(freqs[freqs.length - 1])} ${freqUnit}`;
const TITLE_H = 76;
const X_AXIS_H = 64;
const Y_AXIS_W = 84;
const MARGIN = { left: 24, right: 48 };

function MarginMarker({ marker }: { marker: { x: number; from: number; to: number; side: number; label: string } }) {
  const xScale = useXScale();
  const yScale = useYScale();
  const x = xScale(marker.x);
  const y0 = yScale(marker.from);
  const y1 = yScale(marker.to);
  return (
    <g>
      <line x1={x} y1={y0} x2={x} y2={y1} stroke={t.ink} strokeWidth={2.5} />
      <circle cx={x} cy={y0} r={4.5} fill={t.ink} />
      <circle cx={x} cy={y1} r={4.5} fill={t.ink} />
      <text
        x={x + 12 * marker.side}
        y={(y0 + y1) / 2}
        textAnchor={marker.side > 0 ? "start" : "end"}
        dominantBaseline="middle"
        fontSize={15}
        fontWeight={600}
        fill={t.ink}
      >
        {marker.label}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const topH = Math.floor((height - TITLE_H - X_AXIS_H) / 2);
  const bottomH = height - TITLE_H - topH;
  const xAxisBase = {
    data: freqs,
    scaleType: "log" as const,
    min: freqs[0],
    max: freqs[freqs.length - 1],
    tickInterval: decades,
    valueFormatter: formatFreq,
  };
  const yAxisStyle = {
    width: Y_AXIS_W,
    labelStyle: { fontSize: 16, fill: t.ink },
    tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
  };
  const sx = {
    "& .MuiChartsAxis-line": { stroke: t.inkSoft },
    "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
    "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
    "& .MuiLineChart-line": { strokeWidth: 3 },
  };
  const refLine = { stroke: t.inkSoft, strokeDasharray: "8 6", strokeWidth: 1.75 };
  const refLabel = { fontSize: 14, fill: t.inkSoft };

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column", background: t.pageBg }}>
      <div style={{ height: TITLE_H, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, paddingTop: 10 }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>

      <LineChart
        width={width}
        height={topH}
        skipAnimation
        hideLegend
        grid={{ horizontal: true, vertical: true }}
        xAxis={[{ ...xAxisBase, position: "none" }]}
        yAxis={[{ ...yAxisStyle, label: MAGNITUDE, min: magLo - magPad, max: magHi + magPad }]}
        series={[{ id: "magnitude", data: mags, label: MAGNITUDE, color: t.palette[0], showMark: false }]}
        margin={{ ...MARGIN, top: 12, bottom: 8 }}
        sx={sx}
      >
        <ChartsReferenceLine
          y={GAIN_REF_DB}
          label={`${GAIN_REF_DB}${magSuffix}`}
          labelAlign="end"
          lineStyle={refLine}
          labelStyle={refLabel}
        />
        {gainMarker && <MarginMarker marker={gainMarker} />}
      </LineChart>

      <LineChart
        width={width}
        height={bottomH}
        skipAnimation
        hideLegend
        grid={{ horizontal: true, vertical: true }}
        xAxis={[
          {
            ...xAxisBase,
            label: FREQUENCY,
            height: X_AXIS_H,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[{ ...yAxisStyle, label: PHASE, min: phaseLo - phasePad, max: phaseHi + phasePad }]}
        series={[{ id: "phase", data: phases, label: PHASE, color: t.palette[1], showMark: false }]}
        margin={{ ...MARGIN, top: 8, bottom: 12 }}
        sx={sx}
      >
        <ChartsReferenceLine
          y={PHASE_REF_DEG}
          label={`${PHASE_REF_DEG.toString().replace("-", "−")}${phaseSuffix}`}
          labelAlign="end"
          lineStyle={refLine}
          labelStyle={refLabel}
        />
        {phaseMarker && <MarginMarker marker={phaseMarker} />}
      </LineChart>
    </div>
  );
}
