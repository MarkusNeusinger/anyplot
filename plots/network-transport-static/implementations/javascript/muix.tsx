// anyplot.ai
// network-transport-static: Static Transport Network Diagram
// Library: muix 9.x | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-02
//# anyplot-orientation: square

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = "Inter, system-ui, -apple-system, sans-serif";
const TITLE = "network-transport-static · javascript · muix · anyplot.ai";
const TITLE_H = 62;
const CAPTION_H = 32;
const HUB_RADIUS = 46;
const BASE_STATION_RADIUS = 17;
const DEGREE_RADIUS_STEP = 1.4;
const DOMAIN_SPAN_MULT = 1.3;
const EXPRESS_TYPE = "Express";

const ROUTE_ID_COL = "route_id";
const ROUTE_TYPE_COL = "route_type";
const DEP_TIME_COL = "departure_time";
const ARR_TIME_COL = "arrival_time";
const SRC_ID_COL = "source_id";
const SRC_LABEL_COL = "source_label";
const SRC_X_COL = "source_x";
const SRC_Y_COL = "source_y";
const TGT_ID_COL = "target_id";
const TGT_LABEL_COL = "target_label";
const TGT_X_COL = "target_x";
const TGT_Y_COL = "target_y";

// Data: regional commuter-rail network (flat scalar route records)
const DATA: Array<Record<string, string | number>> = [
  { route_id: "R10", route_type: "Regional", departure_time: "07:05", arrival_time: "07:12", source_id: "CTR", source_label: "Central", source_x: 0, source_y: 0, target_id: "NJC", target_label: "North Jct.", target_x: 0, target_y: 2.4 },
  { route_id: "R11", route_type: "Regional", departure_time: "07:20", arrival_time: "07:27", source_id: "NJC", source_label: "North Jct.", source_x: 0, source_y: 2.4, target_id: "CTR", target_label: "Central", target_x: 0, target_y: 0 },
  { route_id: "R20", route_type: "Regional", departure_time: "07:00", arrival_time: "07:14", source_id: "CTR", source_label: "Central", source_x: 0, source_y: 0, target_id: "EPT", target_label: "Eastport", target_x: 2.8, target_y: 0 },
  { route_id: "R21", route_type: "Regional", departure_time: "07:20", arrival_time: "07:34", source_id: "EPT", source_label: "Eastport", target_id: "CTR", source_x: 2.8, source_y: 0, target_label: "Central", target_x: 0, target_y: 0 },
  { route_id: "R30", route_type: "Regional", departure_time: "07:05", arrival_time: "07:17", source_id: "CTR", source_label: "Central", source_x: 0, source_y: 0, target_id: "WFD", target_label: "Westfield", target_x: -2.8, target_y: 0 },
  { route_id: "R31", route_type: "Regional", departure_time: "07:25", arrival_time: "07:37", source_id: "WFD", source_label: "Westfield", source_x: -2.8, source_y: 0, target_id: "CTR", target_label: "Central", target_x: 0, target_y: 0 },
  { route_id: "R40", route_type: "Regional", departure_time: "07:10", arrival_time: "07:19", source_id: "CTR", source_label: "Central", source_x: 0, source_y: 0, target_id: "SGT", target_label: "Southgate", target_x: 0, target_y: -2.6 },
  { route_id: "R41", route_type: "Regional", departure_time: "07:25", arrival_time: "07:34", source_id: "SGT", source_label: "Southgate", source_x: 0, source_y: -2.6, target_id: "CTR", target_label: "Central", target_x: 0, target_y: 0 },
  { route_id: "L12", route_type: "Local", departure_time: "07:15", arrival_time: "07:26", source_id: "NJC", source_label: "North Jct.", source_x: 0, source_y: 2.4, target_id: "UPT", target_label: "Uptown", target_x: 0.9, target_y: 4.6 },
  { route_id: "L13", route_type: "Local", departure_time: "07:35", arrival_time: "07:46", source_id: "UPT", source_label: "Uptown", source_x: 0.9, source_y: 4.6, target_id: "NJC", target_label: "North Jct.", target_x: 0, target_y: 2.4 },
  { route_id: "L22", route_type: "Local", departure_time: "07:18", arrival_time: "07:33", source_id: "EPT", source_label: "Eastport", source_x: 2.8, source_y: 0, target_id: "HBS", target_label: "Harborside", target_x: 5.6, target_y: 0 },
  { route_id: "L23", route_type: "Local", departure_time: "07:40", arrival_time: "07:55", source_id: "HBS", source_label: "Harborside", source_x: 5.6, source_y: 0, target_id: "EPT", target_label: "Eastport", target_x: 2.8, target_y: 0 },
  { route_id: "L32", route_type: "Local", departure_time: "07:20", arrival_time: "07:34", source_id: "WFD", source_label: "Westfield", source_x: -2.8, source_y: 0, target_id: "WBK", target_label: "Westbrook", target_x: -5.4, target_y: 0.9 },
  { route_id: "L33", route_type: "Local", departure_time: "07:42", arrival_time: "07:56", source_id: "WBK", source_label: "Westbrook", source_x: -5.4, source_y: 0.9, target_id: "WFD", target_label: "Westfield", target_x: -2.8, target_y: 0 },
  { route_id: "L42", route_type: "Local", departure_time: "07:22", arrival_time: "07:38", source_id: "SGT", source_label: "Southgate", source_x: 0, source_y: -2.6, target_id: "SPK", target_label: "Southpark", target_x: 0.7, target_y: -5.0 },
  { route_id: "L43", route_type: "Local", departure_time: "07:45", arrival_time: "08:01", source_id: "SPK", source_label: "Southpark", source_x: 0.7, source_y: -5.0, target_id: "SGT", target_label: "Southgate", target_x: 0, target_y: -2.6 },
  { route_id: "EX1", route_type: "Express", departure_time: "07:00", arrival_time: "07:28", source_id: "CTR", source_label: "Central", source_x: 0, source_y: 0, target_id: "HBS", target_label: "Harborside", target_x: 5.6, target_y: 0 },
  { route_id: "EX2", route_type: "Express", departure_time: "07:35", arrival_time: "08:03", source_id: "HBS", source_label: "Harborside", source_x: 5.6, source_y: 0, target_id: "CTR", target_label: "Central", target_x: 0, target_y: 0 },
];

