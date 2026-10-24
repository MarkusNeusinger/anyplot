// anyplot.ai
// radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-26

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "radar-innovation-timeline · javascript · muix · anyplot.ai";
const RING_ORDER = [
  "Now (0–6 mo)",
  "Near-Term (6–18 mo)",
  "Mid-Term (18–36 mo)",
  "Future (3+ yr)",
];
const R_MAX = 640;
const SECTOR_LABEL_R = R_MAX + 40;
const LABEL_OFFSET = [28, 48, 44, 24];
const OUTER_RING_NUDGE = 12;
const X_HALF = SECTOR_LABEL_R + 100;
const Y_TOP = R_MAX + 24;
const Y_BOTTOM = -60;
const ARC_STEPS = 48;

// Columns: set these to your data's column names
const NAME = "Technology"; // role: name
const RING = "Adoption horizon"; // role: ring
const SECTOR = "Thematic sector"; // role: sector

// Data: replace this block with your own records
const data = [
  { [NAME]: "LLM Fine-Tuning", [RING]: "Now (0–6 mo)", [SECTOR]: "AI & ML" },
  { [NAME]: "AI Coding Assistants", [RING]: "Now (0–6 mo)", [SECTOR]: "AI & ML" },
  { [NAME]: "Multimodal Agents", [RING]: "Near-Term (6–18 mo)", [SECTOR]: "AI & ML" },
  { [NAME]: "RAG Pipelines", [RING]: "Near-Term (6–18 mo)", [SECTOR]: "AI & ML" },
  { [NAME]: "On-Device Inference", [RING]: "Mid-Term (18–36 mo)", [SECTOR]: "AI & ML" },
  { [NAME]: "Autonomous Coding Agents", [RING]: "Mid-Term (18–36 mo)", [SECTOR]: "AI & ML" },
  { [NAME]: "Neuromorphic Chips", [RING]: "Future (3+ yr)", [SECTOR]: "AI & ML" },
  { [NAME]: "Serverless Functions", [RING]: "Now (0–6 mo)", [SECTOR]: "Cloud Infra" },
  { [NAME]: "Edge Computing", [RING]: "Near-Term (6–18 mo)", [SECTOR]: "Cloud Infra" },
  { [NAME]: "Platform Engineering", [RING]: "Near-Term (6–18 mo)", [SECTOR]: "Cloud Infra" },
  { [NAME]: "WebAssembly Runtimes", [RING]: "Mid-Term (18–36 mo)", [SECTOR]: "Cloud Infra" },
  { [NAME]: "Confidential Computing", [RING]: "Mid-Term (18–36 mo)", [SECTOR]: "Cloud Infra" },
  { [NAME]: "Quantum-Safe Networking", [RING]: "Future (3+ yr)", [SECTOR]: "Cloud Infra" },
  { [NAME]: "Zero Trust Access", [RING]: "Now (0–6 mo)", [SECTOR]: "Security" },
  { [NAME]: "AI Threat Detection", [RING]: "Now (0–6 mo)", [SECTOR]: "Security" },
  { [NAME]: "Passwordless Auth", [RING]: "Near-Term (6–18 mo)", [SECTOR]: "Security" },
  { [NAME]: "Passkeys Everywhere", [RING]: "Near-Term (6–18 mo)", [SECTOR]: "Security" },
  { [NAME]: "Post-Quantum Crypto", [RING]: "Mid-Term (18–36 mo)", [SECTOR]: "Security" },
  { [NAME]: "Homomorphic Encryption", [RING]: "Future (3+ yr)", [SECTOR]: "Security" },
  { [NAME]: "Carbon-Aware IT", [RING]: "Now (0–6 mo)", [SECTOR]: "Green Tech" },
  { [NAME]: "Green Data Centers", [RING]: "Near-Term (6–18 mo)", [SECTOR]: "Green Tech" },
  { [NAME]: "Grid-Scale Battery Storage", [RING]: "Near-Term (6–18 mo)", [SECTOR]: "Green Tech" },
  { [NAME]: "Circular Hardware", [RING]: "Mid-Term (18–36 mo)", [SECTOR]: "Green Tech" },
  { [NAME]: "Direct Air Capture", [RING]: "Future (3+ yr)", [SECTOR]: "Green Tech" },
  { [NAME]: "Fusion Energy Pilots", [RING]: "Future (3+ yr)", [SECTOR]: "Green Tech" },
];

