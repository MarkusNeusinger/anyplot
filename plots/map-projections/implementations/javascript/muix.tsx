// anyplot.ai
// map-projections: World Map with Different Projections
// Library: muix 9.2.1 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-08-06

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
const TISSOT_RADIUS_RAD = 550 / 6371;
const TISSOT_STEPS = 48;
const DOMAIN_PAD_SHARE = 0.04;

// Data
const FEATURE_KIND_COL = "Feature Kind";
const FEATURE_NAME_COL = "Feature Name";
const SEQ_COL = "Vertex Sequence";
const LON_COL = "Longitude (°)";
const LAT_COL = "Latitude (°)";
const PROJ_ID_COL = "Projection ID";
const PROJ_TITLE_COL = "Projection Title";
const PROJ_SUBTITLE_COL = "Projection Subtitle";
const PROJ_NOTE_COL = "Distortion Note";

const RAW_POLYGONS: Array<{ kind: string; name: string; pts: Array<[number, number]> }> = [
  {
    kind: "continent",
    name: "North America",
    pts: [
      [-168, 65], [-160, 70], [-140, 70], [-125, 72], [-95, 74], [-80, 70], [-65, 62],
      [-55, 52], [-60, 46], [-70, 42], [-76, 35], [-81, 25], [-90, 21], [-88, 16],
      [-83, 10], [-78, 8], [-85, 11], [-92, 15], [-97, 19], [-105, 20], [-110, 24],
      [-117, 32], [-122, 37], [-124, 48], [-135, 58], [-150, 60], [-162, 55], [-168, 65],
    ],
  },
  {
    kind: "continent",
    name: "Greenland",
    pts: [
      [-52, 60], [-44, 60], [-22, 70], [-18, 77], [-30, 83], [-55, 82], [-68, 76],
      [-56, 68], [-52, 60],
    ],
  },
  {
    kind: "continent",
    name: "South America",
    pts: [
      [-78, 9], [-72, 12], [-62, 10], [-50, 2], [-35, -6], [-38, -15], [-40, -22],
      [-48, -28], [-54, -34], [-62, -40], [-66, -48], [-68, -55], [-74, -52], [-73, -42],
      [-71, -30], [-70, -18], [-76, -12], [-81, -5], [-79, 2], [-78, 9],
    ],
  },
  {
    kind: "continent",
    name: "Europe",
    pts: [
      [-10, 36], [-9, 43], [-2, 44], [-5, 48], [2, 51], [8, 55], [10, 58], [5, 62],
      [15, 68], [28, 71], [42, 68], [58, 68], [60, 55], [48, 46], [38, 45], [29, 41],
      [26, 38], [22, 37], [18, 40], [15, 38], [12, 42], [8, 44], [3, 42], [-2, 37],
      [-6, 36], [-10, 36],
    ],
  },
  {
    kind: "continent",
    name: "Great Britain",
    pts: [[-6, 50], [-5, 58], [-2, 58], [1, 52], [-6, 50]],
  },
  {
    kind: "continent",
    name: "Africa",
    pts: [
      [-17, 15], [-13, 28], [-6, 35], [10, 37], [25, 32], [33, 31], [38, 22], [43, 12],
      [51, 12], [45, 2], [40, -10], [35, -22], [28, -33], [18, -35], [14, -22], [12, -6],
      [9, 4], [2, 6], [-8, 5], [-16, 11], [-17, 15],
    ],
  },
  {
    kind: "continent",
    name: "Madagascar",
    pts: [[44, -25], [49, -13], [50, -16], [47, -25], [44, -25]],
  },
  {
    kind: "continent",
    name: "Asia",
    pts: [
      [28, 41], [40, 42], [50, 40], [58, 55], [60, 68], [75, 73], [105, 76], [140, 73],
      [175, 66], [170, 60], [155, 52], [142, 50], [135, 38], [128, 36], [122, 31],
      [118, 23], [108, 21], [105, 10], [102, 2], [98, 8], [92, 21], [88, 22], [80, 10],
      [76, 8], [72, 20], [67, 24], [58, 25], [55, 22], [48, 14], [43, 13], [38, 22],
      [34, 30], [36, 36], [28, 41],
    ],
  },
  {
    kind: "continent",
    name: "Japan",
    pts: [[130, 31], [136, 35], [141, 41], [145, 44], [141, 38], [134, 33], [130, 31]],
  },
  {
    kind: "continent",
    name: "Maritime SE Asia",
    pts: [[96, 5], [104, -2], [114, -7], [120, -8], [116, -2], [106, 2], [96, 5]],
  },
  {
    kind: "continent",
    name: "Australia",
    pts: [
      [114, -22], [122, -16], [132, -12], [136, -15], [142, -11], [148, -20], [153, -28],
      [150, -37], [140, -38], [132, -32], [122, -34], [115, -34], [114, -22],
    ],
  },
  {
    kind: "continent",
    name: "New Zealand",
    pts: [[166, -46], [172, -41], [178, -37], [175, -42], [168, -46], [166, -46]],
  },
  {
    kind: "continent",
    name: "Antarctica",
    pts: [
      [-179, -72], [-120, -73], [-62, -65], [-58, -74], [-20, -72], [20, -70], [70, -68],
      [120, -67], [170, -71], [179, -78], [120, -82], [0, -82], [-120, -82], [-179, -78],
      [-179, -72],
    ],
  },
  {
    kind: "border",
    name: "Canada-US",
    pts: [[-124, 49], [-95, 49], [-83, 46], [-75, 45], [-67, 47]],
  },
  {
    kind: "border",
    name: "US-Mexico",
    pts: [[-117, 32], [-106, 31], [-97, 26]],
  },
  {
    kind: "border",
    name: "Brazil West",
    pts: [[-52, 4], [-60, 2], [-70, -4], [-70, -11], [-58, -20], [-54, -33]],
  },
  {
    kind: "border",
    name: "Andes South",
    pts: [[-70, -18], [-68, -27], [-70, -38], [-72, -50]],
  },
  {
    kind: "border",
    name: "Europe-Russia",
    pts: [[28, 70], [30, 60], [38, 50], [40, 44]],
  },
  {
    kind: "border",
    name: "Sahara South",
    pts: [[-16, 15], [0, 15], [15, 14], [32, 12], [43, 12]],
  },
  {
    kind: "border",
    name: "Egypt-Sudan",
    pts: [[25, 31], [25, 22], [36, 22]],
  },
  {
    kind: "border",
    name: "Equatorial Africa",
    pts: [[12, -6], [28, -4], [30, -10], [40, -11]],
  },
  {
    kind: "border",
    name: "Southern Africa",
    pts: [[14, -17], [25, -18], [33, -26]],
  },
  {
    kind: "border",
    name: "Russia-Kazakhstan-China",
    pts: [[50, 46], [68, 52], [87, 49], [105, 50], [120, 50], [134, 48]],
  },
  {
    kind: "border",
    name: "India-China",
    pts: [[67, 25], [75, 35], [88, 28], [97, 28]],
  },
];

