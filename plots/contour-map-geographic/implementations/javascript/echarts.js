// anyplot.ai
// contour-map-geographic: Contour Lines on Geographic Map
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-01
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Synthetic elevation model of a coastal mountain range (Cascade-like terrain):
// a wavy coastline, an inland rise, and three peaks. Grid: 46 x 46 points over
// a 4.2° x 4.2° lon/lat box.
const LON_MIN = -124.6, LON_MAX = -120.4;
const LAT_MIN = 43.6, LAT_MAX = 47.8;
const NX = 46, NY = 46;

const lonVals = Array.from({ length: NX }, (_, i) => LON_MIN + (i * (LON_MAX - LON_MIN)) / (NX - 1));
const latVals = Array.from({ length: NY }, (_, j) => LAT_MIN + (j * (LAT_MAX - LAT_MIN)) / (NY - 1));

function coastLon(lat) {
  const p = (lat - LAT_MIN) / (LAT_MAX - LAT_MIN);
  return -122.7 + 0.4 * Math.sin(p * 6.6) - 0.15 * Math.cos(p * 3.1);
}

const PEAKS = [
  { lon: -121.9, lat: 47.0, h: 2000, s: 0.34 }, // northern range crest
  { lon: -121.5, lat: 45.4, h: 1550, s: 0.32 }, // central summit
  { lon: -122.0, lat: 44.1, h: 1300, s: 0.3 },  // southern summit
];

function elevationAt(lon, lat) {
  const coast = coastLon(lat);
  if (lon < coast) return 0; // ocean
  let z = (lon - coast) * 900; // inland rise toward the crest
  for (const peak of PEAKS) {
    const d2 = (lon - peak.lon) ** 2 + (lat - peak.lat) ** 2;
    z += peak.h * Math.exp(-d2 / (2 * peak.s * peak.s));
  }
  return Math.min(3400, z);
}

// Flat grid of elevations (index space) + land-only heatmap tiles.
const gridZ = new Array(NX * NY);
const gridData = [];
let maxVal = 0;
for (let j = 0; j < NY; j++) {
  for (let i = 0; i < NX; i++) {
    const z = elevationAt(lonVals[i], latVals[j]);
    gridZ[j * NX + i] = z;
    if (z > 0) {
      gridData.push([i, j, z]);
      if (z > maxVal) maxVal = z;
    }
  }
}

const lonLabels = lonVals.map((v) => `${Math.abs(v).toFixed(1)}°W`);
const latLabels = latVals.map((v) => `${v.toFixed(1)}°N`);

// --- Coastline overlay (index-space polyline) -------------------------------
function lonToIndex(lon) {
  return ((lon - LON_MIN) / (LON_MAX - LON_MIN)) * (NX - 1);
}
const coastSegments = [];
for (let j = 0; j < NY - 1; j++) {
  const x1 = lonToIndex(coastLon(latVals[j]));
  const x2 = lonToIndex(coastLon(latVals[j + 1]));
  coastSegments.push([[x1, j], [x2, j + 1]]);
}

// --- Marching squares: isoline segments for one elevation threshold ---------
function contourSegments(threshold) {
  const segs = [];
  for (let j = 0; j < NY - 1; j++) {
    for (let i = 0; i < NX - 1; i++) {
      const vbl = gridZ[j * NX + i];
      const vbr = gridZ[j * NX + (i + 1)];
      const vtr = gridZ[(j + 1) * NX + (i + 1)];
      const vtl = gridZ[(j + 1) * NX + i];

      const abl = vbl >= threshold;
      const abr = vbr >= threshold;
      const atr = vtr >= threshold;
      const atl = vtl >= threshold;
      if (abl === abr && abr === atr && atr === atl) continue;

      const lerp = (a, b, va, vb) => a + ((b - a) * (threshold - va)) / (vb - va);
      const pts = [];
      if (abl !== abr) pts.push([lerp(i, i + 1, vbl, vbr), j]);
      if (abr !== atr) pts.push([i + 1, lerp(j, j + 1, vbr, vtr)]);
      if (atr !== atl) pts.push([lerp(i, i + 1, vtl, vtr), j + 1]);
      if (atl !== abl) pts.push([i, lerp(j, j + 1, vbl, vtl)]);

      if (pts.length === 2) {
        segs.push([pts[0], pts[1]]);
      } else if (pts.length === 4) {
        const center = (vbl + vbr + vtr + vtl) / 4;
        const code5 = abl && atr && !abr && !atl;
        const swapped = code5 ? center < threshold : center >= threshold;
        if (swapped) {
          segs.push([pts[0], pts[3]]);
          segs.push([pts[1], pts[2]]);
        } else {
          segs.push([pts[0], pts[1]]);
          segs.push([pts[2], pts[3]]);
        }
      }
    }
  }
  return segs;
}

