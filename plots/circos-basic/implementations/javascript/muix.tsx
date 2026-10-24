// anyplot.ai
// circos-basic: Circos Plot
// Library: muix 9.0.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-04
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { PiePlot } from "@mui/x-charts/PieChart";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Columns
const SOURCE = "Origin service";
const TARGET = "Destination service";
const VALUE = "API call volume (req/s)";
const SEGMENT_SIZE = "Code size (kLOC)";
const TRACK_DATA = "Test coverage (%)";

// Data
const data = [
  { [SOURCE]: "Gateway", [TARGET]: "Auth", [VALUE]: 120, [SEGMENT_SIZE]: 22, [TRACK_DATA]: 73 },
  { [SOURCE]: "Gateway", [TARGET]: "Catalog", [VALUE]: 95, [SEGMENT_SIZE]: 22, [TRACK_DATA]: 73 },
  { [SOURCE]: "Gateway", [TARGET]: "Orders", [VALUE]: 80, [SEGMENT_SIZE]: 22, [TRACK_DATA]: 73 },
  { [SOURCE]: "Gateway", [TARGET]: "Payments", [VALUE]: 60, [SEGMENT_SIZE]: 22, [TRACK_DATA]: 73 },
  { [SOURCE]: "Gateway", [TARGET]: "Inventory", [VALUE]: 55, [SEGMENT_SIZE]: 22, [TRACK_DATA]: 73 },
  { [SOURCE]: "Gateway", [TARGET]: "Notify", [VALUE]: 20, [SEGMENT_SIZE]: 22, [TRACK_DATA]: 73 },
  { [SOURCE]: "Gateway", [TARGET]: "Analytics", [VALUE]: 8, [SEGMENT_SIZE]: 22, [TRACK_DATA]: 73 },
  { [SOURCE]: "Auth", [TARGET]: "Notify", [VALUE]: 15, [SEGMENT_SIZE]: 14, [TRACK_DATA]: 88 },
  { [SOURCE]: "Catalog", [TARGET]: "Inventory", [VALUE]: 40, [SEGMENT_SIZE]: 35, [TRACK_DATA]: 65 },
  { [SOURCE]: "Catalog", [TARGET]: "Notify", [VALUE]: 10, [SEGMENT_SIZE]: 35, [TRACK_DATA]: 65 },
  { [SOURCE]: "Orders", [TARGET]: "Payments", [VALUE]: 70, [SEGMENT_SIZE]: 40, [TRACK_DATA]: 79 },
  { [SOURCE]: "Orders", [TARGET]: "Inventory", [VALUE]: 65, [SEGMENT_SIZE]: 40, [TRACK_DATA]: 79 },
  { [SOURCE]: "Orders", [TARGET]: "Notify", [VALUE]: 30, [SEGMENT_SIZE]: 40, [TRACK_DATA]: 79 },
  { [SOURCE]: "Orders", [TARGET]: "Catalog", [VALUE]: 25, [SEGMENT_SIZE]: 40, [TRACK_DATA]: 79 },
  { [SOURCE]: "Orders", [TARGET]: "Auth", [VALUE]: 14, [SEGMENT_SIZE]: 40, [TRACK_DATA]: 79 },
  { [SOURCE]: "Payments", [TARGET]: "Notify", [VALUE]: 35, [SEGMENT_SIZE]: 18, [TRACK_DATA]: 95 },
  { [SOURCE]: "Payments", [TARGET]: "Auth", [VALUE]: 18, [SEGMENT_SIZE]: 18, [TRACK_DATA]: 95 },
  { [SOURCE]: "Inventory", [TARGET]: "Notify", [VALUE]: 12, [SEGMENT_SIZE]: 28, [TRACK_DATA]: 58 },
  { [SOURCE]: "Notify", [TARGET]: "Analytics", [VALUE]: 14, [SEGMENT_SIZE]: 9, [TRACK_DATA]: 82 },
  { [SOURCE]: "Analytics", [TARGET]: "Orders", [VALUE]: 45, [SEGMENT_SIZE]: 16, [TRACK_DATA]: 69 },
  { [SOURCE]: "Analytics", [TARGET]: "Catalog", [VALUE]: 38, [SEGMENT_SIZE]: 16, [TRACK_DATA]: 69 },
  { [SOURCE]: "Analytics", [TARGET]: "Payments", [VALUE]: 28, [SEGMENT_SIZE]: 16, [TRACK_DATA]: 69 },
  { [SOURCE]: "Analytics", [TARGET]: "Inventory", [VALUE]: 22, [SEGMENT_SIZE]: 16, [TRACK_DATA]: 69 },
];

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

