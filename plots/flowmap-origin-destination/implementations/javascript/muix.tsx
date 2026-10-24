// anyplot.ai
// flowmap-origin-destination: Origin-Destination Flow Map
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02
import { useState } from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "flowmap-origin-destination · javascript · muix · anyplot.ai";
const LON_AXIS_LABEL = "Longitude (°)";
const LAT_AXIS_LABEL = "Latitude (°)";
const LEGEND_NOTE = "Node size = total throughput · arrowheads indicate flow direction";

const LON_PAD_SHARE = 0.09;
const LAT_PAD_SHARE = 0.14;
const HUB_TOP_SHARE = 0.3;
const MIN_ARC_WIDTH = 2.2;
const MAX_ARC_WIDTH = 9.2;
const MIN_NODE_R = 7;
const MAX_NODE_R = 22;

const MARGIN = { top: 88, right: 48, bottom: 108, left: 20 };
const X_AXIS_HEIGHT = 50;
const Y_AXIS_WIDTH = 68;

const CONTINENT_OUTLINES = [
  "-165,68 -135,58 -125,48 -118,33 -105,20 -95,15 -80,25 -75,35 -65,45 -70,50 -95,62 -130,70 -165,68",
  "-80,10 -70,-5 -70,-20 -68,-35 -70,-50 -65,-45 -50,-25 -35,-8 -50,2 -65,8 -80,10",
  "-10,43 0,36 15,38 25,40 30,45 40,55 25,60 5,50 -5,52 -10,43",
  "-17,20 -10,5 5,5 10,-5 15,-30 25,-33 35,-15 42,10 35,32 10,37 -17,20",
  "30,45 40,15 55,25 70,20 80,10 95,15 105,10 115,22 130,35 140,40 135,50 100,55 70,55 45,45 30,45",
];

// Columns: set these to your data's column names
const ORIGIN_NAME = "Origin"; // role: origin_name
const ORIGIN_LAT = "Origin latitude (°)"; // role: origin_lat
const ORIGIN_LON = "Origin longitude (°)"; // role: origin_lon
const DEST_NAME = "Destination"; // role: dest_name
const DEST_LAT = "Destination latitude (°)"; // role: dest_lat
const DEST_LON = "Destination longitude (°)"; // role: dest_lon
const FLOW = "Container flow (thousand TEU/year)"; // role: flow

