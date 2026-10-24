// anyplot.ai
// map-projections: World Map with Different Projections
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-08-26

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "map-projections · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;
const FOOTER_HEIGHT = 44;
const PANEL_HEADER_HEIGHT = 68;
const PANEL_FOOTER_HEIGHT = 36;
const PANEL_GAP = 16;
const OUTER_PAD_X = 24;
const DEG2RAD = Math.PI / 180;
const RAD2DEG = 180 / Math.PI;
const SQRT2 = Math.SQRT2;
const MERCATOR_LAT_CLIP = 82;
const ORTHO_LON0 = 0;
const ORTHO_LAT0 = 20;
const TISSOT_RADIUS_KM = 550;
const EARTH_RADIUS_KM = 6371;
const TISSOT_RADIUS_RAD = TISSOT_RADIUS_KM / EARTH_RADIUS_KM;
const TISSOT_STEPS = 48;
const GRATICULE_STEP_DEG = 30;
const DOMAIN_PAD_SHARE = 0.04;

// Columns: set these to your data's column names
const FEATURE_KIND = "Feature kind"; // role: kind
const FEATURE_NAME = "Country / landmass"; // role: country
const VERTICES = "Boundary coordinates (lon, lat)"; // role: coordinates

// Data: replace this block with your own records
const PROJECTIONS = [
  {
    id: "Mercator",
    title: "Mercator (Cylindrical)",
    subtitle: "Conformal — angles preserved",
    note: "Area inflates as sec²(φ) toward the poles",
  },
  {
    id: "Mollweide",
    title: "Mollweide (Pseudocylindrical)",
    subtitle: "Equal-area — true relative size",
    note: "Shapes shear near the outer limb",
  },
  {
    id: "Orthographic",
    title: "Orthographic (Azimuthal)",
    subtitle: `Globe view centered at ${ORTHO_LAT0}°N, ${ORTHO_LON0}°E`,
    note: "Foreshortened to zero at the horizon",
  },
];

