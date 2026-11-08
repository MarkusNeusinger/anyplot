// anyplot.ai
// ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 90/100 | Updated: 2026-11-08
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const isDark = window.ANYPLOT_THEME === "dark";

// Constants
const PAPER_SPEED = 25; // mm per second, the clinical standard
const GAIN = 10; // mm per mV, the clinical standard
const MINOR_MM = 1; // light ruling every millimetre
const MAJOR_MM = 5; // bold ruling every 5 mm
const CAL_MV = 1; // calibration pulse height
const CAL_WIDTH_MM = 5; // calibration pulse width (0.2 s at 25 mm/s)
const CAL_MARGIN_MM = 10; // paper left of the recording that holds the calibration pulse
const V_PAD = 0.08; // share of the voltage range kept free above and below the traces
// ECG paper ruling in the Imprint matte red, as the spec asks for red or pink paper;
// on dark it is stronger so it stays visible yet below the traces
const RULING = t.palette[4];
const MINOR_ALPHA = isDark ? 0.3 : 0.16;
const MAJOR_ALPHA = isDark ? 0.58 : 0.38;
const PAPER_TINT = isDark ? 0.07 : 0.05;
// One trace colour: leads are told apart by their place in the layout and their label, as on clinical paper
const TRACE = t.palette[0];
const TITLE = "ecg-twelve-lead · javascript · muix · anyplot.ai";
const PAD = 16;
const HEADER_H = 64;
const ROW_GAP = 6;

// Columns: set these to your data's column names
const TIME = "Time (s)"; // role: time
const LEAD_I = "I"; // role: lead_I
const LEAD_II = "II"; // role: lead_II
const LEAD_III = "III"; // role: lead_III
const LEAD_AVR = "aVR"; // role: lead_aVR
const LEAD_AVL = "aVL"; // role: lead_aVL
const LEAD_AVF = "aVF"; // role: lead_aVF
const LEAD_V1 = "V1"; // role: lead_V1
const LEAD_V2 = "V2"; // role: lead_V2
const LEAD_V3 = "V3"; // role: lead_V3
const LEAD_V4 = "V4"; // role: lead_V4
const LEAD_V5 = "V5"; // role: lead_V5
const LEAD_V6 = "V6"; // role: lead_V6

// Data: replace this block with your own records, one object per row (one row per sample, voltages in mV)
// Synthetic normal sinus rhythm at 75 bpm, 10 s at 1000 Hz: every P-QRS-T complex is a sum of Gaussian
// deflections, and per-lead gains give I, II and V1-V6 their morphology (V1 rS, V4-V6 tall R); the other limb
// leads follow from I and II by Einthoven's and Goldberger's equations, so aVR comes out inverted
const data = (() => {
  const fs = 1000;
  const seconds = 10;
  const period = 0.8;
  const profile = [
    [LEAD_I, { p: 1.0, r: 0.75, s: 0.25, t: 0.9 }],
    [LEAD_II, { p: 1.2, r: 1.05, s: 0.3, t: 1.1 }],
    [LEAD_V1, { p: 0.7, r: 0.3, s: 1.0, t: -0.5 }],
    [LEAD_V2, { p: 0.8, r: 0.55, s: 1.35, t: 0.5 }],
    [LEAD_V3, { p: 0.8, r: 0.95, s: 0.95, t: 0.85 }],
    [LEAD_V4, { p: 0.85, r: 1.45, s: 0.5, t: 1.0 }],
    [LEAD_V5, { p: 0.9, r: 1.4, s: 0.25, t: 1.0 }],
    [LEAD_V6, { p: 0.9, r: 1.1, s: 0.15, t: 0.9 }],
  ];
  const round = (mv) => Math.round(mv * 1000) / 1000;
  return Array.from({ length: fs * seconds }, (_, i) => {
    const time = i / fs;
    const tb = time % period;
    const wave = (c, a, w) => a * Math.exp(-((tb - c) ** 2) / (2 * w * w));
    const mv = {};
    profile.forEach(([lead, g]) => {
      mv[lead] =
        wave(0.18, 0.13 * g.p, 0.022) + // P wave
        wave(0.355, -0.09, 0.011) + // Q
        wave(0.39, 1.0 * g.r, 0.011) + // R
        wave(0.42, -0.28 * g.s, 0.013) + // S
        wave(0.585, 0.3 * g.t, 0.042); // T wave
    });
    const i1 = mv[LEAD_I];
    const i2 = mv[LEAD_II];
    mv[LEAD_III] = i2 - i1;
    mv[LEAD_AVR] = -(i1 + i2) / 2;
    mv[LEAD_AVL] = i1 - i2 / 2;
    mv[LEAD_AVF] = i2 - i1 / 2;
    const row = { [TIME]: time };
    Object.entries(mv).forEach(([lead, v]) => {
      row[lead] = round(v);
    });
    return row;
  });
})();

