// anyplot.ai
// circos-basic: Circos Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-04
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { PiePlot } from "@mui/x-charts/PieChart";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "circos-basic · javascript · muix · anyplot.ai";
const GAP_DEG = 3;
const PIE_START_ANGLE = -GAP_DEG / 2;
const PIE_END_ANGLE = 360 - GAP_DEG / 2;
const SEG_OUTER_RATIO = 0.84;
const SEG_THICK_RATIO = 0.07;
const TRACK_GAP_RATIO = 0.02;
const TRACK_THICK_RATIO = 0.11;
const RIBBON_GAP_RATIO = 0.015;
const LABEL_GAP_RATIO = 0.045;
const HEADER_H = 128;

// Columns: set these to your data's column names
const SOURCE = "Origin service"; // role: source
const TARGET = "Destination service"; // role: target
const FLOW = "API call volume (req/s)"; // role: value
const SEGMENT = "Service"; // role: extra
const CODE_SIZE = "Code size (kLOC)"; // role: segment_size
const COVERAGE = "Test coverage (%)"; // role: track_data

// Data: replace this block with your own records
const segmentsData = [
  { [SEGMENT]: "Gateway", [CODE_SIZE]: 22, [COVERAGE]: 73 },
  { [SEGMENT]: "Auth", [CODE_SIZE]: 14, [COVERAGE]: 88 },
  { [SEGMENT]: "Catalog", [CODE_SIZE]: 35, [COVERAGE]: 65 },
  { [SEGMENT]: "Orders", [CODE_SIZE]: 40, [COVERAGE]: 79 },
  { [SEGMENT]: "Payments", [CODE_SIZE]: 18, [COVERAGE]: 95 },
  { [SEGMENT]: "Inventory", [CODE_SIZE]: 28, [COVERAGE]: 58 },
  { [SEGMENT]: "Notify", [CODE_SIZE]: 9, [COVERAGE]: 82 },
  { [SEGMENT]: "Analytics", [CODE_SIZE]: 16, [COVERAGE]: 69 },
];

const data = [
  { [SOURCE]: "Gateway", [TARGET]: "Auth", [FLOW]: 120 },
  { [SOURCE]: "Gateway", [TARGET]: "Catalog", [FLOW]: 95 },
  { [SOURCE]: "Gateway", [TARGET]: "Orders", [FLOW]: 80 },
  { [SOURCE]: "Gateway", [TARGET]: "Payments", [FLOW]: 60 },
  { [SOURCE]: "Gateway", [TARGET]: "Inventory", [FLOW]: 55 },
  { [SOURCE]: "Gateway", [TARGET]: "Notify", [FLOW]: 20 },
  { [SOURCE]: "Gateway", [TARGET]: "Analytics", [FLOW]: 8 },
  { [SOURCE]: "Auth", [TARGET]: "Notify", [FLOW]: 15 },
  { [SOURCE]: "Catalog", [TARGET]: "Inventory", [FLOW]: 40 },
  { [SOURCE]: "Catalog", [TARGET]: "Notify", [FLOW]: 10 },
  { [SOURCE]: "Orders", [TARGET]: "Payments", [FLOW]: 70 },
  { [SOURCE]: "Orders", [TARGET]: "Inventory", [FLOW]: 65 },
  { [SOURCE]: "Orders", [TARGET]: "Notify", [FLOW]: 30 },
  { [SOURCE]: "Orders", [TARGET]: "Catalog", [FLOW]: 25 },
  { [SOURCE]: "Orders", [TARGET]: "Auth", [FLOW]: 14 },
  { [SOURCE]: "Payments", [TARGET]: "Notify", [FLOW]: 35 },
  { [SOURCE]: "Payments", [TARGET]: "Auth", [FLOW]: 18 },
  { [SOURCE]: "Inventory", [TARGET]: "Notify", [FLOW]: 12 },
  { [SOURCE]: "Notify", [TARGET]: "Analytics", [FLOW]: 14 },
  { [SOURCE]: "Analytics", [TARGET]: "Orders", [FLOW]: 45 },
  { [SOURCE]: "Analytics", [TARGET]: "Catalog", [FLOW]: 38 },
  { [SOURCE]: "Analytics", [TARGET]: "Payments", [FLOW]: 28 },
  { [SOURCE]: "Analytics", [TARGET]: "Inventory", [FLOW]: 22 },
];

// Plot: reads only data and the constants above
const SIZE_UNIT = CODE_SIZE.match(/\(([^)]+)\)/)?.[1] ?? "";
const sizeUnitSuffix = SIZE_UNIT ? ` ${SIZE_UNIT}` : "";

