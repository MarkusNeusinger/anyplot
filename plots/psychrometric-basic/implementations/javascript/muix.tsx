// anyplot.ai
// psychrometric-basic: Psychrometric Chart for HVAC
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SATURATION_RH = 100; // percent; this relative-humidity level is the saturation curve
const COMFORT = { tMin: 20, tMax: 26, rhMin: 30, rhMax: 60 }; // comfort zone the spec names, °C and % RH
const GRID_POINTS = 241; // dry-bulb samples per property line
const X_LABEL = "Dry-bulb temperature (°C)";
const Y_LABEL = "Humidity ratio (g water / kg dry air)";
const FAMILY = {
  rh: { color: t.palette[0], dash: "none", width: 1.8, key: "Relative humidity (%)" },
  wb: { color: t.palette[1], dash: "8 5", width: 1.6, key: "Wet-bulb temperature (°C)" },
  h: { color: t.palette[2], dash: "12 4 3 4", width: 1.6, key: "Enthalpy (kJ/kg dry air)" },
  v: { color: t.palette[3], dash: "2 3", width: 2.4, key: "Specific volume (m³/kg dry air)" },
};
const SATURATION_KEY = "Saturation (100 % RH)";
const COMFORT_KEY = "Comfort zone";
const PROCESS_COLOR = t.palette[5]; // cyan reads as cooling; red is reserved for bad / loss
const TITLE_H = 48;
const SUBTITLE_H = 26;
const KEY_H = 40;
const MARGIN = { top: 30, right: 72, bottom: 8, left: 16 };
const LABEL_GAP = 18; // minimum px between stacked edge labels

// Data: replace these parameters with your own pressure, chart range, property levels and process
const PRESSURE_KPA = 101.325; // standard sea-level pressure
const DRY_BULB_MIN = -10; // role: dry_bulb_temp, °C
const DRY_BULB_MAX = 50; // °C
const HUMIDITY_MAX = 30; // role: humidity_ratio, g/kg dry air at the top of the chart
const RH_LEVELS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]; // role: relative_humidity, %
const WB_LEVELS = [5, 10, 15, 20, 25, 30]; // role: wet_bulb_temp, °C
const ENTHALPY_LEVELS = [20, 40, 60, 80, 100]; // role: enthalpy, kJ/kg dry air
const VOLUME_LEVELS = [0.8, 0.85, 0.9, 0.95]; // role: specific_volume, m³/kg dry air
const PROCESS = { name: "Cooling & dehumidification", fromT: 30, fromRh: 50, toT: 14, toRh: 90 };

// Plot: reads only the parameters and the constants above
// ASHRAE moist-air relations; saturation pressure from Alduchov-Eskridge, all w in g/kg
const pa = PRESSURE_KPA * 1000;
const temps = Array.from({ length: GRID_POINTS }, (_, i) => DRY_BULB_MIN + (i * (DRY_BULB_MAX - DRY_BULB_MIN)) / (GRID_POINTS - 1));
const pws = temps.map((tc) => 610.94 * Math.exp((17.625 * tc) / (tc + 243.04)));
const wSat = pws.map((p) => (621.945 * p) / (pa - p));

// Lines that are not RH curves stop at the saturation curve; the plot area clips the rest
const lines = [
  ...RH_LEVELS.map((rh) => ({
    family: "rh",
    level: rh,
    w: pws.map((p) => (621.945 * (p * rh) / 100) / (pa - (p * rh) / 100)),
  })),
  ...WB_LEVELS.map((twb) => {
    const pStar = 610.94 * Math.exp((17.625 * twb) / (twb + 243.04));
    const wStar = (0.621945 * pStar) / (pa - pStar);
    return {
      family: "wb",
      level: twb,
      w: temps.map((tc, i) => {
        const w = (1000 * ((2501 - 2.326 * twb) * wStar - 1.006 * (tc - twb))) / (2501 + 1.86 * tc - 4.186 * twb);
        return tc >= twb && w <= wSat[i] ? w : null;
      }),
    };
  }),
  ...ENTHALPY_LEVELS.map((h) => ({
    family: "h",
    level: h,
    w: temps.map((tc, i) => {
      const w = (1000 * (h - 1.006 * tc)) / (2501 + 1.86 * tc);
      return w <= wSat[i] ? w : null;
    }),
  })),
  ...VOLUME_LEVELS.map((v) => ({
    family: "v",
    level: v,
    w: temps.map((tc, i) => {
      const w = (1000 * ((v * PRESSURE_KPA) / (0.287042 * (tc + 273.15)) - 1)) / 1.607858;
      return w <= wSat[i] ? w : null;
    }),
  })),
].map((line) => ({ ...line, id: `${line.family}-${String(line.level).replace(".", "_")}` }));