// Plot: reads only data and the constants above
// Standard clinical 3x4 layout, each column a consecutive time window, and a Lead II rhythm strip below
const LAYOUT = [
  [LEAD_I, LEAD_AVR, LEAD_V1, LEAD_V4],
  [LEAD_II, LEAD_AVL, LEAD_V2, LEAD_V5],
  [LEAD_III, LEAD_AVF, LEAD_V3, LEAD_V6],
];
const RHYTHM = [LEAD_II];

const rows = [...data].sort((a, b) => a[TIME] - b[TIME]);
const times = rows.map((d) => d[TIME]);
const tMin = times[0];
const tMax = times[times.length - 1];
const columns = LAYOUT[0].length;
const stripSeconds = (tMax - tMin) / columns;
const column = times.map((tm) => Math.min(columns - 1, Math.floor((tm - tMin) / stripSeconds)));
const sampleRate = Math.round((times.length - 1) / (tMax - tMin));

const allLeads = [...LAYOUT.flat(), ...RHYTHM];
const voltages = rows.flatMap((d) => allLeads.map((lead) => d[lead])).filter((v) => Number.isFinite(v));
const rawLo = voltages.reduce((lo, v) => Math.min(lo, v), 0);
const rawHi = voltages.reduce((hi, v) => Math.max(hi, v), CAL_MV);
const majorMv = MAJOR_MM / GAIN;
// Voltage window from the data, widened to whole bold squares so every strip starts on a bold line
const vMin = Math.floor((rawLo - (rawHi - rawLo) * V_PAD) / majorMv) * majorMv;
const vMax = Math.ceil((rawHi + (rawHi - rawLo) * V_PAD) / majorMv) * majorMv;
const xMin = tMin - CAL_MARGIN_MM / PAPER_SPEED;

// One px-per-mm scale for every strip, the largest that fits the canvas, so 1 mm cells are square
const { width: W, height: H } = window.ANYPLOT_SIZE;
const stripMmW = CAL_MARGIN_MM + (tMax - tMin) * PAPER_SPEED;
const stripMmH = (vMax - vMin) * GAIN;
const stripCount = LAYOUT.length + 1;
const pxPerMm = Math.min(
  (W - 2 * PAD) / stripMmW,
  (H - 2 * PAD - HEADER_H - ROW_GAP * (stripCount - 1)) / (stripCount * stripMmH),
);
const stripW = stripMmW * pxPerMm;
const stripH = stripMmH * pxPerMm;

// Per strip: one line series per lead, holding its own time window and null elsewhere
const strips = [...LAYOUT, RHYTHM].map((leads, s) => ({
  key: `strip-${s}`,
  windows: leads.map((lead, c) => ({
    lead,
    from: leads.length === 1 ? tMin : tMin + c * stripSeconds,
  })),
  series: leads.map((lead, c) => ({
    type: "line",
    id: `${s}-${lead}`,
    data: rows.map((d, i) => (leads.length === 1 || column[i] === c ? d[lead] : null)),
    color: TRACE,
    showMark: false,
  })),
}));