const activeSegments = segmentsData.filter(
  (row) => row[CODE_SIZE] != null && Number.isFinite(Number(row[CODE_SIZE])) && Number(row[CODE_SIZE]) > 0,
);
const totalSize = activeSegments.reduce((sum, row) => sum + Number(row[CODE_SIZE]), 0);
const availableDeg = 360 - GAP_DEG * activeSegments.length;
let angleCursor = 0;

const segments = activeSegments.map((row, i) => {
  const name = String(row[SEGMENT]);
  const codeSize = Number(row[CODE_SIZE]);
  const coverage = row[COVERAGE] != null && Number.isFinite(Number(row[COVERAGE])) ? Number(row[COVERAGE]) : null;
  const span = (codeSize / totalSize) * availableDeg;
  const startAngle = angleCursor;
  const endAngle = angleCursor + span;
  angleCursor = endAngle + GAP_DEG;
  return {
    name,
    startAngle,
    endAngle,
    midAngle: (startAngle + endAngle) / 2,
    color: t.palette[i],
    codeSize,
    coverage,
  };
});

const segmentByName = Object.fromEntries(segments.map((s) => [s.name, s]));
const coverageValues = segments.map((s) => s.coverage).filter((v): v is number => v != null);
const coverageMin = Math.min(...coverageValues);
const coverageMax = Math.max(...coverageValues);

const seqStartNum = parseInt(t.seq[0].slice(1), 16);
const seqEndNum = parseInt(t.seq[1].slice(1), 16);
const seqStartRgb = [(seqStartNum >> 16) & 255, (seqStartNum >> 8) & 255, seqStartNum & 255];
const seqEndRgb = [(seqEndNum >> 16) & 255, (seqEndNum >> 8) & 255, seqEndNum & 255];

const touchTotal = Object.fromEntries(segments.map((s) => [s.name, 0]));
for (const row of data) {
  const src = String(row[SOURCE]);
  const tgt = String(row[TARGET]);
  const val = Number(row[FLOW]);
  if (src in touchTotal && tgt in touchTotal && Number.isFinite(val)) {
    touchTotal[src] += val;
    touchTotal[tgt] += val;
  }
}

const degPerUnit = Math.min(
  ...segments
    .filter((s) => touchTotal[s.name] > 0)
    .map((s) => (s.endAngle - s.startAngle) / touchTotal[s.name]),
);

const segCursor = Object.fromEntries(
  segments.map((s) => {
    const usedSpan = touchTotal[s.name] * degPerUnit;
    const padOffset = (s.endAngle - s.startAngle - usedSpan) / 2;
    return [s.name, s.startAngle + padOffset];
  }),
);

const ribbons = data
  .filter((row) => String(row[SOURCE]) in segmentByName && String(row[TARGET]) in segmentByName)
  .map((row) => {
    const srcName = String(row[SOURCE]);
    const tgtName = String(row[TARGET]);
    const val = Number(row[FLOW]);
    const segS = segmentByName[srcName];
    const span = val * degPerUnit;
    const sStart = segCursor[srcName];
    const sEnd = sStart + span;
    segCursor[srcName] = sEnd;
    const tStart = segCursor[tgtName];
    const tEnd = tStart + span;
    segCursor[tgtName] = tEnd;
    return {
      source: srcName,
      target: tgtName,
      value: val,
      sStart,
      sEnd,
      tStart,
      tEnd,
      color: segS.color,
    };
  });

const segmentSeriesData = segments.map((s) => ({
  id: s.name,
  value: s.codeSize,
  label: `${s.name} · ${s.codeSize}${sizeUnitSuffix}`,
  color: s.color,
}));

const trackSeriesData = segments.map((s) => {
  if (s.coverage == null) {
    return {
      id: `${s.name}-track`,
      value: s.codeSize,
      label: s.name,
      color: "transparent",
    };
  }
  const ratio = (s.coverage - coverageMin) / (coverageMax - coverageMin);
  const rgb = seqStartRgb.map((v, idx) => Math.round(v + (seqEndRgb[idx] - v) * ratio));
  return {
    id: `${s.name}-track`,
    value: s.codeSize,
    label: `${s.name} · ${s.coverage}`,
    color: `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`,
  };
});

const SUBTITLE = `Ribbon width ∝ ${FLOW} · outer ring ∝ ${CODE_SIZE} · inner track ∝ ${COVERAGE}`;

