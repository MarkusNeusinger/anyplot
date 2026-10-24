// anyplot.ai
// heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 86/100 | Updated: 2026-10-24
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const size = window.ANYPLOT_SIZE;
const TITLE = "heatmap-polar · javascript · muix · anyplot.ai";
const START_ANGLE = 0;
const RING_HOLE_RATIO = 0.28;
const LABEL_PAD = 56;
const DAY_LABEL_ANGLE = 180;
const COLORBAR_TICKS = [0, 0.25, 0.5, 0.75, 1];
const GRAD_ID = "polar-heatmap-seq-grad";
const DARK_INK = "#1A1A17";
const LIGHT_INK = "#FAF8F1";

// Columns: set these to your data's column names
const HOUR = "Hour of day"; // role: angular
const DAY = "Day of week"; // role: radial
const VISITS = "Visits per hour"; // role: value

// Data: replace this block with your own records
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
  [HOUR]: string;
  [DAY]: string;
  [VISITS]: number;
};

const data: PolarHeatmapRow[] = [];
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

    data.push({
      [HOUR]: HOUR_LABELS[h],
      [DAY]: ds.day,
      [VISITS]: Number((ds.base + morning + evening + nightlife).toFixed(1)),
    });
  }
}

// Plot: reads only data and the constants above
const radialBins: string[] = [];
const angularBins: string[] = [];
for (const row of data) {
  if (!radialBins.includes(row[DAY])) radialBins.push(row[DAY]);
  if (!angularBins.includes(row[HOUR])) angularBins.push(row[HOUR]);
}

const allVals = data.map((r) => r[VISITS]);
const minValue = Math.min(...allVals);
const maxValue = Math.max(...allVals);
const valSpan = maxValue - minValue;

const seqLowNum = parseInt(t.seq[0].slice(1), 16);
const seqHighNum = parseInt(t.seq[1].slice(1), 16);
const lowR = (seqLowNum >> 16) & 255;
const lowG = (seqLowNum >> 8) & 255;
const lowB = seqLowNum & 255;
const highR = (seqHighNum >> 16) & 255;
const highG = (seqHighNum >> 8) & 255;
const highB = seqHighNum & 255;

const cells = data.map((row) => {
  const frac = (row[VISITS] - minValue) / valSpan;
  const r = Math.round(lowR + (highR - lowR) * frac);
  const g = Math.round(lowG + (highG - lowG) * frac);
  const b = Math.round(lowB + (highB - lowB) * frac);
  const lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
  return {
    dayIdx: radialBins.indexOf(row[DAY]),
    hourIdx: angularBins.indexOf(row[HOUR]),
    day: row[DAY],
    hour: row[HOUR],
    value: row[VISITS],
    fill: `rgb(${r}, ${g}, ${b})`,
    labelFill: lum > 0.54 ? DARK_INK : LIGHT_INK,
  };
});

let peakRow = data[0];
for (const row of data) {
  if (row[VISITS] > peakRow[VISITS]) peakRow = row;
}

const anglePerBin = 360 / angularBins.length;
const spokeHourIdx = Math.floor(((DAY_LABEL_ANGLE - START_ANGLE + 360) % 360) / anglePerBin);
const SUBTITLE = `${VISITS} by ${HOUR} (${angularBins.length} sectors) & ${DAY} (${radialBins[0]} inner → ${radialBins[radialBins.length - 1]} outer) · Peak ${Math.round(peakRow[VISITS])} (${peakRow[DAY]} ${peakRow[HOUR]})`;

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

  const daySpokeRad = ((START_ANGLE + (spokeHourIdx + 0.5) * anglePerBin) * Math.PI) / 180;

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

      {radialBins.map((day, i) => {
        const r = innerR + (i + 0.5) * ringThickness;
        const lx = cx + r * Math.sin(daySpokeRad);
        const ly = cy - r * Math.cos(daySpokeRad);
        const spokeCell = cells.find((c) => c.dayIdx === i && c.hourIdx === spokeHourIdx)!;
        return (
          <text
            key={`day-${day}`}
            x={lx}
            y={ly}
            fill={spokeCell.labelFill}
            fontSize={14}
            fontWeight={700}
            textAnchor="middle"
            dominantBaseline="central"
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
        {VISITS}
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
