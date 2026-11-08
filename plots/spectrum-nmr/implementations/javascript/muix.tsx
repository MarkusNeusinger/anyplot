// anyplot.ai
// spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-08-24
import { LineChart } from "@mui/x-charts/LineChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const PEAK_THRESHOLD_SHARE = 0.1; // a line must reach this share of the tallest line
const RESOLUTION_PPM = 0.008; // a line is the highest point within this distance on either side
const MULTIPLET_GAP_PPM = 0.06; // lines closer than this belong to one multiplet
const MULTIPLICITY = ["s", "d", "t", "q", "quint", "sext", "sept"]; // by line count; more lines read "m"
const Y_PAD_SHARE = 0.04;
const LABEL_HEADROOM_SHARE = 0.14; // room above the tallest line for its label

// Columns: set these to your data's column names
const SHIFT = "Chemical shift δ (ppm)"; // role: chemical_shift
const INTENSITY = "Intensity (a.u.)"; // role: intensity

// Data: replace this block with your own records, one object per row
// Synthetic 1H NMR spectrum of ethanol (CH3-CH2-OH) with TMS as internal standard, built
// from the sample's signals (first-order multiplets with binomial line intensities,
// Lorentzian line shapes). A signal's area is proportional to height × binomial sum × half-width,
// scaled so CH3 : CH2 : OH integrate to 3 : 2 : 1 protons; the TMS height is arbitrary.
const signals = [
  { shift: 0.0, lines: 1, splittingPpm: 0, halfWidthPpm: 0.006, height: 24 }, // TMS singlet
  { shift: 1.2, lines: 3, splittingPpm: 0.024, halfWidthPpm: 0.004, height: 34 }, // CH3 triplet
  { shift: 2.6, lines: 1, splittingPpm: 0, halfWidthPpm: 0.012, height: 15.1 }, // OH singlet
  { shift: 3.7, lines: 4, splittingPpm: 0.024, halfWidthPpm: 0.004, height: 11.3 }, // CH2 quartet
];
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const count = 6000;
  const lo = -0.5;
  const hi = 4.6;
  return Array.from({ length: count }, (_, i) => {
    const shift = lo + (i * (hi - lo)) / (count - 1);
    const noise = rand() * 0.6;
    const signal = signals.reduce(
      (acc, a) =>
        acc +
        Array.from({ length: a.lines }, (_, k) => {
          const weight = Array.from({ length: k }, (_, j) => (a.lines - 1 - j) / (j + 1)).reduce((p, v) => p * v, 1);
          const z = (shift - (a.shift + (k - (a.lines - 1) / 2) * a.splittingPpm)) / a.halfWidthPpm;
          return (a.height * weight) / (1 + z * z);
        }).reduce((p, v) => p + v, 0),
      0,
    );
    return { [SHIFT]: shift, [INTENSITY]: noise + signal };
  });
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[SHIFT] - b[SHIFT]);
const shifts = rows.map((d) => d[SHIFT]);
const values = rows.map((d) => d[INTENSITY]);
const vMax = Math.max(...values);
const vMin = Math.min(...values);

// Lines: local maxima above the threshold that are the highest point within the resolution
const lines = rows
  .map((d, i) => ({ shift: d[SHIFT], value: d[INTENSITY], i }))
  .filter((p) => p.value >= PEAK_THRESHOLD_SHARE * vMax)
  .filter((p) =>
    rows.every((d, j) => j === p.i || Math.abs(d[SHIFT] - p.shift) > RESOLUTION_PPM || d[INTENSITY] < p.value),
  );
// Multiplets: neighbouring lines closer than the gap, labelled at their centre above their tallest line
const multiplets = lines
  .reduce((groups, line) => {
    const last = groups[groups.length - 1];
    if (last && line.shift - last[last.length - 1].shift < MULTIPLET_GAP_PPM) last.push(line);
    else groups.push([line]);
    return groups;
  }, [])
  .map((group) => {
    const centre = group.reduce((acc, l) => acc + l.shift, 0) / group.length;
    return {
      centre,
      top: Math.max(...group.map((l) => l.value)),
      text: `${Number(centre.toFixed(2)).toFixed(2)} ${MULTIPLICITY[group.length - 1] ?? "m"}`,
    };
  });

const yMin = vMin - (vMax - vMin) * Y_PAD_SHARE;
const yMax = vMax + (vMax - vMin) * LABEL_HEADROOM_SHARE;

const TITLE = "spectrum-nmr · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length.toLocaleString("en-US")} points from ${Math.min(...shifts)
  .toFixed(1)
  .replace("-", "−")} to ${Math.max(...shifts).toFixed(1)} ppm · ${multiplets.length} signals, ${lines.length} resolved lines · labels give δ and multiplicity`;
const HEADER_H = 80;

function MultipletLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {multiplets.map((m) => (
        <text
          key={m.centre}
          x={xScale(m.centre)}
          y={yScale(m.top) - 12}
          textAnchor="middle"
          fontSize={15}
          fontWeight={600}
          fill={t.ink}
        >
          {m.text}
        </text>
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
      <LineChart
        width={width}
        height={height - HEADER_H}
        margin={{ top: 12, right: 48, bottom: 12, left: 24 }}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        xAxis={[
          {
            data: shifts,
            scaleType: "linear",
            reverse: true,
            min: Math.min(...shifts),
            max: Math.max(...shifts),
            label: SHIFT,
            height: 62,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yMin,
            max: yMax,
            label: INTENSITY,
            width: 76,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "spectrum",
            data: values,
            curve: "linear",
            showMark: false,
            color: t.palette[0],
            label: INTENSITY,
          },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 1.6 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <MultipletLabels />
      </LineChart>
    </div>
  );
}