// Direct labels: wet-bulb values where each line leaves the saturation curve, every
// other line where it leaves the plot area (top or right for RH, bottom or right otherwise)
const lastIndex = GRID_POINTS - 1;
const labels = lines.flatMap((line) => {
  const spec = FAMILY[line.family];
  const text = line.family === "v" ? line.level.toFixed(2) : line.family === "rh" ? `${line.level}%` : `${line.level}`;
  if (line.family === "wb") {
    const start = line.w.findIndex((w) => w !== null);
    return start >= 0 && line.w[start] <= HUMIDITY_MAX ? [{ id: line.id, text: `${text}°`, x: temps[start], y: line.w[start], side: "start", color: spec.color }] : [];
  }
  const rising = line.family === "rh";
  let i = -1;
  for (let k = 0; k <= lastIndex; k++) {
    if (line.w[k] !== null && line.w[k] >= 0 && line.w[k] <= HUMIDITY_MAX) i = k;
  }
  if (i < 0) return [];
  if (i === lastIndex) return [{ id: line.id, text, x: DRY_BULB_MAX, y: line.w[i], side: "right", color: spec.color }];
  const edge = rising ? HUMIDITY_MAX : 0;
  const x = temps[i] + ((edge - line.w[i]) / (line.w[i + 1] - line.w[i])) * (temps[i + 1] - temps[i]);
  return [{ id: line.id, text, x, y: edge, side: rising ? "top" : "bottom", color: spec.color }];
});

// Comfort zone polygon and the process states, from the RH relation
const comfortT = Array.from({ length: 13 }, (_, i) => COMFORT.tMin + (i * (COMFORT.tMax - COMFORT.tMin)) / 12);
const [comfortUpper, comfortLower] = [COMFORT.rhMax, COMFORT.rhMin].map((rh) =>
  comfortT.map((tc) => {
    const p = (610.94 * Math.exp((17.625 * tc) / (tc + 243.04)) * rh) / 100;
    return { x: tc, y: (621.945 * p) / (pa - p) };
  }),
);
const comfortPolygon = [...comfortUpper, ...[...comfortLower].reverse()];
const states = [
  [PROCESS.fromT, PROCESS.fromRh],
  [PROCESS.toT, PROCESS.toRh],
].map(([tc, rh]) => {
  const p = (610.94 * Math.exp((17.625 * tc) / (tc + 243.04)) * rh) / 100;
  return { x: tc, y: (621.945 * p) / (pa - p) };
});

const TITLE = "psychrometric-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `ASHRAE moist-air relations at ${PRESSURE_KPA} kPa · dry bulb ${DRY_BULB_MIN} to ${DRY_BULB_MAX} °C · ${lines.length} property lines`;
const KEY_ITEMS = [
  { text: SATURATION_KEY, color: FAMILY.rh.color, dash: "none", width: 3.6 },
  ...Object.values(FAMILY).map((f) => ({ text: f.key, color: f.color, dash: f.dash, width: f.width + 0.6 })),
  { text: PROCESS.name, color: PROCESS_COLOR, dash: "none", width: 3 },
];

