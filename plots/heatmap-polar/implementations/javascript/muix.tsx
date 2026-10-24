// anyplot.ai
// heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-05
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// Constants
const ANGULAR_COL = "angular";
const RADIAL_COL = "radial";
const VALUE_COL = "value";

const START_ANGLE = 0;
const RING_HOLE_RATIO = 0.17;
const LABEL_PAD = 56;
const DAY_LABEL_ANGLE = 180;
const COLORBAR_TICKS = [0, 0.25, 0.5, 0.75, 1];
const GRAD_ID = "polar-heatmap-seq-grad";

// Data
const DAY_SEEDS = [
  { day: "Mon", base: 14, weekend: false, nightlife: false },
  { day: "Tue", base: 18, weekend: false, nightlife: false },
  { day: "Wed", base: 22, weekend: false, nightlife: false },
  { day: "Thu", base: 26, weekend: false, nightlife: false },
  { day: "Fri", base: 31, weekend: false, nightlife: true },
  { day: "Sat", base: 27, weekend: true, nightlife: true },
  { day: "Sun", base: 19, weekend: true, nightlife: false },
];

const HOUR_LABELS = [
  "12am", "1am", "2am", "3am", "4am", "5am",
  "6am", "7am", "8am", "9am", "10am", "11am",
  "12pm", "1pm", "2pm", "3pm", "4pm", "5pm",
  "6pm", "7pm", "8pm", "9pm", "10pm", "11pm",
];

type PolarHeatmapRow = {
  [ANGULAR_COL]: string;
  [RADIAL_COL]: string;
  [VALUE_COL]: number;
};

const DATA: PolarHeatmapRow[] = [];
const totalHours = HOUR_LABELS.length;

for (let dIdx = 0; dIdx < DAY_SEEDS.length; dIdx++) {
  const ds = DAY_SEEDS[dIdx];
  for (let h = 0; h < totalHours; h++) {
    const mMu = ds.weekend ? 10 : 8.5;
    const mSig = ds.weekend ? 3.2 : 2.1;
    const mAmp = ds.weekend ? 55 : 92;
    const morning = mAmp * Math.exp(-((h - mMu) * (h - mMu)) / (2 * mSig * mSig));

    const eMu = ds.weekend ? 15.5 : 19;
    const eSig = ds.weekend ? 4.2 : 2.6;
    const eAmp = ds.weekend ? 85 : 68;
    const evening = eAmp * Math.exp(-((h - eMu) * (h - eMu)) / (2 * eSig * eSig));

    const cycDist = Math.min(h, totalHours - h);
    const nightlife = ds.nightlife
      ? 48 * Math.exp(-(cycDist * cycDist) / (2 * 2.4 * 2.4))
      : 0;

    DATA.push({
      [ANGULAR_COL]: HOUR_LABELS[h],
      [RADIAL_COL]: ds.day,
      [VALUE_COL]: Number((ds.base + morning + evening + nightlife).toFixed(1)),
    });
  }
}

const radialBins: string[] = [];
const angularBins: string[] = [];
for (const row of DATA) {
  if (!radialBins.includes(row[RADIAL_COL])) radialBins.push(row[RADIAL_COL]);
  if (!angularBins.includes(row[ANGULAR_COL])) angularBins.push(row[ANGULAR_COL]);
}

const allVals = DATA.map((r) => r[VALUE_COL]);
const minValue = Math.min(...allVals);
const maxValue = Math.max(...allVals);
const valSpan = Math.max(1e-6, maxValue - minValue);

const seqLowNum = parseInt(t.seq[0].slice(1), 16);
const seqHighNum = parseInt(t.seq[1].slice(1), 16);
const lowR = (seqLowNum >> 16) & 255;
const lowG = (seqLowNum >> 8) & 255;
const lowB = seqLowNum & 255;
const highR = (seqHighNum >> 16) & 255;
const highG = (seqHighNum >> 8) & 255;
const highB = seqHighNum & 255;

const cells = DATA.map((row) => {
  const frac = Math.max(0, Math.min(1, (row[VALUE_COL] - minValue) / valSpan));
  const r = Math.round(lowR + (highR - lowR) * frac);
  const g = Math.round(lowG + (highG - lowG) * frac);
  const b = Math.round(lowB + (highB - lowB) * frac);
  return {
    dayIdx: radialBins.indexOf(row[RADIAL_COL]),
    hourIdx: angularBins.indexOf(row[ANGULAR_COL]),
    day: row[RADIAL_COL],
    hour: row[ANGULAR_COL],
    value: row[VALUE_COL],
    fill: `rgb(${r}, ${g}, ${b})`,
  };
});

let peakRow = DATA[0];
for (const row of DATA) {
  if (row[VALUE_COL] > peakRow[VALUE_COL]) peakRow = row;
}

const anglePerBin = 360 / angularBins.length;
const TITLE = "heatmap-polar · javascript · muix · anyplot.ai";
const SUBTITLE = `Website traffic by hour (${angularBins.length}h cycle) & day (${radialBins[0]} inner → ${radialBins[radialBins.length - 1]} outer) · Peak ${Math.round(peakRow[VALUE_COL])} visits/hr (${peakRow[RADIAL_COL]} ${peakRow[ANGULAR_COL]})`;