const data: Array<{
  [FEATURE_KIND]: "continent" | "border";
  [FEATURE_NAME]: string;
  [VERTICES]: Array<[number, number]>;
}> = [
  {
    [FEATURE_KIND]: "continent",
    [FEATURE_NAME]: "North America",
    [VERTICES]: [
      [-168, 65], [-160, 70], [-140, 70], [-125, 72], [-95, 74], [-80, 70], [-65, 62],
      [-55, 52], [-60, 46], [-70, 42], [-76, 35], [-81, 25], [-90, 21], [-88, 16],
      [-83, 10], [-78, 8], [-85, 11], [-92, 15], [-97, 19], [-105, 20], [-110, 24],
      [-117, 32], [-122, 37], [-124, 48], [-135, 58], [-150, 60], [-162, 55], [-168, 65],
    ],
  },
  {
    [FEATURE_KIND]: "continent",
    [FEATURE_NAME]: "Greenland",
    [VERTICES]: [
      [-52, 60], [-44, 60], [-22, 70], [-18, 77], [-30, 83], [-55, 82], [-68, 76],
      [-56, 68], [-52, 60],
    ],
  },
  {
    [FEATURE_KIND]: "continent",
    [FEATURE_NAME]: "South America",
    [VERTICES]: [
      [-78, 9], [-72, 12], [-62, 10], [-50, 2], [-35, -6], [-38, -15], [-40, -22],
      [-48, -28], [-54, -34], [-62, -40], [-66, -48], [-68, -55], [-74, -52], [-73, -42],
      [-71, -30], [-70, -18], [-76, -12], [-81, -5], [-79, 2], [-78, 9],
    ],
  },
  {
    [FEATURE_KIND]: "continent",
    [FEATURE_NAME]: "Europe",
    [VERTICES]: [
      [-10, 36], [-9, 43], [-2, 44], [-5, 48], [2, 51], [8, 55], [10, 58], [5, 62],
      [15, 68], [28, 71], [42, 68], [58, 68], [60, 55], [48, 46], [38, 45], [29, 41],
      [26, 38], [22, 37], [18, 40], [15, 38], [12, 42], [8, 44], [3, 42], [-2, 37],
      [-6, 36], [-10, 36],
    ],
  },
  {
    [FEATURE_KIND]: "continent",
    [FEATURE_NAME]: "Great Britain",
    [VERTICES]: [[-6, 50], [-5, 58], [-2, 58], [1, 52], [-6, 50]],
  },
  {
    [FEATURE_KIND]: "continent",
    [FEATURE_NAME]: "Africa",
    [VERTICES]: [
      [-17, 15], [-13, 28], [-6, 35], [10, 37], [25, 32], [33, 31], [38, 22], [43, 12],
      [51, 12], [45, 2], [40, -10], [35, -22], [28, -33], [18, -35], [14, -22], [12, -6],
      [9, 4], [2, 6], [-8, 5], [-16, 11], [-17, 15],
    ],
  },
  {
    [FEATURE_KIND]: "continent",
    [FEATURE_NAME]: "Madagascar",
    [VERTICES]: [[44, -25], [49, -13], [50, -16], [47, -25], [44, -25]],
  },
  {
    [FEATURE_KIND]: "continent",
    [FEATURE_NAME]: "Asia",
    [VERTICES]: [
      [28, 41], [40, 42], [50, 40], [58, 55], [60, 68], [75, 73], [105, 76], [140, 73],
      [175, 66], [170, 60], [155, 52], [142, 50], [135, 38], [128, 36], [122, 31],
      [118, 23], [108, 21], [105, 10], [102, 2], [98, 8], [92, 21], [88, 22], [80, 10],
      [76, 8], [72, 20], [67, 24], [58, 25], [55, 22], [48, 14], [43, 13], [38, 22],
      [34, 30], [36, 36], [28, 41],
    ],
  },
  {
    [FEATURE_KIND]: "continent",
    [FEATURE_NAME]: "Japan",
    [VERTICES]: [[130, 31], [136, 35], [141, 41], [145, 44], [141, 38], [134, 33], [130, 31]],
  },
  {
    [FEATURE_KIND]: "continent",
    [FEATURE_NAME]: "Maritime SE Asia",
    [VERTICES]: [[96, 5], [104, -2], [114, -7], [120, -8], [116, -2], [106, 2], [96, 5]],
  },
  {
    [FEATURE_KIND]: "continent",
    [FEATURE_NAME]: "Australia",
    [VERTICES]: [
      [114, -22], [122, -16], [132, -12], [136, -15], [142, -11], [148, -20], [153, -28],
      [150, -37], [140, -38], [132, -32], [122, -34], [115, -34], [114, -22],
    ],
  },
  {
    [FEATURE_KIND]: "continent",
    [FEATURE_NAME]: "New Zealand",
    [VERTICES]: [[166, -46], [172, -41], [178, -37], [175, -42], [168, -46], [166, -46]],
  },
  {
    [FEATURE_KIND]: "continent",
    [FEATURE_NAME]: "Antarctica",
    [VERTICES]: [
      [-179, -72], [-120, -73], [-62, -65], [-58, -74], [-20, -72], [20, -70], [70, -68],
      [120, -67], [179, -71], [179, -82], [120, -82], [60, -82], [0, -82], [-60, -82],
      [-120, -82], [-179, -82], [-179, -72],
    ],
  },
  {
    [FEATURE_KIND]: "border",
    [FEATURE_NAME]: "Canada-US",
    [VERTICES]: [[-124, 49], [-95, 49], [-83, 46], [-75, 45], [-67, 47]],
  },
  {
    [FEATURE_KIND]: "border",
    [FEATURE_NAME]: "US-Mexico",
    [VERTICES]: [[-117, 32], [-106, 31], [-97, 26]],
  },
  {
    [FEATURE_KIND]: "border",
    [FEATURE_NAME]: "Brazil West",
    [VERTICES]: [[-52, 4], [-60, 2], [-70, -4], [-70, -11], [-58, -20], [-54, -33]],
  },
  {
    [FEATURE_KIND]: "border",
    [FEATURE_NAME]: "Andes South",
    [VERTICES]: [[-70, -18], [-68, -27], [-70, -38], [-72, -50]],
  },
  {
    [FEATURE_KIND]: "border",
    [FEATURE_NAME]: "Europe-Russia",
    [VERTICES]: [[28, 70], [30, 60], [38, 50], [40, 44]],
  },
  {
    [FEATURE_KIND]: "border",
    [FEATURE_NAME]: "Sahara South",
    [VERTICES]: [[-16, 15], [0, 15], [15, 14], [32, 12], [43, 12]],
  },
  {
    [FEATURE_KIND]: "border",
    [FEATURE_NAME]: "Egypt-Sudan",
    [VERTICES]: [[25, 31], [25, 22], [36, 22]],
  },
  {
    [FEATURE_KIND]: "border",
    [FEATURE_NAME]: "Equatorial Africa",
    [VERTICES]: [[12, -6], [28, -4], [30, -10], [40, -11]],
  },
  {
    [FEATURE_KIND]: "border",
    [FEATURE_NAME]: "Southern Africa",
    [VERTICES]: [[14, -17], [25, -18], [33, -26]],
  },
  {
    [FEATURE_KIND]: "border",
    [FEATURE_NAME]: "Russia-Kazakhstan-China",
    [VERTICES]: [[50, 46], [68, 52], [87, 49], [105, 50], [120, 50], [134, 48]],
  },
  {
    [FEATURE_KIND]: "border",
    [FEATURE_NAME]: "India-China",
    [VERTICES]: [[67, 25], [75, 35], [88, 28], [97, 28]],
  },
];