// Plot: reads only data and the constants above
const dataRings = Array.from(new Set(data.map((row) => String(row[RING]))));
const rings = [
  ...RING_ORDER.filter((r) => dataRings.includes(r)),
  ...dataRings.filter((r) => !RING_ORDER.includes(r)),
];
const sectors = Array.from(new Set(data.map((row) => String(row[SECTOR]))));
const ringBounds = Array.from({ length: rings.length + 1 }, (_, i) => (R_MAX * i) / rings.length);
const sectorSpan = 180 / sectors.length;

const cells = new Map();
data.forEach((row) => {
  const ringIdx = rings.indexOf(String(row[RING]));
  const sectorIdx = sectors.indexOf(String(row[SECTOR]));
  const key = `${ringIdx}-${sectorIdx}`;
  if (!cells.has(key)) cells.set(key, []);
  cells.get(key).push({ name: String(row[NAME]), ring: ringIdx, sector: sectorIdx });
});

const points = [];
cells.forEach((cell, key) => {
  const [ringIdx, sectorIdx] = key.split("-").map(Number);
  const sectorStart = 180 - sectorIdx * sectorSpan;
  const ringInner = ringBounds[ringIdx];
  const ringOuter = ringBounds[ringIdx + 1];
  const baseRadius = (ringInner + ringOuter) / 2;
  const radialJitterStep = (ringOuter - ringInner) * 0.32;
  const isOuterRing = ringIdx === rings.length - 1;
  const [pad, span] = ringIdx % 2 === 0 ? [0.2, 0.6] : [0.3, 0.4];
  const sign = sectorIdx < sectors.length / 2 ? 1 : -1;
  const n = cell.length;
  cell.forEach((item, i) => {
    const frac = n === 1 ? 0.5 : pad + span * (i / (n - 1));
    const angle = sectorStart - sectorSpan * frac - (isOuterRing ? OUTER_RING_NUDGE : 0);
    const radius = baseRadius + sign * (i - (n - 1) / 2) * radialJitterStep;
    const labelOffset = LABEL_OFFSET[ringIdx % LABEL_OFFSET.length];
    points.push({ ...item, angle, radius, labelOffset });
  });
});

