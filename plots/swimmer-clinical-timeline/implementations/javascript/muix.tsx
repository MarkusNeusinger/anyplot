// anyplot.ai
// swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: 94/100 | Created: 2026-08-24
import { BarChart } from "@mui/x-charts/BarChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const X_PAD_SHARE = 0.2; // room right of the longest bar for its arrow and the callout
const MARKER_SHARE = 0.42; // event marker radius as a share of the bar band
const MARKER_MAX = 13; // largest event marker radius (px)
const FOCUS_COUNT = 2; // the callout brackets this many longest-running patients
// Event symbols as unit paths around (0, 0), scaled to the marker radius
const STAR = `${Array.from({ length: 10 }, (_, i) => {
  const r = i % 2 === 0 ? 1.15 : 0.48;
  const a = (Math.PI / 5) * i - Math.PI / 2;
  return `${i === 0 ? "M" : "L"} ${(r * Math.cos(a)).toFixed(3)} ${(r * Math.sin(a)).toFixed(3)}`;
}).join(" ")} Z`;
const SHAPE_PATH = {
  triangle: "M 0 -1 L 1 0.85 L -1 0.85 Z",
  star: STAR,
  diamond: "M 0 -1 L 1 0 L 0 1 L -1 0 Z",
  circle: "M -0.72 0 A 0.72 0.72 0 1 0 0.72 0 A 0.72 0.72 0 1 0 -0.72 0 Z",
  arrow: "M 0 -1.05 L 1.8 0 L 0 1.05 Z",
  square: "M -0.75 -0.75 H 0.75 V 0.75 H -0.75 Z",
};
// Clinical event vocabulary: a symbol per type, and the colours fixed by meaning
// (progression in the matte-red loss anchor, adverse events in the warning amber,
// the ongoing arrow in ink); other types take the palette positions left over
const EVENT_SHAPE = {
  "Partial response": "triangle",
  "Complete response": "star",
  "Progressive disease": "diamond",
  "Adverse event": "circle",
  Ongoing: "arrow",
};
const EVENT_COLOR = { "Progressive disease": t.palette[4], "Adverse event": t.amber, Ongoing: t.ink };
const ONGOING = "Ongoing"; // the event type that marks a patient still on treatment at data cutoff
const HEADER_H = 128;

// Columns: set these to your data's column names
const PATIENT = "Patient"; // role: patient_id
const ARM = "Treatment arm"; // role: group
const DURATION = "Time on study (weeks)"; // role: duration
const EVENT_TIME = "Event time (weeks)"; // role: events
const EVENT_TYPE = "Event"; // role: events