function Overlays() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { left, top, width, height } = useDrawingArea();
  const [p1, p2] = states.map((s) => ({ x: xScale(s.x), y: yScale(s.y) }));
  const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x);
  const halo = { stroke: t.pageBg, strokeWidth: 4, paintOrder: "stroke", strokeLinejoin: "round" };
  const comfortMid = comfortUpper[Math.floor(comfortT.length / 2)];
  const comfortLow = comfortLower[Math.floor(comfortT.length / 2)];

  // Right-edge labels keep a minimum vertical gap, pushed downward from the top; the lines stay put
  const rightLabelY = new Map();
  let previousY = -Infinity;
  for (const l of labels.filter((d) => d.side === "right").sort((a, b) => b.y - a.y)) {
    previousY = Math.max(yScale(l.y) + 5, previousY + LABEL_GAP);
    rightLabelY.set(l.id, previousY);
  }

  return (
    <g>
      <polygon
        points={comfortPolygon.map((d) => `${xScale(d.x)},${yScale(d.y)}`).join(" ")}
        fill={t.inkSoft}
        fillOpacity={0.16}
        stroke={t.inkSoft}
        strokeWidth={1.5}
        strokeDasharray="6 4"
      />
      <text x={xScale(comfortMid.x)} y={(yScale(comfortMid.y) + yScale(comfortLow.y)) / 2} fill={t.ink} fontSize={14} fontWeight={700} textAnchor="middle" dominantBaseline="central" {...halo}>
        {COMFORT_KEY}
      </text>

      {labels.map((l) => {
        const x = xScale(l.x);
        const y = yScale(l.y);
        const place = {
          start: { x: x - 6, y: y - 6, anchor: "end" },
          right: { x: left + width + 6, y: rightLabelY.get(l.id), anchor: "start" },
          top: { x, y: top - 8, anchor: "middle" },
          bottom: { x: x + 5, y: top + height - 8, anchor: "start" },
        }[l.side];
        return (
          <text key={l.id} x={place.x} y={place.y} fill={l.color} fontSize={14} fontWeight={700} textAnchor={place.anchor} {...halo}>
            {l.text}
          </text>
        );
      })}

      <line x1={p1.x} y1={p1.y} x2={p2.x - 14 * Math.cos(angle)} y2={p2.y - 14 * Math.sin(angle)} stroke={PROCESS_COLOR} strokeWidth={3.5} strokeLinecap="round" />
      <path d="M 0 0 L -18 -9 L -18 9 Z" transform={`translate(${p2.x},${p2.y}) rotate(${(angle * 180) / Math.PI})`} fill={PROCESS_COLOR} />
      {[p1, p2].map((p, i) => (
        <g key={i}>
          <circle cx={p.x} cy={p.y} r={6.5} fill={PROCESS_COLOR} stroke={t.pageBg} strokeWidth={2} />
          <text x={p.x} y={p.y + (i === 0 ? -14 : 26)} fill={PROCESS_COLOR} fontSize={15} fontWeight={700} textAnchor="middle" {...halo}>
            {i + 1}
          </text>
        </g>
      ))}
      <text x={p1.x + 14} y={p1.y + 5} fill={PROCESS_COLOR} fontSize={15} fontWeight={700} textAnchor="start" {...halo}>
        {PROCESS.name}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <div style={{ height: KEY_H, display: "flex", alignItems: "center", justifyContent: "center", gap: 22, fontSize: 14, color: t.inkSoft }}>
        {KEY_ITEMS.map((k) => (
          <span key={k.text} style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <svg width={30} height={10}>
              <line x1={1} y1={5} x2={29} y2={5} stroke={k.color} strokeWidth={k.width} strokeDasharray={k.dash} />
            </svg>
            {k.text}
          </span>
        ))}
        <span style={{ display: "flex", alignItems: "center", gap: 7 }}>
          <span style={{ width: 22, height: 14, background: t.grid, border: `1.5px dashed ${t.inkSoft}` }} />
          {COMFORT_KEY}
        </span>
      </div>
      <LineChart
        width={width}
        height={height - TITLE_H - SUBTITLE_H - KEY_H}
        margin={MARGIN}
        skipAnimation
        hideLegend
        disableAxisListener
        grid={{ horizontal: true, vertical: true }}
        series={lines.map((line) => ({
          id: line.id,
          data: line.w,
          color: FAMILY[line.family].color,
          curve: "linear",
          showMark: false,
          disableHighlight: true,
        }))}
        xAxis={[
          {
            data: temps,
            scaleType: "linear",
            min: DRY_BULB_MIN,
            max: DRY_BULB_MAX,
            label: X_LABEL,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: HUMIDITY_MAX,
            label: Y_LABEL,
            width: 72,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiLineChart-line[data-series^='rh-']": { strokeWidth: FAMILY.rh.width },
          [`& .MuiLineChart-line[data-series='rh-${SATURATION_RH}']`]: { strokeWidth: 3.6 },
          "& .MuiLineChart-line[data-series^='wb-']": { strokeWidth: FAMILY.wb.width, strokeDasharray: FAMILY.wb.dash },
          "& .MuiLineChart-line[data-series^='h-']": { strokeWidth: FAMILY.h.width, strokeDasharray: FAMILY.h.dash },
          "& .MuiLineChart-line[data-series^='v-']": { strokeWidth: FAMILY.v.width, strokeDasharray: FAMILY.v.dash },
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <Overlays />
      </LineChart>
    </div>
  );
}
