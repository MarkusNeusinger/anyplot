// anyplot.ai
// audiogram-clinical: Clinical Audiogram
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 91/100 | Created: 2026-06-15
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "audiogram-clinical · javascript · muix · anyplot.ai";
const HEADER_H = 84;
const LEGEND_H = 44;
const Y_LABEL = "Hearing level (dB HL)";
const OCTAVES = [125, 250, 500, 1000, 2000, 4000, 8000]; // standard audiometric octave frequencies (Hz)
const Y_MIN = -10; // standard audiogram range (dB HL), widened only when a threshold falls outside
const Y_MAX = 120;
const Y_STEP = 10; // audiogram grid step (dB)
const X_PAD_OCTAVES = 0.2; // room beyond the outer octaves so edge symbols stay whole
const PTA_FREQS = [500, 1000, 2000, 4000]; // four-frequency pure-tone average (Hz)
// ASHA degrees of hearing loss: upper bound of each band in dB HL
const BANDS = [
  { label: "Normal", to: 25 },
  { label: "Mild", to: 40 },
  { label: "Moderate", to: 55 },
  { label: "Moderately severe", to: 70 },
  { label: "Severe", to: 90 },
  { label: "Profound", to: Infinity },
];
const BAND_OPACITY_STEP = 0.045; // band shade deepens with severity, in t.inkSoft
// Clinical convention: right ear red circles, left ear blue crosses
const RIGHT_COLOR = t.palette[4];
const LEFT_COLOR = t.palette[2];
const MARK_R = 9;

// Columns: set these to your data's column names
const FREQUENCY = "Frequency (Hz)"; // role: frequency
const RIGHT = "Right ear (dB HL)"; // role: threshold_right
const LEFT = "Left ear (dB HL)"; // role: threshold_left

// Data: replace this block with your own records, one object per row
// Occupational health screening: pure-tone thresholds with the noise-induced
// high-frequency loss typical of long workplace noise exposure
const data = [
  { [FREQUENCY]: 125, [RIGHT]: 15, [LEFT]: 10 },
  { [FREQUENCY]: 250, [RIGHT]: 15, [LEFT]: 15 },
  { [FREQUENCY]: 500, [RIGHT]: 20, [LEFT]: 15 },
  { [FREQUENCY]: 1000, [RIGHT]: 25, [LEFT]: 20 },
  { [FREQUENCY]: 2000, [RIGHT]: 45, [LEFT]: 40 },
  { [FREQUENCY]: 4000, [RIGHT]: 75, [LEFT]: 70 },
  { [FREQUENCY]: 8000, [RIGHT]: 80, [LEFT]: 75 },
];

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[FREQUENCY] - b[FREQUENCY]);
const freqs = rows.map((d) => d[FREQUENCY]);
const levels = rows.flatMap((d) => [d[RIGHT], d[LEFT]]).filter((v) => v != null);

const xLo = Math.min(OCTAVES[0], freqs[0]) / 2 ** X_PAD_OCTAVES;
const xHi = Math.max(OCTAVES[OCTAVES.length - 1], freqs[freqs.length - 1]) * 2 ** X_PAD_OCTAVES;
const yLo = Math.min(Y_MIN, Math.floor((Math.min(...levels) - Y_STEP / 2) / Y_STEP) * Y_STEP);
const yHi = Math.max(Y_MAX, Math.ceil((Math.max(...levels) + Y_STEP / 2) / Y_STEP) * Y_STEP);
const yTicks = Array.from({ length: Math.round((yHi - yLo) / Y_STEP) + 1 }, (_, i) => yLo + i * Y_STEP);

const fmtFreq = (v: number) => (v >= 1000 ? `${v / 1000}k` : `${v}`);
const UNIT = RIGHT.match(/\(([^)]+)\)/)?.[1] ?? "";
const ptaRows = rows.filter((d) => PTA_FREQS.includes(d[FREQUENCY]));
const ptaRight = Math.round(ptaRows.reduce((s, d) => s + d[RIGHT], 0) / ptaRows.length);
const ptaLeft = Math.round(ptaRows.reduce((s, d) => s + d[LEFT], 0) / ptaRows.length);
const SUBTITLE = [
  `${rows.length} test frequencies, ${fmtFreq(freqs[0])}–${fmtFreq(freqs[freqs.length - 1])} Hz`,
  ptaRows.length === PTA_FREQS.length
    ? `pure-tone average ${fmtFreq(PTA_FREQS[0])}–${fmtFreq(PTA_FREQS[PTA_FREQS.length - 1])} Hz: right ${ptaRight}, left ${ptaLeft} ${UNIT}`
    : null,
]
  .filter(Boolean)
  .join(" · ");