function RadarDiagram() {
  const xScale = useXScale();
  const yScale = useYScale();
  const dividerAngles = Array.from({ length: sectors.length + 1 }, (_, i) => 180 - i * sectorSpan);

  return (
    <g>
      {rings.map((ringLabel, i) => {
        const rInner = ringBounds[i];
        const rOuter = ringBounds[i + 1];
        const outerArc = Array.from({ length: ARC_STEPS + 1 }, (_, k) => {
          const rad = ((180 - (180 * k) / ARC_STEPS) * Math.PI) / 180;
          return [xScale(rOuter * Math.cos(rad)), yScale(rOuter * Math.sin(rad))];
        });
        const innerArc =
          rInner === 0
            ? [[xScale(0), yScale(0)]]
            : Array.from({ length: ARC_STEPS + 1 }, (_, k) => {
                const rad = (((180 * k) / ARC_STEPS) * Math.PI) / 180;
                return [xScale(rInner * Math.cos(rad)), yScale(rInner * Math.sin(rad))];
              });
        const outerStr = outerArc.map(([x, y], idx) => `${idx === 0 ? "M" : "L"}${x},${y}`).join(" ");
        const innerStr = innerArc.map(([x, y]) => `${x},${y}`).join(" L");
        const d = `${outerStr} L${innerStr} Z`;
        return <path key={ringLabel} d={d} fill={t.ink} opacity={i % 2 === 0 ? 0.035 : 0.07} stroke="none" />;
      })}

      {ringBounds.slice(1).map((r, i) => {
        const arcStr = Array.from({ length: ARC_STEPS + 1 }, (_, k) => {
          const rad = ((180 - (180 * k) / ARC_STEPS) * Math.PI) / 180;
          const x = xScale(r * Math.cos(rad));
          const y = yScale(r * Math.sin(rad));
          return `${k === 0 ? "M" : "L"}${x},${y}`;
        }).join(" ");
        return (
          <path
            key={`ring-line-${r}`}
            d={arcStr}
            fill="none"
            stroke={i === ringBounds.length - 2 ? t.inkSoft : t.grid}
            strokeWidth={i === ringBounds.length - 2 ? 2.5 : 1.5}
          />
        );
      })}

      <line
        x1={xScale(-R_MAX)}
        y1={yScale(0)}
        x2={xScale(R_MAX)}
        y2={yScale(0)}
        stroke={t.inkSoft}
        strokeWidth={2.5}
      />

      {dividerAngles.map((angle) => {
        const rad = (angle * Math.PI) / 180;
        return (
          <line
            key={`div-${angle}`}
            x1={xScale(0)}
            y1={yScale(0)}
            x2={xScale(R_MAX * Math.cos(rad))}
            y2={yScale(R_MAX * Math.sin(rad))}
            stroke={t.grid}
            strokeWidth={1.5}
          />
        );
      })}

      {ringBounds.slice(1).map((r, i) => {
        const x = xScale(0);
        const y = yScale(r);
        return (
          <text
            key={`ring-label-${rings[i]}`}
            x={x + 10}
            y={y - 6}
            fontSize={13}
            fontWeight={600}
            fill={t.inkSoft}
            textAnchor="start"
            dominantBaseline="middle"
          >
            {rings[i]}
          </text>
        );
      })}

      {sectors.map((sectorLabel, i) => {
        const sectorStart = 180 - i * sectorSpan;
        const mid = sectorStart - sectorSpan / 2;
        const rad = (mid * Math.PI) / 180;
        const x = xScale(SECTOR_LABEL_R * Math.cos(rad));
        const y = yScale(SECTOR_LABEL_R * Math.sin(rad));
        const cos = Math.cos(rad);
        const anchor = cos > 0.25 ? "start" : cos < -0.25 ? "end" : "middle";
        return (
          <text
            key={`sector-label-${sectorLabel}`}
            x={x}
            y={y}
            fontSize={18}
            fontWeight={700}
            fill={t.ink}
            textAnchor={anchor}
            dominantBaseline="middle"
          >
            {sectorLabel}
          </text>
        );
      })}

      {sectors.map((sectorLabel, i) => {
        const slot = (2 * X_HALF) / sectors.length;
        const cx = xScale(-X_HALF + slot * (i + 0.5));
        const cy = yScale(-32);
        return (
          <g key={`legend-${sectorLabel}`}>
            <circle cx={cx - 55} cy={cy} r={9} fill={t.palette[i % t.palette.length]} stroke={t.pageBg} strokeWidth={2} />
            <text x={cx - 40} y={cy} fontSize={14} fill={t.ink} textAnchor="start" dominantBaseline="middle">
              {sectorLabel}
            </text>
          </g>
        );
      })}

      {points.map((p) => {
        const rad = (p.angle * Math.PI) / 180;
        const mx = xScale(p.radius * Math.cos(rad));
        const my = yScale(p.radius * Math.sin(rad));
        const lx = xScale((p.radius + p.labelOffset) * Math.cos(rad));
        const ly = yScale((p.radius + p.labelOffset) * Math.sin(rad));
        const cos = Math.cos(rad);
        const anchor = cos > 0.2 ? "start" : cos < -0.2 ? "end" : "middle";
        return (
          <g key={p.name}>
            <circle cx={mx} cy={my} r={9} fill={t.palette[p.sector % t.palette.length]} stroke={t.pageBg} strokeWidth={2.2} />
            <text x={lx} y={ly} fontSize={13} fill={t.ink} textAnchor={anchor} dominantBaseline="middle">
              {p.name}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const titleHeight = 64;
  const chartWidth = 2 * X_HALF;
  const chartHeight = Y_TOP - Y_BOTTOM;

  return (
    <Box
      sx={{
        width: size.width,
        height: size.height,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Box sx={{ height: titleHeight, display: "flex", alignItems: "center" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </Typography>
      </Box>
      <ChartsContainer
        width={chartWidth}
        height={chartHeight}
        series={[]}
        xAxis={[{ min: -X_HALF, max: X_HALF, scaleType: "linear", domainLimit: "strict", position: "none" }]}
        yAxis={[{ min: Y_BOTTOM, max: Y_TOP, scaleType: "linear", domainLimit: "strict", position: "none" }]}
        margin={{ top: 0, bottom: 0, left: 0, right: 0 }}
        skipAnimation
      >
        <RadarDiagram />
      </ChartsContainer>
    </Box>
  );
}