// Data: replace this block with your own records
const data: Record<string, string | number>[] = [
  { [ORIGIN_NAME]: "Shanghai", [ORIGIN_LAT]: 31.23, [ORIGIN_LON]: 121.47, [DEST_NAME]: "Los Angeles", [DEST_LAT]: 33.73, [DEST_LON]: -118.26, [FLOW]: 1450 },
  { [ORIGIN_NAME]: "Shanghai", [ORIGIN_LAT]: 31.23, [ORIGIN_LON]: 121.47, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 980 },
  { [ORIGIN_NAME]: "Shanghai", [ORIGIN_LAT]: 31.23, [ORIGIN_LON]: 121.47, [DEST_NAME]: "Singapore", [DEST_LAT]: 1.29, [DEST_LON]: 103.85, [FLOW]: 620 },
  { [ORIGIN_NAME]: "Singapore", [ORIGIN_LAT]: 1.29, [ORIGIN_LON]: 103.85, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 710 },
  { [ORIGIN_NAME]: "Singapore", [ORIGIN_LAT]: 1.29, [ORIGIN_LON]: 103.85, [DEST_NAME]: "Jebel Ali", [DEST_LAT]: 25.01, [DEST_LON]: 55.06, [FLOW]: 540 },
  { [ORIGIN_NAME]: "Singapore", [ORIGIN_LAT]: 1.29, [ORIGIN_LON]: 103.85, [DEST_NAME]: "Mumbai", [DEST_LAT]: 18.95, [DEST_LON]: 72.95, [FLOW]: 460 },
  { [ORIGIN_NAME]: "Hong Kong", [ORIGIN_LAT]: 22.32, [ORIGIN_LON]: 114.17, [DEST_NAME]: "Los Angeles", [DEST_LAT]: 33.73, [DEST_LON]: -118.26, [FLOW]: 890 },
  { [ORIGIN_NAME]: "Hong Kong", [ORIGIN_LAT]: 22.32, [ORIGIN_LON]: 114.17, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 520 },
  { [ORIGIN_NAME]: "Busan", [ORIGIN_LAT]: 35.18, [ORIGIN_LON]: 129.08, [DEST_NAME]: "Los Angeles", [DEST_LAT]: 33.73, [DEST_LON]: -118.26, [FLOW]: 780 },
  { [ORIGIN_NAME]: "Busan", [ORIGIN_LAT]: 35.18, [ORIGIN_LON]: 129.08, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 410 },
  { [ORIGIN_NAME]: "Rotterdam", [ORIGIN_LAT]: 51.92, [ORIGIN_LON]: 4.48, [DEST_NAME]: "New York", [DEST_LAT]: 40.67, [DEST_LON]: -74.13, [FLOW]: 630 },
  { [ORIGIN_NAME]: "Jebel Ali", [ORIGIN_LAT]: 25.01, [ORIGIN_LON]: 55.06, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 590 },
  { [ORIGIN_NAME]: "Jebel Ali", [ORIGIN_LAT]: 25.01, [ORIGIN_LON]: 55.06, [DEST_NAME]: "Mumbai", [DEST_LAT]: 18.95, [DEST_LON]: 72.95, [FLOW]: 350 },
  { [ORIGIN_NAME]: "Mumbai", [ORIGIN_LAT]: 18.95, [ORIGIN_LON]: 72.95, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 480 },
  { [ORIGIN_NAME]: "Mumbai", [ORIGIN_LAT]: 18.95, [ORIGIN_LON]: 72.95, [DEST_NAME]: "Colombo", [DEST_LAT]: 6.95, [DEST_LON]: 79.84, [FLOW]: 260 },
  { [ORIGIN_NAME]: "Colombo", [ORIGIN_LAT]: 6.95, [ORIGIN_LON]: 79.84, [DEST_NAME]: "Singapore", [DEST_LAT]: 1.29, [DEST_LON]: 103.85, [FLOW]: 300 },
  { [ORIGIN_NAME]: "Hamburg", [ORIGIN_LAT]: 53.55, [ORIGIN_LON]: 9.99, [DEST_NAME]: "New York", [DEST_LAT]: 40.67, [DEST_LON]: -74.13, [FLOW]: 410 },
  { [ORIGIN_NAME]: "Piraeus", [ORIGIN_LAT]: 37.94, [ORIGIN_LON]: 23.65, [DEST_NAME]: "Singapore", [DEST_LAT]: 1.29, [DEST_LON]: 103.85, [FLOW]: 330 },
  { [ORIGIN_NAME]: "Santos", [ORIGIN_LAT]: -23.96, [ORIGIN_LON]: -46.33, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 360 },
  { [ORIGIN_NAME]: "Vancouver", [ORIGIN_LAT]: 49.29, [ORIGIN_LON]: -123.11, [DEST_NAME]: "Shanghai", [DEST_LAT]: 31.23, [DEST_LON]: 121.47, [FLOW]: 520 },
  { [ORIGIN_NAME]: "Vancouver", [ORIGIN_LAT]: 49.29, [ORIGIN_LON]: -123.11, [DEST_NAME]: "Singapore", [DEST_LAT]: 1.29, [DEST_LON]: 103.85, [FLOW]: 300 },
];

// Plot: reads only data and the constants above
type PortInfo = {
  name: string;
  lat: number;
  lon: number;
  throughput: number;
};

const portMap = new Map<string, PortInfo>();
for (const row of data) {
  const oName = String(row[ORIGIN_NAME]);
  const oLat = Number(row[ORIGIN_LAT]);
  const oLon = Number(row[ORIGIN_LON]);
  const dName = String(row[DEST_NAME]);
  const dLat = Number(row[DEST_LAT]);
  const dLon = Number(row[DEST_LON]);
  const vol = Number(row[FLOW]);

  if (!portMap.has(oName)) {
    portMap.set(oName, { name: oName, lat: oLat, lon: oLon, throughput: 0 });
  }
  portMap.get(oName)!.throughput += vol;

  if (!portMap.has(dName)) {
    portMap.set(dName, { name: dName, lat: dLat, lon: dLon, throughput: 0 });
  }
  portMap.get(dName)!.throughput += vol;
}

