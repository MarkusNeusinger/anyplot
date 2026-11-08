// anyplot.ai
// area-elevation-profile: Terrain Elevation Profile Along Transect
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
//# anyplot-orientation: landscape

import { LineChart } from "@mui/x-charts/LineChart";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "area-elevation-profile · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const ELEV_PAD_SHARE = 0.15; // room below the lowest sample, as a share of the elevation range
const LABEL_HEADROOM_SHARE = 0.32; // room above the highest sample for the landmark labels
const LABEL_MIN_GAP_PX = 230; // landmark labels closer than this step up one line
const CHAR_W_PX = 9; // approximate width of one 15 px bold label character
const X_AXIS_H = 64;
const Y_AXIS_W = 84;

// Columns: set these to your data's column names
const DISTANCE = "Distance (km)"; // role: distance
const ELEVATION = "Elevation (m)"; // role: elevation
// A place on the first and last sample names the start and end of the transect;
// on any other sample it marks a landmark at that sample's distance and elevation
const PLACE = "Place"; // role: landmark_name
const ELEVATION_PER_DISTANCE = 1000; // elevation units per distance unit (m per km), for the exaggeration note

// Data: replace this block with your own records, one object per row
// Tour du Mont Blanc stages 1–3, Les Houches to Courmayeur: 121 samples every 500 m,
// linearly interpolated between approximate route waypoints [km, m]
const data = (() => {
  const waypoints = [
    [0, 1010], [3, 1330], [6.5, 1653], [8, 1420], [9.5, 1340],
    [12, 1250], [14, 1180], [16, 1167], [18, 1190], [20.5, 1210],
    [22.5, 1500], [24, 1706], [26, 2050], [27.5, 2329], [29, 2479],
    [31, 2050], [33.5, 1549], [36, 1700], [38, 1789], [40, 2000],
    [42.5, 2300], [44.5, 2516], [46.5, 2200], [48, 2050], [50, 1970],
    [51.5, 2150], [53.5, 2435], [55, 2150], [56.5, 1956], [58.5, 1550],
    [60, 1224],
  ];
  const places = new Map([
    [0, "Les Houches"],
    [6.5, "Col de Voza"],
    [16, "Les Contamines"],
    [27.5, "Col du Bonhomme"],
    [33.5, "Les Chapieux"],
    [44.5, "Col de la Seigne"],
    [53.5, "Arête du Mont Favre"],
    [60, "Courmayeur"],
  ]);
  return Array.from({ length: 121 }, (_, i) => {
    const d = i * 0.5;
    let j = 0;
    while (j < waypoints.length - 2 && waypoints[j + 1][0] <= d) j += 1;
    const [d0, e0] = waypoints[j];
    const [d1, e1] = waypoints[j + 1];
    const f = Math.max(0, Math.min(1, (d - d0) / (d1 - d0)));
    return { [DISTANCE]: d, [ELEVATION]: Math.round(e0 + (e1 - e0) * f), [PLACE]: places.get(d) ?? null };
  });
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[DISTANCE] - b[DISTANCE]);
const distances = rows.map((d) => d[DISTANCE]);
const elevations = rows.map((d) => d[ELEVATION]);
const start = rows[0];
const end = rows[rows.length - 1];
const landmarks = rows.slice(1, -1).filter((d) => d[PLACE]);

const known = elevations.filter((v) => v != null);
const elevMin = Math.min(...known);
const elevMax = Math.max(...known);
const elevSpan = elevMax - elevMin || 1;
const yLo = elevMin - ELEV_PAD_SHARE * elevSpan;
const yHi = elevMax + LABEL_HEADROOM_SHARE * elevSpan;
const xMin = distances[0];
const xMax = distances[distances.length - 1];

const DIST_UNIT = DISTANCE.match(/\(([^)]+)\)/)?.[1] ?? "";
const ELEV_UNIT = ELEVATION.match(/\(([^)]+)\)/)?.[1] ?? "";
const fmtElev = (v: number) => `${Math.round(v).toLocaleString("en-US")} ${ELEV_UNIT}`.trim();

const SUBTITLE = [
  start[PLACE] && end[PLACE] ? `${start[PLACE]} → ${end[PLACE]}` : null,
  `${Number((xMax - xMin).toFixed(1))} ${DIST_UNIT} transect`.trim(),
  `${rows.length} samples`,
  `${landmarks.length} landmarks`,
]
  .filter(Boolean)
  .join(" · ");