// Data: replace this block with your own records, one object per row
// Simulated Phase II oncology trial: one row per clinical event of each patient
const data = [
  { [PATIENT]: "PT-001", [ARM]: "Targeted Therapy", [DURATION]: 32, [EVENT_TIME]: 9, [EVENT_TYPE]: "Partial response" },
  { [PATIENT]: "PT-001", [ARM]: "Targeted Therapy", [DURATION]: 32, [EVENT_TIME]: 32, [EVENT_TYPE]: "Progressive disease" },
  { [PATIENT]: "PT-002", [ARM]: "Targeted Therapy", [DURATION]: 47, [EVENT_TIME]: 11, [EVENT_TYPE]: "Partial response" },
  { [PATIENT]: "PT-002", [ARM]: "Targeted Therapy", [DURATION]: 47, [EVENT_TIME]: 25, [EVENT_TYPE]: "Complete response" },
  { [PATIENT]: "PT-002", [ARM]: "Targeted Therapy", [DURATION]: 47, [EVENT_TIME]: 47, [EVENT_TYPE]: "Progressive disease" },
  { [PATIENT]: "PT-003", [ARM]: "Chemotherapy", [DURATION]: 26, [EVENT_TIME]: 26, [EVENT_TYPE]: "Progressive disease" },
  { [PATIENT]: "PT-004", [ARM]: "Targeted Therapy", [DURATION]: 54, [EVENT_TIME]: 12, [EVENT_TYPE]: "Partial response" },
  { [PATIENT]: "PT-004", [ARM]: "Targeted Therapy", [DURATION]: 54, [EVENT_TIME]: 34, [EVENT_TYPE]: "Complete response" },
  { [PATIENT]: "PT-004", [ARM]: "Targeted Therapy", [DURATION]: 54, [EVENT_TIME]: 54, [EVENT_TYPE]: "Ongoing" },
  { [PATIENT]: "PT-005", [ARM]: "Targeted Therapy", [DURATION]: 36, [EVENT_TIME]: 36, [EVENT_TYPE]: "Progressive disease" },
  { [PATIENT]: "PT-006", [ARM]: "Chemotherapy", [DURATION]: 22, [EVENT_TIME]: 10, [EVENT_TYPE]: "Adverse event" },
  { [PATIENT]: "PT-006", [ARM]: "Chemotherapy", [DURATION]: 22, [EVENT_TIME]: 22, [EVENT_TYPE]: "Progressive disease" },
  { [PATIENT]: "PT-007", [ARM]: "Chemotherapy", [DURATION]: 14, [EVENT_TIME]: 14, [EVENT_TYPE]: "Progressive disease" },
  { [PATIENT]: "PT-008", [ARM]: "Targeted Therapy", [DURATION]: 41, [EVENT_TIME]: 10, [EVENT_TYPE]: "Partial response" },
  { [PATIENT]: "PT-008", [ARM]: "Targeted Therapy", [DURATION]: 41, [EVENT_TIME]: 41, [EVENT_TYPE]: "Progressive disease" },
  { [PATIENT]: "PT-009", [ARM]: "Targeted Therapy", [DURATION]: 28, [EVENT_TIME]: 14, [EVENT_TYPE]: "Partial response" },
  { [PATIENT]: "PT-009", [ARM]: "Targeted Therapy", [DURATION]: 28, [EVENT_TIME]: 28, [EVENT_TYPE]: "Ongoing" },
  { [PATIENT]: "PT-010", [ARM]: "Chemotherapy", [DURATION]: 18, [EVENT_TIME]: 18, [EVENT_TYPE]: "Progressive disease" },
  { [PATIENT]: "PT-011", [ARM]: "Targeted Therapy", [DURATION]: 58, [EVENT_TIME]: 9, [EVENT_TYPE]: "Partial response" },
  { [PATIENT]: "PT-011", [ARM]: "Targeted Therapy", [DURATION]: 58, [EVENT_TIME]: 27, [EVENT_TYPE]: "Complete response" },
  { [PATIENT]: "PT-011", [ARM]: "Targeted Therapy", [DURATION]: 58, [EVENT_TIME]: 58, [EVENT_TYPE]: "Ongoing" },
  { [PATIENT]: "PT-012", [ARM]: "Targeted Therapy", [DURATION]: 16, [EVENT_TIME]: 8, [EVENT_TYPE]: "Adverse event" },
  { [PATIENT]: "PT-012", [ARM]: "Targeted Therapy", [DURATION]: 16, [EVENT_TIME]: 16, [EVENT_TYPE]: "Progressive disease" },
  { [PATIENT]: "PT-013", [ARM]: "Chemotherapy", [DURATION]: 39, [EVENT_TIME]: 20, [EVENT_TYPE]: "Adverse event" },
  { [PATIENT]: "PT-013", [ARM]: "Chemotherapy", [DURATION]: 39, [EVENT_TIME]: 22, [EVENT_TYPE]: "Partial response" },
  { [PATIENT]: "PT-013", [ARM]: "Chemotherapy", [DURATION]: 39, [EVENT_TIME]: 39, [EVENT_TYPE]: "Ongoing" },
  { [PATIENT]: "PT-014", [ARM]: "Targeted Therapy", [DURATION]: 12, [EVENT_TIME]: 12, [EVENT_TYPE]: "Progressive disease" },
  { [PATIENT]: "PT-015", [ARM]: "Targeted Therapy", [DURATION]: 20, [EVENT_TIME]: 20, [EVENT_TYPE]: "Progressive disease" },
  { [PATIENT]: "PT-016", [ARM]: "Chemotherapy", [DURATION]: 34, [EVENT_TIME]: 18, [EVENT_TYPE]: "Partial response" },
  { [PATIENT]: "PT-016", [ARM]: "Chemotherapy", [DURATION]: 34, [EVENT_TIME]: 34, [EVENT_TYPE]: "Ongoing" },
  { [PATIENT]: "PT-017", [ARM]: "Chemotherapy", [DURATION]: 50, [EVENT_TIME]: 14, [EVENT_TYPE]: "Partial response" },
  { [PATIENT]: "PT-017", [ARM]: "Chemotherapy", [DURATION]: 50, [EVENT_TIME]: 40, [EVENT_TYPE]: "Adverse event" },
  { [PATIENT]: "PT-017", [ARM]: "Chemotherapy", [DURATION]: 50, [EVENT_TIME]: 50, [EVENT_TYPE]: "Ongoing" },
  { [PATIENT]: "PT-018", [ARM]: "Targeted Therapy", [DURATION]: 24, [EVENT_TIME]: 8, [EVENT_TYPE]: "Partial response" },
  { [PATIENT]: "PT-018", [ARM]: "Targeted Therapy", [DURATION]: 24, [EVENT_TIME]: 24, [EVENT_TYPE]: "Progressive disease" },
  { [PATIENT]: "PT-019", [ARM]: "Chemotherapy", [DURATION]: 44, [EVENT_TIME]: 16, [EVENT_TYPE]: "Partial response" },
  { [PATIENT]: "PT-019", [ARM]: "Chemotherapy", [DURATION]: 44, [EVENT_TIME]: 44, [EVENT_TYPE]: "Ongoing" },
  { [PATIENT]: "PT-020", [ARM]: "Chemotherapy", [DURATION]: 30, [EVENT_TIME]: 12, [EVENT_TYPE]: "Adverse event" },
  { [PATIENT]: "PT-020", [ARM]: "Chemotherapy", [DURATION]: 30, [EVENT_TIME]: 30, [EVENT_TYPE]: "Progressive disease" },
];