const portList = Array.from(portMap.values());
const volumes = data.map((r) => Number(r[FLOW]));
const minVolume = Math.min(...volumes);
const maxVolume = Math.max(...volumes);
const totalVolume = volumes.reduce((s, v) => s + v, 0);

const throughputs = portList.map((p) => p.throughput);
const minThroughput = Math.min(...throughputs);
const maxThroughput = Math.max(...throughputs);

const hubCount = Math.round(portList.length * HUB_TOP_SHARE);
const hubNames = new Set(
  [...portList]
    .sort((a, b) => b.throughput - a.throughput)
    .slice(0, hubCount)
    .map((p) => p.name),
);

const sortedFlows = [...data].sort((a, b) => Number(a[FLOW]) - Number(b[FLOW]));

const allLons = portList.map((p) => p.lon);
const allLats = portList.map((p) => p.lat);
const rawLonMin = Math.min(...allLons);
const rawLonMax = Math.max(...allLons);
const rawLatMin = Math.min(...allLats);
const rawLatMax = Math.max(...allLats);
const rawLonSpan = rawLonMax - rawLonMin;
const rawLatSpan = rawLatMax - rawLatMin;

const baseLonMin = rawLonMin - rawLonSpan * LON_PAD_SHARE;
const baseLonMax = rawLonMax + rawLonSpan * LON_PAD_SHARE;
const baseLatMin = rawLatMin - rawLatSpan * LAT_PAD_SHARE;
const baseLatMax = rawLatMax + rawLatSpan * LAT_PAD_SHARE;

const meanLatRad = (((rawLatMin + rawLatMax) / 2) * Math.PI) / 180;
const cosMeanLat = Math.cos(meanLatRad);
const plotW = window.ANYPLOT_SIZE.width - MARGIN.left - MARGIN.right - Y_AXIS_WIDTH;
const plotH = window.ANYPLOT_SIZE.height - MARGIN.top - MARGIN.bottom - X_AXIS_HEIGHT;

const baseLonSpan = baseLonMax - baseLonMin;
const baseLatSpan = baseLatMax - baseLatMin;
const targetLonSpanForLat = (plotW / plotH) * (baseLatSpan / cosMeanLat);

const lonMid = (baseLonMin + baseLonMax) / 2;
const latMid = (baseLatMin + baseLatMax) / 2;
const finalLonSpan = Math.max(baseLonSpan, targetLonSpanForLat);
const finalLatSpan = (finalLonSpan * cosMeanLat * plotH) / plotW;

const lonMin = Math.round(lonMid - finalLonSpan / 2);
const lonMax = Math.round(lonMid + finalLonSpan / 2);
const latMin = Math.max(-85, Math.round(latMid - finalLatSpan / 2));
const latMax = Math.min(85, Math.round(latMid + finalLatSpan / 2));

const seqStartInt = parseInt(t.seq[0].slice(1), 16);
const seqEndInt = parseInt(t.seq[1].slice(1), 16);

const continentPolygons = CONTINENT_OUTLINES.map((outline) =>
  outline.split(" ").map((pair) => {
    const [lonStr, latStr] = pair.split(",");
    return [Number(lonStr), Number(latStr)] as [number, number];
  }),
);

type HoverInfo = {
  label: string;
  detail: string;
  x: number;
  y: number;
} | null;