// Derive route types in order of first appearance
const routeTypes: string[] = [];
for (const row of DATA) {
  const rt = String(row[ROUTE_TYPE_COL]);
  if (!routeTypes.includes(rt)) routeTypes.push(rt);
}
const typeColorMap: Record<string, string> = {};
for (let i = 0; i < routeTypes.length; i += 1) {
  typeColorMap[routeTypes[i]] = t.palette[i];
}

interface StationInfo {
  id: string;
  label: string;
  x: number;
  y: number;
  degree: number;
  radius: number;
  isHub: boolean;
  neighbors: string[];
}

const stationById = new Map<string, StationInfo>();
const stations: StationInfo[] = [];

for (const row of DATA) {
  const endpoints = [
    { id: String(row[SRC_ID_COL]), label: String(row[SRC_LABEL_COL]), x: Number(row[SRC_X_COL]), y: Number(row[SRC_Y_COL]) },
    { id: String(row[TGT_ID_COL]), label: String(row[TGT_LABEL_COL]), x: Number(row[TGT_X_COL]), y: Number(row[TGT_Y_COL]) },
  ];
  for (const ep of endpoints) {
    if (!stationById.has(ep.id)) {
      const info: StationInfo = {
        id: ep.id,
        label: ep.label,
        x: ep.x,
        y: ep.y,
        degree: 0,
        radius: BASE_STATION_RADIUS,
        isHub: false,
        neighbors: [],
      };
      stationById.set(ep.id, info);
      stations.push(info);
    }
  }
}

interface RouteInfo {
  routeId: string;
  routeType: string;
  departureTime: string;
  arrivalTime: string;
  sourceId: string;
  targetId: string;
}

const routes: RouteInfo[] = [];
for (const row of DATA) {
  const sId = String(row[SRC_ID_COL]);
  const tId = String(row[TGT_ID_COL]);
  const sInfo = stationById.get(sId)!;
  const tInfo = stationById.get(tId)!;
  sInfo.degree += 1;
  tInfo.degree += 1;
  if (!sInfo.neighbors.includes(tId)) sInfo.neighbors.push(tId);
  if (!tInfo.neighbors.includes(sId)) tInfo.neighbors.push(sId);
  routes.push({
    routeId: String(row[ROUTE_ID_COL]),
    routeType: String(row[ROUTE_TYPE_COL]),
    departureTime: String(row[DEP_TIME_COL]),
    arrivalTime: String(row[ARR_TIME_COL]),
    sourceId: sId,
    targetId: tId,
  });
}

