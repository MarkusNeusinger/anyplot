// anyplot.ai
// stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 89/100 | Updated: 2026-11-08
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const NET_STEP_DEG = 10; // Schmidt net graticule spacing
const TICK_STEP_DEG = 10; // perimeter tick marks
const LABEL_STEP_DEG = 30; // labelled perimeter azimuths
const KAMB_SIGMA = 3; // Kamb counting area expected count, in standard deviations
const KAMB_MAX_LEVELS = 5; // contour levels are even multiples of sigma, at most this many
const DENSITY_GRID = 80; // density nodes across the net diameter
const CURVE_STEPS = 120; // points per projected great or small circle
const NET_LIMIT = 1.15; // drawing extent in primitive radii, room for the perimeter labels
const PLANE_ARC_OPACITY = 0.28; // each plane's own great circle, faint behind the poles and the bold mean
const CARDINALS = ["N", "E", "S", "W"];

// Columns: set these to your data's column names
const DIP = "Dip (°)"; // role: dip
const DIP_DIRECTION = "Dip direction (°)"; // role: dip_direction
const FEATURE = "Feature type"; // role: feature_type

// Data: replace this block with your own records, one object per row
// Field measurements from a mapping campaign: four fabric elements, each a
// clustered orientation population (normal scatter about a mean plane)
const data = (() => {
  let seed = 20260616 >>> 0;
  const rand = () => {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const randn = () => {
    let u = 0;
    while (u === 0) u = rand();
    const v = rand();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  };
  const populations = [
    { name: "Bedding", n: 46, dip: 24, dipDir: 118, sDip: 6, sDir: 14 },
    { name: "Joint set", n: 38, dip: 78, dipDir: 48, sDip: 5, sDir: 10 },
    { name: "Foliation", n: 34, dip: 62, dipDir: 305, sDip: 7, sDir: 12 },
    { name: "Fault", n: 26, dip: 54, dipDir: 212, sDip: 6, sDir: 11 },
  ];
  const rows: Record<string, string | number>[] = [];
  for (const p of populations) {
    for (let i = 0; i < p.n; i += 1) {
      const dip = Math.max(2, Math.min(89, p.dip + randn() * p.sDip));
      const dipDir = (((p.dipDir + randn() * p.sDir) % 360) + 360) % 360;
      rows.push({ [DIP]: Number(dip.toFixed(1)), [DIP_DIRECTION]: Number(dipDir.toFixed(1)), [FEATURE]: p.name });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
// Lower-hemisphere Lambert equal-area (Schmidt) net, North up, East right: a line
// of plunge p and trend a lands at radius sqrt(2)·sin((90° − p) / 2) along azimuth a,
// so the horizon is the primitive circle (radius 1) and the vertical is the centre.
const RAD = Math.PI / 180;
const rows = data.filter((d) => d[DIP] != null && d[DIP_DIRECTION] != null && d[FEATURE] != null);
const features = [...new Set(rows.map((d) => d[FEATURE] as string))];
const azUnit = DIP_DIRECTION.match(/\(([^)]+)\)/)?.[1] ?? "";

// Poles: the normal of a plane plunges 90° − dip toward dip direction + 180°
const poleRows = rows.map((d) => {
  const dip = (d[DIP] as number) * RAD;
  const trend = ((d[DIP_DIRECTION] as number) + 180) * RAD;
  const plunge = Math.PI / 2 - dip;
  const r = Math.SQRT2 * Math.sin(dip / 2);
  return {
    feature: d[FEATURE] as string,
    x: r * Math.sin(trend),
    y: r * Math.cos(trend),
    vec: [Math.cos(plunge) * Math.cos(trend), Math.cos(plunge) * Math.sin(trend), Math.sin(plunge)],
  };
});

// Each plane's own great circle: its lines run from strike to strike, plunging by the
// apparent dip atan(tan(dip) · cos(trend − dip direction))
const planeArcs = rows.map((d) => {
  const dip = (d[DIP] as number) * RAD;
  const dipDir = (d[DIP_DIRECTION] as number) * RAD;
  const pts = Array.from({ length: CURVE_STEPS + 1 }, (_, k) => {
    const trend = dipDir - Math.PI / 2 + (k * Math.PI) / CURVE_STEPS;
    const apparent = Math.atan(Math.tan(dip) * Math.cos(trend - dipDir));
    const r = Math.SQRT2 * Math.sin((Math.PI / 2 - apparent) / 2);
    return { x: r * Math.sin(trend), y: r * Math.cos(trend) };
  });
  return { color: t.palette[features.indexOf(d[FEATURE] as string)], pts };
});

// Mean plane per feature: the normalised sum of its pole axes, each turned to agree with the first
const meanPlanes = features.map((feature, i) => {
  const vecs = poleRows.filter((p) => p.feature === feature).map((p) => p.vec);
  const sum = [0, 0, 0];
  for (const v of vecs) {
    const sign = v[0] * vecs[0][0] + v[1] * vecs[0][1] + v[2] * vecs[0][2] < 0 ? -1 : 1;
    sum[0] += sign * v[0];
    sum[1] += sign * v[1];
    sum[2] += sign * v[2];
  }
  const len = Math.hypot(sum[0], sum[1], sum[2]);
  const down = sum[2] < 0 ? -1 : 1;
  const plunge = Math.asin((down * sum[2]) / len);
  const dip = Math.PI / 2 - plunge;
  const dipDir = Math.atan2(down * sum[1], down * sum[0]) + Math.PI;
  const pts = Array.from({ length: CURVE_STEPS + 1 }, (_, k) => {
    const trend = dipDir - Math.PI / 2 + (k * Math.PI) / CURVE_STEPS;
    const apparent = Math.atan(Math.tan(dip) * Math.cos(trend - dipDir));
    const r = Math.SQRT2 * Math.sin((Math.PI / 2 - apparent) / 2);
    return { x: r * Math.sin(trend), y: r * Math.cos(trend) };
  });
  return { feature, color: t.palette[i], pts };
});

// Net graticule: N-S striking great circles every NET_STEP_DEG of dip, and small circles about the N-S axis
const netCurves: { x: number; y: number }[][] = [];
for (let deg = NET_STEP_DEG; deg < 90; deg += NET_STEP_DEG) {
  for (const dipDir of [90 * RAD, 270 * RAD]) {
    netCurves.push(
      Array.from({ length: CURVE_STEPS + 1 }, (_, k) => {
        const trend = dipDir - Math.PI / 2 + (k * Math.PI) / CURVE_STEPS;
        const apparent = Math.atan(Math.tan(deg * RAD) * Math.cos(trend - dipDir));
        const r = Math.SQRT2 * Math.sin((Math.PI / 2 - apparent) / 2);
        return { x: r * Math.sin(trend), y: r * Math.cos(trend) };
      }),
    );
  }
}
for (let deg = NET_STEP_DEG; deg < 180; deg += NET_STEP_DEG) {
  if (deg === 90) continue;
  netCurves.push(
    Array.from({ length: CURVE_STEPS + 1 }, (_, k) => {
      const phi = (k * Math.PI) / CURVE_STEPS;
      const north = Math.cos(deg * RAD);
      const east = Math.sin(deg * RAD) * Math.cos(phi);
      const plunge = Math.asin(Math.sin(deg * RAD) * Math.sin(phi));
      const trend = Math.atan2(east, north);
      const r = Math.SQRT2 * Math.sin((Math.PI / 2 - plunge) / 2);
      return { x: r * Math.sin(trend), y: r * Math.cos(trend) };
    }),
  );
}

// Kamb density (exponential kernel, Vollmer 1995) on a grid over the net, in units of sigma.
// A node beyond the primitive maps onto the upper hemisphere (the equal-area projection
// reaches the zenith at radius √2), where the axial density equals that of the antipode
// just inside the opposite rim, so contours cross the rim and the clip cuts them there.
const nPoles = poleRows.length;
const kambK = 2 * (1 + nPoles / KAMB_SIGMA ** 2);
const kambUnit = Math.sqrt((nPoles * (kambK / 2 - 1)) / kambK ** 2);
const gridStep = 2 / (DENSITY_GRID - 1);
const density = new Float64Array(DENSITY_GRID * DENSITY_GRID);
for (let j = 0; j < DENSITY_GRID; j += 1) {
  for (let i = 0; i < DENSITY_GRID; i += 1) {
    const gx = -1 + i * gridStep;
    const gy = -1 + j * gridStep;
    const r = Math.min(Math.hypot(gx, gy), Math.SQRT2);
    const theta = 2 * Math.asin(r / Math.SQRT2);
    const az = Math.atan2(gx, gy);
    const node = [Math.sin(theta) * Math.cos(az), Math.sin(theta) * Math.sin(az), Math.cos(theta)];
    let sum = 0;
    for (const p of poleRows) {
      const cos = Math.abs(node[0] * p.vec[0] + node[1] * p.vec[1] + node[2] * p.vec[2]);
      sum += Math.exp(kambK * (cos - 1));
    }
    density[j * DENSITY_GRID + i] = (sum - 0.5) / kambUnit;
  }
}
const maxSigma = density.reduce((m, v) => (v > m ? v : m), 0);
const levelStep = 2 * Math.max(1, Math.ceil(maxSigma / (2 * KAMB_MAX_LEVELS)));
const levels: number[] = [];
for (let level = levelStep; level < maxSigma; level += levelStep) levels.push(level);

// Marching squares: per corner code, the cell edges a segment joins (0 bottom, 1 right, 2 top, 3 left)
const SEGMENT_EDGES = [
  [], [[3, 0]], [[0, 1]], [[3, 1]], [[1, 2]], [[3, 2], [0, 1]], [[0, 2]], [[3, 2]],
  [[3, 2]], [[0, 2]], [[3, 0], [1, 2]], [[1, 2]], [[3, 1]], [[0, 1]], [[3, 0]], [],
];
const CORNERS = [[0, 0], [1, 0], [1, 1], [0, 1]];
const contours = levels.map((level, k) => {
  const segs: number[][] = [];
  for (let j = 0; j < DENSITY_GRID - 1; j += 1) {
    for (let i = 0; i < DENSITY_GRID - 1; i += 1) {
      const vals = CORNERS.map(([di, dj]) => density[(j + dj) * DENSITY_GRID + i + di]);
      const code = vals.reduce((c, v, q) => c | (v >= level ? 1 << q : 0), 0);
      for (const pair of SEGMENT_EDGES[code]) {
        const ends = pair.map((edge) => {
          const a = edge;
          const b = (edge + 1) % 4;
          const f = (level - vals[a]) / (vals[b] - vals[a]);
          return [
            -1 + (i + CORNERS[a][0] + f * (CORNERS[b][0] - CORNERS[a][0])) * gridStep,
            -1 + (j + CORNERS[a][1] + f * (CORNERS[b][1] - CORNERS[a][1])) * gridStep,
          ];
        });
        segs.push([ends[0][0], ends[0][1], ends[1][0], ends[1][1]]);
      }
    }
  }
  return { level, segs, width: 1.2 + k * 0.5, opacity: 0.45 + (0.5 * k) / Math.max(1, levels.length - 1) };
});

const perimeterTicks = Array.from({ length: 360 / TICK_STEP_DEG }, (_, k) => k * TICK_STEP_DEG);
const scatterSeries = features.map((feature, i) => ({
  type: "scatter" as const,
  id: `poles-${i}`,
  label: feature,
  color: t.palette[i],
  markerSize: 5,
  data: poleRows.filter((p) => p.feature === feature).map((p, k) => ({ x: p.x, y: p.y, id: `${i}-${k}` })),
}));

const TITLE = "stereonet-equal-area · javascript · muix · anyplot.ai";
const SUBTITLE = `n = ${nPoles} planes · lower-hemisphere equal-area (Schmidt) net · great circles and poles, each feature's mean bold · Kamb contours every ${levelStep}σ`;
const HEADER_H = 76;
const LEGEND_H = 52;
const MARGIN = 10;
const CLIP_ID = "stereonet-primitive";

// Graticule, primitive circle, density contours and mean great circles, below the poles
function NetLayer() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  const cx = xs(0);
  const cy = ys(0);
  const unit = xs(1) - xs(0);
  return (
    <g>
      <defs>
        <clipPath id={CLIP_ID}>
          <circle cx={cx} cy={cy} r={unit} />
        </clipPath>
      </defs>
      {netCurves.map((pts, k) => (
        <path
          key={`net-${k}`}
          d={`M${pts.map((p) => `${xs(p.x)} ${ys(p.y)}`).join(" L")}`}
          fill="none"
          stroke={t.grid}
          strokeWidth={1}
        />
      ))}
      <line x1={xs(-1)} y1={cy} x2={xs(1)} y2={cy} stroke={t.grid} strokeWidth={1} />
      <line x1={cx} y1={ys(-1)} x2={cx} y2={ys(1)} stroke={t.grid} strokeWidth={1} />
      {planeArcs.map((arc, k) => (
        <path
          key={`arc-${k}`}
          d={`M${arc.pts.map((p) => `${xs(p.x)} ${ys(p.y)}`).join(" L")}`}
          fill="none"
          stroke={arc.color}
          strokeWidth={1}
          strokeOpacity={PLANE_ARC_OPACITY}
        />
      ))}
      <g clipPath={`url(#${CLIP_ID})`}>
        {contours.map((c) => (
          <path
            key={`kamb-${c.level}`}
            d={c.segs.map((s) => `M${xs(s[0])} ${ys(s[1])} L${xs(s[2])} ${ys(s[3])}`).join(" ")}
            fill="none"
            stroke={t.ink}
            strokeWidth={c.width}
            strokeOpacity={c.opacity}
            strokeLinecap="round"
          />
        ))}
      </g>
      {meanPlanes.map((mp) => (
        <path
          key={`plane-${mp.feature}`}
          d={`M${mp.pts.map((p) => `${xs(p.x)} ${ys(p.y)}`).join(" L")}`}
          fill="none"
          stroke={mp.color}
          strokeWidth={3.5}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ))}
      <circle cx={cx} cy={cy} r={unit} fill="none" stroke={t.ink} strokeWidth={2.5} />
    </g>
  );
}

// Perimeter ticks every TICK_STEP_DEG, azimuth labels and the cardinal points
function PerimeterLayer() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  return (
    <g>
      {perimeterTicks.map((deg) => {
        const a = deg * RAD;
        const major = deg % LABEL_STEP_DEG === 0;
        const outer = major ? 1.035 : 1.02;
        const cardinal = deg % 90 === 0;
        return (
          <g key={`tick-${deg}`}>
            <line
              x1={xs(Math.sin(a))}
              y1={ys(Math.cos(a))}
              x2={xs(outer * Math.sin(a))}
              y2={ys(outer * Math.cos(a))}
              stroke={t.inkSoft}
              strokeWidth={major ? 1.6 : 1}
            />
            {major && (
              <text
                x={xs((cardinal ? 1.085 : 1.09) * Math.sin(a))}
                y={ys((cardinal ? 1.085 : 1.09) * Math.cos(a))}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={cardinal ? 24 : 15}
                fontWeight={cardinal ? 700 : 400}
                fill={cardinal ? t.ink : t.inkSoft}
              >
                {cardinal ? CARDINALS[deg / 90] : `${deg}${azUnit}`}
              </text>
            )}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width: W, height: H } = window.ANYPLOT_SIZE;
  const chartH = H - HEADER_H - LEGEND_H;
  const side = Math.min(W, chartH) - 2 * MARGIN;
  const hMargin = (W - side) / 2;
  const vMargin = (chartH - side) / 2;
  const swatch = { display: "inline-block", width: 28, height: 0, verticalAlign: "middle" };

  return (
    <div style={{ width: W, height: H, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={W}
        height={chartH}
        skipAnimation
        margin={{ top: vMargin, bottom: vMargin, left: hMargin, right: hMargin }}
        series={scatterSeries}
        xAxis={[{ id: "x", min: -NET_LIMIT, max: NET_LIMIT, position: "none" }]}
        yAxis={[{ id: "y", min: -NET_LIMIT, max: NET_LIMIT, position: "none" }]}
      >
        <NetLayer />
        <ScatterPlot />
        <PerimeterLayer />
        <ChartsTooltip trigger="item" />
      </ChartsContainer>
      <div
        style={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 32,
          fontSize: 15,
          color: t.inkSoft,
        }}
      >
        {meanPlanes.map((mp) => (
          <span key={mp.feature} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 12, height: 12, borderRadius: "50%", background: mp.color }} />
            <span style={{ ...swatch, borderTop: `3.5px solid ${mp.color}` }} />
            {mp.feature}
          </span>
        ))}
        <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ ...swatch, borderTop: `2px solid ${t.ink}` }} />
          {`Kamb density, ${levels.map((l) => `${l}σ`).join(" / ")}`}
        </span>
      </div>
    </div>
  );
}