// Start, end and landmark labels plus the exaggeration note, placed in data coordinates
function ProfileAnnotations() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { left, top, width, height } = useDrawingArea();

  const pxPerDistance = Math.abs(xScale(xMax) - xScale(xMin)) / ((xMax - xMin) * ELEVATION_PER_DISTANCE);
  const pxPerElevation = Math.abs(yScale(yLo) - yScale(yHi)) / (yHi - yLo);
  const exaggeration = pxPerElevation / pxPerDistance;

  const labelXs = landmarks.map((d) => xScale(d[DISTANCE]));
  const levels: number[] = [];
  labelXs.forEach((x, i) => {
    levels.push(i > 0 && x - labelXs[i - 1] < LABEL_MIN_GAP_PX && levels[i - 1] === 0 ? 1 : 0);
  });

  // End labels sit just above the highest stretch of profile they span, so the
  // line never runs through them; a leader drops to the end point when they rise
  const sx = xScale(start[DISTANCE]);
  const sy = yScale(start[ELEVATION]);
  const ex = xScale(end[DISTANCE]);
  const ey = yScale(end[ELEVATION]);
  const startW = String(start[PLACE] ?? "").length * CHAR_W_PX + 24;
  const endW = String(end[PLACE] ?? "").length * CHAR_W_PX + 24;
  const startTop = Math.min(
    sy,
    ...rows.filter((d) => xScale(d[DISTANCE]) <= sx + startW).map((d) => yScale(d[ELEVATION])),
  );
  const endTop = Math.min(
    ey,
    ...rows.filter((d) => xScale(d[DISTANCE]) >= ex - endW).map((d) => yScale(d[ELEVATION])),
  );

  return (
    <g>
      {landmarks.map((d, i) => {
        const x = labelXs[i];
        const py = yScale(d[ELEVATION]);
        const labelY = top + 22 + levels[i] * 40;
        return (
          <g key={`${d[PLACE]}-${d[DISTANCE]}`}>
            <line
              x1={x}
              x2={x}
              y1={labelY + 26}
              y2={py}
              stroke={t.inkSoft}
              strokeWidth={1.5}
              strokeDasharray="5 4"
            />
            <circle cx={x} cy={py} r={5} fill={t.palette[0]} stroke={t.pageBg} strokeWidth={1.5} />
            <text x={x} y={labelY} textAnchor="middle" fontSize={15} fontWeight={600} fill={t.ink}>
              {d[PLACE]}
            </text>
            <text x={x} y={labelY + 18} textAnchor="middle" fontSize={14} fill={t.inkSoft}>
              {fmtElev(d[ELEVATION])}
            </text>
          </g>
        );
      })}
      <line
        x1={sx + 12}
        x2={sx}
        y1={startTop - 10}
        y2={sy}
        stroke={t.inkSoft}
        strokeWidth={1.5}
        strokeDasharray="5 4"
      />
      <circle cx={sx} cy={sy} r={5} fill={t.palette[0]} stroke={t.pageBg} strokeWidth={1.5} />
      <text x={sx + 12} y={startTop - 34} textAnchor="start" fontSize={15} fontWeight={700} fill={t.ink}>
        {start[PLACE]}
      </text>
      <text x={sx + 12} y={startTop - 15} textAnchor="start" fontSize={14} fill={t.inkSoft}>
        {fmtElev(start[ELEVATION])}
      </text>
      <line
        x1={ex - 12}
        x2={ex}
        y1={endTop - 10}
        y2={ey}
        stroke={t.inkSoft}
        strokeWidth={1.5}
        strokeDasharray="5 4"
      />
      <circle cx={ex} cy={ey} r={5} fill={t.palette[0]} stroke={t.pageBg} strokeWidth={1.5} />
      <text x={ex - 12} y={endTop - 34} textAnchor="end" fontSize={15} fontWeight={700} fill={t.ink}>
        {end[PLACE]}
      </text>
      <text x={ex - 12} y={endTop - 15} textAnchor="end" fontSize={14} fill={t.inkSoft}>
        {fmtElev(end[ELEVATION])}
      </text>
      <text x={left + width} y={top + height + X_AXIS_H - 12} textAnchor="end" fontSize={14} fill={t.inkSoft}>
        {`Vertical exaggeration ≈ ${Math.round(exaggeration)}×`}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, px: "40px", pt: "18px", boxSizing: "border-box" }}>
        <Typography sx={{ color: t.ink, fontSize: "22px", fontWeight: 600, lineHeight: 1.2 }}>
          {TITLE}
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: "15px", lineHeight: 1.2, mt: "8px" }}>
          {SUBTITLE}
        </Typography>
      </Box>
      <LineChart
        width={width}
        height={height - TITLE_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        xAxis={[
          {
            data: distances,
            scaleType: "linear",
            min: xMin,
            max: xMax,
            label: DISTANCE,
            tickNumber: 9,
            height: X_AXIS_H,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            label: ELEVATION,
            min: yLo,
            max: yHi,
            width: Y_AXIS_W,
            valueFormatter: (v: number) => v.toLocaleString("en-US"),
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "profile",
            data: elevations,
            label: ELEVATION,
            color: t.palette[0],
            area: true,
            baseline: "min",
            showMark: false,
            curve: "linear",
          },
        ]}
        margin={{ top: 12, right: 48, bottom: 8, left: 24 }}
        sx={{
          "& .MuiLineChart-area": { fillOpacity: 0.35 },
          "& .MuiLineChart-line": { strokeWidth: 2.5 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <ProfileAnnotations />
      </LineChart>
    </Box>
  );
}