const subtitle = `${allLeads.length - RHYTHM.length} leads, ${stripSeconds.toFixed(1)} s each, and a ${(tMax - tMin).toFixed(0)} s ${RHYTHM.join(", ")} rhythm strip · ${sampleRate} Hz · ${PAPER_SPEED} mm/s · ${GAIN} mm/mV · ${CAL_MV} mV calibration pulse`;

function EcgPaper() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { left, top, width, height } = useDrawingArea();
  const minor = [];
  const major = [];
  const nx = Math.round(stripMmW / MINOR_MM);
  const ny = Math.round(stripMmH / MINOR_MM);
  for (let i = 0; i <= nx; i += 1) {
    const x = xScale(xMin + (i * MINOR_MM) / PAPER_SPEED);
    (i % (MAJOR_MM / MINOR_MM) === 0 ? major : minor).push(`M${x},${top}V${top + height}`);
  }
  for (let j = 0; j <= ny; j += 1) {
    const y = yScale(vMin + (j * MINOR_MM) / GAIN);
    (j % (MAJOR_MM / MINOR_MM) === 0 ? major : minor).push(`M${left},${y}H${left + width}`);
  }
  return (
    <g>
      <rect x={left} y={top} width={width} height={height} fill={RULING} fillOpacity={PAPER_TINT} />
      <path d={minor.join("")} stroke={RULING} strokeOpacity={MINOR_ALPHA} strokeWidth={0.8} fill="none" />
      <path d={major.join("")} stroke={RULING} strokeOpacity={MAJOR_ALPHA} strokeWidth={1.3} fill="none" />
    </g>
  );
}

function EcgMarks({ windows }) {
  const xScale = useXScale();
  const yScale = useYScale();
  const { top } = useDrawingArea();
  const calX0 = xScale(xMin + (CAL_MARGIN_MM - CAL_WIDTH_MM) / 2 / PAPER_SPEED);
  const calX1 = xScale(xMin + (CAL_MARGIN_MM + CAL_WIDTH_MM) / 2 / PAPER_SPEED);
  const y0 = yScale(0);
  const y1 = yScale(CAL_MV);
  return (
    <g>
      <path
        d={`M${xScale(xMin)},${y0}H${calX0}V${y1}H${calX1}V${y0}H${xScale(tMin)}`}
        stroke={TRACE}
        strokeWidth={2}
        fill="none"
        strokeLinejoin="miter"
      />
      {windows.map((w) => (
        <text
          key={w.lead}
          x={xScale(w.from) + 6}
          y={top + 20}
          fontSize={16}
          fontWeight={700}
          fill={t.ink}
          stroke={t.pageBg}
          strokeWidth={4}
          paintOrder="stroke"
        >
          {w.lead}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  return (
    <div style={{ width: W, height: H, boxSizing: "border-box", padding: PAD, background: t.pageBg }}>
      <div style={{ height: HEADER_H, padding: "6px 4px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{subtitle}</div>
      </div>
      <div
        style={{
          height: H - 2 * PAD - HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: ROW_GAP,
        }}
      >
        {strips.map((strip) => (
          <ChartsContainer
            key={strip.key}
            width={stripW}
            height={stripH}
            margin={0}
            skipAnimation
            series={strip.series}
            xAxis={[{ data: times, scaleType: "linear", min: xMin, max: tMax, position: "none" }]}
            yAxis={[{ min: vMin, max: vMax, position: "none" }]}
            sx={{ "& .MuiLineChart-line": { strokeWidth: 1.8, strokeLinejoin: "round" } }}
          >
            <EcgPaper />
            <LinePlot skipAnimation />
            <EcgMarks windows={strip.windows} />
          </ChartsContainer>
        ))}
      </div>
    </div>
  );
}
