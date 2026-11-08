// anyplot.ai
// radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-26

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SPREAD = 0.28; // several items in one cell sit between this share and its complement of the ring band
const ARC_STEPS = 96; // segments per half-circle arc
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 44;
const HEADER_PX = 52; // room above the outer ring for the sector headers
const BASE_PX = 44; // room below the baseline for the ring names
const SIDE_PX = 150; // room beside the half circle for the outermost sector headers
const MARKER_R = 8;
const LABEL_PX = 14; // item label font size
const CHAR_PX = 7.6; // approximate width of one label character at LABEL_PX
const HEADER_CHAR_PX = 10.6; // approximate width of one sector-header character at 18 px bold

// Columns: set these to your data's column names
const NAME = "Technology"; // role: name
const HORIZON = "Adoption horizon"; // role: ring
const SECTOR = "Domain"; // role: sector

// Data: replace this block with your own records, one object per row
// Strategic technology planning: 25 technologies by expected adoption horizon (listed nearest first)
// across four domains; most cells hold one or two items, as real radars cluster
const data = [
  { [NAME]: "LLM Fine-Tuning", [HORIZON]: "Now (0–6 mo)", [SECTOR]: "AI & ML" },
  { [NAME]: "AI Coding Assistants", [HORIZON]: "Now (0–6 mo)", [SECTOR]: "AI & ML" },
  { [NAME]: "Multimodal Agents", [HORIZON]: "Near-Term (6–18 mo)", [SECTOR]: "AI & ML" },
  { [NAME]: "RAG Pipelines", [HORIZON]: "Near-Term (6–18 mo)", [SECTOR]: "AI & ML" },
  { [NAME]: "On-Device Inference", [HORIZON]: "Mid-Term (18–36 mo)", [SECTOR]: "AI & ML" },
  { [NAME]: "Autonomous Coding Agents", [HORIZON]: "Mid-Term (18–36 mo)", [SECTOR]: "AI & ML" },
  { [NAME]: "Neuromorphic Chips", [HORIZON]: "Future (3+ yr)", [SECTOR]: "AI & ML" },
  { [NAME]: "Serverless Functions", [HORIZON]: "Now (0–6 mo)", [SECTOR]: "Cloud Infra" },
  { [NAME]: "Edge Computing", [HORIZON]: "Near-Term (6–18 mo)", [SECTOR]: "Cloud Infra" },
  { [NAME]: "Platform Engineering", [HORIZON]: "Near-Term (6–18 mo)", [SECTOR]: "Cloud Infra" },
  { [NAME]: "WebAssembly Runtimes", [HORIZON]: "Mid-Term (18–36 mo)", [SECTOR]: "Cloud Infra" },
  { [NAME]: "Confidential Computing", [HORIZON]: "Mid-Term (18–36 mo)", [SECTOR]: "Cloud Infra" },
  { [NAME]: "Quantum-Safe Networking", [HORIZON]: "Future (3+ yr)", [SECTOR]: "Cloud Infra" },
  { [NAME]: "Zero Trust Access", [HORIZON]: "Now (0–6 mo)", [SECTOR]: "Security" },
  { [NAME]: "AI Threat Detection", [HORIZON]: "Now (0–6 mo)", [SECTOR]: "Security" },
  { [NAME]: "Passwordless Auth", [HORIZON]: "Near-Term (6–18 mo)", [SECTOR]: "Security" },
  { [NAME]: "Passkeys Everywhere", [HORIZON]: "Near-Term (6–18 mo)", [SECTOR]: "Security" },
  { [NAME]: "Post-Quantum Crypto", [HORIZON]: "Mid-Term (18–36 mo)", [SECTOR]: "Security" },
  { [NAME]: "Homomorphic Encryption", [HORIZON]: "Future (3+ yr)", [SECTOR]: "Security" },
  { [NAME]: "Carbon-Aware IT", [HORIZON]: "Now (0–6 mo)", [SECTOR]: "Green Tech" },
  { [NAME]: "Green Data Centers", [HORIZON]: "Near-Term (6–18 mo)", [SECTOR]: "Green Tech" },
  { [NAME]: "Grid-Scale Battery Storage", [HORIZON]: "Near-Term (6–18 mo)", [SECTOR]: "Green Tech" },
  { [NAME]: "Circular Hardware", [HORIZON]: "Mid-Term (18–36 mo)", [SECTOR]: "Green Tech" },
  { [NAME]: "Direct Air Capture", [HORIZON]: "Future (3+ yr)", [SECTOR]: "Green Tech" },
  { [NAME]: "Fusion Energy Pilots", [HORIZON]: "Future (3+ yr)", [SECTOR]: "Green Tech" },
];