// Plot: reads only data and the constants above
interface InputPolyline {
  layer: "continent" | "border" | "graticule" | "equator" | "meridian" | "tissot";
  pts: Array<[number, number]>;
  jumpMax: number;
  minPts: number;
  singleRunOnly: boolean;
  centerLonLat: [number, number] | null;
}

const inputPolylines: InputPolyline[] = [];
for (let i = 0; i < data.length; i++) {
  const row = data[i];
  if (row[FEATURE_KIND] === "continent") {
    inputPolylines.push({
      layer: "continent",
      pts: row[VERTICES],
      jumpMax: 1.8,
      minPts: 3,
      singleRunOnly: false,
      centerLonLat: null,
    });
  } else {
    inputPolylines.push({
      layer: "border",
      pts: row[VERTICES],
      jumpMax: 1.8,
      minPts: 2,
      singleRunOnly: false,
      centerLonLat: null,
    });
  }
}

// Graticules at GRATICULE_STEP_DEG intervals
for (let lat = -60; lat <= 60; lat += GRATICULE_STEP_DEG) {
  if (lat === 0) continue;
  const pts: Array<[number, number]> = [];
  for (let lon = -180; lon <= 180; lon += 3) pts.push([lon, lat]);
  inputPolylines.push({
    layer: "graticule",
    pts,
    jumpMax: 1.6,
    minPts: 2,
    singleRunOnly: false,
    centerLonLat: null,
  });
}
for (let lon = -150; lon <= 150; lon += GRATICULE_STEP_DEG) {
  if (lon === 0) continue;
  const pts: Array<[number, number]> = [];
  for (let lat = -80; lat <= 80; lat += 2) pts.push([lon, lat]);
  inputPolylines.push({
    layer: "graticule",
    pts,
    jumpMax: 1.6,
    minPts: 2,
    singleRunOnly: false,
    centerLonLat: null,
  });
}

// Equator & Prime Meridian
const eqPts: Array<[number, number]> = [];
for (let lon = -180; lon <= 180; lon += 2) eqPts.push([lon, 0]);
inputPolylines.push({
  layer: "equator",
  pts: eqPts,
  jumpMax: 1.6,
  minPts: 2,
  singleRunOnly: false,
  centerLonLat: null,
});

const pmPts: Array<[number, number]> = [];
for (let lat = -82; lat <= 82; lat += 2) pmPts.push([0, lat]);
inputPolylines.push({
  layer: "meridian",
  pts: pmPts,
  jumpMax: 1.6,
  minPts: 2,
  singleRunOnly: false,
  centerLonLat: null,
});

