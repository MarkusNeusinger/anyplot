// anyplot.ai
// network-transport-static: Static Transport Network Diagram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-02
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = "Inter, system-ui, -apple-system, sans-serif";
const TITLE = "network-transport-static · javascript · muix · anyplot.ai";
const TITLE_H = 54;
const LEGEND_H = 36;
const CAPTION_H = 32;
const HUB_RADIUS = 46;
const BASE_STATION_RADIUS = 17;
const DEGREE_RADIUS_STEP = 1.4;
const DOMAIN_SPAN_MULT = 1.3;
const DEFAULT_BOW_PX = 18;
const ROUTE_TYPE_STYLES: Record<
  string,
  { dashed: boolean; bowShare?: number; strokeWidth: number; labelT: number }
> = {
  Express: { dashed: true, bowShare: 0.28, strokeWidth: 2.5, labelT: 0.5 },
};
const DEFAULT_ROUTE_STYLE = { dashed: false, strokeWidth: 2, labelT: 0.54 };

// Columns: set these to your data's column names
const STATION_ID = "Station code"; // role: node
const STATION_NAME = "Station name"; // role: label
const STATION_X = "East-west offset (km)"; // role: x
const STATION_Y = "North-south offset (km)"; // role: y
const ROUTE_ID = "Route ID"; // role: id
const ROUTE_TYPE = "Service type"; // role: group
const DEP_TIME = "Departure"; // role: start
const ARR_TIME = "Arrival"; // role: end
const SOURCE = "Origin station"; // role: source
const TARGET = "Destination station"; // role: target

// Data: replace this block with your own records
const stations: Array<Record<string, string | number>> = [
  { [STATION_ID]: "CTR", [STATION_NAME]: "Central", [STATION_X]: 0, [STATION_Y]: 0 },
  { [STATION_ID]: "NJC", [STATION_NAME]: "North Jct.", [STATION_X]: 0, [STATION_Y]: 2.4 },
  { [STATION_ID]: "EPT", [STATION_NAME]: "Eastport", [STATION_X]: 2.8, [STATION_Y]: 0 },
  { [STATION_ID]: "WFD", [STATION_NAME]: "Westfield", [STATION_X]: -2.8, [STATION_Y]: 0 },
  { [STATION_ID]: "SGT", [STATION_NAME]: "Southgate", [STATION_X]: 0, [STATION_Y]: -2.6 },
  { [STATION_ID]: "UPT", [STATION_NAME]: "Uptown", [STATION_X]: 0.9, [STATION_Y]: 4.6 },
  { [STATION_ID]: "HBS", [STATION_NAME]: "Harborside", [STATION_X]: 5.6, [STATION_Y]: 0 },
  { [STATION_ID]: "WBK", [STATION_NAME]: "Westbrook", [STATION_X]: -5.4, [STATION_Y]: 0.9 },
  { [STATION_ID]: "SPK", [STATION_NAME]: "Southpark", [STATION_X]: 0.7, [STATION_Y]: -5.0 },
];

const data: Array<Record<string, string>> = [
  { [ROUTE_ID]: "R10", [ROUTE_TYPE]: "Regional", [DEP_TIME]: "07:05", [ARR_TIME]: "07:12", [SOURCE]: "CTR", [TARGET]: "NJC" },
  { [ROUTE_ID]: "R11", [ROUTE_TYPE]: "Regional", [DEP_TIME]: "07:20", [ARR_TIME]: "07:27", [SOURCE]: "NJC", [TARGET]: "CTR" },
  { [ROUTE_ID]: "R20", [ROUTE_TYPE]: "Regional", [DEP_TIME]: "07:00", [ARR_TIME]: "07:14", [SOURCE]: "CTR", [TARGET]: "EPT" },
  { [ROUTE_ID]: "R21", [ROUTE_TYPE]: "Regional", [DEP_TIME]: "07:20", [ARR_TIME]: "07:34", [SOURCE]: "EPT", [TARGET]: "CTR" },
  { [ROUTE_ID]: "R30", [ROUTE_TYPE]: "Regional", [DEP_TIME]: "07:05", [ARR_TIME]: "07:17", [SOURCE]: "CTR", [TARGET]: "WFD" },
  { [ROUTE_ID]: "R31", [ROUTE_TYPE]: "Regional", [DEP_TIME]: "07:25", [ARR_TIME]: "07:37", [SOURCE]: "WFD", [TARGET]: "CTR" },
  { [ROUTE_ID]: "R40", [ROUTE_TYPE]: "Regional", [DEP_TIME]: "07:10", [ARR_TIME]: "07:19", [SOURCE]: "CTR", [TARGET]: "SGT" },
  { [ROUTE_ID]: "R41", [ROUTE_TYPE]: "Regional", [DEP_TIME]: "07:25", [ARR_TIME]: "07:34", [SOURCE]: "SGT", [TARGET]: "CTR" },
  { [ROUTE_ID]: "L12", [ROUTE_TYPE]: "Local", [DEP_TIME]: "07:15", [ARR_TIME]: "07:26", [SOURCE]: "NJC", [TARGET]: "UPT" },
  { [ROUTE_ID]: "L13", [ROUTE_TYPE]: "Local", [DEP_TIME]: "07:35", [ARR_TIME]: "07:46", [SOURCE]: "UPT", [TARGET]: "NJC" },
  { [ROUTE_ID]: "L22", [ROUTE_TYPE]: "Local", [DEP_TIME]: "07:18", [ARR_TIME]: "07:33", [SOURCE]: "EPT", [TARGET]: "HBS" },
  { [ROUTE_ID]: "L23", [ROUTE_TYPE]: "Local", [DEP_TIME]: "07:40", [ARR_TIME]: "07:55", [SOURCE]: "HBS", [TARGET]: "EPT" },
  { [ROUTE_ID]: "L32", [ROUTE_TYPE]: "Local", [DEP_TIME]: "07:20", [ARR_TIME]: "07:34", [SOURCE]: "WFD", [TARGET]: "WBK" },
  { [ROUTE_ID]: "L33", [ROUTE_TYPE]: "Local", [DEP_TIME]: "07:42", [ARR_TIME]: "07:56", [SOURCE]: "WBK", [TARGET]: "WFD" },
  { [ROUTE_ID]: "L42", [ROUTE_TYPE]: "Local", [DEP_TIME]: "07:22", [ARR_TIME]: "07:38", [SOURCE]: "SGT", [TARGET]: "SPK" },
  { [ROUTE_ID]: "L43", [ROUTE_TYPE]: "Local", [DEP_TIME]: "07:45", [ARR_TIME]: "08:01", [SOURCE]: "SPK", [TARGET]: "SGT" },
  { [ROUTE_ID]: "EX1", [ROUTE_TYPE]: "Express", [DEP_TIME]: "07:00", [ARR_TIME]: "07:28", [SOURCE]: "CTR", [TARGET]: "HBS" },
  { [ROUTE_ID]: "EX2", [ROUTE_TYPE]: "Express", [DEP_TIME]: "07:35", [ARR_TIME]: "08:03", [SOURCE]: "HBS", [TARGET]: "CTR" },
];