// Elevation isolines every 400 m; every third line (1200 m) is a bold, labeled
// "index contour" — the cartographic convention for topographic maps.
const CONTOUR_INTERVAL = 400;
const INDEX_EVERY = 1200;
const levels = [];
for (let lvl = CONTOUR_INTERVAL; lvl <= maxVal; lvl += CONTOUR_INTERVAL) levels.push(lvl);

// Segment tuples: [x1, y1, x2, y2, label, bold]
const segData = [];
levels.forEach((threshold) => {
  const bold = threshold % INDEX_EVERY === 0;
  const segs = contourSegments(threshold);
  let bestI = 0, bestDist = Infinity;
  segs.forEach((seg, si) => {
    const mx = (seg[0][0] + seg[1][0]) / 2;
    const my = (seg[0][1] + seg[1][1]) / 2;
    if (mx < 5 || mx > NX - 5 || my < 5 || my > NY - 5) return;
    const d = (mx - NX / 2) ** 2 + (my - NY / 2) ** 2;
    if (d < bestDist) { bestDist = d; bestI = si; }
  });
  const lbl = `${threshold} m`;
  segs.forEach((seg, si) => {
    segData.push([seg[0][0], seg[0][1], seg[1][0], seg[1][1], bold && si === bestI ? lbl : '', bold ? 1 : 0]);
  });
});

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById('container'));

const TITLE = 'Cascade Range Elevation · contour-map-geographic · javascript · echarts · anyplot.ai';

chart.setOption({
  animation: false,
  backgroundColor: 'transparent',
  title: {
    text: TITLE,
    left: 'center',
    top: 24,
    textStyle: { color: t.ink, fontSize: Math.round(24 * Math.min(1, 67 / TITLE.length)), fontWeight: 'bold' },
  },
  grid: { left: 110, right: 165, top: 100, bottom: 100 },
  xAxis: {
    type: 'category',
    data: lonLabels,
    name: 'Longitude',
    nameLocation: 'middle',
    nameGap: 50,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: 7 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: 'category',
    data: latLabels,
    name: 'Latitude',
    nameLocation: 'middle',
    nameGap: 60,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: 7 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  visualMap: {
    min: 0,
    max: maxVal,
    seriesIndex: [0],
    calculable: false,
    orient: 'vertical',
    right: 25,
    top: 'center',
    itemHeight: 260,
    itemWidth: 22,
    inRange: { color: t.seq },
    textStyle: { color: t.inkSoft, fontSize: 13 },
    text: [`${Math.round(maxVal)} m`, '0 m (coast)'],
    formatter: (v) => `${Math.round(v)} m`,
  },
  series: [
    {
      // Filled elevation surface — land tiles only, ocean left as page background.
      type: 'heatmap',
      data: gridData,
      emphasis: { disabled: true },
    },
    {
      // Coastline overlay marking land/ocean boundary.
      type: 'custom',
      coordinateSystem: 'cartesian2d',
      renderItem(params, api) {
        const seg = coastSegments[params.dataIndex];
        const p1 = api.coord(seg[0]);
        const p2 = api.coord(seg[1]);
        return {
          type: 'line',
          shape: { x1: p1[0], y1: p1[1], x2: p2[0], y2: p2[1] },
          style: { stroke: t.inkSoft, lineWidth: 2.5, opacity: 0.85 },
        };
      },
      data: coastSegments.map((_, idx) => [idx, 0]),
      encode: { x: 0, y: 1 },
      z: 5,
      silent: true,
    },
    {
      // Elevation isolines via marching squares — bold + labeled every 1200 m.
      type: 'custom',
      coordinateSystem: 'cartesian2d',
      renderItem(params, api) {
        const x1 = api.value(0), y1 = api.value(1);
        const x2 = api.value(2), y2 = api.value(3);
        const lbl = api.value(4);
        const bold = api.value(5) === 1;
        const p1 = api.coord([x1, y1]);
        const p2 = api.coord([x2, y2]);

        const lineEl = {
          type: 'line',
          shape: { x1: p1[0], y1: p1[1], x2: p2[0], y2: p2[1] },
          style: { stroke: t.ink, lineWidth: bold ? 2.4 : 1.2, opacity: bold ? 0.8 : 0.4 },
        };

        if (!lbl) return lineEl;

        const mx = (p1[0] + p2[0]) / 2;
        const my = (p1[1] + p2[1]) / 2;
        return {
          type: 'group',
          children: [
            lineEl,
            {
              type: 'rect',
              shape: { x: mx - 30, y: my - 18, width: 60, height: 20, r: 3 },
              style: { fill: t.pageBg, opacity: 0.82 },
            },
            {
              type: 'text',
              x: mx,
              y: my - 8,
              style: { text: lbl, fill: t.ink, fontSize: 13, fontFamily: 'sans-serif', textAlign: 'center', opacity: 0.95 },
            },
          ],
        };
      },
      data: segData,
      encode: { x: 0, y: 1 },
      z: 10,
      silent: true,
    },
  ],
});
