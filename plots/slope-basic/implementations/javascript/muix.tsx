// anyplot.ai
// slope-basic: Basic Slope Chart (Slopegraph)
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 88/100 | Created: 2026-07-25
//# anyplot-orientation: landscape
// anyplot.ai
// slope-basic: Basic Slope Chart (Slopegraph)
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-07-25

import { LineChart } from "@mui/x-charts/LineChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// --- Data: employee satisfaction score (0-100) by department, 2023 vs 2025 -
const PERIODS = ["2023", "2025"];
const departments = [
  { name: "Customer Support", start: 52, end: 46 },
  { name: "Sales", start: 57, end: 51 },
  { name: "Design", start: 47, end: 55 },
  { name: "Marketing", start: 65, end: 60 },
  { name: "Finance", start: 61, end: 68 },
  { name: "Product", start: 79, end: 72 },
  { name: "HR", start: 70, end: 77 },
  { name: "Operations", start: 74, end: 82 },
  { name: "Engineering", start: 83, end: 90 },
];

// Direction semantics — profit/up/gain -> brand green, loss/down -> matte red
const IMPROVED = t.palette[0];
const DECLINED = t.palette[4];

const series = departments.map((d) => ({
  id: d.name,
  data: [d.start, d.end],
  label: d.name,
  color: d.end >= d.start ? IMPROVED : DECLINED,
  showMark: true,
  curve: "linear",
}));

// Direct endpoint labels — the classic slopegraph identification convention:
// department + value on the left column, value only on the right (the name
// already anchors the line, so the right side stays uncluttered).
function EndpointLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  const xStart = xScale("2023");
  const xEnd = xScale("2025");

  return (
    <g fontFamily="'Roboto','Helvetica Neue',Arial,sans-serif" fontSize={14}>
      {departments.map((d) => (
        <g key={d.name}>
          <text
            x={xStart - 16}
            y={yScale(d.start)}
            textAnchor="end"
            dominantBaseline="middle"
            fill={t.ink}
          >
            {d.name} · {d.start}
          </text>
          <text
            x={xEnd + 16}
            y={yScale(d.end)}
            textAnchor="start"
            dominantBaseline="middle"
            fill={t.ink}
          >
            {d.end}
          </text>
        </g>
      ))}
    </g>
  );
}

const TITLE = "Employee Satisfaction by Department · slope-basic · javascript · muix · anyplot.ai";
const TITLE_FONT_SIZE = Math.round(22 * Math.min(1, 67 / TITLE.length));
const TITLE_H = 70;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        boxSizing: "border-box",
        fontFamily: "'Roboto','Helvetica Neue',Arial,sans-serif",
      }}
    >
      <div
        style={{
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          paddingLeft: 28,
          paddingRight: 28,
        }}
      >
        <span style={{ color: t.ink, fontSize: TITLE_FONT_SIZE, fontWeight: 500, letterSpacing: 0.3 }}>
          {TITLE}
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 22, height: 3, background: IMPROVED }} />
            <span style={{ color: t.inkSoft, fontSize: 15 }}>Improved</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 22, height: 3, background: DECLINED }} />
            <span style={{ color: t.inkSoft, fontSize: 15 }}>Declined</span>
          </div>
        </div>
      </div>

      <LineChart
        width={width}
        height={height - TITLE_H}
        skipAnimation
        margin={{ left: 210, right: 90, top: 50, bottom: 30 }}
        xAxis={[
          {
            scaleType: "point",
            data: PERIODS,
            position: "top",
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: { fontSize: 16, fontWeight: 500, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 35,
            max: 100,
            disableLine: true,
            disableTicks: true,
            tickLabelInterval: () => false,
          },
        ]}
        series={series}
        slotProps={{ legend: { hidden: true } }}
        sx={{
          "& .MuiLineElement-root": { strokeWidth: 3 },
          "& .MuiMarkElement-root": { strokeWidth: 2 },
        }}
      >
        <EndpointLabels />
      </LineChart>
    </div>
  );
}
