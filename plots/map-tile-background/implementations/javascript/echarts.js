// anyplot.ai
// map-tile-background: Map with Tile Background
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 78/100 | Created: 2026-08-26
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Major U.S. landmark cities with annual visitor counts (millions).
const cities = [
  { name: 'New York', lat: 40.7128, lon: -74.006, visitors: 8.2 },
  { name: 'Los Angeles', lat: 34.0522, lon: -118.2437, visitors: 5.9 },
  { name: 'Chicago', lat: 41.8781, lon: -87.6298, visitors: 4.1 },
  { name: 'Houston', lat: 29.7604, lon: -95.3698, visitors: 2.3 },
  { name: 'Phoenix', lat: 33.4484, lon: -112.074, visitors: 1.8 },
  { name: 'San Francisco', lat: 37.7749, lon: -122.4194, visitors: 6.5 },
  { name: 'Seattle', lat: 47.6062, lon: -122.3321, visitors: 3.2 },
  { name: 'Denver', lat: 39.7392, lon: -104.9903, visitors: 2.7 },
  { name: 'Miami', lat: 25.7617, lon: -80.1918, visitors: 5.4 },
  { name: 'Boston', lat: 42.3601, lon: -71.0589, visitors: 3.9 },
  { name: 'Atlanta', lat: 33.749, lon: -84.388, visitors: 2.9 },
  { name: 'New Orleans', lat: 29.9511, lon: -90.0715, visitors: 3.4 },
];

// Equirectangular projection with a latitude-corrected longitude scale — the
// simplest stand-in for the Web Mercator projection real slippy-map tiles use.
const meanLatRad = (cities.reduce((sum, c) => sum + c.lat, 0) / cities.length) * (Math.PI / 180);
const lonScale = Math.cos(meanLatRad);
const points = cities.map(c => [c.lon * lonScale, c.lat, c.visitors, c.name]);

// Padded bounding box around the data, in projected units.
const xs = points.map(p => p[0]);
const ys = points.map(p => p[1]);
const padX = (Math.max(...xs) - Math.min(...xs)) * 0.12;
const padY = (Math.max(...ys) - Math.min(...ys)) * 0.12;
const xMin = Math.min(...xs) - padX;
const xMax = Math.max(...xs) + padX;
const yMin = Math.min(...ys) - padY;
const yMax = Math.max(...ys) + padY;

// Synthetic tile grid: the render harness is offline (no fetch/CDN), so a real
// tile provider (OpenStreetMap, CartoDB, satellite, …) cannot be loaded. A
// checkerboard of tile-sized cells stands in for the raster basemap in its
// place, in the same projected coordinate space as the data points.
const COLS = 12;
const ROWS = 7;
const cellW = (xMax - xMin) / COLS;
const cellH = (yMax - yMin) / ROWS;
const tiles = [];
for (let row = 0; row < ROWS; row++) {
  for (let col = 0; col < COLS; col++) {
    const x0 = xMin + col * cellW;
    const y0 = yMin + row * cellH;
    tiles.push([x0, y0, x0 + cellW, y0 + cellH, (row + col) % 2]);
  }
}

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById('container'));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: 'transparent',
  title: {
    text: 'map-tile-background · javascript · echarts · anyplot.ai',
    subtext: 'Marker size ∝ annual visitors (millions) · schematic tile backdrop (offline render, no live tile provider)',
    left: 'center',
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 'bold' },
    subtextStyle: { color: t.inkSoft, fontSize: 14 },
  },
  grid: { left: 50, right: 50, top: 150, bottom: 60 },
  xAxis: { type: 'value', min: xMin, max: xMax, show: false },
  yAxis: { type: 'value', min: yMin, max: yMax, show: false },
  series: [
    {
      // Tile-grid backdrop — see comment above.
      type: 'custom',
      coordinateSystem: 'cartesian2d',
      renderItem(params, api) {
        const p0 = api.coord([api.value(0), api.value(1)]);
        const p1 = api.coord([api.value(2), api.value(3)]);
        const shaded = api.value(4) === 1;
        return {
          type: 'rect',
          shape: {
            x: Math.min(p0[0], p1[0]),
            y: Math.min(p0[1], p1[1]),
            width: Math.abs(p1[0] - p0[0]),
            height: Math.abs(p1[1] - p0[1]),
          },
          style: { fill: shaded ? t.elevatedBg : t.pageBg, stroke: t.grid, lineWidth: 1 },
        };
      },
      data: tiles,
      encode: { x: 0, y: 1 },
      silent: true,
      z: 1,
    },
    {
      type: 'scatter',
      coordinateSystem: 'cartesian2d',
      data: points,
      encode: { x: 0, y: 1 },
      symbolSize: val => 24 + val[2] * 6,
      itemStyle: { color: t.palette[0], borderColor: t.pageBg, borderWidth: 2 },
      label: {
        show: true,
        formatter: p => p.data[3],
        position: 'top',
        distance: 10,
        color: t.ink,
        fontSize: 15,
      },
      labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
      z: 2,
    },
  ],
});