function FlowMapLayer({
  hover,
  onHoverChange,
}: {
  hover: HoverInfo;
  onHoverChange: (h: HoverInfo) => void;
}) {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const drawingArea = useDrawingArea();

  const positionedPorts = portList.map((p) => {
    const cx = xScale(p.lon);
    const cy = yScale(p.lat);
    const tRatio = (p.throughput - minThroughput) / (maxThroughput - minThroughput);
    const radius = MIN_NODE_R + tRatio * (MAX_NODE_R - MIN_NODE_R);
    const isHub = hubNames.has(p.name);
    return { ...p, cx, cy, radius, isHub };
  });

  const labelBoxes: { x0: number; y0: number; x1: number; y1: number }[] = positionedPorts.map((p) => ({
    x0: p.cx - p.radius - 2,
    y0: p.cy - p.radius - 2,
    x1: p.cx + p.radius + 2,
    y1: p.cy + p.radius + 2,
  }));

  const labelOffsets = new Map<string, { lx: number; ly: number; anchor: "middle" | "start" | "end" }>();
  const portsBySize = [...positionedPorts].sort((a, b) => b.throughput - a.throughput);

  for (const p of portsBySize) {
    const fs = p.isHub ? 15 : 14;
    const textW = p.name.length * fs * 0.56;
    const textH = fs + 4;
    const gap = p.radius + 8;

    const candidates: { lx: number; ly: number; anchor: "middle" | "start" | "end"; bx0: number; by0: number; bx1: number; by1: number }[] = [
      {
        lx: p.cx,
        ly: p.cy - gap,
        anchor: "middle",
        bx0: p.cx - textW / 2,
        by0: p.cy - gap - textH,
        bx1: p.cx + textW / 2,
        by1: p.cy - gap,
      },
      {
        lx: p.cx,
        ly: p.cy + gap + fs - 2,
        anchor: "middle",
        bx0: p.cx - textW / 2,
        by0: p.cy + gap,
        bx1: p.cx + textW / 2,
        by1: p.cy + gap + textH,
      },
      {
        lx: p.cx + gap,
        ly: p.cy + 5,
        anchor: "start",
        bx0: p.cx + gap,
        by0: p.cy - textH / 2,
        bx1: p.cx + gap + textW,
        by1: p.cy + textH / 2,
      },
      {
        lx: p.cx - gap,
        ly: p.cy + 5,
        anchor: "end",
        bx0: p.cx - gap - textW,
        by0: p.cy - textH / 2,
        bx1: p.cx - gap,
        by1: p.cy + textH / 2,
      },
      {
        lx: p.cx + gap * 0.8,
        ly: p.cy - gap * 0.65,
        anchor: "start",
        bx0: p.cx + gap * 0.8,
        by0: p.cy - gap * 0.65 - textH,
        bx1: p.cx + gap * 0.8 + textW,
        by1: p.cy - gap * 0.65,
      },
      {
        lx: p.cx - gap * 0.8,
        ly: p.cy - gap * 0.65,
        anchor: "end",
        bx0: p.cx - gap * 0.8 - textW,
        by0: p.cy - gap * 0.65 - textH,
        bx1: p.cx - gap * 0.8,
        by1: p.cy - gap * 0.65,
      },
    ];

    let best = candidates[0];
    let bestOverlap = Infinity;

    for (const c of candidates) {
      let overlapArea = 0;
      for (const b of labelBoxes) {
        const ox = Math.max(0, Math.min(c.bx1, b.x1) - Math.max(c.bx0, b.x0));
        const oy = Math.max(0, Math.min(c.by1, b.y1) - Math.max(c.by0, b.y0));
        overlapArea += ox * oy;
      }
      if (overlapArea < bestOverlap) {
        bestOverlap = overlapArea;
        best = c;
      }
      if (overlapArea === 0) break;
    }

    labelOffsets.set(p.name, { lx: best.lx, ly: best.ly, anchor: best.anchor });
    labelBoxes.push({ x0: best.bx0 - 3, y0: best.by0 - 2, x1: best.bx1 + 3, y1: best.by1 + 2 });
  }

  const barX = drawingArea.left;
  const barY = drawingArea.top + drawingArea.height + X_AXIS_HEIGHT + 28;
  const barWidth = 260;
  const barHeight = 14;

  return (
    <g>
      <defs>
        <clipPath id="worldClip">
          <rect
            x={drawingArea.left}
            y={drawingArea.top}
            width={drawingArea.width}
            height={drawingArea.height}
          />
        </clipPath>
        <linearGradient id="flowLegendGradient" x1="0%" x2="100%" y1="0%" y2="0%">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>

      {/* Simplified continent silhouettes */}
      <g clipPath="url(#worldClip)">
        {continentPolygons.map((points, i) => {
          const d =
            points
              .map(([lon, lat], j) => `${j === 0 ? "M" : "L"} ${xScale(lon)},${yScale(lat)}`)
              .join(" ") + " Z";
          return (
            <path
              key={i}
              d={d}
              fill={t.inkSoft}
              fillOpacity={0.12}
              stroke={t.inkSoft}
              strokeWidth={1}
              strokeOpacity={0.35}
            />
          );
        })}
      </g>

      {/* Curved origin-destination flow arcs */}
      {sortedFlows.map((flow, i) => {
        const oName = String(flow[ORIGIN_NAME]);
        const dName = String(flow[DEST_NAME]);
        const vol = Number(flow[FLOW]);
        const x1 = xScale(Number(flow[ORIGIN_LON]));
        const y1 = yScale(Number(flow[ORIGIN_LAT]));
        const x2 = xScale(Number(flow[DEST_LON]));
        const y2 = yScale(Number(flow[DEST_LAT]));

        const dx = x2 - x1;
        const dy = y2 - y1;
        const dist = Math.hypot(dx, dy);
        const midX = (x1 + x2) / 2;
        const midY = (y1 + y2) / 2;
        const ux = -dy / dist;
        const uy = dx / dist;
        const bowSign = i % 2 === 0 ? 1 : -1;
        const bowMagnitude = 0.09 + ((i * 53) % 7) * 0.015;
        const bow = dist * bowMagnitude * bowSign;
        const controlX = midX + ux * bow;
        const controlY = midY + uy * bow;

        const ratio = (vol - minVolume) / (maxVolume - minVolume);
        const strokeWidth = MIN_ARC_WIDTH + ratio * (MAX_ARC_WIDTH - MIN_ARC_WIDTH);
        const strokeOpacity = 0.4 + ratio * 0.35;

        const rCh = Math.round(((seqStartInt >> 16) & 255) + (((seqEndInt >> 16) & 255) - ((seqStartInt >> 16) & 255)) * ratio);
        const gCh = Math.round(((seqStartInt >> 8) & 255) + (((seqEndInt >> 8) & 255) - ((seqStartInt >> 8) & 255)) * ratio);
        const bCh = Math.round((seqStartInt & 255) + ((seqEndInt & 255) - (seqStartInt & 255)) * ratio);
        const color = `rgb(${rCh}, ${gCh}, ${bCh})`;

        const arrowX = 0.25 * x1 + 0.5 * controlX + 0.25 * x2;
        const arrowY = 0.25 * y1 + 0.5 * controlY + 0.25 * y2;
        const angleDeg = (Math.atan2(dy, dx) * 180) / Math.PI;

        const flowTooltip = {
          label: `${oName} → ${dName}`,
          detail: `${FLOW}: ${vol.toLocaleString()}`,
          x: arrowX,
          y: arrowY,
        };

        return (
          <g key={`${oName}-${dName}-${i}`}>
            <path
              d={`M ${x1},${y1} Q ${controlX},${controlY} ${x2},${y2}`}
              fill="none"
              stroke={color}
              strokeWidth={strokeWidth}
              strokeOpacity={strokeOpacity}
              strokeLinecap="round"
            />
            <path
              d={`M ${x1},${y1} Q ${controlX},${controlY} ${x2},${y2}`}
              fill="none"
              stroke="transparent"
              strokeWidth={Math.max(strokeWidth, 16)}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => onHoverChange(flowTooltip)}
              onMouseLeave={() => onHoverChange(null)}
            />
            <polygon
              points="-7,-4.5 7,0 -7,4.5"
              transform={`translate(${arrowX}, ${arrowY}) rotate(${angleDeg})`}
              fill={color}
              fillOpacity={Math.min(strokeOpacity + 0.15, 0.92)}
            />
          </g>
        );
      })}

      {/* Port nodes and collision-checked labels */}
      {positionedPorts.map((port) => {
        const pos = labelOffsets.get(port.name)!;
        const portTooltip = {
          label: port.name,
          detail: `Throughput: ${port.throughput.toLocaleString()}`,
          x: port.cx,
          y: port.cy - port.radius - 8,
        };
        return (
          <g key={port.name}>
            <circle
              cx={port.cx}
              cy={port.cy}
              r={port.radius}
              fill={t.palette[0]}
              stroke={t.pageBg}
              strokeWidth={2.5}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => onHoverChange(portTooltip)}
              onMouseLeave={() => onHoverChange(null)}
            />
            <text
              x={pos.lx}
              y={pos.ly}
              textAnchor={pos.anchor}
              fontSize={port.isHub ? 15 : 14}
              fontWeight={port.isHub ? 700 : 600}
              fill={t.ink}
              stroke={t.pageBg}
              strokeWidth={3.5}
              paintOrder="stroke"
              style={{ pointerEvents: "none" }}
            >
              {port.name}
            </text>
          </g>
        );
      })}

      {/* Legend and usage key */}
      <g>
        <text x={barX} y={barY - 10} textAnchor="start" fontSize={14} fontWeight={600} fill={t.inkSoft}>
          {FLOW}
        </text>
        <rect x={barX} y={barY} width={barWidth} height={barHeight} fill="url(#flowLegendGradient)" rx={3} />
        <text x={barX} y={barY + barHeight + 18} textAnchor="start" fontSize={14} fill={t.inkSoft}>
          {minVolume.toLocaleString()}
        </text>
        <text x={barX + barWidth} y={barY + barHeight + 18} textAnchor="end" fontSize={14} fill={t.inkSoft}>
          {maxVolume.toLocaleString()}
        </text>
        <text
          x={drawingArea.left + drawingArea.width}
          y={barY + 12}
          textAnchor="end"
          fontSize={14}
          fill={t.inkSoft}
        >
          {LEGEND_NOTE}
        </text>
      </g>

      {/* Interactive hover tooltip */}
      {hover &&
        (() => {
          const charWidth = 7.8;
          const boxW = Math.max(hover.label.length, hover.detail.length) * charWidth + 24;
          const boxH = 48;
          const bx = hover.x - boxW / 2;
          const by = hover.y - boxH - 12;
          return (
            <g style={{ pointerEvents: "none" }}>
              <rect
                x={bx}
                y={by}
                width={boxW}
                height={boxH}
                rx={6}
                fill={t.elevatedBg}
                stroke={t.inkSoft}
                strokeOpacity={0.4}
              />
              <text x={hover.x} y={by + 20} textAnchor="middle" fontSize={14} fontWeight={600} fill={t.ink}>
                {hover.label}
              </text>
              <text x={hover.x} y={by + 38} textAnchor="middle" fontSize={14} fill={t.inkSoft}>
                {hover.detail}
              </text>
            </g>
          );
        })()}
    </g>
  );
}