// Tissot indicatrix circles at GRATICULE_STEP_DEG intervals
for (let latC = -60; latC <= 60; latC += GRATICULE_STEP_DEG) {
  for (let lonC = -120; lonC <= 120; lonC += GRATICULE_STEP_DEG * 2) {
    const ring: Array<[number, number]> = [];
    const phi1 = latC * DEG2RAD;
    const lam1 = lonC * DEG2RAD;
    const sinPhi1 = Math.sin(phi1);
    const cosPhi1 = Math.cos(phi1);
    const sinD = Math.sin(TISSOT_RADIUS_RAD);
    const cosD = Math.cos(TISSOT_RADIUS_RAD);
    for (let i = 0; i <= TISSOT_STEPS; i++) {
      const brng = (i / TISSOT_STEPS) * 2 * Math.PI;
      const sinPhi2 = sinPhi1 * cosD + cosPhi1 * sinD * Math.cos(brng);
      const phi2 = Math.asin(Math.max(-1, Math.min(1, sinPhi2)));
      const y = Math.sin(brng) * sinD * cosPhi1;
      const x = cosD - sinPhi1 * Math.sin(phi2);
      const lam2 = lam1 + Math.atan2(y, x);
      const normLon = ((((lam2 * RAD2DEG) + 180) % 360) + 360) % 360 - 180;
      ring.push([normLon, phi2 * RAD2DEG]);
    }
    inputPolylines.push({
      layer: "tissot",
      pts: ring,
      jumpMax: 0.9,
      minPts: 10,
      singleRunOnly: true,
      centerLonLat: [lonC, latC],
    });
  }
}

interface ProjectedBundle {
  id: string;
  title: string;
  subtitle: string;
  note: string;
  boundary: Array<[number, number]>;
  continents: Array<Array<[number, number]>>;
  borders: Array<Array<[number, number]>>;
  graticules: Array<Array<[number, number]>>;
  equator: Array<Array<[number, number]>>;
  primeMeridian: Array<Array<[number, number]>>;
  tissot: Array<Array<[number, number]>>;
  bboxMin: [number, number];
  bboxMax: [number, number];
}

const projectedBundles: ProjectedBundle[] = [];
const sinLat0 = Math.sin(ORTHO_LAT0 * DEG2RAD);
const cosLat0 = Math.cos(ORTHO_LAT0 * DEG2RAD);