const DATA: Array<Record<string, string | number>> = [];
for (let p = 0; p < RAW_POLYGONS.length; p++) {
  const poly = RAW_POLYGONS[p];
  for (let i = 0; i < poly.pts.length; i++) {
    DATA.push({
      [FEATURE_KIND_COL]: poly.kind,
      [FEATURE_NAME_COL]: poly.name,
      [SEQ_COL]: i,
      [LON_COL]: poly.pts[i][0],
      [LAT_COL]: poly.pts[i][1],
      [PROJ_ID_COL]: "Mercator",
      [PROJ_TITLE_COL]: "Mercator (Cylindrical)",
      [PROJ_SUBTITLE_COL]: "Conformal — angles preserved",
      [PROJ_NOTE_COL]: "Area inflates as sec²(φ) toward the poles",
    });
  }
}

const PROJECTION_META: Array<Record<string, string | number>> = [
  {
    [FEATURE_KIND_COL]: "projection",
    [FEATURE_NAME_COL]: "Mercator",
    [SEQ_COL]: 0,
    [LON_COL]: 0,
    [LAT_COL]: 0,
    [PROJ_ID_COL]: "Mercator",
    [PROJ_TITLE_COL]: "Mercator (Cylindrical)",
    [PROJ_SUBTITLE_COL]: "Conformal — angles preserved",
    [PROJ_NOTE_COL]: "Area inflates as sec²(φ) toward the poles",
  },
  {
    [FEATURE_KIND_COL]: "projection",
    [FEATURE_NAME_COL]: "Mollweide",
    [SEQ_COL]: 1,
    [LON_COL]: 0,
    [LAT_COL]: 0,
    [PROJ_ID_COL]: "Mollweide",
    [PROJ_TITLE_COL]: "Mollweide (Pseudocylindrical)",
    [PROJ_SUBTITLE_COL]: "Equal-area — true relative size",
    [PROJ_NOTE_COL]: "Shapes shear near the outer limb",
  },
  {
    [FEATURE_KIND_COL]: "projection",
    [FEATURE_NAME_COL]: "Orthographic",
    [SEQ_COL]: 2,
    [LON_COL]: ORTHO_LON0,
    [LAT_COL]: ORTHO_LAT0,
    [PROJ_ID_COL]: "Orthographic",
    [PROJ_TITLE_COL]: "Orthographic (Azimuthal)",
    [PROJ_SUBTITLE_COL]: `Globe view centered at ${ORTHO_LAT0}°N, ${ORTHO_LON0}°E`,
    [PROJ_NOTE_COL]: "Foreshortened to zero at the horizon",
  },
];
for (let m = 0; m < PROJECTION_META.length; m++) {
  DATA.push(PROJECTION_META[m]);
}

