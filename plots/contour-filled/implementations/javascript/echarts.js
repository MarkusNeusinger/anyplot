// anyplot.ai
// contour-filled: Filled Contour Plot
// Library: echarts 6.1.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-09

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// Constants
const LEVEL_TARGET = 10; // aim for about this many evenly stepped contour levels

// Columns: set these to your data's column names
const EAST = "Distance East–West (km)"; // role: x
const NORTH = "Distance North–South (km)"; // role: y
const RAIN = "Rainfall intensity (mm/hr)"; // role: z

// Data: replace this block with your own records, one object per grid point
// Combined rainfall intensity of two overlapping storm cells over a 100 km x 100 km
// region, sampled on a regular 100 x 100 grid. Each storm cell is a Gaussian:
// [centre east, centre north, sigma, peak intensity in mm/hr].
const gridSize = 100;
const storms = [
  [-25, -18, 11, 45],
  [25, 20, 13, 30],
];
const data = [];
for (let i = 0; i < gridSize; i++) {
  for (let j = 0; j < gridSize; j++) {
    const east = Math.round((-50 + (100 * i) / (gridSize - 1)) * 100) / 100;
    const north = Math.round((-50 + (100 * j) / (gridSize - 1)) * 100) / 100;
    const rain = storms.reduce(
      (sum, [cx, cy, sigma, peak]) =>
        sum + peak * Math.exp(-((east - cx) ** 2 + (north - cy) ** 2) / (2 * sigma * sigma)),
      0,
    );
    data.push({ [EAST]: east, [NORTH]: north, [RAIN]: Math.round(rain * 10) / 10 });
  }
}

// Plot: reads only data and the constants above
// Rebuild the regular grid from the records; a missing grid point stays null.
const xs = [...new Set(data.map((d) => d[EAST]))].sort((a, b) => a - b);
const ys = [...new Set(data.map((d) => d[NORTH]))].sort((a, b) => a - b);
const xIndex = new Map(xs.map((v, i) => [v, i]));
const yIndex = new Map(ys.map((v, j) => [v, j]));
const z = xs.map(() => ys.map(() => null));
data.forEach((d) => {
  z[xIndex.get(d[EAST])][yIndex.get(d[NORTH])] = d[RAIN];
});

// Round steps (1, 2, 2.5 or 5 times a power of ten) for the levels and both axes' ticks
const values = data.map((d) => d[RAIN]).filter((v) => v != null);
const zMin = Math.min(...values);
const zMax = Math.max(...values);
const [levelStep, xTick, yTick] = [
  [zMax - zMin, LEVEL_TARGET],
  [xs.at(-1) - xs[0], 4],
  [ys.at(-1) - ys[0], 4],
].map(([span, parts]) => {
  const raw = span / parts;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  return [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= raw);
});

// Evenly stepped levels that span the data's range
const levelLow = Math.floor(zMin / levelStep) * levelStep;
const levelCount = Math.ceil((zMax - levelLow) / levelStep);
const levels = Array.from({ length: levelCount + 1 }, (_, k) => +(levelLow + k * levelStep).toFixed(6));

// Marching triangles: every grid cell splits into two triangles, the field is linear
// on each, so the region above a level and the level's isoline are exact polygons and
// segments. Layer k holds the region at or above levels[k], painted in the colour of
// band k; stacking the layers from low to high leaves each point in the colour of its
// band, with smooth boundaries and no seams between bands.
const layers = levels.slice(0, -1).map(() => []);
const isolines = [];
for (let i = 0; i + 1 < xs.length; i++) {
  for (let j = 0; j + 1 < ys.length; j++) {
    const a = [xs[i], ys[j], z[i][j]];
    const b = [xs[i + 1], ys[j], z[i + 1][j]];
    const c = [xs[i + 1], ys[j + 1], z[i + 1][j + 1]];
    const d = [xs[i], ys[j + 1], z[i][j + 1]];
    for (const tri of [
      [a, b, c],
      [a, c, d],
    ]) {
      if (tri.some((p) => p[2] == null)) continue;
      const triMax = Math.max(...tri.map((p) => p[2]));
      layers.forEach((layer, k) => {
        const level = levels[k];
        if (triMax < level) return;
        const polygon = [];
        const crossings = [];
        tri.forEach((p, n) => {
          const q = tri[(n + 1) % 3];
          if (p[2] >= level) polygon.push(p);
          if (p[2] >= level !== q[2] >= level) {
            const s = (level - p[2]) / (q[2] - p[2]);
            const cross = [p[0] + s * (q[0] - p[0]), p[1] + s * (q[1] - p[1])];
            polygon.push(cross);
            crossings.push(cross);
          }
        });
        layer.push(polygon);
        if (k > 0 && crossings.length === 2) isolines.push(crossings);
      });
    }
  }
}

