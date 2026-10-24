// anyplot.ai
// radar-basic: Basic Radar Chart
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 89/100 | Created: 2026-07-24
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "radar-basic · javascript · muix · anyplot.ai";
const SCALE_MAX = 100;
const RINGS = [20, 40, 60, 80, 100];

// Columns: set these to your data's column names
const CATEGORY = "Skill dimension"; // role: category
const ROLE = "Player position"; // role: series
const VALUE = "Scouting score (0–100)"; // role: value

// Data: replace this block with your own records
const data = [
  { [CATEGORY]: "Speed", [ROLE]: "Guard", [VALUE]: 90 },
  { [CATEGORY]: "Shooting", [ROLE]: "Guard", [VALUE]: 84 },
  { [CATEGORY]: "Passing", [ROLE]: "Guard", [VALUE]: 92 },
  { [CATEGORY]: "Defense", [ROLE]: "Guard", [VALUE]: 68 },
  { [CATEGORY]: "Rebounding", [ROLE]: "Guard", [VALUE]: 52 },
  { [CATEGORY]: "Stamina", [ROLE]: "Guard", [VALUE]: 86 },
  { [CATEGORY]: "Speed", [ROLE]: "Forward", [VALUE]: 70 },
  { [CATEGORY]: "Shooting", [ROLE]: "Forward", [VALUE]: 76 },
  { [CATEGORY]: "Passing", [ROLE]: "Forward", [VALUE]: 62 },
  { [CATEGORY]: "Defense", [ROLE]: "Forward", [VALUE]: 85 },
  { [CATEGORY]: "Rebounding", [ROLE]: "Forward", [VALUE]: 90 },
  { [CATEGORY]: "Stamina", [ROLE]: "Forward", [VALUE]: 80 },
];

// Plot: reads only data and the constants above
const axes = Array.from(new Set(data.map((row) => String(row[CATEGORY]))));
const roleNames = Array.from(new Set(data.map((row) => String(row[ROLE]))));
const nAxes = axes.length;

const seriesList = roleNames.map((roleLabel, idx) => {
  const valueByAxis = new Map(
    data
      .filter((row) => String(row[ROLE]) === roleLabel)
      .map((row) => [String(row[CATEGORY]), Number(row[VALUE])])
  );
  return {
    label: roleLabel,
    color: t.palette[idx % t.palette.length],
    values: axes.map((axis) => Number(valueByAxis.get(axis))),
  };
});

function RadarLayer() {
  const area = useDrawingArea();
  const cx = area.left + area.width / 2;
  const cy = area.top + area.height / 2;
  const half = Math.min(area.width, area.height) / 2;
  const radius = half - 54;
  const labelRadius = half - 4;

  return (
    <g>
      {RINGS.map((level) => {
        const frac = level / SCALE_MAX;
        const ringPoints = axes
          .map((_, i) => {
            const a = (-90 + (i * 360) / nAxes) * (Math.PI / 180);
            return `${cx + frac * radius * Math.cos(a)},${cy + frac * radius * Math.sin(a)}`;
          })
          .join(" ");
        return (
          <polygon
            key={`ring-${level}`}
            points={ringPoints}
            fill="none"
            stroke={t.grid}
            strokeWidth={level === SCALE_MAX ? 2 : 1}
            strokeOpacity={level === SCALE_MAX ? 1 : 0.6}
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
              fontSize={18}
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
          x={cx + 12}
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
        const polyPoints = axes
          .map((_, i) => {
            const a = (-90 + (i * 360) / nAxes) * (Math.PI / 180);
            const frac = s.values[i] / SCALE_MAX;
            return `${cx + frac * radius * Math.cos(a)},${cy + frac * radius * Math.sin(a)}`;
          })
          .join(" ");
        return (
          <g key={`series-${s.label}`}>
            <polygon
              points={polyPoints}
              fill={s.color}
              fillOpacity={0.25}
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
                  r={6}
                  fill={s.color}
                  stroke={t.pageBg}
                  strokeWidth={2}
                />
              );
            })}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const legendGap = 240;
  const legendStart = width / 2 - ((seriesList.length - 1) * legendGap) / 2;
  const legendY = height - 44;

  return (
    <ChartsContainer
      width={width}
      height={height}
      series={[]}
      margin={{ top: 84, bottom: 84, left: 96, right: 96 }}
      skipAnimation
    >
      <text
        x={width / 2}
        y={52}
        fill={t.ink}
        fontSize={28}
        fontWeight={700}
        textAnchor="middle"
      >
        {TITLE}
      </text>
      {seriesList.map((s, i) => {
        const x = legendStart + i * legendGap;
        return (
          <g key={`legend-${s.label}`}>
            <rect x={x - 84} y={legendY - 13} width={26} height={26} rx={5} fill={s.color} />
            <text
              x={x - 50}
              y={legendY}
              fill={t.ink}
              fontSize={17}
              textAnchor="start"
              dominantBaseline="central"
            >
              {s.label}
            </text>
          </g>
        );
      })}
      <RadarLayer />
    </ChartsContainer>
  );
}