function PolarHeatmapLayer() {
  const area = useDrawingArea();
  const cx = area.left + area.width / 2;
  const cy = area.top + area.height / 2;
  const outerR = Math.min(area.width, area.height) / 2 - LABEL_PAD;
  const innerR = outerR * RING_HOLE_RATIO;
  const ringThickness = (outerR - innerR) / radialBins.length;

  const barW = Math.min(480, area.width * 0.52);
  const barH = 18;
  const barX = cx - barW / 2;
  const barY = area.top + area.height + 54;

  const daySpokeRad = (DAY_LABEL_ANGLE * Math.PI) / 180;
  const spokeX1 = cx + innerR * Math.sin(daySpokeRad);
  const spokeY1 = cy - innerR * Math.cos(daySpokeRad);
  const spokeX2 = cx + outerR * Math.sin(daySpokeRad);
  const spokeY2 = cy - outerR * Math.cos(daySpokeRad);

  return (
    <g>
      <defs>
        <linearGradient id={GRAD_ID} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>

      <text
        x={size.width / 2}
        y={44}
        fill={t.ink}
        fontSize={22}
        fontWeight={600}
        textAnchor="middle"
      >
        {TITLE}
      </text>
      <text
        x={size.width / 2}
        y={72}
        fill={t.inkSoft}
        fontSize={15}
        textAnchor="middle"
      >
        {SUBTITLE}
      </text>

      {cells.map((cell) => {
        const r0 = innerR + cell.dayIdx * ringThickness;
        const r1 = r0 + ringThickness;
        const a0 = START_ANGLE + cell.hourIdx * anglePerBin;
        const a1 = a0 + anglePerBin;
        const rad0 = (a0 * Math.PI) / 180;
        const rad1 = (a1 * Math.PI) / 180;

        const x0 = cx + r1 * Math.sin(rad0);
        const y0 = cy - r1 * Math.cos(rad0);
        const x1 = cx + r1 * Math.sin(rad1);
        const y1 = cy - r1 * Math.cos(rad1);
        const x2 = cx + r0 * Math.sin(rad1);
        const y2 = cy - r0 * Math.cos(rad1);
        const x3 = cx + r0 * Math.sin(rad0);
        const y3 = cy - r0 * Math.cos(rad0);

        const d = `M ${x0} ${y0} A ${r1} ${r1} 0 0 1 ${x1} ${y1} L ${x2} ${y2} A ${r0} ${r0} 0 0 0 ${x3} ${y3} Z`;
        return (
          <path
            key={`${cell.day}-${cell.hour}`}
            d={d}
            fill={cell.fill}
            stroke={t.pageBg}
            strokeWidth={2}
          />
        );
      })}

      {angularBins.map((label, hIdx) => {
        if (hIdx % 3 !== 0) return null;
        const angle = START_ANGLE + (hIdx + 0.5) * anglePerBin;
        const rad = (angle * Math.PI) / 180;
        const lx = cx + (outerR + 24) * Math.sin(rad);
        const ly = cy - (outerR + 24) * Math.cos(rad);
        const dx = lx - cx;
        const dy = ly - cy;
        const anchor = dx > 12 ? "start" : dx < -12 ? "end" : "middle";
        const baseline = dy > 12 ? "hanging" : dy < -12 ? "auto" : "central";
        return (
          <text
            key={`hour-${label}`}
            x={lx}
            y={ly}
            fill={t.inkSoft}
            fontSize={15}
            fontWeight={600}
            textAnchor={anchor}
            dominantBaseline={baseline}
          >
            {label}
          </text>
        );
      })}

      <line
        x1={spokeX1}
        y1={spokeY1}
        x2={spokeX2}
        y2={spokeY2}
        stroke={t.ink}
        strokeWidth={1}
        strokeOpacity={0.35}
      />
      {radialBins.map((day, i) => {
        const r = innerR + (i + 0.5) * ringThickness;
        const lx = cx + r * Math.sin(daySpokeRad);
        const ly = cy - r * Math.cos(daySpokeRad);
        return (
          <text
            key={`day-${day}`}
            x={lx}
            y={ly}
            fill={t.ink}
            fontSize={14}
            fontWeight={700}
            textAnchor="middle"
            dominantBaseline="central"
            stroke={t.pageBg}
            strokeWidth={4}
            strokeLinejoin="round"
            paintOrder="stroke"
          >
            {day}
          </text>
        );
      })}

      {/* Horizontal Sequential Colorbar */}
      <text
        x={cx}
        y={barY - 12}
        textAnchor="middle"
        fontSize={14}
        fontWeight={600}
        fill={t.ink}
      >
        Hourly Website Traffic (visits / hr)
      </text>
      <rect
        x={barX}
        y={barY}
        width={barW}
        height={barH}
        fill={`url(#${GRAD_ID})`}
        stroke={t.grid}
        strokeWidth={1}
        rx={4}
      />
      {COLORBAR_TICKS.map((frac) => {
        const val = Math.round(minValue + frac * valSpan);
        const tx = barX + frac * barW;
        return (
          <g key={frac}>
            <line
              x1={tx}
              y1={barY + barH}
              x2={tx}
              y2={barY + barH + 5}
              stroke={t.inkSoft}
              strokeWidth={1}
            />
            <text
              x={tx}
              y={barY + barH + 21}
              textAnchor="middle"
              fontSize={14}
              fill={t.inkSoft}
            >
              {val}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  return (
    <ChartsContainer
      width={size.width}
      height={size.height}
      series={[]}
      xAxis={[{ position: "none" }]}
      yAxis={[{ position: "none" }]}
      margin={{ top: 100, bottom: 135, left: 60, right: 60 }}
      skipAnimation
    >
      <PolarHeatmapLayer />
    </ChartsContainer>
  );
}
