// anyplot.ai
// radar-multi: Multi-Series Radar Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-08-20
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "radar-multi · javascript · muix · anyplot.ai";
const SCALE_MAX = 100;
const RINGS = [20, 40, 60, 80, 100];

// Columns: set these to your data's column names
const CATEGORY = "Evaluation metric"; // role: category
const SERIES = "Headphone model"; // role: series
const VALUE = "Score (0–100)"; // role: value

// Data: replace this block with your own records
const data = [
  { [CATEGORY]: "Sound Quality", [SERIES]: "AudioMax Pro", [VALUE]: 92 },
  { [CATEGORY]: "Noise Cancelling", [SERIES]: "AudioMax Pro", [VALUE]: 88 },
  { [CATEGORY]: "Battery Life", [SERIES]: "AudioMax Pro", [VALUE]: 75 },
  { [CATEGORY]: "Comfort", [SERIES]: "AudioMax Pro", [VALUE]: 80 },
  { [CATEGORY]: "Build Quality", [SERIES]: "AudioMax Pro", [VALUE]: 85 },
  { [CATEGORY]: "Value", [SERIES]: "AudioMax Pro", [VALUE]: 60 },
  { [CATEGORY]: "Connectivity", [SERIES]: "AudioMax Pro", [VALUE]: 90 },
  { [CATEGORY]: "Sound Quality", [SERIES]: "SoundWave Elite", [VALUE]: 78 },
  { [CATEGORY]: "Noise Cancelling", [SERIES]: "SoundWave Elite", [VALUE]: 95 },
  { [CATEGORY]: "Battery Life", [SERIES]: "SoundWave Elite", [VALUE]: 90 },
  { [CATEGORY]: "Comfort", [SERIES]: "SoundWave Elite", [VALUE]: 85 },
  { [CATEGORY]: "Build Quality", [SERIES]: "SoundWave Elite", [VALUE]: 70 },
  { [CATEGORY]: "Value", [SERIES]: "SoundWave Elite", [VALUE]: 55 },
  { [CATEGORY]: "Connectivity", [SERIES]: "SoundWave Elite", [VALUE]: 82 },
  { [CATEGORY]: "Sound Quality", [SERIES]: "EchoBudget", [VALUE]: 65 },
  { [CATEGORY]: "Noise Cancelling", [SERIES]: "EchoBudget", [VALUE]: 60 },
  { [CATEGORY]: "Battery Life", [SERIES]: "EchoBudget", [VALUE]: 82 },
  { [CATEGORY]: "Comfort", [SERIES]: "EchoBudget", [VALUE]: 70 },
  { [CATEGORY]: "Build Quality", [SERIES]: "EchoBudget", [VALUE]: 60 },
  { [CATEGORY]: "Value", [SERIES]: "EchoBudget", [VALUE]: 92 },
  { [CATEGORY]: "Connectivity", [SERIES]: "EchoBudget", [VALUE]: 75 },
];

// Plot: reads only data and the constants above
const axes = Array.from(new Set(data.map((row) => String(row[CATEGORY]))));
const seriesNames = Array.from(new Set(data.map((row) => String(row[SERIES]))));
const nAxes = axes.length;

const seriesList = seriesNames.map((seriesLabel, idx) => {
  const valueByAxis = new Map(
    data
      .filter((row) => String(row[SERIES]) === seriesLabel)
      .map((row) => [String(row[CATEGORY]), Number(row[VALUE])])
  );
  const values = axes.map((axis) => Number(valueByAxis.get(axis)));
  const meanVal = values.reduce((acc, v) => acc + v, 0) / values.length;
  return {
    label: seriesLabel,
    color: t.palette[idx % t.palette.length],
    values,
    meanVal,
  };
});

const specialistSeries = [...seriesList].sort((a, b) => a.meanVal - b.meanVal)[0];
let standoutIdx = 0;
for (let i = 1; i < nAxes; i += 1) {
  if (specialistSeries.values[i] > specialistSeries.values[standoutIdx]) {
    standoutIdx = i;
  }
}