// Plot: reads only data and the constants above
// Rings in order of first appearance, nearest horizon innermost; sectors split the half circle evenly
const rings = [...new Set(data.map((d) => d[HORIZON]))];
const sectors = [...new Set(data.map((d) => d[SECTOR]))];
const sectorSpan = Math.PI / sectors.length;

// Canvas geometry in px: the half circle sits on its baseline, one px-per-ring scale on both axes
const { width, height } = window.ANYPLOT_SIZE;
const svgH = height - TITLE_H - SUBTITLE_H - LEGEND_H;
const radiusPx = Math.min(svgH - HEADER_PX - BASE_PX, width / 2 - SIDE_PX);
const unit = radiusPx / rings.length;
const below = BASE_PX + (svgH - HEADER_PX - BASE_PX - radiusPx) / 2; // px from the bottom edge to the baseline
const cx = width / 2;
const cy = svgH - below;

// Inside each (ring, sector) cell, n items fan out over the sector at (k + 1) / (n + 1) of its
// angle and step outward across the ring band, so no item leaves its own cell. Positions are in
// ring units: ring i spans radius i to i + 1, angle pi (left) to 0 (right).
const cellSize = new Map();
data.forEach((d) => {
  const key = `${rings.indexOf(d[HORIZON])}:${sectors.indexOf(d[SECTOR])}`;
  cellSize.set(key, (cellSize.get(key) ?? 0) + 1);
});
const cellSeen = new Map();
const items = data.map((d) => {
  const ring = rings.indexOf(d[HORIZON]);
  const sector = sectors.indexOf(d[SECTOR]);
  const key = `${ring}:${sector}`;
  const n = cellSize.get(key);
  const k = cellSeen.get(key) ?? 0;
  cellSeen.set(key, k + 1);
  const angle = Math.PI - (sector + (k + 1) / (n + 1)) * sectorSpan;
  const radius = ring + (n === 1 ? 0.5 : SPREAD + ((1 - 2 * SPREAD) * k) / (n - 1));
  const x = radius * Math.cos(angle);
  const y = radius * Math.sin(angle);
  return { name: d[NAME], sector, angle, x, y, px: cx + x * unit, py: cy - y * unit };
});

// Sector headers just outside the outer ring, at each sector's middle angle
const headers = sectors.map((sector, i) => {
  const mid = Math.PI - (i + 0.5) * sectorSpan;
  const cos = Math.cos(mid);
  const anchor = cos > 0.25 ? "start" : cos < -0.25 ? "end" : "middle";
  return { sector, x: cx + (radiusPx + 26) * cos, y: cy - (radiusPx + 26) * Math.sin(mid), anchor };
});

// Label placement: markers stay on their positions; each label takes the first of eight slots around
// its marker (outer side first) that is free of markers, headers, ring names and earlier labels
const obstacles = [
  ...items.map((it, i) => ({ owner: i, box: [it.px - MARKER_R - 3, it.py - MARKER_R - 3, it.px + MARKER_R + 3, it.py + MARKER_R + 3] })),
  ...headers.map((h) => {
    const w = h.sector.length * HEADER_CHAR_PX;
    const x0 = h.anchor === "end" ? h.x - w : h.anchor === "middle" ? h.x - w / 2 : h.x;
    return { owner: -1, box: [x0, h.y - 13, x0 + w, h.y + 13] };
  }),
  { owner: -1, box: [0, cy + 6, width, svgH] }, // the ring names below the baseline
];
const labels = items.map((it, i) => {
  const w = it.name.length * CHAR_PX;
  const out = Math.cos(it.angle) >= 0 ? 1 : -1;
  const gap = MARKER_R + 6;
  const slots = [
    [out * gap, 0, out],
    [0, -gap - 4, 0],
    [0, gap + 4, 0],
    [out * gap * 0.8, -gap, out],
    [out * gap * 0.8, gap, out],
    [-out * gap, 0, -out],
    [-out * gap * 0.8, -gap, -out],
    [-out * gap * 0.8, gap, -out],
  ].map(([dx, dy, side]) => {
    const x0 = side > 0 ? it.px + dx : side < 0 ? it.px + dx - w : it.px - w / 2;
    const box = [x0, it.py + dy - LABEL_PX / 2 - 2, x0 + w, it.py + dy + LABEL_PX / 2 + 2];
    const clash = obstacles
      .filter((o) => o.owner !== i)
      .reduce((sum, { box: o }) => sum + Math.max(0, Math.min(box[2], o[2]) - Math.max(box[0], o[0])) * Math.max(0, Math.min(box[3], o[3]) - Math.max(box[1], o[1])), 0);
    return { dx, dy, anchor: side > 0 ? "start" : side < 0 ? "end" : "middle", box, clash };
  });
  const best = slots.find((s) => s.clash === 0) ?? slots.reduce((a, b) => (b.clash < a.clash ? b : a));
  obstacles.push({ owner: -1, box: best.box });
  return best;
});