// Plot: reads only data and the constants above
const routeTypes: string[] = [];
for (const row of data) {
  const rt = String(row[ROUTE_TYPE]);
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
const stationList: StationInfo[] = [];

for (const row of stations) {
  const info: StationInfo = {
    id: String(row[STATION_ID]),
    label: String(row[STATION_NAME]),
    x: Number(row[STATION_X]),
    y: Number(row[STATION_Y]),
    degree: 0,
    radius: BASE_STATION_RADIUS,
    isHub: false,
    neighbors: [],
  };
  stationById.set(info.id, info);
  stationList.push(info);
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
for (const row of data) {
  const sId = String(row[SOURCE]);
  const tId = String(row[TARGET]);
  const sInfo = stationById.get(sId)!;
  const tInfo = stationById.get(tId)!;
  sInfo.degree += 1;
  tInfo.degree += 1;
  if (!sInfo.neighbors.includes(tId)) sInfo.neighbors.push(tId);
  if (!tInfo.neighbors.includes(sId)) tInfo.neighbors.push(sId);
  routes.push({
    routeId: String(row[ROUTE_ID]),
    routeType: String(row[ROUTE_TYPE]),
    departureTime: String(row[DEP_TIME]),
    arrivalTime: String(row[ARR_TIME]),
    sourceId: sId,
    targetId: tId,
  });
}

const maxStationDegree = Math.max(...stationList.map((s) => s.degree));
let hubStation = stationList[0];
for (const station of stationList) {
  station.isHub = station.degree === maxStationDegree;
  if (station.isHub) hubStation = station;
  station.radius = station.isHub
    ? HUB_RADIUS
    : BASE_STATION_RADIUS + station.degree * DEGREE_RADIUS_STEP;
}

const xs = stationList.map((s) => s.x);
const ys = stationList.map((s) => s.y);
const minX = Math.min(...xs);
const maxX = Math.max(...xs);
const minY = Math.min(...ys);
const maxY = Math.max(...ys);
const centerX = (minX + maxX) / 2;
const centerY = (minY + maxY) / 2;
const halfSpan = (Math.max(maxX - minX, maxY - minY) / 2) * DOMAIN_SPAN_MULT;
const xDomain = [centerX - halfSpan, centerX + halfSpan];
const yDomain = [centerY - halfSpan, centerY + halfSpan];

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

      {routes.map((route) => {
        const source = stationById.get(route.sourceId)!;
        const target = stationById.get(route.targetId)!;
        const sx = Number(xScale(source.x));
        const sy = Number(yScale(source.y));
        const tx = Number(xScale(target.x));
        const ty = Number(yScale(target.y));
        const dx = tx - sx;
        const dy = ty - sy;
        const length = Math.hypot(dx, dy);

        const [aId, bId] =
          route.sourceId < route.targetId
            ? [route.sourceId, route.targetId]
            : [route.targetId, route.sourceId];
        const aStation = stationById.get(aId)!;
        const bStation = stationById.get(bId)!;
        const aPoint = { x: Number(xScale(aStation.x)), y: Number(yScale(aStation.y)) };
        const bPoint = { x: Number(xScale(bStation.x)), y: Number(yScale(bStation.y)) };
        const canonLength = Math.hypot(bPoint.x - aPoint.x, bPoint.y - aPoint.y);
        const perpX = -(bPoint.y - aPoint.y) / canonLength;
        const perpY = (bPoint.x - aPoint.x) / canonLength;
        const sign = route.sourceId === aId ? -1 : 1;

        const rStyle = ROUTE_TYPE_STYLES[route.routeType] ?? DEFAULT_ROUTE_STYLE;
        const offset = rStyle.bowShare !== undefined ? length * rStyle.bowShare : DEFAULT_BOW_PX;
        const startX = sx + (dx / length) * (source.radius + 2);
        const startY = sy + (dy / length) * (source.radius + 2);
        const endX = tx - (dx / length) * (target.radius + 5);
        const endY = ty - (dy / length) * (target.radius + 5);
        const midX = (startX + endX) / 2 + perpX * offset * sign;
        const midY = (startY + endY) / 2 + perpY * offset * sign;

        const d = `M ${startX} ${startY} Q ${midX} ${midY} ${endX} ${endY}`;

        const lt = rStyle.labelT;
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
              strokeWidth={rStyle.strokeWidth}
              strokeDasharray={rStyle.dashed ? "9 6" : undefined}
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
            <text
              x={labelX}
              y={labelY}
              fontSize={14}
              fill={t.ink}
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {text}
            </text>
          </g>
        );
      })}

      {stationList.map((station) => {
        const cx = Number(xScale(station.x));
        const cy = Number(yScale(station.y));
        const r = station.radius;
        const fill = station.isHub ? t.ink : t.elevatedBg;
        const codeColor = station.isHub ? t.pageBg : t.ink;

        if (station.isHub) {
          return (
            <g key={station.id}>
              <circle cx={cx} cy={cy} r={r} fill={fill} stroke={t.ink} strokeWidth={2}>
                <title>{`${station.label} — major interchange, ${station.degree} connecting routes`}</title>
              </circle>
              <text
                x={cx}
                y={cy}
                fontSize={18}
                fontWeight={600}
                fill={codeColor}
                textAnchor="middle"
                dominantBaseline="middle"
              >
                {station.label}
              </text>
            </g>
          );
        }

        const edgeAngles = station.neighbors.map((nid) => {
          const nStation = stationById.get(nid)!;
          return Math.atan2(Number(yScale(nStation.y)) - cy, Number(xScale(nStation.x)) - cx);
        });
        let labelAngle = Math.PI / 2;
        if (edgeAngles.length > 0) {
          edgeAngles.sort((a, b) => a - b);
          let bestGap = -1;
          for (let k = 0; k < edgeAngles.length; k += 1) {
            const start = edgeAngles[k];
            const end =
              edgeAngles[(k + 1) % edgeAngles.length] +
              (k === edgeAngles.length - 1 ? 2 * Math.PI : 0);
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
            <text
              x={cx}
              y={cy}
              fontSize={14}
              fontWeight={600}
              fill={codeColor}
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {station.id}
            </text>
            <text
              x={lx}
              y={ly}
              fontSize={15}
              fontWeight={400}
              fill={t.ink}
              textAnchor={textAnchor}
              dominantBaseline="middle"
            >
              {station.label}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const chartH = H - TITLE_H - LEGEND_H - CAPTION_H;

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
      <div
        style={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 28,
          fontSize: 14,
          color: t.ink,
        }}
      >
        <span style={{ color: t.inkSoft, fontWeight: 500 }}>{`${ROUTE_TYPE}:`}</span>
        {routeTypes.map((type) => {
          const rStyle = ROUTE_TYPE_STYLES[type] ?? DEFAULT_ROUTE_STYLE;
          return (
            <span key={type} style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
              <svg width={30} height={10}>
                <line
                  x1={0}
                  y1={5}
                  x2={30}
                  y2={5}
                  stroke={typeColorMap[type]}
                  strokeWidth={rStyle.strokeWidth + 0.5}
                  strokeDasharray={rStyle.dashed ? "7 4" : undefined}
                />
              </svg>
              <span>{type}</span>
            </span>
          );
        })}
      </div>
      <ChartsContainer
        width={W}
        height={chartH}
        skipAnimation
        series={[]}
        margin={{ top: 14, right: 30, bottom: 14, left: 30 }}
        xAxis={[{ min: xDomain[0], max: xDomain[1], scaleType: "linear", position: "none" }]}
        yAxis={[{ min: yDomain[0], max: yDomain[1], scaleType: "linear", position: "none" }]}
      >
        <TransportNetworkOverlay />
      </ChartsContainer>
      <div style={{ height: CAPTION_H, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ fontSize: 14, color: t.inkSoft }}>
          {`Arrows show travel direction · labels show ${ROUTE_ID} and scheduled ${DEP_TIME} → ${ARR_TIME} · larger circle marks the ${hubStation.label} interchange`}
        </span>
      </div>
    </div>
  );
}