// Reconstruct continent and border polylines from flat DATA rows
const featureMap = new Map<string, { kind: string; pts: Array<[number, number]> }>();
for (let i = 0; i < DATA.length; i++) {
  const row = DATA[i];
  const kind = String(row[FEATURE_KIND_COL]);
  if (kind !== "continent" && kind !== "border") continue;
  const name = String(row[FEATURE_NAME_COL]);
  const key = `${kind}:${name}`;
  let entry = featureMap.get(key);
  if (!entry) {
    entry = { kind, pts: [] };
    featureMap.set(key, entry);
  }
  entry.pts.push([Number(row[LON_COL]), Number(row[LAT_COL])]);
}

interface InputPolyline {
  layer: "continent" | "border" | "graticule" | "equator" | "meridian" | "tissot";
  pts: Array<[number, number]>;
  jumpMax: number;
  minPts: number;
  singleRunOnly: boolean;
  centerLonLat: [number, number] | null;
}

const inputPolylines: InputPolyline[] = [];
for (const entry of featureMap.values()) {
  if (entry.kind === "continent") {
    inputPolylines.push({
      layer: "continent",
      pts: entry.pts,
      jumpMax: 1.6,
      minPts: 3,
      singleRunOnly: false,
      centerLonLat: null,
    });
  } else if (entry.kind === "border") {
    inputPolylines.push({
      layer: "border",
      pts: entry.pts,
      jumpMax: 1.6,
      minPts: 2,
      singleRunOnly: false,
      centerLonLat: null,
    });
  }
}