const titleText = "Storm Rainfall Intensity · contour-filled · javascript · echarts · anyplot.ai";
const titleSize = Math.max(15, Math.round(22 * Math.min(1, 67 / titleText.length)));

// Colour bar: one swatch per band, split by hairline gaps, centred beside the field
const gridBox = { left: 110, top: 145, width: 880, height: 880 };
const swatchGap = 2;
const swatchHeight = Math.min(60, Math.floor(600 / layers.length)) - swatchGap;
const barTop = gridBox.top + (gridBox.height - (swatchHeight + swatchGap) * layers.length) / 2;

const axisStyle = {
  nameLocation: "middle",
  nameTextStyle: { color: t.ink, fontSize: 18 },
  axisLabel: { color: t.inkSoft, fontSize: 15 },
  axisLine: { show: false },
  axisTick: { show: false },
  splitLine: { show: false },
};

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",

  title: [
    {
      text: titleText,
      left: "center",
      top: 24,
      textStyle: { color: t.ink, fontSize: titleSize, fontWeight: "bold" },
    },
    {
      text: RAIN.replace(" (", "\n("),
      left: gridBox.left + gridBox.width + 40,
      top: barTop - 58,
      textStyle: { color: t.ink, fontSize: 15, fontWeight: "normal", lineHeight: 20 },
    },
  ],

  grid: gridBox,

  xAxis: {
    ...axisStyle,
    type: "value",
    name: EAST,
    nameGap: 40,
    min: xs[0],
    max: xs.at(-1),
    interval: xTick,
  },

  yAxis: {
    ...axisStyle,
    type: "value",
    name: NORTH,
    nameGap: 55,
    min: ys[0],
    max: ys.at(-1),
    interval: yTick,
  },

  // Piecewise colour bar on the Imprint sequential ramp, one piece per band
  visualMap: {
    type: "piecewise",
    seriesIndex: 0,
    dimension: 2,
    pieces: layers.map((_, k) => ({
      gte: levels[k],
      lt: levels[k + 1],
      label: `${levels[k]}–${levels[k + 1]}`,
    })),
    inRange: { color: t.seq },
    orient: "vertical",
    align: "left",
    left: gridBox.left + gridBox.width + 40,
    top: barTop,
    itemSymbol: "rect",
    itemWidth: 26,
    itemHeight: swatchHeight,
    itemGap: swatchGap,
    textGap: 12,
    textStyle: { color: t.inkSoft, fontSize: 15 },
    hoverLink: false,
  },

  series: [
    {
      // Filled bands: one path per layer, painted from the lowest level up
      type: "custom",
      silent: true,
      encode: { x: 0, y: 1 },
      data: layers.map((_, k) => [xs[0], ys[0], (levels[k] + levels[k + 1]) / 2]),
      renderItem: (params, api) => ({
        type: "path",
        shape: {
          pathData: layers[params.dataIndex]
            .map(
              (polygon) =>
                polygon
                  .map((p, n) => {
                    const [px, py] = api.coord(p);
                    return `${n ? "L" : "M"}${px.toFixed(2)} ${py.toFixed(2)}`;
                  })
                  .join("") + "Z",
            )
            .join(""),
        },
        style: { fill: api.visual("color") },
      }),
    },
    {
      // Thin contour lines along every inner band boundary
      type: "custom",
      silent: true,
      encode: { x: 0, y: 1 },
      data: [[xs[0], ys[0]]],
      renderItem: (params, api) => ({
        type: "path",
        shape: {
          pathData: isolines
            .map(([p, q]) => {
              const [px, py] = api.coord(p);
              const [qx, qy] = api.coord(q);
              return `M${px.toFixed(2)} ${py.toFixed(2)}L${qx.toFixed(2)} ${qy.toFixed(2)}`;
            })
            .join(""),
        },
        style: { fill: null, stroke: t.ink, lineWidth: 1, opacity: 0.4 },
      }),
    },
  ],

  tooltip: { show: false },
});