// Plot: reads only data and the constants above
// One bar per patient, longest time on study at the top
const patients = [...new Set(data.map((d) => d[PATIENT]))]
  .map((id) => {
    const rows = data.filter((d) => d[PATIENT] === id);
    return {
      id,
      arm: rows[0][ARM],
      duration: Math.max(...rows.map((d) => d[DURATION])),
      events: rows.filter((d) => d[EVENT_TYPE] != null && Number.isFinite(d[EVENT_TIME])),
    };
  })
  .sort((a, b) => b.duration - a.duration);
const arms = [...new Set(data.map((d) => d[ARM]))];
const armColor = Object.fromEntries(arms.map((arm, i) => [arm, t.palette[i]]));

// Event types: the known vocabulary in clinical order, then any other type in order of appearance
const presentTypes = [...new Set(data.map((d) => d[EVENT_TYPE]).filter((v) => v != null))];
const eventTypes = [
  ...Object.keys(EVENT_SHAPE).filter((type) => presentTypes.includes(type)),
  ...presentTypes.filter((type) => !(type in EVENT_SHAPE)),
];
const takenColors = [...Object.values(armColor), ...Object.values(EVENT_COLOR)];
const freeColors = t.palette.filter((c) => !takenColors.includes(c));
const freeTypes = eventTypes.filter((type) => !(type in EVENT_COLOR));
const eventColor = Object.fromEntries(
  eventTypes.map((type) => [type, EVENT_COLOR[type] ?? freeColors[freeTypes.indexOf(type)]]),
);
const eventPath = Object.fromEntries(eventTypes.map((type) => [type, SHAPE_PATH[EVENT_SHAPE[type] ?? "square"]]));

