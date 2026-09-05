// anyplot.ai
// polar-scatter: Polar Scatter Plot
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 76/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Wind observations: direction (degrees), speed (m/s), time of day.
// A tiny LCG stands in for a seeded RNG (Math.random() is not reproducible).
let seed = 42;
function lcg() {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
}

const TIME_OF_DAY = ["morning", "afternoon", "evening"];
const PREVAILING_DIRECTION = [260, 90, 300]; // morning / afternoon / evening prevailing bearing, degrees
const SPREAD = 35; // degrees of scatter around the prevailing bearing
const POINTS_PER_PERIOD = 42;

const observations = [];
TIME_OF_DAY.forEach((period, i) => {
  for (let j = 0; j < POINTS_PER_PERIOD; j++) {
    const jitter = (lcg() - 0.5) * 2 * SPREAD;
    const angle = (PREVAILING_DIRECTION[i] + jitter + 360) % 360;
    const speed = 4 + lcg() * 6 + (lcg() - 0.5) * 3; // m/s, roughly 2.5-11.5
    observations.push({
      name: period,
      value: [Math.max(0.5, speed), angle],
    });
  }
});

const seriesByPeriod = TIME_OF_DAY.map((period, i) => ({
  name: period,
  type: "scatter",
  coordinateSystem: "polar",
  symbolSize: 20,
  itemStyle: { color: t.palette[i], opacity: 0.75 },
  data: observations.filter((o) => o.name === period).map((o) => o.value),
}));

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "Wind Observations · polar-scatter · javascript · echarts · anyplot.ai",
    left: "center",
    top: 30,
    textStyle: { color: t.ink, fontSize: 20, fontWeight: 500 },
  },
  legend: {
    data: TIME_OF_DAY,
    bottom: 20,
    textStyle: { color: t.inkSoft, fontSize: 15 },
    itemWidth: 16,
    itemHeight: 16,
  },
  polar: {
    center: ["50%", "54%"],
    radius: "62%",
  },
  angleAxis: {
    type: "value",
    min: 0,
    max: 360,
    interval: 45,
    startAngle: 90,
    clockwise: false,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 14,
      formatter: "{value}°",
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  radiusAxis: {
    type: "value",
    min: 0,
    name: "Wind speed (m/s)",
    nameGap: 18,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: seriesByPeriod,
});