function RadarLayer() {
  const area = useDrawingArea();
  const cx = area.left + area.width / 2;
  const cy = area.top + area.height / 2;
  const half = Math.min(area.width, area.height) / 2;
  const radius = half - 58;
  const labelRadius = half - 6;

  const calloutAngle = (-90 + (standoutIdx * 360) / nAxes) * (Math.PI / 180);
  const calloutFrac = specialistSeries.values[standoutIdx] / SCALE_MAX;
  const calloutX = cx + calloutFrac * radius * Math.cos(calloutAngle);
  const calloutY = cy + calloutFrac * radius * Math.sin(calloutAngle);
  const anchorR = radius * 0.32;
  const anchorX = cx + anchorR * Math.cos(calloutAngle);
  const anchorY = cy + anchorR * Math.sin(calloutAngle);

  return (
    <g>
      {[...RINGS].reverse().map((level, idx) => {
        const frac = level / SCALE_MAX;
        const pts = axes
          .map((_, i) => {
            const a = (-90 + (i * 360) / nAxes) * (Math.PI / 180);
            return `${cx + frac * radius * Math.cos(a)},${cy + frac * radius * Math.sin(a)}`;
          })
          .join(" ");
        return (
          <polygon
            key={`band-${level}`}
            points={pts}
            fill={idx % 2 === 0 ? t.grid : t.pageBg}
            fillOpacity={idx % 2 === 0 ? 0.07 : 1}
          />
        );
      })}

      {RINGS.map((level) => {
        const frac = level / SCALE_MAX;
        const pts = axes
          .map((_, i) => {
            const a = (-90 + (i * 360) / nAxes) * (Math.PI / 180);
            return `${cx + frac * radius * Math.cos(a)},${cy + frac * radius * Math.sin(a)}`;
          })
          .join(" ");
        return (
          <polygon
            key={`ring-${level}`}
            points={pts}
            fill="none"
            stroke={t.grid}
            strokeWidth={level === SCALE_MAX ? 2 : 1}
            strokeOpacity={0.35 + 0.65 * frac}
          />
        );
      })}

      {axes.map((label, i) => {
        const a = (-90 + (i * 360) / nAxes) * (Math.PI / 180);
        const ox = cx + radius * Math.cos(a);
        const oy = cy + radius * Math.sin(a);
        const lx = cx + labelRadius * Math.cos(a);
        const ly = cy + labelRadius * Math.sin(a);
        const cos = Math.cos(a);
        const anchor = cos > 0.15 ? "start" : cos < -0.15 ? "end" : "middle";
        const sin = Math.sin(a);
        const baseline = sin > 0.5 ? "hanging" : sin < -0.5 ? "auto" : "central";
        return (
          <g key={`axis-${label}`}>
            <line x1={cx} y1={cy} x2={ox} y2={oy} stroke={t.grid} strokeWidth={1.25} />
            <text
              x={lx}
              y={ly}
              fill={t.ink}
              fontSize={16}
              fontWeight={600}
              textAnchor={anchor}
              dominantBaseline={baseline}
            >
              {label}
            </text>
          </g>
        );
      })}

      {RINGS.map((level) => (
        <text
          key={`tick-${level}`}
          x={cx + 10}
          y={cy - (level / SCALE_MAX) * radius}
          fill={t.inkSoft}
          fontSize={15}
          textAnchor="start"
          dominantBaseline="central"
        >
          {level}
        </text>
      ))}

      {seriesList.map((s) => {
        const polyPts = axes
          .map((_, i) => {
            const a = (-90 + (i * 360) / nAxes) * (Math.PI / 180);
            const frac = s.values[i] / SCALE_MAX;
            return `${cx + frac * radius * Math.cos(a)},${cy + frac * radius * Math.sin(a)}`;
          })
          .join(" ");
        return (
          <g key={`series-${s.label}`}>
            <polygon
              points={polyPts}
              fill={s.color}
              fillOpacity={0.22}
              stroke={s.color}
              strokeWidth={3}
              strokeLinejoin="round"
            />
            {axes.map((_, i) => {
              const a = (-90 + (i * 360) / nAxes) * (Math.PI / 180);
              const frac = s.values[i] / SCALE_MAX;
              const px = cx + frac * radius * Math.cos(a);
              const py = cy + frac * radius * Math.sin(a);
              return (
                <circle
                  key={`pt-${s.label}-${i}`}
                  cx={px}
                  cy={py}
                  r={5.5}
                  fill={s.color}
                  stroke={t.pageBg}
                  strokeWidth={2}
                />
              );
            })}
          </g>
        );
      })}

      <g>
        <line
          x1={anchorX}
          y1={anchorY}
          x2={calloutX}
          y2={calloutY}
          stroke={specialistSeries.color}
          strokeWidth={1.5}
          strokeDasharray="4 3"
        />
        <circle cx={calloutX} cy={calloutY} r={10} fill="none" stroke={specialistSeries.color} strokeWidth={2} />
        <rect
          x={anchorX - 100}
          y={anchorY - 32}
          width={200}
          height={46}
          rx={8}
          fill={t.pageBg}
          fillOpacity={0.88}
          stroke={t.grid}
          strokeWidth={1}
        />
        <text x={anchorX} y={anchorY - 13} fill={t.ink} fontSize={15} fontWeight={700} textAnchor="middle">
          {`Best on ${axes[standoutIdx]}`}
        </text>
        <text x={anchorX} y={anchorY + 8} fill={t.inkSoft} fontSize={13} textAnchor="middle">
          {`${specialistSeries.label} trails elsewhere`}
        </text>
      </g>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const legendGap = 320;
  const legendStart = width / 2 - ((seriesList.length - 1) * legendGap) / 2;
  const legendY = height - 40;

  return (
    <ChartsContainer
      width={width}
      height={height}
      series={[]}
      margin={{ top: 88, bottom: 88, left: 96, right: 96 }}
      skipAnimation
    >
      <text x={width / 2} y={50} fill={t.ink} fontSize={26} fontWeight={700} textAnchor="middle">
        {TITLE}
      </text>
      {seriesList.map((s, i) => {
        const x = legendStart + i * legendGap;
        return (
          <g key={`legend-${s.label}`}>
            <rect x={x - 96} y={legendY - 13} width={24} height={24} rx={5} fill={s.color} />
            <text x={x - 64} y={legendY - 1} fill={t.ink} fontSize={16} textAnchor="start" dominantBaseline="central">
              {s.label}
            </text>
          </g>
        );
      })}
      <RadarLayer />
    </ChartsContainer>
  );
}
