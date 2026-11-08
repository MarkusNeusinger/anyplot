// anyplot.ai
// area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08
//# anyplot-orientation: landscape

import { LineChart } from "@mui/x-charts/LineChart";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "area-mountain-panorama · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const Y_PAD_SHARE = 0.06; // room below the lowest skyline sample, as a share of the elevation range
const LABEL_HEADROOM_SHARE = 0.28; // sky above the highest summit for the label shelves
const SILHOUETTE_SHADE = 0.32; // the silhouette fill is the brand green darkened to this share of its brightness
const Y_TICK_TARGET = 15; // about this many tick steps across the whole elevation axis
const SHELF_H = 44; // vertical step between label shelves (px)
const LABEL_GAP_PX = 16; // minimum clear space between two labels on one shelf
const CHAR_W_PX = 8.6; // approximate width of one 15 px bold label character
const CHAR_W_ANCHOR_PX = 10; // the same at the anchor summit's 17 px

// Columns: set these to your data's column names
const BEARING = "Bearing (°)"; // role: angle_deg
const ELEVATION = "Elevation (m)"; // role: elevation_m
// A name on a sample marks a summit whose apex is that sample's bearing and elevation
const PEAK = "Peak"; // role: peaks
const ANCHOR = "Anchor summit"; // role: extra
const BACKDROP = "Background ridge (m)"; // role: extra