// Graticules (30° intervals)
for (const lat of [-60, -30, 30, 60]) {
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
for (const lon of [-150, -120, -90, -60, -30, 30, 60, 90, 120, 150]) {
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

// Tissot indicatrix circles at 30° intervals
for (const latC of [-60, -30, 0, 30, 60]) {
  for (const lonC of [-120, -60, 0, 60, 120]) {
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

// Precompute projected geometry for each of the 3 projections
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

for (let pIdx = 0; pIdx < PROJECTION_META.length; pIdx++) {
  const meta = PROJECTION_META[pIdx];
  const projId = String(meta[PROJ_ID_COL]);

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
        if (cur.length > 0) {
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
    title: String(meta[PROJ_TITLE_COL]),
    subtitle: String(meta[PROJ_SUBTITLE_COL]),
    note: String(meta[PROJ_NOTE_COL]),
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
  const xScale = useXScale();
  const yScale = useYScale();
  const bundle = projectedBundles[bundleIndex];
  const clipId = `proj-clip-${bundle.id}`;

  let boundaryD = "";
  for (let i = 0; i < bundle.boundary.length; i++) {
    const px = Number(xScale(bundle.boundary[i][0]));
    const py = Number(yScale(bundle.boundary[i][1]));
    boundaryD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
  }
  boundaryD += "Z";

  let continentsD = "";
  for (let r = 0; r < bundle.continents.length; r++) {
    const run = bundle.continents[r];
    for (let i = 0; i < run.length; i++) {
      const px = Number(xScale(run[i][0]));
      const py = Number(yScale(run[i][1]));
      continentsD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    }
    continentsD += "Z";
  }

  let bordersD = "";
  for (let r = 0; r < bundle.borders.length; r++) {
    const run = bundle.borders[r];
    for (let i = 0; i < run.length; i++) {
      const px = Number(xScale(run[i][0]));
      const py = Number(yScale(run[i][1]));
      bordersD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    }
  }

  let graticuleD = "";
  for (let r = 0; r < bundle.graticules.length; r++) {
    const run = bundle.graticules[r];
    for (let i = 0; i < run.length; i++) {
      const px = Number(xScale(run[i][0]));
      const py = Number(yScale(run[i][1]));
      graticuleD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    }
  }

  let equatorD = "";
  for (let r = 0; r < bundle.equator.length; r++) {
    const run = bundle.equator[r];
    for (let i = 0; i < run.length; i++) {
      const px = Number(xScale(run[i][0]));
      const py = Number(yScale(run[i][1]));
      equatorD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    }
  }

  let meridianD = "";
  for (let r = 0; r < bundle.primeMeridian.length; r++) {
    const run = bundle.primeMeridian[r];
    for (let i = 0; i < run.length; i++) {
      const px = Number(xScale(run[i][0]));
      const py = Number(yScale(run[i][1]));
      meridianD += `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    }
  }

  let tissotD = "";
  for (let r = 0; r < bundle.tissot.length; r++) {
    const run = bundle.tissot[r];
    for (let i = 0; i < run.length; i++) {
      const px = Number(xScale(run[i][0]));
      const py = Number(yScale(run[i][1]));
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
          fill={t.palette[0]}
          fillOpacity={0.32}
          stroke={t.palette[0]}
          strokeOpacity={0.95}
          strokeWidth={1.3}
          strokeLinejoin="round"
        />
        <path
          d={bordersD}
          fill="none"
          stroke={t.inkSoft}
          strokeOpacity={0.55}
          strokeWidth={0.9}
          strokeDasharray="2 2"
        />
        <path
          d={tissotD}
          fill={t.palette[1]}
          fillOpacity={0.34}
          stroke={t.palette[1]}
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
              background: t.palette[0],
              opacity: 0.55,
              border: `1.5px solid ${t.palette[0]}`,
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
              background: t.palette[1],
              opacity: 0.55,
              border: `1.5px solid ${t.palette[1]}`,
              display: "inline-block",
            }}
          />
          Tissot indicatrix (equal 550 km radius circles on the globe — reveals local scale & angular distortion)
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
          30° graticule (equator & prime meridian dashed)
        </span>
      </div>
    </div>
  );
}