const durationMax = Math.max(...patients.map((p) => p.duration));
const timeUnit = DURATION.match(/\(([^)]+)\)/)?.[1] ?? "";
const focusIds = patients.slice(0, FOCUS_COUNT).map((p) => p.id);
const legendItems = [
  ...arms.map((arm) => ({ key: `arm-${arm}`, label: arm, color: armColor[arm], path: null })),
  ...eventTypes.map((type) => ({ key: `event-${type}`, label: type, color: eventColor[type], path: eventPath[type] })),
];

const TITLE = "swimmer-clinical-timeline · javascript · muix · anyplot.ai";
const SUBTITLE = `${patients.length} patients across ${arms.length} ${ARM.toLowerCase()}s · sorted by ${DURATION.toLowerCase()} · arrow = ${ONGOING.toLowerCase()} at data cutoff`;

function SwimmerLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const band = yScale.bandwidth();
  const r = Math.min(band * MARKER_SHARE, MARKER_MAX);
  const focusRows = focusIds.map((id) => (yScale(id) ?? 0) + band / 2);
  const focusX = xScale(Math.max(...patients.slice(0, FOCUS_COUNT).map((p) => p.duration))) + r * 2.6;

  return (
    <g>
      {patients.map((p) =>
        p.events.map((e, i) => (
          <path
            key={`${p.id}-${i}`}
            d={eventPath[e[EVENT_TYPE]]}
            transform={`translate(${xScale(e[EVENT_TIME])} ${(yScale(p.id) ?? 0) + band / 2}) scale(${r})`}
            fill={eventColor[e[EVENT_TYPE]]}
            stroke={e[EVENT_TYPE] === ONGOING ? "none" : t.pageBg}
            strokeWidth={1.5}
            vectorEffect="non-scaling-stroke"
          />
        )),
      )}
      <path
        d={`M ${focusX} ${Math.min(...focusRows)} h 6 V ${Math.max(...focusRows)} h -6`}
        fill="none"
        stroke={t.inkSoft}
        strokeWidth={1.5}
      />
      <text
        x={focusX + 14}
        y={(Math.min(...focusRows) + Math.max(...focusRows)) / 2}
        fontSize={14}
        fill={t.inkSoft}
        dominantBaseline="central"
      >
        Longest on study
      </text>
    </g>
  );
}

export default function Chart() {
  const { width: W, height: H } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg }}>
      <Box sx={{ height: HEADER_H, pt: "18px", px: "56px", boxSizing: "border-box" }}>
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600, lineHeight: 1.25 }}>{TITLE}</Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 15, mt: "4px" }}>{SUBTITLE}</Typography>
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: "22px", mt: "14px", alignItems: "center" }}>
          {legendItems.map((item) => (
            <Box key={item.key} sx={{ display: "flex", alignItems: "center", gap: "7px" }}>
              <svg width={26} height={20} viewBox="-11 -10 26 20">
                {item.path ? (
                  <path d={item.path} transform="scale(7.5)" fill={item.color} />
                ) : (
                  <rect x={-10} y={-6} width={20} height={12} rx={2} fill={item.color} />
                )}
              </svg>
              <Typography sx={{ color: t.inkSoft, fontSize: 15 }}>{item.label}</Typography>
            </Box>
          ))}
        </Box>
      </Box>

      <BarChart
        width={W}
        height={H - HEADER_H}
        layout="horizontal"
        skipAnimation
        hideLegend
        borderRadius={3}
        grid={{ vertical: true }}
        margin={{ top: 16, right: 40, bottom: 12, left: 24 }}
        series={[
          {
            id: "duration",
            label: DURATION,
            data: patients.map((p) => p.duration),
            valueFormatter: (v) => `${v} ${timeUnit}`,
          },
        ]}
        xAxis={[
          {
            scaleType: "linear",
            min: 0,
            max: durationMax * (1 + X_PAD_SHARE),
            label: DURATION,
            height: 60,
            tickNumber: 8,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: patients.map((p) => p.id),
            colorMap: { type: "ordinal", values: patients.map((p) => p.id), colors: patients.map((p) => armColor[p.arm]) },
            label: PATIENT,
            width: 96,
            categoryGapRatio: 0.32,
            disableTicks: true,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <SwimmerLayer />
      </BarChart>
    </Box>
  );
}