// Data: replace this block with your own records, one object per row
// Wallis (Valais) panorama from the Gornergrat ridge, anchored on the Matterhorn.
// Each ridge is built from control points (col, apex, col per summit, flank widths
// and saddle depths varied per peak) and roughened by midpoint displacement whose
// jitter scales with each segment's span, so apexes stay sharp while long saddles
// pick up notches. A lower, hazier background ridge, which rises behind the front
// ridge's saddles, is resampled onto the same bearings. Seeded mulberry32, since
// the browser has no seeded random generator.
const data = (() => {
  const peaks = [
    { name: "Weisshorn", angle: -62, elev: 4506 },
    { name: "Zinalrothorn", angle: -54, elev: 4221 },
    { name: "Ober Gabelhorn", angle: -47, elev: 4063 },
    { name: "Dent Blanche", angle: -39, elev: 4358 },
    { name: "Matterhorn", angle: -28, elev: 4478 },
    { name: "Dom", angle: -14, elev: 4545 },
    { name: "Täschhorn", angle: -6, elev: 4491 },
    { name: "Alphubel", angle: 3, elev: 4206 },
    { name: "Allalinhorn", angle: 11, elev: 4027 },
    { name: "Rimpfischhorn", angle: 19, elev: 4199 },
    { name: "Strahlhorn", angle: 27, elev: 4190 },
    { name: "Breithorn", angle: 36, elev: 4164 },
    { name: "Pollux", angle: 44, elev: 4092 },
    { name: "Castor", angle: 50, elev: 4223 },
    { name: "Liskamm", angle: 57, elev: 4527 },
    { name: "Monte Rosa", angle: 64, elev: 4634 },
  ];
  const anchor = "Matterhorn";
  const baseline = 2650; // valley-floor elevation at the panorama's flat edges
  const xMin = peaks[0].angle - 11;
  const xMax = peaks[peaks.length - 1].angle + 11;

  const [front, back] = [
    { summits: peaks, seed: 20260820, prominence: [380, 620], depth: 5, amp: 40, persistence: 0.58 },
    {
      summits: peaks.map((p) => ({ angle: p.angle + 4, elev: baseline + (p.elev - baseline) * 0.88 })),
      seed: 777,
      prominence: [200, 520],
      depth: 4,
      amp: 26,
      persistence: 0.55,
    },
  ].map(({ summits, seed, prominence, depth, amp, persistence }) => {
    let state = seed;
    const rng = () => {
      state |= 0;
      state = (state + 0x6d2b79f5) | 0;
      let x = Math.imul(state ^ (state >>> 15), 1 | state);
      x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
      return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
    };
    let pts = [{ angle: xMin, elev: baseline }];
    summits.forEach((p, i) => {
      const prevAngle = i === 0 ? xMin : summits[i - 1].angle;
      const nextAngle = i === summits.length - 1 ? xMax : summits[i + 1].angle;
      const widthBefore = Math.min(1.4 + rng() * 3.8, (p.angle - prevAngle) * 0.42);
      const widthAfter = Math.min(1.4 + rng() * 3.8, (nextAngle - p.angle) * 0.42);
      const drop = prominence[0] + rng() * (prominence[1] - prominence[0]);
      const colElev = Math.max(baseline, p.elev - drop);
      pts.push({ angle: p.angle - widthBefore, elev: colElev + (rng() - 0.5) * 90 });
      pts.push({ angle: p.angle, elev: p.elev });
      pts.push({ angle: p.angle + widthAfter, elev: colElev + (rng() - 0.5) * 90 });
    });
    pts.push({ angle: xMax, elev: baseline });
    let jitterAmp = amp;
    for (let d = 0; d < depth; d += 1) {
      const next = [pts[0]];
      for (let i = 0; i < pts.length - 1; i += 1) {
        const a = pts[i];
        const b = pts[i + 1];
        const jitter = (rng() - 0.5) * 2 * jitterAmp * (b.angle - a.angle);
        next.push({ angle: (a.angle + b.angle) / 2, elev: Math.max(baseline - 40, (a.elev + b.elev) / 2 + jitter) });
        next.push(b);
      }
      pts = next;
      jitterAmp *= persistence;
    }
    return pts;
  });

  return front.map(({ angle, elev }) => {
    let j = 0;
    while (j < back.length - 2 && back[j + 1].angle <= angle) j += 1;
    const f = Math.max(0, Math.min(1, (angle - back[j].angle) / (back[j + 1].angle - back[j].angle)));
    const peak = peaks.find((p) => p.angle === angle);
    return {
      [BEARING]: Number(angle.toFixed(3)),
      [ELEVATION]: Math.round(elev),
      [PEAK]: peak ? peak.name : null,
      [ANCHOR]: peak ? peak.name === anchor : false,
      [BACKDROP]: Math.round(back[j].elev + (back[j + 1].elev - back[j].elev) * f),
    };
  });
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[BEARING] - b[BEARING]);
const bearings = rows.map((d) => d[BEARING]);
const skyline = rows.map((d) => d[ELEVATION]);
const backdrop = rows.map((d) => d[BACKDROP]);
const peaks = rows.filter((d) => d[PEAK]);
const anchorIdx = peaks.findIndex((d) => d[ANCHOR]);

const known = [...skyline, ...backdrop].filter((v) => v != null);
const elevMin = Math.min(...known);
const elevMax = Math.max(...known);
const elevSpan = elevMax - elevMin || 1;
const yLo = elevMin - Y_PAD_SHARE * elevSpan;
const yHi = elevMax + LABEL_HEADROOM_SHARE * elevSpan;

// Round tick step from the axis range; ticks and grid stop at the highest summit
// so the label sky stays clear
const rawStep = (yHi - yLo) / Y_TICK_TARGET;
const stepMag = 10 ** Math.floor(Math.log10(rawStep));
const yStep = ([1, 2, 2.5, 5, 10].find((m) => m * stepMag >= rawStep) ?? 10) * stepMag;
const yTicks: number[] = [];
for (let v = Math.ceil(yLo / yStep) * yStep; v <= elevMax; v += yStep) yTicks.push(v);

const BEARING_UNIT = BEARING.match(/\(([^)]+)\)/)?.[1] ?? "";
const ELEV_UNIT = ELEVATION.match(/\(([^)]+)\)/)?.[1] ?? "";
const fmtElev = (v: number) => `${Math.round(v).toLocaleString("en-US")} ${ELEV_UNIT}`.trim();
// Dusk silhouette: a deep shade of the brand green, the same in both themes, outlined
// in the full brand green so the ridgeline still stands out against the dark page
const silhouette = `#${(t.palette[0] as string)
  .slice(1)
  .match(/../g)!
  .map((c) => Math.round(parseInt(c, 16) * SILHOUETTE_SHADE).toString(16).padStart(2, "0"))
  .join("")}`;