for (let pIdx = 0; pIdx < PROJECTIONS.length; pIdx++) {
  const meta = PROJECTIONS[pIdx];
  const projId = meta.id;

  const boundary: Array<[number, number]> = [];
  if (projId === "Mercator") {
    const xMax = Math.PI;
    const yMax = Math.log(Math.tan(Math.PI / 4 + (MERCATOR_LAT_CLIP * DEG2RAD) / 2));
    boundary.push([-xMax, -yMax], [xMax, -yMax], [xMax, yMax], [-xMax, yMax], [-xMax, -yMax]);
  } else if (projId === "Mollweide") {
    const rx = 2 * SQRT2;
    const ry = SQRT2;
    for (let i = 0; i <= 120; i++) {
      const a = (i / 120) * 2 * Math.PI;
      boundary.push([rx * Math.cos(a), ry * Math.sin(a)]);
    }
  } else {
    for (let i = 0; i <= 120; i++) {
      const a = (i / 120) * 2 * Math.PI;
      boundary.push([Math.cos(a), Math.sin(a)]);
    }
  }

  const continents: Array<Array<[number, number]>> = [];
  const borders: Array<Array<[number, number]>> = [];
  const graticules: Array<Array<[number, number]>> = [];
  const equator: Array<Array<[number, number]>> = [];
  const primeMeridian: Array<Array<[number, number]>> = [];
  const tissot: Array<Array<[number, number]>> = [];

  for (let polyIdx = 0; polyIdx < inputPolylines.length; polyIdx++) {
    const poly = inputPolylines[polyIdx];
    if (projId === "Orthographic" && poly.centerLonLat !== null) {
      const lamC = (poly.centerLonLat[0] - ORTHO_LON0) * DEG2RAD;
      const phiC = poly.centerLonLat[1] * DEG2RAD;
      const cosCC = sinLat0 * Math.sin(phiC) + cosLat0 * Math.cos(phiC) * Math.cos(lamC);
      if (cosCC < 0) continue;
    }

    const runs: Array<Array<[number, number]>> = [];
    let cur: Array<[number, number]> = [];
    let prevLon: number | null = null;

    for (let i = 0; i < poly.pts.length; i++) {
      const [lon, lat] = poly.pts[i];
      if (prevLon !== null && Math.abs(lon - prevLon) > 170) {
        if (cur.length > 1) runs.push(cur);
        cur = [];
      }
      prevLon = lon;

      let projPt: [number, number] | null = null;
      if (projId === "Mercator") {
        const clamped = Math.max(-MERCATOR_LAT_CLIP, Math.min(MERCATOR_LAT_CLIP, lat));
        const phi = clamped * DEG2RAD;
        projPt = [lon * DEG2RAD, Math.log(Math.tan(Math.PI / 4 + phi / 2))];
      } else if (projId === "Mollweide") {
        const phi = lat * DEG2RAD;
        if (Math.abs(Math.abs(phi) - Math.PI / 2) < 1e-7) {
          projPt = [0, SQRT2 * (phi > 0 ? 1 : -1)];
        } else {
          let theta = phi;
          const target = Math.PI * Math.sin(phi);
          for (let it = 0; it < 12; it++) {
            const d = (2 * theta + Math.sin(2 * theta) - target) / (2 + 2 * Math.cos(2 * theta));
            theta -= d;
            if (Math.abs(d) < 1e-9) break;
          }
          projPt = [((2 * SQRT2) / Math.PI) * (lon * DEG2RAD) * Math.cos(theta), SQRT2 * Math.sin(theta)];
        }
      } else {
        const lam = (lon - ORTHO_LON0) * DEG2RAD;
        const phi = lat * DEG2RAD;
        const cosC = sinLat0 * Math.sin(phi) + cosLat0 * Math.cos(phi) * Math.cos(lam);
        if (cosC >= 0) {
          projPt = [
            Math.cos(phi) * Math.sin(lam),
            cosLat0 * Math.sin(phi) - sinLat0 * Math.cos(phi) * Math.cos(lam),
          ];
        }
      }

      if (projPt === null) {
        if (cur.length > 1) runs.push(cur);
        cur = [];
      } else {
        if (cur.length > 0 && poly.layer !== "continent") {
          const last = cur[cur.length - 1];
          if (Math.hypot(projPt[0] - last[0], projPt[1] - last[1]) > poly.jumpMax) {
            if (cur.length > 1) runs.push(cur);
            cur = [];
          }
        }
        cur.push(projPt);
      }
    }
    if (cur.length > 1) runs.push(cur);

    if (poly.singleRunOnly) {
      if (runs.length === 1 && runs[0].length >= poly.minPts) {
        tissot.push(runs[0]);
      }
    } else {
      for (let r = 0; r < runs.length; r++) {
        if (runs[r].length < poly.minPts) continue;
        if (poly.layer === "continent") continents.push(runs[r]);
        else if (poly.layer === "border") borders.push(runs[r]);
        else if (poly.layer === "graticule") graticules.push(runs[r]);
        else if (poly.layer === "equator") equator.push(runs[r]);
        else if (poly.layer === "meridian") primeMeridian.push(runs[r]);
      }
    }
  }

  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (let i = 0; i < boundary.length; i++) {
    const [x, y] = boundary[i];
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
  }

  projectedBundles.push({
    id: projId,
    title: meta.title,
    subtitle: meta.subtitle,
    note: meta.note,
    boundary,
    continents,
    borders,
    graticules,
    equator,
    primeMeridian,
    tissot,
    bboxMin: [minX, minY],
    bboxMax: [maxX, maxY],
  });
}

