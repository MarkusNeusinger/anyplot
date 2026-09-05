// anyplot.ai
// scatter-color-mapped: Color-Mapped Scatter Plot
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const stationCount = 220;
const points = [];
for (let i = 0; i < stationCount; i++) {
  const longitude = -170 + rand() * 60; // degrees W, Pacific basin
  const latitude = -10 + rand() * 50; // degrees N, equator to mid-latitude
  const baseTemp = 29 - 0.32 * Math.abs(latitude - 5); // warmer near the equator
  const gradient = (longitude + 170) * 0.02; // mild east-west drift
  const noise = (rand() - 0.5) * 2.5;
  const seaSurfaceTemp = baseTemp + gradient + noise;
  points.push([longitude, latitude, Number(seaSurfaceTemp.toFixed(2))]);
}

const temps = points.map((p) => p[2]);
const tempMin = Math.min(...temps);
const tempMax = Math.max(...temps);

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "scatter-color-mapped · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: 90, right: 220, top: 100, bottom: 90 },
  xAxis: {
    type: "value",
    name: "Longitude (°W)",
    nameLocation: "middle",
    nameGap: 40,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: -170,
    max: -110,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Latitude (°N)",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: -10,
    max: 40,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  visualMap: {
    type: "continuous",
    dimension: 2,
    min: Math.floor(tempMin),
    max: Math.ceil(tempMax),
    orient: "vertical",
    right: 40,
    top: "middle",
    itemHeight: 500,
    text: ["Sea Surface Temp (°C)", ""],
    textStyle: { color: t.inkSoft, fontSize: 14 },
    inRange: { color: t.seq },
    calculable: true,
  },
  series: [
    {
      type: "scatter",
      data: points,
      symbolSize: 20,
      itemStyle: {
        opacity: 0.85,
        borderColor: t.pageBg,
        borderWidth: 1,
      },
    },
  ],
});
