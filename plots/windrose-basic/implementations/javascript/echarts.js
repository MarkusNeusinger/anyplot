// anyplot.ai
// windrose-basic: Wind Rose Chart
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-08-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// One year of hourly wind observations from a coastal weather station,
// binned into 16 compass sectors and 5 speed classes (m/s).
const directions = [
  "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
];
const speedBins = ["0-3", "3-6", "6-9", "9-12", "12+"];

// Relative direction frequency - prevailing wind out of the SW quadrant,
// with a calmer secondary lobe out of the N.
const directionWeight = [
  6.0, 3.2, 2.0, 1.8, 2.4, 2.6, 3.4, 4.6,
  6.8, 9.5, 13.0, 12.4, 10.2, 7.0, 4.4, 3.4,
];
const totalWeight = directionWeight.reduce((a, b) => a + b, 0);
const directionPct = directionWeight.map((w) => (w / totalWeight) * 100);

// Speed-bin shape shifts toward the higher bins as prevailing strength
// grows - calmer secondary directions stay skewed toward the lowest bin.
const maxWeight = Math.max(...directionWeight);
const speedShape = (strength) => {
  const raw = [0.42, 0.28, 0.16, 0.09, 0.05].map(
    (base, i) => base + (strength - 0.5) * i * 0.03
  );
  const sum = raw.reduce((a, b) => a + b, 0);
  return raw.map((v) => v / sum);
};
const table = directionPct.map((pct, i) =>
  speedShape(directionWeight[i] / maxWeight).map((frac) => pct * frac)
);

// --- Colors: sample the Imprint sequential ramp across the speed bins ------
const hexToRgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
const rgbToHex = (rgb) =>
  "#" + rgb.map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");
const seqColor = (f) => {
  const c0 = hexToRgb(t.seq[0]);
  const c1 = hexToRgb(t.seq[1]);
  return rgbToHex(c0.map((v, i) => v + (c1[i] - v) * f));
};
const speedColors = speedBins.map((_, i) => seqColor(i / (speedBins.length - 1)));

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "windrose-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22 },
  },
  legend: {
    bottom: 20,
    left: "center",
    data: speedBins.map((label) => `${label} m/s`),
    textStyle: { color: t.inkSoft, fontSize: 15 },
    itemWidth: 18,
    itemHeight: 14,
  },
  polar: { center: ["50%", "52%"], radius: "62%" },
  angleAxis: {
    type: "category",
    data: directions,
    // boundaryGap centers each category within its sector, so the start
    // angle is offset by half a sector width to land N exactly at top.
    startAngle: 90 + 180 / directions.length,
    clockwise: true,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  radiusAxis: {
    type: "value",
    splitNumber: 4,
    axisLabel: { color: t.inkSoft, fontSize: 12, formatter: "{value}%" },
    axisLine: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: speedBins.map((label, j) => ({
    name: `${label} m/s`,
    type: "bar",
    coordinateSystem: "polar",
    stack: "speed",
    barCategoryGap: "20%",
    data: table.map((row) => Number(row[j].toFixed(2))),
    itemStyle: { color: speedColors[j] },
  })),
});