const series = sectors.map((s, i) => ({
  type: "scatter",
  id: `sector-${i}`,
  label: s,
  color: t.palette[i],
  markerSize: MARKER_R,
  labelMarkType: "circle",
  data: items.filter((it) => it.sector === i).map((it) => ({ x: it.x, y: it.y, id: it.name })),
}));

const TITLE = "radar-innovation-timeline · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} items · ${rings.length} rings, nearest horizon at the center · ${sectors.length} sectors`;

function RadarFrame() {
  const xScale = useXScale();
  const yScale = useYScale();
  const ox = xScale(0);
  const oy = yScale(0);
  const at = (r, a) => [ox + r * Math.cos(a), oy - r * Math.sin(a)];
  // Each boundary arc as points from the left end (angle pi) to the right end (angle 0)
  const arcs = Array.from({ length: rings.length + 1 }, (_, i) =>
    Array.from({ length: ARC_STEPS + 1 }, (_, s) => at(i * unit, Math.PI - (Math.PI * s) / ARC_STEPS)),
  );

  return (
    <g>
      {rings.map((ring, i) => (
        <path
          key={`band-${ring}`}
          d={`M${[...arcs[i + 1], ...[...arcs[i]].reverse()].map((p) => p.join(",")).join(" L")} Z`}
          fill={t.inkSoft}
          fillOpacity={i % 2 === 0 ? 0.05 : 0.1}
        />
      ))}
      {rings.map((ring, i) => (
        <path
          key={`ring-${ring}`}
          d={`M${arcs[i + 1].map((p) => p.join(",")).join(" L")}`}
          fill="none"
          stroke={i === rings.length - 1 ? t.inkSoft : t.grid}
          strokeWidth={i === rings.length - 1 ? 2 : 1.5}
        />
      ))}
      {Array.from({ length: sectors.length + 1 }, (_, i) => {
        const [x, y] = at(radiusPx, Math.PI - i * sectorSpan);
        return <line key={`spoke-${i}`} x1={ox} y1={oy} x2={x} y2={y} stroke={t.grid} strokeWidth={1.5} />;
      })}
      <line x1={ox - radiusPx} y1={oy} x2={ox + radiusPx} y2={oy} stroke={t.inkSoft} strokeWidth={2} />
      {rings.map((ring, i) =>
        [-1, 1].map((side) => (
          <text
            key={`ring-name-${ring}-${side}`}
            x={ox + side * (i + 0.5) * unit}
            y={oy + 26}
            fontSize={14}
            fontWeight={600}
            fill={t.inkSoft}
            textAnchor="middle"
          >
            {ring}
          </text>
        )),
      )}
      {headers.map((h) => (
        <text key={`header-${h.sector}`} x={h.x} y={h.y} fontSize={18} fontWeight={700} fill={t.ink} textAnchor={h.anchor} dominantBaseline="middle">
          {h.sector}
        </text>
      ))}
      {items.map((it, i) => (
        <text
          key={`label-${it.name}`}
          x={xScale(it.x) + labels[i].dx}
          y={yScale(it.y) + labels[i].dy}
          fontSize={LABEL_PX}
          fill={t.ink}
          textAnchor={labels[i].anchor}
          dominantBaseline="central"
          stroke={t.pageBg}
          strokeWidth={4}
          paintOrder="stroke"
        >
          {it.name}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <ChartsDataProvider
        width={width}
        height={svgH}
        skipAnimation
        margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
        series={series}
        xAxis={[{ scaleType: "linear", min: -cx / unit, max: (width - cx) / unit, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: -below / unit, max: (svgH - below) / unit, position: "none" }]}
      >
        <ChartsWrapper legendPosition={{ vertical: "bottom", horizontal: "center" }} legendDirection="horizontal">
          <ChartsLegend sx={{ fontSize: 16, color: t.ink, height: LEGEND_H, alignItems: "center" }} />
          <ChartsSurface sx={{ "& .MuiScatterChart-marker": { stroke: t.pageBg, strokeWidth: 2 } }}>
            <RadarFrame />
            <ScatterPlot />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