function CircosOverlay() {
  const { left, top, width, height } = useDrawingArea();
  const cx = left + width / 2;
  const cy = top + height / 2;
  const half = Math.min(width, height) / 2;
  const rSegOuter = half * SEG_OUTER_RATIO;
  const rSegInner = rSegOuter - half * SEG_THICK_RATIO;
  const rTrackOuter = rSegInner - half * TRACK_GAP_RATIO;
  const rTrackBase = rTrackOuter - half * TRACK_THICK_RATIO;
  const rRibbon = rTrackBase - half * RIBBON_GAP_RATIO;
  const rLabel = rSegOuter + half * LABEL_GAP_RATIO;

  return (
    <g>
      {ribbons.map((rb, i) => {
        const s1 = (rb.sStart * Math.PI) / 180;
        const s2 = (rb.sEnd * Math.PI) / 180;
        const t1 = (rb.tStart * Math.PI) / 180;
        const t2 = (rb.tEnd * Math.PI) / 180;
        const p1x = cx + rRibbon * Math.sin(s1);
        const p1y = cy - rRibbon * Math.cos(s1);
        const p2x = cx + rRibbon * Math.sin(s2);
        const p2y = cy - rRibbon * Math.cos(s2);
        const p3x = cx + rRibbon * Math.sin(t1);
        const p3y = cy - rRibbon * Math.cos(t1);
        const p4x = cx + rRibbon * Math.sin(t2);
        const p4y = cy - rRibbon * Math.cos(t2);
        const largeS = rb.sEnd - rb.sStart > 180 ? 1 : 0;
        const largeT = rb.tEnd - rb.tStart > 180 ? 1 : 0;
        const d = [
          `M ${p1x} ${p1y}`,
          `A ${rRibbon} ${rRibbon} 0 ${largeS} 1 ${p2x} ${p2y}`,
          `Q ${cx} ${cy} ${p3x} ${p3y}`,
          `A ${rRibbon} ${rRibbon} 0 ${largeT} 1 ${p4x} ${p4y}`,
          `Q ${cx} ${cy} ${p1x} ${p1y}`,
          "Z",
        ].join(" ");
        return (
          <path
            key={`ribbon-${i}`}
            d={d}
            fill={rb.color}
            fillOpacity={0.45}
            stroke={rb.color}
            strokeOpacity={0.55}
            strokeWidth={1}
          />
        );
      })}
      {segments.map((s) => {
        const rad = (s.midAngle * Math.PI) / 180;
        const px = cx + rLabel * Math.sin(rad);
        const py = cy - rLabel * Math.cos(rad);
        const rotate = s.midAngle < 180 ? s.midAngle - 90 : s.midAngle + 90;
        const anchor = s.midAngle < 180 ? "start" : "end";
        return (
          <text
            key={`label-${s.name}`}
            x={px}
            y={py}
            textAnchor={anchor}
            dominantBaseline="middle"
            fontSize={15}
            fontWeight={600}
            fill={t.ink}
            transform={`rotate(${rotate}, ${px}, ${py})`}
          >
            {s.name}
          </text>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const svgSize = Math.round(Math.min(width, height - HEADER_H) * 0.84);
  const half = svgSize / 2;
  const rSegOuter = half * SEG_OUTER_RATIO;
  const rSegInner = rSegOuter - half * SEG_THICK_RATIO;
  const rTrackOuter = rSegInner - half * TRACK_GAP_RATIO;
  const rTrackBase = rTrackOuter - half * TRACK_THICK_RATIO;

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <div style={{ padding: "18px 28px 0 28px" }}>
        <div
          style={{
            fontSize: 22,
            fontWeight: 600,
            color: t.ink,
            lineHeight: 1.3,
          }}
        >
          {TITLE}
        </div>
        <div
          style={{
            fontSize: 15,
            color: t.inkSoft,
            marginTop: 4,
            lineHeight: 1.35,
          }}
        >
          {SUBTITLE}
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginTop: 10,
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          <span style={{ fontWeight: 500, color: t.ink }}>{COVERAGE}:</span>
          <span>{coverageMin}</span>
          <div
            style={{
              width: 88,
              height: 10,
              borderRadius: 5,
              background: `linear-gradient(to right, ${t.seq[0]}, ${t.seq[1]})`,
            }}
          />
          <span>{coverageMax}</span>
        </div>
      </div>
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <ChartsContainer
          width={svgSize}
          height={svgSize}
          margin={{ top: 0, bottom: 0, left: 0, right: 0 }}
          xAxis={[{ position: "none" }]}
          yAxis={[{ position: "none" }]}
          colors={t.palette}
          sx={{ overflow: "visible" }}
          skipAnimation
          series={[
            {
              type: "pie",
              id: "segments",
              data: segmentSeriesData,
              innerRadius: rSegInner,
              outerRadius: rSegOuter,
              startAngle: PIE_START_ANGLE,
              endAngle: PIE_END_ANGLE,
              paddingAngle: GAP_DEG,
            },
            {
              type: "pie",
              id: "track",
              data: trackSeriesData,
              innerRadius: rTrackBase,
              outerRadius: rTrackOuter,
              startAngle: PIE_START_ANGLE,
              endAngle: PIE_END_ANGLE,
              paddingAngle: GAP_DEG,
            },
          ]}
        >
          <PiePlot skipAnimation />
          <CircosOverlay />
        </ChartsContainer>
      </div>
    </div>
  );
}
