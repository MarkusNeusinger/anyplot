// anyplot.ai
// area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
// Library: echarts 5.5.1 | JavaScript 22.23.0
// Quality: 83/100 | Created: 2026-06-30

const t = window.ANYPLOT_TOKENS;
const THEME = window.ANYPLOT_THEME || 'light';

// Wallis (Valais) panorama from Zermatt — Weisshorn to Rimpfischhorn
// peaks: [bearing_deg, elevation_m, name]
const peaks = [
  [6,   4506, "Weisshorn"],
  [16,  4221, "Zinalrothorn"],
  [24,  4063, "Ober Gabelhorn"],
  [31,  4358, "Dent Blanche"],
  [43,  4478, "Matterhorn"],
  [56,  4164, "Breithorn"],
  [63,  4092, "Pollux"],
  [68,  4223, "Castor"],
  [76,  4527, "Liskamm"],
  [86,  4634, "Dufourspitze"],
  [93,  4190, "Strahlhorn"],
  [98,  4199, "Rimpfischhorn"],
];
const MATTERHORN_IDX = 4;

// Piecewise-linear ridgeline — sharp triangular peaks, NOT smooth Gaussian bumps
// Each summit has steep linear flanks meeting at a pointed apex
const ridgePoints = [
  [0, 3050], [2, 3250], [3.5, 3600], [5, 4100], [6, 4506], [7, 4150],
  [8, 3800], [9.5, 3420], [11, 3520], [13, 3750], [15, 4080],
  [16, 4221], [17, 3900], [18.5, 3420], [19.5, 3280],
  [21, 3550], [22.5, 3820], [24, 4063], [25, 3720], [26, 3300], [27, 3080],
  [28.5, 3450], [30, 4000], [31, 4358], [32, 4050], [33.5, 3450], [35, 2980],
  [37, 2870], [38.5, 3000], [40, 3500], [41.5, 3950], [42.5, 4350],
  [43, 4478], [43.5, 4200], [45, 3700], [46.5, 3150], [48, 2950],
  [50, 3000], [52, 3300], [54, 3800], [56, 4164], [57.5, 3900],
  [59, 3500], [60.5, 3480], [62, 3780], [63, 4092], [63.5, 3960],
  [65, 3750], [66.5, 3900], [67.5, 4050], [68, 4223], [68.5, 4010],
  [70, 3650], [71.5, 3750], [73.5, 4050], [75, 4350], [76, 4527],
  [77, 4280], [78.5, 3900], [80, 3650], [82, 4000], [84.5, 4300],
  [86, 4634], [87, 4380], [88.5, 4100], [90, 3750],
  [91.5, 3850], [92.5, 4000], [93, 4190], [94, 3950], [95.5, 3720],
  [96.5, 3800], [97.5, 4030], [98, 4199], [99, 3880],
  [101, 3450], [103, 3100], [105, 2900],
];

// Sky gradient — dusk alpine feel
const skyTop    = THEME === 'dark' ? '#0B1624' : '#BDD6E8';
const skyMid    = THEME === 'dark' ? '#152030' : '#D8EBF2';
const skyBg     = THEME === 'dark' ? '#1A1A17' : '#FAF8F1';

// Mountain silhouette fill — dark warm charcoal for both themes
const fillTop    = THEME === 'dark' ? '#38342E' : '#302C26';
const fillBottom = THEME === 'dark' ? '#201E1A' : '#1A1816';
const ridgeColor = THEME === 'dark' ? '#5A5048' : '#423A30';

// Imprint palette position 1 — highlight the focal Matterhorn peak
const BRAND = t.palette[0]; // #009E73

const titleText = "Alpine Panorama · area-mountain-panorama · javascript · echarts · anyplot.ai";
const titleFontSize = Math.max(14, Math.round(22 * Math.min(1.0, 67 / titleText.length)));

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: {
    type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
    colorStops: [
      { offset: 0,    color: skyTop },
      { offset: 0.55, color: skyMid },
      { offset: 1,    color: skyBg  },
    ],
  },
  title: {
    text: titleText,
    left: 'center',
    top: 18,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 'normal' },
  },
  grid: {
    left: 95,
    right: 50,
    top: 230,
    bottom: 65,
  },
  xAxis: {
    type: 'value',
    min: 0,
    max: 105,
    show: false,
  },
  yAxis: {
    type: 'value',
    min: 2600,
    max: 4900,
    name: 'Elevation (m)',
    nameLocation: 'middle',
    nameGap: 60,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 13,
      formatter: (v) => `${v} m`,
    },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid, width: 1 } },
  },
  series: [{
    type: 'line',
    data: ridgePoints,
    smooth: false,
    symbol: 'none',
    lineStyle: { color: ridgeColor, width: 1.5 },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: fillTop    },
          { offset: 1, color: fillBottom },
        ],
      },
      opacity: 1,
    },
  }],
});

// Peak annotations: staggered leader lines + two-line labels (name + elevation)
// yOffsets: vertical distance (CSS px) from summit to label anchor
// xShifts: horizontal nudge for dense clusters (Pollux/Castor, Strahlhorn/Rimpfischhorn)
const yOffsets = [110,  75, 115,  80, 145,  75,  95,  60, 105, 130,  62,  90];
const xShifts  = [  0,   0,   0,   0,   0,   0, -14, +14,   0,   0,  -8,  +8];

const graphics = [];
peaks.forEach(([angle, elev, name], i) => {
  const result = chart.convertToPixel('grid', [angle, elev]);
  if (!result) return;
  const [px, py] = result;

  const ly = py - yOffsets[i];
  const lx = px + xShifts[i];
  const isMH = (i === MATTERHORN_IDX);

  const dotColor      = isMH ? BRAND : t.inkSoft;
  const lineStroke    = isMH ? BRAND : t.inkSoft;
  const dotR          = isMH ? 5 : 3;
  const nameFill      = isMH ? BRAND : t.ink;
  const nameFontSize  = isMH ? 15 : 13;
  const lineWidth     = isMH ? 1.5 : 1;

  // Leader line: from just above summit dot to just below the elevation label
  graphics.push({
    type: 'line',
    z: 20,
    shape: { x1: px, y1: py - dotR - 1, x2: lx, y2: ly + 16 },
    style: { stroke: lineStroke, lineWidth, opacity: 0.7 },
  });

  // Summit dot
  graphics.push({
    type: 'circle',
    z: 20,
    shape: { cx: px, cy: py - dotR, r: dotR },
    style: { fill: dotColor, stroke: 'none' },
  });

  // Peak name (bold, baseline at ly)
  graphics.push({
    type: 'text',
    z: 20,
    x: lx,
    y: ly,
    style: {
      text: name,
      textAlign: 'center',
      textBaseline: 'bottom',
      fill: nameFill,
      fontSize: nameFontSize,
      fontWeight: 'bold',
    },
  });

  // Elevation in meters (lighter, just below name)
  graphics.push({
    type: 'text',
    z: 20,
    x: lx,
    y: ly + 2,
    style: {
      text: `${elev} m`,
      textAlign: 'center',
      textBaseline: 'top',
      fill: t.inkSoft,
      fontSize: 11,
    },
  });
});

chart.setOption({ graphic: graphics });