// Identify the primary interchange hub by maximum degree
const maxStationDegree = Math.max(...stations.map((s) => s.degree));
for (const station of stations) {
  station.isHub = station.degree === maxStationDegree;
  station.radius = station.isHub ? HUB_RADIUS : BASE_STATION_RADIUS + station.degree * DEGREE_RADIUS_STEP;
}

// Square-friendly domain derived from station coordinates
const xs = stations.map((s) => s.x);
const ys = stations.map((s) => s.y);
const minX = Math.min(...xs);
const maxX = Math.max(...xs);
const minY = Math.min(...ys);
const maxY = Math.max(...ys);
const centerX = (minX + maxX) / 2;
const centerY = (minY + maxY) / 2;
const halfSpan = (Math.max(maxX - minX, maxY - minY) / 2) * DOMAIN_SPAN_MULT;
const X_DOMAIN = [centerX - halfSpan, centerX + halfSpan];
const Y_DOMAIN = [centerY - halfSpan, centerY + halfSpan];

function TransportNetworkOverlay() {
  const xScale = useXScale();
  const yScale = useYScale();

  return (
    <g fontFamily={FONT}>
      <defs>
        {routeTypes.map((type) => (
          <marker
            key={type}
            id={`arrow-${type}`}
            markerWidth="9"
            markerHeight="9"
            refX="6.5"
            refY="3"
            orient="auto"
          >
            <path d="M0,0 L7,3 L0,6 Z" fill={typeColorMap[type]} />
          </marker>
        ))}
      </defs>

      {/* Directed route edges and pill labels */}
      {routes.map((route) => {
        const source = stationById.get(route.sourceId)!;
        const target = stationById.get(route.targetId)!;
        const sx = xScale(source.x);
        const sy = yScale(source.y);
        const tx = xScale(target.x);
        const ty = yScale(target.y);
        const dx = tx - sx;
        const dy = ty - sy;
        const length = Math.hypot(dx, dy) || 1;

        const [aId, bId] = route.sourceId < route.targetId ? [route.sourceId, route.targetId] : [route.targetId, route.sourceId];
        const aStation = stationById.get(aId)!;
        const bStation = stationById.get(bId)!;
        const aPoint = { x: xScale(aStation.x), y: yScale(aStation.y) };
        const bPoint = { x: xScale(bStation.x), y: yScale(bStation.y) };
        const canonLength = Math.hypot(bPoint.x - aPoint.x, bPoint.y - aPoint.y) || 1;
        const perpX = -(bPoint.y - aPoint.y) / canonLength;
        const perpY = (bPoint.x - aPoint.x) / canonLength;
        const sign = route.sourceId === aId ? -1 : 1;

        const isExpress = route.routeType === EXPRESS_TYPE;
        const offset = isExpress ? length * 0.28 : 18;
        const startX = sx + (dx / length) * (source.radius + 2);
        const startY = sy + (dy / length) * (source.radius + 2);
        const endX = tx - (dx / length) * (target.radius + 5);
        const endY = ty - (dy / length) * (target.radius + 5);
        const midX = (startX + endX) / 2 + perpX * offset * sign;
        const midY = (startY + endY) / 2 + perpY * offset * sign;

        const d = `M ${startX} ${startY} Q ${midX} ${midY} ${endX} ${endY}`;

        const lt = isExpress ? 0.5 : 0.54;
        const curveX = (1 - lt) ** 2 * startX + 2 * (1 - lt) * lt * midX + lt ** 2 * endX;
        const curveY = (1 - lt) ** 2 * startY + 2 * (1 - lt) * lt * midY + lt ** 2 * endY;
        const text = `${route.routeId} ${route.departureTime}→${route.arrivalTime}`;
        const boxW = text.length * 7.4 + 10;
        const normPerpX = perpX * sign;
        const normPerpY = perpY * sign;
        const labelX = curveX + normPerpX * (boxW * 0.5 + 10);
        const labelY = curveY + normPerpY * 22;
        const tooltip = `${route.routeId}: ${source.label} → ${target.label} (${route.departureTime} → ${route.arrivalTime}, ${route.routeType})`;

        return (
          <g key={route.routeId}>
            <path
              d={d}
              fill="none"
              stroke={typeColorMap[route.routeType]}
              strokeWidth={isExpress ? 2.5 : 2}
              strokeDasharray={isExpress ? "9 6" : undefined}
              markerEnd={`url(#arrow-${route.routeType})`}
            >
              <title>{tooltip}</title>
            </path>
            <rect
              x={labelX - boxW / 2}
              y={labelY - 11}
              width={boxW}
              height={20}
              rx={3}
              fill={t.elevatedBg}
              opacity={0.94}
            >
              <title>{tooltip}</title>
            </rect>
            <text x={labelX} y={labelY} fontSize={14} fill={t.ink} textAnchor="middle" dominantBaseline="middle">
              {text}
            </text>
          </g>
        );
      })}

      {/* Station nodes and angular-gap labels */}
      {stations.map((station) => {
        const cx = xScale(station.x);
        const cy = yScale(station.y);
        const r = station.radius;
        const fill = station.isHub ? t.ink : t.elevatedBg;
        const codeColor = station.isHub ? t.pageBg : t.ink;

        if (station.isHub) {
          return (
            <g key={station.id}>
              <circle cx={cx} cy={cy} r={r} fill={fill} stroke={t.ink} strokeWidth={2}>
                <title>{`${station.label} — major interchange, ${station.degree} connecting routes`}</title>
              </circle>
              <text x={cx} y={cy} fontSize={18} fontWeight={600} fill={codeColor} textAnchor="middle" dominantBaseline="middle">
                {station.label}
              </text>
            </g>
          );
        }

        const edgeAngles = station.neighbors.map((nid) => {
          const nStation = stationById.get(nid)!;
          return Math.atan2(yScale(nStation.y) - cy, xScale(nStation.x) - cx);
        });
        let labelAngle = Math.PI / 2;
        if (edgeAngles.length > 0) {
          edgeAngles.sort((a, b) => a - b);
          let bestGap = -1;
          for (let k = 0; k < edgeAngles.length; k += 1) {
            const start = edgeAngles[k];
            const end = edgeAngles[(k + 1) % edgeAngles.length] + (k === edgeAngles.length - 1 ? 2 * Math.PI : 0);
            const gap = end - start;
            if (gap > bestGap) {
              bestGap = gap;
              labelAngle = start + gap / 2;
            }
          }
        }
        const cosA = Math.cos(labelAngle);
        const textAnchor = cosA > 0.35 ? "start" : cosA < -0.35 ? "end" : "middle";
        const labelDist = r + (textAnchor === "middle" ? 20 : 13);
        const lx = cx + Math.cos(labelAngle) * labelDist;
        const ly = cy + Math.sin(labelAngle) * labelDist;

        return (
          <g key={station.id}>
            <circle cx={cx} cy={cy} r={r} fill={fill} stroke={t.ink} strokeWidth={2}>
              <title>{`${station.label} (${station.id}) — ${station.degree} connecting route${station.degree === 1 ? "" : "s"}`}</title>
            </circle>
            <text x={cx} y={cy} fontSize={14} fontWeight={600} fill={codeColor} textAnchor="middle" dominantBaseline="middle">
              {station.id}
            </text>
            <text x={lx} y={ly} fontSize={15} fontWeight={400} fill={t.ink} textAnchor={textAnchor} dominantBaseline="middle">
              {station.label}
            </text>
          </g>
        );
      })}

      {/* Route type legend */}
      <g transform="translate(28, 26)">
        {routeTypes.map((type, i) => (
          <g key={type} transform={`translate(0, ${i * 28})`}>
            <line
              x1={0}
              y1={8}
              x2={26}
              y2={8}
              stroke={typeColorMap[type]}
              strokeWidth={3}
              strokeDasharray={type === EXPRESS_TYPE ? "9 6" : undefined}
            />
            <text x={34} y={13} fontSize={14} fill={t.ink}>
              {type}
            </text>
          </g>
        ))}
      </g>
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const chartH = H - TITLE_H - CAPTION_H;

  return (
    <div
      style={{
        width: W,
        height: H,
        backgroundColor: t.pageBg,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div style={{ height: TITLE_H, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</span>
      </div>
      <ChartsContainer
        width={W}
        height={chartH}
        skipAnimation
        series={[]}
        margin={{ top: 20, right: 30, bottom: 20, left: 30 }}
        xAxis={[{ min: X_DOMAIN[0], max: X_DOMAIN[1], scaleType: "linear", position: "none" }]}
        yAxis={[{ min: Y_DOMAIN[0], max: Y_DOMAIN[1], scaleType: "linear", position: "none" }]}
      >
        <TransportNetworkOverlay />
      </ChartsContainer>
      <div style={{ height: CAPTION_H, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ fontSize: 14, color: t.inkSoft }}>
          Arrows show travel direction · labels show route ID and scheduled departure {"→"} arrival · larger circle marks the Central interchange
        </span>
      </div>
    </div>
  );
}