const highest = peaks.reduce((best, d) => (d[ELEVATION] > best[ELEVATION] ? d : best), peaks[0]);

const SUBTITLE = [
  `${peaks.length} named summits`,
  `${Math.round(bearings[bearings.length - 1] - bearings[0])}${BEARING_UNIT} field of view`,
  highest ? `highest: ${highest[PEAK]}, ${fmtElev(highest[ELEVATION])}` : null,
]
  .filter(Boolean)
  .join(" · ");

// Summit labels on shelves in the sky: as many shelves as it takes for labels that
// share one to clear each other, then each leader line drops to its apex
function PeakLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { top } = useDrawingArea();

  const xs = peaks.map((d) => xScale(d[BEARING]));
  const widths = peaks.map((d, i) => String(d[PEAK]).length * (i === anchorIdx ? CHAR_W_ANCHOR_PX : CHAR_W_PX));
  let shelves = 1;
  while (
    shelves < peaks.length &&
    xs.some((x, i) => i + shelves < xs.length && xs[i + shelves] - x < (widths[i] + widths[i + shelves]) / 2 + LABEL_GAP_PX)
  ) {
    shelves += 1;
  }

  return (
    <g>
      {peaks.map((d, i) => {
        const isAnchor = i === anchorIdx;
        const x = xs[i];
        const apexY = yScale(d[ELEVATION]);
        const labelY = top + 18 + (i % shelves) * SHELF_H;
        return (
          <g key={`${d[PEAK]}-${d[BEARING]}`}>
            <line
              x1={x}
              x2={x}
              y1={labelY + 26}
              y2={apexY - (isAnchor ? 8 : 5)}
              stroke={isAnchor ? t.ink : t.inkSoft}
              strokeWidth={isAnchor ? 2 : 1}
              strokeOpacity={isAnchor ? 0.9 : 0.6}
            />
            <circle
              cx={x}
              cy={apexY}
              r={isAnchor ? 6 : 3.5}
              fill={t.palette[0]}
              stroke={isAnchor ? t.ink : t.pageBg}
              strokeWidth={isAnchor ? 2 : 1.5}
            />
            <text
              x={x}
              y={labelY}
              textAnchor="middle"
              fontSize={isAnchor ? 17 : 15}
              fontWeight={isAnchor ? 800 : 700}
              fill={t.ink}
            >
              {d[PEAK]}
            </text>
            <text
              x={x}
              y={labelY + 18}
              textAnchor="middle"
              fontSize={isAnchor ? 15 : 14}
              fontWeight={isAnchor ? 700 : 400}
              fill={t.inkSoft}
            >
              {fmtElev(d[ELEVATION])}
            </text>
          </g>
        );
      })}
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
            data: bearings,
            scaleType: "linear",
            min: bearings[0],
            max: bearings[bearings.length - 1],
            label: BEARING,
            position: "none",
          },
        ]}
        yAxis={[
          {
            label: ELEVATION,
            min: yLo,
            max: yHi,
            width: 84,
            tickInterval: yTicks,
            valueFormatter: (v: number) => v.toLocaleString("en-US"),
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "haze",
            data: backdrop,
            label: BACKDROP,
            color: t.inkSoft,
            area: true,
            baseline: "min",
            showMark: false,
            curve: "linear",
          },
          {
            id: "ridge",
            data: skyline,
            label: ELEVATION,
            color: t.palette[0],
            area: true,
            baseline: "min",
            showMark: false,
            curve: "linear",
          },
        ]}
        margin={{ top: 12, right: 40, bottom: 24, left: 24 }}
        sx={{
          '& .MuiLineChart-area[data-series="haze"]': { fillOpacity: 0.22 },
          // lines are drawn above every area, so the haze keeps no outline across the front ridge
          '& .MuiLineChart-line[data-series="haze"]': { display: "none" },
          // MUI brightens area fills by default; the silhouette keeps its dark solid fill
          '& .MuiLineChart-area[data-series="ridge"]': { fill: silhouette, fillOpacity: 1, filter: "none" },
          '& .MuiLineChart-line[data-series="ridge"]': { strokeWidth: 2.5 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <PeakLabels />
      </LineChart>
    </Box>
  );
}
