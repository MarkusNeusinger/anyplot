// anyplot.ai
// rose-basic: Basic Rose Chart
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: pending | Created: 2026-07-25
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { PiePlot } from "@mui/x-charts/PieChart";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const RING_COUNT = 4; // radial gridlines between the centre and the outer ring
const NICE_STEPS = [1, 2, 2.5, 5, 10]; // ring steps per power of ten
const OUTER_SHARE = 0.88; // outer ring as a share of the available radius, the rest holds the labels
const LABEL_GAP = 32; // px between the outer ring and the category labels

// Columns: set these to your data's column names
const MONTH = "Month"; // role: category
const RAINFALL = "Average rainfall (mm)"; // role: value

// Data: replace this block with your own records, one object per row, in circular order
const data = [
  { [MONTH]: "Jan", [RAINFALL]: 88 },
  { [MONTH]: "Feb", [RAINFALL]: 65 },
  { [MONTH]: "Mar", [RAINFALL]: 70 },
  { [MONTH]: "Apr", [RAINFALL]: 52 },
  { [MONTH]: "May", [RAINFALL]: 48 },
  { [MONTH]: "Jun", [RAINFALL]: 32 },
  { [MONTH]: "Jul", [RAINFALL]: 22 },
  { [MONTH]: "Aug", [RAINFALL]: 28 },
  { [MONTH]: "Sep", [RAINFALL]: 45 },
  { [MONTH]: "Oct", [RAINFALL]: 78 },
  { [MONTH]: "Nov", [RAINFALL]: 95 },
  { [MONTH]: "Dec", [RAINFALL]: 92 },
];

// Plot: reads only data and the constants above
const n = data.length;
const sliceDeg = 360 / n;
const values = data.map((d) => d[RAINFALL]);
const total = values.reduce((sum, v) => sum + v, 0);

// Radial scale from zero to a round outer ring that clears the largest value
const rawStep = Math.max(...values) / RING_COUNT;
const magnitude = 10 ** Math.floor(Math.log10(rawStep));
const ringStep = NICE_STEPS.find((s) => s * magnitude >= rawStep) * magnitude;
const outerValue = ringStep * RING_COUNT;
const rings = Array.from({ length: RING_COUNT }, (_, k) => (k + 1) * ringStep);

// Wedge i is centred on i * sliceDeg, clockwise from 12 o'clock (the pie's own convention)
const wedges = data.map((d, i) => ({
  type: "pie" as const,
  id: `wedge-${i}`,
  data: [{ id: i, value: d[RAINFALL], label: d[MONTH], color: t.palette[0] }],
  startAngle: i * sliceDeg - sliceDeg / 2,
  endAngle: i * sliceDeg + sliceDeg / 2,
  innerRadius: 0,
  outerRadius: `${(d[RAINFALL] / outerValue) * OUTER_SHARE * 100}%`,
}));

// Ring values run along the spoke of the shortest wedge, where they cover the least data
const ringLabelRad = (values.indexOf(Math.min(...values)) * sliceDeg * Math.PI) / 180;

const TITLE = "rose-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `Radius: ${RAINFALL} by ${MONTH.toLowerCase()} · total ${total} · gridlines every ${ringStep}`;
const HEADER_HEIGHT = 84;

function RoseGrid() {
  const area = useDrawingArea();
  const cx = area.left + area.width / 2;
  const cy = area.top + area.height / 2;
  const radius = (Math.min(area.width, area.height) / 2) * OUTER_SHARE;
  return (
    <g>
      {rings.map((ring) => (
        <circle
          key={`ring-${ring}`}
          cx={cx}
          cy={cy}
          r={(ring / outerValue) * radius}
          fill="none"
          stroke={t.grid}
          strokeWidth={ring === outerValue ? 1.5 : 1}
        />
      ))}
      {data.map((d, i) => {
        const rad = (i * sliceDeg * Math.PI) / 180;
        return (
          <line
            key={`spoke-${d[MONTH]}`}
            x1={cx}
            y1={cy}
            x2={cx + radius * Math.sin(rad)}
            y2={cy - radius * Math.cos(rad)}
            stroke={t.grid}
            strokeWidth={1}
          />
        );
      })}
    </g>
  );
}

function RoseLabels() {
  const area = useDrawingArea();
  const cx = area.left + area.width / 2;
  const cy = area.top + area.height / 2;
  const radius = (Math.min(area.width, area.height) / 2) * OUTER_SHARE;
  return (
    <g>
      {data.map((d, i) => {
        const rad = (i * sliceDeg * Math.PI) / 180;
        const sin = Math.sin(rad);
        const cos = Math.cos(rad);
        return (
          <text
            key={`label-${d[MONTH]}`}
            x={cx + (radius + LABEL_GAP) * sin}
            y={cy - (radius + LABEL_GAP) * cos}
            textAnchor={sin > 0.2 ? "start" : sin < -0.2 ? "end" : "middle"}
            dominantBaseline={cos > 0.4 ? "auto" : cos < -0.4 ? "hanging" : "central"}
            fontSize={16}
            fontWeight={500}
            fill={t.ink}
          >
            {d[MONTH]}
          </text>
        );
      })}
      {rings.map((ring) => {
        const r = (ring / outerValue) * radius;
        const x = cx + r * Math.sin(ringLabelRad);
        const y = cy - r * Math.cos(ringLabelRad);
        const text = `${ring}`;
        const pillWidth = text.length * 9 + 12;
        return (
          <g key={`ring-label-${ring}`}>
            <rect x={x - pillWidth / 2} y={y - 11} width={pillWidth} height={22} rx={4} fill={t.pageBg} />
            <text x={x} y={y} textAnchor="middle" dominantBaseline="central" fontSize={14} fill={t.inkSoft}>
              {text}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_HEIGHT,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={height - HEADER_HEIGHT}
        series={wedges}
        margin={{ top: 8, right: 8, bottom: 24, left: 8 }}
        skipAnimation
        sx={{ "& .MuiPieChart-arc": { stroke: t.pageBg, strokeWidth: 2 } }}
      >
        <RoseGrid />
        <PiePlot skipAnimation />
        <RoseLabels />
      </ChartsContainer>
    </div>
  );
}