const moduleNames = [];
const sizeByModule = new Map();
const trackByModule = new Map();
for (const row of data) {
  if (!sizeByModule.has(row[SOURCE])) {
    sizeByModule.set(row[SOURCE], row[SEGMENT_SIZE]);
    trackByModule.set(row[SOURCE], row[TRACK_DATA]);
  }
  if (!moduleNames.includes(row[SOURCE])) {
    moduleNames.push(row[SOURCE]);
  }
}
for (const row of data) {
  if (!moduleNames.includes(row[TARGET])) {
    moduleNames.push(row[TARGET]);
  }
}

const totalSize = moduleNames.reduce((sum, name) => sum + (sizeByModule.get(name) ?? 1), 0);
const availableDeg = 360 - GAP_DEG * moduleNames.length;
let angleCursor = 0;

const segments = moduleNames.map((name, i) => {
  const codeSize = sizeByModule.get(name) ?? 1;
  const coverage = trackByModule.get(name) ?? 0;
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
const coverageValues = segments.map((s) => s.coverage);
const coverageMin = Math.min(...coverageValues);
const coverageMax = Math.max(...coverageValues);

const seqStartNum = parseInt(t.seq[0].slice(1), 16);
const seqEndNum = parseInt(t.seq[1].slice(1), 16);
const seqStartRgb = [(seqStartNum >> 16) & 255, (seqStartNum >> 8) & 255, seqStartNum & 255];
const seqEndRgb = [(seqEndNum >> 16) & 255, (seqEndNum >> 8) & 255, seqEndNum & 255];

const touchTotal = Object.fromEntries(segments.map((s) => [s.name, 0]));
for (const row of data) {
  touchTotal[row[SOURCE]] += row[VALUE];
  touchTotal[row[TARGET]] += row[VALUE];
}

const segCursor = Object.fromEntries(segments.map((s) => [s.name, s.startAngle]));
const ribbons = data.map((row) => {
  const srcName = row[SOURCE];
  const tgtName = row[TARGET];
  const val = row[VALUE];
  const segS = segmentByName[srcName];
  const segT = segmentByName[tgtName];
  const spanS = (val / touchTotal[srcName]) * (segS.endAngle - segS.startAngle);
  const spanT = (val / touchTotal[tgtName]) * (segT.endAngle - segT.startAngle);
  const sStart = segCursor[srcName];
  const sEnd = sStart + spanS;
  segCursor[srcName] = sEnd;
  const tStart = segCursor[tgtName];
  const tEnd = tStart + spanT;
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
  label: `${s.name} · ${s.codeSize} kLOC`,
  color: s.color,
}));

const trackSeriesData = segments.map((s) => {
  const ratio = (s.coverage - coverageMin) / (coverageMax - coverageMin || 1);
  const rgb = seqStartRgb.map((v, idx) => Math.round(v + (seqEndRgb[idx] - v) * ratio));
  return {
    id: `${s.name}-track`,
    value: s.codeSize,
    label: `${s.name} · ${s.coverage}%`,
    color: `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`,
  };
});

const SUBTITLE = `Ribbon width ∝ ${VALUE.toLowerCase()} · outer ring ∝ ${SEGMENT_SIZE.toLowerCase()} · inner track ∝ ${TRACK_DATA.toLowerCase()}`;

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
          <span style={{ fontWeight: 500, color: t.ink }}>{TRACK_DATA}:</span>
          <span>{coverageMin}%</span>
          <div
            style={{
              width: 88,
              height: 10,
              borderRadius: 5,
              background: `linear-gradient(to right, ${t.seq[0]}, ${t.seq[1]})`,
            }}
          />
          <span>{coverageMax}%</span>
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
          <ChartsTooltip trigger="item" />
        </ChartsContainer>
      </div>
    </div>
  );
}