export default function Chart() {
  const [hover, setHover] = useState<HoverInfo>(null);
  const { width, height } = window.ANYPLOT_SIZE;
  const subtitle = `${data.length} flows across ${portList.length} locations · total ${FLOW}: ${totalVolume.toLocaleString()}`;

  return (
    <ChartsContainer
      width={width}
      height={height}
      margin={MARGIN}
      series={[]}
      skipAnimation
      disableAxisListener
      xAxis={[
        {
          scaleType: "linear",
          min: lonMin,
          max: lonMax,
          height: X_AXIS_HEIGHT,
          label: LON_AXIS_LABEL,
          valueFormatter: (v: number) => `${v}°`,
          labelStyle: { fontSize: 15, fill: t.ink },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        },
      ]}
      yAxis={[
        {
          scaleType: "linear",
          min: latMin,
          max: latMax,
          width: Y_AXIS_WIDTH,
          label: LAT_AXIS_LABEL,
          valueFormatter: (v: number) => `${v}°`,
          labelStyle: { fontSize: 15, fill: t.ink },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        },
      ]}
    >
      <ChartsGrid horizontal />
      <FlowMapLayer hover={hover} onHoverChange={setHover} />
      <ChartsXAxis />
      <ChartsYAxis />
      <text x={width / 2} y={38} textAnchor="middle" fontSize={22} fontWeight={600} fill={t.ink}>
        {TITLE}
      </text>
      <text x={width / 2} y={64} textAnchor="middle" fontSize={15} fill={t.inkSoft}>
        {subtitle}
      </text>
    </ChartsContainer>
  );
}