// Severity bands across the full width, deepening with the degree of loss, named in
// the right margin
function SeverityBands() {
  const yScale = useYScale();
  const { left, width } = useDrawingArea();
  return (
    <g>
      {BANDS.map((band, i) => {
        const from = i === 0 ? yLo : BANDS[i - 1].to;
        const to = Math.min(band.to, yHi);
        if (to <= from) return null;
        const y0 = yScale(from);
        const y1 = yScale(to);
        const mid = (y0 + y1) / 2;
        const range = i === 0 ? `≤ ${band.to}` : band.to === Infinity ? `> ${from}` : `${from + 1}–${band.to}`;
        return (
          <g key={band.label}>
            <rect
              x={left}
              y={Math.min(y0, y1)}
              width={width}
              height={Math.abs(y1 - y0)}
              fill={t.inkSoft}
              fillOpacity={BAND_OPACITY_STEP * (i + 1)}
            />
            <text x={left + width + 14} y={mid - 4} fontSize={15} fontWeight={600} fill={t.ink}>
              {band.label}
            </text>
            <text x={left + width + 14} y={mid + 15} fontSize={14} fill={t.inkSoft}>
              {range}
            </text>
          </g>
        );
      })}
    </g>
  );
}

// O for the right ear and X for the left, at each threshold's exact coordinates
function EarSymbols() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {rows.map((d) => {
        const x = xScale(d[FREQUENCY]);
        const yl = d[LEFT] != null ? yScale(d[LEFT]) : null;
        return (
          <g key={d[FREQUENCY]}>
            {d[RIGHT] != null && (
              <circle cx={x} cy={yScale(d[RIGHT])} r={MARK_R} fill="none" stroke={RIGHT_COLOR} strokeWidth={2.75} />
            )}
            {yl != null && (
              <path
                d={`M${x - 7},${yl - 7}L${x + 7},${yl + 7}M${x + 7},${yl - 7}L${x - 7},${yl + 7}`}
                stroke={LEFT_COLOR}
                strokeWidth={2.75}
                strokeLinecap="round"
              />
            )}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: HEADER_H, px: "40px", pt: "18px", boxSizing: "border-box" }}>
        <Typography sx={{ color: t.ink, fontSize: "22px", fontWeight: 600, lineHeight: 1.2 }}>
          {TITLE}
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: "15px", lineHeight: 1.2, mt: "8px" }}>
          {SUBTITLE}
        </Typography>
      </Box>
      <ChartsContainer
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        margin={{ top: 16, right: 170, bottom: 8, left: 24 }}
        xAxis={[
          {
            id: "freq",
            scaleType: "log",
            data: freqs,
            min: xLo,
            max: xHi,
            tickInterval: OCTAVES,
            valueFormatter: fmtFreq,
            label: FREQUENCY,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "level",
            min: yLo,
            max: yHi,
            reverse: true,
            tickInterval: yTicks,
            label: Y_LABEL,
            width: 70,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          { type: "line", id: "right", data: rows.map((d) => d[RIGHT]), label: RIGHT, color: RIGHT_COLOR, curve: "linear" },
          { type: "line", id: "left", data: rows.map((d) => d[LEFT]), label: LEFT, color: LEFT_COLOR, curve: "linear" },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 2.5 },
          '& .MuiLineChart-line[data-series="left"]': { strokeDasharray: "8 5" },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <SeverityBands />
        <ChartsGrid horizontal vertical />
        <LinePlot skipAnimation />
        <EarSymbols />
        <ChartsXAxis axisId="freq" />
        <ChartsYAxis axisId="level" />
      </ChartsContainer>
      <Box sx={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: "36px" }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <svg width={44} height={22}>
            <line x1={0} x2={44} y1={11} y2={11} stroke={RIGHT_COLOR} strokeWidth={2.5} />
            <circle cx={22} cy={11} r={MARK_R} fill="none" stroke={RIGHT_COLOR} strokeWidth={2.75} />
          </svg>
          <Typography sx={{ fontSize: 15, color: t.ink }}>{`${RIGHT.replace(/\s*\([^)]*\)$/, "")} (O)`}</Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <svg width={44} height={22}>
            <line x1={0} x2={44} y1={11} y2={11} stroke={LEFT_COLOR} strokeWidth={2.5} strokeDasharray="8 5" />
            <path d="M15,4L29,18M29,4L15,18" stroke={LEFT_COLOR} strokeWidth={2.75} strokeLinecap="round" />
          </svg>
          <Typography sx={{ fontSize: 15, color: t.ink }}>{`${LEFT.replace(/\s*\([^)]*\)$/, "")} (X)`}</Typography>
        </Box>
      </Box>
    </Box>
  );
}