function GeoOverlay({ bundleIndex }: { bundleIndex: number }) {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const bundle = projectedBundles[bundleIndex];
  const clipId = `proj-clip-${bundle.id}`;

  let boundaryD = "";
  for (let i = 0; i < bundle.boundary.length; i++) {
    const px = xScale(bundle.boundary[i][0]);
    const py = yScale(bundle.boundary[i][1]);
    boundaryD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
  }
  boundaryD += "Z";

  let continentsD = "";
  for (let r = 0; r < bundle.continents.length; r++) {
    const run = bundle.continents[r];
    for (let i = 0; i < run.length; i++) {
      const px = xScale(run[i][0]);
      const py = yScale(run[i][1]);
      continentsD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    }
    continentsD += "Z";
  }

  let bordersD = "";
  for (let r = 0; r < bundle.borders.length; r++) {
    const run = bundle.borders[r];
    for (let i = 0; i < run.length; i++) {
      const px = xScale(run[i][0]);
      const py = yScale(run[i][1]);
      bordersD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    }
  }

  let graticuleD = "";
  for (let r = 0; r < bundle.graticules.length; r++) {
    const run = bundle.graticules[r];
    for (let i = 0; i < run.length; i++) {
      const px = xScale(run[i][0]);
      const py = yScale(run[i][1]);
      graticuleD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    }
  }

  let equatorD = "";
  for (let r = 0; r < bundle.equator.length; r++) {
    const run = bundle.equator[r];
    for (let i = 0; i < run.length; i++) {
      const px = xScale(run[i][0]);
      const py = yScale(run[i][1]);
      equatorD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    }
  }

  let meridianD = "";
  for (let r = 0; r < bundle.primeMeridian.length; r++) {
    const run = bundle.primeMeridian[r];
    for (let i = 0; i < run.length; i++) {
      const px = xScale(run[i][0]);
      const py = yScale(run[i][1]);
      meridianD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    }
  }

  let tissotD = "";
  for (let r = 0; r < bundle.tissot.length; r++) {
    const run = bundle.tissot[r];
    for (let i = 0; i < run.length; i++) {
      const px = xScale(run[i][0]);
      const py = yScale(run[i][1]);
      tissotD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    }
    tissotD += "Z";
  }

  return (
    <g>
      <defs>
        <clipPath id={clipId}>
          <path d={boundaryD} />
        </clipPath>
      </defs>
      <path d={boundaryD} fill={t.elevatedBg} />
      <g clipPath={`url(#${clipId})`}>
        <path d={graticuleD} fill="none" stroke={t.inkSoft} strokeOpacity={0.28} strokeWidth={0.9} />
        <path
          d={equatorD}
          fill="none"
          stroke={t.inkSoft}
          strokeOpacity={0.62}
          strokeWidth={1.3}
          strokeDasharray="4 3"
        />
        <path
          d={meridianD}
          fill="none"
          stroke={t.inkSoft}
          strokeOpacity={0.62}
          strokeWidth={1.3}
          strokeDasharray="4 3"
        />
        <path
          d={continentsD}
          fill={t.inkSoft}
          fillOpacity={0.28}
          stroke={t.inkSoft}
          strokeOpacity={0.85}
          strokeWidth={1.2}
          strokeLinejoin="round"
        />
        <path
          d={bordersD}
          fill="none"
          stroke={t.ink}
          strokeOpacity={0.55}
          strokeWidth={0.9}
          strokeDasharray="2 2"
        />
        <path
          d={tissotD}
          fill={t.palette[0]}
          fillOpacity={0.28}
          stroke={t.palette[0]}
          strokeOpacity={0.95}
          strokeWidth={1.2}
        />
      </g>
      <path d={boundaryD} fill="none" stroke={t.inkSoft} strokeOpacity={0.75} strokeWidth={1.6} />
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const rowHeight = height - TITLE_HEIGHT - FOOTER_HEIGHT;
  const totalWidth = width - OUTER_PAD_X * 2 - PANEL_GAP * (projectedBundles.length - 1);

  const weights: number[] = [];
  let weightSum = 0;
  for (let i = 0; i < projectedBundles.length; i++) {
    const b = projectedBundles[i];
    const aspect = (b.bboxMax[0] - b.bboxMin[0]) / (b.bboxMax[1] - b.bboxMin[1]);
    const w = Math.pow(aspect, 0.45);
    weights.push(w);
    weightSum += w;
  }

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
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <div
        style={{
          height: rowHeight,
          padding: `0 ${OUTER_PAD_X}px`,
          display: "flex",
          flexDirection: "row",
          gap: PANEL_GAP,
          alignItems: "center",
        }}
      >
        {projectedBundles.map((bundle, idx) => {
          const panelW = Math.floor((totalWidth * weights[idx]) / weightSum);
          const mapH = rowHeight - PANEL_HEADER_HEIGHT - PANEL_FOOTER_HEIGHT;
          const margin = { top: 8, right: 12, bottom: 8, left: 12 };
          const drawW = panelW - margin.left - margin.right;
          const drawH = mapH - margin.top - margin.bottom;

          const dx = (bundle.bboxMax[0] - bundle.bboxMin[0]) * (1 + DOMAIN_PAD_SHARE);
          const dy = (bundle.bboxMax[1] - bundle.bboxMin[1]) * (1 + DOMAIN_PAD_SHARE);
          const cx = (bundle.bboxMin[0] + bundle.bboxMax[0]) / 2;
          const cy = (bundle.bboxMin[1] + bundle.bboxMax[1]) / 2;
          const targetAspect = drawW / drawH;
          const dataAspect = dx / dy;
          const halfW = dataAspect >= targetAspect ? dx / 2 : (dy * targetAspect) / 2;
          const halfH = dataAspect >= targetAspect ? dx / targetAspect / 2 : dy / 2;

          return (
            <div
              key={bundle.id}
              style={{
                width: panelW,
                height: rowHeight,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
              }}
            >
              <div
                style={{
                  height: PANEL_HEADER_HEIGHT,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "flex-end",
                  paddingBottom: 6,
                }}
              >
                <div style={{ fontSize: 18, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>
                  {bundle.title}
                </div>
                <div style={{ fontSize: 14, color: t.inkSoft, marginTop: 3 }}>
                  {bundle.subtitle}
                </div>
              </div>
              <ChartsContainer
                width={panelW}
                height={mapH}
                margin={margin}
                skipAnimation
                series={[]}
                xAxis={[
                  {
                    position: "none",
                    scaleType: "linear",
                    min: cx - halfW,
                    max: cx + halfW,
                  },
                ]}
                yAxis={[
                  {
                    position: "none",
                    scaleType: "linear",
                    min: cy - halfH,
                    max: cy + halfH,
                  },
                ]}
              >
                <GeoOverlay bundleIndex={idx} />
              </ChartsContainer>
              <div
                style={{
                  height: PANEL_FOOTER_HEIGHT,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 14,
                  color: t.inkSoft,
                }}
              >
                {bundle.note}
              </div>
            </div>
          );
        })}
      </div>
      <div
        style={{
          height: FOOTER_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 28,
          fontSize: 14,
          color: t.inkSoft,
        }}
      >
        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: 3,
              background: t.inkSoft,
              opacity: 0.45,
              border: `1.5px solid ${t.inkSoft}`,
              display: "inline-block",
            }}
          />
          Landmasses & country borders
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: "50%",
              background: t.palette[0],
              opacity: 0.55,
              border: `1.5px solid ${t.palette[0]}`,
              display: "inline-block",
            }}
          />
          {`Tissot indicatrix (equal ${TISSOT_RADIUS_KM} km radius circles on the globe — reveals local scale & angular distortion)`}
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 18,
              height: 0,
              borderTop: `1.5px dashed ${t.inkSoft}`,
              display: "inline-block",
            }}
          />
          {`${GRATICULE_STEP_DEG}° graticule (equator & prime meridian dashed)`}
        </span>
      </div>
    </div>
  );
}
